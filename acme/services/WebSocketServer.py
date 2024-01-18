 #
#	WebSocketServer.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Implementation of a WebSocket Server for a WebSocket Mcx binding implementation.
"""

from __future__ import annotations
from typing import Optional, Any, cast
import logging, uuid
from urllib.parse import urlparse

from websockets.sync.connection import Connection as WSConnection
from websockets.sync.server import WebSocketServer as WSServer, serve, ServerConnection
from websockets.sync.client import connect
from websockets.protocol import State
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..etc.RequestUtils import prepareResultForSending
from ..etc.Utils import renameThread, exceptionToResult, uniqueID, isValidAEI, toSPRelative, csiFromSPRelative, uniqueRI
from ..etc.DateUtils import getResourceDate
from ..etc.Types import ContentSerializationType, Result, CSERequest, Operation, ResourceTypes, RequestType
from ..etc.ResponseStatusCodes import ResponseStatusCode, ResponseException
from ..services.Configuration import Configuration
from ..services import CSE
from ..resources.Resource import Resource
from ..services.Logging import Logging as L


# TODO associations: originator -> websocket.id
# TODO security TLS etc
# TODO record WS requests
# TODO add WS to test suite
# TODO add events for WS connections
# TODO add statistics for WS connections

class WebSocketServer(object):
	"""	WebSocket Server implementation.
	"""

	__slots__ = [ 
		'enable', 
		'interface',
		'port', 
		'logLevel',
		'requestTimeout',
		'isPaused', 
		'websocketServer', 
		'wsConnections', 
		'associatedConnections', 
		'actor'
	]
	""" Define slots for instance variables. """


	def __init__(self) -> None:
		"""	Initialization of the WebSocket Server.
		"""

		# Get the configuration settings
		self._assignConfig()

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)			# type: ignore

		# Add a handler for resource deletion
		CSE.event.addHandler(CSE.event.deleteResource, self.handleDeleteEvent)	# type: ignore

		self.isPaused = False
		"""	Flag whether the server is currently paused. Requests are not handled when the server is paused. """
		self.websocketServer:Optional[WSServer] = None
		"""	The WebSocket server object. """
		self.wsConnections:dict[uuid.UUID, WSConnection] = {}	# websocket.id -> websocket
		"""	The list of currently handled WebSocket connections. """
		self.associatedConnections:dict[str, uuid.UUID] = {}		# originator -> websocket.id
		"""	The list of currently handled WebSocket connections, associated with an originator. """
		L.isInfo and L.log('WebSocket server initialized')


# TODO restart: close all connections, restart server (shutdown and run again)


	def shutdown(self) -> bool:
		"""	Shutdown the WebSocket server.
		"""
		L.isInfo and L.log('WebSocket server shut down')
		# TODO close all connections
		self._stop()
		return True


	def _assignConfig(self) -> None:
		"""	Store relevant configuration values in the manager.
		"""
		self.enable = Configuration.get('websocket.enable')
		"""	Flag whether the WebSocket server is enabled. """

		self.port = Configuration.get('websocket.port')
		"""	The port the WebSocket server is listening on."""

		self.interface = Configuration.get('websocket.listenIF')
		"""	The interface the WebSocket server is listening on."""

		self.logLevel = Configuration.get('websocket.loglevel')
		"""	The log level for the WebSocket server."""

		self.requestTimeout = Configuration.get('websocket.timeout')
		"""	The timeout for requests."""


	def configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Optional[Any] = None) -> None:
		"""	Callback for the `configUpdate` event.
			
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

		# assign new values
		self._assignConfig()

		# TODO restart server if necessary


	def handleDeleteEvent(self, name:str, deletedResource:Resource) -> None:
		"""	Callback and handler for the *deleteResource* event.

			In case of an AE deletion, the associated WS connection is dissociated, but left open.

			Args:
				name: Event name.
				deletedResource: The deleted resource.
		"""

		if deletedResource.ty != ResourceTypes.AE or deletedResource.aei not in self.associatedConnections:
			return
		self.dissociateConnectionFromOriginator(deletedResource.aei)


	def run(self) -> bool:
		"""	Initialize and run the WebSocket server as a BackgroundWorker/Actor.
		"""
		if not self.enable:
			L.isInfo and L.log('WebSocket: server NOT enabled')
			return True
		# Actually start the actor to run the WebSocket Server as a thread
		self.actor = BackgroundWorkerPool.newActor(self._run, name = 'WSServer').start()
		"""	The actor for running the synchronous WebSocket server in the background. """

		L.isInfo and L.log('Start WebSocket server')
		return True


	def _run(self) -> None:
		"""	WebSocket server main loop.
		"""
		self.websocketServer = serve(self.handleIncomingConnection, 
							   		 self.interface, 
									 self.port, 
									 subprotocols = ContentSerializationType.supportedContentSerializationsWS(), # type:ignore[arg-type]
									 ssl_context = CSE.security.getSSLContextWs()) # type:ignore[list-item]	
		logging.getLogger('websockets.server').setLevel(self.logLevel)
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


	def addConnection(self, websocket:WSConnection) -> None:
		"""	Add a new connection to the list of connections.

			Args:
				websocket: The WebSocket connection.
		"""
		L.isDebug and L.logDebug(f'Adding new WS connection: {websocket.id}')
		self.wsConnections[websocket.id] = websocket


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
		L.isDebug and L.logDebug(f'Closing WS connection for originator {originator}')
		if originator in self.associatedConnections:
			websocketID = self.associatedConnections[originator]

			# Also remove from the list of websocket connections
			if websocketID in self.wsConnections:
				websocket = self.wsConnections[websocketID]
				websocket.close()
				self.removeConnection(websocket, originator)
			

	def _checkIsServerRunning(self, websocket:WSConnection) -> bool:
		"""	Check if the server is running. If not, send an error message to the client.

			Returns:
				True if the server is running, False otherwise.
		"""
		if self.isPaused:
			websocket.send('WebSocket server is not running')
			return False
		return True


	def receiveLoop(self, websocket:WSConnection, wsOriginator:str, ct:ContentSerializationType) -> None:
		"""	Receive loop for the WebSocket server. This is the main entry point for handling a received message,
			whether the connection was initiated by the server or the client.

			Args:
				websocket: The WebSocket connection.
				wsOriginator: The originator of the connection.
				ct: The content type.
		"""
		try:	
			# Handle incoming requests in separate threads as long as there is no error or the server is stopped
			# or the client closes the connection
			while (message := websocket.recv()) is not None:	# recv() is blocking
				# L.isDebug and L.logDebug(f'Received WS message: {message}')
				if not self._checkIsServerRunning(websocket):
					continue
				# Run the message handling in a separate thread
				BackgroundWorkerPool.runJob(lambda: self._handleReceivedMessage(websocket, message, wsOriginator, ct), name = f'ws_{uniqueID()}')
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
		renameThread(prefix = 'ws')

		if not self._checkIsServerRunning(websocket):
			return

		L.isDebug and L.logDebug('New WS connection')
		L.logDebug(f'Received subprotocol: {websocket.subprotocol}')
		L.logDebug(f'Received headers: {websocket.request.headers}')
		L.logDebug(f'Received request: {websocket.request}')

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
				BackgroundWorkerPool.runJob(lambda: self._handleReceivedMessage(websocket, message, wsOriginator, contentType),
											name = f'ws_{uniqueID()}')
		except ConnectionClosedError as e:
			L.isWarn and L.logWarn('Connection closed: {e}')
		except ConnectionClosedOK:
			L.isDebug and L.logDebug('Connection closed by client')
		
		# Remove the connection from the list of unassociated connections or from the list of associated connections
		self.removeConnection(websocket, wsOriginator)


	def _handleReceivedMessage(self, websocket:WSConnection, message:str|bytes, wsOriginator:str, contentType:ContentSerializationType) -> None:
		"""	Handle a received message. This is the main entry point for handling a received message, whether the
			message is a request or a response.

			Args:
				websocket: The WebSocket connection.
				message: The received message.
				wsOriginator: The originator of the connection.
				contentType: The content type.
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
											dbg = L.logWarn(f'Unknown WS connection (no X-M2M-Origin header) are only allowed for AE registrations'))
				# Else, the request must be an AE registration

			# Compare the originator and the from, only for Mca
			if wsOriginator is not None and isValidAEI(wsOriginator):
				if toSPRelative(requestOriginator) != toSPRelative(wsOriginator):
					raise ResponseException(ResponseStatusCode.ORIGINATOR_HAS_NO_PRIVILEGE, 
											dbg = L.logWarn(f'Originator mismatch: {requestOriginator} != {wsOriginator}'))

			L.isDebug and L.logDebug(f'Operation: {request.op}')
			L.isDebug and L.logDebug(f'Originator: {requestOriginator}')

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
				responseResult = exceptionToResult(e)

		# add, copy and update some fields from the original request
		responseResult.prepareResultFromRequest(request)

		# TODO	CSE.request.recordRequest(dissectResult.request, dissectResult)

		_r, _data = prepareResultForSending(responseResult, isResponse = True)	
		L.isDebug and L.logDebug(f'WS Response <== ({str(_r.rsc)}):')

		L.logRequest(_r, _data) # type:ignore [arg-type]
		websocket.send(_data)
	

	def sendWSRequest(self, request:CSERequest, url:str) -> Result:
		"""	Send a request to another WebSocket server.

			Args:
				request: The request to send.
				url: The URL to send the request to.

			Returns:
				The result object of the request.
		"""

		def connectWS(target:str, ct:ContentSerializationType) -> WSConnection:
			"""	Connect to a WebSocket server.

				Args:
					target: The target to connect to.
					ct: The content type to use for the connection.
				
				Returns:
					The WebSocket connection.
			"""
			# Check whether we already have an established connection to the target. Otherwise establish a new WS connection
			websocket:WSConnection = None
			if target not in self.associatedConnections:
				websocket = connect(url, 
									subprotocols=[ct.toWSContentType()], 					# type:ignore[list-item]
									additional_headers = { 'X-m2m-origin': CSE.cseCsi})
				self.addConnection(websocket)
				self.associateConnectionWithOriginator(websocket, target) # In this case, the target is the originator
				BackgroundWorkerPool.runJob(lambda: self.receiveLoop(websocket, target, ct),
											name = f'ws_{uniqueID()}')
			else:
				websocket = self.wsConnections[self.associatedConnections[target]]
			return websocket

		try: 
			# Get the serialization format first
			ct = request.ct if request.ct is not None else CSE.defaultSerialization
			target = csiFromSPRelative(request.to)

			websocket = connectWS(target, ct)

			if websocket is None:
				return Result(rsc = ResponseStatusCode.TARGET_NOT_REACHABLE, dbg = 'No WS connection established')
			if websocket.protocol.state == State.CLOSED:
				# Remove the connection and try to establish a new one once
				L.isWarn and L.logWarn(f'WS connection to {target} was closed. Trying to re-establish connection')
				self.removeConnection(websocket, target)
				websocket = connectWS(target, ct)
				if websocket is None or websocket.protocol.state == State.CLOSED:
					return Result(rsc = ResponseStatusCode.TARGET_NOT_REACHABLE, dbg = 'No WS connection established')

		except ConnectionRefusedError as e:
			return Result(rsc = ResponseStatusCode.TARGET_NOT_REACHABLE, dbg = f'WS connection refused: {e}')
		
		# TODO optimize this. Same code is in MQTTServer.py
		u = urlparse(url)
		req 					= Result(request = request)
		req.request.id			= u.path[1:] if u.path[1:] else req.request.to
		req.resource			= req.request.pc
		req.request.rqi			= uniqueRI()
		if req.request.rvi != '1':
			req.request.rvi		= req.request.rvi if req.request.rvi is not None else CSE.releaseVersion
		req.request.ot			= getResourceDate()
		req.rsc					= ResponseStatusCode.UNKNOWN								# explicitly remove the provided OK because we don't want have any
		req.request.ct			= req.request.ct if req.request.ct else CSE.defaultSerialization 	# get the serialization


		# Sending the request
		try:
			message = prepareResultForSending(req)[1]
			L.isDebug and L.logDebug(f'WS Request ==>: {target}')
			L.isDebug and L.logDebug(f'Body: {message!r}')
			websocket.send(message)
		except Exception as e:
			return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, dbg = f'Error sending WS request: {e}')	

		# Receiving the response
		resResp, _ = CSE.request.waitForResponse(req.request.rqi, self.requestTimeout)

		if resResp is None:
			return Result(rsc = ResponseStatusCode.REQUEST_TIMEOUT, dbg = 'No response received within timeout')

		# TODO Log request

		return resResp
