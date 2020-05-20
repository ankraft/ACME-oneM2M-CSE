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
	'daci'	: [ BT.list, 			CAR.car01L, RO.O,	RO.O,  AN.OA ],
	'loc'	: [ BT.list, 			CAR.car01,  RO.O,	RO.O,  AN.OA ],

	'or'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  AN.OA ],
	'cr'	: [ BT.list, 			CAR.car01,  RO.O,	RO.NP, AN.NA ],

	# CNT
	'mni'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],
	'mbs'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],
	'mia'	: [ BT.nonNegInteger,	CAR.car01,  RO.O,	RO.O,  AN.OA ],
	'cni'	: [ BT.nonNegInteger,	CAR.car1, 	RO.NP,	RO.NP, AN.NA ],
	'cbs'	: [ BT.nonNegInteger,	CAR.car1,   RO.NP,	RO.NP, AN.NA ],
	'li'	: [ BT.anyURI,			CAR.car01,  RO.NP,	RO.NP, AN.OA ],
	'disr'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],


	# AE
	'apn'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],
	'api'	: [ BT.string,			CAR.car1,   RO.M,	RO.NP, AN.OA ],
	'aei'	: [ BT.string,			CAR.car1,   RO.NP,	RO.NP, AN.OA ],
	'poa'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:poaList
	'nl'	: [ BT.anyURI,			CAR.car01,  RO.O,	RO.O,  AN.OA ],
	'rr'	: [ BT.boolean,			CAR.car1,   RO.M,	RO.O,  AN.OA ],
	'csz'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:serializations
	'esi'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.MA ],		# m2m:e2eSecInfo
	'mei'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.NA ],		# m2m:externalID
	'srv'	: [ BT.list,			CAR.car01,  RO.M,	RO.O,  AN.MA ],		# m2m:supportedReleaseVersions
	'regs'	: [ BT.string,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:AERegistrationStatus
	'trps'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],
	'scp'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:sessionCapabilities
	'tren'	: [ BT.boolean,			CAR.car01,  RO.O,	RO.O,  AN.OA ],
	'ape'	: [ BT.list,			CAR.car01,  RO.O,	RO.O,  AN.OA ],		# m2m:activityPatternElements
	# Not defined yet: ExternalGroupID?
	# Not defined yet: enableTimeCompensation
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


	def	validateAttributes(self, jsn, attributePolicies, create=True):
		""" Validate a resources attributes for types etc."""
		Logging.logDebug('Validating attributes')

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
			if pt == BT.boolean and isinstance(v, bool) and v > 0:
				continue
			if pt == BT.geoCoordinates and isinstance(v, dict):
				continue
			
			# fall-through means: not validated
			Logging.logDebug('Attribute/value validation error: %s=%s' % (r, str(v)))
			return (False, C.rcBadRequest)

		return (True, C.rcOK)

