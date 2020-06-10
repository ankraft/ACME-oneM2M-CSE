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
	'loc'	: [ BT.list, 			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CSE, AE, CNT





	'acrs'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# m2m:listOfURIs - SUB
	'adri'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  AN.MA ],		# m2m:listOfURIs - ACP
	'aei'	: [ BT.string,			CAR.car1,   RO.NP,	RO.NP, AN.OA ],		# AE
	'airi'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  AN.MA ],		# m2m:listOfURIs - ACP
	'ape'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:activityPatternElements - AE
	'api'	: [ BT.string,			CAR.car1,   RO.M,	RO.NP, AN.OA ],		# AE
	'apn'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE
	'apri'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  AN.MA ],		# m2m:listOfURIs - ACP
	'bn'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'cbs'	: [ BT.nonNegInteger,	CAR.car1,   RO.NP,	RO.NP, AN.NA ],		# CNT
	'cnf'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# m2m_contentInfo - CIN
	'cni'	: [ BT.nonNegInteger,	CAR.car1, 	RO.NP,	RO.NP, AN.NA ],		# CNT
	'cnm'	: [ BT.nonNegInteger,	CAR.car1, 	RO.NP,	RO.NP, AN.NA ],		# GRP
	'con'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# CIN
	'conr'	: [ BT.dict,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# m2m:contentRef - CIN
	'cr'	: [ BT.list, 			CAR.car01,  RO.O,	RO.NP, AN.NA ],		# CNT
	'cs'	: [ BT.nonNegInteger,	CAR.car01,  RO.NP,	RO.NP, AN.NA ],		# CIN
	'csi'	: [ BT.string,			CAR.car1,   RO.NP,	RO.NP, AN.OA ],		# CSE
	'cst'	: [ BT.nonNegInteger,	CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# CSE
	'csy'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.NP, AN.OA ],		# m2m:consistencyStrategy - GRP
	'csz'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:serializations - AE, CSE (RO!)
	'disr'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'enc'	: [ BT.dict,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'esi'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.MA ],		# m2m:e2eSecInfo - AE, CSE
	'exc'	: [	BT.positiveInteger, CAR.car01, 	RO.O, 	RO.O,  AN.NA ],  	# SUB
	'gn'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# GRP
	'gpi'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'li'	: [ BT.anyURI,			CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# CNT
	'ln'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'macp'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'mbs'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'mei'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# m2m:externalID - AE
	'mia'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'mid'	: [ BT.list,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# list of m2m:anyURI - GRP
	'mni'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'mnm'	: [ BT.positiveInteger,	CAR.car1,   RO.M,	RO.O,  AN.OA ],		# GRP
	'mt'	: [ BT.nonNegInteger,	CAR.car1,   RO.O,	RO.NP, AN.OA ],		# m2m:memberType - GRP
	'mtv'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# GRP
	'nar'	: [ BT.dict,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# GRP
	'nec'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'nct'	: [ BT.nonNegInteger,	CAR.car1,  	RO.O,	RO.O,  AN.NA ],		# SUB
	'nfu'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'nl'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE, CSE
	'nsp'	: [ BT.positiveInteger,	CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'nu'	: [	BT.list, 			CAR.car1, 	RO.M, 	RO.O,  AN.NA],  	# SUB
	'or'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'pn'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'poa'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:poaList - AE, CSE
	'psn'	: [ BT.positiveInteger,	CAR.car01,  RO.O,	RO.NP, AN.NA ],		# SUB
	'pv'	: [ BT.dict,			CAR.car1,	RO.M,	RO.O,  AN.MA ],		# m2m:setOfArcs - ACP
	'pvs'	: [ BT.dict,			CAR.car1,	RO.M,	RO.O,  AN.MA ],		# m2m:setOfArcs - ACP
	'regs'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:AERegistrationStatus - AE
	'rl'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.NA ],		# SUB
	'rr'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# AE
	'scp'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:sessionCapabilities - AE
	'spty'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.NP, AN.OA ],		# m2m:specializationType - GRP
	'srt'	: [ BT.list, 			CAR.car01,  RO.O,	RO.NP, AN.NA ],		# CSE
	'srv'	: [ BT.list,			CAR.car01,  RO.M,	RO.O,  AN.MA ],		# m2m:supportedReleaseVersions - AE, CSE
	'ssi'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# GRP
	'su'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, AN.NA ],		# SUB
	'tren'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE
	'trps'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE

	# TBC Group:



	# TODO Lookup in TS-0004, 0001

	# CSE notificationCongestionPolicy 'ncp'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP,  AN.OA ],		# CSE

	# AE Not defined yet: ExternalGroupID?
	# AE CSE Not defined yet: enableTimeCompensation
	# CSE currentTime
	# CIN deletionCnt
	# GRP: somecastEnable, somecastAlgorithm not defined yet (shortname)

	

}



def constructPolicy(attributes):
	""" Help to construct a dict of policies for the given list of shortnames. """
	return { k:attributePolicies.get(k) for k in attributes }


class Validator(object):

	def __init__(self):
		Logging.log('Validator initialized')


	def shutdown(self):
		Logging.log('Validator shut down')

	#########################################################################


	def	validateAttributes(self, jsn, attributePolicies, create=True, isImported=False):
		""" Validate a resources attributes for types etc."""
		Logging.logDebug('Validating attributes')

		# Just return in case the resource instance is imported
		if isImported is not None and isImported:
			return (True, C.rcOK)

		# No policies?
		if attributePolicies is None:
			Logging.logWarn("No attribute policies")
			return (True, C.rcOK)

		# determine the request column, depending on create or updates
		reqp = 2 if create else 3
		(pureJson, key) = Utils.pureResource(jsn)
		if key is not None and not key.startswith("m2m:"):
			pureJson = jsn

		#Logging.logDebug(attributePolicies.items())
		for r in pureJson.keys():
			if r not in attributePolicies.keys():
				Logging.logWarn('Unknown attribute in resource: %s' % r)
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


	def validatePvs(self, jsn):
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


