#
#	Validator.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Validation service and functions
#

from __future__ import annotations
from typing import Any, Dict, Tuple, Optional

from copy import deepcopy
import re
import isodate

from ..etc.Types import AttributePolicy, ResourceAttributePolicyDict, AttributePolicyDict, BasicType, Cardinality
from ..etc.Types import RequestOptionality, Announced, AttributePolicy
from ..etc.Types import JSON, FlexContainerAttributes, FlexContainerSpecializations
from ..etc.Types import Result, ResourceTypes
from ..etc import Utils, DateUtils
from ..helpers import TextTools
from ..resources.Resource import Resource
from ..services.Logging import Logging as L


# TODO AE Not defined yet: ExternalGroupID?
# TODO AE CSE Not defined yet: enableTimeCompensation
# TODO GRP: somecastEnable, somecastAlgorithm not defined yet (shortname)

attributePolicies:ResourceAttributePolicyDict = {}
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

	_scheduleRegex = re.compile('(^((\*\/)?([0-5]?[0-9])((\,|\-|\/)([0-5]?[0-9]))*|\*)\s+((\*\/)?([0-5]?[0-9])((\,|\-|\/)([0-5]?[0-9]))*|\*)\s+((\*\/)?((2[0-3]|1[0-9]|[0-9]|00))((\,|\-|\/)(2[0-3]|1[0-9]|[0-9]|00))*|\*)\s+((\*\/)?([1-9]|[12][0-9]|3[01])((\,|\-|\/)([1-9]|[12][0-9]|3[01]))*|\*)\s+((\*\/)?([1-9]|1[0-2])((\,|\-|\/)([1-9]|1[0-2]))*|\*)\s+((\*\/)?[0-6]((\,|\-|\/)[0-6])*|\*|00)\s+((\*\/)?(([2-9][0-9][0-9][0-9]))((\,|\-|\/)([2-9][0-9][0-9][0-9]))*|\*)\s*$)')
	"""	Compiled regular expression that matches a valid cron-like schedule: "second minute hour day month weekday year" """


	def __init__(self) -> None:
		L.isInfo and L.log('Validator initialized')


	def shutdown(self) -> bool:
		L.isInfo and L.log('Validator shut down')
		return True

	#########################################################################


	def	validateAttributes(self, resource:JSON, 
								 tpe:str, 
								 ty:Optional[ResourceTypes] = ResourceTypes.UNKNOWN, 
								 attributes:Optional[AttributePolicyDict] = None, 
								 create:Optional[bool] = True , 
								 isImported:Optional[bool] = False, 
								 createdInternally:Optional[bool] = False, 
								 isAnnounced:Optional[bool] = False) -> Result:
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
		pureResDict, _tpe, _ = Utils.pureResource(resource)

		tpe = _tpe if _tpe and _tpe != tpe else tpe 				# determine the real tpe

		# if tpe is not None and not tpe.startswith("m2m:"):
		# 	pureResDict = dct

		attributePolicies = attributes
		# If this is a flexContainer then add the additional attributePolicies.
		# We don't want to change the original attributes, so copy it before (only if we add new attributePolicies)

		if ty in [ ResourceTypes.FCNT, ResourceTypes.FCI ] and tpe:
			if (fca := flexContainerAttributes.get(tpe)) is not None:
				attributePolicies = deepcopy(attributePolicies)
				attributePolicies.update(fca)
			else:
				return Result.errorResult(dbg = L.logWarn(f'Unknown resource type: {tpe}'))

		# L.logDebug(attributePolicies.items())
		# L.logWarn(pureResDict)
		
		# Check that all attributes have been defined
		for attributeName in pureResDict.keys():
			if attributeName not in attributePolicies.keys():
				return Result.errorResult(dbg = L.logWarn(f'Unknown attribute: {attributeName} in resource: {tpe}'))

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
					
				if policyOptional == RequestOptionality.M:		# Not okay, this attribute is mandatory but absent
					return Result.errorResult(dbg = L.logWarn(f'Cannot find mandatory attribute: {attributeName}'))

				if attributeName in pureResDict:
					if policy.cardinality == Cardinality.CAR1: 	# but ignore CAR.car1N (which may be Null/None)
						return Result.errorResult(dbg = L.logWarn(f'Cannot delete a mandatory attribute: {attributeName}'))
					if policyOptional == RequestOptionality.NP: # present with any value or None/null? Then this is an error for NP
						return Result.errorResult(dbg = L.logWarn(f'Attribute: {attributeName} is NP for operation'))

				if policyOptional in [ RequestOptionality.NP, RequestOptionality.O ]:		# Okay that the attribute is not in the dict, since it is provided or optional
					continue
			else:
				if not createdInternally:
					if policyOptional == RequestOptionality.NP:
						return Result.errorResult(dbg = L.logWarn(f'Found non-provision attribute: {attributeName}'))

				# check the the announced cases
				if isAnnounced:
					if policy.announcement == Announced.NA:	# Not okay, attribute is not announced
						return Result.errorResult(dbg = L.logWarn(f'Found non-announced attribute: {attributeName}'))
					continue

				# Special handling for the ACP's pvs attribute
				if attributeName == 'pvs' and not (res := self.validatePvs(pureResDict)).status:
					return Result.errorResult(dbg = res.dbg)

			# Check whether the value is of the correct type
			if (res := self._validateType(policy.type, attributeValue, policy = policy)).status:
				# Still some further checks are necessary

				# Check list. May be empty or needs to contain at least one member
				if policy.cardinality == Cardinality.CAR1LN and len(attributeValue) == 0:
					return Result.errorResult(dbg = L.logWarn(f'List attribute must be non-empty: {attributeName}'))

				# Check list. May be empty or needs to contain at least one member
				# L.isWarn and L.logWarn(f'CAR: {policy.cardinality.name}: {attributeValue}')
				if policy.cardinality == Cardinality.CAR01L and attributeValue is not None and len(attributeValue) == 0:
					return Result.errorResult(dbg = L.logWarn(f'Optional list attribute must be non-empty: {attributeName}'))
				continue
		

			# fall-through means: not validated
			return Result.errorResult(dbg = L.logWarn(f'Attribute/value validation error: {attributeName}={str(attributeValue)} ({res.dbg})'))

		return Result.successResult()



	def validateAttribute(self, attribute:str, 
								value:Any, 
								attributeType:Optional[BasicType] = None, 
								rtype:Optional[ResourceTypes] = ResourceTypes.ALL) -> Result:
		""" Validate a single attribute. 
		
			Args:
				attribute: Name of the attribute to perform the check.
				value: Value to validate for the attribute.
				attributeType: If *attributeType* is set then that type is taken to perform the check, otherwise the attribute type is determined.
				rtype: Some attributes' validations depend on the resource type.
			Return:
				`Result` object. If successful then *data* contains the determined attribute and the converted value in a tuple.
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
			'rsc' : AttributePolicy(type = BasicType.integer,          cardinality =Cardinality.CAR1,  optionalCreate = RequestOptionality.M, optionalUpdate = RequestOptionality.M, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'rsp', lname = 'responseStatusCode', namespace = 'm2m', tpe = 'm2m:rsc'),
			'rqi' : AttributePolicy(type = BasicType.string,           cardinality =Cardinality.CAR1,  optionalCreate = RequestOptionality.M, optionalUpdate = RequestOptionality.M, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'rqi', lname = 'requestIdentifier', namespace = 'm2m', tpe = 'm2m:rqi'),
			'pc' : AttributePolicy(type = BasicType.dict,              cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'pc', lname = 'primitiveContent', namespace = 'm2m', tpe = 'm2m:pc'),
			'to' : AttributePolicy(type = BasicType.string,            cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'to', lname = 'to', namespace = 'm2m', tpe = 'm2m:to'),
			'fr' : AttributePolicy(type = BasicType.string,            cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'fr', lname = 'from', namespace = 'm2m', tpe = 'm2m:fr'),
			'ot' : AttributePolicy(type = BasicType.timestamp,         cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'ot', lname = 'originatingTimestamp', namespace = 'm2m', tpe = 'm2m:or'),
			'rset' : AttributePolicy(type = BasicType.absRelTimestamp, cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'rset', lname = 'resultExpirationTimestamp', namespace = 'm2m', tpe = 'm2m:rset'),
			'ec' : AttributePolicy(type = BasicType.positiveInteger,   cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'ec', lname = 'eventCategory', namespace = 'm2m', tpe = 'm2m:ec'),
			'cnst' : AttributePolicy(type = BasicType.positiveInteger, cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'cnst', lname = 'contentStatus', namespace = 'm2m', tpe = 'm2m:cnst'),
			'cnot' : AttributePolicy(type = BasicType.positiveInteger, cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'cnot', lname = 'contentOffset', namespace = 'm2m', tpe = 'm2m:cnot'),
			'ati' : AttributePolicy(type = BasicType.dict,             cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'ati', lname = 'assignedTokenIdentifiers', namespace = 'm2m', tpe = 'm2m:ati'),
			'tqf' : AttributePolicy(type = BasicType.dict,             cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'tqf', lname = 'tokenRequestInformation', namespace = 'm2m', tpe = 'm2m:tqf'),
			'asri' : AttributePolicy(type = BasicType.boolean,         cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'asri', lname = 'authorSignReqInfo', namespace = 'm2m', tpe = 'm2m:asri'),
			'rvi' : AttributePolicy(type = BasicType.string,           cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'rvi', lname = 'releaseVersionIndicator', namespace = 'm2m', tpe = 'm2m:rvi'),
			'vsi' : AttributePolicy(type = BasicType.string,           cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'vsi', lname = 'vendorInformation', namespace = 'm2m', tpe = 'm2m:vsi'),
		},
		# 'm2m:sgn' : {
		# 	'fr' : AttributePolicy(type=BasicType.string,            cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='fr', lname='from', namespace='m2m', tpe='m2m:fr'),
		# 	'to' : AttributePolicy(type=BasicType.string,            cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='to', lname='to', namespace='m2m', tpe='m2m:to'),
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
			return self.validateAttributes(obj, tpe = name, attributes=ap)
		
		return Result.successResult()


	#
	#	Additional validations.
	#

	def validatePvs(self, dct:JSON) -> Result:
		""" Validating special case for lists that are not allowed to be empty (pvs in ACP). """

		if (l :=len(dct['pvs'])) == 0:
			return Result.errorResult(dbg = L.logWarn('Attribute pvs must not be an empty list'))
		elif l > 1:
			return Result.errorResult(dbg = L.logWarn('Attribute pvs must contain only one item'))
		if not (acr := Utils.findXPath(dct, 'pvs/acr')):
			return Result.errorResult(dbg = L.logWarn('Attribute pvs/acr not found'))
		if not isinstance(acr, list):
			return Result.errorResult(dbg = L.logWarn('Attribute pvs/acr must be a list'))
		if len(acr) == 0:
			return Result.errorResult(dbg = L.logWarn('Attribute pvs/acr must not be an empty list'))
		return Result.successResult()


	# TODO allowed media type chars
	cnfRegex = re.compile(
		r'^[^:/]+/[^:/]+:[0-2]$'
		r'|^[^:/]+/[^:/]+:[0-2]$'	# TODO why twice?
		r'|^[^:/]+/[^:/]+:[0-2]:[0-5]$'
	)
	def validateCNF(self, value:str) -> Result:
		"""	Validate the contents of the *contentInfo* attribute. """
		if isinstance(value, str) and re.match(self.cnfRegex, value) is not None:
			return Result.successResult()
		return Result.errorResult(dbg = f'validation of cnf attribute failed: {value}')


	def validateCSICB(self, val:str, name:str) -> Result:
		"""	Validate the format of a CSE-ID in csi or cb attributes.
		"""
		# TODO Decide whether to correct this automatically, like in RemoteCSEManager._retrieveRemoteCSE()
		if not val:
			return Result.errorResult(dbg = L.logDebug(f"{name} is missing"))
		if not val.startswith('/'):
			return Result.errorResult(dbg = L.logDebug(f"{name} must start with '/': {val}"))
		return Result.successResult()


	def isExtraResourceAttribute(self, attr:str, resource:Resource) -> bool:
		"""	Check whether the resource attribute *attr* is neither a universal,
			common, or resource attribute, nor an internal attribute. 

			Args:
				attr: Short name of the attribute to check.
				resource: The `Resource` to check.	
			Return:
				his method returns *True* when the attribute is a custom attribute.
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


	def addAttributePolicy(self, rtype:ResourceTypes|str, attr:str, attrPolicy:AttributePolicy) -> None:
		"""	Add a new attribute policy for normal resources. 
		"""
		if (rtype, attr) in attributePolicies:
			L.logErr(f'Policy {(rtype, attr)} is already registered')
		attributePolicies[(rtype, attr)] = attrPolicy


	def getAttributePolicy(self, rtype:ResourceTypes|str, attr:str) -> AttributePolicy:
		"""	Return the attributePolicy for a resource type.
		"""
		# Search for the specific type first
		if (ap := attributePolicies.get((rtype, attr))):
			return ap

		# If it couldn't be found, look whether it has been defined for ALL
		if (ap := attributePolicies.get((ResourceTypes.ALL, attr))):
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

	def _validateType(self, dataType:BasicType, 
							value:Any, 
							convert:Optional[bool] = False, 
							policy:Optional[AttributePolicy] = None) -> Result:
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
			if dataType in [ BasicType.positiveInteger, 
							 BasicType.nonNegInteger, 
							 BasicType.unsignedInt, 
							 BasicType.unsignedLong, 
							 BasicType.integer, 
							 BasicType.enum ] and isinstance(value, str):
				try:
					value = int(value)
				except Exception as e:
					return Result.errorResult(dbg = str(e))
			elif dataType == BasicType.boolean and isinstance(value, str):	# "true"/"false"
				try:
					value = Utils.strToBool(value)
				except Exception as e:
					return Result.errorResult(dbg = str(e))
			elif dataType == BasicType.float and isinstance(value, str):
				try:
					value = float(value)
				except Exception as e:
					return Result.errorResult(dbg = str(e))

		# Check types and values

		if dataType == BasicType.positiveInteger:
			if isinstance(value, int):
				if value > 0:
					return Result(status = True, data = (dataType, value))
				return Result.errorResult(dbg = 'value must be > 0')
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: positive integer')
		
		if dataType == BasicType.enum:
			if isinstance(value, int):
				if policy is not None and len(policy.evalues) and value not in policy.evalues:
					return Result.errorResult(dbg = 'undefined enum value')
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: positive integer')

		if dataType == BasicType.nonNegInteger:
			if isinstance(value, int):
				if value >= 0:
					return Result(status = True, data = (dataType, value))
				return Result.errorResult(dbg = 'value must be >= 0')
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: non-negative integer')

		if dataType in [ BasicType.unsignedInt, BasicType.unsignedLong ]:
			if isinstance(value, int):
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: unsigned integer')

		if dataType == BasicType.timestamp and isinstance(value, str):
			if DateUtils.fromAbsRelTimestamp(value) == 0.0:
				return Result.errorResult(dbg = f'format error in timestamp: {value}')
			return Result(status = True, data = (dataType, value))

		if dataType == BasicType.absRelTimestamp:
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

		if dataType in [ BasicType.string, BasicType.anyURI ] and isinstance(value, str):
			return Result(status = True, data = (dataType, value))

		if dataType in [ BasicType.list, BasicType.listNE ] and isinstance(value, list):
			if dataType == BasicType.listNE and len(value) == 0:
				return Result.errorResult(dbg = 'empty list is not allowed')
			if policy is not None and policy.ltype is not None:
				for each in value:
					if not (res := self._validateType(policy.ltype, each, convert = convert, policy = policy)).status:
						return res
			return Result(status = True, data = (dataType, value))

		if dataType == BasicType.dict and isinstance(value, dict):
			return Result(status = True, data = (dataType, value))
		
		if dataType == BasicType.boolean:
			if isinstance(value, bool):
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: bool')

		if dataType == BasicType.float:
			if isinstance(value, (float, int)):
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: float')

		if dataType == BasicType.integer:
			if isinstance(value, int):
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__}. Expected: integer')

		if dataType == BasicType.geoCoordinates and isinstance(value, dict):
			return Result(status = True, data = (dataType, value))
		
		if dataType == BasicType.duration:
			try:
				isodate.parse_duration(value)
			except Exception as e:
				return Result.errorResult(dbg = f'must be an ISO duration: {str(e)}')
			return Result(status = True, data = (dataType, value))
		
		if dataType == BasicType.base64:
			if not TextTools.isBase64(value):
				return Result.errorResult(dbg = f'value is not base64-encoded')
			return Result(status = True, data = (dataType, value))
		
		if dataType == BasicType.schedule:
			if isinstance(value, str) and re.match(self._scheduleRegex, value):
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'invalid type: {type(value).__name__} or pattern {value}. Expected: cron-like schedule')

		if dataType == BasicType.any:
			return Result(status = True, data = (dataType, value))
		
		if dataType == BasicType.complex:
			if not policy:
				L.logErr(f'policy is missing for validation of complex attribute')
				return Result.errorResult(dbg = f'internal error: policy missing for validation')

			if isinstance(value, dict):
				typeName = policy.lTypeName if policy.type == BasicType.list else policy.typeName;
				for k, v in value.items():
					if not (p := self.getAttributePolicy(typeName, k)):
						return Result.errorResult(dbg = f'unknown or undefined attribute:{k} in complex type: {typeName}')
					if not (res := self._validateType(p.type, v, convert = convert, policy = p)).status:
						return res
				return Result(status = True, data = (dataType, value))
			return Result.errorResult(dbg = f'Expected complex type, found: {value}')

		return Result.errorResult(dbg = f'type mismatch or unknown; expected type: {str(dataType)}, value type: {type(value).__name__}')


