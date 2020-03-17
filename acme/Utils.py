#
#	Utils.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

import datetime, random, string, sys, re
from resources import ACP, AE, ANDI, ANI, BAT, CIN, CNT, CNT_LA, CNT_OL, CSEBase, CSR, DVC
from resources import DVI, EVL, FCI, FCNT, FCNT_LA, FCNT_OL, FWR, GRP, GRP_FOPT, MEM, NOD, RBO, SUB, SWR, Unknown
from Constants import Constants as C
from Configuration import Configuration
from Logging import Logging
import CSE


def uniqueRI(prefix=''):
	p = prefix.split(':')
	p = p[1] if len(p) == 2 else p[0]
	return p + uniqueID()


def isUniqueRI(ri):
	return len(CSE.storage.identifier(ri)) == 0


def uniqueRN(prefix='un'):
	p = prefix.split(':')
	p = p[1] if len(p) == 2 else p[0]
	return "%s_%s" % (p, ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=C.maxIDLength)))


# create a unique aei, M2M-SP type
def uniqueAEI(prefix='S'):
	return prefix + ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=C.maxIDLength))


def fullRI(ri):
	return '/' + Configuration.get('cse.csi') + '/' + ri


def uniqueID():
	return str(random.randint(1,sys.maxsize))


def isVirtualResource(resource):
	return (ty := r.ty) and ty in C.tVirtualResources


# Check for valid ID
def isValidID(id):
	#return len(id) > 0 and '/' not in id 	# pi might be ""
	return '/' not in id


def getResourceDate(delta=0):
	return toISO8601Date(datetime.datetime.utcnow() + datetime.timedelta(seconds=delta))


def toISO8601Date(ts):
	if isinstance(ts, float):
		ts = datetime.datetime.utcfromtimestamp(ts)
	return ts.strftime('%Y%m%dT%H%M%S,%f')


def structuredPath(resource):
	rn = resource.rn
	if resource.ty == C.tCSEBase: # if CSE
		return rn

	# retrieve identifier record of the parent
	if (pi := resource.pi) is None:
		Logging.logErr('PI is None')
		return rn
	rpi = CSE.storage.identifier(pi) 
	if len(rpi) == 1:
		return rpi[0]['srn'] + '/' + rn
	Logging.logErr('Parent not fount in DB')
	return rn # fallback


def structuredPathFromRI(ri):
	if len((identifiers := CSE.storage.identifier(ri))) == 1:
		return identifiers[0]['srn']
	return None


def resourceFromJSON(jsn, pi=None, acpi=None, tpe=None, create=False):
	(jsn, root) = pureResource(jsn)	# remove optional "m2m:xxx" level
	ty = jsn['ty'] if 'ty' in jsn else tpe
	if ty != None and tpe != None and ty != tpe:
		return None
	mgd = jsn['mgd'] if 'mgd' in jsn else None		# for mgmtObj

	# Add extra acpi
	if acpi is not None:
		jsn['acpi'] = acpi if type(acpi) is list else [ acpi ]

	# sorted by assumed frequency (small optimization)
	if ty == C.tCIN or root == C.tsCIN:
		return CIN.CIN(jsn, pi=pi, create=create)
	elif ty == C.tCNT or root == C.tsCNT:
		return CNT.CNT(jsn, pi=pi, create=create)
	elif ty == C.tGRP or root == C.tsGRP:
		return GRP.GRP(jsn, pi=pi, create=create)
	elif ty == C.tGRP_FOPT or root == C.tsGRP_FOPT:
		return GRP_FOPT.GRP_FOPT(jsn, pi=pi, create=create)
	elif ty == C.tACP or root == C.tsACP:
		return ACP.ACP(jsn, pi=pi, create=create)
	elif ty == C.tFCNT:
		return FCNT.FCNT(jsn, pi=pi, fcntType=root, create=create)	
	elif ty == C.tFCI:
		return FCI.FCI(jsn, pi=pi, fcntType=root, create=create)	
	elif ty == C.tAE or root == C.tsAE:
		return AE.AE(jsn, pi=pi, create=create)
	elif ty == C.tSUB or root == C.tsSUB:
		return SUB.SUB(jsn, pi=pi, create=create)
	elif ty == C.tCSR or root == C.tsCSR:
		return CSR.CSR(jsn, pi=pi, create=create)
	elif ty == C.tNOD or root == C.tsNOD:
		return NOD.NOD(jsn, pi=pi, create=create)
	elif (ty == C.tMGMTOBJ and mgd == C.mgdFWR) or root == C.tsFWR:
		return FWR.FWR(jsn, pi=pi, create=create)
	elif (ty == C.tMGMTOBJ and mgd == C.mgdSWR) or root == C.tsSWR:
		return SWR.SWR(jsn, pi=pi, create=create)
	elif (ty == C.tMGMTOBJ and mgd == C.mgdMEM) or root == C.tsMEM:
		return MEM.MEM(jsn, pi=pi, create=create)
	elif (ty == C.tMGMTOBJ and mgd == C.mgdANI) or root == C.tsANI:
		return ANI.ANI(jsn, pi=pi, create=create)
	elif (ty == C.tMGMTOBJ and mgd == C.mgdANDI) or root == C.tsANDI:
		return ANDI.ANDI(jsn, pi=pi, create=create)
	elif (ty == C.tMGMTOBJ and mgd == C.mgdBAT) or root == C.tsBAT:
		return BAT.BAT(jsn, pi=pi, create=create)
	elif (ty == C.tMGMTOBJ and mgd == C.mgdDVI) or root == C.tsDVI:
		return DVI.DVI(jsn, pi=pi, create=create)
	elif (ty == C.tMGMTOBJ and mgd == C.mgdDVC) or root == C.tsDVC:
		return DVC.DVC(jsn, pi=pi, create=create)
	elif (ty == C.tMGMTOBJ and mgd == C.mgdRBO) or root == C.tsRBO:
		return RBO.RBO(jsn, pi=pi, create=create)
	elif (ty == C.tMGMTOBJ and mgd == C.mgdEVL) or root == C.tsEVL:
		return EVL.EVL(jsn, pi=pi, create=create)
	elif ty == C.tCNT_LA or root == C.tsCNT_LA:
		return CNT_LA.CNT_LA(jsn, pi=pi, create=create)
	elif ty == C.tCNT_OL or root == C.tsCNT_OL:
		return CNT_OL.CNT_OL(jsn, pi=pi, create=create)
	elif ty == C.tFCNT_LA:
		return FCNT_LA.FCNT_LA(jsn, pi=pi, create=create)
	elif ty == C.tFCNT_OL:
		return FCNT_OL.FCNT_OL(jsn, pi=pi, create=create)

	elif ty == C.tCSEBase or root == C.tsCSEBase:
		return CSEBase.CSEBase(jsn, create=create)
	else:
		return Unknown.Unknown(jsn, ty, root, pi=pi, create=create)	# Capture-All resource
	return None


# return the "pure" json without the "m2m:xxx" resource specifier
excludeFromRoot = [ 'pi' ]
def pureResource(jsn):
	rootKeys = list(jsn.keys())
	if len(rootKeys) == 1 and rootKeys[0] not in excludeFromRoot:
		return (jsn[rootKeys[0]], rootKeys[0])
	return (jsn, None)


# find a structured element in JSON
def findXPath(jsn, element, default=None):     
	paths = element.split("/")
	data = jsn
	for i in range(0,len(paths)):
		if paths[i] not in data:
			return default
		data = data[paths[i]]
	return data


# set a structured element in JSON. Create if necessary, and observce the overwrite option
def setXPath(jsn, element, value, overwrite=True):
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


def isURL(url):
	return url is not None and re.match(urlregex, url) is not None



#	Compare an old and a new resource. Keywords and values. Ignore internal __XYZ__ keys
#	Return a dictionary.
def resourceDiff(old, new):
	res = {}
	for k,v in new.items():
		if k.startswith('__'):	# ignore all internal attributes
			continue
		if not k in old:		# Key not in old
			res[k] = v
		elif v != old[k]:		# Value different
			res[k] = v 
	return res


def getCSE():
	return CSE.dispatcher.retrieveResource(Configuration.get('cse.ri'))

	
# Check whether the target contains a fanoutPoint in between or as the target
def fanoutPointResource(id):
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

def requestID(request, rootPath):
	p = request.path
	if p.startswith(rootPath):
		p = p[len(rootPath):]
	if p.startswith('/'):
		p = p[1:]
	return p


def requestHeaderField(request, field):
	if not request.headers.has_key(field):
		return None
	return request.headers.get(field)

		
def getRequestHeaders(request):
	originator = requestHeaderField(request, C.hfOrigin)
	rqi = requestHeaderField(request, C.hfRI)

	# content-type
	ty = None
	if (ct := request.content_type) is not None:
		if not ct.startswith(tuple(C.supportedContentSerializations)):
			ct = None
		else:
			p = ct.partition(';')
			ct = p[0] # content-type
			t = p[2].partition('=')[2]
			ty = int(t) if t.isdigit() else C.tUNKNOWN # resource type

	return (originator, ct, ty, rqi, C.rcOK)



