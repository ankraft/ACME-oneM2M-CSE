#
#	Utils.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

import datetime, json, random, string, sys, re, threading, traceback, time
import cbor2
from copy import deepcopy
import isodate
from typing import Any, List, Tuple, Union, Dict
from resources import ACP, ACPAnnc, AE, AEAnnc, ANDI, ANDIAnnc, ANI, ANIAnnc, BAT, BATAnnc
from resources import CIN, CINAnnc, CNT, CNTAnnc, CNT_LA, CNT_OL, CSEBase, CSR, CSRAnnc
from resources import DVC, DVCAnnc,DVI, DVIAnnc, EVL, EVLAnnc, FCI, FCIAnnc, FCNT, FCNTAnnc, FCNT_LA, FCNT_OL
from resources import FWR, FWRAnnc, GRP, GRPAnnc, GRP_FOPT, MEM, MEMAnnc, MgmtObj, MgmtObjAnnc, NOD, NODAnnc
from resources import NYCFC, NYCFCAnnc, PCH, REQ, RBO, RBOAnnc, SUB
from resources import SWR, SWRAnnc, Unknown, Resource


from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from Types import Result,  RequestHeaders, Operation, RequestArguments, FilterUsage, DesiredIdentifierResultType, ResultContentType, ResponseType, FilterOperation
from Types import CSERequest, ContentSerializationType
from Configuration import Configuration
from Logging import Logging
import CSE
from flask import Request
import cbor2


def uniqueRI(prefix:str='') -> str:
	return noDomain(prefix) + uniqueID()


def uniqueID() -> str:
	return str(random.randint(1,sys.maxsize))


def isUniqueRI(ri:str) -> bool:
	return len(CSE.storage.identifier(ri)) == 0


def uniqueRN(prefix:str='un') -> str:
	return f'{noDomain(prefix)}_{_randomID()}'

def announcedRN(resource:Resource.Resource) -> str:
	""" Create the announced rn for a resource.
	"""
	return f'{resource.rn}_Annc'


# create a unique aei, M2M-SP type
def uniqueAEI(prefix:str='S') -> str:
	return f'{prefix}{_randomID()}'


def noDomain(id:str) -> str:
	p = id.split(':')
	return p[1] if len(p) == 2 else p[0]


def _randomID() -> str:
	""" Generate an ID. Prevent certain patterns in the ID. """
	while True:
		result = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=C.maxIDLength))
		if 'fopt' not in result:	# prevent 'fopt' in ID
			return result


def fullRI(ri:str) -> str:
	return f'{Configuration.get("cse.csi")}/{ri}'


def isSPRelative(uri:str) -> bool:
	""" Check whether a URI is SP-Relative. """
	return uri is not None and len(uri) >= 2 and uri[0] == '/' and uri [1] != '/'


def isAbsolute(uri:str) -> bool:
	""" Check whether a URI is Absolute. """
	return uri is not None and uri.startswith('//')


def isCSERelative(uri:str) -> bool:
	""" Check whether a URI is CSE-Relative. """
	return uri is not None and uri[0] != '/'


def isStructured(uri:str) -> bool:
	if isCSERelative(uri):
		if '/' in uri:
			return True
	elif isSPRelative(uri):
		if uri.count('/') > 2:
			return True
	elif isAbsolute(uri):
		if uri.count('/') > 4:
			return True
	return False


def isVirtualResource(resource: Resource.Resource) -> bool:
	result = resource[resource._isVirtual]
	return result if result is not None else False
	# ireturn (ty := r.ty) and ty in C.virtualResources


def isValidID(id: str) -> bool:
	""" Check for valid ID. """
	#return len(id) > 0 and '/' not in id 	# pi might be ""
	return id is not None and '/' not in id


def getResourceDate(delta: int = 0) -> str:
	return toISO8601Date(datetime.datetime.utcnow() + datetime.timedelta(seconds=delta))


def toISO8601Date(ts: Union[float, datetime.datetime]) -> str:
	if isinstance(ts, float):
		ts = datetime.datetime.utcfromtimestamp(ts)
	return ts.strftime('%Y%m%dT%H%M%S,%f')


def fromISO8601Date(timestamp:str) -> float:
	try:
		return datetime.datetime.strptime(timestamp, '%Y%m%dT%H%M%S,%f').timestamp()
	except Exception as e:
		Logging.logWarn(f'Wrong format for timestamp: {timestamp}')
		return 0.0


def structuredPath(resource: Resource.Resource) -> str:
	""" Determine the structured path of a resource. """
	rn = resource.rn
	if resource.ty == T.CSEBase: # if CSE
		return rn

	# retrieve identifier record of the parent
	if (pi := resource.pi) is None or len(pi) == 0:
		# Logging.logErr('PI is None')
		return rn
	rpi = CSE.storage.identifier(pi) 
	if len(rpi) == 1:
		return rpi[0]['srn'] + '/' + rn
	# Logging.logErr(traceback.format_stack())
	Logging.logErr(f'Parent {pi} not found in DB')
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


def srnFromHybrid(srn:str, id:str) -> Tuple[str, str]:
	""" Handle Hybrid ID. """
	if id is not None:
		ids = id.split('/')
		if srn is None and len(ids) > 1  and ids[-1] in C.virtualResourcesNames: # Hybrid
			if (srn := structuredPathFromRI('/'.join(ids[:-1]))) is not None:
				srn = '/'.join([srn, ids[-1]])
				id = riFromStructuredPath(srn) # id becomes the ri of the fopt
	return srn, id


def riFromCSI(csi: str) -> str:
	""" Get the ri from an CSEBase resource by its csi. """
	if (res := resourceFromCSI(csi)) is None:
		return None
	return res.ri


def resourceFromCSI(csi: str) -> Resource.Resource:
	""" Get the CSEBase resource by its csi. """
	if (res := CSE.storage.retrieveResource(csi=csi)).resource is None:
		return None
	return res.resource


def retrieveIDFromPath(id: str, csern: str, csecsi: str) -> Tuple[str, str, str]:
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
	csecsi = csecsi[1:]	# remove leading / from csi for our comparisons here

	if (idsLen := len(ids)) == 0:	# There must be something!
		return None, None, None

	# Remove virtual resource shortname if it is present
	if ids[-1] in C.virtualResourcesNames:
		vrPresent = ids.pop()	# remove and return last path element
		idsLen -= 1

	if ids[0] == '~' and idsLen > 1:			# SP-Relative
		# Logging.logDebug("SP-Relative")
		csi = ids[1]							# extract the csi
		if csi != csecsi:						# Not for this CSE? retargeting
			if vrPresent is not None:			# append last path element again
				ids.append(vrPresent)
			return f'/{"/".join(ids[1:])}', csi, srn		# Early return. ri is the remaining (un)structured path
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
		if csi != csecsi:
			if vrPresent is not None:						# append last path element again
				ids.append(vrPresent)
			return f'/{"/".join(ids[2:])}', csi, srn	# Not for this CSE? retargeting
		if ids[3] == csern or ids[3] == '-':				# structured
			ids[3] = csern if ids[3] == '-' else ids[3]
			srn = '/'.join(ids[3:])
		elif idsLen == 4:						# unstructured
			ri = ids[3]
		else:
			return None, None, None

	else:										# CSE-Relative
		# Logging.logDebug("CSE-Relative")
		if idsLen == 1 and ((ids[0] != csern and ids[0] != '-') or ids[0] == csecsi):	# unstructured
			ri = ids[0]
		else:									# structured
			ids[0] = csern if ids[0] == '-' else ids[0]
			srn = '/'.join(ids)

	# Now either csi, ri or structured is set
	if ri is not None:
		if vrPresent is not None:
			ri = f'{ri}/{vrPresent}'
		return ri, csi, srn
	if srn is not None:
		# if '/fopt' in ids:	# special handling for fanout points
		# 	return srn, csi, srn
		if vrPresent is not None:
			srn = f'{srn}/{vrPresent}'
		return riFromStructuredPath(srn), csi, srn
	if csi is not None:
		return riFromCSI(f'/{csi}'), csi, srn
	# TODO do something with spi?
	return None, None, None


mgmtObjTPEs = 		[	T.FWR.tpe(), T.SWR.tpe(), T.MEM.tpe(), T.ANI.tpe(), T.ANDI.tpe(),
						T.BAT.tpe(), T.DVI.tpe(), T.DVC.tpe(), T.RBO.tpe(), T.EVL.tpe(),
			  		]

mgmtObjAnncTPEs = 	[	T.FWRAnnc.tpe(), T.SWRAnnc.tpe(), T.MEMAnnc.tpe(), T.ANIAnnc.tpe(),
						T.ANDIAnnc.tpe(), T.BATAnnc.tpe(), T.DVIAnnc.tpe(), T.DVCAnnc.tpe(),
						T.RBOAnnc.tpe(), T.EVLAnnc.tpe(),
			  		]

def resourceFromDict(resDict:dict, pi:str=None, acpi:str=None, ty:Union[T, int]=None, create:bool=False, isImported:bool=False) -> Result:
	""" Create a resource from a dictionary structure.
		This will *not* call the activate method, therefore some attributes
		may be set separately.
	"""
	resDict, root = pureResource(resDict)	# remove optional "m2m:xxx" level
	typ = resDict['ty'] if 'ty' in resDict else ty
	if typ != None and ty != None and typ != ty:
		return Result(dbg='type and resource specifier mismatch')
	mgd = resDict['mgd'] if 'mgd' in resDict else None		# for mgmtObj

	# Add extra acpi
	if acpi is not None:
		resDict['acpi'] = acpi if type(acpi) is list else [ acpi ]

	# store the import status in the original resDict
	if isImported:
		resDict[Resource.Resource._imported] = True	# Indicate that this is an imported resource


	# sorted by assumed frequency (small optimization)
	if typ == T.CIN or root == T.CIN.tpe():
		return Result(resource=CIN.CIN(resDict, pi=pi, create=create))
	elif typ == T.CNT or root == T.CNT.tpe():
		return Result(resource=CNT.CNT(resDict, pi=pi, create=create))
	elif typ == T.GRP or root == T.GRP.tpe():
		return Result(GRP.GRP(resDict, pi=pi, create=create))
	elif typ == T.GRP_FOPT or root == T.GRP_FOPT.tpe():
		return Result(resource=GRP_FOPT.GRP_FOPT(resDict, pi=pi, create=create))
	elif typ == T.ACP or root == T.ACP.tpe():
		return Result(resource=ACP.ACP(resDict, pi=pi, create=create))
	elif typ == T.FCNT:
		return Result(resource=FCNT.FCNT(resDict, pi=pi, fcntType=root, create=create))
	elif typ == T.FCI:
		return Result(resource=FCI.FCI(resDict, pi=pi, fcntType=root, create=create))	
	elif typ == T.AE or root == T.AE.tpe():
		return Result(resource=AE.AE(resDict, pi=pi, create=create))
	elif typ == T.SUB or root == T.SUB.tpe():
		return Result(resource=SUB.SUB(resDict, pi=pi, create=create))
	elif typ == T.CSR or root == T.CSR.tpe():
		return Result(resource=CSR.CSR(resDict, pi=pi, create=create))
	elif typ == T.NOD or root == T.NOD.tpe():
		return Result(resource=NOD.NOD(resDict, pi=pi, create=create))
	elif (typ == T.CNT_LA or root == T.CNT_LA.tpe()) and typ != T.FCNT_LA:
		return Result(resource=CNT_LA.CNT_LA(resDict, pi=pi, create=create))
	elif (typ == T.CNT_OL or root == T.CNT_OL.tpe()) and typ != T.FCNT_OL:
		return Result(resource=CNT_OL.CNT_OL(resDict, pi=pi, create=create))
	elif typ == T.FCNT_LA:
		return Result(resource=FCNT_LA.FCNT_LA(resDict, pi=pi, create=create))
	elif typ == T.FCNT_OL:
		return Result(resource=FCNT_OL.FCNT_OL(resDict, pi=pi, create=create))
	elif typ == T.REQ or root == T.REQ.tpe():
		return Result(resource=REQ.REQ(resDict, pi=pi, create=create))
	elif typ == T.PCH or root == T.PCH.tpe():
		return Result(resource=PCH.PCH(resDict, pi=pi, create=create))
	elif typ == T.CSEBase or root == T.CSEBase.tpe():
		return Result(resource=CSEBase.CSEBase(resDict, create=create))

	# Management Objects
	elif typ == T.MGMTOBJ or root in mgmtObjTPEs:
		if mgd == T.FWR or root == T.FWR.tpe():
			return Result(resource=FWR.FWR(resDict, pi=pi, create=create))
		elif mgd == T.SWR or root == T.SWR.tpe():
			return Result(resource=SWR.SWR(resDict, pi=pi, create=create))
		elif mgd == T.MEM or root == T.MEM.tpe():
			return Result(resource=MEM.MEM(resDict, pi=pi, create=create))
		elif mgd == T.ANI or root == T.ANI.tpe():
			return Result(resource=ANI.ANI(resDict, pi=pi, create=create))
		elif mgd == T.ANDI or root == T.ANDI.tpe():
			return Result(resource=ANDI.ANDI(resDict, pi=pi, create=create))
		elif mgd == T.BAT or root == T.BAT.tpe():
			return Result(resource=BAT.BAT(resDict, pi=pi, create=create))
		elif mgd == T.DVI or root == T.DVI.tpe():
			return Result(resource=DVI.DVI(resDict, pi=pi, create=create))
		elif mgd == T.DVC or root == T.DVC.tpe():
			return Result(resource=DVC.DVC(resDict, pi=pi, create=create))
		elif mgd == T.RBO or root == T.RBO.tpe():
			return Result(resource=RBO.RBO(resDict, pi=pi, create=create))
		elif  mgd == T.EVL or root == T.EVL.tpe():
			return Result(resource=EVL.EVL(resDict, pi=pi, create=create))
		elif  mgd == T.NYCFC or root == T.NYCFC.tpe():
			return Result(resource=NYCFC.NYCFC(resDict, pi=pi, create=create))

	# Announced Resources
	elif typ == T.ACPAnnc:
		return Result(resource=ACPAnnc.ACPAnnc(resDict, pi=pi, create=create))
	elif typ == T.AEAnnc:
		return Result(resource=AEAnnc.AEAnnc(resDict, pi=pi, create=create))
	elif typ == T.CNTAnnc:
		return Result(resource=CNTAnnc.CNTAnnc(resDict, pi=pi, create=create))
	elif typ == T.CINAnnc:
		return Result(resource=CINAnnc.CINAnnc(resDict, pi=pi, create=create))
	elif typ == T.GRPAnnc:
		return Result(resource=GRPAnnc.GRPAnnc(resDict, pi=pi, create=create))
	elif typ == T.NODAnnc:
		return Result(resource=NODAnnc.NODAnnc(resDict, pi=pi, create=create))
	elif typ == T.CSRAnnc:
		return Result(resource=CSRAnnc.CSRAnnc(resDict, pi=pi, create=create))
	elif typ == T.FCIAnnc:
		return Result(resource=FCIAnnc.FCIAnnc(resDict, pi=pi, create=create))
	elif typ == T.FCNTAnnc:
		return Result(resource=FCNTAnnc.FCNTAnnc(resDict, pi=pi, create=create))

	# Announced Management Objects
	elif typ == T.MGMTOBJAnnc or root in mgmtObjAnncTPEs:
		if mgd == T.FWRAnnc or root == T.FWRAnnc.tpe():
			return Result(resource=FWRAnnc.FWRAnnc(resDict, pi=pi, create=create))
		elif mgd == T.SWRAnnc or root == T.SWRAnnc.tpe():
			return Result(resource=SWRAnnc.SWRAnnc(resDict, pi=pi, create=create))
		elif mgd == T.MEMAnnc or root == T.MEMAnnc.tpe():
			return Result(resource=MEMAnnc.MEMAnnc(resDict, pi=pi, create=create))
		elif mgd == T.ANIAnnc or root == T.ANIAnnc.tpe():
			return Result(resource=ANIAnnc.ANIAnnc(resDict, pi=pi, create=create))
		elif mgd == T.ANDIAnnc or root == T.ANDIAnnc.tpe():
			return Result(resource=ANDIAnnc.ANDIAnnc(resDict, pi=pi, create=create))
		elif mgd == T.BATAnnc or root == T.BATAnnc.tpe():
			return Result(resource=BATAnnc.BATAnnc(resDict, pi=pi, create=create))
		elif mgd == T.DVIAnnc or root == T.DVIAnnc.tpe():
			return Result(resource=DVIAnnc.DVIAnnc(resDict, pi=pi, create=create))
		elif mgd == T.DVCAnnc or root == T.DVCAnnc.tpe():
			return Result(resource=DVCAnnc.DVCAnnc(resDict, pi=pi, create=create))
		elif mgd == T.RBOAnnc or root == T.RBOAnnc.tpe():
			return Result(resource=RBOAnnc.RBOAnnc(resDict, pi=pi, create=create))
		elif  mgd == T.EVLAnnc or root == T.EVLAnnc.tpe():
			return Result(resource=EVLAnnc.EVLAnnc(resDict, pi=pi, create=create))
		elif  mgd == T.NYCFCAnnc or root == T.NYCFCAnnc.tpe():
			return Result(resource=NYCFCAnnc.NYCFCAnnc(resDict, pi=pi, create=create))

	return Result(resource=Unknown.Unknown(resDict, root, pi=pi, create=create))	# Capture-All resource


excludeFromRoot = [ 'pi' ]
def pureResource(dct:dict) -> Tuple[dict, str]:
	""" Return the "pure" structure without the "m2m:xxx" or "<domain>:id" resource specifier."""
	rootKeys = list(dct.keys())
	# Try to determine the root identifier 
	if len(rootKeys) == 1 and (rk := rootKeys[0]) not in excludeFromRoot and re.match('[\w]+:[\w]', rk):
		return dct[rootKeys[0]], rootKeys[0]
	# Otherwise try to get the root identifier from the resource itself (stored as a private attribute)
	root = None
	if Resource.Resource._rtype in dct:
		root = dct[Resource.Resource._rtype]
	return dct, root


# def removeCommentsFromJSON(data:str) -> str:
# 	"""	Remove C-style comments from JSON.
# 	"""
# 	data = re.sub(r'^[\s]*//[^\n]*\n', '\n', data)		# Comment on first line
# 	data = re.sub(r'\n[\s]*//[^\n]*\n', '\n', data)	# Comments on some line in the middle
# 	data = re.sub(r'\n[\s]*//[^\n]*$', '\n', data)		# Comment on last line w/o newline at the end
# 	data = re.sub(r'/\\*.*?\\*/', '', data)
# 	return data


#commentPattern = r'(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)'
commentPattern = r'(\".*?(?<!\\)\"|\'.*?(?<!\\)\')|(/\*.*?\*/|//[^\r\n]*$)'	# recognized escaped comments
# first group captures quoted strings (double or single)
# second group captures comments (//single-line or /* multi-line */)
commentRegex = re.compile(commentPattern, re.MULTILINE|re.DOTALL)

def removeCommentsFromJSON(data:str) -> str:
	"""	This WILL remove:
			/* multi-line comments */
			// single-line comments
		
		Will NOT remove:
			String var1 = "this is /* not a comment. */";
			char *var2 = "this is // not a comment, either.";
			url = 'http://not.comment.com';
	"""
	def _replacer(match):	# type: ignore
		# if the 2nd group (capturing comments) is not None,
		# it means we have captured a non-quoted (real) comment string.
		if match.group(2) is not None:
			return "" # so we will return empty to remove the comment
		else: # otherwise, we will return the 1st group
			return match.group(1) # captured quoted-string
	return commentRegex.sub(_replacer, data)

decimalMatch = re.compile(r'{(\d+)}')
def findXPath(dct:dict, element:str, default:Any=None) -> Any:
	""" Find a structured element in dictionary.
		Example: findXPath(resource, 'm2m:cin/{1}/lbl/{0}')
	"""

	if element is None or dct is None:
		return default

	paths = element.split("/")
	data = dct
	for i in range(0,len(paths)):
		if data is None:
			return default
		if len(paths[i]) == 0:	# return if there is an empty path element
			return default
		elif (m := decimalMatch.search(paths[i])) is not None:	# Match array index {i}
			idx = int(m.group(1))
			if not isinstance(data, (list,dict)) or idx >= len(data):	# Check idx within range of list
				return default
			if isinstance(data, dict):
				data = data[list(data)[i]]
			else:
				data = data[idx]
		elif paths[i] not in data:	# if key not in dict
			return default
		else:
			data = data[paths[i]]	# found data for the next level down
	return data


# set a structured element in dictionary. Create if necessary, and observe the overwrite option
def setXPath(dct:Dict[str, Any], element:str, value:Any, overwrite:bool=True) -> bool:
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


def deleteNoneValuesFromDict(dct:dict) -> dict:
	if not isinstance(dct, dict):
		return dct
	return { key:value for key,value in ((key, deleteNoneValuesFromDict(value)) for key,value in dct.items()) if value is not None }


urlregex = re.compile(
		r'^(?:http|ftp)s?://' 						# http://, https://, ftp://, ftps://
		r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain
		r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9]))|' # localhost or single name w/o domain
		r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 		# ipv4
		r'(?::\d+)?' 								# optional port
		r'(?:/?|[/?]\S+)$', re.IGNORECASE)			# optional path


def isURL(url: str) -> bool:
	""" Check whether a given string is a URL. """
	return url is not None and isinstance(url, str) and re.match(urlregex, url) is not None


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
	Logging.logDebug(f'Originator: {originator}')
	Logging.logDebug(f'Allowed originators: {allowedOriginators}')

	if originator is None or allowedOriginators is None:
		return False
	for ao in allowedOriginators:
		if re.fullmatch(re.compile(ao), getIdFromOriginator(originator)):
			return True
	return False


def resourceDiff(old:Union[Resource.Resource, dict], new:Union[Resource.Resource, dict], modifiers:dict=None) -> dict:
	"""	Compare an old and a new resource. Keywords and values. Ignore internal __XYZ__ keys.
		Return a dictionary.
		If the modifier dict is given then it contains the changes that let from old to new.
	"""
	res = {}
	for k, v in new.items():
		if k.startswith('__'):	# ignore all internal attributes
			continue
		if not k in old:		# Key not in old
			res[k] = v
		elif v != old[k]:		# Value different
			res[k] = v
		elif modifiers is not None and k in modifiers:	# this means the attribute is overwritten by the same value. But still modified
			res[k] = v

	# Process deleted attributes. This is necessary since attributes can be
	# explicitly set to None/Nulls.
	for k, v in old.items():
		if k not in new:
			res[k] = None

	# ==> Old try to process Null attributes
	# if modifiers is not None:
	# 	for k,v in modifiers.items():
	# 		if v is None:
	# 			res[k] = v

	return res


def getCSE() -> Result:
	return CSE.dispatcher.retrieveResource(Configuration.get('cse.ri'))

	
def fanoutPointResource(id: str) -> Resource.Resource:
	"""	Check whether the target contains a fanoutPoint in between or as the target.
	"""
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
		if (result := CSE.dispatcher.retrieveResource(nid)).resource is not None:
			return result.resource
	return None


def getSerializationFromOriginator(originator:str) -> List[ContentSerializationType]:
	"""	Look for the content serializations of a registered originator.
		It is either an AE, a CSE or a CSR.
		Return a list of types.
	"""
	# First check whether there is an AE with that originator
	if (l := len(aes := CSE.storage.searchByValueInField('aei', originator))) > 0:
		if l > 1:
			Logging.logErr(f'More then one AE with the same aei: {originator}')
			return []
		csz = aes[0].csz
	# Else try whether there is a CSE or CSR
	elif (l := len(cses := CSE.storage.searchByValueInField('csi', getIdFromOriginator(originator)))) > 0:
		if l > 1:
			Logging.logErr(f'More then one CSE with the same csi: {originator}')
			return []
		csz = cses[0].csz
	# Else just an empty list
	else:
		return []
	# Convert the poa to a list of ContentSerializationTypes
	return [ ContentSerializationType.getType(c) for c in csz]

#
#	HTTP request helper functions
#


def dissectHttpRequest(request:Request, operation:Operation, _id:Tuple[str, str, str]) -> Result:
	cseRequest = CSERequest()

	# get the data first. This marks the request as consumed 
	#cseRequest.data = request.get_data(as_text=True)	# alternative: request.data.decode("utf-8")
	#cseRequest.data = request.data.decode("utf-8")		# alternative: request.get_data(as_text=True)
	cseRequest.data = request.data

	# handle ID's 
	cseRequest.id, cseRequest.csi, cseRequest.srn = _id

	# Copy the original request headers
	res = getRequestHeaders(request)
	cseRequest.headers = res.data	# copy the headers
	if res.rsc != RC.OK:			# but still, something might be wrong
		return Result(rsc=res.rsc, request=cseRequest, dbg=res.dbg, status=False)

	# No ID, return immediately 
	if cseRequest.id is None and cseRequest.srn is None:
		return Result(rsc=RC.notFound, request=cseRequest, dbg='missing identifier', status=False)
	
	try:
		cseRequest.args, msg = getRequestArguments(request, operation)
		if cseRequest.args is None:
			return Result(rsc=RC.badRequest, request=cseRequest, dbg=msg, status=False)
	except Exception as e:
		return Result(rsc=RC.invalidArguments, request=cseRequest, dbg=f'invalid arguments ({str(e)})', status=False)
	cseRequest.originalArgs	= deepcopy(request.args)	#type: ignore

	if cseRequest.data is not None and len(cseRequest.data) > 0:
		try:
			ct = ContentSerializationType.getType(cseRequest.headers.contentType, default=CSE.defaultSerialization)
			if (_d := deserializeData(cseRequest.data, ct)) is None:
				return Result(rsc=RC.unsupportedMediaType, request=cseRequest, dbg=f'Unsuppored media type for content-type: {cseRequest.headers.contentType}', status=False)
			cseRequest.dict = _d
		except Exception as e:
			Logging.logWarn('Bad request (malformed content?)')
			return Result(rsc=RC.badRequest, request=cseRequest, dbg=str(e), status=False)
			
	return Result(request=cseRequest, status=True)



def requestHeaderField(request: Request, field : str) -> str:
	if not request.headers.has_key(field):
		return None
	return request.headers.get(field)


# Get the request arguments, or meaningful defaults.
# Only a small subset is supported yet
# Throws an exception when a wrong type is encountered. This is part of the validation
def getRequestArguments(request:Request, operation:Operation=Operation.RETRIEVE) -> Tuple[RequestArguments, str]:
	
	# copy arguments for greedy attributes checking
	args = request.args.copy()	 	# type: ignore

	def _extractMultipleArgs(argName:str, target:dict, validate:bool=True) -> Tuple[bool, str]:
		"""	Get multi-arguments. Always create at least an empty list. Remove
			the found arguments from the original list.
		"""
		lst = []
		for e in args.getlist(argName):
			for es in (t := e.split()):	# check for number
				if validate:
					if not CSE.validator.validateRequestArgument(argName, es).status:
						return False, f'error validating "{argName}" argument(s)'
			lst.extend(t)
		if len(lst) > 0:
			target[argName] = lst
		args.poplist(argName)
		return True, None

	# result = RequestArguments(operation=operation, request=request)
	result = RequestArguments(operation=operation)


	# FU - Filter Usage
	if (fu := args.get('fu')) is not None:
		if not CSE.validator.validateRequestArgument('fu', fu).status:
			return None, 'error validating "fu" argument'
		try:
			fu = FilterUsage(int(fu))
		except ValueError as exc:
			return None, f'"{fu}" is not a valid value for fu'
		del args['fu']
	else:
		fu = FilterUsage.conditionalRetrieval
	if fu == FilterUsage.discoveryCriteria and operation == Operation.RETRIEVE:
		operation = Operation.DISCOVERY
	result.fu = fu


	# DRT - Desired Identifier Result Type
	if (drt := args.get('drt')) is not None: # 1=strucured, 2=unstructured
		if not CSE.validator.validateRequestArgument('drt', drt).status:
			return None, 'error validating "drt" argument'
		try:
			drt = DesiredIdentifierResultType(int(drt))
		except ValueError as exc:
			return None, f'"{drt}" is not a valid value for drt'
		del args['drt']
	else:
		drt = DesiredIdentifierResultType.structured
	result.drt = drt


	# FO - Filter Operation
	if (fo := args.get('fo')) is not None: # 1=AND, 2=OR
		if not CSE.validator.validateRequestArgument('fo', fo).status:
			return None, 'error validating "fo" argument'
		try:
			fo = FilterOperation(int(fo))
		except ValueError as exc:
			return None, f'"{fo}" is not a valid value for fo'
		del args['fo']
	else:
		fo = FilterOperation.AND # default
	result.fo = fo


	# RCN Result Content Type
	if (rcn := args.get('rcn')) is not None: 
		if not CSE.validator.validateRequestArgument('rcn', rcn).status:
			return None, 'error validating "rcn" argument'
		rcn = int(rcn)
		del args['rcn']
	else:
		if fu != FilterUsage.discoveryCriteria:
			# Different defaults for each operation
			if operation in [ Operation.RETRIEVE, Operation.CREATE, Operation.UPDATE ]:
				rcn = ResultContentType.attributes
			elif operation == Operation.DELETE:
				rcn = ResultContentType.nothing
		else:
			# discovery-result-references as default for Discovery operation
			rcn = ResultContentType.discoveryResultReferences

	# Check value of rcn depending on operation
	if operation == Operation.RETRIEVE and rcn not in [ ResultContentType.attributes,
														ResultContentType.attributesAndChildResources,
														ResultContentType.attributesAndChildResourceReferences,
														ResultContentType.childResourceReferences,
														ResultContentType.childResources,
														ResultContentType.originalResource ]:
		return None, f'rcn: {rcn:d} not allowed in RETRIEVE operation'
	elif operation == Operation.DISCOVERY and rcn not in [ ResultContentType.childResourceReferences,
														   ResultContentType.discoveryResultReferences ]:
		return None, f'rcn: {rcn:d} not allowed in DISCOVERY operation'
	elif operation == Operation.CREATE and rcn not in [ ResultContentType.attributes,
														ResultContentType.modifiedAttributes,
														ResultContentType.hierarchicalAddress,
														ResultContentType.hierarchicalAddressAttributes,
														ResultContentType.nothing ]:
		return None, f'rcn: {rcn:d} not allowed in CREATE operation'
	elif operation == Operation.UPDATE and rcn not in [ ResultContentType.attributes,
														ResultContentType.modifiedAttributes,
														ResultContentType.nothing ]:
		return None, f'rcn: {rcn:d} not allowed in UPDATE operation'
	elif operation == Operation.DELETE and rcn not in [ ResultContentType.attributes,
														ResultContentType.nothing,
														ResultContentType.attributesAndChildResources,
														ResultContentType.childResources,
														ResultContentType.attributesAndChildResourceReferences,
														ResultContentType.childResourceReferences ]:
		return None, f'rcn:  not allowed DELETE operation'

	result.rcn = ResultContentType(rcn)


	# RT - Response Type
	if (rt := args.get('rt')) is not None: 
		if not CSE.validator.validateRequestArgument('rt', rt).status:
			return None, 'error validating "rt" argument'
		try:
			rt = ResponseType(int(rt))
		except ValueError as exc:
			return None, f'"{rt}" is not a valid value for rt'
		del args['rt']
	else:
		rt = ResponseType.blockingRequest
	result.rt = rt


	# RP - Response Persistence
	if (rp := args.get('rp')) is not None: 
		if not CSE.validator.validateRequestArgument('rp', rp).status:
			return None, 'error validating "rp" argument'
		try:
			if rp.startswith('P'):
				rpts = getResourceDate(isodate.parse_duration(rp).total_seconds())
			elif 'T' in rp:
				rpts = rp
			else:
				raise ValueError
		except ValueError as exc:
			return None, f'"{rp}" is not a valid value for rp'
		del args['rp']
	else:
		rp = None
		rpts = None
	result.rp = rp
	result.rpts = rpts


	# handling conditions
	handling = { }
	for c in ['lim', 'lvl', 'ofst']:	# integer parameters
		if c in args:
			v = args[c]
			if not CSE.validator.validateRequestArgument(c, v).status:
				return None, f'error validating "{c}" argument'
			handling[c] = int(v)
			del args[c]
	for c in ['arp']:
		if c in args:
			v = args[c]
			if not CSE.validator.validateRequestArgument(c, v).status:
				return None, f'error validating "{c}" argument'
			handling[c] = v # string
			del args[c]
	result.handling = handling

	# conditions
	conditions:dict = {}

	# Extract and store other arguments
	for c in ['crb', 'cra', 'ms', 'us', 'sts', 'stb', 'exb', 'exa', 'lbq', 'sza', 'szb', 'catr', 'patr']:
		if (v := args.get(c)) is not None:
			if not CSE.validator.validateRequestArgument(c, v).status:
				return None, f'error validating "{c}" argument'
			conditions[c] = v
			del args[c]

	if not (res := _extractMultipleArgs('ty', conditions))[0]:
		return None, res[1]
	if not (res := _extractMultipleArgs('cty', conditions))[0]:
		return None, res[1]
	if not (res := _extractMultipleArgs('lbl', conditions, validate=False))[0]:
		return None, res[1]

	result.conditions = conditions

	# all remaining arguments are treated as matching attributes
	for arg, val in args.items():
		if not CSE.validator.validateRequestArgument(arg, val).status:
			return None, f'error validating (unknown?) "{arg}" argument)'
	# all arguments have passed, so add the remaining 
	result.attributes = args

	# Alternative: in case attributes are handled like ty, lbl, cty
	# attributes:dict = {}
	# for key in list(args.keys()):
	# 	if not (res := _extractMultipleArgs(key, attributes))[0]:
	# 		return None, res[1]
	# result.attributes = attributes

	# Finally return the collected arguments
	return result, None

		
def getRequestHeaders(request: Request) -> Result:
	rh 								= RequestHeaders()
	rh.originator 					= requestHeaderField(request, C.hfOrigin)
	rh.requestIdentifier			= requestHeaderField(request, C.hfRI)
	rh.requestExpirationTimestamp 	= requestHeaderField(request, C.hfRET)
	rh.responseExpirationTimestamp 	= requestHeaderField(request, C.hfRST)
	rh.operationExecutionTime 		= requestHeaderField(request, C.hfOET)
	rh.releaseVersionIndicator 		= requestHeaderField(request, C.hfRVI)


	if (rtu := requestHeaderField(request, C.hfRTU)) is not None:			# handle rtu list
		rh.responseTypeNUs = rtu.split('&')

	# content-type and accept
	rh.contentType 	= request.content_type
	rh.accept		= [ mt for mt, _ in request.accept_mimetypes ]	# get (multiple) accept headers from MIMEType[(x,nr)]

	if rh.contentType is not None:
		if not rh.contentType.startswith(tuple(C.supportedContentHeaderFormat)):
			rh.contentType 	= None
		else:
			p 				= rh.contentType.partition(';')	# always returns a 3-tuple
			rh.contentType 	= p[0] # content-type
			t  				= p[2].partition('=')[2]
			if len(t) > 0:	# check only if there is a resource type
				if t.isdigit() and (_t := int(t)) and T.has(_t):
					rh.resourceType = T(_t)
				else:
					return Result(rsc=RC.badRequest, data=rh, dbg=f'Unknown resource type: {t}')
	
	# accept
	rh.accept = request.headers.getlist('accept')
	rh.accept = [ a for a in rh.accept if a != '*/*' ]
	# if ((l := len(rh.accept)) == 1 and '*/*' in rh.accept) or l == 0:
	# 	rh.accept = [ CSE.defaultSerialization.toHeader() ]

	return Result(data=rh, rsc=RC.OK)


def serializeData(data:dict, ct:ContentSerializationType) -> Union[str, bytes]:
	"""	Serialize a dictionary, depending on the serialization type.
	"""
	encoder = json if ct == ContentSerializationType.JSON else cbor2 if ct == ContentSerializationType.CBOR else None
	if encoder is None:
		return None
	return encoder.dumps(data)


def deserializeData(data:bytes, ct:ContentSerializationType) -> dict:
	"""	Deserialize data into a dictionary, depending on the serialization type.
		If the len of the data is 0 then an empty dictionary is returned. 
	"""
	try:
		if len(data) == 0:
			return {}
		if ct == ContentSerializationType.JSON:
			return json.loads(data.decode("utf-8"))
		elif ct == ContentSerializationType.CBOR:
			return cbor2.loads(data)
	except Exception as e:
		Logging.logErr(f'Deserialization error: {str(e)}')
	return None

#
#	Threads
#

def renameCurrentThread(name:str = None, thread:threading.Thread = None) -> None:
	thread = threading.current_thread() if thread is None else thread
	thread.name = name if name is not None else str(thread.native_id)


#
#	Text formattings
#

def toHex(bts:bytes, toBinary:bool=False, withLength:bool=False) -> str:
	"""	Print bts as hex output, similar to the 'od' command.
	"""
	if len(bts) == 0 and not withLength: return ''
	result = ''
	n = 0
	b = bts[n:n+16]

	while b and len(b) > 0:

		if toBinary:
			s1 = ' '.join([f'{i:08b}' for i in b])
			s1 = f'{s1[0:71]} {s1[71:]}'
			width = 144
		else:
			s1 = ' '.join([f'{i:02x}' for i in b])
			s1 = f'{s1[0:23]} {s1[23:]}'
			width = 48

		s2 = ''.join([chr(i) if 32 <= i <= 127 else '.' for i in b])
		s2 = f'{s2[0:8]} {s2[8:]}'
		result += f'0x{n:08x}  {s1:<{width}}  | {s2}\n'

		n += 16
		b = bts[n:n+16]
	result += f'0x{len(bts):08x}'

	return result
