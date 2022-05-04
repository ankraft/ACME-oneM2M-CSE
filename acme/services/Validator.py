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
from typing import Any, Dict, Tuple
import isodate

from ..etc.Types import AttributePolicy, ResourceAttributePolicyDict, AttributePolicyDict, BasicType as BT, Cardinality as CAR
from ..etc.Types import RequestOptionality as RO, Announced as AN, AttributePolicy
from ..etc.Types import JSON, FlexContainerAttributes, FlexContainerSpecializations
from ..etc.Types import Result, ResourceTypes as T
from ..etc import Utils as Utils, DateUtils as DateUtils
from ..services.Logging import Logging as L
from ..resources.Resource import Resource


# TODO AE Not defined yet: ExternalGroupID?
# TODO AE CSE Not defined yet: enableTimeCompensation
# TODO GRP: somecastEnable, somecastAlgorithm not defined yet (shortname)

attributePolicies:ResourceAttributePolicyDict 			= {}
""" General attribute Policies.

	{ ResourceType : AttributePolicy }
"""

# Will be filled by further specialization definitions.
flexContainerAttributes:FlexContainerAttributes = { }
"""	FlexContainer specialization attributes. 

	{ tpe : { sn : AttributePolicy } }
"""

flexContainerSpecializations:FlexContainerSpecializations = {}
"""	FlexContainer specialization aspects.

	{ tpe : cnd }
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
			return Result.successResult()

		# No policies?
		if not attributes:
			L.isWarn and L.logWarn(f'No attribute policies: {resource}')
			return Result.successResult()

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
				return Result.errorResult(dbg = dbg)

		# L.logDebug(attributePolicies.items())
		# L.logWarn(pureResDict)
		
		# Check that all attributes have been defined
		for attributeName in pureResDict.keys():
			if attributeName not in attributePolicies.keys():
				L.logWarn(dbg := f'Unknown attribute: {attributeName} in resource: {tpe}')
				return Result.errorResult(dbg = dbg)

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
					return Result.errorResult(dbg = dbg)

				# TODO Is the following actually executed??? Should it be somewhere else? Write a test
				if attributeName in pureResDict and policy.cardinality == CAR.CAR1: 	# but ignore CAR.car1N (which may be Null/None)
					L.logWarn(dbg := f'Cannot delete a mandatory attribute: {attributeName}')
					return Result.errorResult(dbg = dbg)

				if policyOptional in [ RO.NP, RO.O ]:		# Okay that the attribute is not in the dict, since it is provided or optional
					continue
			else:
				if not createdInternally:
					if policyOptional == RO.NP:
						L.logWarn(dbg := f'Found non-provision attribute: {attributeName}')
						return Result.errorResult(dbg = dbg)

				# check the the announced cases
				if isAnnounced:
					if policy.announcement == AN.NA:	# Not okay, attribute is not announced
						L.logWarn(dbg := f'Found non-announced attribute: {attributeName}')
						return Result.errorResult(dbg = dbg)
					continue

				# Special handling for the ACP's pvs attribute
				if attributeName == 'pvs' and not (res := self.validatePvs(pureResDict)).status:
					return Result.errorResult(dbg = res.dbg)

			# Check whether the value is of the correct type
			if (res := self._validateType(policy.type, attributeValue, policy = policy)).status:
				# Still some further checks are necessary

				# Check list. May be empty or needs to contain at least one member
				if policy.cardinality == CAR.CAR1LN and len(attributeValue) == 0:
					L.logWarn(dbg := f'List attribute must be non-empty: {attributeName}')
					return Result.errorResult(dbg = res.dbg)

				continue
		

			# fall-through means: not validated
			L.logWarn(dbg := f'Attribute/value validation error: {attributeName}={str(attributeValue)} ({res.dbg})')
			return Result.errorResult(dbg = dbg)

		return Result.successResult()



	def validateAttribute(self, attribute:str, value:Any, attributeType:BT = None, rtype:T = T.ALL) -> Result:
		""" Validate a single attribute. 
		
			Args:
				attribute: Name of the attribute to perform the check.
				value: Value to validate for the attribute.
				attributeType: If `attributeType` is set then that type is taken to perform the check, otherwise the attribute type is determined.
				rtype: ResourceType. Some attributes depend on the resource type.
			Return:
				Result. If successful then Result.data contains the determined attribute.
		"""
		if attributeType is not None:	# use the given attribute type instead of determining it
			return self._validateType(attributeType, value, True)
		if policy := self.getAttributePolicy(rtype, attribute):
			return self._validateType(policy.type, value, True, policy = policy)
		return Result.errorResult(dbg = f'validation for attribute {attribute} not defined')


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
			return Result.successResult()
		
		# Check number of elements == 1
		if len(pc.keys()) != 1:	# TODO is this correct?
			return Result.errorResult(dbg = f'primitive content shall contain exactly one element')
		
		name,obj = list(pc.items())[0]
		if ap := self.complexAttributePolicies.get(name):
			return self.validateAttributes(obj, tpe=name, attributes=ap)
		
		return Result.successResult()


	#
	#	Additional validations.
	#

	def validatePvs(self, dct:JSON) -> Result:
		""" Validating special case for lists that are not allowed to be empty (pvs in ACP). """

		if (l :=len(dct['pvs'])) == 0:
			L.logWarn(dbg := 'Attribute pvs must not be an empty list')
			return Result.errorResult(dbg = dbg)
		elif l > 1:
			L.logWarn(dbg := 'Attribute pvs must contain only one item')
			return Result.errorResult(dbg = dbg)
		if not (acr := Utils.findXPath(dct, 'pvs/acr')):
			L.logWarn(dbg := 'Attribute pvs/acr not found')
			return Result.errorResult(dbg = dbg)
		if not isinstance(acr, list):
			L.logWarn(dbg := 'Attribute pvs/acr must be a list')
			return Result.errorResult(dbg = dbg)
		if len(acr) == 0:
			L.logWarn(dbg := 'Attribute pvs/acr must not be an empty list')
			return Result.errorResult(dbg = dbg)
		return Result.successResult()


	# TODO allowed media type chars
	cnfRegex = re.compile(
		r'^[^:/]+/[^:/]+:[0-2]$'
		r'|^[^:/]+/[^:/]+:[0-2]$'
		r'|^[^:/]+/[^:/]+:[0-2]:[0-5]$'
	)
	def validateCNF(self, value:str) -> Result:
		"""	Validate the contents of the `contentInfo` attribute. """
		if isinstance(value, str) and re.match(self.cnfRegex, value) is not None:
			return Result.successResult()
		return Result.errorResult(dbg = f'validation of cnf attribute failed: {value}')


	def validateCSICB(self, val:str, name:str) -> Result:
		"""	Validate the format of a CSE-ID in csi or cb attributes.
		"""
		# TODO Decide whether to correct this automatically, like in RemoteCSEManager._retrieveRemoteCSE()
		if not val:
			L.logDebug(dbg := f"{name} is missing")
			return Result.errorResult(dbg = dbg)
		if not val.startswith('/'):
			L.logDebug(dbg := f"{name} must start with '/': {val}")
			return Result.errorResult(dbg = dbg)
		return Result.successResult()


	# TODO REMOVEME
	# def validateEvalCriteria(self, dct:JSON) -> Result:
	# 	"""	Validate the format and content of an evc attribute.
	# 	"""
	# 	if (optr := dct.get('optr')) is None:
	# 		L.logDebug(dbg := f'evc/optr is missing in evalCriteria')
	# 		return Result.errorResult(dbg = dbg)
	# 	if not (res := self.validateAttribute('optr', optr)).status:
	# 		return res
	# 	if not (EvalCriteriaOperator.equal <= optr <= EvalCriteriaOperator.lessThanEqual):
	# 		L.logDebug(dbg := f'evc/optr is out of range')
	# 		return Result.errorResult(dbg = dbg)
		
	# 	if (sbjt := dct.get('sbjt')) is None:
	# 		L.logDebug(dbg := f'evc/sbjt is missing in evalCriteria')
	# 		return Result.errorResult(dbg = dbg)
	# 	if not (res := self.validateAttribute('sbjt', sbjt)).status:
	# 		return res

	# 	if (thld := dct.get('thld')) is None:
	# 		L.logDebug(dbg := f'evc/thld is missing in evalCriteria')
	# 		return Result.errorResult(dbg = dbg)
	# 	if not (res := self.validateAttribute('thld', sbjt)).status:
	# 		return res

	# 	return Result.successResult()
	

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

			Args:
				policy: AttributePolicy dictionary with a single attribute policy.
			Return:
				Boolean, indicating whether a policy was added successfully.
		"""
		if not (policiesForTPE := flexContainerAttributes.get(policy.tpe)):
			defsForTPE = { policy.tpe : { policy.sname : policy } }					# No policy for TPE yes, so create it
		else:
			policiesForTPE[policy.sname] = policy									# Add/replace the policy for sname
			defsForTPE = { policy.tpe : policiesForTPE }				
		return self.updateFlexContainerAttributes(defsForTPE)


	def getFlexContainerAttributesFor(self, tpe:str) -> AttributePolicyDict:
		""" Return the attribute policies for a flexContainer specialization.
		
			Args:
				tpe: String, domain and short name of the flexContainer specialization.
			Return:
				Dictictionary of additional attributes for a flexCOntainer type or None.
		 """
		return flexContainerAttributes.get(tpe)
	

	def clearFlexContainerAttributes(self) -> None:
		"""	Clear the flexContainer attributes.
		"""
		flexContainerAttributes.clear()


	def addFlexContainerSpecialization(self, tpe:str, cnd:str) -> bool:
		"""	Add flexContainer specialization information to the internal dictionary.
		
			Args:
				tpe: String, domain and short name of the flexContainer specialization.
				cnd: String, the containerDefinition of the flexContainer specialization.
			Return:
				Boolean, indicating whether a specialization was added successfully. 

		"""
		if not tpe in flexContainerSpecializations:
			flexContainerSpecializations[tpe] = cnd
			return True
		return False


	def getFlexContainerSpecialization(self, tpe:str) -> Tuple[str]:
		"""	Return the availale data for a flexContainer specialization.
		
			Args:
				tpe: String, domain and short name of the flexContainer specialization.
			Return:
				Tuple with the flexContainer specialization data (or None if none exists).
		"""
		return ( flexContainerSpecializations.get(tpe), )

	
	def hasFlexContainerContainerDefinition(self, cnd:str) -> bool:
		"""	Test whether a flexContainer specialization with a containerDefinition exists.
				
			Args:
				cnd: String, containerDefinition
			Return:
				Boolean, indicating existens.

		"""
		return any(( each for each in flexContainerSpecializations.values() if each == cnd ))
	

	def clearFlexContainerSpecializations(self) -> None:
		"""	Clear the flexContainer specialization information.
		"""
		flexContainerSpecializations.clear()


	def addAttributePolicy(self, rtype:T|str, attr:str, attrPolicy:AttributePolicy) -> None:
		"""	Add a new attribute policy for normal resources. 
		"""
		if (rtype, attr) in attributePolicies:
			L.logErr(f'Policy {(rtype, attr)} is already registered')
		attributePolicies[(rtype, attr)] = attrPolicy


	def getAttributePolicy(self, rtype:T|str, attr:str) -> AttributePolicy:
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
	

	def getAllAttributePolicies(self) -> ResourceAttributePolicyDict:
		return attributePolicies


	def clearAttributePolicies(self) -> None:
		"""	Clear the attribute policies.
		"""
		attributePolicies.clear()


	#
	#	Internals.
	#

	def _validateType(self, dataType:BT, value:Any, convert:bool = False, policy:AttributePolicy = None) -> Result:
		""" Check a value for its type. 
					
			Args:
				dataType: Required data type for the value to check against.
				value: Value to validate.
				convert: If the convert parameter is True then it is assumed that the value could be a stringified
					value and the method will attempt to convert the value to its target type; otherwise this
					is an error. 
			Return:
				Result. If the check is positive (Result.status = =True) then Result.data is set to a tuple (the determined data type, the converted value).
		"""


		# Ignore None values
		if value is None:
			return Result(status = True, data = (dataType, value))


		# convert some types if necessary
		if convert:
			if dataType in [ BT.positiveInteger, BT.nonNegInteger, BT.unsignedInt, BT.unsignedLong, BT.integer, BT.enum ] and isinstance(value, str):
				try:
					value = int(value)
				except Exception as e:
					return Result.errorResult(dbg = str(e))
			elif dataType == BT.boolean and isinstance(value, str):	# "true"/"false"
				try:
					value = bool(value)
				except Exception as e:
					return Result.errorResult(dbg = str(e))
			elif dataType == BT.float and isinstance(value, str):
				try:
					value = float(value)
				except Exception as e:
					return Result.errorResult(dbg = str(e))

		# Check types and values

		if dataType == BT.positiveInteger:
			if isinstance(value, int):
				if value > 0:
					return Result(status = True, data = (dataType, value))
				return Result.errorResult(dbg = 'value must be > 0')
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: positive integer')
		
		if dataType == BT.enum:
			if isinstance(value, int):
				if policy is not None and len(policy.evalues) and value not in policy.evalues:
					return Result.errorResult(dbg = 'undefined enum value')
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: positive integer')

		if dataType == BT.nonNegInteger:
			if isinstance(value, int):
				if value >= 0:
					return Result(status = True, data = (dataType, value))
				return Result.errorResult(dbg = 'value must be >= 0')
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: non-negative integer')

		if dataType in [ BT.unsignedInt, BT.unsignedLong ]:
			if isinstance(value, int):
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: unsigned integer')

		if dataType == BT.timestamp and isinstance(value, str):
			if DateUtils.fromAbsRelTimestamp(value) == 0.0:
				return Result.errorResult(dbg = f'format error in timestamp: {value}')
			return Result(status = True, data = (dataType, value))

		if dataType == BT.absRelTimestamp:
			if isinstance(value, str):
				try:
					rel = int(value)
					# fallthrough
				except Exception as e:	# could happen if this is a string with an iso timestamp. Then try next test
					if DateUtils.fromAbsRelTimestamp(value) == 0.0:
						return Result.errorResult(dbg = f'format error in absRelTimestamp: {value}')
				# fallthrough
			elif not isinstance(value, int):
				return Result.errorResult(dbg = f'unsupported data type for absRelTimestamp')
			return Result(status = True, data = (dataType, value))		# int/long is ok

		if dataType in [ BT.string, BT.anyURI ] and isinstance(value, str):
			return Result(status = True, data = (dataType, value))

		if dataType in [ BT.list, BT.listNE ] and isinstance(value, list):
			if dataType == BT.listNE and len(value) == 0:
				return Result.errorResult(dbg = 'empty list is not allowed')
			if policy is not None and policy.ltype is not None:
				for each in value:
					if not (res := self._validateType(policy.ltype, each, convert = convert, policy = policy)).status:
						return res
			return Result(status = True, data = (dataType, value))

		if dataType == BT.dict and isinstance(value, dict):
			return Result(status = True, data = (dataType, value))
		
		if dataType == BT.boolean:
			if isinstance(value, bool):
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: bool')

		if dataType == BT.float:
			if isinstance(value, (float, int)):
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: float')

		if dataType == BT.integer:
			if isinstance(value, int):
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: integer')

		if dataType == BT.geoCoordinates and isinstance(value, dict):
			return Result(status = True, data = (dataType, value))
		
		if dataType == BT.duration:
			try:
				isodate.parse_duration(value)
			except Exception as e:
				return Result.errorResult(dbg = f'must be an ISO duration: {str(e)}')
			return Result(status = True, data = (dataType, value))
		
		if dataType == BT.any:
			return Result(status = True, data = (dataType, value))
		
		if dataType == BT.complex:
			if not policy:
				L.logErr(f'policy is missing for validation of complex attribute')
				return Result.errorResult(dbg = f'internal error: policy missing for validation')

			if isinstance(value, dict):
				typeName = policy.lTypeName if policy.type == BT.list else policy.typeName;
				for k, v in value.items():
					if not (p := self.getAttributePolicy(typeName, k)):
						return Result.errorResult(dbg = f'unknown or undefined attribute:{k} in complex type: {typeName}')
					if not (res := self._validateType(p.type, v, convert = convert, policy = p)).status:
						return res
			return Result(status = True, data = (dataType, value))

		return Result.errorResult(dbg = f'type mismatch or unknown; expected type: {str(dataType)}, value type: {type(value).__name__}')


