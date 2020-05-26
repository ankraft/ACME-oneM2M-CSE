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





	'adri'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  AN.MA ],		# m2m:listOfURIs - ACP
	'aei'	: [ BT.string,			CAR.car1,   RO.NP,	RO.NP, AN.OA ],		# AE
	'airi'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  AN.MA ],		# m2m:listOfURIs - ACP
	'ape'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:activityPatternElements - AE
	'api'	: [ BT.string,			CAR.car1,   RO.M,	RO.NP, AN.OA ],		# AE
	'apn'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE
	'apri'	: [ BT.list,			CAR.car1,	RO.O,	RO.O,  AN.MA ],		# m2m:listOfURIs - ACP
	'cbs'	: [ BT.nonNegInteger,	CAR.car1,   RO.NP,	RO.NP, AN.NA ],		# CNT
	'cnf'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# m2m_contentInfo - CIN
	'cni'	: [ BT.nonNegInteger,	CAR.car1, 	RO.NP,	RO.NP, AN.NA ],		# CNT
	'con'	: [ BT.string,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# CIN
	'conr'	: [ BT.dict,			CAR.car01,  RO.O,	RO.NP, AN.OA ],		# m2m:contentRef - CIN
	'cr'	: [ BT.list, 			CAR.car01,  RO.O,	RO.NP, AN.NA ],		# CNT
	'cs'	: [ BT.nonNegInteger,	CAR.car01,  RO.NP,	RO.NP, AN.NA ],		# CIN
	'csi'	: [ BT.string,			CAR.car1,   RO.NP,	RO.NP, AN.OA ],		# CSE
	'cst'	: [ BT.nonNegInteger,	CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# CSE
	'csz'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:serializations - AE, CSE (RO!)
	'disr'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'esi'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.MA ],		# m2m:e2eSecInfo - AE, CSE
	'li'	: [ BT.anyURI,			CAR.car01,  RO.NP,	RO.NP, AN.OA ],		# CNT
	'mbs'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'mei'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# m2m:externalID - AE
	'mia'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'mni'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'nl'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE, CSE
	'or'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# CNT
	'poa'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:poaList - AE, CSE
	'pv'	: [ BT.dict,			CAR.car1,	RO.M,	RO.O,  AN.MA ],		# m2m:setOfArcs - ACP
	'pvs'	: [ BT.dict,			CAR.car1,	RO.M,	RO.O,  AN.MA ],		# m2m:setOfArcs - ACP
	'regs'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:AERegistrationStatus - AE
	'rr'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  AN.OA ],		# AE
	'scp'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:sessionCapabilities - AE
	'srt'	: [ BT.list, 			CAR.car01,  RO.O,	RO.NP, AN.NA ],		# CSE
	'srv'	: [ BT.list,			CAR.car01,  RO.M,	RO.O,  AN.MA ],		# m2m:supportedReleaseVersions - AE, CSE
	'tren'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE
	'trps'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# AE

	# TBC Group:

	'mt'	: [ BT.nonNegInteger,	CAR.car1,	RO.O,	RO.NP, AN.OA ],		# GRP
	'spty'	: [ BT.dict,			CAR.car01,	RO.O,	RO.NP, AN.OA ],		# GRP


	# TODO Lookup in TS-0004, 0001

	# CSE notificationCongestionPolicy 'ncp'	: [ BT.boolean,			CAR.car01,  RO.NP,	RO.NP,  AN.OA ],		# CSE

	# AE Not defined yet: ExternalGroupID?
	# AE CSE Not defined yet: enableTimeCompensation
	# CSE currentTime
	# CIN deletionCnt

	

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
			return (True, C.rcOK)


		# determine the request column, depending on create or updates
		reqp = 2 if create else 3

		for r, p in attributePolicies.items():
			if p is None:
				Logging.logWarn('No validation policy found for attribute: %s' % r)
				continue

			# Check whether the attribute is allowed or mandatory in the request
			if (v := jsn.get(r)) is None:
				if p[reqp] == RO.M:		# Not okay, this attribute is mandatory
					Logging.logDebug('Cannot find mandatory attribute: %s' % r)
					return (False, C.rcBadRequest)
				if p[reqp] in [ RO.NP, RO.O]:	# Okay that the attribute is not in the json, since it is provided or optional
					continue
			else:
				if p[reqp] == RO.NP:
					Logging.logDebug('Found non-provision attribute: %s' % r)
					return (False, C.rcBadRequest)
				#Special case for lists that are not allowed to be empty (pvs in ACP)
				if r in ['pvs']:
					if jsn.get(r).len == 0:
						Logging.logDebug('Attribute %s cannot be an empty list' % r)
						return (False, C.rcBadRequest)
					elif jsn.get(r).len == 1:
						if jsn.get(r['acr'][0].len == 0):
							Logging.logDebug('Attribute %s cannot be an empty list' % r)
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
			Logging.logDebug('Attribute/value validation error: %s=%s' % (r, str(v)))
			return (False, C.rcBadRequest)

		return (True, C.rcOK)

