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
from typing import overload
import json, argparse, sys, ssl
import cbor2
from rich.console import Console
from rich.syntax import Syntax


port = 9999	# Change this variable to specify another port.
messageColor = 'spring_green2'

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

	def do_GET(self) -> None:
		"""	Just provide a simple web page.
		"""
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		self.wfile.write(bytes("<html><head><title>[ACME] Notification Server</title></head><body>This server doesn't provide a web page.</body></html>","utf-8")) 


	def do_POST(self) -> None:
		"""	Handle notification.
		"""

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

		# Print JSON
		if contentType in [ 'application/json', 'application/vnd.onem2m-res+json' ]:
			console.print(Syntax(json.dumps(json.loads(post_data.decode('utf-8')), indent=4),
							 "json", 
							 theme="monokai",
							 line_numbers=False))
		
		# Print CBOR
		elif contentType in [ 'application/cbor', 'application/vnd.onem2m-res+cbor' ]:
			console.print('[dim]Content as Hexdump:\n')
			print(toHex(post_data))
			console.print('\n[dim]Content as JSON:\n')
			console.print(Syntax(json.dumps(cbor2.loads(post_data), indent=4),
							 "json", 
							 theme="monokai",
							 line_numbers=False))		

		# Print other binary content
		else:
			console.print('[dim]Content as Hexdump:\n')
			print(toHex(post_data))

	def log_message(self, format:str, *args:int) -> None:
		if (msg := format%args).startswith('"GET'):	return	# ignore GET log messages
		console.print(f'[{messageColor} reverse]{msg}')


def toHex(bts:bytes, toBinary:bool=False, withLength:bool=False) -> str:
	"""	Print bts as hex output, similar to the 'od' command.
	"""
	if len(bts) == 0 and not withLength: return ''
	result = ''
	n = 0
	b = bts[n:n+16]

	while b and len(b) > 0:

		if toBinary:
			s1 = ' '.join([f'{i:08b}' for i in b])
			s1 = f'{s1[0:71]} {s1[71:]}'
			width = 144
		else:
			s1 = ' '.join([f'{i:02x}' for i in b])
			s1 = f'{s1[0:23]} {s1[23:]}'
			width = 48

		s2 = ''.join([chr(i) if 32 <= i <= 127 else '.' for i in b])
		s2 = f'{s2[0:8]} {s2[8:]}'
		result += f'0x{n:08x}  {s1:<{width}}  | {s2}\n'

		n += 16
		b = bts[n:n+16]

	return result + f'0x{len(bts):08x}'


if __name__ == '__main__':
	console = Console()
	console.print('\n[dim][[/dim][red][i]ACME[/i][/red][dim]][/dim] - [bold]Notification Server[/bold]\n\n')


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
	
	console.print(f'[{messageColor}]Notification server started.\nListening for connections on port {args.port}.')
	try:
		httpd.serve_forever()
	except KeyboardInterrupt as e:
		console.print(f'\n[{messageColor}]Notification server stopped.')
	except Exception as e:
		console.print()
		console.print_exception()

