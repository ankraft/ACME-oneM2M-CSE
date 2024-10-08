#
#	webUI.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	WebUI for the ACME CSE
#

""" This module defines the web user interface for the ACME CSE.
"""

from __future__ import annotations
from typing import Callable, Optional

import flask, sys, argparse, logging, ssl, collections, time, webbrowser
from rich.console import Console
import requests
from flask import Flask, request
from werkzeug.wrappers import Response
from werkzeug.serving import WSGIRequestHandler


FlaskHandler = 	Callable[[str], Response]
""" Type definition for flask handler. """


class WebUI(object):
	"""	The web user interface for the ACME CSE.
	"""

	def __init__(self, app:Flask, 
					   defaultRI:str, 
					   defaultOriginator:str, 
					   root:Optional[str] = '/webui', 
					   webuiDirectory:Optional[str] = '.', 
					   redirectURL:Optional[str] = None, 
					   version:Optional[str] ='',
					   httpRoot:Optional[str] = '') -> None:
		"""	Initialize the web user interface.

			Args:
				app: The flask app.
				defaultRI: The default CSE RI.
				defaultOriginator: The default originator.
				root: The root for the web UI.
				webuiDirectory: The directory for the web UI.
				redirectURL: The URL to redirect to.
				version: The version of the web UI.
				httpRoot: The root for the HTTP server.
		"""

		# Register the endpoint for the web UI
		self.flaskApp 			= app
		""" The flask app. """

		self.webuiRoot 			= root
		""" The root for the web UI. """

		self.defaultRI 			= defaultRI
		""" The default CSE RI. """

		self.defaultOriginator	= defaultOriginator
		""" The default originator. """

		self.webuiDirectory 	= f'{webuiDirectory}/web'
		""" The directory for the web UI. """
		
		self.redirectURL 		= redirectURL
		""" The URL to redirect to. """

		self.version 			= version
		""" The version of the web UI. """

		self.httpRoot 			= httpRoot
		""" The root for the HTTP server. """
		
		self.oauthToken:Token	= None
		""" The oauth token. """

		# Append / if necessary
		if self.redirectURL is not None and self.redirectURL[-1] != '/':
			self.redirectURL += '/'

		self.addEndpoint(self.webuiRoot, handler = self.handleWebUIGET, methods = ['GET'])
		self.addEndpoint(f'{self.webuiRoot}/<path:path>', handler = self.handleWebUIGET, methods = ['GET'])
		self.addEndpoint(f'{httpRoot}/', handler = self.redirectRoot, methods = ['GET'])
		self.addEndpoint(f'{self.webuiRoot}/__version__', handler = self.getVersion, methods = ['GET'])

		if self.redirectURL:
			print("will redirect" + self.redirectURL)
			self.addEndpoint('/<path:path>', handler = self.proxy, methods = ['GET', 'POST', 'PUT', 'DELETE'])
		
		logging.getLogger("requests").setLevel(logging.WARNING)
		logging.getLogger("urllib3").setLevel(logging.WARNING)


	def addEndpoint(self, endpoint:Optional[str] = None, 
						  endpoint_name:Optional[str] = None, 
						  handler:Optional[FlaskHandler] = None, 
						  methods:Optional[list[str]] = None, 
						  strictSlashes:Optional[bool] = True) -> None:
		"""	Add an endpoint to the web UI.

			Args:
				endpoint: The endpoint.
				endpoint_name: The name of the endpoint.
				handler: The handler for the endpoint.
				methods: The methods for the endpoint.
				strictSlashes: Whether to use strict slashes.
		"""
		self.flaskApp.add_url_rule(endpoint, endpoint_name, handler, methods = methods, strict_slashes = strictSlashes)


	def redirectRoot(self, path:str = None) -> Response:
		"""	Redirect request to / to webui.

			Args:
				path: The path.
				
			Returns:
				The response.
		"""
		print(f'Forwarding {request.method.upper()} request {request.url}')
		return flask.redirect(f'{self.webuiRoot}{"?" + request.query_string.decode() if request.query_string else ""}', code = 302)


	def getVersion(self, path:str = None) -> Response:
		"""	Get the version of the web UI.

			Args:
				path: The path.
				
			Returns:
				The response.
		"""	
		return Response(self.version)


	def handleWebUIGET(self, path:str = None) -> Response:
		""" Handle a GET request for the web GUI. 

			Args:
				path: The path.
				
			Returns:
				The response.
		"""

		# security check whether the path will under the web root

		if not f'{self.webuiRoot}/{request.path}'.startswith(self.webuiRoot):
			return Response(status = 404)

		# Redirect to index file. Also include base / cse RI
		# if path == None or len(path) == 0 or (path.endswith('index.html') and len(request.args) != 2):
		if not path:
			# print(f'{self.webuiRoot}/index.html?ri=/{self.defaultRII}&or={self.defaultOriginator}')
			return flask.redirect(f'{self.webuiRoot}/index.html?ri={self.defaultRI}&or={self.defaultOriginator}{"&hr=" + self.httpRoot}{"&" + request.query_string.decode() if request.query_string else ""}', code = 302)
		else:
			filename = f'{self.webuiDirectory}/{path}'	# return any file in the web directory
		try:
			return flask.send_file(filename)
		except Exception as e:
			print(str(e))
			return flask.abort(404)


	# Proxy method from: https://stackoverflow.com/a/36601467/4799
	def proxy(self, *args, **kwargs) -> Response:	# type: ignore
		"""	Proxy a request to another server.

			Args:
				args: The arguments.
				kwargs: The keyword arguments.

			Returns:
				The response.
		"""
		print(request.host_url)
		print(self.redirectURL)
		url = request.url.replace(request.host_url, self.redirectURL)
		if doLogging and console:
			console.log('[dim]--------------------------------------------------')
			console.log(f'Forwarding {request.method.upper()} request to {url}')
		
		# Remove some headers.
		requestHeaders = { key: value for (key, value) in request.headers if key not in [ 'Host', 'If-None-Match', 'If-Match' ] }
		if doLogging and console:
			console.log(f'[dark_orange]Request')
			console.log(requestHeaders)		# Don't include a possible authorization header in log
		
		# Retrieve / refresh an oauth token (if configured)
		if doOauth:
			if (token := getOAuthToken(self.oauthToken)) is None:
				if doLogging:
					console.log(f'Error retrieving oauth token')
				return Response('', 500)
			self.oauthToken = token
			requestHeaders['Authorization'] = f'Bearer {self.oauthToken.token}'	

		resp = requests.request(
			method=request.method,
			url=url,
			headers=requestHeaders,
			data=request.get_data(),
			cookies=request.cookies,
			allow_redirects=False)

		if doLogging and console:
			console.log('[dark_orange]Response')
			console.log(dict(resp.headers))
			if (cl := resp.headers['Content-Length']) is not None and int(cl) > 0:
				console.log(resp.json())
			# console.log(resp.text)
			# console.log(resp.content)

		excluded_headers 	= ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
		responseHeaders 	= [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
		response 			= Response(resp.content, resp.status_code, responseHeaders)

		return response

##############################################################################
#
#	From here on this supports the stand-alone web UI app
#


console:Console = None
""" The ACME console for logging. """
doLogging:bool = True
""" Whether to do logging. """
doOauth:bool = False
""" Whether to use OAuth2. """


def runServer(flaskApp:Flask, 
			  host:str, 
			  port:int, 
			  useTLS:bool, 
			  certFile:Optional[str] = None, 
			  privateKey:Optional[str] = None) -> None:
	"""	Run the web server.

		Args:
			flaskApp: The flask app to run.
			host: The host to bind to.
			port: The port to bind to.
			useTLS: Whether to use TLS.
			certFile: The certificate file.
			privateKey: The private key file.
	"""
	
	WSGIRequestHandler.protocol_version = "HTTP/1.1"

	# Run the http server. This runs forever.
	# The server can run single-threadedly since some of the underlying
	# components (e.g. TinyDB) may run into problems otherwise.
	if flaskApp is not None:
		# Disable the flask banner messages
		cli = sys.modules['flask.cli']
		cli.show_server_banner = lambda *x: None 	# type: ignore
		# Start the server
		try:
			context = None
			if useTLS:
				context = ssl.SSLContext(ssl.PROTOCOL_TLS)
				context.load_cert_chain(certFile, privateKey)
			flaskApp.run(	host=host, 
							port=port,
							threaded=True,
							request_handler=ACMERequestHandler,
							ssl_context=context,
							debug=False)
		except Exception as e:
			print(str(e))

##########################################################################
#
#	Own request handler.
#	Actually only to redirect some logging of the http server.
#	This handler does NOT handle requests.
#

class ACMERequestHandler(WSGIRequestHandler):
	"""	Own request handler to redirect some logging of the http server.
	"""

	# Just like WSGIRequestHandler, but without "- -"
	def log(self, type, message, *args): # type: ignore
		"""	Log a message. Overridden to redirect logging.

			Args:
				type: The type of the message.
				message: The message.
				args: The arguments.
		"""
		if doLogging:
			console.log(message % args)


	# Just like WSGIRequestHandler, but without "code"
	def log_request(self, code='-', size='-'): 	# type: ignore
		"""	Log an incoming request. Overridden to redirect logging.

			Args:
				code: The response code.
				size: The response size.
		"""
		if doLogging:
			console.log(f'"{self.requestline}" {size} {code}')


	def log_message(self, format, *args): 	# type: ignore
		"""	Log a message. Overridden to redirect logging.

			Args:
				format: The format of the message.
				args: The arguments.
		"""
		if doLogging:
			console.log(format % args)

#
#	OAuth2 token handling
#	

Token = collections.namedtuple('Token', 'token expiration')
""" Named tuple for a token. """
_expirationLeeway	= 5.0		# 5 seconds leeway for token expiration
"""	Leeway for token expiration. """



def getOAuthToken(token:Optional[Token] = None, 
				  kind:Optional[str] = 'keycloak') -> Optional[Token]:
	"""	Retrieve and return a oauth2 token. If there is a provided token that is still valid, then that token
		is returned.

		This function returns a new named tuple Token(token, expiration), or None in case of an error. The expiration 
		is in epoch seconds.

		Args:
			token: The token to check. If None, a new token is retrieved.
			kind: The kind of token to retrieve. Currently only 'keycloak' is supported.

		Returns:
			The token, or None in case of an error.
	"""
	if token is None:
		token = Token(token=None, expiration=0.0)

	# Return the old token, if it exists and is not expired
	if token.expiration > time.time() and token.token is not None:
		return token

	# Retrieve a new token
	if kind == 'keycloak':
		headers = {
			'contentType' 	: 'application/x-www-form-urlencoded',
		}
		formData = {
			'grant_type' 	: 'client_credentials',
			'client_secret'	: clientSecret,
			'client_id'		: clientID,
		}
		if (response := requests.post(oauthServerUrl	, data=formData, headers=headers)).status_code == 200:
			data = response.json()
			if data is None or 'access_token' not in data or 'expires_in' not in data:
				return None
		return	Token(token	     = data['access_token'],
					expiration = time.time() + data['expires_in'] - _expirationLeeway
				)
	return None


if __name__ == '__main__':
	console = Console()
	console.print('\n[dim][[/dim][red][i]ACME[/i][/red][dim]][/dim] - [bold]WebUI[/bold]\n\n')

	# parse command line argiments
	parser = argparse.ArgumentParser()

	parser.add_argument('--ip', action='store', dest='hostIP', default='127.0.0.1', help='the web UI\'s local IP address to bind to (default: %(default)s)')
	parser.add_argument('--port', action='store', dest='hostPort', default=8000, help='the web UI\'s local port (default: %(default)d)')
	parser.add_argument('--cseurl', action='store', dest='targetURL', default='http://127.0.0.1:8080/', help='the target CSE\'s base URL (default: %(default)s)')	
	parser.add_argument('--ri', action='store', dest='targetRI', default='id-in', help='the target CSE\'s default base RI (default: %(default)s)')	
	parser.add_argument('--originator', action='store', dest='targetOriginator', default='CAdmin', help='the target CSE\'s default originator (default: %(default)s)')	
	parser.add_argument('--logging', action='store_true', dest='logging', default=False, help='enable logging')
	parser.add_argument('--no-open', action='store_true', dest='noOpen', default=False, help='disable opening a web browser on startup (default: %(default)s)')

	# https / tls arguments
	parser.add_argument('--tls', action='store_true', dest='useTLS', default=False, help='enable TLS (https) for the web UI (default: %(default)s)')	
	parser.add_argument('--certfile', action='store', dest='certFile', default=None, required='--tls' in sys.argv, help='path to certificate file (default: %(default)s, required for --tls)')	
	parser.add_argument('--keyfile', action='store', dest='keyFile', default=None, required='--tls' in sys.argv, help='path to private key file (default: %(default)s, required for --tls)')	

	# oauth arguments
	parser.add_argument('--oauth', action='store_true', dest='oauth', default=False, help='enable OAuth2 authentication for CSE access (default: %(default)s)')
	parser.add_argument('--oauth-server-url', action='store', dest='oauthServerUrl', required='--oauth' in sys.argv, help='the OAuth2 server URL')
	parser.add_argument('--client-id', action='store', dest='clientID', required='--oauth' in sys.argv, help='the OAuth2 client ID')
	parser.add_argument('--client-secret', action='store', dest='clientSecret',  required='--oauth' in sys.argv, help='the OAuth2 client secret')

	# Assign some args for easier access later
	args 				= parser.parse_args()
	doLogging 			= args.logging
	doOauth 			= args.oauth
	oauthServerUrl		= args.oauthServerUrl
	clientID 			= args.clientID
	clientSecret 		= args.clientSecret

	# Start Server
	flaskApp = Flask('ACME WebUI')
	webui = WebUI(flaskApp, defaultRI=args.targetRI, defaultOriginator=args.targetOriginator, redirectURL=args.targetURL)
	if not args.noOpen:
		webbrowser.open(f'http{"s" if args.useTLS else ""}://{args.hostIP}:{args.hostPort}')
	runServer(flaskApp, args.hostIP, args.hostPort, args.useTLS, certFile=args.certFile, privateKey=args.keyFile)
