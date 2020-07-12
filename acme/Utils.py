#
#	Utils.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

import datetime, random, string, sys, re, threading
from typing import Any, List, Tuple, Union
from resources import ACP, AE, ANDI, ANI, BAT, CIN, CNT, CNT_LA, CNT_OL, CSEBase, CSR, DVC
from resources import DVI, EVL, FCI, FCNT, FCNT_LA, FCNT_OL, FWR, GRP, GRP_FOPT, MEM, NOD, RBO, SUB, SWR, Unknown, Resource
from Constants import Constants as C
from Types import ResourceTypes as T
from Configuration import Configuration
from Logging import Logging
import CSE
from flask import Request


def uniqueRI(prefix: str = '') -> str:
	return noDomain(prefix) + uniqueID()


def uniqueID() -> str:
	return str(random.randint(1,sys.maxsize))


def isUniqueRI(ri: str) -> bool:
	return len(CSE.storage.identifier(ri)) == 0


def uniqueRN(prefix: str = 'un') -> str:
	# return "%s_%s" % (p, ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=C.maxIDLength)))
	return "%s_%s" % (noDomain(prefix), _randomID())


# create a unique aei, M2M-SP type
def uniqueAEI(prefix : str = 'S') -> str:
	# return prefix + ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=C.maxIDLength))
	return prefix + _randomID()


def noDomain(id : str) -> str:
	p = id.split(':')
	return p[1] if len(p) == 2 else p[0]


def _randomID() -> str:
	""" Generate an ID. Prevent certain patterns in the ID. """
	while True:
		result = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=C.maxIDLength))
		if 'fopt' not in result:	# prevent 'fopt' in ID
			return result


def fullRI(ri : str) -> str:
	return Configuration.get('cse.csi') + '/' + ri


def isSPRelative(uri : str) -> bool:
	""" Check whether a URI is SP-Relative. """
	return uri is not None and len(uri) >= 2 and uri[0] == "/" and uri [1] != "/"


def isAbsolute(uri : str) -> bool:
	""" Check whether a URI is Absolute. """
	return uri is not None and uri.startswith('//')


def isCSERelative(uri : str) -> bool:
	""" Check whether a URI is CSE-Relative. """
	return uri is not None and uri[0] != '/'


def isStructured(uri : str) -> bool:
	if isCSERelative(uri):
		if "/" in uri:
			return True
	elif isSPRelative(uri):
		if uri.count("/") > 2:
			return True
	elif isAbsolute(uri):
		if uri.count("/") > 4:
			return True
	return False


def isVirtualResource(resource: Resource.Resource) -> bool:
	result = resource[resource._isVirtual]
	return result if result is not None else False
	# ireturn (ty := r.ty) and ty in C.virtualResources


def isValidID(id: str) -> bool:
	""" Check for valid ID. """
	#return len(id) > 0 and '/' not in id 	# pi might be ""
	return '/' not in id


def getResourceDate(delta: int = 0) -> str:
	return toISO8601Date(datetime.datetime.utcnow() + datetime.timedelta(seconds=delta))


def toISO8601Date(ts: Union[float, datetime.datetime]) -> str:
	if isinstance(ts, float):
		ts = datetime.datetime.utcfromtimestamp(ts)
	return ts.strftime('%Y%m%dT%H%M%S,%f')



def structuredPath(resource: Resource.Resource) -> str:
	""" Determine the structured path of a resource. """
	rn = resource.rn
	if resource.ty == T.CSEBase: # if CSE
		return rn

	# retrieve identifier record of the parent
	if (pi := resource.pi) is None:
		# Logging.logErr('PI is None')
		return rn
	rpi = CSE.storage.identifier(pi) 
	if len(rpi) == 1:
		return rpi[0]['srn'] + '/' + rn
	Logging.logErr('Parent %s not fount in DB' % pi)
	return rn # fallback


def structuredPathFromRI(ri: str) -> str:
	""" Get the structured path of a resource by its ri. """
	if len((identifiers := CSE.storage.identifier(ri))) == 1:
		return identifiers[0]['srn']
	return None


def riFromStructuredPath(srn: str) -> str:
	""" Get the ri from a resource by its structured path. """
	if len((paths := CSE.storage.structuredPath(srn))) == 1:
		return paths[0]['ri']
	return None


def riFromCSI(csi: str) -> str:
	""" Get the ri from an CSEBase resource by its csi. """
	if (res := CSE.storage.retrieveResource(csi=csi))[0] is None:
		return None
	return res[0].ri


def retrieveIDFromPath(id: str, csern: str, cseri: str) -> Tuple[str, str, str]:
	""" Split a ful path e.g. from a http request into its component and return a local ri .
		Also handle retargeting paths.
		The return tupple is (RI, CSI, SRN).
	"""
	csi 		= None
	spi 		= None
	srn 		= None
	ri 			= None
	vrPresent	= None

	# Prepare. Remove leading / and split
	if id[0] == '/':
		id = id[1:]
	ids = id.split('/')

	if (idsLen := len(ids)) == 0:	# There must be something!
		return None, None, None

	# Remove virtual resource shortname if it is present
	if ids[-1] in C.virtualResourcesNames:
		vrPresent = ids.pop()	# remove and return last path element
		idsLen -= 1

	# Logging.logDebug("ID split: %s" % ids)
	if ids[0] == '~' and idsLen > 1:			# SP-Relative
		# Logging.logDebug("SP-Relative")
		csi = ids[1]							# extract the csi
		if csi != cseri:						# Not for this CSE? retargeting
			if vrPresent is not None:			# append last path element again
				ids.append(vrPresent)
			return '/%s' % '/'.join(ids[1:]), csi, srn		# Early return. ri is the remaining (un)structured path
		if idsLen > 2 and (ids[2] == csern or ids[2] == '-'):	# structured
			ids[2] = csern if ids[2] == '-' else ids[2]
			srn = '/'.join(ids[2:])
		elif idsLen == 3:						# unstructured
			ri = ids[2]
		else:
			return None, None, None

	elif ids[0] == '_' and idsLen >= 4:			# Absolute
		# Logging.logDebug("Absolute")
		spi = ids[1] 	#TODO Check whether it is same SPID, otherwise forward it throw mcc'
		csi = ids[2]
		if csi != cseri:
			if vrPresent is not None:						# append last path element again
				ids.append(vrPresent)
			return '/%s' % '/'.join(ids[2:]), csi, srn	# Not for this CSE? retargeting
		if ids[3] == csern or ids[3] == '-':				# structured
			ids[3] = csern if ids[3] == '-' else ids[3]
			srn = '/'.join(ids[3:])
		elif idsLen == 4:						# unstructured
			ri = ids[3]
		else:
			return None, None, None

	else:										# CSE-Relative
		# Logging.logDebug("CSE-Relative")
		if idsLen == 1 and ((ids[0] != csern and ids[0] != '-') or ids[0] == cseri):	# unstructured
			ri = ids[0]
		else:									# structured
			ids[0] = csern if ids[0] == '-' else ids[0]
			srn = '/'.join(ids)

	# Now either csi, ri or structured is set
	if ri is not None:
		if vrPresent is not None:
			ri = '%s/%s' % (ri, vrPresent)
		return ri, csi, srn
	if srn is not None:
		# if '/fopt' in ids:	# special handling for fanout points
		# 	return srn, csi, srn
		if vrPresent is not None:
			srn = '%s/%s' % (srn, vrPresent)
		return riFromStructuredPath(srn), csi, srn
	if csi is not None:
		return riFromCSI('/'+csi), csi, srn
	# TODO do something with spi?
	return None, None, None


def resourceFromJSON(jsn: dict, pi: str = None, acpi: str = None, ty: Union[T, int] = None, create: bool = False, isImported: bool = False) -> Tuple[Resource.Resource, str]:
	""" Create a resource from a JSON structure.
		This will *not* call the activate method, therefore some attributes
		may be set separately.
	"""
	jsn, root = pureResource(jsn)	# remove optional "m2m:xxx" level
	typ = jsn['ty'] if 'ty' in jsn else ty
	if typ != None and ty != None and typ != ty:
		return None, 'type and resource specifier mismatch'
	mgd = jsn['mgd'] if 'mgd' in jsn else None		# for mgmtObj

	# Add extra acpi
	if acpi is not None:
		jsn['acpi'] = acpi if type(acpi) is list else [ acpi ]

	# store the import status in the original jsn
	if isImported:
		jsn[Resource.Resource._imported] = True	# Indicate that this is an imported resource


	# sorted by assumed frequency (small optimization)
	if typ == T.CIN or root == T.CIN.tpe():
		return CIN.CIN(jsn, pi=pi, create=create), None
	elif typ == T.CNT or root == T.CNT.tpe():
		return CNT.CNT(jsn, pi=pi, create=create), None
	elif typ == T.GRP or root == T.GRP.tpe():
		return GRP.GRP(jsn, pi=pi, create=create), None
	elif typ == T.GRP_FOPT or root == T.GRP_FOPT.tpe():
		return GRP_FOPT.GRP_FOPT(jsn, pi=pi, create=create), None
	elif typ == T.ACP or root == T.ACP.tpe():
		return ACP.ACP(jsn, pi=pi, create=create), None
	elif typ == T.FCNT:
		return FCNT.FCNT(jsn, pi=pi, fcntType=root, create=create), None
	elif typ == T.FCI:
		return FCI.FCI(jsn, pi=pi, fcntType=root, create=create), None	
	elif typ == T.AE or root == T.AE.tpe():
		return AE.AE(jsn, pi=pi, create=create), None
	elif typ == T.SUB or root == T.SUB.tpe():
		return SUB.SUB(jsn, pi=pi, create=create), None
	elif typ == T.CSR or root == T.CSR.tpe():
		return CSR.CSR(jsn, pi=pi, create=create), None
	elif typ == T.NOD or root == T.NOD.tpe():
		return NOD.NOD(jsn, pi=pi, create=create), None
	elif (typ == T.MGMTOBJ and mgd == T.FWR) or root == T.FWR.tpe():
		return FWR.FWR(jsn, pi=pi, create=create), None
	elif (typ == T.MGMTOBJ and mgd == T.SWR) or root == T.SWR.tpe():
		return SWR.SWR(jsn, pi=pi, create=create), None
	elif (typ == T.MGMTOBJ and mgd == T.MEM) or root == T.MEM.tpe():
		return MEM.MEM(jsn, pi=pi, create=create), None
	elif (typ == T.MGMTOBJ and mgd == T.ANI) or root == T.ANI.tpe():
		return ANI.ANI(jsn, pi=pi, create=create), None
	elif (typ == T.MGMTOBJ and mgd == T.ANDI) or root == T.ANDI.tpe():
		return ANDI.ANDI(jsn, pi=pi, create=create), None
	elif (typ == T.MGMTOBJ and mgd == T.BAT) or root == T.BAT.tpe():
		return BAT.BAT(jsn, pi=pi, create=create), None
	elif (typ == T.MGMTOBJ and mgd == T.DVI) or root == T.DVI.tpe():
		return DVI.DVI(jsn, pi=pi, create=create), None
	elif (typ == T.MGMTOBJ and mgd == T.DVC) or root == T.DVC.tpe():
		return DVC.DVC(jsn, pi=pi, create=create), None
	elif (typ == T.MGMTOBJ and mgd == T.RBO) or root == T.RBO.tpe():
		return RBO.RBO(jsn, pi=pi, create=create), None
	elif (typ == T.MGMTOBJ and mgd == T.EVL) or root == T.EVL.tpe():
		return EVL.EVL(jsn, pi=pi, create=create), None
	elif typ == T.CNT_LA or root == T.CNT_LA.tpe():
		return CNT_LA.CNT_LA(jsn, pi=pi, create=create), None
	elif typ == T.CNT_OL or root == T.CNT_OL.tpe():
		return CNT_OL.CNT_OL(jsn, pi=pi, create=create), None
	elif typ == T.FCNT_LA:
		return FCNT_LA.FCNT_LA(jsn, pi=pi, create=create), None
	elif typ == T.FCNT_OL:
		return FCNT_OL.FCNT_OL(jsn, pi=pi, create=create), None
	elif typ == T.CSEBase or root == T.CSEBase.tpe():
		return CSEBase.CSEBase(jsn, create=create), None

	return Unknown.Unknown(jsn, root, pi=pi, create=create), None	# Capture-All resource


excludeFromRoot = [ 'pi' ]
def pureResource(jsn: dict) -> Tuple[dict, str]:
	""" Return the "pure" json without the "m2m:xxx" or "<domain>:id" resource specifier."""
	rootKeys = list(jsn.keys())
	# Try to determine the root identifier 
	if len(rootKeys) == 1 and (rk := rootKeys[0]) not in excludeFromRoot and re.match('[\w]+:[\w]', rk):
		return jsn[rootKeys[0]], rootKeys[0]
	return jsn, None



decimalMatch = re.compile('{(\d+)}')
def findXPath(jsn : dict, element : str, default : Any = None) -> Any:
	""" Find a structured element in JSON.
		Example: findXPath(resource, 'm2m:cin/{1}/lbl/{0}')
	"""

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


# set a structured element in JSON. Create if necessary, and observe the overwrite option
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


urlregex = re.compile(
        r'^(?:http|ftp)s?://' 						# http://, https://, ftp://, ftps://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9]))|' # localhost or single name w/o domain
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 		# ipv4
        r'(?::\d+)?' 								# optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)			# optional path


def isURL(url: str) -> bool:
	""" Check whether a given string is a URL. """
	return url is not None and re.match(urlregex, url) is not None


def normalizeURL(url: str) -> str:
	""" Remove trailing / from the url. """
	if url is not None:
		while len(url) > 0 and url[-1] == '/':
			url = url[:-1]
	return url


def getIdFromOriginator(originator: str, idOnly: bool = False) -> str:
	""" Get AE-ID-Stem or CSE-ID from the originator (in case SP-relative or Absolute was used) """
	if idOnly:
		return originator.split("/")[-1] if originator is not None  else originator
	else:
		return originator.split("/")[-1] if originator is not None and originator.startswith('/') else originator


def isAllowedOriginator(originator: str, allowedOriginators: List[str]) -> bool:
	""" Check whether an Originator is in the provided list of allowed 
		originators. This list may contain regex.
	"""
	if originator is None or allowedOriginators is None:
		return False
	for ao in allowedOriginators:
		if re.fullmatch(re.compile(ao), getIdFromOriginator(originator)):
			return True
	return False


#	Compare an old and a new resource. Keywords and values. Ignore internal __XYZ__ keys
#	Return a dictionary.
def resourceDiff(old: Union[Resource.Resource, dict], new: Union[Resource.Resource, dict]) -> dict:
	res = {}
	for k,v in new.items():
		if k.startswith('__'):	# ignore all internal attributes
			continue
		if not k in old:		# Key not in old
			res[k] = v
		elif v != old[k]:		# Value different
			res[k] = v 
	return res


def getCSE() -> Tuple[Resource.Resource, int, str]:
	return CSE.dispatcher.retrieveResource(Configuration.get('cse.ri'))


def getCSETypeAsString() -> str:
	return C.cseTypes[Configuration.get('cse.type')]

	
# Check whether the target contains a fanoutPoint in between or as the target
def fanoutPointResource(id: str) -> Resource.Resource:
	if id is None:
		return None
	# retrieve srn
	if not isStructured(id):
		id = structuredPathFromRI(id)
	if id is None:
		return None
	nid = None
	if id.endswith('/fopt'):
		nid = id
	elif '/fopt/' in id:
		(head, sep, tail) = id.partition('/fopt/')
		nid = head + '/fopt'
	if nid is not None:
		if (result := CSE.dispatcher.retrieveResource(nid))[0] is not None:
			return result[0]
	return None



#
#	HTTP request helper functions
#


def requestHeaderField(request: Request, field : str) -> str:
	if not request.headers.has_key(field):
		return None
	return request.headers.get(field)

		
def getRequestHeaders(request: Request) -> Tuple[str, str, T, str, int]:
	originator = requestHeaderField(request, C.hfOrigin)
	rqi = requestHeaderField(request, C.hfRI)

	# content-type
	ty = None
	ct = None
	if (ct := request.content_type) is not None:
		if not ct.startswith(tuple(C.supportedContentHeaderFormat)):
			ct = None
		else:
			p = ct.partition(';')
			ct = p[0] # content-type
			t = p[2].partition('=')[2]
			ty = T(int(t)) if t.isdigit() else T.UNKNOWN # resource type

	return originator, ct, ty, rqi, C.rcOK


#
#	Threads
#

def renameCurrentThread(name:str = None, thread:threading.Thread = None) -> None:
	thread = threading.current_thread() if thread is None else thread
	thread.name = name if name is not None else str(thread.native_id)

