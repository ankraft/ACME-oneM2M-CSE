#
#	Validator.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Validation service and functions. """

from __future__ import annotations
from typing import Any, Dict, Tuple, Optional

from copy import deepcopy
import re, json
import isodate

from ..etc.Types import AttributePolicy, ResourceAttributePolicyDict, AttributePolicyDict, BasicType, Cardinality
from ..etc.Types import RequestOptionality, Announced, AttributePolicy, ResultContentType
from ..etc.Types import JSON, FlexContainerAttributes, FlexContainerSpecializations, GeometryType, GeoSpatialFunctionType
from ..etc.Types import CSEType, ResourceTypes, Permission, Operation
from ..etc.ResponseStatusCodes import ResponseStatusCode, BAD_REQUEST, ResponseException, CONTENTS_UNACCEPTABLE
from ..etc.ACMEUtils import pureResource
from ..etc.Utils import strToBool
from ..helpers.TextTools import findXPath, soundsLike
from ..etc.DateUtils import fromAbsRelTimestamp
from ..helpers import TextTools
from ..resources.Resource import Resource
from ..resources.mgmtobjs.BAT import BatteryStatus
from ..runtime.Logging import Logging as L


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

	{ typeShortname : { sn : AttributePolicy } }
"""

flexContainerSpecializations:FlexContainerSpecializations = {}
"""	FlexContainer specialization aspects.

	{ typeShortname : cnd }
"""

complexTypeAttributes:dict[str, list[str]] = {}
"""	Mapping of complex types to their attributes. """

attributesComplexTypes:dict[str, list[str]] = {}
"""	Mapping of attributes to their complex types. """


# TODO make this more generic!
_valueNameMappings = {
	'acop': lambda v: '+'.join([ p.name for p in Permission.fromBitfield(int(v))]),
	'bts': lambda v: BatteryStatus(int(v)).name,
	'chty': lambda v: ResourceTypes.fullname(int(v)),
	'cst': lambda v: CSEType(int(v)).name,
	#'nct': lambda v: NotificationContentType(int(v)).name,
	#'net': lambda v: NotificationEventType(int(v)).name,
	'gmty': lambda v: GeometryType(int(v)).name,
	'gsf': lambda v: GeoSpatialFunctionType(int(v)).name,
	'op': lambda v: Operation(int(v)).name,
	'rcn': lambda v: ResultContentType(int(v)).name,
	'rsc': lambda v: ResponseStatusCode(int(v)).name,
	'srt': lambda v: ResourceTypes.fullname(int(v)),
	'ty': lambda v: ResourceTypes.fullname(int(v)),
}
"""	Mapping of attribute names to value mappings. """


class Validator(object):
	"""	Validator class. """

	_scheduleRegex = re.compile(r'(^((\*\/)?([0-5]?[0-9])((\,|\-|\/)([0-5]?[0-9]))*|\*)\s+((\*\/)?([0-5]?[0-9])((\,|\-|\/)([0-5]?[0-9]))*|\*)\s+((\*\/)?((2[0-3]|1[0-9]|[0-9]|00))((\,|\-|\/)(2[0-3]|1[0-9]|[0-9]|00))*|\*)\s+((\*\/)?([1-9]|[12][0-9]|3[01])((\,|\-|\/)([1-9]|[12][0-9]|3[01]))*|\*)\s+((\*\/)?([1-9]|1[0-2])((\,|\-|\/)([1-9]|1[0-2]))*|\*)\s+((\*\/)?[0-6]((\,|\-|\/)[0-6])*|\*|00)\s+((\*\/)?(([2-9][0-9][0-9][0-9]))((\,|\-|\/)([2-9][0-9][0-9][0-9]))*|\*)\s*$)')
	"""	Compiled regular expression that matches a valid cron-like schedule: "second minute hour day month weekday year" """


	def __init__(self) -> None:
		"""	Initialize the validator. """
		L.isInfo and L.log('Validator initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the validator. 
		
			Return:
				Always *True*.
		"""
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
		if resource.typeShortname not in dct and resource.ty != ResourceTypes.FCNTAnnc:	# Don't check announced versions of announced FCNT
			raise CONTENTS_UNACCEPTABLE(L.logWarn(f"Update type doesn't match target (expected: {resource.typeShortname}, is: {list(dct.keys())[0]})"))
		# validate the attributes
		if doValidateAttributes:
			self.validateAttributes(dct, 
									resource.typeShortname, 
									resource.ty, 
									resource._attributes, 
									create = False, 
									createdInternally = resource.isCreatedInternally(), 
									isAnnounced = resource.isAnnounced())


	def	validateAttributes(self, resource:JSON, 
								 typeShortname:str, 
								 ty:Optional[ResourceTypes] = ResourceTypes.UNKNOWN, 
								 attributes:Optional[AttributePolicyDict] = None, 
								 create:Optional[bool] = True , 
								 isImported:Optional[bool] = False, 
								 createdInternally:Optional[bool] = False, 
								 isAnnounced:Optional[bool] = False) -> None:
		""" Validate a resources' attributes for types etc.

			Args:
				resource: dictionary to check
				typeShortname: The resource's resource type name
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

		# Get the pure resource and the resource's typeShortname
		pureResDict, _typeShortname, _ = pureResource(resource)

		typeShortname = _typeShortname if _typeShortname and _typeShortname != typeShortname else typeShortname 				# determine the real typeShortname

		# if typeShortname is not None and not typeShortname.startswith("m2m:"):
		# 	pureResDict = dct

		attributePolicies = attributes
		# If this is a flexContainer then add the additional attributePolicies.
		# We don't want to change the original attributes, so copy it before (only if we add new attributePolicies)

		if ty in ( ResourceTypes.FCNT, ResourceTypes.FCI ) and typeShortname:
			if (fca := flexContainerAttributes.get(typeShortname)) is not None:
				attributePolicies = deepcopy(attributePolicies)
				attributePolicies.update(fca)
			else:
				raise BAD_REQUEST(L.logWarn(f'unknown resource type: {typeShortname}'))

		# L.logDebug(attributePolicies.items())
		# L.logWarn(pureResDict)
		
		# Check that all attributes have been defined
		for attributeName in pureResDict.keys():
			if attributeName not in attributePolicies.keys():
				raise BAD_REQUEST(L.logWarn(f'unknown attribute: {attributeName} in resource: {typeShortname}'))

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
					if policy.cardinality in (Cardinality.CAR1, Cardinality.CAR1LN): 	# but ignore CAR.car1N or CAR1LN (which may be Null/None)
						raise BAD_REQUEST( L.logWarn(f'cannot delete a mandatory attribute: {attributeName}'))
					if policyOptional == RequestOptionality.NP: # present with any value or None/null? Then this is an error for NP
						raise BAD_REQUEST(L.logWarn(f'attribute: {attributeName} is NP for operation'))

				if policyOptional in ( RequestOptionality.NP, RequestOptionality.O ):		# Okay that the attribute is not in the dict, since it is provided or optional
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
		raise BAD_REQUEST(f'validation for attribute {attribute} not defined for resource type: {rtype}')


	#
	#	Validate complex types
	#

	# TODO move this later to the attributePolicies file in init/ directory. Perhaps something along
	# 		"name" : [ "attribute1", "attribute", ...]


	complexAttributePolicies:Dict[str, AttributePolicyDict] = {
		# Response
		'rsp' :	{
			'rsc' : AttributePolicy(type = BasicType.integer,          cardinality =Cardinality.CAR1,  optionalCreate = RequestOptionality.M, optionalUpdate = RequestOptionality.M, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'rsp', lname = 'responseStatusCode', namespace = 'm2m', typeShortname = 'm2m:rsc'),
			'rqi' : AttributePolicy(type = BasicType.string,           cardinality =Cardinality.CAR1,  optionalCreate = RequestOptionality.M, optionalUpdate = RequestOptionality.M, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'rqi', lname = 'requestIdentifier', namespace = 'm2m', typeShortname = 'm2m:rqi'),
			'pc' : AttributePolicy(type = BasicType.dict,              cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'pc', lname = 'primitiveContent', namespace = 'm2m', typeShortname = 'm2m:pc'),
			'to' : AttributePolicy(type = BasicType.string,            cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'to', lname = 'to', namespace = 'm2m', typeShortname = 'm2m:to'),
			'fr' : AttributePolicy(type = BasicType.ID,			       cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'fr', lname = 'from', namespace = 'm2m', typeShortname = 'm2m:fr'),
			'ot' : AttributePolicy(type = BasicType.timestamp,         cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'ot', lname = 'originatingTimestamp', namespace = 'm2m', typeShortname = 'm2m:or'),
			'rset' : AttributePolicy(type = BasicType.absRelTimestamp, cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'rset', lname = 'resultExpirationTimestamp', namespace = 'm2m', typeShortname = 'm2m:rset'),
			'ec' : AttributePolicy(type = BasicType.positiveInteger,   cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'ec', lname = 'eventCategory', namespace = 'm2m', typeShortname = 'm2m:ec'),
			'cnst' : AttributePolicy(type = BasicType.positiveInteger, cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'cnst', lname = 'contentStatus', namespace = 'm2m', typeShortname = 'm2m:cnst'),
			'cnot' : AttributePolicy(type = BasicType.positiveInteger, cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'cnot', lname = 'contentOffset', namespace = 'm2m', typeShortname = 'm2m:cnot'),
			'ati' : AttributePolicy(type = BasicType.dict,             cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'ati', lname = 'assignedTokenIdentifiers', namespace = 'm2m', typeShortname = 'm2m:ati'),
			'tqf' : AttributePolicy(type = BasicType.dict,             cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'tqf', lname = 'tokenRequestInformation', namespace = 'm2m', typeShortname = 'm2m:tqf'),
			'asri' : AttributePolicy(type = BasicType.boolean,         cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'asri', lname = 'authorSignReqInfo', namespace = 'm2m', typeShortname = 'm2m:asri'),
			'rvi' : AttributePolicy(type = BasicType.string,           cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'rvi', lname = 'releaseVersionIndicator', namespace = 'm2m', typeShortname = 'm2m:rvi'),
			'vsi' : AttributePolicy(type = BasicType.string,           cardinality =Cardinality.CAR01, optionalCreate = RequestOptionality.O, optionalUpdate = RequestOptionality.O, optionalDiscovery = RequestOptionality.O, announcement = Announced.NA, sname = 'vsi', lname = 'vendorInformation', namespace = 'm2m', typeShortname = 'm2m:vsi'),
		},
		# 'm2m:sgn' : {
		# 	'fr' : AttributePolicy(type=BasicType.string,            cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='fr', lname='from', namespace='m2m', typeShortname='m2m:fr'),
		# 	'to' : AttributePolicy(type=BasicType.string,            cardinality=CAR.CAR01, optionalCreate=RO.O, optionalUpdate=RO.O, optionalDiscovery=RO.O, announcement=AN.NA, sname='to', lname='to', namespace='m2m', typeShortname='m2m:to'),
		# }

	}
	"""	Some complex attribute policies. 
	
		Todo:
			- move this to the attributePolicies file in init/ directory.
	"""


	def validatePrimitiveContent(self, pc:JSON) -> None:
		""" Validate the primitive content.
		
			Args:
				pc: The primitive content to validate.
		"""
		# None - pc is ok
		if pc is None:
			return
		
		# Check number of elements == 1
		if len(pc.keys()) != 1:	# TODO is this correct?
			raise BAD_REQUEST(f'primitive content shall contain exactly one element')
		
		name,obj = list(pc.items())[0]
		if ap := self.complexAttributePolicies.get(name):
			self.validateAttributes(obj, typeShortname = name, attributes=ap)
		

	#
	#	Additional validations.
	#

	def validatePvs(self, dct:JSON) -> None:
		""" Validating special case for lists that are not allowed to be empty (pvs in ACP). """

		match len(dct['pvs']):
			case 0:
				raise BAD_REQUEST(L.logWarn('Attribute pvs must not be an empty list'))
			case l if l > 1:
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
	"""	Compiled regular expression that matches a valid contentInfo string. """

	def validateCNF(self, value:str) -> None:
		"""	Validate the contents of the *contentInfo* attribute. 

			Args:
				value: The value to validate.
		"""
		if isinstance(value, str) and re.match(self.cnfRegex, value) is not None:
			return
		raise BAD_REQUEST(f'validation of cnf attribute failed: {value}')
		# fall-through


	def validateCSICB(self, val:str, name:str) -> None:
		"""	Validate the format of a CSE-ID in csi or cb attributes.

			Args:
				val: The value to validate.
				name: The name of the attribute.
		"""
		# TODO Decide whether to correct this automatically, like in RemoteCSEManager._retrieveRemoteCSE()
		if not val:
			raise BAD_REQUEST(L.logDebug(f"{name} is missing"))
		if not val.startswith('/'):
			raise BAD_REQUEST(L.logDebug(f"{name} must start with '/': {val}"))
		# fall-through


	def validateGeoPoint(self, geo:dict) -> bool:
		""" Validate a GeoJSON point. A point is a list of two or three floats.

			Args:
				geo: GeoJSON point.
			
			Return:
				Boolean, indicating whether the point is valid.
		"""
		if not isinstance(geo, list) or 2 > len(geo) > 3:
			return False
		for g in geo:
			if not isinstance(g, float):
				return False
		return True


	def validateGeoLinePolygon(self, geo:dict, isPolygon:Optional[bool] = False) -> bool:
		""" Validate a GeoJSON line or polygon. 
			A line or polygon is a list of lists of two or three floats.

			Args:
				geo: GeoJSON string line or polygon.
				isPolygon: Boolean, indicating whether the coordinates describe a polygon.
			
			Return:
				Boolean, indicating whether the line or polygon is valid.
		"""
		if not isinstance(geo, list) or len(geo) < 2:
			return False
		for g in geo:
			if not self.validateGeoPoint(g):
				return False
		if isPolygon and geo[0] != geo[-1]:
			return False
		return True


	def validateGeoMultiLinePolygon(self, geo:dict, isPolygon:Optional[bool] = False) -> bool:
		""" Validate a GeoJSON multi line or polygon. 
			A line or polygon is a list of list of lists of two or three floats.

			Args:
				geo: GeoJSON string multi line or polygon.
				isPolygon: Boolean, indicating whether the coordinates describe a polygon.
	
			Return:
				Boolean, indicating whether the line or polygon is valid.
		"""
		if not isinstance(geo, list):
			return False
		
		for g in geo:
			if not isinstance(g, list) or len(g) < 2:
				return False
			if not self.validateGeoLinePolygon(g, isPolygon):
				return False
		return True


	def validateGeoLocation(self, loc:dict) -> dict:
		""" Validate a GeoJSON location. A location is a dictionary with a type and coordinates.

			Args:
				loc: GeoJSON location.
			
			Return:
				The validated location dictionary.
			
			Raises:
				BAD_REQUEST: If the location definition is invalid.
		"""
		crd = json.loads(loc.get('crd')) # was validated before
		match loc.get('typ'):
			case GeometryType.Point:
				if not self.validateGeoPoint(crd):
					raise BAD_REQUEST(L.logWarn(f'Invalid GeoJSON point: {crd}'))
			case GeometryType.LineString:	
				if not self.validateGeoLinePolygon(crd):
					raise BAD_REQUEST(L.logWarn(f'Invalid GeoJSON LineString: {crd}'))
			case GeometryType.Polygon:
				if not self.validateGeoLinePolygon(crd, True):
					raise BAD_REQUEST(L.logWarn(f'Invalid GeoJSON Polygon: {crd}'))
			case GeometryType.MultiPoint:
				for p in crd:
					if not self.validateGeoPoint(p):
						raise BAD_REQUEST(L.logWarn(f'Invalid GeoJSON MultiPoint: {crd}'))
			case GeometryType.MultiLineString:
				if not self.validateGeoMultiLinePolygon(crd):
					raise BAD_REQUEST(L.logWarn(f'Invalid GeoJSON MultiLineString: {crd}'))
			case GeometryType.MultiPolygon:
				if not self.validateGeoMultiLinePolygon(crd, True):
					raise BAD_REQUEST(L.logWarn(f'Invalid GeoJSON MultiPolygon: {crd}'))
		return crd


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
		if not (policiesForTypeShortname := flexContainerAttributes.get(policy.typeShortname)):
			defsForTypeShortname = { policy.typeShortname : { policy.sname : policy } }					# No policy for TPtypeShortnameE yes, so create it
		else:
			policiesForTypeShortname[policy.sname] = policy									# Add/replace the policy for sname
			defsForTypeShortname = { policy.typeShortname : policiesForTypeShortname }				
		return self.updateFlexContainerAttributes(defsForTypeShortname)


	def getFlexContainerAttributesFor(self, typeShortname:str) -> AttributePolicyDict:
		""" Return the attribute policies for a flexContainer specialization.
		
			Args:
				typeShortname: String, domain and short name of the flexContainer specialization.
			Return:
				Dictictionary of additional attributes for a flexCOntainer type or None.
		 """
		return flexContainerAttributes.get(typeShortname)
	

	def clearFlexContainerAttributes(self) -> None:
		"""	Clear the flexContainer attributes.
		"""
		flexContainerAttributes.clear()


	def addFlexContainerSpecialization(self, typeShortname:str, cnd:str, lname:str) -> bool:
		"""	Add flexContainer specialization information to the internal dictionary.
		
			Args:
				typeShortname: String, domain and short name of the flexContainer specialization.
				cnd: String, the containerDefinition of the flexContainer specialization.
				lname: String, the long name of the flexContainer specialization.
			Return:
				Boolean, indicating whether a specialization was added successfully. 

		"""
		if not typeShortname in flexContainerSpecializations:
			flexContainerSpecializations[typeShortname] = (cnd, lname)
			return True
		return False


	def getFlexContainerSpecialization(self, typeShortname:str) -> Tuple[str, str]:
		"""	Return the availale data for a flexContainer specialization.
		
			Args:
				typeShortname: String, domain and short name of the flexContainer specialization.
			Return:
				Tuple with the flexContainer specialization data (or None if none exists). The tuple contains the containerDefinition and the long name.
		"""
		return flexContainerSpecializations.get(typeShortname)

	
	def hasFlexContainerContainerDefinition(self, cnd:str) -> bool:
		"""	Test whether a flexContainer specialization with a containerDefinition exists.
				
			Args:
				cnd: String, containerDefinition
			Return:
				Boolean, indicating existens.

		"""
		return any(( each for each in flexContainerSpecializations.values() if each[0] == cnd ))
	

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

			if (ctypes := attributesComplexTypes.get(attr)):
				ctypes.append(attrPolicy.ctype)
			else:
				attributesComplexTypes[attr] = [ attrPolicy.ctype ]


	def getAttributePolicy(self, rtype:ResourceTypes|str, attr:str) -> AttributePolicy:
		"""	Return the attributePolicy for a resource type.

			Args:
				rtype: Resource type.
				attr: Attribute name.
			
			Return:
				AttributePolicy or None.
		"""
		# Search for the specific type first
		if (ap := attributePolicies.get((rtype, attr))):
			return ap

		# If it couldn't be found, look whether it has been defined for ALL
		if (ap := attributePolicies.get((ResourceTypes.ALL, attr))):
			return ap
		
		# TODO look for other types, requests, filter...
		return None
	

	def getAttributePoliciesByName(self, attr:str) -> Optional[list[AttributePolicy]]:
		"""	Return the attribute policies for an attribute name.

			Args:
				attr: Attribute name.
			
			Return:
				List of AttributePolicy or None.
		"""
		result = { }
		keys = attributePolicies.keys()
		_attrlower = attr.lower()

		# First search for the specific attribute name
		for each in keys:
			s = each[1]
			if s == _attrlower:
				result[s] = attributePolicies[each]
				break

		# If it couldn't be found, search for similar full attribute names
		if not result:
			for each in keys:
				s = each[1]
				v = attributePolicies[each]
				if soundsLike(_attrlower, v.lname, 99):
					if s not in result:
						result[s] = v
		
			# If it couldn't be found, search for parts of the attribute name
			for each in keys:
				s = each[1]
				v = attributePolicies[each]
				if _attrlower in v.lname.lower():
					if s not in result:
						result[s] = v


		return [ each for each in result.values() ]
	

	def getComplexTypeAttributePolicies(self, ctype:str) -> Optional[list[AttributePolicy]]:
		"""	Return the attribute policies for a complex type.

			Args:
				ctype: Complex type name.
			
			Return:
				List of AttributePolicy or None.
		"""
		if (attrs := complexTypeAttributes.get(ctype)):
			return [ self.getAttributePolicy(ctype, attr) for attr in attrs ]
		L.logWarn(f'no policies found for complex type: {ctype}')
		return []


	def getAllAttributePolicies(self) -> ResourceAttributePolicyDict:
		"""	Return all attribute policies.

			Return:
				Dictionary with all attribute policies.
		"""
		return attributePolicies


	def clearAttributePolicies(self) -> None:
		"""	Clear the attribute policies.
		"""
		attributePolicies.clear()


	def getShortnameLongNameMapping(self) -> dict[str, str]:
		"""	Return the shortname to longname mappings.

			Return:
				Dictionary with the shortname to longname mappings.
		"""
		result = {}
		for a in attributePolicies.values():
			result[a.sname] = a.lname
		return result


	def getAttributeValueName(self, attr:str, value:int, rtype:Optional[ResourceTypes] = None) -> str:
		"""	Return the name of an attribute value. This is usually used for
			enumerations, where the value is a number and the name is a string.

			This method is mainly used for the interpretation of enumeration values in the UIs.

			Args:
				attr: Attribute name.
				value: Attribute value.	
			
			Return:
				String, name of the attribute value.
		"""
		try:
			if attr in _valueNameMappings:
				return _valueNameMappings[attr](value) # type: ignore [no-untyped-call]
			from ..runtime import CSE
			return CSE.validator.getEnumInterpretation(rtype, attr, value)
		except Exception as e:
			return str(e)


	def getEnumInterpretation(self, rtype: ResourceTypes, attr:str, value:int) -> str:
		"""	Return the interpretation of an enumeration.

			Args:
				rtype: Resource type. May be None.
				attr: Attribute name.
				value: Enumeration value.
			
			Return:
				String, interpretation of the enumeration, or the value itself if no interpretation is available.
		"""
		if rtype is not None:
			if (policy := self.getAttributePolicy(rtype, attr)) and policy.evalues:
				return policy.evalues.get(int(value), str(value))

		if (ctype := attributesComplexTypes.get(attr)):
			if (policy := self.getAttributePolicy(ctype[0], attr)) and policy.evalues:	# just any policy for the complex type
				return policy.evalues.get(int(value), str(value))
		return ''
		return str(value)


	def getAttributeValueRepresentation(self, attr:str, resourceType:ResourceTypes) -> str:
		"""	Return the representation of an attribute value. This is usually used for
			the representation of an attribute where the value is not known yet.

			Args:
				attr: Attribute name.
				resourceType: Type of the attribute's resource.
				
			Return:
				String, representation of the attribute value. This might be a JSON representation of the value.
		"""

		def basicTypeDefaultValue(typ:BasicType, 
								  policy:Optional[AttributePolicy] = None, 
								  level:Optional[int] = 0) -> str:
			"""	Return a default value for a basic type.
			
				Args:
					typ: Basic type.
					policy: Attribute policy.
					level: Indentation level.
					
				Return:
					String, default value for the basic type.
			"""

			match typ:
				case BasicType.string:
					return '<string>'
				case BasicType.ID:
					return '<ID>'
				case BasicType.anyURI:
					return '<uri>'
				case BasicType.ncname:
					return '<NCname>'
				case BasicType.imsi:
					return '<imsi>'
				case BasicType.iccid:
					return '<iccid>'
				case BasicType.base64:
					return '<base64 encoded string>'
				case BasicType.positiveInteger:
					return '<positiveInteger>'
				case BasicType.nonNegInteger:
					return '<nonNegativeInteger>'
				case BasicType.unsignedInt:
					return '<unsigned integer>'
				case BasicType.unsignedLong:
					return '<unsigned long>'
				case BasicType.integer:
					return '<integer>'
				case BasicType.float:
					return '<float>'
				case BasicType.boolean:
					return '<boolean true|false>'
				case BasicType.timestamp:
					return '<ISO 8601 timestamp>'
				case BasicType.absRelTimestamp:
					return '<ISO 8601 timestamp or integer>'
				case BasicType.duration:
					return '<ISO 8601 duration>'
				case BasicType.schedule:
					return '<schedule 7-digits cron-like>'
				case BasicType.geoJsonCoordinate:
					return '<GeoJsonCoordinate>'
				case BasicType.list | BasicType.listNE:
					if policy:
						if policy.ltype == BasicType.complex:
							_result = '[ {\n'
							for a in self.getComplexTypeAttributePolicies(policy.lTypeName):
								_result += f'        //{" "*4*(level+1)} "{a.sname}": {basicTypeDefaultValue(a.type, a, level+1)}\n'
							_result += f'        //{" "*4*(level+1)} }} ]'
							return _result

						return f'[ {basicTypeDefaultValue(policy.ltype, policy, level+1)} ]'
					return f'[ {policy.ltype} ]'
				
				case BasicType.enum:
					if policy:
						_enums = [ f'{k}:{v}' for k,v in policy.evalues.items()]
						return f'<enum {policy.etype} {", ".join(_enums)}>'
					return '""'
				
				case BasicType.complex:
					if policy:
						_result = '{\n'
						for a in self.getComplexTypeAttributePolicies(policy.typeName):
							_result += f'        //{" "*4*(level+1)} "{a.sname}": {basicTypeDefaultValue(a.type, a, level+1)}\n'
						_result += f'        //{" "*4*(level+1)} }}'
						return _result
					return '{ ... }'
				case _:
					return f'"{typ}"'

		_policy = self.getAttributePolicy(resourceType, attr)
		return basicTypeDefaultValue(_policy.type, _policy)


	#
	#	Internals.
	#

	_ncNameDisallowedChars = (	'!', '"', '#', '$', '%', '&', '\'', '(', ')', 
						   		'*', '+', ',', '/', ':', ';', '<', '=', '>', 
								'?', '@', '[', ']', '^', '´' , '`', '{', '|', '}', '~' )
	"""	Disallowed characters in NCName. """

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
				Result. If the check is positive then a tuple is returned: (the determined data type, the converted value).
		"""

		# Ignore None values
		if value is None:
			return (dataType, value)


		# convert some types if necessary
		if convert:
			if isinstance(value, str):
				try:
					match dataType:
						case BasicType.positiveInteger |\
							 BasicType.nonNegInteger |\
							 BasicType.unsignedInt |\
							 BasicType.unsignedLong |\
							 BasicType.integer |\
							 BasicType.enum:
							value = int(value)

						case BasicType.boolean:
							value = strToBool(value)

						case BasicType.float:
							value = float(value)

				except Exception as e:
					raise BAD_REQUEST(str(e))

		# Check types and values

		match dataType:
			case BasicType.positiveInteger:
				if isinstance(value, int) and value > 0:
					return (dataType, value)
				raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: positive integer')

			case BasicType.enum:
				if isinstance(value, int):
					if policy is not None and len(policy.evalues) and value not in policy.evalues:
						raise BAD_REQUEST('undefined enum value')
					return (dataType, value)
				raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: integer')
			
			case BasicType.nonNegInteger:
				if isinstance(value, int) and value >= 0:
					return (dataType, value)
				raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: non-negative integer')
			
			case BasicType.unsignedInt | BasicType.unsignedLong:
				if isinstance(value, int):
					return (dataType, value)
				raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: unsigned integer')

			case BasicType.timestamp if isinstance(value, str):
				if fromAbsRelTimestamp(value) == 0.0:
					raise BAD_REQUEST(f'format error in timestamp: {value}')
				return (dataType, value)
		
			case BasicType.absRelTimestamp:
				match value:
					case str():
						try:
							int(value)
							# fallthrough
						except Exception as e:	# could happen if this is a string with an iso timestamp. Then try next test
							if fromAbsRelTimestamp(value) == 0.0:
								raise BAD_REQUEST(f'format error in absRelTimestamp: {value}')
						# fallthrough
					case int():
						pass
						# fallthrough
					case _:
						raise BAD_REQUEST(f'unsupported data type for absRelTimestamp')
				return (dataType, value)		# int/long is ok

			case BasicType.string | BasicType.anyURI if isinstance(value, str):
				return (dataType, value)

			case BasicType.ID if isinstance(value, str):	# TODO check for valid resourceID
				return (dataType, value)
			
			case BasicType.ncname if isinstance(value, str):
				if len(value) == 0 or value[0].isdigit() or value[0] in ('-', '.'):
					raise BAD_REQUEST(f'invalid NCName: {value} (must not start with a digit, "-", or ".")')
				for v in value:
					if v.isspace():
						raise BAD_REQUEST(f'invalid NCName: {value} (must not contain whitespace)')
					if v in self._ncNameDisallowedChars:
						raise BAD_REQUEST(f'invalid NCName: {value} (must not contain any of {",".join(self._ncNameDisallowedChars)})')
				return (dataType, value)

			case BasicType.list | BasicType.listNE if isinstance(value, list):
				if dataType == BasicType.listNE and len(value) == 0:
					raise BAD_REQUEST('empty list is not allowed')
				if policy is not None and policy.ltype is not None:
					for each in value:
						self._validateType(policy.ltype, each, convert = convert, policy = policy)
				return (dataType, value)

			case BasicType.complex:
				# Check complex types
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

			case BasicType.dict if isinstance(value, dict):
				return (dataType, value)

			case BasicType.boolean:
				if isinstance(value, bool):
					return (dataType, value)
				raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: bool')

			case BasicType.integer:			
				if isinstance(value, int):
					return (dataType, value)
				raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: integer')
			
			case BasicType.float:
				if isinstance(value, (float, int)):
					return (dataType, value)
				raise BAD_REQUEST(f'invalid type: {type(value).__name__}. Expected: float')

			case BasicType.geoJsonCoordinate if isinstance(value, str):					
				try:
					geo = json.loads(value)
				except Exception as e:
					raise BAD_REQUEST(f'Invalid geoJsonCoordinate: {str(e)}')
				if self.validateGeoPoint(geo) or self.validateGeoLinePolygon(geo) or self.validateGeoMultiLinePolygon(geo):
					return (dataType, geo)
				raise BAD_REQUEST(f'Invalid geoJsonCoordinate: {value}')

			case BasicType.duration:
				try:
					isodate.parse_duration(value)
				except Exception as e:
					raise BAD_REQUEST(f'must be an ISO duration (e.g. "PT2S"): {str(e)}')
				return (dataType, value)

			case BasicType.base64:
				if not TextTools.isBase64(value):
					raise BAD_REQUEST(f'value is not base64-encoded')
				return (dataType, value)

			case BasicType.schedule:
				if isinstance(value, str) and re.match(self._scheduleRegex, value):
					return (dataType, value)
				raise BAD_REQUEST(f'invalid type: {type(value).__name__} or pattern {value}. Expected: cron-like schedule')

			case BasicType.imsi if isinstance(value, str):
				# TODO check for valid IMSI
				return (dataType, value)

			case BasicType.iccid if isinstance(value, str):
				# TODO check for valid ICCID
				return (dataType, value)
		
			case BasicType.ipv4Address if isinstance(value, str):
				# TODO check for valid IPv4 address
				return (dataType, value)
			
			case BasicType.ipv6Address if isinstance(value, str):
				# TODO check for valid IPv6 address
				return (dataType, value)
			
			case BasicType.jsonLike if isinstance(value, (str, int, float, bool, dict, list)):
				return (dataType, value)

			case BasicType.any:
				return (dataType, value)

		raise BAD_REQUEST(f'type mismatch or unknown; expected type: {str(dataType)}, value type: {type(value).__name__}')


