#
#	wsrequests.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	WebSocket requests and utility functions
#

from config import *
import json, random, sys, threading, queue
from rich import print, rule
from websockets.sync.client import connect, ClientConnection
from websockets.sync.server import WebSocketServer as WSServer, serve, ServerConnection


_websocket:ClientConnection = None
""" The main WebSocket connection to send requests. """
_updateWebsocket:ClientConnection = None
""" The WebSocket connection to send update requests. """
_websocketServer:WSServer = None
""" The WebSocket server to receive notifications. """
_notifications:queue.Queue = queue.Queue()
""" The queue to store received notifications. """


def _printSend(request:dict, reason:str = None, websocket:ClientConnection = None) -> dict:
	""" Print the request.
	
		Args:	
			request: The request to print.
			reason: The reason for the request.
			websocket: The websocket connection.

		Returns:
			The request.
	"""
	print('\n', rule.Rule(f'Request{": " + reason if reason else ""}', style='green1 dim'))
	if websocket:
		print(websocket.request.headers, request)
	else:
		print(request)
	return request


def _printRecv(response:dict, reason:str = 'Response') -> dict:
	""" Print the response.

		Args:
			response: The response to print.
			reason: The reason for the response.

		Returns:
			The response.
	"""
	print('\n', rule.Rule(reason, style='orange1 dim'))
	print(response)
	return response


def _uniqueID() -> str:
	""" Create a unique ID.

		Returns:
			A unique ID.
	"""
	return str(random.randint(1,sys.maxsize))


def openConnection(originator:str = None) -> None:
	""" Open a new WebSocket connection.
	
		Args:
			originator: The originator to use for the connection.
	"""
	global _websocket
	_websocket = connect(cseUrl, 
					 	subprotocols=[subProtocol], 
						additional_headers = { 'X-M2M-Origin': originator } if originator else {})
	print(f'\n[yellow]>>> Connected to WebSocket server at [bold]{cseUrl}[/bold] with originator [bold]{originator}[/bold]')
	

def closeConnection() -> None:
	""" Close the WebSocket connection.
	"""
	global _websocket
	if _websocket:
		_websocket.close()
		_websocket = None
		print(f'\n[yellow]>>> Disconnected from WebSocket server at [bold]{cseUrl}[/bold]')


def openUpdateConnection(originator:str = None) -> None:
	""" Open a new WebSocket connection for updates. This is a separate connection to the CSE for sending updates from a different originator.

		Args:
			originator: The originator to use for the connection.
	"""
	global _updateWebsocket
	_updateWebsocket = connect(cseUrl, 
						 	   subprotocols=[subProtocol], 
							   additional_headers = { 'X-M2M-Origin': originator } if originator else {})
	print(f'\n[yellow]>>> (Updates) Connected to WebSocket server at [bold]{cseUrl}[/bold] with originator [bold]{originator}[/bold]')


def closeUpdateConnection() -> None:
	""" Close the WebSocket connection for updates.
	"""
	global _updateWebsocket
	if _updateWebsocket:
		_updateWebsocket.close()
		_updateWebsocket = None
		print(f'\n[yellow]>>> (Updates) Disconnected from WebSocket server at [bold]{cseUrl}[/bold]')


def _doRequest(request:dict, originator:str = None, reason:str = None, websocket:ClientConnection = None) -> dict:
	""" Send a request and receive the response.

		Args:
			request: The request to send.
			originator: The originator to use for the request.
			reason: The reason for the request.
			websocket: The websocket connection to use for the request.

		Returns:
			The received response.
	"""
	websocket.send(json.dumps(_printSend(request, reason, websocket)))
	try:
		while True:
			if (response := _printRecv(json.loads(websocket.recv(timeout = timeout)))):
				return response
			else:
				continue
	except Exception as e:
		print(e)
	return None


def receiveNotification(originator:str = None) -> dict:
	""" Receive a notification. If no originator is given, the notification server is used to receive the notification.

		Args:
			originator: The originator for to use for the notification.

		Returns:
			The received notification.
	"""
	if not originator and _websocketServer:
		# Use the notification queue to receive the notification
		while True:
			if not _notifications.empty():
				return _notifications.get()
			else:
				continue
	else:
		# Use the existing connection to receive the notification

		try:
			while True:
				if (request := _printRecv(json.loads(_websocket.recv(timeout = timeout)), 'Received Notification')):
					if request['pc'].get('m2m:sgn'):
						# This is a notification, send response
						response = {
							'fr': request['to'],
							'to': request['fr'],
							'rqi': request['rqi'],
							'rvi': request['rvi'],
							'rsc': 2000
						}
						_websocket.send(json.dumps(_printSend(response, 'Send Notification Response')))
					return request
				else:
					continue
		except Exception as e:
			print(e)
		return None


def startNotificationServer(doRespond:bool = True) -> None:
	""" Start the notification server.

		Args:
			originator: The originator for to use for the notification.
	"""
	global _websocketServer

	stopNotificationServer()

	def _handleNotification(websocket:ServerConnection) -> None:
		_printRecv(request := json.loads(websocket.recv()), 'Received Notification via standalone WS server')
		_notifications.put(request)

		if doRespond:
			# Send response

			response = {
				'fr': request['to'],
				'to': request['fr'],
				'rqi': request['rqi'],
				'rvi': request['rvi'],
				'rsc': 2000
			}
			websocket.send(json.dumps(_printSend(response, 'Send Notification Response via standalone WS server')))

	def _runNotificationServer() -> None:
		with _websocketServer as server:
			print(f'\n[yellow]>>> Notification server started at [bold]{notificationHost}:{notificationPort}[/bold]')
			server.serve_forever()	# Will block until the server is shutdown
			print(f'\n[yellow]>>> WebSocket Notification server stopped')

	# Start the notification server
	_websocketServer = serve(_handleNotification,
							 notificationHost,
							 notificationPort,
							 subprotocols = [ subProtocol ]) # type:ignore[arg-type]

	threading.Thread(target=_runNotificationServer).start()


def stopNotificationServer() -> None:
	""" Stop the notification server.
	"""
	global _websocketServer
	if _websocketServer:
		print(f'\n[yellow]>>> Stopping WebSocket server')
		_websocketServer.shutdown()
		_websocketServer = None

#
#	Specific requests
#

def registerAE(originator:str = None, poa:str = None) -> dict:
	""" Register an AE.

		Args:
			originator: The originator to use for the request.
			poa: The point of access for the AE.

		Returns:
			The received response.
	"""
	registerRequest = {
		'to': 'cse-in',
		'op': 1,
		'rqi': _uniqueID(),
		'rvi': '4',
		'ty': 2,
		'pc': {
			'm2m:ae': {
				'api': 'NmyApp',
				'rr': True,
				'rn': aeName,
				'srv': [ '3', '4' ],
			}}
	}
	if originator:
		registerRequest['fr'] = originator
		reason = 'register AE'
	else:
		reason = 'register AE without originator'
	if poa:
		registerRequest['pc']['m2m:ae']['poa'] = [ poa ]
	return _doRequest(registerRequest, originator, reason, websocket=_websocket)


def unregisterAE(rn:str, originator:str = None, reason:str = 'Unregister AE') -> dict:
	""" Unregister an AE.
	
		Args:
			rn: The resource name of the AE to unregister.
			originator: The originator to use for the request.
			reason: The reason for the request.

		Returns:
			The received response.
	"""
	unregisterRequest = {
		'to': f'cse-in/{rn}',
		'op': 4,
		'rqi': _uniqueID(),
		'rvi': '4',
	}
	if originator:
		unregisterRequest['fr'] = originator

	return _doRequest(unregisterRequest, originator, reason, _websocket)


def updateAE(rn:str, originator:str = None, reason:str = 'Update AE') -> dict:
	""" Update an AE.
	
		Args:
			rn: The resource name of the AE to update.
			originator: The originator to use for the request.
			reason: The reason for the request.
			
		Returns:
			The received response.
	"""
	updateRequest = {
		'to': f'cse-in/{rn}',
		'op': 3,
		'rqi': _uniqueID(),
		'rvi': '4',
		'pc': {
			'm2m:ae': {
				'lbl': ['newLabel'],
			}}
	}
	if originator:
		updateRequest['fr'] = originator
	return _doRequest(updateRequest, originator, reason, _updateWebsocket)


def createContainer(rn:str, originator:str = None, reason:str = 'Create Container') -> dict:
	""" Create a container.
	
		Args:
			rn: The resource name of the container to create.
			originator: The originator to use for the request.
			reason: The reason for the request.

		Returns:
			The received response.
	"""
	createRequest = {
		'to': f'cse-in/{aeName}',
		'op': 1,
		'rqi': _uniqueID(),
		'rvi': '4',
		'ty': 3,
		'pc': {
			'm2m:cnt': {
				'rn': rn,
			}}
	}
	if originator:
		createRequest['fr'] = originator

	return _doRequest(createRequest, originator, reason)


def createSubscription(rn:str, originator:str = None, reason:str = 'Create Subscription', nu:str = None) -> dict:
	""" Create a subscription. The subscription is created for the AE.
	
		Args:
			rn: The resource name of the subscription to create.
			originator: The originator to use for the request.
			reason: The reason for the request.

		Returns:
			The received response.
	"""
	createRequest = {
		'to': f'cse-in/{aeName}',
		'op': 1,
		'rqi': _uniqueID(),
		'rvi': '4',
		'ty': 23,
		'pc': {
			'm2m:sub': {
				'rn': rn,
				'nu': [ originator if not nu else nu ],
			}}
	}
	if originator:
		createRequest['fr'] = originator

	return _doRequest(createRequest, originator, reason, _websocket)


def cleanup(rn:str, originator:str = adminOriginator) -> None:
	""" Clean up the resources and connections.
	
		Args:
			rn: The resource name of the AE to unregister.
			originator: The originator to use for the request.
	"""
	closeUpdateConnection()
	openConnection(originator)
	expectRSC(unregisterAE(rn, originator, 'unregister AE (cleanup)'), 2002, 'Unregister AE', doexit = False)
	closeConnection()
	stopNotificationServer()


#
#	Helper functions for the tests.
#

def expectRSC(response:dict, expectedRsc:int, msg:str, doexit:bool = True, cleanup:callable = None) -> None:
	""" Expect a specific response status code and print the result.

		If the response status code is not the expected one, the program is exited.
	
		Args:
			response: The response to check.
			expectedRsc: The expected response status code.
			msg: The message to print.
			doexit: Whether to exit the program after the check.
			cleanup: The cleanup function to call after the check.
	"""
	if (r := response['rsc']) != expectedRsc:
		print(f'[red]{msg}: Expected RSC={expectedRsc}, got {r}')
		closeConnection()
		if doexit:
			if cleanup:
				cleanup()
			exit()
	else:
		print(f'[green1]OK')


def getOriginator(dct:dict) -> str:
	""" Get the originator from a response.

		Args:
			dct: The response to get the originator from.

		Returns:
			The originator.
	"""
	return dct['pc']['m2m:ae']['aei']

