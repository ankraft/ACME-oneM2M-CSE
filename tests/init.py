#
#	init.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configuration & helper functions for unit tests
#

from __future__ import annotations
from typing import Any, Callable, Tuple, cast, Optional, TypeAlias, Type
from dataclasses import dataclass

from urllib.parse import ParseResult, urlparse, parse_qs
import sys, io, atexit, base64
import unittest
from datetime import timedelta


import requests.adapters
from rich import inspect
from rich.console import Console
import requests, sys, json, time, ssl, urllib3, random, re, random, importlib
from datetime import datetime, timezone
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import cbor2
from websockets.sync.client import connect, ClientConnection
from websockets.sync.connection import Connection as WSConnection
from websockets.exceptions import ConnectionClosed

# sys.path.append('../acme')
if '..' not in sys.path:
	sys.path.append('..')

# CoAP Libraries
from coapthon import defines	# actually this is the import from ACME
from coapthon.client.helperclient import HelperClient as CoAPClient
from coapthon.messages.option import Option as CoAPOption
from coapthon.messages.request import Request as CoAPRequest
from coapthon.messages.response import Response as	CoAPResponse


from acme.etc import DateUtils, RequestUtils
from acme.etc.Types import ContentSerializationType, Parameters, JSON, Operation, ResourceTypes, ResponseStatusCode, ResponseType
import acme.helpers.OAuth as OAuth
from acme.helpers import CoAPthonTools
from acme.helpers.MQTTConnection import MQTTConnection, MQTTHandler
from acme.etc.Constants import Constants as C
from acme.etc.ResponseStatusCodes import INTERNAL_SERVER_ERROR
from config import *


TestResult:TypeAlias = Tuple[int, int, int, float]
"""	Results of a test case. The tuple contains the following values:

	- number of tests executed
	- number of errors
	- number of skipped tests
	- time spent sleeping in the test cases
"""

verifyCertificate = False						# verify the certificate when using https?
oauthToken = None								# current OAuth Token
verboseRequests = False							# Print requests and responses
testCaseNames:Optional[list[str]] = None		# List of test cases to run
excludedTestNames:Optional[list[str]] = []		# List of test cases to exclude
enableTearDown = True  							# Run or don't run TearDownClass test case methods
initialRequestTimeout  = 10.0					# Timeout in s for the initial connectivity test.
localNotificationServer = False					# Use a local notification server address

# possible time delta between test system and CSE
# This is not really important, but for discoveries and others
timeDelta 					= 0 # seconds

# Notifications
notificationDelay 			= NOTIFICATIONDELAY

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

# crossResourceSubscription Time Window Size (s)
crsTimeWindowSize			= 4.0

# actionPeriod
actionPeriod				= 1 * 1000 # seconds

# Test Suite Verbosity (0-2)
testVerbosity				= 2





@dataclass
class MQTTTopics:
	reqTopic:str
	respTopic:str
	subscribed:bool			= False


# TODO move utility functions somewhere else?
# TODO make use of upper tester configurable
# TODO Better fine-grain excluding of expiration tests when

# TODO think about to move mqtt and http bindings to separate source files

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
		# print(f'<== {topic} / {data}')
		resp = RequestUtils.deserializeData(data, ContentSerializationType.JSON)
		if 'rqi' in resp:
			self.responses[resp['rqi']] = (topic, resp)
		else:
			print(f'no rqi in message: {resp}')


	def publish(self, topic:str, data:bytes) -> None:
		 #print(f'==> {topic} / {data}')
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
			testSleep(0.01)

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


# CoAP Client
coapClient:CoAPClient = None
CoAPthonTools.registerOneM2MOptions()		# register extra options
CoAPthonTools.registerOneM2MContentTypes()	# register extra content types


# HTTP Session
httpSession:requests.Session = None

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
crsRN	= 'testCRS'
csrRN	= 'testCSR'
deprRN	= 'testDEPR'
fcntRN	= 'testFCNT'
grpRN	= 'testGRP'
lcpRN	= 'testLCP'
nodRN 	= 'testNOD'
ntpRN	= 'testNTP'
ntprRN	= 'testNTPR'
pchRN 	= 'testPCH'
pdrRN 	= 'testPDR'
prmrRN	= 'testPRMR'
prpRN	= 'testPRP'
reqRN	= 'testREQ'
schRN 	= 'testSCH'
smdRN	= 'testSMD'
subRN	= 'testSUB'
stteRN	= 'testSTTE'
tsRN	= 'testTS'
tsbRN	= 'testTSB'
tsiRN	= 'testTSI'
memRN	= 'testMEM'
wificRN	= 'testWIFIC'


cseURL 	= f'{CSEURL}{CSERN}'
csiURL 	= f'{CSEURL}{CSEID}'
aeURL 	= f'{cseURL}/{aeRN}'
acpURL 	= f'{cseURL}/{acpRN}'
cntURL 	= f'{aeURL}/{cntRN}'
cinURL 	= f'{cntURL}/{cinRN}'	# under the <cnt>
crsURL	= f'{aeURL}/{crsRN}'
csrURL	= f'{cseURL}/{csrRN}'
fcntURL	= f'{aeURL}/{fcntRN}'
grpURL 	= f'{aeURL}/{grpRN}'
lcpURL 	= f'{aeURL}/{lcpRN}'	# under the <ae>
nodURL 	= f'{cseURL}/{nodRN}'	# under the <ae>
ntpURL 	= f'{cseURL}/{ntpRN}'	# under the <cse>
pchURL 	= f'{aeURL}/{pchRN}'
pdrURL 	= f'{ntpURL}/{pdrRN}'	# under the <ntp>
pcuURL 	= f'{pchURL}/pcu'
smdURL 	= f'{aeURL}/{smdRN}'	# under the <ae>
subURL 	= f'{cntURL}/{subRN}'	# under the <cnt>
tsURL 	= f'{aeURL}/{tsRN}'
tsBURL 	= f'{aeURL}/{tsbRN}'
actrURL = f'{cntURL}/{actrRN}'
deprURL = f'{actrURL}/{deprRN}'
prmrURL = f'{aeURL}/{prmrRN}'
stteURL = f'{prmrURL}/{stteRN}'
prpURL 	= f'{cseURL}/{prpRN}'


batURL 	= f'{nodURL}/{batRN}'	# under the <nod>
memURL	= f'{nodURL}/{memRN}'	# under the <nod>


REMOTEcseURL 	= f'{REMOTECSEURL}{REMOTECSERN}'
localCsrURL 	= f'{cseURL}{REMOTECSEID}'
remoteCsrURL 	= f'{REMOTEcseURL}{CSEID}'

###############################################################################


@atexit.register
def shutdown() -> None:
	"""	Shutdown the system. 
	"""
	global mqttClient, coapClient
	if mqttClient:
		mqttClient.shutdown()
		mqttClient = None
	if coapClient:
		coapClient.close()
		coapClient = None
	
	for _, websocket in websockets.items():
		websocket.close()

###############################################################################

#
#	Requests
#

requestCount:int = 0

def _RETRIEVE(url:str, originator:str, timeout:float=None, headers:Parameters={}) -> Tuple[str|JSON, int]:
	return sendRequest(Operation.RETRIEVE, url, originator, timeout=timeout, headers=headers)

def RETRIEVESTRING(url:str, originator:str, timeout:float=None, headers:Parameters={}) -> Tuple[str, int]:
	x,rsc = _RETRIEVE(url=url, originator=originator, timeout=timeout, headers=headers)
	return str(x, 'utf-8'), rsc		# type:ignore[call-overload]

def RETRIEVE(url:str, originator:str, timeout:float=None, headers:Parameters={}) -> Tuple[JSON, int]:
	x,rsc = _RETRIEVE(url=url, originator=originator, timeout=timeout, headers=headers)
	return cast(JSON, x), rsc

def CREATE(url:str, originator:str, ty:ResourceTypes=None, data:JSON=None, headers:Parameters={}) -> Tuple[JSON, int]:
	x,rsc = sendRequest(Operation.CREATE, url, originator, ty, data, headers=headers)
	return cast(JSON, x), rsc

def NOTIFY(url:str, originator:str, data:JSON=None, headers:Parameters={}) -> Tuple[JSON, int]:
	x,rsc = sendRequest(Operation.NOTIFY, url, originator, data=data, headers=headers)
	return cast(JSON, x), rsc

def _UPDATE(url:str, originator:str, data:JSON|str, headers:Parameters={}) -> Tuple[str|JSON, int]:
	return sendRequest(Operation.UPDATE, url, originator, data=data, headers=headers)

def UPDATESTRING(url:str, originator:str, data:str, headers:Parameters={}) -> Tuple[str, int]:
	x, rsc = _UPDATE(url=url, originator=originator, data=data, headers=headers)
	return str(x, 'utf-8'), rsc		# type:ignore[call-overload]

def UPDATE(url:str, originator:str, data:JSON, headers:Parameters={}) -> Tuple[JSON, int]:
	x, rsc = _UPDATE(url=url, originator=originator, data=data, headers=headers)
	return cast(JSON, x), rsc

def DELETE(url:str, originator:str, headers:Parameters={}) -> Tuple[JSON, int]:
	x, rsc = sendRequest(Operation.DELETE, url, originator, headers=headers)
	return cast(JSON, x), rsc


def sendRequest(operation:Operation, 
				url:str, 
				originator:str, 
				ty:ResourceTypes=None, 
				data:JSON|str=None, 
				ct:str='application/json', 
				timeout:float=None, 
				headers:Parameters = {}) -> Tuple[STRING|JSON, int]:	# type: ignore # TODO Constants
	"""	Send a request. Call the appropriate framework, depending on the protocol.
	"""
	global requestCount, httpSession
	requestCount += 1
	if url.startswith(('http', 'https')):
		if not httpSession:
			httpSession = requests.Session()
			httpAdapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=20)
			httpsAdapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=20)
			httpSession.mount('http://', httpAdapter)
			httpSession.mount('https://', httpsAdapter)


		# if operation == Operation.CREATE:
		# 	return sendHttpRequest(requests.post, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		# elif operation == Operation.RETRIEVE:
		# 	return sendHttpRequest(requests.get, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		# elif operation == Operation.UPDATE:
		# 	return sendHttpRequest(requests.put, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		# elif operation == Operation.DELETE:
		# 	return sendHttpRequest(requests.delete, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		# elif operation == Operation.NOTIFY:
		# 	return sendHttpRequest(requests.post, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
		match operation:
			case Operation.CREATE:
				return sendHttpRequest('post', url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.RETRIEVE:
				return sendHttpRequest('get', url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.UPDATE:
				return sendHttpRequest('put', url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.DELETE:
				return sendHttpRequest('delete', url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.NOTIFY:
				return sendHttpRequest('post', url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			
	elif url.startswith('mqtt'):
		match operation:
			case Operation.CREATE:
				return sendMqttRequest(Operation.CREATE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.RETRIEVE:
				return sendMqttRequest(Operation.RETRIEVE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.UPDATE:
				return sendMqttRequest(Operation.UPDATE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.DELETE:
				return sendMqttRequest(Operation.DELETE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.NOTIFY:
				return sendMqttRequest(Operation.NOTIFY, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
	
	elif url.startswith(('ws', 'wss')):
		match operation:
			case Operation.CREATE:
				return sendWsRequest(Operation.CREATE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.RETRIEVE:
				return sendWsRequest(Operation.RETRIEVE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.UPDATE:
				return sendWsRequest(Operation.UPDATE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.DELETE:
				return sendWsRequest(Operation.DELETE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.NOTIFY:
				return sendWsRequest(Operation.NOTIFY, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)

	elif url.startswith(('coap', 'coaps')):
		match operation:
			case Operation.CREATE:
				return sendCoapRequest(Operation.CREATE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.RETRIEVE:
				return sendCoapRequest(Operation.RETRIEVE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.UPDATE:
				return sendCoapRequest(Operation.UPDATE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.DELETE:
				return sendCoapRequest(Operation.DELETE, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)
			case Operation.NOTIFY:
				return sendCoapRequest(Operation.NOTIFY, url=url, originator=originator, ty=ty, data=data, ct=ct, timeout=timeout, headers=headers)

	print('ERROR')
	return None, 5103


def _packRequest(operation:Operation, url:str, originator:str, ty:int=None, data:JSON|str=None, ct:str=None, headers:Parameters=None) -> Tuple[JSON, str, ParseResult]:
	urlComponents:ParseResult = urlparse(url)
	urlquery = parse_qs(urlComponents.query)
	#print(urlquery)

	req:dict	= dict()
	fc:dict		= dict()
	req['fr'] 	= originator
	req['to'] 	= urlComponents.path[1:]	# remove the leading / of an url ( usually the root path)
	req['op'] 	= operation.value
	req['rqi'] 	= (rqi := uniqueID())
	req['rvi'] 	= RELEASEVERSION

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
		req['drt'] = int(rp[0])	# only first drt
		del urlquery['drt']
	if (sqi := urlquery.get('sqi')):
		req['sqi'] = sqi[0]	# only first sqi
		del urlquery['sqi']

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

	# add some attributes to CONTENT
	if (atrl := urlquery.get('atrl')):
		if data is not None:
			raise INTERNAL_SERVER_ERROR('data must be not set when using "atrl"')
		data = dict()
		data['m2m:atrl'] =  [ tt for t in atrl for tt in t.split(' ') ]
		# Add CONTENT
		del urlquery['atrl']

	# add remaining arguments as attributes to filterCriteria
	for k in urlquery.keys():	
		fc[k] = urlquery.get(k)[0]

	# Add filterCriteria to request
	if len(fc):
		req['fc'] = fc

	if headers:			# extend with other headers
		for hdr,attr in [ (C.hfRVI, 'rvi'), (C.hfVSI, 'vsi'), (C.hfRET, 'rqet'), (C.hfOET, 'oet'), (C.hfOT, 'ot'), (C.hfRST, 'rset')]:
			if (h := headers.get(hdr)) is not None:
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

	return req, rqi, urlComponents



def addHttpAuthorizationHeader(headers:Parameters) -> Optional[Tuple[str, int]]:
	global oauthToken

	if doOAuth:
		if (token := OAuth.getOAuthToken(oauthServerUrl, oauthClientID, oauthClientSecret, oauthToken)) is None:
			return 'error retrieving oauth token', 5103
		oauthToken = token
		headers['Authorization'] = f'Bearer {oauthToken.token}'
	elif doHttpBasicAuth:
		_t = f'{httpUserName}:{httpPassword}'
		headers['Authorization'] = f'Basic {base64.b64encode(_t.encode("utf-8")).decode("utf-8")}'
	elif doHttpTokenAuth:
		headers['Authorization'] = f'Bearer {httpAuthToken}'
	return None


def sendHttpRequest(method:str, url:str, originator:str, ty:ResourceTypes=None, data:JSON|str=None, ct:str=None, timeout:float=None, headers:Parameters=None) -> Tuple[STRING|JSON, int]:	# type: ignore # TODO Constants
	global httpSession

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
		C.hfRVI				: RELEASEVERSION,
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
	if (_r := addHttpAuthorizationHeader(hds)) is not None:
		return _r

	# if doOAuth:
	# 	if (token := OAuth.getOAuthToken(oauthServerUrl, oauthClientID, oauthClientSecret, oauthToken)) is None:
	# 		return 'error retrieving oauth token', 5103
	# 	oauthToken = token
	# 	hds['Authorization'] = f'Bearer {oauthToken.token}'
	# elif doHttpBasicAuth:
	# 	_t = f'{httpUserName}:{httpPassword}'
	# 	hds['Authorization'] = f'Basic {base64.b64encode(_t.encode("utf-8")).decode("utf-8")}'
	# elif doHttpTokenAuth:
	# 	hds['Authorization'] = f'Bearer aRandomToken'

	# Verbose output
	if verboseRequests:
		console.print('\n[b u]Request')
		console.print(f'[dark_orange]{method}[/dark_orange] {url}')
		console.print('\n'.join([f'{h}: {v}' for h,v in hds.items()]))
		console.print()
		if isinstance(data, dict):
			console.print_json(data=data)

	setLastRequestID(rid)
	try:
		sendData:Optional[str] = None
		if data is not None:
			if isinstance(data, dict):	# actually JSON, but isinstance() cannot be used with generics
				sendData = json.dumps(data)
			else:
				sendData = data
			# data = cbor2.dumps(data)	# TODO use CBOR as well
		r = httpSession.request(method=method, url=url, data=sendData, headers=hds, verify=verifyCertificate, timeout=timeout)
	except Exception as e:
		# print(f'Failed to send request: {str(e)}')
		return f'Failed to send request: {str(e)}', 5103
	
	rc = int(r.headers.get(C.hfRSC, r.status_code))
	if rc == 204:
		rc = ResponseStatusCode.NO_CONTENT

	# save last header for later
	setLastHeaders(r.headers)	# type: ignore[arg-type]

	# Verbose output
	if verboseRequests:
		console.print(f'\n[b u]Response - {r.status_code}')
		console.print('\n'.join([f'{h}: {v}' for h,v in r.headers.items()]))
		if r.content:
			console.print()
			console.print(r.json())

	# return plain text
	if (ct := r.headers.get('Content-Type')) is not None and ct.startswith('text/plain'):
		return r.content, rc
	elif ct is not None and ct.startswith(('application/json', 'application/vnd.onem2m-res+json')):
		return r.json() if len(r.content) > 0 else None, rc
	# just return what's in there
	return r.content, rc


def sendMqttRequest(operation:Operation, url:str, originator:str, ty:int=None, data:JSON|str=None, ct:str=None, timeout:float=None, headers:Parameters=None) -> Tuple[STRING|JSON, int]:	# type: ignore # TODO Constants

	req, rqi, urlComponents = _packRequest(operation, url, originator, ty, data, ct, headers)

	# MQTT: Which topic to use for request and response?
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

	# Verbose output
	if verboseRequests:
		console.print('\n[b u]Request')
		console.print(f'[dark_orange]{reqTopic}[/dark_orange]')
		console.print(req)

	# send the data
	mqttHandler.publish(reqTopic, cast(bytes, RequestUtils.serializeData(req, ContentSerializationType.JSON)))  # TODO support cbor

	# Wait for response? 
	if (_rt := req.get('rt')):
		if _rt.get('rtv') == ResponseType.noResponse.value:
			return '', ResponseStatusCode.NO_CONTENT

	# Wait for response
	while True: 	# Timeout?
		try:
			if not DateUtils.waitFor(timeout = 60.0, condition = lambda:rqi in mqttHandler.responses):
				console.print('MQTT Timeout')
				return None, 5103
			message = mqttHandler.responses.pop(rqi)
		except:
			return None, 5103

		# Verbose output
		if verboseRequests:
			console.print('\n[b u]Response')
			console.print(f'[dark_orange]{message[0]}[/dark_orange]')
			console.print(message[1])


		if message[0] == respTopic:
			resp = message[1]
			# resp = RequestUtils.deserializeData(message[1], ContentSerializationType.JSON)

			# Since the tests usually work with http binding headers, some response attributes are mapped
			# hds = dict()
			# for f, k in [ (C.hfRVI, 'rvi'), (C.hfVSI, 'vsi'), (C.hfOT, 'ot') ]:
			# 	if k in resp:
			# 		hds[f] = resp[k]
			setLastHeaders(fillLastHeaders(resp))

			return resp.get('pc'), resp['rsc']


websockets:dict[str, ClientConnection] = dict()
wsin:int = 0

def sendWsRequest(operation:Operation, 
				  url:str, 
				  originator:str, 
				  ty:int=None, 
				  data:JSON|str=None, 
				  ct:str=None, 
				  timeout:float=10.0, 
				  headers:Parameters=None) -> Tuple[STRING|JSON, int]:	# type: ignore # TODO Constants
	req, rqi, urlComponents = _packRequest(operation, url, originator, ty, data, ct, headers)

	def isWSOpen(websocket:WSConnection) -> bool:
		try:
			websocket.recv(timeout = 0)
		except ConnectionClosed as e:
			return False
		except:
			return True
		return True


	# Verbose output
	if verboseRequests:
		console.print('\n[b u]Request')
		console.print(f'[dark_orange]{PROTOCOL}://{wsAddress}:{wsPort}[/dark_orange]')
		console.print(req)


	# TODO addioanl headers: 'X-M2M-Origin': 'CAdmin'
		
	additionalHeaders = { }	if not originator else { 'X-M2M-Origin': originator }

	websocket = websockets.get(originator)
	if not isWSOpen(websocket):
		websocket.close()
		websockets.pop(originator)
		websocket = None

	if not websocket:
		context:ssl.SSLContext = None
		if urlComponents.scheme == 'wss':
			context = ssl.create_default_context()
			if not verifyCertificate:
				context.check_hostname = False
				context.verify_mode = ssl.CERT_NONE

		websocket = connect(f'{PROTOCOL}://{wsAddress}:{wsPort}', 
					  		subprotocols = wsSubProtocols, 	# type:ignore [arg-type]
							additional_headers = additionalHeaders, 
							ssl_context = context)
		websockets[originator] = websocket

	# TODO support cbor

	websocket.send(cast(bytes, RequestUtils.serializeData(req, ContentSerializationType.JSON)))
	# TODO Decouple WS receiving to support notifications via 

	# Wait for response? 
	if (_rt := req.get('rt')):
		if _rt.get('rtv') == ResponseType.noResponse.value:
			return '', ResponseStatusCode.NO_CONTENT

	# Waiting for response
	try:
		while True:
			if (response := websocket.recv(timeout = timeout)):
				resp = RequestUtils.deserializeData(bytes(response, 'utf-8') if isinstance(response, str) else response,
										 			ContentSerializationType.JSON)
				setLastHeaders(fillLastHeaders(resp))
				return resp.get('pc'), resp['rsc']
			else:
				console.print(response)
				console.print('.', end='')
				return None, 0
	except TimeoutError:	# expected
		console.print('timeout')
		pass
	return None, 0



def sendCoapRequest(operation:Operation, 
					url:str, 
					originator:str, 
					ty:ResourceTypes=None, 
					data:JSON|str = None, 
					ct:str=None, 
					timeout:float=None, 
					headers:Parameters=None) -> Tuple[str|JSON, int]:	# type: ignore # TODO Constants
	
	if timeout is None:
		timeout = coapTimeout	# not an argument default, because a calling function might set it to None

	def _addCoAPOption(request:CoAPRequest, number:int, value:Any) -> None:
		option = CoAPOption()
		option.number = number
		option.value = value
		request.add_option(option)
	

	urlComponents:ParseResult = urlparse(RequestUtils.toHttpUrl(url))

	# TODO DTLS socket
	# TODO add verboserequest output
	global coapClient
	if not coapClient:
		coapClient = CoAPClient(server=(urlComponents.hostname, urlComponents.port))

	request = CoAPRequest()

	# Set the appropriate CoAP code
	match operation:
		case Operation.CREATE:
			request.code = defines.Codes.POST.number
		case Operation.RETRIEVE if RELEASEVERSION == '5':
			request.code = defines.Codes.FETCH.number
		case Operation.RETRIEVE:
			request.code = defines.Codes.GET.number
		case Operation.UPDATE:
			request.code = defines.Codes.PUT.number
		case Operation.DELETE:
			request.code = defines.Codes.DELETE.number
		case Operation.NOTIFY:
			request.code = defines.Codes.POST.number

	request.type = defines.Types['CON']
	request.destination = urlComponents.hostname, urlComponents.port
	request.uri_path = urlComponents.path[1:]


	# CoAP Options
	_addCoAPOption(request, defines.OptionRegistry.CONTENT_TYPE.number, defines.Content_types[ct])

	if RELEASEVERSION == '5':
		console.print('[red]Warning: CoAP binding for Release 5 is not yet supported')
		quit()
		# if data is None:
		# 	data = dict()
		# else:
		# 	data_pc = data
		# 	data = dict()
		# 	data['pc'] = data_pc

		# if ty is not None:
		# 	data['ty'] = int(ty)

		# if originator is not None:
		# 	data['fr'] = originator

		# data['rqi'] = uniqueID()
		# if C.hfRVI in headers:	# overwrite RVI option
		# 	data['rvi'] = headers[C.hfRVI]
		# 	del headers[C.hfRVI]
		# else:
		# 	data['rvi'] = RELEASEVERSION

	else:
		# OneM2M Options
		if ty is not None:
			_addCoAPOption(request, defines.OptionRegistry.oneM2M_TY.number, int(ty))				# type:ignore[attr-defined]

		if originator is not None:
			_addCoAPOption(request, defines.OptionRegistry.oneM2M_FR.number, originator)			# type:ignore[attr-defined]

		_addCoAPOption(request, defines.OptionRegistry.oneM2M_RQI.number, rid := uniqueID())		# type:ignore[attr-defined]
		setLastRequestID(rid)

		if C.hfRVI in headers:	# overwrite RVI option
			_addCoAPOption(request, defines.OptionRegistry.oneM2M_RVI.number, headers[C.hfRVI])		# type:ignore[attr-defined]
			del headers[C.hfRVI]
		else:
			_addCoAPOption(request, defines.OptionRegistry.oneM2M_RVI.number, RELEASEVERSION)		# type:ignore[attr-defined]
		if C.hfVSI in headers:
			_addCoAPOption(request, defines.OptionRegistry.oneM2M_VSI.number, headers[C.hfVSI])		# type:ignore[attr-defined]
			del headers[C.hfVSI]
		if C.hfRET in headers:
			_addCoAPOption(request, defines.OptionRegistry.oneM2M_RQET.number, headers[C.hfRET])	# type:ignore[attr-defined]
			del headers[C.hfRET]
		if C.hfOET in headers:
			_addCoAPOption(request, defines.OptionRegistry.oneM2M_OET.number, headers[C.hfOET])		# type:ignore[attr-defined]
			del headers[C.hfOET]
		if C.hfRST in headers:
			_addCoAPOption(request, defines.OptionRegistry.oneM2M_RSET.number, headers[C.hfRST])	# type:ignore[attr-defined]
			del headers[C.hfRST]
		if C.hfRTU in headers:
			_addCoAPOption(request, defines.OptionRegistry.oneM2M_RTURI.number, headers[C.hfRTU])	# type:ignore[attr-defined]
			del headers[C.hfRTU]
		if C.hfOT in headers:
			_addCoAPOption(request, defines.OptionRegistry.oneM2M_OT.number, headers[C.hfOT])		# type:ignore[attr-defined]
			del headers[C.hfOT]

	if len(headers):
		console.print(f'[red]Warning: {headers} not used in CoAP request')

	# Set CoAP payload
	if data is not None and isinstance(data, dict):
		request.payload = bytes(json.dumps(data), 'utf-8')
	
	# Add query parameters 
	request.uri_query = urlComponents.query

	# check for response type == no response
	awaitNoResponse = parse_qs(request.uri_query).get('rt') == ['5'] # no response

	# Send the CoAP request
	try:
		response = coapClient.send_request(request, timeout = timeout, no_response = awaitNoResponse)
	except Exception as e:
		return 'Failed to send CoAP request', 5103

	if response is None:
		return '', 5103 if not awaitNoResponse else ResponseStatusCode.NO_CONTENT

	content_type = response.content_type

	options = response.options
	rsc = None
	rvi = None
	resp:JSON = {}
	for option in options:
		match option.number:
			case defines.OptionRegistry.oneM2M_RSC.number:		# type:ignore[attr-defined]
				rsc = cast(int, option.value)
				resp['rsc'] = rsc
			case defines.OptionRegistry.oneM2M_RVI.number:		# type:ignore[attr-defined]
				rvi = cast(str, option.value)
				resp['rvi'] = rvi
			case defines.OptionRegistry.oneM2M_VSI.number:		# type:ignore[attr-defined]
				resp['vsi'] = cast(str, option.value)
			case defines.OptionRegistry.oneM2M_OT.number:		# type:ignore[attr-defined]
				resp['ot'] = cast(str, option.value)
			case defines.OptionRegistry.oneM2M_RSET.number:		# type:ignore[attr-defined]
				resp['rset'] = cast(str, option.value)
	
	# Set the last response header for the test cases to check later
	setLastHeaders(fillLastHeaders(resp))

	if response.payload:
		payload = cast(JSON, json.loads(response.payload))
		if rvi == '5':
			if 'pc' in payload:
				return payload['pc'], rsc
		else:
			return payload, rsc
	else:
		return cast(str, response.payload), rsc

	print('Error')
	return None, 5103


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


def connectionPossible(url:str) -> Tuple[bool, int]:
	"""	Check whether a connection to the CSE is possible and the CSE is running. This is
		done by retrieving the CSEBase using the protocol binding that is used also
		for the rest of the tests. So, the Upper Tester interface is not used.

		Args:
			url: The URL of the CSEBase
		
		Return:
			Return the status (reachable and available) and the response code.
	"""
	try:
		# The following request is not supposed to return a resource, it just
		# tests whether a connection can be established at all.
		result = RETRIEVE(url, ORIGINATOR, timeout = initialRequestTimeout)
		return result[1] == ResponseStatusCode.OK, result[1]
	except Exception as e:
		print(e)
		return False, 5103 
	
def checkUpperTester() -> None:
	if UPPERTESTERENABLED:
		try:
			headers = { UTCMD: f'Status'}
			addHttpAuthorizationHeader(headers)
			response = requests.post(UTURL, headers = headers)
			match response.status_code:
				case 200:
					pass
				case 401:
					console.print('[red]CSE requires authorization')
					console.print('Add authorization settings to the test suite configuration file')
					quit(-1)
				case _:
					console.print('[red]Upper Tester Interface not enabeled in CSE')
					console.print(r'Enable with configuration setting: "\[http]:enableUpperTesterEndpoint=True"')
					quit(-1)
		except (ConnectionRefusedError, requests.exceptions.ConnectionError):
			console.print('[red]Connection to CSE not possible[/red]\nIs it running?')
			shutdown()
			quit(-1)
		

_lastHeaders:Parameters = None

def setLastHeaders(hds:Parameters) -> None:
	global _lastHeaders
	_lastHeaders = hds


def fillLastHeaders(resp:JSON) -> JSON:
	# Since the tests usually work with http binding headers, some response attributes are mapped
	hds = dict()
	for f, k in [ (C.hfRVI, 'rvi'), (C.hfVSI, 'vsi'), (C.hfOT, 'ot'), (C.hfRST, 'rset') ]:
		if k in resp:
			hds[f] = str(resp[k])
	return hds

	
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
	if not RECONFIGURATIONENABLED:
		return

	global _orgExpCheck, _maxExpiration, _tooLargeResourceExpirationDelta

	# Send UT request
	headers = { UTCMD: f'enableShortResourceExpiration {expirationCheckDelay}'}
	addHttpAuthorizationHeader(headers)
	resp = requests.post(UTURL, headers = headers)
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
	if not RECONFIGURATIONENABLED:
		return

	global _orgExpCheck, _orgREQExpCheck
	if _orgExpCheck != -1:
		# Send UT request
		headers = { UTCMD: f'disableShortResourceExpiration'}
		addHttpAuthorizationHeader(headers)
		resp = requests.post(UTURL, headers = headers)
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
	headers = { UTCMD: f'enableShortRequestExpiration {requestExpirationDelay}'}
	addHttpAuthorizationHeader(headers)
	resp = requests.post(UTURL, headers = headers)
	if resp.status_code == 200:
		if UTRSP in resp.headers:
			_orgRequestExpirationDelta = float(resp.headers[UTRSP])


def disableShortRequestExpirations() -> None:
	"""	Disable the short request expiration in the CSE.
	"""
	global _orgRequestExpirationDelta
	
	# Send UT request
	headers = { UTCMD: f'disableShortRequestExpiration'}
	addHttpAuthorizationHeader(headers)
	resp = requests.post(UTURL, headers = headers)
	if resp.status_code == 200:
		_orgRequestExpirationDelta = -1.0
	

def isShortRequestExpirations() -> bool:
	"""	Test whether the request expiration have been configured for testing.

		Return:
			Boolean.
	"""
	return _orgRequestExpirationDelta != -1.0


def testCaseStart(name:str) -> None:
	"""	Indicate the start of a new test case to the CSE via the UT interface.

		Args:
			name: Name of the test case.
	"""
	if UPPERTESTERENABLED:
		headers = { UTCMD: f'testCaseStart {name}'}
		addHttpAuthorizationHeader(headers)
		requests.post(UTURL, headers = headers)
	if verboseRequests:
		console.print('')
		ln  = '=' * int((console.width - 11 - len(name)) / 2)
		console.print(f'[dim]{ln}[ Start {name} ]{ln}')



def testCaseEnd(name:str) -> None:
	"""	Indicate the end of a test case to the CSE via the UT interface.
		
		Args:
			name: Name of the test case.
	"""
	if UPPERTESTERENABLED:
		headers = { UTCMD: f'testCaseEnd {name}'}
		addHttpAuthorizationHeader(headers)
		requests.post(UTURL, headers = headers)
	if verboseRequests:
		console.print('')
		ln  = '=' * int((console.width - 9 - len(name)) / 2)
		console.print(f'[dim]{ln}[ End {name} ]{ln}')


def disableUpperTester() -> None:
	"""	Disable the use of the upper tester interface.
	"""
	global UPPERTESTERENABLED
	UPPERTESTERENABLED = False


###############################################################################

# Surpress warnings for insecure requests, e.g. self-signed certificates
if not verifyCertificate:
	#requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning) 
	urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning) 	# type: ignore[attr-defined]


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
		self.send_header(C.hfOrigin, ORIGINATORNotifResp)
		if C.hfRI in self.headers:
			self.send_header(C.hfRI, self.headers[C.hfRI])
		nextNotificationResult = ResponseStatusCode.OK

		# Get headers and content data
		length = int(self.headers['Content-Length'])
		post_data = self.rfile.read(length)
		decoded_data = ''
		if len(post_data) > 0:
			contentType = ''
			if (val := self.headers.get('Content-Type')) is not None:
				contentType = val.lower()
			match contentType:
				case 'application/json' | 'application/vnd.onem2m-res+json':
					setLastNotification(decoded_data := json.loads(post_data.decode('utf-8')))
				case 'application/cbor' | 'application/vnd.onem2m-res+cbor':
					setLastNotification(decoded_data := cbor2.loads(post_data))	# type:ignore [assignment, arg-type]

		setLastNotificationHeaders(dict(self.headers))	# make a dict out of the headers
		# make a dict out of the query arguments 
		setLastNotificationArguments(parse_qs(urlparse(self.path).query))	# type:ignore[arg-type] 

		# Verbose output
		if verboseRequests and self.headers.get(C.hfOrigin):
			console.print('\n[b u]Received Notification Request')
			console.print('\n'.join([f'{h}: {v}' for h,v in self.headers.items()]))
			if post_data:
				console.print()
				# console.print(json.loads(post_data))
				console.print(decoded_data)
			console.print('\n[b u]Sent Notification Response')
			console.print(b''.join(self._headers_buffer).decode('UTF-8'))	# type: ignore[attr-defined]
		self.end_headers()

	def log_message(self, format:str, *args:int) -> None:
		pass


notificationServerIsRunning = False
# Save the original notification server URL
_NOTIFICATIONSERVER = NOTIFICATIONSERVER
_NOTIFICATIONSERVERW = NOTIFICATIONSERVERW

#
#	This function sets the notification server URL. Depending on the configuration, and
#	the localNotificationServer flag, the URL is set to the local IP address or the
#	original URL.
#	This function is called twice. Once at loading time, and once after the state of the
#	localNotificationServer flag is known.
#

def setNotificationServerURL() -> None:
	global NOTIFICATIONSERVER, NOTIFICATIONSERVERW, TESTHOSTIP
	
	# Set the TESTHOSTIP to the local IP address if it is not set
	if TESTHOSTIP is None:	# type: ignore[used-before-def]
		TESTHOSTIP = getIPAddress()
		if not TESTHOSTIP:
			TESTHOSTIP = '127.0.0.1'	# fallback
	if localNotificationServer:
		TESTHOSTIP = '127.0.0.1'

	NOTIFICATIONSERVER = _NOTIFICATIONSERVER.replace('${TESTHOSTIP}', TESTHOSTIP)
	NOTIFICATIONSERVERW = _NOTIFICATIONSERVERW.replace('${TESTHOSTIP}', TESTHOSTIP)


def runNotificationServer() -> None:
	global notificationServerIsRunning

	httpd = HTTPServer(('', NOTIFICATIONPORT), SimpleHTTPRequestHandler)
	if PROTOCOL == 'https':
		# init ssl socket
		context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)					# Create a SSL Context
		context.load_cert_chain(certfile='../certs/acme_cert.pem', keyfile='../certs/acme_key.pem')	# Load the certificate and private key
		httpd.socket = context.wrap_socket(httpd.socket, server_side=True)	# wrap the original http server socket as an SSL/TLS socket

	notificationServerIsRunning = True
	while notificationServerIsRunning:
		httpd.handle_request()


def startNotificationServer() -> None:
	notificationThread = Thread(target=runNotificationServer)
	notificationThread.start()
	waitMessage(f'Starting notification server at {NOTIFICATIONSERVER}', 2)


def stopNotificationServer() -> None:
	global notificationServerIsRunning

	if notificationServerIsRunning:
		notificationServerIsRunning = False
		try:
			requests.post(NOTIFICATIONSERVER, verify=verifyCertificate, timeout=1)	# send empty/termination request
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
lastNotificationArguments:Parameters 		= {}
nextNotificationResult:ResponseStatusCode	= ResponseStatusCode.OK

def setLastNotification(notification:JSON) -> None:
	global lastNotification
	lastNotification = notification


def getLastNotification(clear:bool = False, wait:float = 0.0) -> JSON:
	testSleep(wait)
	r = lastNotification
	if clear:
		clearLastNotification()
	return r


def clearLastNotification(nextResult:ResponseStatusCode = ResponseStatusCode.OK) -> None:
	global lastNotification, lastNotificationHeaders, lastNotificationArguments, nextNotificationResult
	lastNotification = None
	lastNotificationHeaders = None
	lastNotificationArguments = None
	nextNotificationResult = nextResult


def setLastNotificationHeaders(headers:Parameters) -> None:
	global lastNotificationHeaders
	lastNotificationHeaders = headers


def getLastNotificationHeaders() -> Parameters:
	return lastNotificationHeaders


def setLastNotificationArguments(arguments:Parameters) -> None:
	global lastNotificationArguments
	lastNotificationArguments = arguments


def getLastNotificationArguments() -> Parameters:
	return lastNotificationArguments


_sleepTimeCount:float = 0.0

def testSleep(ti:float) -> None:
	global _sleepTimeCount
	_sleepTimeCount += ti
	time.sleep(ti)


def clearSleepTimeCount() -> None:
	global _sleepTimeCount
	_sleepTimeCount = 0


def getSleepTimeCount() -> float:
	return _sleepTimeCount


def utcNow() -> datetime:
	"""	Return the current time, but relative to UTC.

		Return:
			Datetime UTC-based timestamp
	"""
	return datetime.now(tz = timezone.utc)


def utcTimestamp() -> float:
	"""	Return the current time's timestamp, but relative to UTC.

		Return:
			Float UTC-based timestamp
	"""
	return utcNow().timestamp()


def createScheduleString(range:int, delay:int=0) -> str:
	"""	Create schedule string for range seconds.

		Args:
			range: The range in seconds
			delay: The delay in seconds. This can be used to delay the start of the schedule to create an schedule for a later time.
		
		Return:
			String with the schedule string
	"""
	dts = datetime.now(tz = timezone.utc) + timedelta(seconds = delay)
	dte = dts + timedelta(seconds = range)
	return f'{dts.second}-{dte.second} {dts.minute}-{dte.minute} {dts.hour}-{dte.hour} * * * *'



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
			testSleep(delay)
	else:
		console.print(f'[bright_blue]{msg}')


def uniqueID() -> str:
	return str(random.randint(1,sys.maxsize))


def uniqueRN(prefix:str='') -> str:
	"""	Create a unique resource name.
	"""
	return f'{prefix}{round(time.time() * 1000)}-{uniqueID()}'


def toSPRelative(originator:str) -> str:
	"""	Add the CSI to an originator (if not already present).

		Args:
			An originator.
		Return:
			A string in the format */<csi>/<originator*.
	"""
	if not isSPRelative(originator):
		return  f'{CSEID}/{originator}'
	return originator


def isSPRelative(uri:str) -> bool:
	""" Test whether a URI is SP-Relative. 

		Args:
			uri: The URI to check
		Return:
			Boolean
	"""
	return uri is not None and len(uri) >= 2 and uri[0] == '/' and uri [1] != '/'


def getIPAddress() -> str:
	"""	Get the IP address of the local machine.

		Return:
			String with the IP address.
	"""
	from acme.helpers.NetworkTools import getIPAddress as _getIPAddress
	return _getIPAddress()


def addTest(suite:unittest.TestSuite, case:unittest.TestCase) -> None:
	"""	Add a test case to a test suite.

		Args:
			suite: The test suite
			case: The test case
	"""
	global testCaseNames

	if testCaseNames is None:
		suite.addTest(case)

	elif testCaseNames and case._testMethodName in testCaseNames:
		testCaseNames.remove(case._testMethodName)
		suite.addTest(case)


def addTests(suite:unittest.TestSuite, cls:Type[unittest.TestCase], cases:list[str]) -> None:
	"""	Add a list of test cases to a test suite. If the global variable `testCaseNames` is set
		then only the test cases in that list are added in the order they are listed. Duplicates are
		allowed.
	
		Args:
			suite: The test suite
			cls: The class of the test cases
			cases: The list of test case names
	"""
	def _addTest(case:str) -> None:
		if case and case not in excludedTestNames:
			try:
				suite.addTest(cls(case))
			except ValueError as e:
				console.print(f'[red]Test case "{case}" not found - skipping[/red]')

	if testCaseNames is None:
		for case in cases:
			_addTest(case)
	else:
		for case in testCaseNames:
			_addTest(case)


def isTearDownEnabled() -> bool:
	return enableTearDown


decimalMatch = re.compile(r'{(\d+)}')
def findXPath(dct:JSON, key:str, default:Any=None) -> Any:
	""" Find a structured `key` in the dictionary `dct`. If `key` does not exists then
		`default` is returned.

		- It is possible to address a specific element in an array. This is done be
		specifying the element as `{n}`.

		Example: findXPath(resource, 'm2m:cin/{1}/lbl/{0}')

		- If an element is specified as `{}` then all elements in that array are returned in
		an array.

		Example: findXPath(resource, 'm2m:cin/{1}/lbl/{}') or findXPath(input, 'm2m:cnt/m2m:cin/{}/rn')

		- If an element is specified as `{*}` and is targeting a dictionary then a single random path is chosen.
		This can be used to skip, for example, unknown first elements in a structure.

		Example: findXPath(resource, '{*}/rn') 

	"""

	if not key or not dct:
		return default
	if key in dct:
		return dct[key]

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

		elif pathElement == '{*}':
			if isinstance(data, dict):
				if keys := list(data.keys()):
					data = data[keys[0]]
				else:
					return default
			else:
				return default

		elif pathElement not in data:	# if key not in dict
			return default
		else:
			data = data[pathElement]	# found data for the next level down
	return data



###############################################################################


match PROTOCOL:
	# Start MQTT Client if test protocol is mqtt
	case 'mqtt':
		mqttHandler = MQTTClientHandler()
		mqttClient = MQTTConnection(mqttAddress, mqttPort, clientID=mqttClientID, username=mqttUsername, password=mqttPassword, messageHandler=mqttHandler)
		mqttClient.run()
		while not mqttHandler.connection:
			testSleep(1)


###############################################################################

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
_r, status = connectionPossible(cseURL)
if status == 401:	# Access denied
	console.print('[red]CSE requires authorization')
	console.print('Add authorization settings to the test suite configuration file')
	quit(-1)
noCSE = not _r

_r,status = connectionPossible(REMOTEcseURL)
if status == 401:	# Access denied
	console.print('[red]Remote CSE requires authorization')
	console.print('Add authorization settings to the test suite configuration file')
	quit(-1)
noRemote = not _r

# Set the notification server URL
setNotificationServerURL()

