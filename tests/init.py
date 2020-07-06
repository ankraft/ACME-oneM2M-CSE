#
#	init.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configuration & helper functions for unit tests
#

import requests, random, sys, json, time
from typing import Any, Callable
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

SERVER				= 'http://localhost:8080'
ROOTPATH			= '/'
CSERN				= 'cse-in'
CSEID				= '/id-in'
SPID 				= 'sp-in'
ORIGINATOR			= 'CAdmin'


NOTIFICATIONPORT 	= 9990
NOTIFICATIONSERVER	= 'http://localhost:%d' % NOTIFICATIONPORT
NOTIFICATIONSERVERW	= 'http://localhost:6666'


testVerbosity 		= 2		# 0, 1, 2

###############################################################################

aeRN	= 'testAE'
cntRN	= 'testCNT'
cinRN	= 'testCIN'
grpRN	= 'testGRP'
fcntRN	= 'testFCNT'
nodRN 	= 'testNOD'
subRN	= 'testSUB'


URL		= '%s%s' % (SERVER, ROOTPATH)
cseURL 	= '%s%s' % (URL, CSERN)
aeURL 	= '%s/%s' % (cseURL, aeRN)
cntURL 	= '%s/%s' % (aeURL, cntRN)
cinURL 	= '%s/%s' % (cntURL, cinRN)
fcntURL	= '%s/%s' % (aeURL, fcntRN)
grpURL 	= '%s/%s' % (aeURL, grpRN)
nodURL 	= '%s/%s' % (cseURL, nodRN)
subURL 	= '%s/%s' % (cntURL, subRN)



###############################################################################


#
#	HTTP Requests
#

def RETRIEVE(url : str, originator : str) -> (dict, int):
	return sendRequest(requests.get, url, originator)


def CREATE(url : str, originator : str, ty : int = None, data : Any = None) -> (dict, int):
	return sendRequest(requests.post, url, originator, ty, data)


def UPDATE(url : str, originator : str, data : Any) -> (dict, int):
	return sendRequest(requests.put, url, originator, data=data)


def DELETE(url : str, originator : str) -> (dict, int):
	return sendRequest(requests.delete, url, originator)


def sendRequest(method : Callable , url : str, originator : str, ty : int = None, data : Any = None, ct : str = 'application/json') -> (dict, int):	# TODO Constants
	headers = { 'Content-Type' 	: '%s%s' % (ct, ';ty=%d' % ty if ty is not None else ''), 
				'X-M2M-Origin'	 	: originator,
				'X-M2M-RI' 			: uniqueID(),
				'X-M2M-RVI'			: '3',			# TODO this actually depends in the originator
			   }
	try:
		#print('Sending request: %s %s' % (method.__name__.upper(), url))
		if isinstance(data, dict):
			data = json.dumps(data)
		r = method(url, data=data, headers=headers)
	except Exception as e:
		print('Failed to send request: %s' % str(e))
		return None, 5103
	rc = int(r.headers['X-M2M-RSC']) if 'X-M2M-RSC' in r.headers else 5000
	return r.json() if len(r.content) > 0 else None, rc


#
#	Notification Server
#

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

	def log_message(self, format, *args):
		pass


keepNotificationServerRunning = True

def runNotificationServer():
	global keepNotificationServerRunning
	httpd = HTTPServer(('', NOTIFICATIONPORT), SimpleHTTPRequestHandler)
	keepNotificationServerRunning = True
	while keepNotificationServerRunning:
		httpd.handle_request()


def startNotificationServer():
	notificationThread = Thread(target=runNotificationServer)
	notificationThread.start()
	time.sleep(0.5)	# give the server a moment to start


def stopNotificationServer():
	global keepNotificationServerRunning
	keepNotificationServerRunning = False
	requests.post(NOTIFICATIONSERVER)	# send empty/termination request 



#
#	ID
#

def uniqueID() -> str:
	return str(random.randint(1,sys.maxsize))

#
#	Utilities
#

# find a structured element in JSON
def findXPath(jsn : dict, element : str, default : Any = None) -> Any:
	paths = element.split("/")
	data = jsn
	for i in range(0,len(paths)):
		if paths[i] not in data:
			return default
		data = data[paths[i]]
	return data


def setXPath(jsn: dict, element: str, value: Any, overwrite: bool = True) -> None:
	paths = element.split("/")
	ln = len(paths)
	data = jsn
	for i in range(0,ln-1):
		if paths[i] not in data:
			data[paths[i]] = {}
		data = data[paths[i]]
	if paths[ln-1] in data is not None and not overwrite:
			return # don't overwrite
	data[paths[ln-1]] = value

	