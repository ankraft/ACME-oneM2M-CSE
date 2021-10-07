#
#	init.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configuration & helper functions for unit tests
#

from __future__ import annotations
from argparse import OPTIONAL
from urllib.parse import ParseResult, urlparse, parse_qs
import sys, io, atexit
from queue import Queue
import unittest

from rich.console import Console
import requests, random, sys, json, re, time, datetime, ssl, urllib3
import cbor2
from typing import Any, Callable, Union, Tuple, cast
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import cbor2

# sys.path.append('../acme')
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ContentSerializationType, Parameters, JSON, Operation, ResourceTypes, ResponseStatusCode
import acme.etc.RequestUtils as RequestUtils, acme.etc.DateUtils as DateUtils
import acme.helpers.OAuth as OAuth
from acme.helpers.MQTTConnection import MQTTConnection, MQTTHandler
from acme.etc.Constants import Constants as C
from config import *


CONFIGURL			= f'{CONFIGSERVER}{ROOTPATH}__config__'


verifyCertificate	= False	# verify the certificate when using https?
oauthToken			= None	# current OAuth Token

# possible time delta between test system and CSE
# This is not really important, but for discoveries and others
timeDelta 				= 0 # seconds

# Expirations
expirationCheckDelay 	= 2	# seconds
expirationSleep			= expirationCheckDelay * 3

requestETDuration 		= f'PT{expirationCheckDelay:d}S'
requestETDurationInteger= expirationCheckDelay * 1000
requestCheckDelay		= 1	#seconds

# TimeSeries Interval
timeSeriesInterval 		= 2.0 # seconds

# ReleaseVersionIndicator
RVI						 ='3'

from dataclasses import dataclass, field

@dataclass
class MQTTTopics:
	reqTopic:str
	respTopic:str
	subscribed:bool					= False


# TODO think about to move this?
class MQTTClientHandler(MQTTHandler):
	"""	Class for handling receiced MQTT requests.
	"""

	def	__init__(self) -> None:
		super().__init__()
		self.responses:dict[str, bytes] 	= dict()
		self.topics:dict[str, MQTTTopics]	= dict()
		self.connection:MQTTConnection		= None
		# self.respTopic 					= f'/oneM2M/resp/+{CSEID}/json'
		# self.ready 						= False

	def onConnect(self, connection:MQTTConnection) -> None:
		# always subscribe to register response 
		connection.subscribeTopic(MQTTREGRESPONSETOPIC, callback=self._callback)
		self.connection = connection
	
	def onDisconnect(self, _: MQTTConnection) -> None:
		self.unregisterAllOriginators()
		self.connection = None

	def onSubscribed(self, _:MQTTConnection, topic:str) -> None:
		if topic == MQTTREGRESPONSETOPIC:
			return
		for o,t in self.topics.items():
			if t.respTopic == topic:
				t.subscribed = True
				self.topics[o] = t
				#print(f'Subscribed to: {o} / {topic}')
				return
		print(f'unknown topic: {topic}')
		# self.ready = topic in [ self.respTopic ]


	def onUnsubscribed(self, _:MQTTConnection, topic:str) -> None:
		# self.ready = not topic in [ self.respTopic ]
		pass

	def onError(self, _:MQTTConnection, rc:int) -> None:
		print(f'mqtt error: {rc}')
		# TODO
	
	# def logging(self, _:MQTTConnection, level:int, message:str) -> None:
	# 	print(message)
	# 	pass
	
	def _callback(self, connection:MQTTConnection, topic:str, data:bytes) -> None:
		#print(f'<== {topic} / {data}')
		resp = RequestUtils.deserializeData(data, ContentSerializationType.JSON)
		if 'rqi' in resp:
			self.responses[resp['rqi']] = (topic, resp)
		else:
			print(f'no rqi in message: {resp}')


	def publish(self, topic:str, data:bytes) -> None:
		self.connection.publish(topic, data)

	
	def registerOriginator(self, originator:str) -> MQTTTopics:
		"""	Register and subscribe to a topic for that originator, only once. 
		"""
		if originator in self.topics:
			return self.topics[originator]
		topics = MQTTTopics(MQTTREQUESTTOPIC.replace('$ORIGINATOR$', originator),
							MQTTRESPONSETOPIC.replace('$ORIGINATOR$', originator))
		self.topics[originator] = topics
		self.connection.subscribeTopic(topics.respTopic, callback=self._callback)
		
		#  Wait for subscription
		while True:		# TODO Timeout
			if self.topics[originator].respTopic:
				break
			time.sleep(0.01)

		return topics
	

	def unregisterAllOriginators(self) -> None:
		"""	Unsubscribe from all topics for originators.
		"""
		for t in self.topics.values():
			if t.subscribed:
				self.connection.unsubscribeTopic(t.respTopic)
		self.topics.clear()
	


# MQTT Connection
mqttClient:MQTTConnection = None
mqttHandler:MQTTClientHandler = None

# A timestamp far in the future
# Why 8888? Year 9999 may actually problematic, because this might be interpreteted
# already as year 10000 (and this hits the limit of the isodata module implmenetation)

def isRaspberrypi() -> bool:
	"""	Check whether we run on a Raspberry Pi. 
	"""
	try:
		with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
			if 'raspberry pi' in m.read().lower(): return True
	except Exception: pass
	return False

# Raspbian is still a 32-bit OS and doesn't	support really long timestamps.
futureTimestamp = '20371231T235959' if isRaspberrypi() else '88881231T235959'


# Rich console
console = Console()


###############################################################################

aeRN	= 'testAE'
acpRN	= 'testACP'
batRN	= 'testBAT'
cinRN	= 'testCIN'
cntRN	= 'testCNT'
csrRN	= 'testCSR'
grpRN	= 'testGRP'
fcntRN	= 'testFCNT'
nodRN 	= 'testNOD'
pchRN 	= 'testPCH'
reqRN	= 'testREQ'
subRN	= 'testSUB'
tsRN	= 'testTS'
tsiRN	= 'testTSI'
memRN	= 'mem'
batRN	= 'bat'


URL		= f'{SERVER}{ROOTPATH}'
cseURL 	= f'{URL}{CSERN}'
csiURL 	= f'{URL}{CSEID}'
aeURL 	= f'{cseURL}/{aeRN}'
acpURL 	= f'{cseURL}/{acpRN}'
cntURL 	= f'{aeURL}/{cntRN}'
cinURL 	= f'{cntURL}/{cinRN}'	# under the <cnt>
csrURL	= f'{cseURL}/{csrRN}'
fcntURL	= f'{aeURL}/{fcntRN}'
grpURL 	= f'{aeURL}/{grpRN}'
nodURL 	= f'{cseURL}/{nodRN}'	# under the <ae>
pchURL 	= f'{aeURL}/{pchRN}'
pcuURL 	= f'{pchURL}/pcu'
subURL 	= f'{cntURL}/{subRN}'	# under the <cnt>
tsURL 	= f'{aeURL}/{tsRN}'
batURL 	= f'{nodURL}/{batRN}'	# under the <nod>
memURL	= f'{nodURL}/{memRN}'	# under the <nod>


REMOTEURL		= f'{REMOTESERVER}{REMOTEROOTPATH}'
REMOTEcseURL 	= f'{REMOTEURL}{REMOTECSERN}'
localCsrURL 	= f'{cseURL}{REMOTECSEID}'
remoteCsrURL 	= f'{REMOTEcseURL}{CSEID}'

###############################################################################


@atexit.register
def shutdown() -> None:
	if mqttClient:
		mqttClient.shutdown()

###############################################################################

#
#	Requests
#

requestCount:int = 0

def _RETRIEVE(url:str, originator:str, timeout:float=None, headers:Parameters=None) -> Tuple[str|JSON, int]:
	return sendRequest(Operation.RETRIEVE, url, originator, timeout=timeout, headers=headers)

def RETRIEVESTRING(url:str, originator:str, timeout:float=None, headers:Parameters=None) -> Tuple[str, int]:
	x,rsc = _RETRIEVE(url=url, originator=originator, timeout=timeout, headers=headers)
	return str(x, 'utf-8'), rsc		# type:ignore[call-overload]

def RETRIEVE(url:str, originator:str, timeout:float=None, headers:Parameters=None) -> Tuple[JSON, int]:
	x,rsc = _RETRIEVE(url=url, originator=originator, timeout=timeout, headers=headers)
	return cast(JSON, x), rsc

def CREATE(url:str, originator:str, ty:ResourceTypes=None, data:JSON=None, headers:Parameters=None) -> Tuple[JSON, int]:
	x,rsc = sendRequest(Operation.CREATE, url, originator, ty, data, headers=headers)
	return cast(JSON, x), rsc

def NOTIFY(url:str, originator:str, data:JSON=None, headers:Parameters=None) -> Tuple[JSON, int]:
	x,rsc = sendRequest(Operation.NOTIFY, url, originator, data=data, headers=headers)
	return cast(JSON, x), rsc

def _UPDATE(url:str, originator:str, data:JSON|str, headers:Parameters=None) -> Tuple[str|JSON, int]:
	return sendRequest(Operation.UPDATE, url, originator, data=data, headers=headers)

def UPDATESTRING(url:str, originator:str, data:str, headers:Parameters=None) -> Tuple[str, int]:
	x, rsc = _UPDATE(url=url, originator=originator, data=data, headers=headers)
	return str(x, 'utf-8'), rsc		# type:ignore[call-overload]

def UPDATE(url:str, originator:str, data:JSON, headers:Parameters=None) -> Tuple[JSON, int]:
	x, rsc = _UPDATE(url=url, originator=originator, data=data, headers=headers)
	return cast(JSON, x), rsc

def DELETE(url:str, originator:str, headers:Parameters=None) -> Tuple[JSON, int]:
	x, rsc = sendRequest(Operation.DELETE, url, originator, headers=headers)
	return cast(JSON, x), rsc


def sendRequest(operation:Operation, url:str, originator:str, ty:ResourceTypes=None, data:JSON|str=None, ct:str=None, timeout:float=None, headers:Parameters=None) -> Tuple[STRING|JSON, int]:	# type: ignore # TODO Constants
	"""	Send a request. Call the appropriate framework, depending on the protocol.
	"""
	global requestCount
	requestCount += 1
	if url.startswith(('http', 'https')):
		if operation == Operation.CREATE:
			return sendHttpRequest(requests.post, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		elif operation == Operation.RETRIEVE:
			return sendHttpRequest(requests.get, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		elif operation == Operation.UPDATE:
			return sendHttpRequest(requests.put, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		elif operation == Operation.DELETE:
			return sendHttpRequest(requests.delete, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		elif operation == Operation.NOTIFY:
			return sendHttpRequest(requests.post, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
	elif url.startswith('mqtt'):
		if operation == Operation.CREATE:
			return sendMqttRequest(Operation.CREATE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		elif operation == Operation.RETRIEVE:
			return sendMqttRequest(Operation.RETRIEVE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		elif operation == Operation.UPDATE:
			return sendMqttRequest(Operation.UPDATE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		elif operation == Operation.DELETE:
			return sendMqttRequest(Operation.DELETE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		elif operation == Operation.NOTIFY:
			return sendMqttRequest(Operation.NOTIFY, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
	else:
		print('ERROR')
		return None, 5103


def sendHttpRequest(method:Callable, url:str, originator:str, ty:ResourceTypes=None, data:JSON|str=None, ct:str=None, timeout:float=None, headers:Parameters=None) -> Tuple[STRING|JSON, int]:	# type: ignore # TODO Constants
	global oauthToken

	# correct url
	url = RequestUtils.toHttpUrl(url)
	urlComponents:ParseResult = urlparse(url)

	if isinstance(ty, (ResourceTypes, int)):
		tys = f';ty={int(ty)}'
	elif ty is not None:	# e.g. for string
		tys = f';ty={ty}'
	else:
		tys = ''

	ct = 'application/json'
	hds = { 
		'Content-Type' 		: f'{ct}{tys}',
		'Accept'			: ct,
		C.hfRI 				: (rid := uniqueID()),
		C.hfRVI				: RVI,
	}
	if originator is not None:		# Set originator if it is not None
		hds[C.hfOrigin] = originator

	if headers is not None:			# extend with other headers
		if C.hfRVI in headers:	# overwrite X-M2M-RVI header
			hds[C.hfRVI] = headers[C.hfRVI]
			del headers[C.hfRVI]
		if C.hfRSC in headers:	# set RSC in header
			hds[C.hfRSC] = str(headers[C.hfRSC])
			del headers[C.hfRSC]
		hds.update(headers)
	
	# authentication
	if doOAuth:
		if (token := OAuth.getOAuthToken(oauthServerUrl, oauthClientID, oauthClientSecret, oauthToken)) is None:
			return 'error retrieving oauth token', 5103
		oauthToken = token
		hds['Authorization'] = f'Bearer {oauthToken.token}'

	# print(url)
	# print(hds)
	setLastRequestID(rid)
	try:
		sendData:str = None
		if data is not None:
			if isinstance(data, dict):	# actually JSON, but isinstance() cannot be used with generics
				sendData = json.dumps(data)
			else:
				sendData = data
			# data = cbor2.dumps(data)	# TODO use CBOR as well
		r = method(url, data=sendData, headers=hds, verify=verifyCertificate, timeout=timeout)
	except Exception as e:
		#print(f'Failed to send request: {str(e)}')
		return None, 5103
	rc = int(r.headers[C.hfRSC]) if C.hfRSC in r.headers else r.status_code

	# save last header for later
	setLastHeaders(r.headers)

	# return plain text
	if (ct := r.headers.get('Content-Type')) is not None and ct.startswith('text/plain'):
		return r.content, rc
	elif ct.startswith(('application/json', 'application/vnd.onem2m-res+json')):
		return r.json() if len(r.content) > 0 else None, rc
	# just return what's in there
	return r.content, rc


def sendMqttRequest(operation:Operation, url:str, originator:str, ty:int=None, data:JSON|str=None, ct:str=None, timeout:float=None, headers:Parameters=None) -> Tuple[STRING|JSON, int]:	# type: ignore # TODO Constants

	urlComponents:ParseResult = urlparse(url)
	urlquery = parse_qs(urlComponents.query)
	# print(urlquery)

	req:dict	= dict()
	fc:dict		= dict()
	req['fr'] 	= originator
	req['to'] 	= urlComponents.path[1:]	# remove the leading / of an url ( usually the root path)
	req['op'] 	= operation.value
	req['ot'] 	= DateUtils.getResourceDate()
	req['rqi'] 	= (rqi := uniqueID())
	req['rvi'] 	= RVI

	# Various request parameters
	if ty:	
		req['ty'] = ty
	if (rcn := urlquery.get('rcn')):
		req['rcn'] = int(rcn[0])	# only first rcn
		del urlquery['rcn']
	if (rt := urlquery.get('rt')):
		rt2 = dict()
		rt2['rtv'] = int(rt[0])	# only first rt
		req['rt'] = rt2
		del urlquery['rt']
	if (rp := urlquery.get('rp')):
		req['rp'] = rp[0]	# only first rp
		del urlquery['rp']
	
	# FilterCriteria
	if (fu := urlquery.get('fu')):
		fc['fu'] = int(fu[0])
		del urlquery['fu']
	if (fcty := urlquery.get('ty')):
		fc['ty'] = [ int(tt) for t in fcty for tt in t.split(' ') ]	# input may be: [ '1 2' , '3' ]
		del urlquery['ty']
	if (lbl := urlquery.get('lbl')):
		fc['lbl'] = [ tt for t in lbl for tt in t.split(' ') ]	# s.a.
		del urlquery['lbl']
	if (cty := urlquery.get('cty')):
		fc['cty'] = [ tt for t in cty for tt in t.split(' ') ]	# s.a.
		del urlquery['cty']

	# add remaining arguments as attributes to filterCriteria
	for k in urlquery.keys():	
		fc[k] = urlquery.get(k)[0]

	# Add filterCriteria to request
	if len(fc):
		req['fc'] = fc

	if headers:			# extend with other headers
		for hdr,attr in [ (C.hfRVI, 'rvi'), (C.hfVSI, 'vsi'), (C.hfRET, 'rqet') ]:
			if (h := headers.get(hdr)) is not None:	# overwrite X-M2M-RVI header
				req[attr] = h
				del headers[hdr]
		# Special handling for rtu/nu, which is a sub-structure for rt.
		# Either get it (if exist), or create it. Then add nu, and add it again
		if (h := headers.get(C.hfRTU)) is not None:
			if (rtu := req.get('rt')) is None:
				rtu = dict()
			rtu['nu'] = h.split('&')	# -> list
			req['rt'] = rtu
			del headers[C.hfRTU]
	if data:
		req['pc'] = data	

	setLastRequestID(rqi)


	# Which topic to use for request and response?
	if ty == ResourceTypes.AE and operation == Operation.CREATE:
	# if originator in [ 'C', 'S', '', None ]:
		reqTopic  = MQTTREGREQUESTTOPIC
		respTopic = MQTTREGRESPONSETOPIC
	else:
		# Also if normale originator: Register originator with the MQTTClient
		topics 	  = mqttHandler.registerOriginator(originator)

		reqTopic  = topics.reqTopic
		respTopic = topics.respTopic
		
	# print(f'==> {reqTopic} / {req}')

	# send the data
	mqttHandler.publish(reqTopic, cast(bytes, RequestUtils.serializeData(req, ContentSerializationType.JSON)))  # TODO support cbor

	# Wait for response
	while True: 	# Timeout?
		try:
			if not DateUtils.waitFor(timeout=60.0, condition=lambda:rqi in mqttHandler.responses):
				print('MQTT Timeout')
				return None, 5103
			message = mqttHandler.responses.pop(rqi)
		except:
			return None, 5103

		if message[0] == respTopic:
			resp = message[1]
			# resp = RequestUtils.deserializeData(message[1], ContentSerializationType.JSON)

			# Since the tests usually work with http binding headers, some response attributes are converted
			hds = dict()
			if (rvi := resp.get('rvi')):
				hds[C.hfRVI] = rvi
			if (vsi := resp.get('vsi')):
				hds[C.hfVSI] = vsi
			setLastHeaders(hds)

			return resp['pc'] if 'pc' in resp else None, resp['rsc']



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
		return RETRIEVE(url, ORIGINATOR, timeout=1.0)[0] is not None
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
	try:
		_orgExpCheck = setExpirationCheck(expirationCheckDelay)
		_orgREQExpCheck = setRequestMinET(expirationCheckDelay)
		# Retrieve the max expiration delta from the CSE
		_maxExpiration = getMaxExpiration()
		_tooLargeExpirationDelta = _maxExpiration * 2	# double of what is allowed
	except:
		pass


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
		self.send_header(C.hfRSC, str(int(ResponseStatusCode.OK)))
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
	try:
		requests.post(NOTIFICATIONSERVER, verify=verifyCertificate)	# send empty/termination request
	except Exception:
		pass


def isNotificationServerRunning() -> bool:
	try:
		_ = requests.post(NOTIFICATIONSERVER, data='{"test": "test"}', verify=verifyCertificate)
		return True
	except Exception:
		return False

lastNotification:JSON				= None
lastNotificationHeaders:Parameters 	= {}

def setLastNotification(notification:JSON) -> None:
	global lastNotification
	lastNotification = notification

def getLastNotification(clear:bool=False) -> JSON:
	r = lastNotification
	if clear:
		clearLastNotification()
	return r

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


def uniqueRN(prefix:str='') -> str:
	"""	Create a unique resource name.
	"""
	return f'{prefix}{round(time.time() * 1000)}-{uniqueID()}'

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


# TODO check whether these functions can be replaced by the etc.DateUtils

def getDate(delta:int = 0) -> str:
	return toISO8601Date(datetime.datetime.utcnow() + datetime.timedelta(seconds=delta))


def toISO8601Date(ts: Union[float, datetime.datetime]) -> str:
	if isinstance(ts, float):
		ts = datetime.datetime.fromtimestamp(ts)
	return ts.strftime('%Y%m%dT%H%M%S,%f')


def printResult(result:unittest.TestResult) -> None:
	"""	Print the test results. """

	# Failures
	for f in result.failures:
		console.print(f'\n[bold][red]{f[0]}')
		console.print(f'[dim]{f[0].shortDescription()}')
		console.print(f[1])




###############################################################################




# Start MQTT Client if test protocol is mqtt
if PROTOCOL == 'mqtt':
	mqttHandler = MQTTClientHandler()
	mqttClient = MQTTConnection(mqttAddress, mqttPort, clientID=mqttClientID, username=mqttUsername, password=mqttPassword, messageHandler=mqttHandler)
	mqttClient.run()
	while not mqttHandler.connection:
		time.sleep(1)


###############################################################################

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)
noRemote = not connectionPossible(REMOTEcseURL)

