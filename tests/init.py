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
from glob import glob
from urllib.parse import ParseResult, urlparse, parse_qs
import sys, io, atexit
import unittest

from rich.console import Console
import requests, sys, json, time, ssl, urllib3, random, re, random
import cbor2
from typing import Any, Callable, Tuple, cast
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import cbor2

# sys.path.append('../acme')
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ContentSerializationType, Parameters, JSON, Operation, ResourceTypes, ResponseStatusCode
import acme.helpers.OAuth as OAuth
from acme.etc import RequestUtils, DateUtils
from acme.helpers.MQTTConnection import MQTTConnection, MQTTHandler
from acme.etc.Constants import Constants as C
from config import *


verifyCertificate			= False	# verify the certificate when using https?
oauthToken					= None	# current OAuth Token

# possible time delta between test system and CSE
# This is not really important, but for discoveries and others
timeDelta 					= 0 # seconds

# Expirations
expirationCheckDelay 		= 2	# seconds
expirationSleep				= expirationCheckDelay * 3

requestETDuration 			= f'PT{expirationCheckDelay:d}S'
requestETDuration2 			= f'PT{expirationCheckDelay*2:d}S'
requestETDurationInteger	= expirationCheckDelay * 1000
requestCheckDelay			= 1	#seconds
requestExpirationDelay		= 3.0

# TimeSeries Interval
timeSeriesInterval 			= 2.0 # seconds

# TimeSyncBeacon
tsbPeriodicInterval			= 1.0

# ReleaseVersionIndicator
RVI							='3'

from dataclasses import dataclass, field

@dataclass
class MQTTTopics:
	reqTopic:str
	respTopic:str
	subscribed:bool			= False


# TODO think about to move this?
class MQTTClientHandler(MQTTHandler):
	"""	Class for handling receiced MQTT requests.
	"""

	def	__init__(self) -> None:
		super().__init__()
		self.responses:dict[str, Tuple[str, JSON]] 	= dict()
		self.topics:dict[str, MQTTTopics]			= dict()
		self.connection:MQTTConnection				= None
		# self.respTopic 							= f'/oneM2M/resp/+{CSEID}/json'
		# self.ready 								= False

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
		if originator[0] == '/':	# Remove leading /, e.g. for csi
			originator = originator[1:]

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
# already as year 10000 (and this hits the limit of the isodate module implementation)

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

actrRN	= 'testACTR'
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
tsbRN	= 'testTSB'
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
tsBURL 	= f'{aeURL}/{tsbRN}'
actrURL = f'{aeURL}/{actrRN}'

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
		print(222)
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
		if C.hfOT in headers:	# set Originating Timestamo in header
			hds[C.hfOT] = str(headers[C.hfOT])
			del headers[C.hfOT]
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
	if (rp := urlquery.get('drt')):
		req['drt'] = int(rp[0])	# only first rp
		del urlquery['drt']
	
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
		for hdr,attr in [ (C.hfRVI, 'rvi'), (C.hfVSI, 'vsi'), (C.hfRET, 'rqet'), (C.hfOET, 'oet'), (C.hfOT, 'ot')]:
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
			if not DateUtils.waitFor(timeout = 60.0, condition = lambda:rqi in mqttHandler.responses):
				print('MQTT Timeout')
				return None, 5103
			message = mqttHandler.responses.pop(rqi)
		except:
			return None, 5103

		if message[0] == respTopic:
			resp = message[1]
			# resp = RequestUtils.deserializeData(message[1], ContentSerializationType.JSON)

			# Since the tests usually work with http binding headers, some response attributes are mapped
			hds = dict()
			for f, k in [ (C.hfRVI, 'rvi'), (C.hfVSI, 'vsi'), (C.hfOT, 'ot') ]:
				if k in resp:
					hds[f] = resp[k]
			setLastHeaders(hds)

			return resp['pc'] if 'pc' in resp else None, resp['rsc']



_lastRequstID = None

def setLastRequestID(rid:str) -> None:
	"""	Set the last request's ID.
	
		Args:
			rid: Request ID	
	"""
	global _lastRequstID
	_lastRequstID = rid


def lastRequestID() -> str:
	return _lastRequstID


def connectionPossible(url:str) -> bool:
	"""	Check whether a connection to the CSE is possible and the CSE is running. This is
		done by retrieving the CSEBase using the protocol binding that tis used also
		for the rest of the tests. So, it the Upper Tester interface is not used.

		Args:
			url: The URL of the CSEBase
		
		Return:
			Return the status (reachable and available).
	"""
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
#	Reconfiguring CSE via the upper tester interface
#

_orgExpCheck = -1
_orgREQExpCheck = -1
_maxExpiration = -1
_tooLargeResourceExpirationDelta = -1
_orgRequestExpirationDelta = -1.0


# Reconfigure the server to check faster for expirations. This is set to the
# old value in the tearDowndClass() method.
def enableShortResourceExpirations() -> None:
	"""	Enable the short resource expiration in the CSE.
	"""
	global _orgExpCheck, _maxExpiration, _tooLargeResourceExpirationDelta

	# Send UT request
	resp = requests.post(UTURL, headers = { UTCMD: f'enableShortResourceExpiration {expirationCheckDelay}'})
	_maxExpiration = -1
	_orgExpCheck = -1
	if resp.status_code == 200:
		if UTRSP in resp.headers:
			rsp = resp.headers[UTRSP].split(',')
			_orgExpCheck = int(rsp[0])
			_maxExpiration = int(rsp[1])
			_tooLargeResourceExpirationDelta = _maxExpiration * 2	# double of what is allowed


def disableShortResourceExpirations() -> None:
	"""	Disable the short resource expiration in the CSE.
	"""
	global _orgExpCheck, _orgREQExpCheck
	if _orgExpCheck != -1:
		# Send UT request
		resp = requests.post(UTURL, headers = { UTCMD: f'disableShortResourceExpiration'})
		if resp.status_code == 200:
			_orgExpCheck = -1
			_orgREQExpCheck = -1


def isTestResourceExpirations() -> bool:
	"""	Test whether the resource expiration values have been configured for testing.

		Return:
			Boolean.
	"""
	return _orgExpCheck != -1


def tooLargeResourceExpirationDelta() -> int:
	"""	Return the configured "too large" value for resource expiration delta.

		Return:
			Integer, the too large expiration delta, or -1 of it is not configured.
	"""
	return _tooLargeResourceExpirationDelta


# Reconfigure the server to check faster for sent request expirations. This is set to the
# old value in the tearDowndClass() method.
def enableShortRequestExpirations() -> None:
	"""	Enable the short request expiration in the CSE.
	"""
	global _orgRequestExpirationDelta

	# Send UT request
	resp = requests.post(UTURL, headers = { UTCMD: f'enableShortRequestExpiration {requestExpirationDelay}'})
	if resp.status_code == 200:
		if UTRSP in resp.headers:
			_orgRequestExpirationDelta = float(resp.headers[UTRSP])


def disableShortRequestExpirations() -> None:
	"""	Disable the short request expiration in the CSE.
	"""
	global _orgRequestExpirationDelta
	
	# Send UT request
	resp = requests.post(UTURL, headers = { UTCMD: f'disableShortRequestExpiration'})
	if resp.status_code == 200:
		_orgRequestExpirationDelta = -1.0
	

def isShortRequestExpirations() -> bool:
	"""	Test whether the request expiration have been configured for testing.

		Return:
			Boolean.
	"""
	return _orgRequestExpirationDelta != -1.0

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
		global nextNotificationResult

		# Construct return header
		# Always acknowledge the verification requests
		self.send_response(nextNotificationResult.httpStatusCode())
		self.send_header(C.hfRSC, str(int(nextNotificationResult)))
		self.send_header(C.hfOT, DateUtils.getResourceDate())
		self.send_header(C.hfOrigin, ORIGINATORResp)
		if C.hfRI in self.headers:
			self.send_header(C.hfRI, self.headers[C.hfRI])
		self.end_headers()
		nextNotificationResult = ResponseStatusCode.OK

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
	waitMessage('Starting notification server', 2)


def stopNotificationServer() -> None:
	global keepNotificationServerRunning
	keepNotificationServerRunning = False
	try:
		requests.post(NOTIFICATIONSERVER, verify=verifyCertificate)	# send empty/termination request
	except Exception:
		pass
	waitMessage('Stopping notification server', 2.0)



def isNotificationServerRunning() -> bool:
	try:
		_ = requests.post(NOTIFICATIONSERVER, data='{"test": "test"}', verify=verifyCertificate)
		return True
	except Exception:
		return False

lastNotification:JSON						= None
lastNotificationHeaders:Parameters 			= {}
nextNotificationResult:ResponseStatusCode	= ResponseStatusCode.OK

def setLastNotification(notification:JSON) -> None:
	global lastNotification
	lastNotification = notification


def getLastNotification(clear:bool=False) -> JSON:
	r = lastNotification
	if clear:
		clearLastNotification()
	return r


def clearLastNotification(nextResult:ResponseStatusCode = ResponseStatusCode.OK) -> None:
	global lastNotification, lastNotificationHeaders, nextNotificationResult
	lastNotification = None
	lastNotificationHeaders = None
	nextNotificationResult = nextResult


def setLastNotificationHeaders(headers:Parameters) -> None:
	global lastNotificationHeaders
	lastNotificationHeaders = headers


def getLastNotificationHeaders() -> Parameters:
	return lastNotificationHeaders


#
#	Utilities
#	Some are copied from acme.etc.Utils . 
#	We wont import Utils, because of circular imports with other CSE modules
#


def printResult(result:unittest.TestResult) -> None:
	"""	Print the test results. """

	# Failures
	for f in result.failures:
		console.print(f'\n[bold][red]{f[0]}')
		console.print(f'[dim]{f[0].shortDescription()}')
		console.print(f[1])

def waitMessage(msg:str, delay:float) -> None:
	if delay:
		with console.status(f'[bright_blue]{msg}') as status:
			time.sleep(delay)
	else:
		console.print(f'[bright_blue]{msg}')


def uniqueID() -> str:
	return str(random.randint(1,sys.maxsize))


def uniqueRN(prefix:str='') -> str:
	"""	Create a unique resource name.
	"""
	return f'{prefix}{round(time.time() * 1000)}-{uniqueID()}'



decimalMatch = re.compile(r'{(\d+)}')
def findXPath(dct:JSON, key:str, default:Any=None) -> Any:
	""" Find a structured `key` in the dictionary `dct`. If `key` does not exists then
		`default` is returned.

		It is possible to address a specific element in an array. This is done be
		specifying the element as `{n}`.

		Example: findXPath(resource, 'm2m:cin/{1}/lbl/{0}')

		If an element if specified as '{}' then all elements in that array are returned in
		an array.

		Example: findXPath(resource, 'm2m:cin/{1}/lbl/{}') or findXPath(input, 'm2m:cnt/m2m:cin/{}/rn')

	"""

	if not key or not dct:
		return default

	paths = key.split("/")
	data:Any = dct
	for i in range(0,len(paths)):
		if not data:
		 	return default
		pathElement = paths[i]
		if len(pathElement) == 0:	# return if there is an empty path element
			return default
		elif (m := decimalMatch.search(pathElement)) is not None:	# Match array index {i}
			idx = int(m.group(1))
			if not isinstance(data, (list,dict)) or idx >= len(data):	# Check idx within range of list
				return default
			if isinstance(data, dict):
				data = data[list(data)[i]]
			else:
				data = data[idx]

		elif pathElement == '{}':	# Match an array in general
			if not isinstance(data, (list,dict)):	# not a list, return the default
				return default
			if i == len(paths)-1:	# if this is the last element and it is a list then return the data
				return data
			return [ findXPath(d, '/'.join(paths[i+1:]), default) for d in data  ]	# recursively build an array with remnainder of the selector

		elif pathElement not in data:	# if key not in dict
			return default
		else:
			data = data[pathElement]	# found data for the next level down
	return data


def setXPath(dct:JSON, key:str, value:Any, overwrite:bool=True) -> bool:
	"""	Set a structured `key` and `value` in the dictionary `dict`. 
		Create if necessary, and observe the `overwrite` option (True overwrites an
		existing key/value).
	"""
	paths = key.split("/")
	ln1 = len(paths)-1
	data = dct
	if ln1 > 0:	# Small optimization. don't check if there is no extended path
		for i in range(0,ln1):
			if paths[i] not in data:
				data[paths[i]] = {}
			data = data[paths[i]]
	# if not isinstance(data, dict):
	# 	return False
	if not overwrite and paths[ln1] in data: # test overwrite first, it's faster
		return True # don't overwrite
	data[paths[ln1]] = value
	return True

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

try:
	if requests.post(UTURL, headers = { UTCMD: f'status'}).status_code == 501:
		console.print('[red]Upper Tester Interface not enabeled in CSE')
		console.print('Enable with configuration setting: "\[server.http]:enableUpperTesterEndpoint=True"')
		quit(-1)
except (ConnectionRefusedError, requests.exceptions.ConnectionError):
	console.print('[red]Connection to CSE not possible[/red]\nIs it running?')
	quit(-1)

