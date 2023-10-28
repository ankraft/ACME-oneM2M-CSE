 #
#	WebSocketServer.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Implementation of a WebSocket Server for a WebSocket Mcx binding implementation.
"""

from __future__ import annotations
from typing import Optional, Any
import logging

from websockets.sync.server import WebSocketServer as WSServer, serve, ServerConnection
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..etc.RequestUtils import prepareResultForSending
from ..etc.Utils import renameThread, exceptionToResult, uniqueID
from ..etc.Types import ContentSerializationType, Result, CSERequest
from ..etc.ResponseStatusCodes import ResponseStatusCode, ResponseException
from ..services.Configuration import Configuration
from ..services import CSE
from ..services.Logging import Logging as L


# TODO associations: originator -> websocket.id
# TODO security TLS etc
# TODO record WS requests
# TODO add WS to test suite

class WebSocketServer(object):

	__slots__ = [ 
		'enable', 
		'interface',
		'port', 
		'logLevel',
		'isPaused', 
		'websocketServer', 
		'wsConnections', 
		'associations', 
		'actor'
	]

	def __init__(self) -> None:

		# Get the configuration settings
		self._assignConfig()

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)		# type: ignore

		self.isPaused = False
		self.websocketServer:Optional[WSServer] = None
		self.wsConnections:dict[str, ServerConnection] = {}
		self.associations:dict[str, str] = {}	# originator -> websocket.id

# TODO restart: close all connections, restart server (shutdown and run again)


	def shutdown(self) -> bool:
		"""	Shutdown the WebSocket server.
		"""
		L.isInfo and L.log('Shutdown WebSocket server')
		# TODO close all connections
		self._stop()
		return True


	def _assignConfig(self) -> None:
		"""	Store relevant configuration values in the manager.
		"""
		self.enable = Configuration.get('websocket.enable')
		self.port = Configuration.get('websocket.port')
		self.interface = Configuration.get('websocket.listenIF')
		self.logLevel = Configuration.get('websocket.loglevel')


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
						'websocket.loglevel'
					  ]:
			return

		# assign new values
		self._assignConfig()

		# TODO restart server if necessary


	def run(self) -> bool:
		"""	Initialize and run the WebSocket server as a BackgroundWorker/Actor.
		"""
		if not self.enable:
			L.isInfo and L.log('WebSocket: server NOT enabled')
			return True
		# Actually start the actor to run the WebSocket Server as a thread
		self.actor = BackgroundWorkerPool.newActor(self._run, name = 'WSServer').start()

		L.isInfo and L.log('Start WebSocket server')
		return True


	def _run(self) -> None:
		"""	WebSocket server main loop.
		"""
		self.websocketServer = serve(self.handleConnection, 
							   		 self.interface, 
									 self.port, 
									 subprotocols = ContentSerializationType.supportedContentSerializationsWS()) # type:ignore[list-item]	
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
		self.isStopped = True
		
	
	def unpause(self) -> None:
		"""	Continue handling requests.
		"""
		L.isInfo and L.log('WS server unpaused')
		self.isStopped = False


	def addConnection(self, websocket:ServerConnection) -> None:
		"""	Add a new connection to the list of connections.

			Args:
				websocket: The WebSocket connection.
		"""
		L.isDebug and L.logDebug(f'Adding new WS connection: {websocket.id}')
		self.wsConnections[websocket.id] = websocket


	def associateConnectionWithOriginator(self, websocket:ServerConnection, originator:str) -> None:
		"""	Associate a connection with an originator.

			Args:
				websocket: The WebSocket connection.
				originator: The originator.
		"""
		L.isDebug and L.logDebug(f'Associating WS connection {websocket.id} with originator {originator}')
		# TODO check if originator is already associated with another connection ??? What should be the behaviour then?
		self.associations[originator] = websocket.id	


	def removeConnection(self, websocket:ServerConnection, originator:str) -> None:
		"""	Remove a connection from the list of connections.
			Also remove the association between the connection and the originator.

			Args:
				websocket: The WebSocket connection.
				orignator: The originator.
		"""
		L.isDebug and L.logDebug(f'Removing WS connection: {websocket.id} and originator {originator}')
		if websocket.id in self.wsConnections:
			del self.wsConnections[websocket.id]
		if originator in self.associations:
			del self.associations[originator]


	def handleConnection(self, websocket:ServerConnection) -> None:
		"""	Handle a new WebSocket connection. This connection stays open until the client closes it, or the
			server is stopped.

			Args:
				websocket: The WebSocket connection.
		"""

		def _handleReceivedMessage(websocket:ServerConnection, message:str|bytes) -> None:
			"""	Handle a received message. This is the main entry point for handling a received message.

				Args:
					websocket: The WebSocket connection.
					message: The received message.
			"""
			nonlocal originator

			# TODO improve originator handling: add originator after registration as well!

			L.isDebug and L.logDebug(f'==> WS Request: {originator}')
			L.isDebug and L.logDebug(f'Body: {message}')

			request:CSERequest = None
			try:
				if isinstance(message, str):
					message = message.encode()
				
				dissectResult = CSE.request.dissectRequestFromBytes(message, contentType)
				request = dissectResult.request

				# Associate the connection with the originator
				# TODO as well for registration (then this originator here is wrong)
				if originator is None:
					originator = request.originator
					self.associateConnectionWithOriginator(websocket, originator)

				L.isDebug and L.logDebug(f'Operation: {request.op}')
				L.isDebug and L.logDebug(f'Originator: {originator}')

				try:
					responseResult = CSE.request.handleRequest(request)
				except Exception as e:
					responseResult = exceptionToResult(e)

				# add, copy and update some fields from the original request
				responseResult.prepareResultFromRequest(request)

			except ResponseException as e:
				# something went wrong during dissection
				responseResult = Result(rsc = e.rsc, dbg = e.dbg, request = e.data)
				responseResult.prepareResultFromRequest(request)

			# TODO	CSE.request.recordRequest(dissectResult.request, dissectResult)

			_r, _data = prepareResultForSending(responseResult, isResponse = True)	
			L.isDebug and L.logDebug(f'WS Response <== ({str(_r.rsc)}):')

			L.logRequest(_r, _data) # type:ignore [arg-type]
			websocket.send(_data)			


		def _checkIsServerRunning() -> bool:
			"""	Check if the server is running. If not, send an error message to the client.

				Returns:
					True if the server is running, False otherwise.
			"""
			if self.isPaused:
				_, _data = prepareResultForSending(Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, dbg = 'WebSocket server is not running').prepareResultFromRequest(),
									   			isResponse = True)	
				websocket.send(_data)
				return False
			return True

		# Rename thread
		renameThread(prefix = 'ws')

		if not _checkIsServerRunning():
			return

		# Variable for this connection originator
		originator = None	# This is valid until the first message is received. Then the originator is determined from the message


		L.isDebug and L.logDebug('New WS connection')
		L.logDebug(f'Received: {websocket.subprotocol}')
		# L.logDebug(f'Received: {websocket.remote_address}')
		L.logDebug(f'Received: {websocket.request}')

		# Determine the content type.
		# The negotiation is done by the server part already. The subprotocol is determined by the client.
		subprotocol = websocket.subprotocol
		contentType = ContentSerializationType.fromWebSocketSubProtocol(subprotocol)

		# Add the connection to the list of unassociated connections
		self.addConnection(websocket)

		try:
			# Handle incoming requests in separate threads as long as there is no error or the server is stopped
			# or the client closes the connection
			while (message := websocket.recv()) is not None:	# rev() is blocking
				if not _checkIsServerRunning():
					continue
				BackgroundWorkerPool.runJob(lambda: _handleReceivedMessage(websocket, message), name = f'ws_{uniqueID()}')
		except ConnectionClosedError as e:
			L.isWarn and L.logWarn('Connection closed: {e}')
		except ConnectionClosedOK:
			L.isDebug and L.logDebug('Connection closed by client')
		
		# Remove the connection from the list of unassociated connections or from the list of associated connections
		self.removeConnection(websocket, originator)

