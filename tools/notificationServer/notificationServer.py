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


port = 9999	# Change this variable to specify another port.


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
		print('### Notification')
		print (self.headers)
		print(post_data.decode('utf-8'))



httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
print('**starting server & listening for connections on port %s **' % port)
httpd.serve_forever()
