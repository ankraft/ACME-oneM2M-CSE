#
#	notificationServer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Simple base implementation of a notification server to handle notifications 
#	from a CSE.
#

from http.server import HTTPServer, BaseHTTPRequestHandler
import json, argparse, sys, ssl
from rich import print
from rich.console import Console
from rich.syntax import Syntax


port = 9999	# Change this variable to specify another port.
messageColor = 'spring_green2'

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
		
	def do_POST(self):

		# Construct return header
		# Always acknowledge the verification requests
		self.send_response(200)
		self.send_header('X-M2M-RSC', '2000')
		self.end_headers()

		# Get headers and content data
		length = int(self.headers['Content-Length'])
		contentType = self.headers['Content-Type']
		post_data = self.rfile.read(length)
		
		# Print the content data
		console.print(f'[{messageColor}]### Notification')
		console.print(self.headers, highlight=False)
		console.print(Syntax(json.dumps(json.loads(post_data.decode('utf-8')), indent=4),
							 "json", 
							 theme="monokai",
							 line_numbers=False))

	def log_message(self, format, *args):
		console.print(f'[{messageColor} reverse] {format%args}')



if __name__ == '__main__':
	console = Console()
	console.print('\n[dim]\[[/dim][red][i]ACME[/i][/red][dim]][/dim] - [bold]Notification Server[/bold]\n\n')


	# parse command line argiments
	parser = argparse.ArgumentParser()
	parser.add_argument('--port', action='store', dest='port', default=port, type=int, help='specify the server port')

	# two mutual exlcusive arguments
	groupApps = parser.add_mutually_exclusive_group()
	groupApps.add_argument('--http', action='store_false', dest='usehttps', default=None, help='run as http server (default)')
	groupApps.add_argument('--https', action='store_true', dest='usehttps', default=None, help='run as https server')

	parser.add_argument('--certfile', action='store', dest='certfile', required='--https' in sys.argv, metavar='<filename>', help='specify the certificate file for https')
	parser.add_argument('--keyfile', action='store', dest='keyfile', required='--https' in sys.argv, metavar='<filename>', 	help='specify the key file for https')
	args = parser.parse_args()

	# run http(s) server
	httpd = HTTPServer(('', args.port), SimpleHTTPRequestHandler)
	
	if args.usehttps:
		# init ssl socket
		context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)					# Create a SSL Context
		context.load_cert_chain(args.certfile, args.keyfile)				# Load the certificate and private key
		httpd.socket = context.wrap_socket(httpd.socket, server_side=True)	# wrap the original http server socket as an SSL/TLS socket
	
	console.print(f'[{messageColor}]**starting server & listening for connections on port {args.port}**')
	httpd.serve_forever()


