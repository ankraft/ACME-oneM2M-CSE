#
#	init.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configuration & helper functions for unit tests
#

from __future__ import annotations
import sys
sys.path.append('../acme')
import unittest
from rich.console import Console
import requests, random, sys, json, re, time, datetime, ssl, urllib3
import cbor2
from typing import Any, Callable, Union, Tuple, cast
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import cbor2
from Types import Parameters, JSON

PROTOCOL			= 'http'	# possible values: http, https
# ENCODING 			= 


SERVER				= f'{PROTOCOL}://localhost:8080'
ROOTPATH			= '/'
CSERN				= 'cse-in'
CSEID				= '/id-in'
SPID 				= 'sp-in'
ORIGINATOR			= 'CAdmin'

REMOTESERVER		= f'{PROTOCOL}://localhost:8081'
REMOTEROOTPATH		= '/'
REMOTECSERN			= 'cse-mn'
REMOTECSEID			= '/id-mn'
REMOTESPID 			= 'sp-mn'
REMOTEORIGINATOR	= 'CAdmin'


NOTIFICATIONPORT 	= 9990
NOTIFICATIONSERVER	= f'{PROTOCOL}://localhost:{NOTIFICATIONPORT}' 
NOTIFICATIONSERVERW	= f'{PROTOCOL}://localhost:6666'

CONFIGURL			= f'{SERVER}{ROOTPATH}__config__'


verifyCertificate	= False	# verify the certificate when using https?

# possible time delta between test system and CSE
# This is not really important, but for discoveries and others
timeDelta 				= 0 # seconds

# Expirations
expirationCheckDelay 	= 2	# seconds
expirationSleep			= expirationCheckDelay * 3

requestETDuration 		= f'PT{expirationCheckDelay:d}S'
requestCheckDelay		= 1	#seconds

# ReleaseVersionIndicator
RVI						 ='3'


###############################################################################

aeRN	= 'testAE'
acpRN	= 'testACP'
batRN	= 'testBAT'
cntRN	= 'testCNT'
cinRN	= 'testCIN'
grpRN	= 'testGRP'
fcntRN	= 'testFCNT'
nodRN 	= 'testNOD'
pchRN 	= 'testPCH'
subRN	= 'testSUB'
reqRN	= 'testREQ'
memRN	= 'mem'
batRN	= 'bat'


URL		= f'{SERVER}{ROOTPATH}'
cseURL 	= f'{URL}{CSERN}'
csiURL 	= f'{URL}~{CSEID}'
aeURL 	= f'{cseURL}/{aeRN}'
acpURL 	= f'{cseURL}/{acpRN}'
cntURL 	= f'{aeURL}/{cntRN}'
cinURL 	= f'{cntURL}/{cinRN}'
fcntURL	= f'{aeURL}/{fcntRN}'
grpURL 	= f'{aeURL}/{grpRN}'
nodURL 	= f'{cseURL}/{nodRN}'
pchURL 	= f'{aeURL}/{pchRN}'
subURL 	= f'{cntURL}/{subRN}'
batURL 	= f'{nodURL}/{batRN}'
memURL	= f'{nodURL}/{memRN}'
batURL	= f'{nodURL}/{batRN}'


REMOTEURL		= f'{REMOTESERVER}{REMOTEROOTPATH}'
REMOTEcseURL 	= f'{REMOTEURL}{REMOTECSERN}'
localCsrURL 	= f'{cseURL}{REMOTECSEID}'
remoteCsrURL 	= f'{REMOTEcseURL}{CSEID}'


###############################################################################

#
#	HTTP Requests
#

def _RETRIEVE(url:str, originator:str, timeout:float=None, headers:Parameters=None) -> Tuple[str|JSON, int]:
	return sendRequest(requests.get, url, originator, timeout=timeout, headers=headers)

def RETRIEVESTRING(url:str, originator:str, timeout:float=None, headers:Parameters=None) -> Tuple[str, int]:
	x,rsc = _RETRIEVE(url=url, originator=originator, timeout=timeout, headers=headers)
	return str(x, 'utf-8'), rsc		# type:ignore[call-overload]

def RETRIEVE(url:str, originator:str, timeout:float=None, headers:Parameters=None) -> Tuple[JSON, int]:
	x,rsc = _RETRIEVE(url=url, originator=originator, timeout=timeout, headers=headers)
	return cast(JSON, x), rsc


def CREATE(url:str, originator:str, ty:int=None, data:JSON=None, headers:Parameters=None) -> Tuple[JSON, int]:
	x,rsc = sendRequest(requests.post, url, originator, ty, data, headers=headers)
	return cast(JSON, x), rsc


def _UPDATE(url:str, originator:str, data:JSON|str, headers:Parameters=None) -> Tuple[str|JSON, int]:
	return sendRequest(requests.put, url, originator, data=data, headers=headers)

def UPDATESTRING(url:str, originator:str, data:str, headers:Parameters=None) -> Tuple[str, int]:
	x, rsc = _UPDATE(url=url, originator=originator, data=data, headers=headers)
	return str(x, 'utf-8'), rsc		# type:ignore[call-overload]

def UPDATE(url:str, originator:str, data:JSON, headers:Parameters=None) -> Tuple[JSON, int]:
	x, rsc = _UPDATE(url=url, originator=originator, data=data, headers=headers)
	return cast(JSON, x), rsc


def DELETE(url:str, originator:str, headers:Parameters=None) -> Tuple[JSON, int]:
	x, rsc = sendRequest(requests.delete, url, originator, headers=headers)
	return cast(JSON, x), rsc


def sendRequest(method:Callable, url:str, originator:str, ty:int=None, data:JSON|str=None, ct:str=None, timeout:float=None, headers:Parameters=None) -> Tuple[STRING|JSON, int]:	# type: ignore # TODO Constants
	tys = f';ty={ty}' if ty is not None else ''
	ct = 'application/json'
	hds = { 
		'Content-Type' 		: f'{ct}{tys}',
		'Accept'			: ct,
		'X-M2M-Origin'	 	: originator,
		'X-M2M-RI' 			: (rid := uniqueID()),
		'X-M2M-RVI'			: RVI,
	}
	if headers is not None:		# extend with other headers
		if 'X-M2M-RVI' in headers:	# overwrite X-M2M-RVI header
			hds['X-M2M-RVI'] = headers['X-M2M-RVI']
			del headers['X-M2M-RVI']
		hds.update(headers)

	setLastRequestID(rid)
	try:
		sendData:str = None
		if data is not None:
			if isinstance(data, dict):	# actually JSON, but isinstance() cannot be used with generics
				sendData = json.dumps(data)
			else:
				sendData = data
			# data = cbor2.dumps(data)	# TODO use CBOR as well
		r = method(url, data=sendData, headers=hds, verify=verifyCertificate)
	except Exception as e:
		#print(f'Failed to send request: {str(e)}')
		return None, 5103
	rc = int(r.headers['X-M2M-RSC']) if 'X-M2M-RSC' in r.headers else r.status_code

	# save last header for later
	setLastHeaders(r.headers)

	# return plain text
	if (ct := r.headers.get('Content-Type')) is not None and ct.startswith('text/plain'):
		return r.content, rc
	elif ct.startswith(('application/json', 'application/vnd.onem2m-res+json')):
		return r.json() if len(r.content) > 0 else None, rc
	# just return what's in there
	return r.content, rc


_lastRequstID = None

def setLastRequestID(rid:str) -> None:
	global _lastRequstID
	_lastRequstID = rid


def lastRequestID() -> str:
	return _lastRequstID

def connectionPossible(url:str) -> bool:
	try:
		# The following request is not supposed to return a resource, it just
		# tests whether a connection can be established at all.
		return RETRIEVE(url, 'none', timeout=1.0)[0] is not None
	except Exception as e:
		print(e)
		return False

_lastHeaders:Parameters = None

def setLastHeaders(hds:Parameters) -> None:
	global _lastHeaders
	_lastHeaders = hds

def lastHeaders() -> Parameters:
	return _lastHeaders


###############################################################################

#
#	Expirations
#


def setExpirationCheck(interval:int) -> int:
	c, rc = RETRIEVESTRING(CONFIGURL, '')
	if rc == 200 and c.startswith('Configuration:'):
		# retrieve the old value
		c, rc = RETRIEVESTRING(f'{CONFIGURL}/cse.checkExpirationsInterval', '')
		oldValue = int(c)
		c, rc = UPDATESTRING(f'{CONFIGURL}/cse.checkExpirationsInterval', '', str(interval))
		return oldValue if c == 'ack' else -1
	return -1


def getMaxExpiration() -> int:
	c, rc = RETRIEVESTRING(CONFIGURL, '')
	if rc == 200 and c.startswith('Configuration:'):
		# retrieve the old value
		c, rc = RETRIEVESTRING(f'{CONFIGURL}/cse.maxExpirationDelta', '')
		return int(c)
	return -1


_orgExpCheck = -1
_orgREQExpCheck = -1
_maxExpiration = -1
_tooLargeExpirationDelta = -1



def disableShortExpirations() -> None:
	global _orgExpCheck, _orgREQExpCheck
	if _orgExpCheck != -1:
		setExpirationCheck(_orgExpCheck)
		_orgExpCheck = -1
	if _orgREQExpCheck != -1:
		setRequestMinET(_orgREQExpCheck)
		_orgREQExpCheck = -1

def isTestExpirations() -> bool:
	return _orgExpCheck != -1


def tooLargeExpirationDelta() -> int:
	return _tooLargeExpirationDelta


#	Request expirations

def setRequestMinET(interval:int) -> int:
	c, rc = RETRIEVESTRING(CONFIGURL, '')
	if rc == 200 and c.startswith('Configuration:'):
		# retrieve the old value
		c, rc = RETRIEVESTRING(f'{CONFIGURL}/cse.req.minet', '')
		oldValue = int(c)
		c, rc = UPDATESTRING(f'{CONFIGURL}/cse.req.minet', '', str(interval))
		return oldValue if c == 'ack' else -1
	return -1


def getRequestMinET() -> int:
	c, rc = RETRIEVESTRING(CONFIGURL, '')
	if rc == 200 and c.startswith('Configuration:'):
		# retrieve the old value
		c, rc = RETRIEVESTRING(f'{CONFIGURL}/cse.req.minet', '')
		return int(c)
	return -1
	


# Reconfigure the server to check faster for expirations. This is set to the
# old value in the tearDowndClass() method.
def enableShortExpirations() -> None:
	global _orgExpCheck, _orgREQExpCheck, _maxExpiration, _tooLargeExpirationDelta
	_orgExpCheck = setExpirationCheck(expirationCheckDelay)
	_orgREQExpCheck = setRequestMinET(expirationCheckDelay)
	# Retrieve the max expiration delta from the CSE
	_maxExpiration = getMaxExpiration()
	_tooLargeExpirationDelta = _maxExpiration * 2	# double of what is allowed


###############################################################################

# Surpress warnings for insecure requests, e.g. self-signed certificates
if not verifyCertificate:
	#requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning) 
	urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning) 



#
#	Notification Server
#

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
		
	def do_POST(self) -> None:
		# Construct return header
		# Always acknowledge the verification requests
		self.send_response(200)
		self.send_header('X-M2M-RSC', '2000')
		self.end_headers()

		# Get headers and content data
		length = int(self.headers['Content-Length'])
		post_data = self.rfile.read(length)
		if len(post_data) > 0:
			contentType = ''
			if (val := self.headers.get('Content-Type')) is not None:
				contentType = val.lower()
			if contentType in [ 'application/json', 'application/vnd.onem2m-res+json' ]:
				setLastNotification(json.loads(post_data.decode('utf-8')))
			elif contentType in [ 'application/cbor', 'application/vnd.onem2m-res+cbor' ]:
				setLastNotification(cbor2.loads(post_data))
			# else:
			# 	setLastNotification(post_data.decode('utf-8'))

		setLastNotificationHeaders(dict(self.headers))	# make a dict out of the headers


	def log_message(self, format:str, *args:int) -> None:
		pass


keepNotificationServerRunning = True

def runNotificationServer() -> None:
	global keepNotificationServerRunning
	httpd = HTTPServer(('', NOTIFICATIONPORT), SimpleHTTPRequestHandler)
	if PROTOCOL == 'https':
		# init ssl socket
		context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)					# Create a SSL Context
		context.load_cert_chain(certfile='../certs/acme_cert.pem', keyfile='../certs/acme_key.pem')	# Load the certificate and private key
		httpd.socket = context.wrap_socket(httpd.socket, server_side=True)	# wrap the original http server socket as an SSL/TLS socket

	keepNotificationServerRunning = True
	while keepNotificationServerRunning:
		httpd.handle_request()


def startNotificationServer() -> None:
	notificationThread = Thread(target=runNotificationServer)
	notificationThread.start()
	time.sleep(0.1)	# give the server a moment to start


def stopNotificationServer() -> None:
	global keepNotificationServerRunning
	keepNotificationServerRunning = False
	requests.post(NOTIFICATIONSERVER, verify=verifyCertificate)	# send empty/termination request 

lastNotification:JSON				= None
lastNotificationHeaders:Parameters 	= {}

def setLastNotification(notification:JSON) -> None:
	global lastNotification
	lastNotification = notification

def getLastNotification() -> JSON:
	return lastNotification

def clearLastNotification() -> None:
	global lastNotification
	lastNotification = None

def setLastNotificationHeaders(headers:Parameters) -> None:
	global lastNotificationHeaders
	lastNotificationHeaders = headers

def getLastNotificationHeaders() -> Parameters:
	return lastNotificationHeaders


#
#	ID
#

def uniqueID() -> str:
	return str(random.randint(1,sys.maxsize))

#
#	Utilities
#

# find a structured element in JSON
decimalMatch = re.compile(r'{(\d+)}')
def findXPath(dct:JSON, element:str, default:Any=None) -> Any:
	if dct is None:
		return default
	paths = element.split("/")
	data = dct
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


def setXPath(dct:JSON, element:str, value:Any, overwrite:bool=True) -> None:
	paths = element.split("/")
	ln = len(paths)
	data = dct
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


def printResult(result:unittest.TestResult) -> None:
	"""	Print the test results. """
	console = Console()

	# Failures
	for f in result.failures:
		console.print(f'\n[bold][red]{f[0]}')
		console.print(f'[dim]{f[0].shortDescription()}')
		console.print(f[1])


###############################################################################

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)
noRemote = not connectionPossible(REMOTEcseURL)

