#
#	Types.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

"""	Various CSE and oneM2M types.
"""

from __future__ import annotations

from dataclasses import dataclass, field, astuple
from typing import Tuple, cast, Dict, Any, List, Union, Sequence, Callable, Optional
from enum import IntEnum,  auto
from http import HTTPStatus
from collections import namedtuple


class ACMEIntEnum(IntEnum):
	""" A base class for many oneM2M related enum types in ACME. It provides additional halper
		methods to simplify working with *IntEnum* classes.
	"""

	@classmethod
	def has(cls, value:int|str|List[int|str]|Tuple[int|str]) -> bool:
		"""	Check whether the enum type has an entry with
			either the given int value or string name. 

			Args:
				value: *value* can also be a tuple of values to test. 
					In this case, all the values in the tuple must exist.
			Return:
				*True* if the value exists.
		"""

		def _check(value:int|str) -> bool:
			if isinstance(value, int):
				return value in cls.__members__.values()
			else:
				return value in cls.__members__

		if isinstance(value, list):	# Checks if list
			for v in cast(list, value):
				if not _check(v):
					return False
			return True

		if isinstance(value, tuple):	# Checks if tuple
			for v in cast(tuple, value):
				if not _check(v):
					return False
			return True

		return _check(value)


	@classmethod
	def to(cls, name:str|Tuple[str], insensitive:Optional[bool]=False) -> Any:
		# TODO docu
		
		def _to(name:str) -> Any:
			try:
				if insensitive:
					_n = name.lower()
					return next(v for n,v in cls.__members__.items() if n.lower() == _n)	# type: ignore
				return next(v for n,v in cls.__members__.items() if n == name)	# type: ignore
			except StopIteration:
				return None

		if isinstance(name, tuple):
			result = []
			for n in name:
				if not (t := _to(n)):
					return None			# Early return
				result.append(t)
			return result
			
		return _to(cast(str, name))


	def __str__(self) -> str:
		return self.name


	def __repr__(self) -> str:
		return self.__str__()

#
#	Resource Types
#

class ResourceTypes(ACMEIntEnum):

	UNKNOWN			= -1
	ALL 			= -2	# used to indicate that something applies to all resources
	REQRESP			= -3
	COMPLEX			= -4

	# Resource Types
	# NOTE Always apply changes also to the m2m:resourceTypes in attributePolicies.ap etc

	MIXED			=  0
	ACP 			=  1
	AE				=  2
	CNT				=  3
	CIN 			=  4
	CSEBase 		=  5
	GRP 			=  9
	MGMTOBJ			= 13
	NOD				= 14
	PCH 			= 15
	CSR				= 16
	REQ 			= 17
	SUB				= 23
	SMD				= 24
	FCNT	 		= 28
	TS				= 29
	TSI   			= 30
	CRS				= 48
	FCI 			= 58
	TSB				= 60
	ACTR			= 63


	# Virtual resources (some are proprietary resource types)

	CNT_OL			=  20001	# actually a memberType
	CNT_LA			=  20002	# actually a memberType

	GRP_FOPT		=  -20003
	FCNT_OL			=  -20004
	FCNT_LA			=  -20005
	PCH_PCU			=  -20006
	TS_OL			=  -20007
	TS_LA			=  -20008

	# <mgmtObj> Specializations
	# NOTE Always apply changes also to the m2m:mgmtDefinition in attributePolicies.ap etc

	FWR				= 1001
	SWR				= 1002
	MEM				= 1003
	ANI				= 1004
	ANDI			= 1005
	BAT				= 1006
	DVI 			= 1007
	DVC 			= 1008
	RBO 			= 1009
	EVL 			= 1010
	DATC			= 1021	# dataCollection
	NYCFC			= 1023	# myCertFileCred
	WIFIC			= 1028	# WifiClient

	# Announced Resources

	ACPAnnc 		= 10001
	AEAnnc 			= 10002	
	CNTAnnc 		= 10003
	CINAnnc 		= 10004
	CSEBaseAnnc 	= 10005
	GRPAnnc 		= 10009
	MGMTOBJAnnc 	= 10013
	NODAnnc 		= 10014
	CSRAnnc 		= 10016
	SMDAnnc			= 10024
	FCNTAnnc 		= 10028
	TSAnnc			= 10029
	TSIAnnc			= 10030
	TSBAnnc			= 10060
	ACTRAnnc		= 10063

	FWRAnnc			= -30001
	SWRAnnc			= -30002
	MEMAnnc			= -30003
	ANIAnnc			= -30004
	ANDIAnnc		= -30005
	BATAnnc			= -30006
	DVIAnnc			= -30007
	DVCAnnc			= -30008
	RBOAnnc			= -30009
	EVLAnnc			= -30010
	DATCAnnc		= -30021
	NYCFCAnnc		= -30023
	WIFICAnnc		= -30028


	def tpe(self) -> str:
		return _ResourceTypesNames.get(self)


	def announced(self, mgd:Optional[ResourceTypes] = None) -> ResourceTypes:

		if self != ResourceTypes.MGMTOBJ:
			# Handling for non-mgmtObjs
			if (r := _ResourceTypesAnnouncedMappings.get(self)):
				return r
		else:
			# Handling for mgmtObjs
			if mgd is not None:
				if (r := _ResourceTypesAnnouncedMappings.get(mgd)):
					return r
			else:
				return _ResourceTypesAnnouncedMappings[ResourceTypes.MGMTOBJ] 
		return ResourceTypes.UNKNOWN


	def fromAnnounced(self) -> ResourceTypes:
		"""	Get the orginal announceable resource type for an announced type.

			Return:
				Announceable resource type, or UNKNOWN
		"""
		if (r := _ResourceTypesAnnouncedReverseMappings.get(self)):
			return r
		return ResourceTypes.UNKNOWN


	def isAnnounced(self) -> bool:
		"""	Test whether this type is an announced resource type.
		
			Return:
				True if the type is an announced resource type.
		"""
		return self in _ResourceTypesAnnouncedSetFull
	
	
	def isVirtual(self) -> bool:
		"""	Test whether this type is virtual resource type.
		
			Return:
				True if the type is a virtual resource type.
		"""
		return self.value in _ResourceTypesVirtualResourcesSet


	def resourceClass(self) -> Resource:			# type:ignore [name-defined]
		"""	Return a Resource class for this resource type.

			Return:
				The Resource class for the ResourceType.
		"""
		return _ResourceTypeDetails.get(self).clazz


	def resourceFactory(self) -> FactoryCallableT:
		"""	Return a Resource factory for this resource type.

			Return:
				The FactoryCallableT for the ResourceType.
		"""		
		return _ResourceTypeDetails.get(self).factory


	@classmethod
	def fromTPE(cls, tpe:str) -> ResourceTypes:
		"""	Get a resource type by its resource name.

			Args:
				tpe: Type name.
			Return:
				The resource type.
		"""
		return _ResourceNamesTypes.get(tpe)


	@classmethod
	def isVirtualResource(cls, ty:int) -> bool:
		"""	Check whether *ty* is a virtual resource.

			Args:
				ty: The resource type to check.
			Return:
				True if the resource type is a virtual resource.
		"""
		return ty in _ResourceTypesVirtualResourcesSet


	@classmethod
	def isVirtualResourceName(cls, name:str) -> bool:
		"""	Check whether *name* is the name of a virtual resource.

			Args:
				name: The resource name to check.
			Return:
				True if the resource type inidcated by the name is a virtual resource.
		"""
		return name in _ResourceTypesVirtualResourcesNames


	@classmethod
	def supportedResourceTypes(self) -> list[ResourceTypes]:
		"""	Return the supported resource types, including the 
			announced resource types.

			Return:
				List of supported `ResourceTypes`.
		"""
		return _ResourceTypesSupportedResourceTypes


	@classmethod
	def isInstanceResource(cls, ty:int) -> bool:
		"""	Test whether a resource type is an instance data resource type.

			Args:
				ty: Type to test.
			Return:
				*True* if the resource type is an instance resource.
		"""
		return ty in _ResourceTypesInstanceResourcesSet


	@classmethod
	def isRequestCreatable(cls, ty:ResourceTypes) -> bool:
		"""	Test whether a resource type is creatable through a request.
		
			Args:
				ty: `ResourceTypes` value to test.
			Return:
				*True* if the resource type can be created through a request.
		"""
		return ty in _ResourceTypesIsRequestCreatable


	@classmethod
	def isNotificationEntity(cls, ty:ResourceTypes) -> bool:
		"""	Test whether a resource type represents an entity that can be a notification target.
			This is different from any resource, that can be a notification target as well.
		
			Args:
				ty: `ResourceTypes` value to test.
			Return:
				*True* if the resource type represents a notification target.
		"""
		return ty in _ResourceTypesIsNotificationEntity


	@classmethod
	def isLatestOldestResource(cls, ty:int) -> bool:
		"""	Test whether a resource type is a *latest* or *oldest* virtual resource type.

			Args:
				ty: Type to test.

			Return:
				*True* if the resource type is a *latest* or *oldest* virtual resource.
		"""
		return ty in _ResourceTypesLatestOldest
		

@dataclass()
class ResourceDescription():
	typeName:str = None
	announcedType:ResourceTypes = None
	isAnnouncedResource:bool= False
	isMgmtSpecialization:bool = False
	isInstanceResource:bool = False
	isInternalType:bool = False
	virtualResourceName:str = None	# If this is set then the resource is a virtual resouce
	clazz:Resource = None 			# type:ignore [name-defined]
	factory:FactoryCallableT = None
	isRequestCreatable:bool = True	# Can be created by a request
	isNotificationEntity:bool = False	# Is a direct notification target
	
_ResourceTypeDetails = {
	
	# Normal resource types
	ResourceTypes.ACP 			: ResourceDescription(typeName = 'm2m:acp', announcedType = ResourceTypes.ACPAnnc),
	ResourceTypes.ACPAnnc 		: ResourceDescription(typeName = 'm2m:acpA', isAnnouncedResource = True),
	ResourceTypes.ACTR 			: ResourceDescription(typeName = 'm2m:actr', announcedType = ResourceTypes.ACTRAnnc),
	ResourceTypes.ACTRAnnc		: ResourceDescription(typeName = 'm2m:actrA', isAnnouncedResource = True),
	ResourceTypes.AE 			: ResourceDescription(typeName = 'm2m:ae', announcedType = ResourceTypes.AEAnnc, isNotificationEntity = True),
	ResourceTypes.AEAnnc		: ResourceDescription(typeName = 'm2m:aeA', isAnnouncedResource = True),
	ResourceTypes.CIN 			: ResourceDescription(typeName = 'm2m:cin', announcedType = ResourceTypes.CINAnnc, isInstanceResource = True),
	ResourceTypes.CINAnnc 		: ResourceDescription(typeName = 'm2m:cinA', isAnnouncedResource = True),
	ResourceTypes.CNT			: ResourceDescription(typeName = 'm2m:cnt', announcedType = ResourceTypes.CNTAnnc),
	ResourceTypes.CNTAnnc 		: ResourceDescription(typeName = 'm2m:cntA', isAnnouncedResource = True),
	ResourceTypes.CNT_LA		: ResourceDescription(typeName = 'm2m:la', virtualResourceName = 'la'),
	ResourceTypes.CNT_OL		: ResourceDescription(typeName = 'm2m:ol', virtualResourceName = 'ol'),
	ResourceTypes.CRS			: ResourceDescription(typeName = 'm2m:crs'),
	ResourceTypes.CSEBase 		: ResourceDescription(typeName = 'm2m:cb', announcedType = ResourceTypes.CSEBaseAnnc, isRequestCreatable = False, isNotificationEntity = True),
	ResourceTypes.CSEBaseAnnc 	: ResourceDescription(typeName = 'm2m:cbA', isAnnouncedResource = True),
	ResourceTypes.CSR			: ResourceDescription(typeName = 'm2m:csr', announcedType = ResourceTypes.CSRAnnc, isNotificationEntity = True),
	ResourceTypes.CSRAnnc 		: ResourceDescription(typeName = 'm2m:csrA', isAnnouncedResource = True),
	ResourceTypes.FCI			: ResourceDescription(typeName = 'm2m:fci', isInstanceResource = True, isRequestCreatable = False),					# not an official type name
	ResourceTypes.FCNT			: ResourceDescription(typeName = 'm2m:fcnt', announcedType = ResourceTypes.FCNTAnnc), 	# not an official type name
	ResourceTypes.FCNTAnnc 		: ResourceDescription(typeName = 'm2m:fcntA', isAnnouncedResource = True),				# not an official type name
	ResourceTypes.FCNT_LA		: ResourceDescription(typeName = 'm2m:la', virtualResourceName = 'la'),
	ResourceTypes.FCNT_OL		: ResourceDescription(typeName = 'm2m:ol', virtualResourceName = 'ol'),
	ResourceTypes.GRP			: ResourceDescription(typeName = 'm2m:grp', announcedType = ResourceTypes.GRPAnnc),
	ResourceTypes.GRPAnnc 		: ResourceDescription(typeName = 'm2m:grpA', isAnnouncedResource = True),
	ResourceTypes.GRP_FOPT		: ResourceDescription(typeName = 'm2m:fopt', virtualResourceName = 'fopt'),
	ResourceTypes.MGMTOBJ		: ResourceDescription(typeName = 'm2m:mgo', announcedType = ResourceTypes.MGMTOBJAnnc),	# not an official type name
	ResourceTypes.MGMTOBJAnnc 	: ResourceDescription(typeName = 'm2m:mgoA', isAnnouncedResource = True),				# not an official type name
	ResourceTypes.NOD			: ResourceDescription(typeName = 'm2m:nod', announcedType = ResourceTypes.NODAnnc),
	ResourceTypes.NODAnnc	 	: ResourceDescription(typeName = 'm2m:nodA', isAnnouncedResource = True),
	ResourceTypes.PCH			: ResourceDescription(typeName = 'm2m:pch'),
	ResourceTypes.PCH_PCU		: ResourceDescription(typeName = 'm2m:pcu', virtualResourceName = 'pcu'),
	ResourceTypes.REQ			: ResourceDescription(typeName = 'm2m:req', isRequestCreatable = False),
	ResourceTypes.SMD			: ResourceDescription(typeName = 'm2m:smd', announcedType = ResourceTypes.SMDAnnc),
	ResourceTypes.SMDAnnc		: ResourceDescription(typeName = 'm2m:smdA', isAnnouncedResource = True),
	ResourceTypes.SUB			: ResourceDescription(typeName = 'm2m:sub'),
	ResourceTypes.TS 			: ResourceDescription(typeName = 'm2m:ts', announcedType = ResourceTypes.TSAnnc),
	ResourceTypes.TSAnnc		: ResourceDescription(typeName = 'm2m:tsA', isAnnouncedResource = True),
	ResourceTypes.TS_LA			: ResourceDescription(typeName = 'm2m:la', virtualResourceName = 'la'),
	ResourceTypes.TS_OL			: ResourceDescription(typeName = 'm2m:ol', virtualResourceName = 'ol'),
	ResourceTypes.TSI 			: ResourceDescription(typeName = 'm2m:tsi', announcedType = ResourceTypes.TSIAnnc, isInstanceResource = True),
	ResourceTypes.TSIAnnc		: ResourceDescription(typeName = 'm2m:tsiA', isAnnouncedResource = True),
	ResourceTypes.TSB 			: ResourceDescription(typeName = 'm2m:tsb', announcedType = ResourceTypes.TSBAnnc),
	ResourceTypes.TSBAnnc 		: ResourceDescription(typeName = 'm2m:tsbA', isAnnouncedResource = True),

	# ManagementObj Specializations
	ResourceTypes.ANDI			: ResourceDescription(typeName = 'm2m:andi', announcedType = ResourceTypes.ANDIAnnc, isMgmtSpecialization = True),
	ResourceTypes.ANDIAnnc		: ResourceDescription(typeName = 'm2m:andiA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.ANI			: ResourceDescription(typeName = 'm2m:ani', announcedType = ResourceTypes.ANIAnnc, isMgmtSpecialization = True),
	ResourceTypes.ANIAnnc		: ResourceDescription(typeName = 'm2m:aniA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.BAT			: ResourceDescription(typeName = 'm2m:bat', announcedType = ResourceTypes.BATAnnc, isMgmtSpecialization = True),
	ResourceTypes.BATAnnc		: ResourceDescription(typeName = 'm2m:batA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.DATC			: ResourceDescription(typeName = 'dcfg:datc', announcedType = ResourceTypes.DATCAnnc, isMgmtSpecialization = True),
	ResourceTypes.DATCAnnc		: ResourceDescription(typeName = 'dcfg:datcA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.DVC			: ResourceDescription(typeName = 'm2m:dvc', announcedType = ResourceTypes.DVCAnnc, isMgmtSpecialization = True),
	ResourceTypes.DVCAnnc		: ResourceDescription(typeName = 'm2m:dvcA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.DVI			: ResourceDescription(typeName = 'm2m:dvi', announcedType = ResourceTypes.DVIAnnc, isMgmtSpecialization = True),
	ResourceTypes.DVIAnnc		: ResourceDescription(typeName = 'm2m:dviA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.EVL			: ResourceDescription(typeName = 'm2m:evl', announcedType = ResourceTypes.EVLAnnc, isMgmtSpecialization = True),
	ResourceTypes.EVLAnnc		: ResourceDescription(typeName = 'm2m:evlA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.FWR			: ResourceDescription(typeName = 'm2m:fwr', announcedType = ResourceTypes.FWRAnnc, isMgmtSpecialization = True),
	ResourceTypes.FWRAnnc		: ResourceDescription(typeName = 'm2m:fwrA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.MEM			: ResourceDescription(typeName = 'm2m:mem', announcedType = ResourceTypes.MEMAnnc, isMgmtSpecialization = True),
	ResourceTypes.MEMAnnc		: ResourceDescription(typeName = 'm2m:memA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.NYCFC			: ResourceDescription(typeName = 'm2m:nycfc', announcedType = ResourceTypes.NYCFCAnnc, isMgmtSpecialization = True),
	ResourceTypes.NYCFCAnnc		: ResourceDescription(typeName = 'm2m:nycfctA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.RBO			: ResourceDescription(typeName = 'm2m:rbo', announcedType = ResourceTypes.RBOAnnc, isMgmtSpecialization = True),
	ResourceTypes.RBOAnnc		: ResourceDescription(typeName = 'm2m:rboA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.SWR			: ResourceDescription(typeName = 'm2m:swr', announcedType = ResourceTypes.SWRAnnc, isMgmtSpecialization = True),
	ResourceTypes.SWRAnnc		: ResourceDescription(typeName = 'm2m:swrA', isAnnouncedResource = True, isMgmtSpecialization = True),
	ResourceTypes.WIFIC			: ResourceDescription(typeName = 'dcfg:wific', announcedType = ResourceTypes.WIFICAnnc, isMgmtSpecialization = True),
	ResourceTypes.WIFICAnnc		: ResourceDescription(typeName = 'dcfg:wificA', isAnnouncedResource = True, isMgmtSpecialization = True),

	# Internal resource types
	ResourceTypes.UNKNOWN	: ResourceDescription(typeName = 'unknown', isInternalType = True),
	ResourceTypes.ALL		: ResourceDescription(typeName = 'all', isInternalType = True),
	ResourceTypes.MIXED		: ResourceDescription(typeName = 'm2m:mixed', isInternalType = True),
	ResourceTypes.REQRESP	: ResourceDescription(typeName = 'reqresp', isInternalType = True),
	ResourceTypes.COMPLEX	: ResourceDescription(typeName = 'complex', isInternalType = True),

}


def addResourceFactoryCallback(ty:ResourceTypes, clazz:Resource, factory:FactoryCallableT) -> None: 	# type:ignore [name-defined]
	"""	Add a class and a factory to create an instande for a resource type.

		Args:
			ty: Resource type.
			clazz: A resource class.
			factory: A callable to create an instance for the resource type.
	"""
	if ty not in _ResourceTypeDetails:
		raise RuntimeError(f'Unknown resource type: {ty}')
	if not clazz:
		raise RuntimeError('undefined class')
	if not factory:
		raise RuntimeError('undefined factory callback')
	_ResourceTypeDetails[ty].clazz = clazz
	_ResourceTypeDetails[ty].factory = factory


# Fill  resource helper structures

_ResourceTypesAnnouncedMappings = { t : d.announcedType
								   for t, d in _ResourceTypeDetails.items()
								   if d.announcedType }
"""	Mapping between announceable and announced resources. """


_ResourceTypesAnnouncedReverseMappings = { d.announcedType : t
										   for t, d in _ResourceTypeDetails.items()
										   if d.announcedType }
"""	Mapping between announced and announceable resources. """


_ResourceTypesAnnouncedSetFull = [ t
								   for t, d in _ResourceTypeDetails.items()
								   if d.isAnnouncedResource ]
""" Mapping of resources to their announced counterparts. """


_ResourceTypesAnnouncedResourceTypes = [ d.announcedType
										 for t, d in _ResourceTypeDetails.items()
										 if d.announcedType and not d.isMgmtSpecialization and t != ResourceTypes.CSEBase]
""" Sorted list of announced resources without MgmtObj specializations. """
_ResourceTypesAnnouncedResourceTypes.sort()


_ResourceTypesSupportedResourceTypes = [ t
										 for t, d in _ResourceTypeDetails.items()
										 if not d.isMgmtSpecialization and not d.virtualResourceName and not d.isInternalType and t != ResourceTypes.CSEBaseAnnc]
""" Sorted list of supported resource types (without MgmtObj spezializations and virtual resources). """
_ResourceTypesSupportedResourceTypes.sort()


_ResourceTypesVirtualResourcesSet = [ t
									  for t, d in _ResourceTypeDetails.items()
									  if d.virtualResourceName ]
""" List of virtual resources. """


_ResourceTypesInstanceResourcesSet = [ t
									   for t, d in _ResourceTypeDetails.items()
									   if d.isInstanceResource ]
"""	List of instance resources. """


_ResourceTypesVirtualResourcesNames = [ d.virtualResourceName
										for d in _ResourceTypeDetails.values()
										if d.virtualResourceName ]
"""	List of virtual resource names. """
_ResourceTypesVirtualResourcesNames = list(set(_ResourceTypesVirtualResourcesNames))	# unique names


_ResourceTypesNames = { t : d.typeName
						for t, d in _ResourceTypeDetails.items()
						if not d.isInternalType }
""" Mapping between oneM2M resource types to type names. """

_ResourceNamesTypes = { d.typeName : t
						for t, d in _ResourceTypeDetails.items()
						if not d.isInternalType }
""" Mapping between oneM2M resource names to type names. """

_ResourceTypesIsRequestCreatable = [ t
									 for t, d in _ResourceTypeDetails.items()
									 if d.isRequestCreatable ]
"""	List of resource types that can be created by a request. """


_ResourceTypesIsNotificationEntity = [ t
									   for t, d in _ResourceTypeDetails.items()
									   if d.isNotificationEntity ]
"""	List of resource types that represent an entity that can be a notification target. """


_ResourceTypesLatestOldest = [ t
							   for t, d in _ResourceTypeDetails.items()
							   if d.typeName in [ 'm2m:la', 'm2m:ol' ] ]
"""	List of resource typs that represent latest or oldest virtual resources. """



class BasicType(ACMEIntEnum):
	""" Basic resource types.
	"""

	positiveInteger	= auto()
	nonNegInteger	= auto()
	unsignedInt		= auto()
	unsignedLong	= auto()
	string 			= auto()
	timestamp		= auto()
	absRelTimestamp	= auto()
	list 			= auto()
	listNE 			= auto()	# Not empty list
	dict 			= auto()
	anyURI			= auto()
	boolean			= auto()
	float 			= auto()
	geoCoordinates	= auto()
	integer			= auto()
	void 			= auto()
	duration 		= auto()
	any				= auto()
	complex 		= auto()
	enum	 		= auto()
	adict			= auto()	# anoymous dict structure
	base64 			= auto()
	schedule		= auto()	# scheduleEntry
	time			= timestamp	# alias type for time
	date			= timestamp	# alias type for date

	@classmethod
	def to(cls, name:str|Tuple[str], insensitive:Optional[bool] = True) -> BasicType:
		""" Convert a type name string to an enum value.
		
			Args:
				name: String or a Tuple of strings with names.
				insensitive: Whether to handle the type case-insensitive.
			Return:
				Enum value.
		"""
		return super().to(name, insensitive=insensitive)


class Cardinality(ACMEIntEnum):
	""" Resource attribute cardinalities.
	"""
	CAR1			= auto()
	"""	Mandatory."""
	CAR1L			= auto()
	"""	Mandatory list. """
	CAR1LN			= auto()
	"""	Mandatory list that shall not be empty. """
	CAR01			= auto()
	""" Optional. """
	CAR01L			= auto()
	""" Optional list."""
	CAR1N			= auto()
	""" Mandatory but may be Null/None. """

	@classmethod
	def hasCar(cls, name:str) -> bool:
		"""	Check whether an Cardinality without the 'car'
			prefix exists. 
			
			Example: 
				hasCar('01')
			Args:
				name: Cardinality.
			Return:
				Retun *True* if the cardinality exists.
		"""
		return cls.has(f'CAR{name}')
	
	
	@classmethod
	def to(cls, name:str|Tuple[str], insensitive:Optional[bool] = True) -> Cardinality:
		""" Convert a cardinality name string to an enum value.
		
			Args:
				name: String or a Tuple of strings with names.
				insensitive: Whether to handle the name case-insensitive.
			Return:
				Enum value.
		"""

		def _prepare(name:str) -> str:
			return name if name.lower().startswith('car') else f'CAR{name}'
		
		if isinstance(name, str):
			# handle and prepare as string
			return super().to(_prepare(name), insensitive=insensitive)
		else:
			# handle and prepare as tuple of strings
			return super().to(cast(Tuple[str], tuple([ _prepare(n) for n in name ])), insensitive=insensitive)


class RequestOptionality(ACMEIntEnum):
	""" Request optionality enum values.
	"""
	NP				= auto()
	""" Not provided. """
	O 				= auto()
	""" Optional. """
	M 				= auto()
	""" Mandatory. """


class Announced(ACMEIntEnum):
	""" Anouncement attribute enum values.
	"""
	NA				= auto()
	"""	Not announced. """
	OA				= auto()
	""" Optionally announced. """
	MA				= auto()
	"""	Mandatory announced. """


##############################################################################
#
#	Response Codes
#


class ResponseStatusCode(ACMEIntEnum):
	""" Response codes """
	accepted									= 1000
	acceptedNonBlockingRequestSynch				= 1001
	acceptedNonBlockingRequestAsynch			= 1002
	OK											= 2000
	created 									= 2001
	deleted 									= 2002
	updated										= 2004
	badRequest									= 4000
	releaseVersionNotSupported					= 4001
	notFound 									= 4004
	operationNotAllowed							= 4005
	requestTimeout 								= 4008
	unsupportedMediaType						= 4015
	subscriptionCreatorHasNoPrivilege			= 4101
	contentsUnacceptable						= 4102
	originatorHasNoPrivilege					= 4103
	conflict									= 4105
	securityAssociationRequired					= 4107
	invalidChildResourceType					= 4108
	groupMemberTypeInconsistent					= 4110
	originatorHasAlreadyRegistered				= 4117
	appRuleValidationFailed						= 4126
	operationDeniedByRemoteEntity				= 4127
	serviceSubscriptionNotEstablished			= 4128
	invalidSPARQLQuery 							= 4143
	internalServerError							= 5000
	notImplemented								= 5001
	targetNotReachable 							= 5103
	receiverHasNoPrivileges						= 5105
	alreadyExists								= 5106
	remoteEntityNotReachable					= 5107
	targetNotSubscribable						= 5203
	subscriptionVerificationInitiationFailed	= 5204
	subscriptionHostHasNoPrivilege				= 5205
	notAcceptable 								= 5207
	crossResourceOperationFailure 				= 5221
	maxNumberOfMemberExceeded					= 6010
	invalidArguments							= 6023
	insufficientArguments						= 6024


	UNKNOWN										= -1


	def httpStatusCode(self) -> int:
		""" Map the oneM2M RSC to an http status code. """
		return _ResponseStatusCodeHttpStatusCodes[self]



#
#	Mapping of oneM2M return codes to http status codes
#

_ResponseStatusCodeHttpStatusCodes = {
	ResponseStatusCode.OK 										: HTTPStatus.OK,						# OK
	ResponseStatusCode.deleted 									: HTTPStatus.OK,						# DELETED
	ResponseStatusCode.updated 									: HTTPStatus.OK,						# UPDATED
	ResponseStatusCode.created									: HTTPStatus.CREATED,					# CREATED
	ResponseStatusCode.accepted 								: HTTPStatus.ACCEPTED, 					# ACCEPTED
	ResponseStatusCode.acceptedNonBlockingRequestSynch 			: HTTPStatus.ACCEPTED,					# ACCEPTED FOR NONBLOCKINGREQUESTSYNCH
	ResponseStatusCode.acceptedNonBlockingRequestAsynch 		: HTTPStatus.ACCEPTED,					# ACCEPTED FOR NONBLOCKINGREQUESTASYNCH
	ResponseStatusCode.badRequest								: HTTPStatus.BAD_REQUEST,				# BAD REQUEST
	ResponseStatusCode.contentsUnacceptable						: HTTPStatus.BAD_REQUEST,				# NOT ACCEPTABLE
	ResponseStatusCode.insufficientArguments 					: HTTPStatus.BAD_REQUEST,				# INSUFFICIENT ARGUMENTS
	ResponseStatusCode.invalidArguments							: HTTPStatus.BAD_REQUEST,				# INVALID ARGUMENTS
	ResponseStatusCode.maxNumberOfMemberExceeded				: HTTPStatus.BAD_REQUEST, 				# MAX NUMBER OF MEMBER EXCEEDED
	ResponseStatusCode.groupMemberTypeInconsistent				: HTTPStatus.BAD_REQUEST,				# GROUP MEMBER TYPE INCONSISTENT
	ResponseStatusCode.invalidSPARQLQuery						: HTTPStatus.BAD_REQUEST,				# INVALID SPARQL QUERY
	ResponseStatusCode.serviceSubscriptionNotEstablished		: HTTPStatus.FORBIDDEN,					# SERVICE SUBSCRIPTION NOT ESTABLISHED
	ResponseStatusCode.originatorHasNoPrivilege					: HTTPStatus.FORBIDDEN,					# ORIGINATOR HAS NO PRIVILEGE
	ResponseStatusCode.invalidChildResourceType					: HTTPStatus.FORBIDDEN,					# INVALID CHILD RESOURCE TYPE
	ResponseStatusCode.alreadyExists							: HTTPStatus.FORBIDDEN,					# ALREAD EXISTS
	ResponseStatusCode.targetNotSubscribable					: HTTPStatus.FORBIDDEN,					# TARGET NOT SUBSCRIBABLE
	ResponseStatusCode.receiverHasNoPrivileges					: HTTPStatus.FORBIDDEN,					# RECEIVER HAS NO PRIVILEGE
	ResponseStatusCode.securityAssociationRequired				: HTTPStatus.FORBIDDEN,					# SECURITY ASSOCIATION REQUIRED
	ResponseStatusCode.subscriptionCreatorHasNoPrivilege		: HTTPStatus.FORBIDDEN,					# SUBSCRIPTION CREATOR HAS NO PRIVILEGE
	ResponseStatusCode.subscriptionHostHasNoPrivilege			: HTTPStatus.FORBIDDEN,					# SUBSCRIPTION HOST HAS NO PRIVILEGE
	ResponseStatusCode.originatorHasAlreadyRegistered			: HTTPStatus.FORBIDDEN,					# ORIGINATOR HAS ALREADY REGISTERED
	ResponseStatusCode.appRuleValidationFailed					: HTTPStatus.FORBIDDEN,					# APP RULE VALIDATION FAILED
	ResponseStatusCode.operationDeniedByRemoteEntity			: HTTPStatus.FORBIDDEN,					# OPERATION_DENIED_BY_REMOTE_ENTITY
	ResponseStatusCode.requestTimeout							: HTTPStatus.GATEWAY_TIMEOUT,			# REQUEST TIMEOUT
	ResponseStatusCode.notFound									: HTTPStatus.NOT_FOUND,					# NOT FOUND
	ResponseStatusCode.targetNotReachable						: HTTPStatus.NOT_FOUND,					# TARGET NOT REACHABLE
	ResponseStatusCode.remoteEntityNotReachable					: HTTPStatus.NOT_FOUND,					# REMOTE_ENTITY_NOT_REACHABLE
	ResponseStatusCode.operationNotAllowed						: HTTPStatus.METHOD_NOT_ALLOWED,		# OPERATION NOT ALLOWED
	ResponseStatusCode.notAcceptable 							: HTTPStatus.NOT_ACCEPTABLE,			# NOT ACCEPTABLE
	ResponseStatusCode.crossResourceOperationFailure			: HTTPStatus.INTERNAL_SERVER_ERROR,		# CROSS RESOURCE OPERATION FAILURE
	ResponseStatusCode.conflict									: HTTPStatus.CONFLICT,					# CONFLICT
	ResponseStatusCode.unsupportedMediaType						: HTTPStatus.UNSUPPORTED_MEDIA_TYPE,	# UNSUPPORTED_MEDIA_TYPE
	ResponseStatusCode.internalServerError 						: HTTPStatus.INTERNAL_SERVER_ERROR,		# INTERNAL SERVER ERROR
	ResponseStatusCode.subscriptionVerificationInitiationFailed	: HTTPStatus.INTERNAL_SERVER_ERROR,		# SUBSCRIPTION_VERIFICATION_INITIATION_FAILED
	ResponseStatusCode.releaseVersionNotSupported				: HTTPStatus.NOT_IMPLEMENTED,			# RELEASE_VERSION_NOT_SUPPORTED
	ResponseStatusCode.notImplemented							: HTTPStatus.NOT_IMPLEMENTED,			# NOT IMPLEMENTED
	
	ResponseStatusCode.UNKNOWN									: HTTPStatus.NOT_IMPLEMENTED,			# NOT IMPLEMENTED

}


##############################################################################
#
#	Gweneric Enums
#

class EvalCriteriaOperator(ACMEIntEnum):
	"""	Eval Criteria Operator enum values."""
	
	equal				= 1
	""" Equal. """
	
	notEqual			= 2
	""" Not equal. """
	
	greaterThan			= 3
	""" Greater than. """
	
	lessThan			= 4
	""" Less than. """

	greaterThanEqual	= 5
	""" Greater than or equal. """

	lessThanEqual		= 6
	""" Less than or equal. """


class EvalMode(ACMEIntEnum):
	"""	Eval Mode enum values. """
	
	off					= 0
	""" Evaluation off. """

	once				= 1
	""" Evaluation once. """

	periodic			= 2
	""" Evaluation periodic. """

	continous 			= 3
	""" Evaluation continous. """



##############################################################################
#
#	Permission related
#

class Permission(ACMEIntEnum):
	""" Permissions """
	NONE				=  0
	CREATE				=  1
	RETRIEVE			=  2
	UPDATE				=  4
	DELETE 				=  8
	NOTIFY 				= 16
	DISCOVERY			= 32
	ALL					= 63

	@classmethod
	def allExcept(cls, permission:Permission) -> int:
		p = Permission.ALL - permission
		return p if Permission.NONE <= p <= Permission.ALL else Permission.NONE


##############################################################################
#
#	Operation related
#

class Operation(ACMEIntEnum):
	# Operations
	CREATE 				= 1
	RETRIEVE			= 2
	UPDATE				= 3
	DELETE				= 4
	NOTIFY 				= 5
	DISCOVERY			= -2
	NA 					= -1


	def permission(self) -> Permission:
		""" Return the corresponding permission for an operation.
		"""
		return _OperationPermissionsMapping[self]


	def __str__(self) -> str:
		return self.name


	def __repr__(self) -> str:
		return self.__str__()


	@classmethod
	def isvalid(cls, op:int) -> bool:
		"""	Check whether an operation is valid.
		"""
		return cls.CREATE <= op <= cls.NOTIFY
	

	@classmethod
	def toOperation(cls, v:Optional[int]) -> Optional[Operation]:
		"""	Convert an integer or None to an Operation. Returns an Operation or None.
		"""
		return Operation(v) if v is not None else None


# Mapping between request operations and permissions
_OperationPermissionsMapping =	{
	Operation.RETRIEVE	: Permission.RETRIEVE,
	Operation.CREATE 	: Permission.CREATE,
	Operation.UPDATE 	: Permission.UPDATE,
	Operation.DELETE 	: Permission.DELETE,
	Operation.NOTIFY 	: Permission.NOTIFY,
	Operation.DISCOVERY : Permission.DISCOVERY,
}

##############################################################################
#
#	Discovery & Filter
#

class ResultContentType(ACMEIntEnum):
	"""	Result Content Types """
	nothing									= 0
	attributes 								= 1
	hierarchicalAddress						= 2
	hierarchicalAddressAttributes			= 3
	attributesAndChildResources				= 4	
	attributesAndChildResourceReferences	= 5
	childResourceReferences					= 6
	originalResource 						= 7
	childResources							= 8
	modifiedAttributes						= 9
	semanticContent							= 10
	discoveryResultReferences				= 11


	def validForOperation(self, op:Operation) -> bool:
		"""	Check whether an operation is valid with a Result Content.

			Args:
				op: The operation to check.
			Return:
				Boolean indicating the validity.
		"""
		return op in _ResultContentTypeForOperations and self.value in _ResultContentTypeForOperations[op] 

_ResultContentTypeForOperations = {
	Operation.RETRIEVE:		[ ResultContentType.attributes, 					
		   					  ResultContentType.attributesAndChildResources, 
							  ResultContentType.childResources, 
							  ResultContentType.attributesAndChildResourceReferences, 
							  ResultContentType.originalResource, 
							  ResultContentType.childResourceReferences ],
	Operation.DISCOVERY:	[ ResultContentType.discoveryResultReferences,
							  ResultContentType.childResourceReferences,
							  ResultContentType.semanticContent ],
	Operation.CREATE:		[ ResultContentType.attributes,
							  ResultContentType.modifiedAttributes,
							  ResultContentType.hierarchicalAddress,
							  ResultContentType.hierarchicalAddressAttributes,
							  ResultContentType.nothing ],
	Operation.UPDATE:		[ ResultContentType.attributes,
							  ResultContentType.modifiedAttributes,
							  ResultContentType.nothing ],
	Operation.DELETE:		[ ResultContentType.attributes,
							  ResultContentType.nothing,
							  ResultContentType.attributesAndChildResources,
							  ResultContentType.childResources,
							  ResultContentType.attributesAndChildResourceReferences,
							  ResultContentType.childResourceReferences ],
	Operation.NOTIFY:		[ ResultContentType.nothing ],
}


	# ResultContentType.discoveryRCN = [ ResultContentType.discoveryResultReferences,		 #  type: ignore
	# 								   ResultContentType.childResourceReferences ]

class FilterOperation(ACMEIntEnum):
	"""	Filter Operation """
	AND 			= 1 # default
	OR 				= 2
	XOR 			= 3


class FilterUsage(ACMEIntEnum):
	"""	Filter Usage """
	discoveryCriteria		= 1
	conditionalRetrieval	= 2 # default
	ipeOnDemandDiscovery	= 3
	discoveryBasedOperation	= 4


class DesiredIdentifierResultType(ACMEIntEnum):
	""" Desired Identifier Result Type """
	structured		= 1 # default
	unstructured	= 2


##############################################################################
#
#	CSE related
#

class CSEType(ACMEIntEnum):
	""" CSE Types """
	IN					=  1
	MN					=  2
	ASN					=  3


class CSEStatus(ACMEIntEnum):
	"""	CSE Status """
	STOPPED				= auto()
	STARTING			= auto()
	RUNNING				= auto()
	STOPPING			= auto()
	RESETTING			= auto()

##############################################################################
#
#	ResponseType 
#

class ResponseType(ACMEIntEnum):
	"""	Reponse Types enum values. """

	nonBlockingRequestSynch		= 1
	""" Non-blocking synchronous. """

	nonBlockingRequestAsynch	= 2
	""" Non-blocking asynchronous. """
	blockingRequest				= 3	# default
	""" Blocking request (default). """

	flexBlocking				= 4
	""" Flex-blocking (CSE decides). """

	noResponse					= 5
	""" No response. """
	

##############################################################################
#
#	Request Status 
#

class RequestStatus(ACMEIntEnum):
	"""	Reponse Types """
	COMPLETED			= 1
	FAILED				= 2
	PENDING				= 3
	FORWARDED			= 4
	PARTIALLY_COMPLETED	= 5


##############################################################################
#
#	Event Category 
#

class EventCategory(ACMEIntEnum):
	"""	Event Categories """
	Immediate			= 2
	BestEffort			= 3
	Latest				= 4


##############################################################################
#
#	Content Serializations
#

class ContentSerializationType(ACMEIntEnum):
	"""	Content Serialization Types 
	"""

	XML					= auto()
	JSON				= auto()
	CBOR				= auto()
	PLAIN				= auto()
	NA	 				= auto()
	UNKNOWN				= auto()

	def toHeader(self) -> str:
		"""	Return the mime header for a enum value.
		"""
		if self.value == self.JSON:	return 'application/json'
		if self.value == self.CBOR:	return 'application/cbor'
		if self.value == self.XML:	return 'application/xml'
		return None
	
	def toSimple(self) -> str:
		"""	Return the simple string for a enum value.
		"""
		if self.value == self.JSON:	return 'json'
		if self.value == self.CBOR:	return 'cbor'
		if self.value == self.XML:	return 'xml'
		return None

	@classmethod
	def toContentSerialization(cls, t:str) -> ContentSerializationType:
		"""	Return the enum from a string.
		"""
		t = t.lower()
		if t in [ 'cbor', 'application/cbor' ]:	return cls.CBOR
		if t in [ 'json', 'application/json' ]:	return cls.JSON
		if t in [ 'xml',  'application/xml'  ]:	return cls.XML
		return cls.UNKNOWN

	
	@classmethod
	def getType(cls, hdr:str, default:Optional[ContentSerializationType] = None) -> ContentSerializationType:
		"""	Return the enum from a header definition.
		"""
		default = cls.UNKNOWN if not default else default
		if not hdr:														return default
		hdr = hdr.lower()

		if hdr.lower() == 'json':										return cls.JSON
		if hdr.lower().startswith('application/json'):					return cls.JSON
		if hdr.lower().startswith('application/vnd.onem2m-res+json'):	return cls.JSON

		if hdr.lower() == 'cbor':										return cls.CBOR
		if hdr.lower().startswith('application/cbor'):					return cls.CBOR
		if hdr.lower().startswith('application/vnd.onem2m-res+cbor'):	return cls.CBOR
		
		if hdr.lower() == 'xml':										return cls.XML
		if hdr.lower().startswith('application/xml'):					return cls.XML
		if hdr.lower().startswith('application/vnd.onem2m-res+XML'):	return cls.XML

		return cls.UNKNOWN
	

	@classmethod
	def supportedContentSerializations(cls) -> list[str]:
		"""	Return a list of supported media types for content serialization.
		"""
		return [ 'application/json',
				 'application/vnd.onem2m-res+json', 
				 'application/cbor',
				 'application/vnd.onem2m-res+cbor' ]


	@classmethod
	def supportedContentSerializationsSimple(cls) -> list[str]:
		"""	Return a simplified (only the names of the serializations)
			list of supported media types for content serialization.
		"""
		return [ cls.JSON.toSimple(), cls.CBOR.toSimple() ]


	def __eq__(self, other:object) -> bool:
		if not isinstance(other, str):
			return NotImplemented
		return self.value == self.getType(str(other))


##############################################################################
#
#	Group related
#

class ConsistencyStrategy(ACMEIntEnum):
	"""	Consistency Strategy """
	abandonMember		= 1	# default
	abandonGroup		= 2
	setMixed			= 3


##############################################################################
#
#	Subscription related
#

class NotificationContentType(ACMEIntEnum):
	"""	Notification Content Types """
	all						= 1
	modifiedAttributes		= 2
	ri 						= 3
	triggerPayload			= 4
	timeSeriesNotification	= 5
	

class NotificationEventType(ACMEIntEnum):
	""" eventNotificationCriteria/NotificationEventTypes """
	resourceUpdate						=  1	# A, default
	resourceDelete						=  2	# B
	createDirectChild					=  3 # C
	deleteDirectChild					=  4 # D	
	retrieveCNTNoChild					=  5 # E # TODO not supported yet
	triggerReceivedForAE				=  6 # F # TODO not supported yet
	blockingUpdate 						=  7 # G
	# TODO spec and implementation for blockingUpdateDirectChild			=  ???
	reportOnGeneratedMissingDataPoints	=  8 # H
	blockingRetrieve					=  9 # I # EXPERIMENTAL
	blockingRetrieveDirectChild			= 10 # J # EXPERIMENTAL


	def isAllowedNCT(self, nct:NotificationContentType) -> bool:
		if nct == NotificationContentType.all:
			return self.value in [ NotificationEventType.resourceUpdate, 
								   NotificationEventType.resourceDelete, 
								   NotificationEventType.createDirectChild, 
								   NotificationEventType.deleteDirectChild ]
		elif nct == NotificationContentType.modifiedAttributes:
			return self.value in [ NotificationEventType.resourceUpdate, 
								   NotificationEventType.blockingUpdate ]
		elif nct == NotificationContentType.ri:
			return self.value in [ NotificationEventType.resourceUpdate, 
								   NotificationEventType.resourceDelete, 
								   NotificationEventType.createDirectChild, 
								   NotificationEventType.deleteDirectChild ]
		elif nct == NotificationContentType.triggerPayload:
			return self.value in [ NotificationEventType.triggerReceivedForAE ]
		elif nct == NotificationContentType.timeSeriesNotification:
			return self.value in [ NotificationEventType.reportOnGeneratedMissingDataPoints ]
		return False


##############################################################################
#
#	TimeSeries related
#

@dataclass
class MissingData:
	"""	Data class for collecting the missing data states. """ 
	subscriptionRi:str
	missingDataDuration:float
	missingDataNumber:int
	timeWindowEndTimestamp:float	= None
	missingDataList:list[str]		= field(default_factory=list)
	missingDataCurrentNr:int 		= 0

	def clear(self) -> None:
		self.timeWindowEndTimestamp	= None
		self.clearMissingDataList()


	def clearMissingDataList(self) -> None:
		self.missingDataList		= []
		self.missingDataCurrentNr	= 0

	
	def asDict(self) -> JSON:
		return {
			'mdlt': self.missingDataList,
			'mdc' : self.missingDataCurrentNr
		}



@dataclass
class LastTSInstance:
	"""	Data class for a single TS's latest and next expected TSI/dgt, and other information """

	# runtime attributes
	dgt:list[float]						= field(default_factory = lambda: [0])
	expectedDgt:float				 	= 0.0
	missingDataDetectionTime:float		= 0.0

	# <TS> attributes
	pei:float							= 0.0
	mdt:float							= 0.0
	peid:float							= 0.0

	# Subscriptions
	missingData:dict[str, MissingData]	= field(default_factory = dict)

	# Internal
	actor:BackgroundWorker				= None	#type:ignore[name-defined] # actor for this TS 
	running:bool 						= False # for late activation of this 


	def prepareNextDgt(self) -> None:
		"""	Set the next expectedDgt.
		"""
		self.expectedDgt += self.pei
	

	def prepareNextRun(self) -> None:
		"""	Set the next missingDataDetectionTime.
		"""
		self.missingDataDetectionTime += self.pei # mdt?
	

	def addDgt(self, dgt:float) -> None:
		# TODO really support list. currently only one dgt is put, but 
		# always overrides the old one. 
		# Also change declaration of dgt above
		if len(self.dgt) == 0:
			self.dgt.append(dgt)
		else:
			self.dgt[0] = dgt
	

	def nextDgt(self) -> float:
		if len(self.dgt) == 0:
			return None
		return self.dgt.pop(0)
	

	def hasDgt(self) -> bool:
		return len(self.dgt) > 0
	

	def clearDgt(self) -> None:
		self.dgt.clear()
		


##############################################################################
#
#	Announcement related
#

class AnnounceSyncType(ACMEIntEnum):
	""" Announce Sync Types """
	UNI_DIRECTIONAL = 1
	BI_DIRECTIONAL = 2


##############################################################################
#
#	TimeSyncBeacon related
#

class BeaconCriteria(ACMEIntEnum):
	""" TimeSyncBeacon criteria.
	"""
	
	PERIODIC = 1
	"""	Periodic check (default). """
	LOSS_OF_SYNCHRONIZATION = 2
	""" When loss of synchronization happens. """


##############################################################################
#
#	CrossResourceSubscription related
#

class TimeWindowType(ACMEIntEnum):
	""" Time window type.
	"""
	
	PERIODICWINDOW = 1
	"""	Periodic Window (default)."""
	SLIDINGWINDOW = 2
	"""	Sliding Window. """

##############################################################################
#
#	Semantic related
#

class SemanticFormat(ACMEIntEnum):
	""" Semantic Format.
	"""
	
	IRI = 1
	"""	IRI."""
	FF_FunctionalStyle = 2
	"""	File format: Functional-style. """
	FF_OwlXml = 3
	"""	File format: OWL/XML. """
	FF_RdfXml = 4
	"""	File format: RDF/XML. """
	FF_RdfTurtle = 5
	"""	File format: RDF/Turtle. """
	FF_Manchester = 6
	"""	File format: Manchester. """
	FF_JsonLD = 7
	"""	File format: JSON-LD. """


_SemanticFormatAsString = {
	SemanticFormat.IRI:					'iri',
	SemanticFormat.FF_FunctionalStyle:	'functional',
	SemanticFormat.FF_OwlXml:			'owl-xml',
	SemanticFormat.FF_RdfXml:			'xml',
	SemanticFormat.FF_RdfTurtle:		'ttl',
	SemanticFormat.FF_Manchester:		'manchester',
	SemanticFormat.FF_JsonLD:			'json-ld',
	

}

##############################################################################
#
#	Result and Argument and Header Data Classes
#


@dataclass
class Result:
	"""	This class represents the generic return state for many functions. It main contain
		the general result, a status code, values, resources etc.
	"""
	resource:Resource						= None		# type: ignore # Actually this is a Resource type, but have a circular import problem.
	data:Any|Sequence[Any]|Tuple|JSON|str	= None 		# Anything, or list of anything, or a JSON dictionary	
	rsc:ResponseStatusCode					= ResponseStatusCode.UNKNOWN	#	The responseStatusCode of a Result
	dbg:str 								= None
	request:CSERequest						= None  	# may contain the processed incoming request object
	embeddedRequest:CSERequest 				= None		# May contain a request as a response, e.g. when polling
	status:bool 							= None


	def errorResultCopy(self) -> Result:
		""" Copy only the rsc and dbg to a new result instance.

			Return:
				Result instance.
		"""
		return Result(status = self.status, rsc = self.rsc, dbg = self.dbg)
	

	@classmethod
	def errorResult(cls, rsc:Optional[ResponseStatusCode] = ResponseStatusCode.badRequest,
						 dbg:Optional[str] = '', 
						 request:Optional[CSERequest] = None,
						 data:Optional[Any] = None) -> Result:
		"""	Create and return a `Result` object with *status* set to *False* and `ResponseStatusCode` and debug
			message set.

			Args:
				rsc: `ResponseStatusCode` to return as an error.
				dbg: String with the debug message.
				request: `CSERequest` to return.
			Return:
				Error `Result` instance.
		"""
		return Result(status = False, rsc = rsc, request = request, dbg = dbg, data = data) 


	@classmethod
	def successResult(cls) -> Result:
		"""	Create and return a static `Result` object with *status* attribute set to *True*.

			Return:
				Success `Result` instance. This is always the same `Result` instance!
		"""
		return _successResult


	def toData(self, ct:Optional[ContentSerializationType] = None) -> str|bytes|JSON:
		from ..resources.Resource import Resource
		from ..etc.RequestUtils import serializeData
		from ..services.CSE import defaultSerialization

		# determine the default serialization type if none was given
		ct = defaultSerialization if not ct else ct

		if isinstance(self.resource, Resource):
			r = serializeData(self.resource.asDict(), ct)
		elif self.dbg:
			r = serializeData({ 'm2m:dbg' : self.dbg }, ct)
		elif isinstance(self.resource, dict):
			r = serializeData(self.resource, ct)
		elif self.data:									# explicit json or cbor from the dict
			r = serializeData(cast(JSON, self.data), ct)
		elif self.request and self.request.pc:		# Return the dict if the request is set and has a dict
			r = self.request.pc
		else:
			r = ''
		return r


	def prepareResultFromRequest(self, originalRequest:CSERequest) -> None:
		"""	Copy the necessary fields from an original request. Existing
			fields will not be overwritten.
		"""
		if not self.request:
			self.request = CSERequest()
		if originalRequest:
			if not self.request.ct:
				self.request.ct = originalRequest.ct
			if not self.request.rqi:
				self.request.rqi = originalRequest.rqi
			if not self.request.rvi:
				self.request.rvi = originalRequest.rvi
			if not self.request.vsi:
				self.request.vsi = originalRequest.vsi
			if not self.request.httpAccept:
				self.request.httpAccept = originalRequest.httpAccept
			if not self.request.mediaType:
				self.request.mediaType = originalRequest.mediaType
			if not self.request.originator:
				self.request.originator = originalRequest.originator
			if not self.request.ec:
				self.request.ec = originalRequest.ec
			

# Result instance to be re-used all over the place
_successResult = Result(status = True)


##############################################################################
#
#	Request and Response structures
#

class RequestType(ACMEIntEnum):
	"""	Internal type to indicate the purpose of the
		the CSERequest struct.
	"""
	REQUEST							= auto()
	"""	CSERequest is a request. """
	
	RESPONSE 						= auto()
	""" CSERequest is a response. """

	NOTSET	 						= auto()
	""" Undetermined. """


@dataclass
class FilterCriteria:
	"""	Sub-structure for CSERequest.
	
		It contains the filterCriteria attributes and further helper attributes.
	"""

	# Result handling
	fu:FilterUsage = FilterUsage.conditionalRetrieval
	""" Filter usage. Default: conditional retrieval. """

	fo:FilterOperation = None
	""" Filter Operation. Default is *AND*. """

	lim:int = None
	""" Limit filter criterion. Default is *sys.maxsize*. """

	lvl:int = None
	""" Level filter criterion. Default is *sys.maxsize*. """

	ofst:int = None
	"""	Offset filter criterion. Default is *1*. """

	arp:str = None
	""" applyRelativePath. Default is *None*. """

	# Conditions
	crb:str = None
	""" Created before. Default is *None*. """

	cra:str = None
	""" Created after. Default is *None*. """

	ms:str = None
	""" Modified since. Default is *None*. """

	us:str = None
	""" Unmodified since. Default is *us*. """

	sts:int = None
	""" State tag smaller. Default is *None*. """
	
	stb:int = None
	""" State tag bigger. Default is *None*. """

	exb:str = None
	""" Expire before. Default is *None*. """
	
	exa:str = None
	""" Expire after. Default is *None*. """

	lbq:str = None
	""" Labels query. Default is *None*. """	

	sza:int = None
	""" Size above. Default is *None*. """

	szb:int = None
	""" Size before. Default is *None*. """

	catr:str = None
	""" Child attribute. Default is *None*. """

	patr:str = None
	""" Parent attribute. Dfault is *None*. """

	cty:list = None
	""" List of content types. Default is *None*. """

	smf:str = None
	""" Semantic filter. Default is *None*. """

	ty:list = None
	""" List of resource types. Default is *None*. """

	lbl:list = None
	""" List of labels. Default is *None*. """

	# Other filter attributes
	attributes:Parameters = field(default_factory = dict)
	""" All other remaining filter resource attributes. """


	def set(self, name:str, value:Any) -> None:
		"""	Set a Filter Criteria attribute by it's name. If it is not a predefined
			attribute, then add it to the *attributes* attrribute.
			
			Args:
				name: Name of the attribute.
				value: Value of the attribute.
		"""
		if hasattr(self, name):
			setattr(self, name, value)
	

	def criteriaAttributes(self) -> dict:
		"""	Return all the set Filter Criteria attributes, ie. that are not None.
			The result doesn't include handling attributes, such as 'fu' or 'fo'.
			
			Return:
				Dictionary with set Filter Criteria attributes.
		"""
		return { k:v 
				 for k, v in self.__dict__.items() 
				 if k is not None and k not in [ 'fu', 'fo', 'lim', 'ofst', 'lvl', 'arp', 'attributes' ] and v is not None
			   }


	def __str__(self) -> str:
		"""	String representation of the Filter Criteria attributes.
			
			Return:
				String representation.
		"""
		return ', '.join([ f'{k}: {v}' 
						   for k, v in self.__dict__.items() 
						   if k is not None and k != 'attributes' and v is not None ])


@dataclass
class CSERequest:
	"""	Structure that holds all the attributes for a Request (or a Response) to a CSE.
	"""

	fc:FilterCriteria = field(default_factory = FilterCriteria)
	""" Filter Criteria complex structure. """
	
	# ID handling
	to:str = None
	"""	The request's original target. """

	id:str = None
	""" Target resource ID. Might be structured or unstructured. Based on the value of `to`. """

	srn:str = None
	""" The target's structured resource ID. Might not be present in a request. Based on the value of `to`. """
	
	csi:str = None
	""" The CSE-ID of the target's hosting CSI. Might not be present in a request. Based on the value of `to`. """

	# Request attributes
	op:Operation = None
	"""	Request Operation. """

	originator:str = None 
	"""	Request originator (from, X-M2M-Origin). """

	rsc:ResponseStatusCode = ResponseStatusCode.UNKNOWN
	""" Response Status Code. """

	rqi:str = None
	"""	Request Identifier (X-M2M-RI). """
	
	rvi:str = None
	"""	Release Version Identifier (X-M2M-RVI). """
	
	ty:ResourceTypes = None
	""" Resource type. """

	drt:DesiredIdentifierResultType	= DesiredIdentifierResultType.structured
	"""	Desired Indentifier Result Type (default: structured). """

	rcn:ResultContentType = ResultContentType.discoveryResultReferences
	""" Result Content Type. """

	rt:ResponseType = ResponseType.blockingRequest
	""" Response Type (default: blocking request)."""

	rp:str = None
	""" Result Persistence. """

	_rpts:str = None
	""" Internal: Result Persistence (rp) as a timestamp. """

	vsi:str = None
	"""	Vendor Information (X-M2M-VSI). """
	
	rqet:str = None
	"""	Request Expiration Timestamp in ISO8901 format (X-M2M-RET). """
	
	_rqetUTCts:float = None 	# X-M2M-RET as UTC based timestamp
	""" Request Expiration Timestamp as UTC-based timestamp (internal). """
	
	ot:str = None  
	"""	Originating Timestamp in ISO8901 format. """
	
	oet:str = None
	""" Operation Execution Time in ISO8901 format or as ms (X-M2M-OET). """
	
	rset:str = None 
	""" Result Expiration Time in ISO8901 format or as ms (X-M2M-RST). """

	rtu:list[str] = None
	""" The notificationURI element of the Response Type parameter(X-M2M-RTU). """

	ct:ContentSerializationType = None
	"""	Content Serialization Type. """

	ec:int = None
	"""	Event Category. """

	sqi:bool = None
	""" Semantic Query Indicator """

	pc:JSON = None
	""" The request's primitive content as a dictionary. """
	
	# HTTP specifics

	mediaType:str = None
	""" Transmitted media type (http ->'Content-Type'). """

	# Generics, internals
	originalData:bytes = None 
	""" The request's original data. """

	originalRequest:JSON = None
	""" The original request after dissection as a dictionary. """

	requestType:RequestType	= RequestType.NOTSET
	""" The struture is for a request or a response. """

	#
	#	HTTP specifics
	#

	httpAccept:list[str]			= None
	"""	http Accept header media type. """

	originalHttpArgs:Any 			= None
	""" Original http request arguments. A MultiDict. """


##############################################################################
#
#	Validation Types
#

@dataclass
class AttributePolicy:
	
	# !!! DON'T CHANGE the order of the attributes!

	type:BasicType
	cardinality:Cardinality
	optionalCreate:RequestOptionality
	optionalUpdate:RequestOptionality
	optionalDiscovery:RequestOptionality
	announcement:Announced
	sname:str 					= None 	# short name
	lname:str 					= None	# longname
	namespace:str				= None	# namespace
	tpe:str   					= None	# namespace:type name
	rtypes:List[ResourceTypes]	= None	# Optional list of multiple resourceTypes
	ctype:str					= None	# Definition for a complex type attribute
	typeName:str				= None	# The type as written in the definition
	fname:str					= None 	# Name of the definition file
	ltype:BasicType				= None	# sub-type of a list
	lTypeName:str				= None	# sub-type of a list as writen in the definition
	evalues:list[Any]			= None 	# List of enum values

	# TODO support annnouncedSyncType

	def select(self, index:int) -> Optional[Any]:
		"""	Return the n-th attributes in the dataclass.

			Args:
				index: Attribute index
			Return:
				n-th attribute from the dataclass, or None in case of an error.
		"""
		try:
			return astuple(self)[index]
		except IndexError:
			return None


"""	Represent a dictionary of attribute policies used in validation. """
AttributePolicyDict = Dict[str, AttributePolicy]
ResourceAttributePolicyDict = Dict[Tuple[Union[ResourceTypes, str], str], AttributePolicy]

FlexContainerAttributes = Dict[str, Dict[str, AttributePolicy]]
FlexContainerSpecializations = Dict[str, str]


##############################################################################
#
#	Generic Types
#


Parameters = Dict[str, str]
Attributes = Dict[str, Any]
JSON = Dict[str, Any]
JSONLIST = List[JSON]
ReqResp = Dict[str, Union[int, str, List[str], JSON]]

RequestCallback = namedtuple('RequestCallback', 'ownRequest dispatcherRequest')
RequestHandler = Dict[Operation, RequestCallback]
""" Type definition for a map between operations and handler for outgoing request operations. """

FactoryCallableT = Callable[ [ Dict[str, object], str, str, bool], object ]
"""	Type definition for a factory callback to create and initializy a Resource instance. """