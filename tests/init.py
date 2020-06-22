#
#	init.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configuration & helper functions for unit tests
#

import requests, random, sys, json
from typing import Any, Callable


SERVER		= 'http://localhost:8080'
ROOTURL		= '/'
CSERN		= 'cse-in'
CSEID		= '/id-in'
ORIGINATOR	= 'CAdmin'


testVerbosity = 2		# 0, 1, 2

###############################################################################

aeRN	= 'testAE'
cntRN	= 'testCNT'
cinRN	= 'testCIN'
grpRN	= 'testGRP'


URL		= '%s%s' % (SERVER, ROOTURL)
cseURL 	= '%s%s' % (URL, CSERN)
aeURL 	= '%s/%s' % (cseURL, aeRN)
cntURL 	= '%s/%s' % (aeURL, cntRN)
cinURL 	= '%s/%s' % (cntURL, cinRN)
grpURL 	= '%s/%s' % (aeURL, grpRN)



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
#	ID
#

def uniqueID() -> str:
	return str(random.randint(1,sys.maxsize))


# find a structured element in JSON
def findXPath(jsn : dict, element : str, default : Any = None) -> Any:
	paths = element.split("/")
	data = jsn
	for i in range(0,len(paths)):
		if paths[i] not in data:
			return default
		data = data[paths[i]]
	return data