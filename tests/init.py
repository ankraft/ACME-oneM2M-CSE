#
#	init.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configuration & helper functions for unit tests
#

import requests, random, sys, json, re, time, datetime
from typing import Any, Callable, Union
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

PROTOCOL			= 'http'	# possible values: http, https


SERVER				= '%s://localhost:8080' % PROTOCOL
ROOTPATH			= '/'
CSERN				= 'cse-in'
CSEID				= '/id-in'
SPID 				= 'sp-in'
ORIGINATOR			= 'CAdmin'

REMOTESERVER		= '%s://localhost:8081' % PROTOCOL
REMOTEROOTPATH		= '/'
REMOTECSERN			= 'cse-mn'
REMOTECSEID			= '/id-mn'
REMOTESPID 			= 'sp-mn'
REMOTEORIGINATOR	= 'CAdmin'


NOTIFICATIONPORT 	= 9990
NOTIFICATIONSERVER	= 'http://localhost:%d' % NOTIFICATIONPORT
NOTIFICATIONSERVERW	= 'http://localhost:6666'

CONFIGURL			= '%s%s__config__' % (SERVER, ROOTPATH)


testVerbosity 		= 2		# 0, 1, 2

verifyCertificate	= False	# verify the certificate when using https?

###############################################################################

aeRN	= 'testAE'
acpRN	= 'testACP'
batRN	= 'testBAT'
cntRN	= 'testCNT'
cinRN	= 'testCIN'
grpRN	= 'testGRP'
fcntRN	= 'testFCNT'
nodRN 	= 'testNOD'
subRN	= 'testSUB'


URL		= '%s%s' % (SERVER, ROOTPATH)
cseURL 	= '%s%s' % (URL, CSERN)
aeURL 	= '%s/%s' % (cseURL, aeRN)
acpURL 	= '%s/%s' % (cseURL, acpRN)
cntURL 	= '%s/%s' % (aeURL, cntRN)
cinURL 	= '%s/%s' % (cntURL, cinRN)
fcntURL	= '%s/%s' % (aeURL, fcntRN)
grpURL 	= '%s/%s' % (aeURL, grpRN)
nodURL 	= '%s/%s' % (cseURL, nodRN)
subURL 	= '%s/%s' % (cntURL, subRN)
batURL 	= '%s/%s' % (nodURL, batRN)

REMOTEURL		= '%s%s' % (REMOTESERVER, REMOTEROOTPATH)
REMOTEcseURL 	= '%s%s' % (REMOTEURL, REMOTECSERN)
localCsrURL 	= '%s%s' % (cseURL, REMOTECSEID)
remoteCsrURL 	= '%s%s' % (REMOTEcseURL, CSEID)





###############################################################################


#
#	HTTP Requests
#

def RETRIEVE(url:str, originator:str, timeout=None) -> (dict, int):
	return sendRequest(requests.get, url, originator, timeout=timeout)


def CREATE(url:str, originator:str, ty:int=None, data:Any=None) -> (dict, int):
	return sendRequest(requests.post, url, originator, ty, data)


def UPDATE(url:str, originator:str, data:Any) -> (dict, int):
	return sendRequest(requests.put, url, originator, data=data)


def DELETE(url:str, originator:str) -> (dict, int):
	return sendRequest(requests.delete, url, originator)


def sendRequest(method:Callable , url:str, originator:str, ty:int=None, data:Any=None, ct:str='application/json', timeout=None) -> (dict, int):	# TODO Constants
	headers = { 'Content-Type' 	: '%s%s' % (ct, ';ty=%d' % ty if ty is not None else ''), 
				'X-M2M-Origin'	 	: originator,
				'X-M2M-RI' 			: uniqueID(),
				'X-M2M-RVI'			: '3',			# TODO this actually depends in the originator
			   }
	try:
		#print('Sending request: %s %s' % (method.__name__.upper(), url))
		if isinstance(data, dict):
			data = json.dumps(data)
		r = method(url, data=data, headers=headers, verify=verifyCertificate)
	except Exception as e:
		#print('Failed to send request: %s' % str(e))
		return None, 5103
	rc = int(r.headers['X-M2M-RSC']) if 'X-M2M-RSC' in r.headers else r.status_code

	# response doesn't always contain JSON
	try:
		result = r.json() if len(r.content) > 0 else None, rc
	except Exception as e:
		result = r.content, rc
	return result


def connectionPossible(url):
	try:
		# The following request is not supposed to return a resource, it just
		# tests whether a connection can be established at all.
		return RETRIEVE(url, 'none', timeout=1.0)[0] is not None
	except Exception as e:
		return False


def setExpirationCheck(interval:int) -> int:
	c, rc = RETRIEVE(CONFIGURL, '')
	if rc == 200 and c.startswith(b'Configuration:'):
		# retrieve the old value
		c, rc = RETRIEVE('%s/cse.checkExpirationsInterval' % CONFIGURL, '')
		oldValue = int(c)
		c, rc = UPDATE('%s/cse.checkExpirationsInterval' % CONFIGURL, '', str(interval))
		return oldValue if c == b'ack' else -1
	return -1
		

# Surpress warnings for insecure requests, e.g. self-signed certificates
if not verifyCertificate:
	requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning) 



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
		if len(post_data) > 0:
			setLastNotification(json.loads(post_data.decode('utf-8')))


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
	time.sleep(0.1)	# give the server a moment to start


def stopNotificationServer():
	global keepNotificationServerRunning
	keepNotificationServerRunning = False
	requests.post(NOTIFICATIONSERVER)	# send empty/termination request 

lastNotification = None

def setLastNotification(notification:str):
	global lastNotification
	lastNotification = notification

def getLastNotification():
	return lastNotification



#
#	ID
#

def uniqueID() -> str:
	return str(random.randint(1,sys.maxsize))

#
#	Utilities
#

# find a structured element in JSON
decimalMatch = re.compile('{(\d+)}')
def findXPath(jsn : dict, element : str, default : Any = None) -> Any:
	paths = element.split("/")
	data = jsn
	for i in range(0,len(paths)):
		if len(paths[i]) == 0:	# return if there is an empty path element
			return default
		elif (m := decimalMatch.search(paths[i])) is not None:	# Match array index {i}
			idx = int(m.group(1))
			if not isinstance(data, list) or idx >= len(data):	# Check idx within range of list
				return default
			data = data[idx]
		elif paths[i] not in data:	# if key not in dict
			return default
		else:
			data = data[paths[i]]	# found data for the next level down
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


def getDate(delta:int = 0) -> str:
	return toISO8601Date(datetime.datetime.utcnow() + datetime.timedelta(seconds=delta))


def toISO8601Date(ts: Union[float, datetime.datetime]) -> str:
	if isinstance(ts, float):
		ts = datetime.datetime.utcfromtimestamp(ts)
	return ts.strftime('%Y%m%dT%H%M%S,%f')
	
