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
import json
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
		console.print('[%s]### Notification' % messageColor)
		console.print(self.headers, highlight=False)
		console.print(Syntax(json.dumps(json.loads(post_data.decode('utf-8')), indent=4),
							 "json", 
							 theme="monokai",
							 line_numbers=False))

	def log_message(self, format, *args):
		console.print("[%s reverse] %s" % (messageColor, format%args))



if __name__ == '__main__':
	console = Console()
	httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
	console.print('\n[dim][[[/dim][red][i]ACME[/i][/red][dim]][/dim] - [bold]Notification Server[/bold]\n\n')

	console.print('[%s]**starting server & listening for connections on port %s **' % (messageColor, port))
	httpd.serve_forever()
