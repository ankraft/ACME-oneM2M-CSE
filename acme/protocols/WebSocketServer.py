#
#	WebSocketServer.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Implementation of a WebSocket Server for a WebSocket Mcx binding implementation.
"""

from __future__ import annotations
from typing import Optional, Any, Tuple
import logging, uuid, base64

from websockets.sync.connection import Connection as WSConnection
from websockets.sync.server import WebSocketServer as WSServer, serve, ServerConnection
from websockets.sync.client import connect
from websockets.protocol import State
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from ..etc.Constants import Constants
from ..helpers.BackgroundWorker import BackgroundWorkerPool, BackgroundWorker
from ..helpers.ThreadSafeCounter import ThreadSafeCounter
from ..etc.RequestUtils import prepareResultForSending, createPositiveResponseResult, createRequestResultFromURI
from ..etc.IDUtils import uniqueID, csiFromSPRelative
from ..etc.Utils import renameThread
from ..etc.Types import ContentSerializationType, Result, CSERequest, Operation, ResourceTypes, RequestType, ResponseType, AuthorizationResult
from ..etc.ResponseStatusCodes import ResponseStatusCode, ResponseException, TARGET_NOT_REACHABLE, ORIGINATOR_HAS_NO_PRIVILEGE
from ..runtime.Configuration import Configuration
from ..runtime import CSE
from ..resources.Resource import Resource
from ..runtime.Logging import Logging as L
from ..etc.Constants import RuntimeConstants as RC

class WebSocketServer(object):
	"""	WebSocket Server implementation.
	"""

	__slots__ = [ 
		'isPaused', 
		'websocketServer', 
		'wsConnections', 
		'associatedConnections', 
		'connectionUsedCounter',
		'operationEvents',
		'actor'
	]
	""" Define slots for instance variables. """


	def __init__(self) -> None:
		"""	Initialization of the WebSocket Server.
		"""

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self._configUpdate)			# type: ignore

		# Add a handler for resource deletion
		CSE.event.addHandler(CSE.event.deleteResource, self._handleDeleteEvent)	# type: ignore

		self.isPaused = False
		"""	Flag whether the server is currently paused. Requests are not handled when the server is paused. """

		self.websocketServer:Optional[WSServer] = None
		"""	The WebSocket server object. """

		self.wsConnections:dict[uuid.UUID, WSConnection] = {}	# websocket.id -> websocket
		"""	The list of currently handled WebSocket connections. """

		self.associatedConnections:dict[str, uuid.UUID] = {}		# originator -> websocket.id
		"""	The list of currently handled WebSocket connections, associated with an originator. """

		self.connectionUsedCounter:dict[uuid.UUID, ThreadSafeCounter] = {}	# websocket.id -> counter
		"""	A counter for each opened WS connection opened by the CSE. """

		self.actor:Optional[BackgroundWorker] = None
		"""	The actor for running the synchronous WebSocket server in the background. """


		self.operationEvents = {
			Operation.CREATE:		[CSE.event.wsCreate, 'WS_C'],		# type: ignore [attr-defined]
			Operation.RETRIEVE: 	[CSE.event.wsRetrieve, 'WS_R'],		# type: ignore [attr-defined]
			Operation.UPDATE:		[CSE.event.wsUpdate, 'WS_U'],		# type: ignore [attr-defined]
			Operation.DELETE:		[CSE.event.wsDelete, 'WS_D'],		# type: ignore [attr-defined]
			Operation.NOTIFY:		[CSE.event.wsNotify, 'WS_M'],		# type: ignore [attr-defined]
			Operation.DISCOVERY:	[CSE.event.wsRetrieve, 'WS_F'],		# type: ignore [attr-defined]
		}
		"""	Events for the different operations. """

		L.isInfo and L.log('WebSocket server initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the WebSocket server.
		"""
		L.isInfo and L.log('WebSocket server shut down')

		# Close all connections gracefully
		L.isDebug and L.logDebug('Closing all WS connections')
		for originator in list(self.associatedConnections.keys()):
			self.closeConnectionForOriginator(originator)

		self._stop()
		return True


	def _configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Optional[Any] = None) -> None:
		"""	Callback for the *configUpdate* event.
			
			Args:
				name: Event name.
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'websocket.enable', 
						'websocket.port',
						'websocket.listenIF',
						'websocket.loglevel',
						'websocket.timeout'
					  ]:
			return

		# Restart the server if the configuration has changed
		self.shutdown()
		self.run()		# Restart the server


	def _handleDeleteEvent(self, name:str, deletedResource:Resource) -> None:
		"""	Callback and handler for the *deleteResource* event.

			In case of an AE deletion, the associated WS connection is dissociated, but left open.

			Args:
				name: Event name.
				deletedResource: The deleted resource.
		"""

		if deletedResource.ty != ResourceTypes.AE or deletedResource.aei not in self.associatedConnections:
			return
		self.dissociateConnectionFromOriginator(deletedResource.aei)


	def _getWSSendingTargetName(self, target:str) -> str:
		"""	Get the target name for sending a WebSocket request.

			Args:
				target: The target to send the request to.

			Returns:
				The target for sending the request.
		"""
		return target if target == Constants.defaultWebSocketSchema else f'{target} (2)'
	

	def run(self) -> bool:
		"""	Initialize and run the WebSocket server as a BackgroundWorker/Actor.
		"""
		if not Configuration.websocket_enable:	# type:ignore[attr-defined]
			L.isInfo and L.log('WebSocket: server NOT enabled')
			return True
		# Actually start the actor to run the WebSocket Server as a thread
		self.actor = BackgroundWorkerPool.newActor(self._run, name = 'WSServer').start()

		L.isInfo and L.log('Start WebSocket server')
		return True


	def _run(self) -> None:
		"""	WebSocket server main loop.
		"""
		self.websocketServer = serve(self.handleIncomingConnection, 
							   		 Configuration.websocket_listenIF,
									 Configuration.websocket_port, 
									 subprotocols = ContentSerializationType.supportedContentSerializationsWS(), # type:ignore[arg-type]
									 ssl_context = CSE.security.getSSLContextWs())		
		logging.getLogger('websockets.server').setLevel(Configuration.websocket_loglevel)
		with self.websocketServer as server:
			server.serve_forever()	# Will block until the server is shutdown
		L.isDebug and L.logDebug('WebSocket server shut down')
		

	def _stop(self) -> None:
		"""	Stop the WebSocket server.
		"""
		if self.websocketServer is not None:
			L.isDebug and L.logDebug('Stopping WebSocket server')
			self.websocketServer.shutdown()
			self.websocketServer = None
		if self.actor is not None:
			self.actor.stop()
			self.actor = None


	def pause(self) -> None:
		"""	Stop handling requests.
		"""
		L.isInfo and L.log('WS server paused')
		self.isPaused = True
		
	
	def unpause(self) -> None:
		"""	Continue handling requests.
		"""
		L.isInfo and L.log('WS server unpaused')
		self.isPaused = False


	def addConnection(self, websocket:WSConnection, cseInitiated:bool = False) -> None:
		"""	Add a new connection to the list of connections.

			Args:
				websocket: The WebSocket connection.
		"""
		L.isDebug and L.logDebug(f'Adding new WS connection: {websocket.id}')
		self.wsConnections[websocket.id] = websocket
		if cseInitiated:
			self.connectionUsedCounter[websocket.id] = ThreadSafeCounter(1)
			L.isDebug and L.logDebug(f'WS connection counter added: {websocket.id}')
	
	
	def incrementConnection(self, websocket:WSConnection) -> None:
		"""	Increment the counter for a connection.

			Args:
				websocket: The WebSocket connection.
		"""
		# Increment the counter for the connection if it is a CSE initiated connection
		if websocket.id in self.connectionUsedCounter:
			_v = self.connectionUsedCounter[websocket.id].increment()
			L.isDebug and L.logDebug(f'WS connection counter incremented: {websocket.id} = {_v}')


	def associateConnectionWithOriginator(self, websocket:WSConnection, originator:str) -> None:
		"""	Associate a connection with an originator.

			If the originator is already associated with another connection then that connection is closed.

			Args:
				websocket: The WebSocket connection.
				originator: The originator.

		"""
		# Check if the originator is already associated with another connection. If so, close that connection
		if originator in self.associatedConnections:
			if self.associatedConnections[originator] != websocket.id:	# Not the same connection
				L.isWarn and L.logWarn(f'WS connection {websocket.id} already associated with originator {originator}. Closing first connection.')
				self.closeConnectionForOriginator(originator)
			else:
				return	# Already associated with this connection
		
		# Associate the connection with the originator
		L.isDebug and L.logDebug(f'Associating WS connection {websocket.id} with originator {originator}')
		self.associatedConnections[originator] = websocket.id

	
	def dissociateConnectionFromOriginator(self, originator:str) -> bool:
		"""	Dissociate a connection from an originator.

			Args:
				originator: The originator to dissociate.
			
			Returns:
				True if the originator was associated with a connection, False otherwise.
		"""
		if originator in self.associatedConnections:
			L.isDebug and L.logDebug(f'Dissociating originator: {originator} from WS connection (+ closing WS Connection)')
			del self.associatedConnections[originator]
			return True
		return False


	def removeConnection(self, websocket:WSConnection, originator:str) -> None:
		"""	Remove a connection from the list of connections.
			Also remove the association between the connection and the originator.

			Args:
				websocket: The WebSocket connection.
				originator: The originator.
		"""
		L.isDebug and L.logDebug(f'Removing WS connection: {websocket.id} and originator: {originator}')
		if websocket.id in self.wsConnections:
			del self.wsConnections[websocket.id]
		if originator in self.associatedConnections:
			del self.associatedConnections[originator]


	def closeConnectionForOriginator(self, originator:str) -> None:
		"""	Close a connection for an originator.

			Args:
				originator: The originator.
		"""
		def _removeConnection(originator:str) -> None:
			if originator in self.associatedConnections:
				websocketID = self.associatedConnections[originator]

				if websocketID in self.connectionUsedCounter:
					# Decrement the counter for the connection
					if (_v := self.connectionUsedCounter[websocketID].decrement()) > 0:
						L.isDebug and L.logDebug(f'WS connection counter decremented: {websocketID} = {_v} - NOT closing connection')
						# There are still other requests using the connection. Do not close the connection yet
						return
					else:
						# Remove the counter
						del self.connectionUsedCounter[websocketID]
						L.isDebug and L.logDebug(f'WS connection counter removed: {websocketID} - closing connection')

				# Also remove from the list of websocket connections
				if websocketID in self.wsConnections:
					websocket = self.wsConnections[websocketID]
					websocket.close()
					self.removeConnection(websocket, originator)
				else:
					del self.associatedConnections[originator]

		L.isDebug and L.logDebug(f'Closing WS connection(s) for originator {originator}')
		_removeConnection(originator)
			
		# Also remove an optional sending target connection
		_removeConnection(self._getWSSendingTargetName(originator))

			

	def _checkIsServerRunning(self, websocket:WSConnection) -> bool:
		"""	Check if the server is running. If not, send an error message to the client.

			Returns:
				True if the server is running, False otherwise.
		"""
		if self.isPaused:
			websocket.send('WebSocket server is not running')
			return False
		return True


	def receiveLoop(self, websocket:WSConnection, wsOriginator:str, ct:ContentSerializationType, authResult:AuthorizationResult) -> None:
		"""	Receive loop for the WebSocket server. This is the main entry point for handling a received message,
			whether the connection was initiated by the server or the client.

			Args:
				websocket: The WebSocket connection.
				wsOriginator: The originator of the connection.
				ct: The content type.
				authResult: The result of the request authentication.
		"""
		try:	
			# Handle incoming requests in separate threads as long as there is no error or the server is stopped
			# or the client closes the connection
			while (message := websocket.recv()) is not None:	# recv() is blocking
				# L.isDebug and L.logDebug(f'Received WS message: {message}')
				if not self._checkIsServerRunning(websocket):
					continue
				# Run the message handling in a separate thread
				BackgroundWorkerPool.runJob(lambda: self._handleReceivedMessage(websocket, message, wsOriginator, ct, authResult), name = f'ws_{uniqueID()}')
		except ConnectionClosedError as e:
			L.isWarn and L.logWarn('Connection closed: {e}')
		except ConnectionClosedOK:
			L.isDebug and L.logDebug('Connection closed by client')
		

	def handleIncomingConnection(self, websocket:ServerConnection) -> None:
		"""	Handle a new incoming WebSocket connection. This connection stays open until the client closes it, or the
			server is stopped. 
			
			Note:
				This method is not called for connections initiated by the server.

			Args:
				websocket: The WebSocket connection.
		"""

		# Variable for this connection's originator
		wsOriginator = None	# This is valid until the first message is received. Then the originator is determined from the message

		# Rename thread
		L.enableScreenLogging and renameThread(prefix = 'ws')

		if not self._checkIsServerRunning(websocket):
			return

		L.isDebug and L.logDebug('New WS connection')
		L.logDebug(f'Received subprotocol: {websocket.subprotocol}')
		L.logDebug(f'Received headers: {websocket.request.headers}')
		L.logDebug(f'Received request: {websocket.request}')

		# Check the authentication
		if (authResult := self._handleAuthentication(websocket)) == AuthorizationResult.UNAUTHORIZED:
			raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logWarn('Authorization failed'))


		# Get the originator from the WS headers
		if 'X-M2M-Origin' in websocket.request.headers:
			wsOriginator = websocket.request.headers['X-M2M-Origin']
			L.isDebug and L.logDebug(f'Originator from WS headers: {wsOriginator}')

		# Determine the content type.
		# The negotiation is done by the server part already. The subprotocol is determined by the client.
		subprotocol = websocket.subprotocol
		contentType = ContentSerializationType.fromWebSocketSubProtocol(subprotocol)

		# Add the connection to the list 
		self.addConnection(websocket)

		# Associate the connection with the originator
		if wsOriginator is not None:
			self.associateConnectionWithOriginator(websocket, wsOriginator)

		try:
			# Handle incoming requests in separate threads as long as there is no error or the server is stopped
			# or the client closes the connection
			while (message := websocket.recv()) is not None:	# recv() is blocking
				L.isDebug and L.logDebug(f'Received WS message: {message!r}')
				if not self._checkIsServerRunning(websocket):
					continue
				# Run the message handling in a separate thread
				BackgroundWorkerPool.runJob(lambda: self._handleReceivedMessage(websocket, 
																				message, 
																				wsOriginator, 
																				contentType, 
																				authResult),
											name = f'ws_{uniqueID()}')
		except ConnectionClosedError as e:
			L.isWarn and L.logWarn('Connection closed: {e}')
		except ConnectionClosedOK:
			L.isDebug and L.logDebug('Connection closed by client')
		
		# Remove the connection from the list of unassociated connections or from the list of associated connections
		self.removeConnection(websocket, wsOriginator)


	def _handleReceivedMessage(self, websocket:WSConnection, 
									 message:str|bytes, 
									 wsOriginator:str, 
									 contentType:ContentSerializationType,
									 authResult:AuthorizationResult) -> None:
		"""	Handle a received message. This is the main entry point for handling a received message, whether the
			message is a request or a response.

			Args:
				websocket: The WebSocket connection.
				message: The received message.
				wsOriginator: The originator of the connection.
				contentType: The content type.
				authResult: The result of the request authentication.
		"""
		if isinstance(message, str):
			message = message.encode()	# Encode to bytes

		request:CSERequest = None
		try:
			
			dissectResult:Result = None
			try:
				dissectResult = CSE.request.dissectRequestFromBytes(message, contentType)
			except ResponseException as e:
				dissectResult = Result(rsc = e.rsc, dbg = e.dbg, request = e.data)
				L.logWarn(f'Error dissecting WS request: {e}')
				raise


			request = dissectResult.request	# type:ignore [attr-defined]
			requestOriginator:str = request.originator	# type:ignore [attr-defined]

			# Add Authorization result to the request
			request.rq_authn = authResult == AuthorizationResult.AUTHORIZED

			# Check whether the message is a response or a request. If it is a response, then put it into the
			# response queue and return. Another process might have sent the request and is waiting for the response.
			if request.requestType == RequestType.RESPONSE:
				L.isDebug and L.logDebug(f'<== WS response: {wsOriginator}')
				L.isDebug and L.logDebug(f'Body: {message.decode()}')
				CSE.request.addResponse(dissectResult)
				return
	
			L.isDebug and L.logDebug(f'==> WS Request: {wsOriginator}')
			L.isDebug and L.logDebug(f'Body: {message.decode()}')

			# Allow empty wsOriginator for AE registrations
			if wsOriginator is None:
				if not (request.op == Operation.CREATE and request.ty == ResourceTypes.AE):
					raise ResponseException(ResponseStatusCode.ORIGINATOR_HAS_NO_PRIVILEGE, 
											dbg = L.logWarn(f'Unknown WS connections (no X-M2M-Origin header) are only allowed for AE registrations'))
				# Else, the request must be an AE registration

			# Compare the originator and the from, only for Mca
			# REMOVEME The following code was used for the Mca, but is not necessary anymore
			# if wsOriginator is not None and not isCSI(wsOriginator):	# wsOriginator is not a CSE-ID, so it must be an AE-ID, ie. it is an Mca request
			# 	if isValidAEI(wsOriginator):
			# 		if toSPRelative(requestOriginator) != toSPRelative(wsOriginator):
			# 			raise ORIGINATOR_HAS_NO_PRIVILEGE(L.logWarn(f'Originator mismatch: {requestOriginator} != {wsOriginator}'))
			# 	else:
			# 		raise BAD_REQUEST(L.logWarn(f'Invalid originator format: {wsOriginator}'))

			# Send the operation event and rename the thread
			_t = self.operationEvents[request.op]
			_t[0]()	# Send event
			L.enableScreenLogging and renameThread(_t[1]) # rename threads

			L.isDebug and L.logDebug(f'Operation: {request.op}')
			L.isDebug and L.logDebug(f'Originator: {requestOriginator}')
			L.isDebug and L.logDebug(f'Authorization: {authResult}')

			responseResult = CSE.request.handleRequest(request)

			# Associate the connection with the originator, if not yet done.
			# wsOriginator is None if the connection is not yet associated with an originator, and this
			# can only be the case when the request is an AE registration
			if wsOriginator is None and (res := responseResult.resource) is not None and res.ty == ResourceTypes.AE:
				self.associateConnectionWithOriginator(websocket, res.aei)
				wsOriginator = res.aei

		except ResponseException as e:
			# something went wrong during dissection
			responseResult = Result(rsc = e.rsc, dbg = e.dbg, request = e.data)

		except Exception as e:
			responseResult = Result.exceptionToResult(e)

		# Don't send a response for "no response" response type
		# We have t use the dissectResult here, because the request object might not 
		# be fully initialized because of an exception
		if dissectResult.request.rt == ResponseType.noResponse:
			L.isDebug and L.logDebug('No response required')
			return
		
		# add, copy and update some fields from the original request
		responseResult.prepareResultFromRequest(request)

		_r, _data = prepareResultForSending(responseResult, isResponse = True, originalRequest = request)	
		L.isDebug and L.logDebug(f'WS Response <== ({str(_r.rsc)}):')

		L.logRequest(_r, _data) # type:ignore [arg-type]
		websocket.send(_data)


	def _handleAuthentication(self, websocket:WSConnection) -> AuthorizationResult:
		"""	Handle the authentication of a new connection.

			Args:
				websocket: The WebSocket connection.

			Returns:
				Eneumeration value of the result of the authentication.
		"""

		def testBasicAuthentication(auth:str) -> bool:
			"""	Validate the basic authentication.

				Args:
					auth: The authentication string as a base64 encoded string. The decoded string is expected to be in the format
						'username:password'.
			
				Return:
					True if the authentication is valid, False otherwise.
			"""
			# Decode the base64 encoded string and split it into username and password
			username, password = base64.b64decode(auth).decode().split(':')
			if not CSE.security.validateWSBasicAuth(username, password):
				L.isWarn and L.logWarn(f'Invalid username or password for basic authentication: {username}')
				return False
			return True
		

		def testTokenAuthentication(token:str) -> bool:
			"""	Validate the token.

				Args:
					token: The token to validate.
			
				Return:
					True if the token is valid, False otherwise.
			"""
			if not CSE.security.validateWSTokenAuth(token):
				L.isWarn and L.logWarn(f'Invalid token for token authentication: {token}')
				return False
			return True
		
		L.isDebug and L.logDebug('Checking authentication')
		authorization = websocket.request.headers.get('Authorization')
		if not (Configuration.websocket_security_enableBasicAuth or Configuration.websocket_security_enableTokenAuth):
			if authorization is not None:
				L.isWarn and L.logWarn('Basic or token authentication is not enabled, but an authorization header was found.')
			return AuthorizationResult.NOTSET
		
		if authorization is None:
			L.isDebug and L.logDebug('No authorization header found.')
			return AuthorizationResult.UNAUTHORIZED
		
		if authorization.startswith('Basic '):
			return AuthorizationResult.AUTHORIZED if testBasicAuthentication(authorization[6:]) else AuthorizationResult.UNAUTHORIZED
		elif authorization.startswith('Bearer '):
			return AuthorizationResult.AUTHORIZED if testTokenAuthentication(authorization[7:]) else AuthorizationResult.UNAUTHORIZED
		else:
			L.isWarn and L.logWarn(f'Unsupported authentication method: {authorization}')
			return AuthorizationResult.UNAUTHORIZED


	def sendWSRequest(self, request:CSERequest, url:str, ignoreResponse:bool) -> Result:
		"""	Send a request to another WebSocket server.

			Args:
				request: The request to send.
				url: The URL to send the request to.
				ignoreResponse: Flag whether to ignore the response.

			Returns:
				The result object of the request.
		"""

		def connectWS(target:str, ct:ContentSerializationType) -> Tuple[WSConnection, bool]:
			"""	Connect to a WebSocket server.

				Args:
					target: The target CSE to connect to, if any.
					ct: The content type to use for the connection.
				
				Returns:
					The WebSocket connection and a flag whether the connection is one that is initiated by the CSE.
			"""

			# TODO check whether we need a lock() here


			# Check whether the target is alredy associated with an established connection
			if target in self.associatedConnections:
				L.isDebug and L.logDebug(f'Sending request via established WS Connection to: {target}')
				webSocket = self.wsConnections.get(self.associatedConnections[target])
				self.incrementConnection(webSocket)	# Increment the counter for the connection
				return webSocket, False
		
			# From here on it is assumed that there is no established connection with the target
	
			# Check whether the url is the default unreachable target url.
			# If so, then no WS connection is established
			if url == Constants.defaultWebSocketSchema:
				raise TARGET_NOT_REACHABLE(L.logWarn(f'No WS connection established. Target is not reachable by default.'))	# No WS connection established

			# Construct addional headers
			additionalHeaders = { 'X-m2m-Origin': RC.cseCsi }	#  Always add the originator
			authResult = AuthorizationResult.NOTSET
			if request.credentials:	# Add the credentials if available
				if request.credentials.wsUsername and request.credentials.wsPassword:
					additionalHeaders['Authorization'] = request.credentials.getWsBasic()
					authResult = AuthorizationResult.AUTHORIZED	# Assume success. Otherwise, the connection would not be established anyway
				elif request.credentials.wsToken:
					additionalHeaders['Authorization'] = request.credentials.getWsBearerToken()
					authResult = AuthorizationResult.AUTHORIZED # Assume success. Otherwise, the connection would not be established anyway
				else:
					L.logWarn('No credentials for WS request found')


			# Else connect to the target WS server using the URL
			L.isDebug and L.logDebug(f'Establishing new temporary WS connection to send request to: {target}')
			try:
				websocket = connect(url, 
									subprotocols=[ct.toWSContentType()], 					# type:ignore[list-item]
									additional_headers = additionalHeaders)
			except Exception as e:
				raise TARGET_NOT_REACHABLE(L.logWarn(f'Error connecting to WS server: {url} - {e}'))
			
			# Associate the WS connection with the originator
			self.addConnection(websocket, True)
			self.associateConnectionWithOriginator(websocket, target) # In this case, the target is the originator

			BackgroundWorkerPool.runJob(lambda: self.receiveLoop(websocket, target, ct, authResult),
										name = f'ws_{uniqueID()}')
			return websocket, True


		def disconnectWS(target:str, doClose:bool) -> None:
			if doClose:
				L.isDebug and L.logDebug(f'Closing temporary WS connection to: {target}')
				self.closeConnectionForOriginator(target)

		try: 
			# Get the serialization format
			ct = request.ct if request.ct is not None else RC.defaultSerialization
			targetOriginator = csiFromSPRelative(request.to)
			if targetOriginator is None:
				targetOriginator = request.to

			# Connect to the target WS server. If the connection is already established, then use the existing connection.
			websocket, isSenderWS = connectWS(targetOriginator, ct)

			if websocket is None:
				return Result(rsc = ResponseStatusCode.TARGET_NOT_REACHABLE, dbg = 'No WS connection established')
			if websocket.protocol.state == State.CLOSED:
				# Remove the connection and try to establish a new one once
				L.isWarn and L.logWarn(f'WS connection to {targetOriginator} was closed. Trying to re-establish connection')
				self.removeConnection(websocket, targetOriginator)
				websocket, isSenderWS = connectWS(targetOriginator, ct)
				if websocket is None or websocket.protocol.state == State.CLOSED:
					return Result(rsc = ResponseStatusCode.TARGET_NOT_REACHABLE, dbg = 'No WS connection established')

		except ConnectionRefusedError as e:
			return Result(rsc = ResponseStatusCode.TARGET_NOT_REACHABLE, dbg = f'WS connection refused: {e}')
		
		req, url, urlParsed = createRequestResultFromURI(request, url)

		# Sending the request
		try:
			message = prepareResultForSending(req)[1]
			L.isDebug and L.logDebug(f'WS Request ==>: {targetOriginator if not isSenderWS else self._getWSSendingTargetName(targetOriginator)}')
			L.isDebug and L.logDebug(f'Body: {message!r}')
			websocket.send(message)
		except Exception as e:
			disconnectWS(targetOriginator, isSenderWS)
			return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, dbg = f'Error sending WS request: {e}')	

		# Ignore the response to notifications in some cases
		if ignoreResponse and request.op == Operation.NOTIFY:
			L.isDebug and L.logDebug('WS: Ignoring response to notification')
			disconnectWS(targetOriginator, isSenderWS)
			return createPositiveResponseResult()

		# Receiving the response
		resResp, _ = CSE.request.waitForResponse(req.request.rqi, Configuration.websocket_timeout)

		if resResp is None:
			disconnectWS(targetOriginator, isSenderWS)
			return Result(rsc = ResponseStatusCode.REQUEST_TIMEOUT, dbg = 'No response received within timeout')

		# Disconnect the WS connection if it is just a temporary connection
		disconnectWS(targetOriginator, isSenderWS)

		return resResp
