import requests, argparse, sys, random, json
sys.path.append('../acme')
from typing import Any, Callable, List
from Types import ResourceTypes as T

host 		= 'http://localhost:8080'
csi  		= '/id-in'
url  		= host if host.endswith('/') else '%s/' % host


#
#	HTTP Requests
#

def RETRIEVE(url:str, originator:str) -> (dict, int):
	return sendRequest(requests.get, url, originator)


def CREATE(url:str, originator:str, ty:int=None, data:Any=None) -> (dict, int):
	return sendRequest(requests.post, url, originator, ty, data)


def UPDATE(url:str, originator:str, data:Any=None) -> (dict, int):
	return sendRequest(requests.put, url, originator, data=data)


def DELETE(url:str, originator:str) -> (dict, int):
	return sendRequest(requests.delete, url, originator)


def sendRequest(method:Callable, url:str, originator:str, ty:int=None, data:Any=None, ct:str='application/json') -> (dict, int):	# TODO Constants
	headers = { 'Content-Type' 	: '%s%s' % (ct, ';ty=%d' % ty if ty is not None else ''), 
				'X-M2M-Origin'	 	: originator,
				'X-M2M-RI' 			: uniqueID(),
				'X-M2M-RVI'			: '3',
			   }
	try:
		if isinstance(data, dict):
			data = json.dumps(data)
		r = method(url, data=data, headers=headers)
	except Exception as e:
		print('Failed to send request: %s' % str(e))
		return None, 5103
	rc = int(r.headers['X-M2M-RSC']) if 'X-M2M-RSC' in r.headers else 5000
	return r.json() if len(r.content) > 0 else None, rc


def uniqueID() -> str:
	return str(random.randint(1,sys.maxsize))

def setXPath(dct: dict, element: str, value: Any, overwrite: bool = True) -> bool:
	paths = element.split("/")
	ln = len(paths)
	data = dct
	for i in range(0,ln-1):
		if paths[i] not in data:
			data[paths[i]] = {}
		data = data[paths[i]]
	if paths[ln-1] in data is not None and not overwrite:
			return True # don't overwrite
	data[paths[ln-1]] = value
	return True


types = {
	'node' : T.NOD
}



def createResource(srn:str, originator:str, ty:str, rn:str, attributes:List[str], verbose:bool) -> (dict, int):
	if ty is None:
		print('Error: type must be provided')
		return None, None

	resources = { 'node' : ( 'm2m:nod', { 'rn': rn } ),
			}

	# Fill in extra attributes
	(tpe, dct) = resources[ty]
	for a in attributes:
		k = a.split('=')
		if len(k) == 2:
			if k[1].endswith(':i'):
				setXPath(dct, k[0], int(k[1][:-2]))
			elif k[1].endswith(':f'):
				setXPath(dct, k[0], float(k[1][:-2]))
			elif k[1].endswith(':b'):
				setXPath(dct, k[0], True if k[1][:-2] == 'true' else False)
			elif k[1].endswith(':s'):
				setXPath(dct, k[0], '%s' % k[1][:-2])
			else:
				setXPath(dct, k[0], '%s' % k[1])

	return CREATE('%s/%s' % (url, srn), originator, types[ty], { tpe:dct })


def deleteResource(srn:str, originator:str, verbose) -> None:
	return DELETE('%s/%s' % (url, srn), originator)



if __name__ == '__main__':

	# Get command line arguments
	parser = argparse.ArgumentParser()
	commands = parser.add_mutually_exclusive_group(required=True)
	commands.add_argument('--create', dest='create', action='store_true', help='add device node')
	commands.add_argument('--delete', dest='delete', action='store_true', help='delete device node')
	parser.add_argument('--type', '-t' , choices = [ 'node'], help='resource type')
	parser.add_argument('--rn', required=False, default=uniqueID(), help='resoure name')
	parser.add_argument('--srn', required=True, help='target structured resource name')
	parser.add_argument('--originator', '-o', required=True, help='target structured resource name')
	parser.add_argument('--verbose', '-v', action='store_true', required=False, default=False, help='verbose output')
	parser.add_argument('attributes', nargs='*')	# all others are attributes
	args = parser.parse_args()

	# Call the appropriate method
	args.create and (result := createResource(args.srn, args.originator, args.type, args.rn, args.attributes, args.verbose))
	args.delete and (result := deleteResource(args.srn, args.originator, args.verbose))

	# Handle results
	print(result)



