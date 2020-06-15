#
#	Types.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Validation service and functions
#

from Logging import Logging
from Types import BasicType as BT, Cardinality as CAR, RequestOptionality as RO, Announced as AN
from Constants import Constants as C
import Utils


# TODO add wildcard, e.g. for custom attributes

# predefined policies
attributePolicies = {
	'ty'	: [ BT.positiveInteger,	CAR.car1,   RO.NP, 	RO.NP, AN.NA ],
	'ri'	: [ BT.string, 			CAR.car1,   RO.NP, 	RO.NP, AN.NA ],
	'rn' 	: [ BT.string, 			CAR.car1,   RO.O,  	RO.NP, AN.NA ],
	'pi' 	: [ BT.string, 			CAR.car1,   RO.NP,	RO.NP, AN.NA ],
	'acpi'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  AN.MA ],
	'ct'	: [ BT.timestamp, 		CAR.car1,   RO.NP,	RO.NP, AN.NA ],
	'et'	: [ BT.timestamp, 		CAR.car1,   RO.O,	RO.O,  AN.MA ],
	'lt'	: [ BT.timestamp, 		CAR.car1,   RO.NP,	RO.NP, AN.NA ],
	'st'	: [ BT.nonNegInteger,	CAR.car1,   RO.NP,	RO.NP, AN.NA ],
	'lbl'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  AN.MA ],
	'at'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  AN.NA ],
	'aa'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  AN.NA ],
	'daci'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  AN.OA ],		# AE, CSE, CNT
	'loc'	: [ BT.list, 			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CSE, AE, CNT, FCNT



	'acrs'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# m2m:listOfURIs - SUB
	'act'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.O,  AN.OA ],		# SWR
	'acts'	: [ BT.dict,			CAR.car01,  RO.NP,	RO.NP, AN.NA ],		# SWR
	'adri'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  AN.MA ],		# m2m:listOfURIs - ACP
	'aei'	: [ BT.string,			CAR.car1,   RO.NP,	RO.NP, AN.OA ],		# AE
	'airi'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  AN.MA ],		# m2m:listOfURIs - ACP
	'ant'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# ANI
	'ape'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:activityPatternElements - AE
	'api'	: [ BT.string,			CAR.car1,   RO.M,	RO.NP, AN.OA ],		# AE
	'apn'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE
	'apri'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  AN.MA ],		# m2m:listOfURIs - ACP
	'att'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# BAT
	'awi'	: [ BT.anyURI,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# ANDI
	'bn'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'btl'	: [ BT.unsignedInt,		CAR.car1,   RO.M,	RO.O,  AN.OA ],		# BAT
	'bts'	: [ BT.positiveInteger,	CAR.car1,   RO.M,	RO.O,  AN.OA ],		# BAT
	'can'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# BAT
	'cas'	: [ BT.dict,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# BAT
	'cbs'	: [ BT.nonNegInteger,	CAR.car1,   RO.NP,	RO.NP, AN.NA ],		# CNT
	'cmlk'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# MGO
	'cnd'	: [ BT.string,			CAR.car1,   RO.M,	RO.NP, AN.MA ],		# CND
	'cnf'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# m2m_contentInfo - CIN
	'cni'	: [ BT.nonNegInteger,	CAR.car1, 	RO.NP,	RO.NP, AN.NA ],		# CNT, FCNT (CAR01)
	'cnm'	: [ BT.nonNegInteger,	CAR.car1, 	RO.NP,	RO.NP, AN.NA ],		# GRP
	'cnty'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# DVI
	'con'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# CIN
	'conr'	: [ BT.dict,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# m2m:contentRef - CIN
	'cr'	: [ BT.list, 			CAR.car01,  RO.O,	RO.NP, AN.NA ],		# CNT
	'cs'	: [ BT.nonNegInteger,	CAR.car01,  RO.NP,	RO.NP, AN.NA ],		# CIN, FCNT
	'csi'	: [ BT.string,			CAR.car1,   RO.NP,	RO.NP, AN.OA ],		# CSE
	'cst'	: [ BT.nonNegInteger,	CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# CSE
	'csy'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.NP, AN.OA ],		# m2m:consistencyStrategy - GRP
	'csz'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:serializations - AE, CSE (RO!)
	'cus'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# BAT
	'dc'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# MGO
	'dea'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.O,  AN.OA ],		# SWR
	'dis'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# BAT
	'disr'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'dlb'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# DVI
	'dty'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# DVI
	'dvd'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# ANDI
	'dvnm'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'dvt'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# ANDI
	'ena'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# BAT
	'enc'	: [ BT.dict,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'esi'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.MA ],		# m2m:e2eSecInfo - AE, CSE
	'exc'	: [	BT.positiveInteger, CAR.car01, 	RO.O, 	RO.O,  AN.NA ],  	# SUB
	'far'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# RBO
	'fwn'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# FWR
	'fwv'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'gn'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# GRP
	'gpi'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'hael'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# NOD
	'hcl'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# NOD
	'hsl'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# NOD
	'hwv'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# DVI
	'in'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.O,  AN.OA ],		# SWR
	'ins'	: [ BT.dict,			CAR.car01,  RO.NP,	RO.NP, AN.NA ],		# SWR
	'ldv'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# ANI
	'lga'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# ELV
	'lgd'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# ELV
	'lgO'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# ELV
	'lgst'	: [ BT.nonNegInteger,	CAR.car1,   RO.M,	RO.O,  AN.OA ],		# ELV
	'lgt'	: [ BT.nonNegInteger,	CAR.car1,   RO.M,	RO.O,  AN.OA ],		# ELV
	'li'	: [ BT.anyURI,			CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# CNT
	'ln'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'lnh'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# ANDI
	'loc'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'macp'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'man'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# DVI
	'mbs'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT, FCNT
	'mei'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# m2m:externalID - AE
	'mfd'	: [ BT.timestamp,		CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'mfdl'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'mgca'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# NOD
	'mgd'	: [ BT.nonNegInteger,	CAR.car1,   RO.M,	RO.NP, AN.MA ],		# MGO
	'mgs'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.NP, AN.MA ],		# MGO
	'mia'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT, FCNT
	'mid'	: [ BT.list,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# list of m2m:anyURI - GRP
	'mma'	: [ BT.unsignedLong,	CAR.car1,   RO.M,	RO.O,  AN.OA ],		# MEM
	'mmt'	: [ BT.unsignedLong,	CAR.car1,   RO.M,	RO.O,  AN.OA ],		# MEM
	'mni'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT, FCNT
	'mnm'	: [ BT.positiveInteger,	CAR.car1,   RO.M,	RO.O,  AN.OA ],		# GRP
	'mod'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# DVI
	'mt'	: [ BT.nonNegInteger,	CAR.car1,   RO.O,	RO.NP, AN.OA ],		# m2m:memberType - GRP
	'mtv'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# GRP
	'nar'	: [ BT.dict,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# GRP
	'nec'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'nct'	: [ BT.nonNegInteger,	CAR.car1,  	RO.O,	RO.O,  AN.NA ],		# SUB
	'nfu'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'ni'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.MA ],		# NOD
	'nid'	: [ BT.string,			CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# NOD
	'nl'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE, CSE, FCNT
	'nsp'	: [ BT.positiveInteger,	CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'nty'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# NOD
	'nu'	: [	BT.list, 			CAR.car1, 	RO.M, 	RO.O,  AN.NA ],  	# SUB
	'obis'	: [ BT.list,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# MGO
	'obps'	: [ BT.list,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# MGO
	'or'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT, FCNT
	'osv'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'pn'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'poa'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:poaList - AE, CSE
	'psn'	: [ BT.positiveInteger,	CAR.car01,  RO.O,	RO.NP, AN.NA ],		# SUB
	'ptl'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'purl'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'pv'	: [ BT.dict,			CAR.car1,	RO.M,	RO.O,  AN.MA ],		# m2m:setOfArcs - ACP
	'pvs'	: [ BT.dict,			CAR.car1,	RO.M,	RO.O,  AN.MA ],		# m2m:setOfArcs - ACP
	'rbo'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# RBO
	'regs'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:AERegistrationStatus - AE
	'rl'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'rms'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# NOD
	'rr'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# AE
	'scp'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:sessionCapabilities - AE
	'sld'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# ANDI
	'sli'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# ANDI
	'smod'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'spty'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.NP, AN.OA ],		# m2m:specializationType - GRP
	'spur'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'srt'	: [ BT.list, 			CAR.car01,  RO.O,	RO.NP, AN.NA ],		# CSE
	'srv'	: [ BT.list,			CAR.car01,  RO.M,	RO.O,  AN.MA ],		# m2m:supportedReleaseVersions - AE, CSE
	'ss'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# ANDI
	'ssi'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# GRP
	'su'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, AN.NA ],		# SUB
	'swn'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# SWR
	'swv'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'syst'	: [ BT.timestamp,		CAR.car01,  RO.O,	RO.O,  AN.OA ],		# DVI
	'tren'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE
	'trps'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE
	'ud'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# FWR
	'uds'	: [ BT.dict,			CAR.car01,  RO.NP,	RO.O,  AN.OA ],		# FWR
	'Un'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.O,  AN.OA ],		# SWR
	'url'	: [ BT.anyURI,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# FWR, SWR
	'vr'	: [ BT.string,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# FWR, SWR

	# TODO Lookup in TS-0004, 0001

	# CSE notificationCongestionPolicy 'ncp'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP,  AN.OA ],		# CSE

	# AE Not defined yet: ExternalGroupID?
	# AE CSE Not defined yet: enableTimeCompensation
	# CSE currentTime
	# CIN deletionCnt
	# GRP: somecastEnable, somecastAlgorithm not defined yet (shortname)


}



def constructPolicy(attributes : list) -> dict:
	""" Help to construct a dict of policies for the given list of shortnames. """
	return { k:attributePolicies.get(k) for k in attributes }


class Validator(object):

	def __init__(self):
		Logging.log('Validator initialized')


	def shutdown(self):
		Logging.log('Validator shut down')

	#########################################################################


	def	validateAttributes(self, jsn : dict, tpe: str, attributePolicies : dict, create : bool = True , isImported : bool = False) -> (bool, int):
		""" Validate a resources attributes for types etc."""
		Logging.logDebug('Validating attributes')

		# Just return in case the resource instance is imported
		if isImported is not None and isImported:
			return (True, C.rcOK)

		# No policies?
		if attributePolicies is None:
			Logging.logWarn("No attribute policies: %s" % jsn)
			return (True, C.rcOK)

		# determine the request column, depending on create or updates
		reqp = 2 if create else 3
		(pureJson, _tpe) = Utils.pureResource(jsn)
		tpe = _tpe if _tpe is not None and _tpe != tpe else tpe 				# determine the real tpe

		# if tpe is not None and not tpe.startswith("m2m:"):
		# 	pureJson = jsn
		attributePolicies = self._checkAdditionalAttributes(tpe, attributePolicies)

		#Logging.logDebug(attributePolicies.items())
		for r in pureJson.keys():
			if r not in attributePolicies.keys():
				Logging.logWarn('Unknown attribute: %s in resource: %s' % (r, tpe))
				return (False, C.rcBadRequest)
		for r, p in attributePolicies.items():
			if p is None:
				Logging.logWarn('No validation policy found for attribute: %s' % r)
				continue
			# Check whether the attribute is allowed or mandatory in the request
			if (v := pureJson.get(r)) is None:
				if p[reqp] == RO.M:		# Not okay, this attribute is mandatory
					Logging.logWarn('Cannot find mandatory attribute: %s' % r)
					return (False, C.rcBadRequest)
				if r in pureJson and p[1] == CAR.car1:
					Logging.logWarn('Cannot delete a mandatory attribute: %s' % r)
					return (False, C.rcBadRequest)
				if p[reqp] in [ RO.NP, RO.O]:	# Okay that the attribute is not in the json, since it is provided or optional
					continue
			else:
				if p[reqp] == RO.NP:
					Logging.logWarn('Found non-provision attribute: %s' % r)
					return (False, C.rcBadRequest)
				if r == 'pvs' and not self.validatePvs(pureJson):
					return (False, C.rcBadRequest)

			# Check whether the value is of the correct type
			pt = p[0]	# type
			pc = p[1]	# cardinality
			if pt == BT.positiveInteger and isinstance(v, int) and v > 0:
				continue
			if pt == BT.nonNegInteger and isinstance(v, int) and v >= 0:
				continue
			if pt in [ BT.unsignedInt, BT.unsignedLong ] and isinstance(v, int):
				continue
			if pt in [ BT.string, BT.timestamp, BT.anyURI ] and isinstance(v, str):
				continue
			if pt == BT.list and isinstance(v, list):
				continue
			if pt == BT.dict and isinstance(v, dict):
				continue
			if pt == BT.boolean and isinstance(v, bool):
				continue
			if pt == BT.geoCoordinates and isinstance(v, dict):
				continue
			
			# fall-through means: not validated
			Logging.logWarn('Attribute/value validation error: %s=%s' % (r, str(v)))
			return (False, C.rcBadRequest)

		return (True, C.rcOK)


	def validatePvs(self, jsn : dict) -> bool:
		""" Validating special case for lists that are not allowed to be empty (pvs in ACP). """

		if (l :=len(jsn['pvs'])) == 0:
			Logging.logWarn('Attribute pvs must not be an empty list')
			return False
		elif l > 1:
			Logging.logWarn('Attribute pvs must contain only one item')
			return False
		if (acr := Utils.findXPath(jsn, 'pvs/acr')) is None:
			Logging.logWarn('Attribute pvs/acr not found')
			return False
		if not isinstance(acr, list):
			Logging.logWarn('Attribute pvs/acr must be a list')
			return False
		if len(acr) == 0:
			Logging.logWarn('Attribute pvs/acr must not be an empty list')
			return False
		return True


	#
	#	Additional attribute definitions, e.g. for <flexContainer> specialisations.
	#

	# Will be filled by further specialization definitions.
	additionalAttributes = { }


	def addAdditionalAttributes(self, attributes : dict):
		""" Add new specialization attribute definitions to the validator. """
		self.additionalAttributes.update(attributes)


	def _checkAdditionalAttributes(self, tpe : str, attributePolicies : dict) -> dict:
		if tpe is not None and not tpe.startswith('m2m:') and tpe in self.additionalAttributes:
			attributePolicies.update(self.additionalAttributes.get(tpe))
		return attributePolicies

