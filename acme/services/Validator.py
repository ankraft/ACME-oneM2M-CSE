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
from ..etc.ResponseStatusCodes import BAD_REQUEST, ResponseException, CONTENTS_UNACCEPTABLE
from ..etc.Utils import pureResource, strToBool
from ..helpers.TextTools import findXPath
from ..etc.DateUtils import fromAbsRelTimestamp
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

complexTypeAttributes:dict[str, list[str]] = {}
# TODO doc

class Validator(object):

	_scheduleRegex = re.compile('(^((\*\/)?([0-5]?[0-9])((\,|\-|\/)([0-5]?[0-9]))*|\*)\s+((\*\/)?([0-5]?[0-9])((\,|\-|\/)([0-5]?[0-9]))*|\*)\s+((\*\/)?((2[0-3]|1[0-9]|[0-9]|00))((\,|\-|\/)(2[0-3]|1[0-9]|[0-9]|00))*|\*)\s+((\*\/)?([1-9]|[12][0-9]|3[01])((\,|\-|\/)([1-9]|[12][0-9]|3[01]))*|\*)\s+((\*\/)?([1-9]|1[0-2])((\,|\-|\/)([1-9]|1[0-2]))*|\*)\s+((\*\/)?[0-6]((\,|\-|\/)[0-6])*|\*|00)\s+((\*\/)?(([2-9][0-9][0-9][0-9]))((\,|\-|\/)([2-9][0-9][0-9][0-9]))*|\*)\s*$)')
	"""	Compiled regular expression that matches a valid cron-like schedule: "second minute hour day month weekday year" """


	def __init__(self) -> None:
		L.isInfo and L.log('Validator initialized')


	def shutdown(self) -> bool:
		L.isInfo and L.log('Validator shut down')
		return True

	#########################################################################


	def validateResourceUpdate(self, resource:Resource, dct:JSON, doValidateAttributes:bool = False) -> None:
		"""	Validate a resource update dictionary. Besides of the attributes it also validates the resource type.

			Args:
				resource: The resource to validate the update request for.
				dct: The JSON dictionary of the update request.
				doValidateAttributes: Boolean indicating whether to validate the attributes.

			See Also:
				`validateAttributes`

			Return:
				None
		"""
		if resource.tpe not in dct and resource.ty not in [ResourceTypes.FCNTAnnc]:	# Don't check announced versions of announced FCNT
			raise CONTENTS_UNACCEPTABLE(L.logWarn(f"Update type doesn't match target (expected: {resource.tpe}, is: {list(dct.keys())[0]})"))
		# validate the attributes
		if doValidateAttributes:
			self.validateAttributes(dct, 
									resource.tpe, 
									resource.ty, 
									resource._attributes, 
									create = False, 
									createdInternally = resource.isCreatedInternally(), 
									isAnnounced = resource.isAnnounced())


	def	validateAttributes(self, resource:JSON, 
								 tpe:str, 
								 ty:Optional[ResourceTypes] = ResourceTypes.UNKNOWN, 
								 attributes:Optional[AttributePolicyDict] = None, 
								 create:Optional[bool] = True , 
								 isImported:Optional[bool] = False, 
								 createdInternally:Optional[bool] = False, 
								 isAnnounced:Optional[bool] = False) -> None:
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
		L.isDebug and L.logDebug('validating attributes')

		# Just return in case the resource instance is imported
		if isImported:
			return

		# No policies?
		if not attributes:
			L.logErr(f'no attribute policies: {resource}')
			return

		# Set an index into the policy dataclass, depending on the validation type
		optionalIndex = 2 if create else 3	# index to create or update
		if isAnnounced:
			optionalIndex = 5	# index to announced

		# Get the pure resource and the resource's tpe
		pureResDict, _tpe, _ = pureResource(resource)

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
				raise BAD_REQUEST(L.logWarn(f'unknown resource type: {tpe}'))

		# L.logDebug(attributePolicies.items())
		# L.logWarn(pureResDict)
		
		# Check that all attributes have been defined
		for attributeName in pureResDict.keys():
			if attributeName not in attributePolicies.keys():
				raise BAD_REQUEST(L.logWarn(f'unknown attribute: {attributeName} in resource: {tpe}'))

		for attributeName, policy in attributePolicies.items():
			if not policy:
				L.isWarn and L.logWarn(f'no attribute policy found for attribute: {attributeName}')
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
					raise BAD_REQUEST(L.logWarn(f'cannot find mandatory attribute: {attributeName}'))

				if attributeName in pureResDict:
					if policy.cardinality == Cardinality.CAR1: 	# but ignore CAR.car1N (which may be Null/None)
						raise BAD_REQUEST( L.logWarn(f'cannot delete a mandatory attribute: {attributeName}'))
					if policyOptional == RequestOptionality.NP: # present with any value or None/null? Then this is an error for NP
						raise BAD_REQUEST(L.logWarn(f'attribute: {attributeName} is NP for operation'))

				if policyOptional in [ RequestOptionality.NP, RequestOptionality.O ]:		# Okay that the attribute is not in the dict, since it is provided or optional
					continue
			else:
				if not createdInternally:
					if policyOptional == RequestOptionality.NP:
						raise BAD_REQUEST(L.logWarn(f'found non-provision attribute: {attributeName}'))

				# check the the announced cases
				if isAnnounced:
					if policy.announcement == Announced.NA:	# Not okay, attribute is not announced
						raise BAD_REQUEST(L.logWarn(f'found non-announced attribute: {attributeName}'))
					continue

				# Special handling for the ACP's pvs attribute
				if attributeName == 'pvs':
					self.validatePvs(pureResDict)

			# Check whether the value is of the correct type
			try:
				self._validateType(policy.type, attributeValue, policy = policy)
				# Still some further checks are necessary

				# Check list. May be empty or needs to contain at least one member
				if policy.cardinality == Cardinality.CAR1LN and len(attributeValue) == 0:
					raise BAD_REQUEST(L.logWarn(f'Mandatory list attribute must be non-empty: {attributeName}'))

				# Check list. May be empty or needs to contain at least one member
				# L.isWarn and L.logWarn(f'CAR: {policy.cardinality.name}: {attributeValue}')
				if policy.cardinality == Cardinality.CAR01L and attributeValue is not None and len(attributeValue) == 0:
					raise BAD_REQUEST(L.logWarn(f'Optional list attribute must be non-empty: {attributeName}'))
			except ResponseException as e:
				raise BAD_REQUEST(L.logWarn(f'Attribute/value validation error: {attributeName}={str(attributeValue)} ({e.dbg})'))


	def validateAttribute(self, attribute:str, 
								value:Any, 
								attributeType:Optional[BasicType] = None, 
								rtype:Optional[ResourceTypes] = ResourceTypes.ALL) -> Tuple[BasicType, Any]:
		""" Validate a single attribute. 
		
			Args:
				attribute: Name of the attribute to perform the check.
				value: Value to validate for the attribute.
				attributeType: If *attributeType* is set then that type is taken to perform the check, otherwise the attribute type is determined.
				rtype: Some attributes' validations depend on the resource type.
			Return:
				A tuple with determined data type and the converted value.
		"""
		if attributeType is not None:	# use the given attribute type instead of determining it
			return self._validateType(attributeType, value, True)
		if policy := self.getAttributePolicy(rtype, attribute):
			return self._validateType(policy.type, value, True, policy = policy)
		raise BAD_REQUEST(f'validation for attribute {attribute} not defined')


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



	def validatePrimitiveContent(self, pc:JSON) -> None:
		# None - pc is ok
		if pc is None:
			return
		
		# Check number of elements == 1
		if len(pc.keys()) != 1:	# TODO is this correct?
			raise BAD_REQUEST(f'primitive content shall contain exactly one element')
		
		name,obj = list(pc.items())[0]
		if ap := self.complexAttributePolicies.get(name):
			self.validateAttributes(obj, tpe = name, attributes=ap)
		

	#
	#	Additional validations.
	#

	def validatePvs(self, dct:JSON) -> None:
		""" Validating special case for lists that are not allowed to be empty (pvs in ACP). """

		if (l :=len(dct['pvs'])) == 0:
			raise BAD_REQUEST(L.logWarn('Attribute pvs must not be an empty list'))
		elif l > 1:
			raise BAD_REQUEST(L.logWarn('Attribute pvs must contain only one item'))
		if not (acr := findXPath(dct, 'pvs/acr')):
			raise BAD_REQUEST(L.logWarn('Attribute pvs/acr not found'))
		if not isinstance(acr, list):
			raise BAD_REQUEST(L.logWarn('Attribute pvs/acr must be a list'))
		if len(acr) == 0:
			raise BAD_REQUEST(L.logWarn('Attribute pvs/acr must not be an empty list'))


	# TODO allowed media type chars
	cnfRegex = re.compile(
		r'^[^:/]+/[^:/]+:[0-2]$'
		r'|^[^:/]+/[^:/]+:[0-2]$'	# TODO why twice?
		r'|^[^:/]+/[^:/]+:[0-2]:[0-5]$'
	)
	def validateCNF(self, value:str) -> None:
		"""	Validate the contents of the *contentInfo* attribute. 
		"""
		if isinstance(value, str) and re.match(self.cnfRegex, value) is not None:
			return
		raise BAD_REQUEST(f'validation of cnf attribute failed: {value}')
		# fall-through


	def validateCSICB(self, val:str, name:str) -> None:
		"""	Validate the format of a CSE-ID in csi or cb attributes.
		"""
		# TODO Decide whether to correct this automatically, like in RemoteCSEManager._retrieveRemoteCSE()
		if not val:
			raise BAD_REQUEST(L.logDebug(f"{name} is missing"))
		if not val.startswith('/'):
			raise BAD_REQUEST(L.logDebug(f"{name} must start with '/': {val}"))
		# fall-through


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

		# Collect a list of attributes for complex types
		if attrPolicy.ctype:
			if (attrs := complexTypeAttributes.get(attrPolicy.ctype)):
				attrs.append(attr)
			else:
				complexTypeAttributes[attrPolicy.ctype] = [ attr ]


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
	

	def getComplexTypeAttributePolicies(self, ctype:str) -> Optional[list[AttributePolicy]]:
		if (attrs := complexTypeAttributes.get(ctype)):
			return [ self.getAttributePolicy(ctype, attr) for attr in attrs ]
		L.logWarn(f'no policies found for complex type: {ctype}')
		return []


	def getAllAttributePolicies(self) -> ResourceAttributePolicyDict:
		return attributePolicies


	def clearAttributePolicies(self) -> None:
		"""	Clear the attribute policies.
		"""
		attributePolicies.clear()


	def getShortnameLongNameMappings(self) -> dict[str, str]:
		"""	Return the shortname to longname mappings.

			Return:
				Dictionary with the shortname to longname mappings.
		"""
		result = {}
		for a in attributePolicies.values():
			result[a.sname] = a.lname
		return result

	#
	#	Internals.
	#

	def _validateType(self, dataType:BasicType, 
							value:Any, 
							convert:Optional[bool] = False, 
							policy:Optional[AttributePolicy] = None) -> Tuple[BasicType, Any]:
		""" Check a value for its type. 
					
			Args:
				dataType: Required data type for the value to check against.
				value: Value to validate.
				convert: If the convert parameter is True then it is assumed that the value could be a stringified
					value and the method will attempt to convert the value to its target type; otherwise this
					is an error. 
			Return:
				Result. If the check is positive then Result.data is set to a tuple (the determined data type, the converted value).
		"""

		# Ignore None values
		if value is None:
			return (dataType, value)


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
					raise BAD_REQUEST(str(e))
			elif dataType == BasicType.boolean and isinstance(value, str):	# "true"/"false"
				try:
					value = strToBool(value)
				except Exception as e:
					raise BAD_REQUEST(str(e))
			elif dataType == BasicType.float and isinstance(value, str):
				try:
					value = float(value)
				except Exception as e:
					raise BAD_REQUEST(str(e))

		# Check types and values

		if dataType == BasicType.positiveInteger:
			if isinstance(value, int):
				if value > 0:
					return (dataType, value)
				raise BAD_REQUEST('value must be > 0')
			raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: positive integer')
		
		if dataType == BasicType.enum:
			if isinstance(value, int):
				if policy is not None and len(policy.evalues) and value not in policy.evalues:
					raise BAD_REQUEST('undefined enum value')
				return (dataType, value)
			raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: positive integer')

		if dataType == BasicType.nonNegInteger:
			if isinstance(value, int):
				if value >= 0:
					return (dataType, value)
				raise BAD_REQUEST('value must be >= 0')
			raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: non-negative integer')

		if dataType in [ BasicType.unsignedInt, BasicType.unsignedLong ]:
			if isinstance(value, int):
				return (dataType, value)
			raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: unsigned integer')

		if dataType == BasicType.timestamp and isinstance(value, str):
			if fromAbsRelTimestamp(value) == 0.0:
				raise BAD_REQUEST(f'format error in timestamp: {value}')
			return (dataType, value)

		if dataType == BasicType.absRelTimestamp:
			if isinstance(value, str):
				try:
					rel = int(value)
					# fallthrough
				except Exception as e:	# could happen if this is a string with an iso timestamp. Then try next test
					if fromAbsRelTimestamp(value) == 0.0:
						raise BAD_REQUEST(f'format error in absRelTimestamp: {value}')
				# fallthrough
			elif not isinstance(value, int):
				raise BAD_REQUEST(f'unsupported data type for absRelTimestamp')
			return (dataType, value)		# int/long is ok

		if dataType in [ BasicType.string, BasicType.anyURI ] and isinstance(value, str):
			return (dataType, value)

		if dataType in [ BasicType.list, BasicType.listNE ] and isinstance(value, list):
			if dataType == BasicType.listNE and len(value) == 0:
				raise BAD_REQUEST('empty list is not allowed')
			if policy is not None and policy.ltype is not None:
				for each in value:
					self._validateType(policy.ltype, each, convert = convert, policy = policy)
			return (dataType, value)

		if dataType == BasicType.dict and isinstance(value, dict):
			return (dataType, value)
		
		if dataType == BasicType.boolean:
			if isinstance(value, bool):
				return (dataType, value)
			raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: bool')

		if dataType == BasicType.float:
			if isinstance(value, (float, int)):
				return (dataType, value)
			raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: float')

		if dataType == BasicType.integer:
			if isinstance(value, int):
				return (dataType, value)
			raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: integer')

		if dataType == BasicType.geoCoordinates and isinstance(value, dict):
			return (dataType, value)
		
		if dataType == BasicType.duration:
			try:
				isodate.parse_duration(value)
			except Exception as e:
				raise BAD_REQUEST(f'must be an ISO duration: {str(e)}')
			return (dataType, value)
		
		if dataType == BasicType.base64:
			if not TextTools.isBase64(value):
				raise BAD_REQUEST(f'value is not base64-encoded')
			return (dataType, value)
		
		if dataType == BasicType.schedule:
			if isinstance(value, str) and re.match(self._scheduleRegex, value):
				return (dataType, value)
			raise BAD_REQUEST(f'invalid type: {type(value).__name__} or pattern {value}. Expected: cron-like schedule')

		if dataType == BasicType.any:
			return (dataType, value)
		
		if dataType == BasicType.complex:
			if not policy:
				raise BAD_REQUEST(L.logErr(f'internal error: policy is missing for validation of complex attribute'))

			if isinstance(value, dict):
				typeName = policy.lTypeName if policy.type == BasicType.list else policy.typeName;
				for k, v in value.items():
					if not (p := self.getAttributePolicy(typeName, k)):
						raise BAD_REQUEST(f'unknown or undefined attribute:{k} in complex type: {typeName}')
					# recursively validate a dictionary attribute
					self._validateType(p.type, v, convert = convert, policy = p)

				# Check that all mandatory attributes are present
				attributeNames = value.keys()
				for ap in self.getComplexTypeAttributePolicies(typeName):
					if Cardinality.isMandatory(ap.cardinality) and ap.sname not in attributeNames:
						raise BAD_REQUEST(f'attribute is mandatory for complex type : {typeName}.{ap.sname}')
				return (dataType, value)
			raise BAD_REQUEST(f'Expected complex type, found: {value}')

		raise BAD_REQUEST(f'type mismatch or unknown; expected type: {str(dataType)}, value type: {type(value).__name__}')


