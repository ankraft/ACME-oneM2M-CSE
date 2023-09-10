#
#	Types.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#

"""	Various CSE and oneM2M types.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, astuple
from typing import Tuple, cast, Dict, Any, List, Union, Sequence, Callable, Optional, Type
from enum import auto
from collections import namedtuple
from ..helpers.ACMEIntEnum import ACMEIntEnum
from ..etc.ResponseStatusCodes import ResponseStatusCode
from ..etc.DateUtils import utcTime


#
#	Resource Types
#

class ResourceTypes(ACMEIntEnum):
	"""	oneM2M Resource types.

		This includes Announced resouces, ManagementObject specifalizations, and CSE-internal resource types.
	"""

	UNKNOWN			= -1
	""" Indicate an unknown type (internal). """
	ALL 			= -2	# used to indicate that something applies to all resources
	""" Indicate all supported resource types (internal). """
	REQRESP			= -3
	"""	Type for request / response structures (internal). """
	COMPLEX			= -4
	"""	Indicate a comples data structure (internal). """

	# Resource Types
	# NOTE Always apply changes also to the m2m:resourceTypes in attributePolicies.ap etc

	MIXED			=  0
	"""	oneM2M *mixed* resource type (e.g. for groups). """
	ACP 			=  1
	"""	Access Control Policy resource type. """
	AE				=  2
	"""	Application Entity resource type. """
	CNT				=  3
	"""	Container resource type. """
	CIN 			=  4
	"""	ContentInstance resource type. """
	CSEBase 		=  5
	"""	CSEBase resource type. """
	GRP 			=  9
	"""	Group resouce type. """
	LCP				= 10
	"""	LocationPolicy resource type. """
	MGMTOBJ			= 13
	"""	ManagementObject resource type. """
	NOD				= 14
	"""	Node resource type. """
	PCH 			= 15
	"""	PollingChannel resource type. """
	CSR				= 16
	"""	Remote CSE resource type. """
	REQ 			= 17
	"""	Request resource type. """
	SCH				= 18
	"""	Schedule resource type. """
	SUB				= 23
	"""	Subscription resource type. """
	SMD				= 24
	""" SemanticDescriptor resouce type. """
	FCNT	 		= 28
	"""	FlexContainer resource type. """
	TS				= 29
	"""	TimeSeries resource type. """
	TSI   			= 30
	"""	TimeSeriesInstance resource type. """
	CRS				= 48
	"""	CrossResourceSubscription resource type. """
	FCI 			= 58
	""" FlexContainerInstance resource type. """
	TSB				= 60
	"""	TimeSyncBeacon resource type. """
	ACTR			= 65
	""" Action resource type. """
	DEPR			= 66



	# Virtual resources (some are proprietary resource types)

	CNT_OL			=  20001	# actually a memberType
	"""	Latest virtual resource type for Container. """
	CNT_LA			=  20002	# actually a memberType
	"""	Oldest virtual resource type for Container. """
	GRP_FOPT		=  -20003
	"""	Group FanOutPoint virtual resource type. """
	FCNT_OL			=  -20004
	"""	Latest virtual resource type for FlexContainer. """
	FCNT_LA			=  -20005
	"""	Oldest virtual resource type for FlexContainer. """
	PCH_PCU			=  -20006
	"""	PollingChannelURI virtual resource type. """
	TS_OL			=  -20007
	"""	Latest virtual resource type for TimeSeries. """
	TS_LA			=  -20008
	"""	Oldest virtual resource type for TimeSeries. """


	# <mgmtObj> Specializations
	# NOTE Always apply changes also to the m2m:mgmtDefinition in attributePolicies.ap etc

	FWR				= 1001
	"""	Firmware ManagementObject specialization. """
	SWR				= 1002
	"""	Software ManagementObject specialization. """
	MEM				= 1003
	"""	Memory ManagementObject specialization. """
	ANI				= 1004
	"""	AreaNetworkInfo ManagementObject specialization. """
	ANDI			= 1005
	"""	AreaNwkDeviceInfo ManagementObject specialization. """
	BAT				= 1006
	"""	Battery ManagementObject specialization. """
	DVI 			= 1007
	"""	DeviceInfo ManagementObject specialization. """
	DVC 			= 1008
	"""	DeviceCapability ManagementObject specialization. """
	RBO 			= 1009
	"""	Reboot ManagementObject specialization. """
	EVL 			= 1010
	"""	EventLog ManagementObject specialization. """
	DATC			= 1021	# dataCollection
	"""	DataCollection ManagementObject specialization. """
	NYCFC			= 1023	# myCertFileCred
	"""	MyCertFileCred ManagementObject specialization. """
	WIFIC			= 1028	# WifiClient
	"""	WifiClient ManagementObject specialization. """

	# Announced Resources

	ACPAnnc 		= 10001
	"""	Announced Access Control Policy resource type. """
	AEAnnc 			= 10002	
	"""	Announced Application Entity resource type. """
	CNTAnnc 		= 10003
	"""	Announced Container resource type. """
	CINAnnc 		= 10004
	"""	Announced ContentInstance resource type. """
	CSEBaseAnnc 	= 10005
	"""	Announced CSEBase resource type. """
	GRPAnnc 		= 10009
	"""	Announced Group resouce type. """
	LCPAnnc			= 10010
	"""	Announced LocationPolicy resource type. """
	MGMTOBJAnnc 	= 10013
	"""	Announced ManagementObject resource type. """
	NODAnnc 		= 10014
	"""	Announced Node resource type. """
	CSRAnnc 		= 10016
	"""	Announced Remote CSE resource type. """
	SCHAnnc 		= 10018
	"""	Announced Schedule resource type. """
	SMDAnnc			= 10024
	"""	Announced SemanticDescriptor resouce type. """
	FCNTAnnc 		= 10028
	"""	Announced FlexContainer resource type. """
	TSAnnc			= 10029
	"""	Announced TimeSeries resource type. """
	TSIAnnc			= 10030
	"""	Announced TimeSeriesInstance resource type. """
	TSBAnnc			= 10060
	"""	Announced TimeSyncBeacon resource type. """
	ACTRAnnc		= 10065
	"""	Announced Action resource type. """
	DEPRAnnc		= 10066

	"""	Announced Dependency resource type. """
	FWRAnnc			= -30001
	"""	Announced Firmware ManagementObject specialization. """
	SWRAnnc			= -30002
	"""	Announced Softwware ManagementObject specialization. """
	MEMAnnc			= -30003
	"""	Announced Memory ManagementObject specialization. """
	ANIAnnc			= -30004
	"""	Announced AreaNetworkInfo ManagementObject specialization. """
	ANDIAnnc		= -30005
	"""	Announced AreaNwkDeviceInfo ManagementObject specialization. """
	BATAnnc			= -30006
	"""	Announced Battery ManagementObject specialization. """
	DVIAnnc			= -30007
	"""	Announced DeviceInfo ManagementObject specialization. """
	DVCAnnc			= -30008
	"""	Announced DeviceCapability ManagementObject specialization. """
	RBOAnnc			= -30009
	"""	Announced Reboot ManagementObject specialization. """
	EVLAnnc			= -30010
	"""	Announced EventLog ManagementObject specialization. """
	DATCAnnc		= -30021
	"""	Announced DataCollection ManagementObject specialization. """
	NYCFCAnnc		= -30023
	"""	Announced MyCertFileCred ManagementObject specialization. """
	WIFICAnnc		= -30028
	"""	Announced WifiClient ManagementObject specialization. """


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
			This is different from any other resource type, that can be a notification target as well.
		
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
		

	@classmethod
	def fullname(cls, ty:int) -> str:
		"""	Get the full name of a resource type.

			Args:
				ty: Type to get the full name for.
			Return:
				The full name of the resource type.
		"""
		return _ResourceTypeDetails.get(ResourceTypes(ty)).fullName


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
	fullName:str = ''				# Full name of the resource type
	
_ResourceTypeDetails = {
	
	# Normal resource types
	ResourceTypes.ACP 			: ResourceDescription(typeName = 'm2m:acp', announcedType = ResourceTypes.ACPAnnc, fullName = 'AccessControlPolicy'),
	ResourceTypes.ACPAnnc 		: ResourceDescription(typeName = 'm2m:acpA', isAnnouncedResource = True, fullName = 'AccessControlPolicy Announced'),
	ResourceTypes.ACTR 			: ResourceDescription(typeName = 'm2m:actr', announcedType = ResourceTypes.ACTRAnnc, fullName = 'Action'),
	ResourceTypes.ACTRAnnc		: ResourceDescription(typeName = 'm2m:actrA', isAnnouncedResource = True, fullName = 'Action Announced'),
	ResourceTypes.AE 			: ResourceDescription(typeName = 'm2m:ae', announcedType = ResourceTypes.AEAnnc, isNotificationEntity = True, fullName = 'ApplicationEntity'),
	ResourceTypes.AEAnnc		: ResourceDescription(typeName = 'm2m:aeA', isAnnouncedResource = True, fullName = 'ApplicationEntity Announced'),
	ResourceTypes.CIN 			: ResourceDescription(typeName = 'm2m:cin', announcedType = ResourceTypes.CINAnnc, isInstanceResource = True, fullName='ContentInstance'),
	ResourceTypes.CINAnnc 		: ResourceDescription(typeName = 'm2m:cinA', isAnnouncedResource = True, fullName='ContentInstance Announced'),
	ResourceTypes.CNT			: ResourceDescription(typeName = 'm2m:cnt', announcedType = ResourceTypes.CNTAnnc, fullName='Container'),
	ResourceTypes.CNTAnnc 		: ResourceDescription(typeName = 'm2m:cntA', isAnnouncedResource = True, fullName='Container Announced'),
	ResourceTypes.CNT_LA		: ResourceDescription(typeName = 'm2m:la', virtualResourceName = 'la', fullName='Latest'),
	ResourceTypes.CNT_OL		: ResourceDescription(typeName = 'm2m:ol', virtualResourceName = 'ol', fullName='Oldest'),
	ResourceTypes.CRS			: ResourceDescription(typeName = 'm2m:crs', fullName='Cross Resource Subscription'),
	ResourceTypes.CSEBase 		: ResourceDescription(typeName = 'm2m:cb', announcedType = ResourceTypes.CSEBaseAnnc, isRequestCreatable = False, isNotificationEntity = True, fullName='CSEBase'),
	ResourceTypes.CSEBaseAnnc 	: ResourceDescription(typeName = 'm2m:cbA', isAnnouncedResource = True, fullName='CSEBase Announced'),
	ResourceTypes.CSR			: ResourceDescription(typeName = 'm2m:csr', announcedType = ResourceTypes.CSRAnnc, isNotificationEntity = True, fullName='RemoteCSE'),
	ResourceTypes.CSRAnnc 		: ResourceDescription(typeName = 'm2m:csrA', isAnnouncedResource = True, fullName='RemoteCSE Announced'),
	ResourceTypes.DEPR 			: ResourceDescription(typeName = 'm2m:depr',  announcedType = ResourceTypes.DEPRAnnc, fullName='Dependency'),
	ResourceTypes.DEPRAnnc		: ResourceDescription(typeName = 'm2m:deprA', isAnnouncedResource = True, fullName='Dependency Announced'),
	ResourceTypes.FCI			: ResourceDescription(typeName = 'm2m:fci', isInstanceResource = True, isRequestCreatable = False, fullName='FlexContainer Instance'),					# not an official type name
	ResourceTypes.FCNT			: ResourceDescription(typeName = 'm2m:fcnt', announcedType = ResourceTypes.FCNTAnnc, fullName='FlexContainer'), 	# not an official type name
	ResourceTypes.FCNTAnnc 		: ResourceDescription(typeName = 'm2m:fcntA', isAnnouncedResource = True, fullName = 'FlexContainer Announced'),				# not an official type name
	ResourceTypes.FCNT_LA		: ResourceDescription(typeName = 'm2m:la', virtualResourceName = 'la', fullName='Latest'),	# not an official type name
	ResourceTypes.FCNT_OL		: ResourceDescription(typeName = 'm2m:ol', virtualResourceName = 'ol', fullName='Oldest'),	# not an official type name
	ResourceTypes.GRP			: ResourceDescription(typeName = 'm2m:grp', announcedType = ResourceTypes.GRPAnnc, fullName='Group'),
	ResourceTypes.GRPAnnc 		: ResourceDescription(typeName = 'm2m:grpA', isAnnouncedResource = True, fullName='Group Announced'),
	ResourceTypes.GRP_FOPT		: ResourceDescription(typeName = 'm2m:fopt', virtualResourceName = 'fopt', fullName='Fanout Point'),	# not an official type name
	ResourceTypes.LCP			: ResourceDescription(typeName = 'm2m:lcp', announcedType = ResourceTypes.LCPAnnc, fullName='LocationPolicy'),
	ResourceTypes.LCPAnnc		: ResourceDescription(typeName = 'm2m:lcpA', isAnnouncedResource = True, fullName='LocationPolicy Announced'),
	ResourceTypes.MGMTOBJ		: ResourceDescription(typeName = 'm2m:mgo', announcedType = ResourceTypes.MGMTOBJAnnc, fullName = 'ManagementObject'),	# not an official type name
	ResourceTypes.MGMTOBJAnnc 	: ResourceDescription(typeName = 'm2m:mgoA', isAnnouncedResource = True, fullName = 'ManagementObject Announced'),				# not an official type name
	ResourceTypes.NOD			: ResourceDescription(typeName = 'm2m:nod', announcedType = ResourceTypes.NODAnnc, fullName='Node'),
	ResourceTypes.NODAnnc	 	: ResourceDescription(typeName = 'm2m:nodA', isAnnouncedResource = True, fullName='Node Announced'),
	ResourceTypes.PCH			: ResourceDescription(typeName = 'm2m:pch', fullName='PollingChannel'),
	ResourceTypes.PCH_PCU		: ResourceDescription(typeName = 'm2m:pcu', virtualResourceName = 'pcu', fullName='PollingChannel URI'),
	ResourceTypes.REQ			: ResourceDescription(typeName = 'm2m:req', isRequestCreatable = False, fullName='Request'),
	ResourceTypes.SCH			: ResourceDescription(typeName = 'm2m:sch', announcedType = ResourceTypes.SCHAnnc, fullName='Schedule'),
	ResourceTypes.SCHAnnc		: ResourceDescription(typeName = 'm2m:schA', isAnnouncedResource = True, fullName='Schedule Announced'),
	ResourceTypes.SMD			: ResourceDescription(typeName = 'm2m:smd', announcedType = ResourceTypes.SMDAnnc, fullName='SemanticDescriptor'),
	ResourceTypes.SMDAnnc		: ResourceDescription(typeName = 'm2m:smdA', isAnnouncedResource = True, fullName='SemanticDescriptor Announced'),
	ResourceTypes.SUB			: ResourceDescription(typeName = 'm2m:sub', fullName='Subscription'),
	ResourceTypes.TS 			: ResourceDescription(typeName = 'm2m:ts', announcedType = ResourceTypes.TSAnnc, fullName='TimeSeries'),
	ResourceTypes.TSAnnc		: ResourceDescription(typeName = 'm2m:tsA', isAnnouncedResource = True, fullName='TimeSeries Announced'),
	ResourceTypes.TS_LA			: ResourceDescription(typeName = 'm2m:la', virtualResourceName = 'la', fullName='Latest'),
	ResourceTypes.TS_OL			: ResourceDescription(typeName = 'm2m:ol', virtualResourceName = 'ol', fullName='Oldest'),
	ResourceTypes.TSI 			: ResourceDescription(typeName = 'm2m:tsi', announcedType = ResourceTypes.TSIAnnc, isInstanceResource = True, fullName='TimeSeriesInstance'),
	ResourceTypes.TSIAnnc		: ResourceDescription(typeName = 'm2m:tsiA', isAnnouncedResource = True, fullName='TimeSeriesInstance Announced'),
	ResourceTypes.TSB 			: ResourceDescription(typeName = 'm2m:tsb', announcedType = ResourceTypes.TSBAnnc, fullName='TimeSyncBeacon'),
	ResourceTypes.TSBAnnc 		: ResourceDescription(typeName = 'm2m:tsbA', isAnnouncedResource = True, fullName='TimeSyncBeacon Announced'),

	# ManagementObj Specializations
	ResourceTypes.ANDI			: ResourceDescription(typeName = 'm2m:andi', announcedType = ResourceTypes.ANDIAnnc, isMgmtSpecialization = True, fullName='AreaNetworkDeviceInfo'),
	ResourceTypes.ANDIAnnc		: ResourceDescription(typeName = 'm2m:andiA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='AreaNetworkDeviceInfo Announced'),
	ResourceTypes.ANI			: ResourceDescription(typeName = 'm2m:ani', announcedType = ResourceTypes.ANIAnnc, isMgmtSpecialization = True, fullName='AreaNetworkInfo'),
	ResourceTypes.ANIAnnc		: ResourceDescription(typeName = 'm2m:aniA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='AreaNetworkInfo Announced'),
	ResourceTypes.BAT			: ResourceDescription(typeName = 'm2m:bat', announcedType = ResourceTypes.BATAnnc, isMgmtSpecialization = True, fullName='Battery'),
	ResourceTypes.BATAnnc		: ResourceDescription(typeName = 'm2m:batA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='Battery Announced'),
	ResourceTypes.DATC			: ResourceDescription(typeName = 'dcfg:datc', announcedType = ResourceTypes.DATCAnnc, isMgmtSpecialization = True, fullName='DataCollection'),
	ResourceTypes.DATCAnnc		: ResourceDescription(typeName = 'dcfg:datcA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='DataCollection Announced'),
	ResourceTypes.DVC			: ResourceDescription(typeName = 'm2m:dvc', announcedType = ResourceTypes.DVCAnnc, isMgmtSpecialization = True, fullName='DeviceCapability'),
	ResourceTypes.DVCAnnc		: ResourceDescription(typeName = 'm2m:dvcA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='DeviceCapability Announced'),
	ResourceTypes.DVI			: ResourceDescription(typeName = 'm2m:dvi', announcedType = ResourceTypes.DVIAnnc, isMgmtSpecialization = True, fullName='DeviceInfo'),
	ResourceTypes.DVIAnnc		: ResourceDescription(typeName = 'm2m:dviA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='DeviceInfo Announced'),
	ResourceTypes.EVL			: ResourceDescription(typeName = 'm2m:evl', announcedType = ResourceTypes.EVLAnnc, isMgmtSpecialization = True, fullName='EventLog'),
	ResourceTypes.EVLAnnc		: ResourceDescription(typeName = 'm2m:evlA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='EventLog Announced'),
	ResourceTypes.FWR			: ResourceDescription(typeName = 'm2m:fwr', announcedType = ResourceTypes.FWRAnnc, isMgmtSpecialization = True, fullName='Firmware'),
	ResourceTypes.FWRAnnc		: ResourceDescription(typeName = 'm2m:fwrA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='Firmware Announced'),
	ResourceTypes.MEM			: ResourceDescription(typeName = 'm2m:mem', announcedType = ResourceTypes.MEMAnnc, isMgmtSpecialization = True, fullName='Memory'),
	ResourceTypes.MEMAnnc		: ResourceDescription(typeName = 'm2m:memA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='Memory Announced'),
	ResourceTypes.NYCFC			: ResourceDescription(typeName = 'm2m:nycfc', announcedType = ResourceTypes.NYCFCAnnc, isMgmtSpecialization = True, fullName='myCertFileCred'),
	ResourceTypes.NYCFCAnnc		: ResourceDescription(typeName = 'm2m:nycfctA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='myCertFileCred Announced'),
	ResourceTypes.RBO			: ResourceDescription(typeName = 'm2m:rbo', announcedType = ResourceTypes.RBOAnnc, isMgmtSpecialization = True, fullName='Reboot'),
	ResourceTypes.RBOAnnc		: ResourceDescription(typeName = 'm2m:rboA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='Reboot Announced'),
	ResourceTypes.SWR			: ResourceDescription(typeName = 'm2m:swr', announcedType = ResourceTypes.SWRAnnc, isMgmtSpecialization = True, fullName='Software'),
	ResourceTypes.SWRAnnc		: ResourceDescription(typeName = 'm2m:swrA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='Software Announced'),
	ResourceTypes.WIFIC			: ResourceDescription(typeName = 'dcfg:wific', announcedType = ResourceTypes.WIFICAnnc, isMgmtSpecialization = True, fullName='WiFi Client'),
	ResourceTypes.WIFICAnnc		: ResourceDescription(typeName = 'dcfg:wificA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='WiFi Client Announced'),

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


_ResourceTypesSupportedResourceTypes:list[ResourceTypes] = [ t
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

	positiveInteger		= auto()
	nonNegInteger		= auto()
	unsignedInt			= auto()
	unsignedLong		= auto()
	string 				= auto()
	timestamp			= auto()
	absRelTimestamp		= auto()
	list 				= auto()
	listNE 				= auto()	# Not empty list
	dict 				= auto()
	anyURI				= auto()
	boolean				= auto()
	float 				= auto()
	geoJsonCoordinate	= auto()
	integer				= auto()
	void 				= auto()
	duration 			= auto()
	any					= auto()
	complex 			= auto()
	enum	 			= auto()
	adict				= auto()	# anoymous dict structure
	base64 				= auto()
	schedule			= auto()	# scheduleEntry
	time				= timestamp	# alias type for time
	date				= timestamp	# alias type for date
	ID 					= auto()	# m2m:ID

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
		
		Attributes:
			CAR1: Mandatory.
			CAR1L: Mandatory list.
			CAR1LN: Mandatory list that shall not be empty.
			CAR01: Optional.
			CAR01L: Optional list.
			CAR1N: Mandatory but may be Null/None.
	"""
	CAR1			= auto()
	CAR1L			= auto()
	CAR1LN			= auto()
	CAR01			= auto()
	CAR01L			= auto()
	CAR1N			= auto()

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
	def isMandatory(cls, car:Cardinality) -> bool:
		"""	Check whether a Cardinality is mandatory.
		
			Args:
				car: Cardinality to check.
			Return:
				*True* if the Cardinality is of mandatory kind.
		"""
		return car in [ Cardinality.CAR1, Cardinality.CAR1L, Cardinality.CAR1LN, Cardinality.CAR1N ]

	
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

		Attributes:
			NP: Not provided.
			O: Optional.
			M: Mandatory.
	"""
	NP				= auto()
	O 				= auto()
	M 				= auto()


class Announced(ACMEIntEnum):
	""" Anouncement attribute enum values.

		Attributes:
			NA:	Not announced.
			OA: Optionally announced.
			MA: Mandatory announced.
	"""

	NA				= auto()
	"""	Not announced """
	OA				= auto()
	"""	Optionally announced """
	MA				= auto()
	"""	Mandatory announced """

##############################################################################
#
#	Evaluation Enums
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

	def isAllowedType(self, typ:BasicType) -> bool:
		# Ordered types are allowed for all operators
		if typ in [ BasicType.positiveInteger,
					BasicType.nonNegInteger,
					BasicType.unsignedInt,
					BasicType.unsignedLong,
					BasicType.timestamp,
					BasicType.absRelTimestamp,
					BasicType.float,
					BasicType.integer,
					BasicType.duration,
					BasicType.enum,
					BasicType.time,
					BasicType.date ]:
			return True
		# Equal and unequal are the only operators allowed for all other types
		if self.value in [ EvalCriteriaOperator.equal,
						   EvalCriteriaOperator.notEqual ]:
			return True
		# Not allowed
		return False



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
	"""	No permission """
	CREATE				=  1
	"""	CREATE permission """
	RETRIEVE			=  2
	"""	RETRIEVE permission """
	UPDATE				=  4
	"""	UPDATE permission """
	DELETE 				=  8
	"""	DELETE permission """
	NOTIFY 				= 16
	"""	NOTIFY permission """
	DISCOVERY			= 32
	"""	DISCOVERY permission """
	ALL					= 63
	"""	ALL permission (includes all other permissions) """

	@classmethod
	def allExcept(cls, permission:Permission) -> int:
		"""	Get a permission set without the specified permission(s).

			Args:
				permission: The permission(s) to remove from a permission.

			Return:
				The new permission without the specified *permission*, or *Permission.NONE* in case of an error. 
		"""
		p = Permission.ALL - permission
		return p if Permission.NONE <= p <= Permission.ALL else Permission.NONE


	@classmethod
	def fromBitfield(cls, bitfield:int) -> List[Permission]:
		""" Get a list of permissions from a bitfield.

			Args:
				bitfield: The bitfield to convert.

			Return:
				A list of permissions.
		"""
		if bitfield == Permission.ALL.value:
			return [ Permission.ALL ]
		return [ p for p in Permission if p != Permission.ALL and p & bitfield ]
		

##############################################################################
#
#	Operation related
#

class Operation(ACMEIntEnum):
	""" Request operations. """
	# Operations
	CREATE 				= 1
	"""	CREATE operation """
	RETRIEVE			= 2
	"""	RETRIEVE operation """
	UPDATE				= 3
	"""	UPDATE operation """
	DELETE				= 4
	"""	DELETE operation """
	NOTIFY 				= 5
	"""	NOTIFY operation """
	DISCOVERY			= -2
	"""	DISCOVERY operation (special form of a RETRIEVE operation) """
	NA 					= -1
	"""	Not applicable """


	def permission(self) -> Permission:
		""" Return the corresponding permission for an operation.
		"""
		return _OperationPermissionsMapping[self]


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


_OperationPermissionsMapping =	{	
	Operation.RETRIEVE	: Permission.RETRIEVE,
	Operation.CREATE 	: Permission.CREATE,
	Operation.UPDATE 	: Permission.UPDATE,
	Operation.DELETE 	: Permission.DELETE,
	Operation.NOTIFY 	: Permission.NOTIFY,
	Operation.DISCOVERY : Permission.DISCOVERY,
}
"""	Mappings between request operations and permissions """

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

	@classmethod
	def default(cls, op:Operation) -> ResultContentType:
		return _ResultContentTypeDefaults[op]
	


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

_ResultContentTypeDefaults = {
	Operation.RETRIEVE:	ResultContentType.attributes, 					
	Operation.DISCOVERY: ResultContentType.discoveryResultReferences,
	Operation.CREATE: ResultContentType.attributes,
	Operation.UPDATE: ResultContentType.attributes,
	Operation.DELETE: ResultContentType.nothing,
	Operation.NOTIFY: None,
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
	"""	Event Categories from m2m:stdEventCats """
	Immediate			= 2
	"""	Immediate event. """
	BestEffort			= 3
	"""	Best effort event. """
	Latest				= 4
	"""	Only latest event. """


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
	allAttributes			= 1
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
		"""	Return True if the NotificationEventType is allowed for the NotificationContentType.

			Args:
				nct: the NotificationContentType
			
			Return:
				True if the NotificationEventType is allowed for the NotificationContentType.
		"""
		match nct:
			case NotificationContentType.allAttributes:
				return self.value in [ NotificationEventType.resourceUpdate, 
									   NotificationEventType.resourceDelete, 
									   NotificationEventType.createDirectChild, 
									   NotificationEventType.deleteDirectChild ]
			case NotificationContentType.modifiedAttributes:
				return self.value in [ NotificationEventType.resourceUpdate, 
									   NotificationEventType.blockingUpdate ]
			case NotificationContentType.ri:
				return self.value in [ NotificationEventType.resourceUpdate, 
									   NotificationEventType.resourceDelete, 
									   NotificationEventType.createDirectChild, 
									   NotificationEventType.deleteDirectChild ]
			case NotificationContentType.triggerPayload:
				return self.value in [ NotificationEventType.triggerReceivedForAE ]
			case NotificationContentType.timeSeriesNotification:
				return self.value in [ NotificationEventType.reportOnGeneratedMissingDataPoints ]
			case _:
				return False


	def defaultNCT(self) -> NotificationContentType:
		"""	Return the default NotificationContentType for this NotificationEventType.

			Return:
				NotificationContentType.
		"""
		return _defaultNCT.get(self)


_defaultNCT = {
	NotificationEventType.resourceUpdate:						NotificationContentType.allAttributes,
	NotificationEventType.resourceDelete:						NotificationContentType.allAttributes,
	NotificationEventType.createDirectChild:					NotificationContentType.allAttributes,
	NotificationEventType.deleteDirectChild:					NotificationContentType.allAttributes,
	NotificationEventType.retrieveCNTNoChild:					NotificationContentType.allAttributes,
	NotificationEventType.triggerReceivedForAE:					NotificationContentType.triggerPayload,
	NotificationEventType.blockingUpdate:						NotificationContentType.modifiedAttributes,
	NotificationEventType.reportOnGeneratedMissingDataPoints:	NotificationContentType.timeSeriesNotification
}

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
	"""	Data class for a single `TS`'s latest and next expected `TSI`.dgt (data generation time) attribute, and other information """

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
		"""	Set the next expected data generation time.
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
	"""	Announcement shall be done uni-directional, ie. changes in the announced resource are not synced back."""
	BI_DIRECTIONAL = 2
	"""	Announcement shall be done bi-directional, ie. changes in the announced resource are synced back."""


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


# EXPERIMENTAL
class EventEvaluationMode(ACMEIntEnum):
	"""	Time Window Interpretation.
		This determines how events received in a time window are to be interpreted.
	"""
	ALL_EVENTS_PRESENT = 1
	"""	All events present for a `PERIODICWINDOW` or `SLIDINGWINDOW` window. This is the default. """
	ALL_OR_SOME_EVENTS_PRESENT = 2
	"""	All or some events present for a `PERIODICWINDOW` or `SLIDINGWINDOW` window."""
	ALL_OR_SOME_EVENTS_MISSING = 3
	"""	All or some events missing for a `PERIODICWINDOW` (only)."""
	ALL_EVENTS_MISSING = 4
	"""	All some events missing for a `PERIODICWINDOW` (only)."""
	SOME_EVENTS_MISSING = 5
	"""	Some events present for a `PERIODICWINDOW` or `SLIDINGWINDOW` window."""

##############################################################################
#
#	MgmtObj related
#

class Status(ACMEIntEnum):
	"""	Status of Firmware Update and Software Update.
	"""
	UNINITIALIZED = 0
	"""	Uninitialized. """
	SUCCESSFUL = 1
	"""	Successful. """
	FAILURE = 2
	"""	Failure. """
	IN_PROCESS = 3
	"""	In process. """


class WifiConnectionStatus(ACMEIntEnum):
	"""	Wifi Connection Status.
	"""
	CONNECTED = 0
	"""	Connected. """
	DISCONNECTED = 1
	"""	Disconnected. """
	IDLE = 2
	"""	Idle. """
	NO_SSID_AVAILABLE = 3
	"""	No SSID available. """
	SCAN_COMPLETED = 4
	"""	Scan completed. """
	FAILED = 5
	"""	Failed. """
	LOST = 6
	"""	Lost. """
	

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
#	LocationPolicy and GeoQuery related
#

class LocationSource(ACMEIntEnum):
	"""	Location Source.
	"""
	
	Network_based = 1
	"""	Network based. """
	Device_based = 2
	"""	Device based. """
	Sharing_based = 3
	"""	Sharing based. """


class GeofenceEventCriteria(ACMEIntEnum):
	"""	Geofence Event Criteria.
	"""
	
	Entering = 1
	"""	Entering. """
	Leaving = 2
	"""	Leaving. """
	Inside = 3
	"""	Inside. """
	Outside = 4
	"""	Outside. """
	

class LocationUpdateEventCriteria(ACMEIntEnum):
	"""	Location Update Event Criteria.
	"""
	
	Location_Change = 0
	"""	Location Change. """


class LocationInformationType(ACMEIntEnum):
	"""	Location Information Type.
	"""
	
	Position_fix = 1
	"""	Position fix. """
	Geofence_event = 2
	"""	Geofence event. """


class GeometryType(ACMEIntEnum):
	"""	Geometry Type.
	"""
	Point = 1
	"""	Point."""
	LineString = 2
	"""	LineString. """
	Polygon = 3 
	"""	Polygon. """
	MultiPoint = 4
	"""	MultiPoint. """
	MultiLineString = 5
	"""	MultiLineString. """
	MultiPolygon = 6
	"""	MultiPolygon. """

Coordinate = Tuple[float, float, Optional[float]]
""" Coordinate type. """
ListOfCoordinates = list[Coordinate]
""" List of coordinates type. """


class GeoSpatialFunctionType(ACMEIntEnum):
	"""	Geo Spatial Function Type.
	"""
	Within = 1
	"""	Within."""
	Contains = 2
	"""	Contains."""
	Intersects = 3
	"""	Intersects."""


class GeoQuery:
	"""	Geo Query.
	"""
	geometryType:GeometryType = None
	"""	Geometry Type. """
	geometry:ListOfCoordinates = []
	"""	Geometry. """
	geoSpatialFunction:GeoSpatialFunctionType = None


	
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
	dbg:Optional[str]						= None
	request:Optional[CSERequest]			= None  	# may contain the processed incoming request object
	embeddedRequest:Optional[CSERequest]	= None		# May contain a request as a response, e.g. when polling


	# def errorResultCopy(self) -> Result:
	# 	""" Copy only the rsc and dbg to a new result instance.

	# 		Return:
	# 			Result instance.
	# 	"""
	# 	return Result(status = self.status, rsc = self.rsc, dbg = self.dbg)
	

	# @classmethod
	# def errorResult(cls, rsc:Optional[ResponseStatusCode] = ResponseStatusCode.BAD_REQUEST,
	# 					 dbg:Optional[str] = '', 
	# 					 request:Optional[CSERequest] = None,
	# 					 data:Optional[Any] = None) -> Result:
	# 	"""	Create and return a `Result` object with *status* set to *False* and `ResponseStatusCode` and debug
	# 		message set.

	# 		Args:
	# 			rsc: `ResponseStatusCode` to return as an error.
	# 			dbg: String with the debug message.
	# 			request: `CSERequest` to return.
	# 		Return:
	# 			Error `Result` instance.
	# 	"""
	# 	return Result(status = False, rsc = rsc, request = request, dbg = dbg, data = data) 


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
# _successResult = Result(status = True)


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
	fu:FilterUsage = None
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

	gq:GeoQuery = None
	""" Geo query. Default is *None*. """

	aq:str = None
	""" Advanced query. Default is *None*. """


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
			The result doesn't include handling attributes, such as 'fu','lim' or 'fo' etc.
			
			Return:
				Dictionary with set Filter Criteria attributes.
		"""
		return { k:v 
				 for k, v in self.__dict__.items() 
				 if k is not None and k not in [ 'fu', 'fo', 'lim', 'ofst', 'lvl', 'arp', 'attributes' ] and v is not None
			   }


	def fillCriteriaAttributes(self) -> dict:
		"""	Create and return a dictionary with all (unfiltered) Filter Criteria attributes.
		
			Return:
				Dictionary with all attributes.
		"""
		result = {}

		def _fill(k:str, v:Any) -> None:
			"""	Callback function to fill the dictionary. 
				Filter Usage and Filter Operation are not included if they are set to their default values.

				Args:
					k: Key of the attribute.
					v: Value of the attribute.
			"""
			if k == 'fu' and int(v) == FilterUsage.conditionalRetrieval:
				return
			if k == 'fo' and int(v) == FilterOperation.AND:
				return
			result[k] = v
		
		self.mapAttributes(_fill, False)
		return result



	def mapAttributes(self, cb:Callable, flattenList:bool) -> None:
		"""	Map the standard and attribute Filter Criteria attributes.
		 	
			This method calls a callback or lambda function that can map the keys and attributes
			further.
			  
			Args:
				cb: Callback function that receives a key and its value.
				flattenList: Separate a list in multiple values or keep the list
		"""

		def _getValue(v:Any) -> Any:
			if isinstance(v, ACMEIntEnum):
				return int(v)
			return v


		# Map only the attributes that are part of the Filter Criteria
		 
		for k, v in self.__dict__.items():
			if k in [ 'attributes']:	# Handle "attributes" below
				continue
			if v is None:
				continue

			# skip default values
			# TODO combine this with the default handling in fillCriteriaAttributes()
			if k == 'fu' and int(v) == FilterUsage.conditionalRetrieval:
				continue
			if k == 'fo' and int(v) == FilterOperation.AND:
				continue

			if isinstance(v, list) and flattenList:
				for e in v:
					cb(k, _getValue(e))
			else:
				cb(k, _getValue(v))

		# Also map free filter criteria attributes
		if self.attributes:
			for k, v in self.attributes.items():
				if isinstance(v, list):
					for e in v:
						cb(k, e)
				else:
					cb(k, v)


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

	def __post_init__(self) -> None:
		"""	Post initialization actions.
		"""
		self._ot = utcTime()	# This must be done here because this is dynamic hand has to be done after the object is created, and not during the class initialization
		

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

	_rcnDefault = ResultContentType.discoveryResultReferences
	rcn:ResultContentType = None
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
	
	rset:str = None 
	""" Result Expiration Time in ISO8901 format or as ms (X-M2M-RST). """

	_rsetUTCts:float = None 	# X-M2M-RET as UTC based timestamp
	""" Result Expiration Timestamp as UTC-based timestamp (internal). """

	ot:str = None  
	"""	Originating Timestamp in ISO8901 format. """
	
	oet:str = None
	""" Operation Execution Time in ISO8901 format or as ms (X-M2M-OET). """
	
	rtu:list[str] = None
	""" The notificationURI element of the Response Type parameter(X-M2M-RTU). """

	ct:ContentSerializationType = None
	"""	Content Serialization Type. """

	ec:EventCategory = None
	"""	Event Category. """

	sqi:bool = None
	""" Semantic Query Indicator """

	ma:str = None
	"""	maxAge """

	_ma:float = None
	""" maxAge duration converted """

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

	#
	#	Helpers
	#

	_outgoing:bool = False
	""" Whether this is a request sent by the CSE. """

	_directURL:str = None
	""" The direct URL of the request. """

	_ot:float = None
	""" The timestamp when this request object was created. """



	def fillOriginalRequest(self, update:bool = False) -> None:
		"""	Create an originalRequest from at least some request attributes.
			This overwrites the internal originalRequest attribute.
		"""
		if not update or not self.originalRequest:
			self.originalRequest = {}

		if self.op:
			self.originalRequest['op'] = self.op.value
		if self.to:
			self.originalRequest['to'] = self.to
		if self.rvi:
			self.originalRequest['rvi'] = self.rvi
		if self.rqi:
			self.originalRequest['rqi'] = self.rqi
		if self.ty:
			self.originalRequest['ty'] = self.ty
		if self.originator:
			self.originalRequest['org'] = self.originator
		if self.drt and int(self.drt) != DesiredIdentifierResultType.structured:
			self.originalRequest['drt'] = self.drt
		if self.rcn and int(self.rcn) != self._rcnDefault:
			self.originalRequest['rcn'] = self.rcn
		if self.rt and int(self.rt) != ResponseType.blockingRequest:
			self.originalRequest['rt'] = self.rt
		if self.rp:
			self.originalRequest['rp'] = self.rp
		if self.vsi:
			self.originalRequest['vsi'] = self.vsi
		if self.rqet:
			self.originalRequest['rqet'] = self.rqet
		if self.ot:
			self.originalRequest['ot'] = self.ot
		if self.oet:
			self.originalRequest['oet'] = self.oet
		if self.rset:
			self.originalRequest['rset'] = self.rset
		if self.rtu:
			self.originalRequest['rtu'] = self.rtu
		# TODO is the content serialization type necessary to store? An "ct" is not the right shortname
		# if self.ct:
		# 	self.originalRequest['ct'] = self.ct
		if self.ec:
			self.originalRequest['ec'] = self.ec
		if self.sqi:
			self.originalRequest['sqi'] = self.sqi
		if self.fc and (_fc := self.fc.fillCriteriaAttributes()):
			self.originalRequest['fc'] = _fc
		elif 'fc' in self.originalRequest:
			del self.originalRequest['fc']
		if self.pc:
			self.originalRequest['pc'] = self.pc
		

	def convertToR1Target(self, targetRvi:str) -> CSERequest:
		"""	Remove the *Release Version Indicator* and the *Vendor Information*
			from a request if the request targets a target that only supports 
			release 1.

			Args:
				targetRvi: The target's supported release version.
			Return:
				A deep copy of the request, with the fields removed or set to None.
		"""
		newRequest = deepcopy(self)
		if targetRvi != '1':
			return newRequest
		if self.rvi:
			newRequest.rvi = None
		if self.vsi:
			newRequest.vsi = None
		return newRequest




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
	etype:str					= None	# name of the enum type
	lTypeName:str				= None	# sub-type of a list as writen in the definition
	evalues:dict[int, str]		= None 	# Dict of enum values and interpretations
	ptype:Type					= None	# Implementation type of the enum values

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

RequestCallback = namedtuple('RequestCallback', 'ownRequest dispatcherRequest sendRequest httpEvent mqttEvent')
RequestHandler = Dict[Operation, RequestCallback]
""" Type definition for a map between operations and handler for outgoing request operations. """

RequestResponse = namedtuple('RequestResponse', 'request result')
RequestResponseList = List[RequestResponse]

FactoryCallableT = Callable[ [ Dict[str, object], str, str, bool], object ]
"""	Type definition for a factory callback to create and initializy a Resource instance. """