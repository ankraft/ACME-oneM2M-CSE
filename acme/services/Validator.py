#
#	Types.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Validation service and functions
#

from __future__ import annotations
from copy import deepcopy
import re
from typing import Any, List, Dict, Tuple
import isodate

from ..etc.Types import AttributePolicy, AttributePolicyDict, BasicType as BT, Cardinality as CAR, EvalCriteriaOperator, RequestOptionality as RO, Announced as AN, ResponseStatusCode as RC, AttributePolicy
from ..etc.Types import JSON, FlexContainerAttributes
from ..etc.Types import Result, ResourceTypes as T
from ..etc import Utils as Utils, DateUtils as DateUtils
from ..services.Logging import Logging as L
from ..resources.Resource import Resource


# TODO AE Not defined yet: ExternalGroupID?
# TODO AE CSE Not defined yet: enableTimeCompensation
# TODO GRP: somecastEnable, somecastAlgorithm not defined yet (shortname)


attributePolicies:Dict[Tuple[T, str], AttributePolicy] 			= {}
""" General attribute Policies.

	{ ResourceType : AttributePolicy }
"""

# Will be filled by further specialization definitions.
flexContainerAttributes:FlexContainerAttributes = { }
"""	FlexContainer specializations. 

	{ tpe : { sn : AttributePolicy } }
"""

class Validator(object):


	def __init__(self) -> None:
		if L.isInfo: L.log('Validator initialized')


	def shutdown(self) -> bool:
		if L.isInfo: L.log('Validator shut down')
		return True

	#########################################################################


	def	validateAttributes(self, resource:JSON, tpe:str, ty:T = T.UNKNOWN, attributes:AttributePolicyDict = None, create:bool = True , isImported:bool = False, createdInternally:bool = False, isAnnounced:bool = False) -> Result:
		""" Validate a resources' attributes for types etc.

			Args:
				resource: dictionary to check
				tpe: The resource's resource type name
				ty: The resource type
				attributes: The attribute policy dictionary for the resource type. If this is None then validate automatically
				create: Boolean indicating whether this a CREATE request
				isImported: Boolean indicating whether a resource is imported. Then automatically return True.
				createdInternally: Boolean indicating that a resource is created internally
				isAnnounced: Boolean indicating that a resource is announced
			Return:
				Result object
		"""
		L.isDebug and L.logDebug('Validating attributes')

		# Just return in case the resource instance is imported
		if isImported:
			return Result(status = True)

		# No policies?
		if not attributes:
			L.isWarn and L.logWarn(f'No attribute policies: {resource}')
			return Result(status = True)

		# Set an index into the policy dataclass, depending on the validation type
		optionalIndex = 2 if create else 3	# index to create or update
		if isAnnounced:
			optionalIndex = 5	# index to announced

		# Get the pure resource and the resource's tpe
		(pureResDict, _tpe) = Utils.pureResource(resource)

		tpe = _tpe if _tpe and _tpe != tpe else tpe 				# determine the real tpe

		# if tpe is not None and not tpe.startswith("m2m:"):
		# 	pureResDict = dct

		attributePolicies = attributes
		# If this is a flexContainer then add the additional attributePolicies.
		# We don't want to change the original attributes, so copy it before (only if we add new attributePolicies)

		if ty in [ T.FCNT, T.FCI ] and tpe:
			if (fca := flexContainerAttributes.get(tpe)) is not None:
				attributePolicies = deepcopy(attributePolicies)
				attributePolicies.update(fca)
			else:
				L.logWarn(dbg := f'Unknown resource type: {tpe}')
				return Result(status = False, rsc = RC.badRequest, dbg = dbg)

		# L.logDebug(attributePolicies.items())
		# L.logWarn(pureResDict)
		
		# Check that all attributes have been defied
		for attributeName in pureResDict.keys():
			if attributeName not in attributePolicies.keys():
				L.logWarn(dbg := f'Unknown attribute: {attributeName} in resource: {tpe}')
				return Result(status = False, rsc = RC.badRequest, dbg = dbg)

		for attributeName, policy in attributePolicies.items():
			if not policy:
				L.isWarn and L.logWarn(f'No attribute policy found for attribute: {attributeName}')
				continue

			# Get the correct tuple for a resource when there are more definitions

			# Used a couple of times below
			policyOptional = policy.select(optionalIndex)

			# Check whether the attribute is allowed or mandatory in the request
			if (attributeValue := pureResDict.get(attributeName)) is None:	# ! might be an int, bool, so we need to check for None

				# check the the announced cases first
				if isAnnounced:
					# MA are not checked bc they are only present if they are present in the original resource
					continue
					
				if policyOptional == RO.M:		# Not okay, this attribute is mandatory but absent
					L.logWarn(dbg := f'Cannot find mandatory attribute: {attributeName}')
					return Result(status = False, rsc = RC.badRequest, dbg = dbg)

				# TODO Is the following actually executed??? Should it be somewhere else? Write a test
				if attributeName in pureResDict and policy.cardinality == CAR.CAR1: 	# but ignore CAR.car1N (which may be Null/None)
					L.logWarn(dbg := f'Cannot delete a mandatory attribute: {attributeName}')
					return Result(status = False, rsc = RC.badRequest, dbg = dbg)

				if policyOptional in [ RO.NP, RO.O ]:		# Okay that the attribute is not in the dict, since it is provided or optional
					continue
			else:
				if not createdInternally:
					if policyOptional == RO.NP:
						L.logWarn(dbg := f'Found non-provision attribute: {attributeName}')
						return Result(status = False, rsc = RC.badRequest, dbg = dbg)

				# check the the announced cases
				if isAnnounced:
					if policy.announcement == AN.NA:	# Not okay, attribute is not announced
						L.logWarn(dbg := f'Found non-announced attribute: {attributeName}')
						return Result(status = False, rsc = RC.badRequest, dbg = dbg)
					continue

				# Special handling for the ACP's pvs attribute
				if attributeName == 'pvs' and not (res := self.validatePvs(pureResDict)).status:
					return Result(status = False, rsc = RC.badRequest, dbg = res.dbg)

			# Check whether the value is of the correct type
			if (res := self._validateType(policy.type, attributeValue)).status:
				continue

			# fall-through means: not validated
			L.logWarn(dbg := f'Attribute/value validation error: {attributeName}={str(attributeValue)} ({res.dbg})')
			return Result(status = False, rsc = RC.badRequest, dbg = dbg)

		return Result(status = True)



	def validateAttribute(self, attribute:str, value:Any, attributeType:BT=None, rtype:T=T.ALL) -> Result:
		""" Validate a single attribute. 
			If `attributeType` is set then that type is taken to perform the check, otherwise the attribute
			type is determined.
		"""
		if attributeType is not None:	# use the given attribute type instead of determining it
			return self._validateType(attributeType, value, True)
		if policy := self.getAttributePolicy(rtype, attribute):
			return self._validateType(policy.type, value, True)
		return Result(status=False, dbg=f'validation for attribute {attribute} not defined')


	#
	#	Validate complex types
	#

	# TODO move this later to the attributePolicies file in init/ directory. Perhaps something along
	# 		"name" : [ "attribute1", "attribute", ...]


	complexAttributePolicies:Dict[str, AttributePolicyDict] = {
		# Response
		'rsp' :	{
			'rsc' : AttributePolicy(type=BT.integer,          cardinality=CAR.CAR1,  optionalCreate=RO.M, optionalUpdate=RO.M, optionalDiscovery=RO.O, announcement=AN.NA, sname='rsp', lname='responseStatusCode', namespace='m2m', tpe='m2m:rsc'),
			'rqi' : AttributePolicy(type=BT.string,           cardinality=CAR.CAR1,  optionalCreate=RO.M, optionalUpdate=RO.M, optionalDiscovery=RO.O, announcement=AN.NA, sname='rqi', lname='requestIdentifier', namespace='m2m', tpe='m2m:rqi'),
			'pc' : AttributePolicy(type=BT.dict,              cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='pc', lname='primitiveContent', namespace='m2m', tpe='m2m:pc'),
			'to' : AttributePolicy(type=BT.string,            cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='to', lname='to', namespace='m2m', tpe='m2m:to'),
			'fr' : AttributePolicy(type=BT.string,            cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='fr', lname='from', namespace='m2m', tpe='m2m:fr'),
			'or' : AttributePolicy(type=BT.timestamp,         cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='or', lname='originatingTimestamp', namespace='m2m', tpe='m2m:or'),
			'rset' : AttributePolicy(type=BT.absRelTimestamp, cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='rset', lname='resultExpirationTimestamp', namespace='m2m', tpe='m2m:rset'),
			'ec' : AttributePolicy(type=BT.positiveInteger,   cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='ec', lname='eventCategory', namespace='m2m', tpe='m2m:ec'),
			'cnst' : AttributePolicy(type=BT.positiveInteger, cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='cnst', lname='contentStatus', namespace='m2m', tpe='m2m:cnst'),
			'cnot' : AttributePolicy(type=BT.positiveInteger, cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='cnot', lname='contentOffset', namespace='m2m', tpe='m2m:cnot'),
			'ati' : AttributePolicy(type=BT.dict,             cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='ati', lname='assignedTokenIdentifiers', namespace='m2m', tpe='m2m:ati'),
			'tqf' : AttributePolicy(type=BT.dict,             cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='tqf', lname='tokenRequestInformation', namespace='m2m', tpe='m2m:tqf'),
			'asri' : AttributePolicy(type=BT.boolean,         cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='asri', lname='authorSignReqInfo', namespace='m2m', tpe='m2m:asri'),
			'rvi' : AttributePolicy(type=BT.string,           cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='rvi', lname='releaseVersionIndicator', namespace='m2m', tpe='m2m:rvi'),
			'vsi' : AttributePolicy(type=BT.string,           cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='vsi', lname='vendorInformation', namespace='m2m', tpe='m2m:vsi'),
		},
		# 'm2m:sgn' : {
		# 	'fr' : AttributePolicy(type=BT.string,            cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='fr', lname='from', namespace='m2m', tpe='m2m:fr'),
		# 	'to' : AttributePolicy(type=BT.string,            cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='to', lname='to', namespace='m2m', tpe='m2m:to'),
		# }

	}




	def validatePrimitiveContent(self, pc:JSON) -> Result:
		
		# None - pc is ok
		if pc is None:
			return Result(status=True)
		
		# Check number of elements == 1
		if len(pc.keys()) != 1:	# TODO is this correct?
			return Result(status=False, rsc=RC.badRequest, dbg=f'primitive content shall contain exactly one element')
		
		name,obj = list(pc.items())[0]
		if ap := self.complexAttributePolicies.get(name):
			return self.validateAttributes(obj, tpe=name, attributes=ap)
		
		return Result(status=True)


	#
	#	Additional validations.
	#

	def validatePvs(self, dct:JSON) -> Result:
		""" Validating special case for lists that are not allowed to be empty (pvs in ACP). """

		if (l :=len(dct['pvs'])) == 0:
			L.logWarn(dbg := 'Attribute pvs must not be an empty list')
			return Result(status=False, dbg=dbg)
		elif l > 1:
			L.logWarn(dbg := 'Attribute pvs must contain only one item')
			return Result(status=False, dbg=dbg)
		if not (acr := Utils.findXPath(dct, 'pvs/acr')):
			L.logWarn(dbg := 'Attribute pvs/acr not found')
			return Result(status=False, dbg=dbg)
		if not isinstance(acr, list):
			L.logWarn(dbg := 'Attribute pvs/acr must be a list')
			return Result(status=False, dbg=dbg)
		if len(acr) == 0:
			L.logWarn(dbg := 'Attribute pvs/acr must not be an empty list')
			return Result(status=False, dbg=dbg)
		return Result(status=True)


	# TODO allowed media type chars
	cnfRegex = re.compile(
		r'^[^:/]+/[^:/]+:[0-2]$'
		r'|^[^:/]+/[^:/]+:[0-2]$'
		r'|^[^:/]+/[^:/]+:[0-2]:[0-5]$'
	)
	def validateCNF(self, value:str) -> Result:
		"""	Validate the contents of the `contentInfo` attribute. """
		if isinstance(value, str) and re.match(self.cnfRegex, value) is not None:
			return Result(status=True)
		return Result(status=False, dbg=f'validation of cnf attribute failed: {value}')


	def validateCSICB(self, val:str, name:str) -> Result:
		"""	Validate the format of a CSE-ID in csi or cb attributes.
		"""
		# TODO Decide whether to correct this automatically, like in RemoteCSEManager._retrieveRemoteCSE()
		if not val:
			L.logDebug(dbg := f"{name} is missing")
			return Result(status = False, rsc = RC.badRequest, dbg = dbg)
		if not val.startswith('/'):
			L.logDebug(dbg := f"{name} must start with '/': {val}")
			return Result(status = False, rsc = RC.badRequest, dbg = dbg)
		return Result(status = True)


	def validateEvalCriteria(self, dct:JSON) -> Result:
		"""	Validate the format and content of an evc attribute.
		"""
		if (optr := dct.get('optr')) is None:
			L.logDebug(dbg := f'evc/optr is missing in evalCriteria')
			return Result(status = False, rsc = RC.badRequest, dbg = dbg)
		if not (res := self.validateAttribute('optr', optr)).status:
			return res
		if not (EvalCriteriaOperator.equal <= optr <= EvalCriteriaOperator.lessThanEqual):
			L.logDebug(dbg := f'evc/optr is out of range')
			return Result(status = False, rsc = RC.badRequest, dbg = dbg)
		
		if (sbjt := dct.get('sbjt')) is None:
			L.logDebug(dbg := f'evc/sbjt is missing in evalCriteria')
			return Result(status = False, rsc = RC.badRequest, dbg = dbg)
		if not (res := self.validateAttribute('sbjt', sbjt)).status:
			return res

		if (thld := dct.get('thld')) is None:
			L.logDebug(dbg := f'evc/thld is missing in evalCriteria')
			return Result(status = False, rsc = RC.badRequest, dbg = dbg)
		if not (res := self.validateAttribute('thld', sbjt)).status:
			return res

		return Result(status = True)
	



	def isExtraResourceAttribute(self, attr:str, resource:Resource) -> bool:
		"""	Check whether the attribute `attr` is neither a universal, common, or resource attribute,
			nor an internal attribute. Basically, this method returns `True` when the attribute
			is a custom attribute.
		
		"""
		return attr not in resource.attributePolicies and not attr.startswith('__')



	##########################################################################
	#
	#	Additional attribute definitions, e.g. for <flexContainer> specialisations.
	#

	def updateFlexContainerAttributes(self, additionalPolicies:FlexContainerAttributes) -> bool:
		""" Add or update new specialization attribute definitions to the validator.
			The dict has a single entry (the type) that contains another dict 
			of attribute policies for that type. 
		"""
		if len(additionalPolicies.keys()) != 1:
			L.logErr('Additional attributes must only contain 1 type')
			return False
		try:
			flexContainerAttributes.update(additionalPolicies)
		except Exception as e:
			L.logErr(str(e))
			return False
		return True


	def addFlexContainerAttributePolicy(self, policy:AttributePolicy) -> bool:
		""" Add a single new policy dictionary for a type's attributes. 
			
			This is done by either creating a new entry, or adding the new policy
			to the existing policies and then updating the old entry in the
			global dictionary.
		"""
		if not (policiesForTPE := flexContainerAttributes.get(policy.tpe)):
			defsForTPE = { policy.tpe : { policy.sname : policy } }					# No policy for TPE yes, so create it
		else:
			policiesForTPE[policy.sname] = policy									# Add/replace the policy for sname
			defsForTPE = { policy.tpe : policiesForTPE }				
		return self.updateFlexContainerAttributes(defsForTPE)


	def getFlexContainerAttributesFor(self, tpe:str) -> AttributePolicyDict:
		""" Return the dictionary of additional attributes for a flexCOntainer type or None. """
		return flexContainerAttributes.get(tpe)


	def addAttributePolicy(self, rtype:T, attr:str, attrPolicy:AttributePolicy) -> None:
		"""	Add a new attribute policy for normal resources. 
		"""
		attributePolicies[(rtype, attr)] = attrPolicy


	def getAttributePolicy(self, rtype:T, attr:str) -> AttributePolicy:
		"""	Return the attributePolicy for a resource type.
		"""
		# Search for the specific type first
		if (ap := attributePolicies.get((rtype, attr))):
			return ap

		# If it couldn't be found, look whether it has been defined for ALL
		if (ap := attributePolicies.get((T.ALL, attr))):
			return ap
		
		# TODO look for other types, requests, filter...
		return None

	#
	#	Internals.
	#

	def _validateType(self, dataType:BT, value:Any, convert:bool = False) -> Result:
		""" Check a value for its type. If the convert parameter is True then it
			is assumed that the value could be a stringified value and the method
			will attempt to convert the value to its target type; otherwise this
			is an error. 

			If the check is positive (Result.status==True) then Result.data is set
			to the determined data type.
		"""

		if dataType == BT.positiveInteger:
			if isinstance(value, int):
				if value > 0:
					return Result(status=True, data=dataType)
				return Result(status=False, dbg='value must be > 0')
			# try to convert string to number and compare
			if convert and isinstance(value, str):
				try:
					if int(value) > 0:
						return Result(status=True, data=dataType)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg=f'invalid type: {type(value).__name__}. Expected: positive integer')

		if dataType == BT.nonNegInteger:
			if isinstance(value, int):
				if value >= 0:
					return Result(status=True, data=dataType)
				return Result(status=False, dbg='value must be >= 0')
			# try to convert string to number and compare
			if convert and isinstance(value, str):
				try:
					if int(value) >= 0:
						return Result(status=True, data=BT.nonNegInteger)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg=f'invalid type: {type(value).__name__}. Expected: non-negative integer')

		if dataType in [ BT.unsignedInt, BT.unsignedLong ]:
			if isinstance(value, int):
				return Result(status=True, data=dataType)
			# try to convert string to number 
			if convert and isinstance(value, str):
				try:
					int(value)
					return Result(status=True, data=dataType)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg=f'invalid type: {type(value).__name__}. Expected: unsigned integer')

		if dataType == BT.timestamp and isinstance(value, str):
			if DateUtils.fromAbsRelTimestamp(value) == 0.0:
				return Result(status=False, dbg=f'format error in timestamp: {value}')
			return Result(status=True, data=dataType)

		if dataType == BT.absRelTimestamp:
			if isinstance(value, str):
				try:
					rel = int(value)
					# fallthrough
				except Exception as e:	# could happen if this is a string with an iso timestamp. Then try next test
					if DateUtils.fromAbsRelTimestamp(value) == 0.0:
						return Result(status=False, dbg=f'format error in absRelTimestamp: {value}')
				# fallthrough
			elif not isinstance(value, int):
				return Result(status=False, dbg=f'unsupported data type for absRelTimestamp')
			return Result(status=True, data=dataType)		# int/long is ok

		if dataType in [ BT.string, BT.anyURI ] and isinstance(value, str):
			return Result(status=True, data=dataType)

		if dataType == BT.list and isinstance(value, list):
			return Result(status=True, data=dataType)

		if dataType == BT.listNE and isinstance(value, list):
			if len(value) == 0:
				return Result(status=False, dbg='empty list is not allowed')
			return Result(status=True, data=dataType)
		
		if dataType == BT.dict and isinstance(value, dict):
			return Result(status=True, data=dataType)
		
		if dataType == BT.boolean:
			if isinstance(value, bool):
				return Result(status=True, data=dataType)
			# try to convert string to bool
			if convert and isinstance(value, str):	# "true"/"false"
				try:
					bool(value)
					return Result(status=True, data=dataType)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg=f'invalid type: {type(value).__name__}. Expected: bool')

		if dataType == BT.float:
			if isinstance(value, (float, int)):
				return Result(status=True, data=dataType)
			# try to convert string to number and compare
			if convert and isinstance(value, str):
				try:
					float(value)
					return Result(status=True, data=dataType)
				except Exception as e:
					return Result(status=False, dbg=str(e))
			return Result(status=False, dbg=f'invalid type: {type(value).__name__}. Expected: float')

		if dataType == BT.integer:
			if isinstance(value, int):
				return Result(status=True, data=dataType)
			# try to convert string to number and compare
			if convert and isinstance(value, str):
				try:
					int(value)
					return Result(status = True, data = dataType)
				except Exception as e:
					return Result(status = False, dbg = str(e))
			return Result(status = False, dbg = f'invalid type: {type(value).__name__}. Expected: integer')

		if dataType == BT.geoCoordinates and isinstance(value, dict):
			return Result(status = True, data = dataType)
		
		if dataType == BT.duration:
			try:
				isodate.parse_duration(value)
			except Exception as e:
				return Result(status = False, dbg = str(e))
			return Result(status = True, data = dataType)
		
		if dataType == BT.any:
			return Result(status = True, data = dataType)

		return Result(status = False, dbg = f'unknown type: {str(dataType)}, value type:{type(value)}')

