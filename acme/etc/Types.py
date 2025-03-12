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
import traceback, logging, sys, base64
from dataclasses import dataclass, field, astuple
from typing import Tuple, cast, Dict, Any, List, Union, Sequence, Callable, Optional, Type, TypeAlias
from enum import auto
from collections import namedtuple
from ..helpers.ACMEIntEnum import ACMEIntEnum
from ..etc.ResponseStatusCodes import ResponseStatusCode
from ..etc.DateUtils import utcTime, getResourceDate
from coapthon.defines import Content_types_numbers as CoAPContentTypesNumbers
from coapthon.defines import Content_types as CoAPContentTypes
from ..etc.Constants import RuntimeConstants as RC



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
	PRP 			= 62
	""" Primitive Profile type. """
	PRMR 			= 63
	""" ProcessManagement resource type. """
	STTE 			= 64
	"""	State resource type. """
	ACTR			= 65
	""" Action resource type. """
	DEPR			= 66
	""" Dependency resource type. """


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
	CRDS			= 1029	# credentials
	"""	Credentials ManagementObject specialization. """
	SIM 			= 1030	# SIM
	"""	SIM ManagementObject specialization. """
	MNWK			= 1031	# mobileNetwork
	"""	MobileNetwork ManagementObject specialization. """

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
	FCIAnnc 		= 10058
	"""	Announced FlexContainerInstance resource type. """
	TSBAnnc			= 10060
	"""	Announced TimeSyncBeacon resource type. """
	PRPAnnc			= 10062
	"""	Announced Primitive Profile type. """
	PRMRAnnc		= 10063
	"""	Announced ProcessManagement resource type. """
	STTEAnnc		= 10064
	"""	Announced State resource type. """
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
	CRDSAnnc		= -30029
	"""	Announced Credentials ManagementObject specialization. """
	SIMAnnc			= -30030
	"""	Announced SIM ManagementObject specialization. """
	MNWKAnnc		= -30031
	"""	Announced MobileNetwork ManagementObject specialization. """


	def typeShortname(self) -> str:
		"""	Get the resource type name.
		
			Return:
				The resource type name.
		"""
		return _ResourceTypesNames.get(self)


	def announced(self, mgd:Optional[ResourceTypes] = None) -> ResourceTypes:
		"""	Get the announced resource type for a resource type.
		
			Args:
				mgd: The mgmtObj specialization type. Only used for mgmtObjs.
			Return:
				The announced resource type, or UNKNOWN.
		"""

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
	def fromTypeShortname(cls, typeShortname:str) -> ResourceTypes:
		"""	Get a resource type by its resource name.

			Args:
				typeShortname: Type name.
			Return:
				The resource type.
		"""
		return _ResourceNamesTypes.get(typeShortname)


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
	def isContainerResource(cls, ty:int) -> bool:
		"""	Test whether a resource type is a container resource type.

			Args:
				ty: Type to test.
			Return:
				*True* if the resource type is a container resource.
		"""
		return ty in _ResourceTypesContainerResourcesSet
	

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
	
	
	def __str__(self) -> str:
		return str(int(self.value))
	
	

@dataclass()
class ResourceDescription():
	"""	Describes a resource type.
	"""
	typeName:str = None
	"""	The resource type name. """
	announcedType:ResourceTypes = None
	"""	The announced resource type. """
	isAnnouncedResource:bool= False
	"""	Whether the resource type is an announced resource type. """
	isMgmtSpecialization:bool = False
	"""	Whether the resource type is a mgmtObj specialization. """
	isInstanceResource:bool = False
	"""	Whether the resource type is an instance resource. """
	isContainer:bool = False
	"""	Whether the resource type is a container. """
	isInternalType:bool = False
	"""	Whether the resource type is an internal type. """
	virtualResourceName:str = None	# If this is set then the resource is a virtual resouce
	"""	The name of a virtual resource. """
	clazz:Resource = None 			# type:ignore [name-defined]
	"""	The resource class. """
	factory:FactoryCallableT = None
	"""	The resource factory callable to create this resource. """
	isRequestCreatable:bool = True	# Can be created by a request
	"""	Whether the resource type can be created by a request. """
	isNotificationEntity:bool = False	# Is a direct notification target
	"""	Whether the resource type is a direct notification target. """
	fullName:str = ''				# Full name of the resource type
	"""	The full name of the resource type. """
	
_ResourceTypeDetails = {
	
	# Normal resource types
	ResourceTypes.ACP 			: ResourceDescription(typeName = 'm2m:acp', announcedType = ResourceTypes.ACPAnnc, fullName = 'AccessControlPolicy'),
	ResourceTypes.ACPAnnc 		: ResourceDescription(typeName = 'm2m:acpA', isAnnouncedResource = True, fullName = 'AccessControlPolicy Announced'),
	ResourceTypes.ACTR 			: ResourceDescription(typeName = 'm2m:actr', announcedType = ResourceTypes.ACTRAnnc, fullName = 'Action'),
	ResourceTypes.ACTRAnnc		: ResourceDescription(typeName = 'm2m:actrA', isAnnouncedResource = True, fullName = 'Action Announced'),
	ResourceTypes.AE 			: ResourceDescription(typeName = 'm2m:ae', announcedType = ResourceTypes.AEAnnc, isNotificationEntity = True, fullName = 'ApplicationEntity'),
	ResourceTypes.AEAnnc		: ResourceDescription(typeName = 'm2m:aeA', isAnnouncedResource = True, fullName = 'ApplicationEntity Announced'),
	ResourceTypes.CIN 			: ResourceDescription(typeName = 'm2m:cin', announcedType = ResourceTypes.CINAnnc, isInstanceResource = True, fullName='ContentInstance'),
	ResourceTypes.CINAnnc 		: ResourceDescription(typeName = 'm2m:cinA', isAnnouncedResource = True,  isInstanceResource = True, fullName='ContentInstance Announced'),
	ResourceTypes.CNT			: ResourceDescription(typeName = 'm2m:cnt', announcedType = ResourceTypes.CNTAnnc, isContainer = True, fullName='Container'),
	ResourceTypes.CNTAnnc 		: ResourceDescription(typeName = 'm2m:cntA', isAnnouncedResource = True, isContainer = True, fullName='Container Announced'),
	ResourceTypes.CNT_LA		: ResourceDescription(typeName = 'm2m:la', virtualResourceName = 'la', isRequestCreatable = False, fullName='Latest'),
	ResourceTypes.CNT_OL		: ResourceDescription(typeName = 'm2m:ol', virtualResourceName = 'ol', isRequestCreatable = False, fullName='Oldest'),
	ResourceTypes.CRS			: ResourceDescription(typeName = 'm2m:crs', fullName='CrossResourceSubscription'),
	ResourceTypes.CSEBase 		: ResourceDescription(typeName = 'm2m:cb', announcedType = ResourceTypes.CSEBaseAnnc, isRequestCreatable = False, isNotificationEntity = True, fullName='CSEBase'),
	ResourceTypes.CSEBaseAnnc 	: ResourceDescription(typeName = 'm2m:cbA', isAnnouncedResource = True, fullName='CSEBase Announced'),
	ResourceTypes.CSR			: ResourceDescription(typeName = 'm2m:csr', announcedType = ResourceTypes.CSRAnnc, isNotificationEntity = True, fullName='RemoteCSE'),
	ResourceTypes.CSRAnnc 		: ResourceDescription(typeName = 'm2m:csrA', isAnnouncedResource = True, fullName='RemoteCSE Announced'),
	ResourceTypes.DEPR 			: ResourceDescription(typeName = 'm2m:depr',  announcedType = ResourceTypes.DEPRAnnc, fullName='Dependency'),
	ResourceTypes.DEPRAnnc		: ResourceDescription(typeName = 'm2m:deprA', isAnnouncedResource = True, fullName='Dependency Announced'),
	ResourceTypes.FCI			: ResourceDescription(typeName = 'm2m:fci', isInstanceResource = True, isRequestCreatable = False, fullName='FlexContainer Instance'),					# not an official type name
	ResourceTypes.FCIAnnc		: ResourceDescription(typeName = 'm2m:fciA', isAnnouncedResource = True, isInstanceResource = True, isRequestCreatable = False, fullName='FlexContainer Instance Announced'),	# not an official type name
	ResourceTypes.FCNT			: ResourceDescription(typeName = 'm2m:fcnt', announcedType = ResourceTypes.FCNTAnnc, isContainer = True, fullName='FlexContainer'), 	# not an official type name
	ResourceTypes.FCNTAnnc 		: ResourceDescription(typeName = 'm2m:fcntA', isAnnouncedResource = True, isContainer = True, fullName = 'FlexContainer Announced'),				# not an official type name
	ResourceTypes.FCNT_LA		: ResourceDescription(typeName = 'm2m:la', virtualResourceName = 'la', isRequestCreatable = False, fullName='Latest'),	# not an official type name
	ResourceTypes.FCNT_OL		: ResourceDescription(typeName = 'm2m:ol', virtualResourceName = 'ol', isRequestCreatable = False, fullName='Oldest'),	# not an official type name
	ResourceTypes.GRP			: ResourceDescription(typeName = 'm2m:grp', announcedType = ResourceTypes.GRPAnnc, fullName='Group'),
	ResourceTypes.GRPAnnc 		: ResourceDescription(typeName = 'm2m:grpA', isAnnouncedResource = True, fullName='Group Announced'),
	ResourceTypes.GRP_FOPT		: ResourceDescription(typeName = 'm2m:fopt', virtualResourceName = 'fopt', isRequestCreatable = False, fullName='Fanout Point'),	# not an official type name
	ResourceTypes.LCP			: ResourceDescription(typeName = 'm2m:lcp', announcedType = ResourceTypes.LCPAnnc, fullName='LocationPolicy'),
	ResourceTypes.LCPAnnc		: ResourceDescription(typeName = 'm2m:lcpA', isAnnouncedResource = True, fullName='LocationPolicy Announced'),
	ResourceTypes.MGMTOBJ		: ResourceDescription(typeName = 'm2m:mgo', announcedType = ResourceTypes.MGMTOBJAnnc, fullName = 'ManagementObject'),	# not an official type name
	ResourceTypes.MGMTOBJAnnc 	: ResourceDescription(typeName = 'm2m:mgoA', isAnnouncedResource = True, fullName = 'ManagementObject Announced'),				# not an official type name
	ResourceTypes.NOD			: ResourceDescription(typeName = 'm2m:nod', announcedType = ResourceTypes.NODAnnc, fullName='Node'),
	ResourceTypes.NODAnnc	 	: ResourceDescription(typeName = 'm2m:nodA', isAnnouncedResource = True, fullName='Node Announced'),
	ResourceTypes.PCH			: ResourceDescription(typeName = 'm2m:pch', fullName='PollingChannel'),
	ResourceTypes.PCH_PCU		: ResourceDescription(typeName = 'm2m:pcu', virtualResourceName = 'pcu', isRequestCreatable = False, fullName='PollingChannel URI'),
	ResourceTypes.PRMR			: ResourceDescription(typeName = 'm2m:prmr', announcedType = ResourceTypes.PRMRAnnc, fullName='ProcessManagement'),
	ResourceTypes.PRMRAnnc		: ResourceDescription(typeName = 'm2m:prmrA', isAnnouncedResource = True, fullName='ProcessManagement Announced'),
	ResourceTypes.PRP			: ResourceDescription(typeName = 'm2m:prp', announcedType = ResourceTypes.PRPAnnc, fullName='PrimitiveProfile'),
	ResourceTypes.PRPAnnc		: ResourceDescription(typeName = 'm2m:prpA', isAnnouncedResource = True, fullName='PrimitiveProfile Announced'),
	ResourceTypes.REQ			: ResourceDescription(typeName = 'm2m:req', isRequestCreatable = False, fullName='Request'),
	ResourceTypes.SCH			: ResourceDescription(typeName = 'm2m:sch', announcedType = ResourceTypes.SCHAnnc, fullName='Schedule'),
	ResourceTypes.SCHAnnc		: ResourceDescription(typeName = 'm2m:schA', isAnnouncedResource = True, fullName='Schedule Announced'),
	ResourceTypes.SMD			: ResourceDescription(typeName = 'm2m:smd', announcedType = ResourceTypes.SMDAnnc, fullName='SemanticDescriptor'),
	ResourceTypes.SMDAnnc		: ResourceDescription(typeName = 'm2m:smdA', isAnnouncedResource = True, fullName='SemanticDescriptor Announced'),
	ResourceTypes.STTE			: ResourceDescription(typeName = 'm2m:stte', announcedType = ResourceTypes.STTEAnnc, fullName='State'),
	ResourceTypes.STTEAnnc		: ResourceDescription(typeName = 'm2m:stteA', isAnnouncedResource = True, fullName='State Announced'),
	ResourceTypes.SUB			: ResourceDescription(typeName = 'm2m:sub', fullName='Subscription'),
	ResourceTypes.TS 			: ResourceDescription(typeName = 'm2m:ts', announcedType = ResourceTypes.TSAnnc, isContainer = True, fullName='TimeSeries'),
	ResourceTypes.TSAnnc		: ResourceDescription(typeName = 'm2m:tsA', isAnnouncedResource = True, isContainer = True, fullName='TimeSeries Announced'),
	ResourceTypes.TS_LA			: ResourceDescription(typeName = 'm2m:la', virtualResourceName = 'la', isRequestCreatable = False, fullName='Latest'),
	ResourceTypes.TS_OL			: ResourceDescription(typeName = 'm2m:ol', virtualResourceName = 'ol', isRequestCreatable = False, fullName='Oldest'),
	ResourceTypes.TSI 			: ResourceDescription(typeName = 'm2m:tsi', announcedType = ResourceTypes.TSIAnnc, isInstanceResource = True, fullName='TimeSeriesInstance'),
	ResourceTypes.TSIAnnc		: ResourceDescription(typeName = 'm2m:tsiA', isAnnouncedResource = True,  isInstanceResource = True, fullName='TimeSeriesInstance Announced'),
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
	ResourceTypes.CRDS			: ResourceDescription(typeName = 'dcfg:crds', announcedType = ResourceTypes.CRDSAnnc, isMgmtSpecialization = True, fullName='Credentials'),
	ResourceTypes.CRDSAnnc		: ResourceDescription(typeName = 'dcfg:crdsA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='Credentials Announced'),
	ResourceTypes.SIM			: ResourceDescription(typeName = 'dcfg:sim', announcedType = ResourceTypes.SIMAnnc, isMgmtSpecialization = True, fullName='SIM'),
	ResourceTypes.SIMAnnc		: ResourceDescription(typeName = 'dcfg:simA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='SIM Announced'),
	ResourceTypes.MNWK			: ResourceDescription(typeName = 'dcfg:mnwk', announcedType = ResourceTypes.MNWKAnnc, isMgmtSpecialization = True, fullName='Mobile Network'),
	ResourceTypes.MNWKAnnc		: ResourceDescription(typeName = 'dcfg:mnwkA', isAnnouncedResource = True, isMgmtSpecialization = True, fullName='Mobile Network Announced'),

	# Internal resource types
	ResourceTypes.UNKNOWN	: ResourceDescription(typeName = 'unknown', isInternalType = True),
	ResourceTypes.ALL		: ResourceDescription(typeName = 'all', isInternalType = True),
	ResourceTypes.MIXED		: ResourceDescription(typeName = 'm2m:mixed', isInternalType = True),
	ResourceTypes.REQRESP	: ResourceDescription(typeName = 'reqresp', isInternalType = True),
	ResourceTypes.COMPLEX	: ResourceDescription(typeName = 'complex', isInternalType = True),

}
"""	Mapping between resource types and their description. """


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


_ResourceTypesContainerResourcesSet = [ t
									   for t, d in _ResourceTypeDetails.items()
									   if d.isContainer ]
"""	List of container resources. """


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
	"""	Positive integer. """
	nonNegInteger		= auto()
	"""	Non-negative integer. """
	unsignedInt			= auto()
	"""	Unsigned integer. """
	unsignedLong		= auto()
	"""	Unsigned long. """
	string 				= auto()
	"""	String. """
	timestamp			= auto()
	"""	Timestamp. """
	absRelTimestamp		= auto()
	"""	Absolute or relative timestamp. """
	list 				= auto()
	"""	List. """
	listNE 				= auto()	# Not empty list
	"""	Not empty list. """
	dict 				= auto()
	"""	Dictionary or sub-structure. """
	anyURI				= auto()
	"""	Any URI. """
	boolean				= auto()
	"""	Boolean. """
	float 				= auto()
	"""	Float. """
	geoJsonCoordinate	= auto()
	"""	GeoJSON coordinate. """
	integer				= auto()
	"""	Integer. """
	void 				= auto()
	"""	Void. """
	duration 			= auto()
	"""	Duration. """
	any					= auto()
	"""	Any type. """
	complex 			= auto()
	"""	Complex type. """
	enum	 			= auto()
	"""	Enumeration. """
	adict				= auto()	# anoymous dict structure
	"""	Anonymous dictionary. """
	base64 				= auto()
	"""	Base64 encoded data. """
	schedule			= auto()	# scheduleEntry
	"""	Schedule entry. """
	jsonLike			= auto()	# JSON like structure or data types
	""" JSON like structure, list, or allowed data types. """

	# Special string types
	ID					= auto()	# m2m:ID
	"""	oneM2M ID. """
	ncname				= auto()	# xs:NCName
	"""	XML NCName. """
	imsi				= auto()	# dcfg:imsi
	"""	IMSI compliant numerical representation. """
	iccid				= auto()	# dcfg:iccid
	"""	ICCID alphanumerical representation. """
	ipv4Address			= auto()	# dcfg:ipv4Address
	"""	IPv4 address. """
	ipv6Address			= auto()	# dcfg:ipv6Address
	"""	IPv6 address. """

	# aliases. Always put at the end! Seems cause confusion with python < 3.11
	time				= timestamp	# alias type for time
	"""	Alias for timestamp. """
	date				= timestamp	# alias type for date
	"""	Alias for timestamp. """

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
	"""	Mandatory. """
	CAR1L			= auto()
	"""	Mandatory list. """
	CAR1LN			= auto()
	"""	Mandatory list that shall not be empty. """
	CAR01			= auto()
	"""	Optional. """
	CAR01L			= auto()
	"""	Optional list. """
	CAR1N			= auto()
	"""	Mandatory but may be Null/None. """

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
	"""
	NP				= auto()
	"""	Not provided. """
	O 				= auto()
	"""	Optional. """
	M 				= auto()
	"""	Mandatory. """


class Announced(ACMEIntEnum):
	""" Anouncement attribute enum values.
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
			"""	Check if the given BasicType is allowed for the current EvalCriteriaOperator.

				Args:
					typ: The BasicType to check.

				Returns:
					True if the BasicType is allowed for the current EvalCriteriaOperator, False otherwise.
			"""
			# Ordered types are allowed for all operators
			if typ in _evalCriteriaOrderedTypes:
				return True
			# Equal and unequal are the only operators allowed for all other types
			if self.value in _evalCriteriaComparisonEqualityOperators:
				return True
			# Not allowed
			return False

_evalCriteriaOrderedTypes = (
	BasicType.positiveInteger,
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
	BasicType.date,
	BasicType.string 
)
""" List of BasicTypes that are have an order. """


_evalCriteriaComparisonEqualityOperators = (
	EvalCriteriaOperator.equal,
	EvalCriteriaOperator.notEqual,
)
""" List of EvalCriteriaOperators that test for equality or inequality. """


class EvalMode(ACMEIntEnum):
	"""	Eval Mode enum values. 
	"""
	
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
	""" Permissions.
	"""
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
	def fromBitfield(cls, bitfield:AccessControlOperations) -> List[Permission]:
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


AccessControlOperations:TypeAlias = int
"""	Access Control Operations. This is a bitfield of Operation values, therefore difficult to implement as an enum. """

OperationMonitor:TypeAlias = Dict[str, Tuple[AccessControlOperations, str]]
"""	Operation Monitor. """
	

##############################################################################
#
#	Discovery & Filter
#

class ResultContentType(ACMEIntEnum):
	"""	Result Content Types """
	nothing									= 0
	"""	Nothing. """
	attributes 								= 1
	""" Resource Attributes. """
	hierarchicalAddress						= 2
	""" Hierarchical Address. """
	hierarchicalAddressAttributes			= 3
	""" Hierarchical Address and Attributes. """
	attributesAndChildResources				= 4	
	""" Attributes and Child Resources. """
	attributesAndChildResourceReferences	= 5
	""" Attributes and Child Resource References. """
	childResourceReferences					= 6
	""" Child Resource References. """
	originalResource 						= 7
	""" Original Resource. """
	childResources							= 8
	""" Child Resources. """
	modifiedAttributes						= 9
	""" Modified Attributes. """
	semanticContent							= 10
	""" Semantic Content. """
	discoveryResultReferences				= 11
	""" Discovery Result References. """
	permissions								= 12
	""" Permissions. """


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
		"""	Get the default Result Content for an operation.

			Args:
				op: The operation to get the default Result Content for.

			Return:
				The default Result Content for the operation.
		"""
		return _ResultContentTypeDefaults[op]
	


_ResultContentTypeForOperations = {
	Operation.RETRIEVE:		[ ResultContentType.attributes, 					
		   					  ResultContentType.attributesAndChildResources, 
							  ResultContentType.childResources, 
							  ResultContentType.attributesAndChildResourceReferences, 
							  ResultContentType.originalResource, 
							  ResultContentType.childResourceReferences,
							  ResultContentType.semanticContent,
							  ResultContentType.permissions],
	Operation.DISCOVERY:	[ ResultContentType.discoveryResultReferences,
							  ResultContentType.childResourceReferences ],
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
"""	Mappings between request operations and allowed Result Content """

_ResultContentTypeDefaults = {
	Operation.RETRIEVE:	ResultContentType.attributes, 					
	Operation.DISCOVERY: ResultContentType.discoveryResultReferences,
	Operation.CREATE: ResultContentType.attributes,
	Operation.UPDATE: ResultContentType.attributes,
	Operation.DELETE: ResultContentType.nothing,
	Operation.NOTIFY: None,
}
"""	Mappings between request operations and default Result Content """


	# ResultContentType.discoveryRCN = [ ResultContentType.discoveryResultReferences,		 #  type: ignore
	# 								   ResultContentType.childResourceReferences ]

class FilterOperation(ACMEIntEnum):
	"""	Filter Operation """
	AND 			= 1 # default
	""" AND. The default. """
	OR 				= 2
	""" OR. """
	XOR 			= 3
	""" XOR. """


class FilterUsage(ACMEIntEnum):
	"""	Filter Usage """
	discoveryCriteria		= 1
	"""	Discovery Criteria. """
	conditionalRetrieval	= 2 # default
	""" Conditional Retrieval. The default. """
	ipeOnDemandDiscovery	= 3
	""" IPE On-Demand Discovery. """
	discoveryBasedOperation	= 4
	""" Discovery Based Operation. """


class DesiredIdentifierResultType(ACMEIntEnum):
	""" Desired Identifier Result Type """
	structured		= 1 # default
	""" Structured. """
	unstructured	= 2
	""" Unstructured. """


##############################################################################
#
#	CSE related
#

class CSEType(ACMEIntEnum):
	""" CSE Types """
	IN					=  1
	"""	Infrastructure Node. """
	MN					=  2
	"""	Middle Node. """
	ASN					=  3
	"""	Access Node. """


class CSEStatus(ACMEIntEnum):
	"""	CSE Status """
	STOPPED				= auto()
	"""	CSE is stopped. """
	STARTING			= auto()
	"""	CSE is starting. """
	RUNNING				= auto()
	"""	CSE is running. """
	STOPPING			= auto()
	"""	CSE is stopping. """
	RESETTING			= auto()
	"""	CSE is resetting. """

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
	""" Completed. """
	FAILED				= 2
	""" Failed. """
	PENDING				= 3
	""" Pending. """
	FORWARDED			= 4
	""" Forwarded. """
	PARTIALLY_COMPLETED	= 5
	""" Partially completed. """


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
	"""	XML. """
	JSON				= auto()
	"""	JSON. """
	CBOR				= auto()
	"""	CBOR. """
	PLAIN				= auto()
	"""	Plain text. """
	UNKNOWN				= auto()
	"""	Unknown. """

	def toHttpContentType(self) -> str:
		"""	Return the http mime header for an enum value.

			Return:
				The mime header for an enum value.
		"""
		match self.value:
			case self.JSON:	
				return 'application/json'
			case self.CBOR:	
				return 'application/cbor'
			case self.XML:	
				return 'application/xml'
			case _:
				return None


	def toWSContentType(self) -> str:
		"""	Return the WebSocket content header for an enum value.

			Return:
				The mime header for an enum value.
		"""
		match self.value:
			case self.JSON:	
				return 'oneM2M.json'
			case self.CBOR:	
				return 'oneM2M.cbor'
			case self.XML:	
				return 'oneM2M.xml'
			case _:
				return None
	

	def toCoAPContentType(self) -> int:
		"""	Return the CoAP content header for an enum value.

			Return:
				The number for the CoAP content type.
		"""
		# TODO hard code values for performance reasons
		match self.value:
			case self.JSON:	
				return CoAPContentTypes['application/json']
			case self.CBOR:	
				return CoAPContentTypes['application/cbor']
			case self.XML:	
				return CoAPContentTypes['application/xml']
			case _:
				return None

		return self.toHttpContentType()
	

	def toSimple(self) -> str:
		"""	Return the simple string for an enum value.

			Return:
				The simple string for an enum value.
		"""
		match self.value:
			case self.JSON:
				return 'json'
			case self.CBOR:
				return 'cbor'
			case self.XML:
				return 'xml'
			case _:
				return None


	@classmethod
	def getType(cls, t:str|ContentSerializationType, default:Optional[ContentSerializationType] = None) -> ContentSerializationType:
		"""	Return the enum from a content-type header definition.

			Args:
				t: String to convert. If it is already an enum, it is returned as is.
				default: Default value to return if the string is not a valid content-type.

			Return:
				The enum value.
		"""
		# TODO add more of the defined oneM2M content types
		if not t:
			return cls.UNKNOWN if not default else default
		if isinstance(t, cls):
			return t
		match cast(str, t).lower():
			case 'json' | 'application/json' | 'application/vnd.onem2m-res+json':
				return cls.JSON
			case 'cbor' | 'application/cbor' | 'application/vnd.onem2m-res+cbor':
				return cls.CBOR
			case 'xml' |  'application/xml' | 'application/vnd.onem2m-res+xml':
				return cls.XML
			case _:
				return cls.UNKNOWN
	

	@classmethod
	def supportedContentSerializations(cls) -> list[str]:
		"""	Return a list of supported media types for content serialization.

			Return:
				A list of supported media types for content serialization.
		"""
		return [ 'application/json',
				 'application/vnd.onem2m-res+json', 
				 'application/cbor',
				 'application/vnd.onem2m-res+cbor' ]


	@classmethod
	def supportedContentSerializationsWS(cls) -> Sequence[str]:
		"""	Return a list of supported media types for content serialization
			for WebSocket communication.

			Return:
				A list of supported media types for content serialization.
		"""
		return [ 'oneM2M.json', 'oneM2M.cbor' ]


	@classmethod
	def fromWebSocketSubProtocol(cls, t:str) -> ContentSerializationType:
		"""	Return the enum from a string for a content serialization.

			Args:
				t: String to convert.

			Return:
				The enum value.
		"""
		match t:
			case 'oneM2M.json':
				return cls.JSON
			case 'oneM2M.cbor':
				return cls.CBOR
			case 'oneM2M.xml':
				return cls.XML
			case _:
				return cls.UNKNOWN


	@classmethod
	def fromCoAP(cls, t:int) -> ContentSerializationType:
		"""	Return the enum from a string for a content serialization.

			Args:
				t: content type number to convert

			Return:
				The enum value.
		"""
		match t:
			case 41 | 10014 | 10002 | 10006 | 10008 | 10014 | 10016:
				return cls.XML
			case 50 | 10001 | 10003 | 10007 | 10009 | 10015:
				return cls.JSON
			case 60 | 10010 | 10011 | 10012 | 10013:
				return cls.CBOR
			case _:
				return cls.UNKNOWN
			

	@classmethod
	def supportedContentSerializationsSimple(cls) -> list[str]:
		"""	Return a simplified (only the names of the serializations)
			list of supported media types for content serialization.

			Return:
				A list of supported media types for content serialization.
		"""
		return [ cls.JSON.toSimple(), cls.CBOR.toSimple() ]


	def __eq__(self, other:object) -> bool:
		"""	Compare two ContentSerializationType enums for equality.

			Args:
				other: The other enum to compare with.

			Return:
				True if the enums are equal.
		"""
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
	""" Abandon member. The default. """
	abandonGroup		= 2
	""" Abandon group. """
	setMixed			= 3
	""" Set mixed. """


##############################################################################
#
#	Subscription related
#

class NotificationContentType(ACMEIntEnum):
	"""	Notification Content Types """
	allAttributes			= 1
	""" All Attributes. """
	modifiedAttributes		= 2
	""" Modified Attributes. """
	ri 						= 3
	""" Resource Identifier. """
	triggerPayload			= 4
	""" Trigger Payload. """
	timeSeriesNotification	= 5
	""" Time Series Notification. """
	

class NotificationEventType(ACMEIntEnum):
	""" eventNotificationCriteria/NotificationEventTypes """

	notSet								=  0
	""" Not Set (0). """
	resourceUpdate						=  1 # A, default
	""" Resource Update (1) - the default."""
	resourceDelete						=  2 # B
	""" Resource Delete (2). """
	createDirectChild					=  3 # C
	""" Create Direct Child (3). """
	deleteDirectChild					=  4 # D	
	""" Delete Direct Child (4). """
	retrieveCNTNoChild					=  5 # E # TODO not supported yet
	""" Retrieve CNT No Child (5). """
	triggerReceivedForAE				=  6 # F # TODO not supported yet
	""" Trigger Received For AE (6). """
	blockingUpdate 						=  7 # G
	""" Blocking Update (7). """
	# TODO spec and implementation for blockingUpdateDirectChild			=  ???
	reportOnGeneratedMissingDataPoints	=  8 # H
	""" Report On Generated Missing Data Points (8). """
	blockingRetrieve					=  9 # I # EXPERIMENTAL
	""" Blocking Retrieve (9). """
	blockingRetrieveDirectChild			= 10 # J # EXPERIMENTAL
	""" Blocking Retrieve Direct Child (10). """


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
"""	Mappings between NotificationEventType and default NotificationContentType """

##############################################################################
#
#	TimeSeries related
#

@dataclass
class MissingData:
	"""	Data class for collecting the missing data states. """ 

	subscriptionRi:str
	""" Subscription resource identifier. """
	missingDataDuration:float
	""" Missing data duration. """
	missingDataNumber:int
	""" Missing data number. """
	timeWindowEndTimestamp:float	= None
	""" Time window end timestamp. """
	missingDataList:list[str]		= field(default_factory=list)
	""" Missing data list. """
	missingDataCurrentNr:int 		= 0
	""" Missing data current number. """

	def clear(self) -> None:
		"""	Clear the missing data states.
		"""
		
		self.timeWindowEndTimestamp	= None
		self.clearMissingDataList()


	def clearMissingDataList(self) -> None:
		"""	Clear the missing data list.
		"""

		self.missingDataList		= []
		self.missingDataCurrentNr	= 0

	
	def asDict(self) -> JSON:
		"""	Return the missing data as a dictionary.

			Return:
				The missing data as a dictionary.
		"""
		return {
			'mdlt': self.missingDataList,
			'mdc' : self.missingDataCurrentNr
		}



@dataclass
class LastTSInstance:
	"""	Data class for a single `TS`'s latest and next expected `TSI`.dgt (data generation time) attribute, and other information """

	# runtime attributes
	dgt:list[float]						= field(default_factory = lambda: [0])
	""" List of data generation times. """
	expectedDgt:float				 	= 0.0
	""" Expected data generation time. """
	missingDataDetectionTime:float		= 0.0
	""" Missing data detection time. """

	# <TS> attributes
	pei:float							= 0.0
	""" Periodic interval. """
	mdt:float							= 0.0
	""" Missing data detection time. """
	peid:float							= 0.0
	""" Periodic interval duration. """

	# Subscriptions
	missingData:dict[str, MissingData]	= field(default_factory = dict)
	""" Missing data. """

	# Internal
	actor:BackgroundWorker				= None	#type:ignore[name-defined] # actor for this TS 
	""" Actor for this TS."""
	running:bool 						= False # for late activation of this 
	""" Running. """


	def prepareNextDgt(self) -> None:
		"""	Set the next expected data generation time.
		"""
		self.expectedDgt += self.pei
	

	def prepareNextRun(self) -> None:
		"""	Set the next missingDataDetectionTime.
		"""
		self.missingDataDetectionTime += self.pei # mdt?
	

	def addDgt(self, dgt:float) -> None:
		"""	Add a data generation time to the list of data generation times.

			Args:
				dgt: The data generation time to add.
		"""
		# TODO really support list. currently only one dgt is put, but 
		# always overrides the old one. 
		# Also change declaration of dgt above
		if len(self.dgt) == 0:
			self.dgt.append(dgt)
		else:
			self.dgt[0] = dgt
	

	def nextDgt(self) -> float:
		"""	Get the next expected data generation time.

			Return:
				The next expected data generation time.
		"""
		if len(self.dgt) == 0:
			return None
		return self.dgt.pop(0)
	

	def hasDgt(self) -> bool:
		"""	Check if there is a data generation time.

			Return:
				True if there is a data generation time.
		"""
		return len(self.dgt) > 0
	

	def clearDgt(self) -> None:
		"""	Clear the data generation time.

			Return:
				True if there is a data generation time.
		"""
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
"""	Mappings between semantic formats and strings representations. """


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


##############################################################################
#
#	ProcessManagement related
#

class ProcessState(ACMEIntEnum):
	"""	ProcessManager Process States.
	"""
	Disabled = 1
	"""	Disabled. """
	Enabled = 2
	"""	Enabled. """
	Activated = 3
	"""	Activated. """
	Paused = 4
	"""	Paused. """
	Completed = 5
	"""	Completed. """
	Aborted = 6
	"""	Aborted. """


class ProcessControl(ACMEIntEnum):
	"""	ProcessManager Process Control
	"""
	Enable = 1
	"""	Enable. """
	Disable = 2
	"""	Disable. """
	Pause = 3
	"""	Pause. """
	Reactivate = 4
	"""	Reactivate. """


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
	""" Resource instance. """
	data:Any|Sequence[Any]|Tuple|JSON|str	= None 		# Anything, or list of anything, or a JSON dictionary	
	""" Data. """
	rsc:ResponseStatusCode					= ResponseStatusCode.UNKNOWN	#	The responseStatusCode of a Result
	""" ResponseStatusCode. """
	dbg:Optional[str]						= None
	""" Optional debug message. """
	request:Optional[CSERequest]			= None  	# may contain the processed incoming request object
	""" Optional `CSERequest`. """
	embeddedRequest:Optional[CSERequest]	= None		# May contain a request as a response, e.g. when polling
	""" Optional embedded `CSERequest`. """


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
		"""	Return the result data as a string or bytes or JSON.

			Args:
				ct: The content serialization type to use. If not given, the default serialization type is used.

			Return:
				The result data as a string or bytes or JSON.
		"""
		from ..resources.Resource import Resource
		from ..etc.RequestUtils import serializeData

		# determine the default serialization type if none was given
		ct = RC.defaultSerialization if not ct else ct

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


	def prepareResultFromRequest(self, originalRequest:CSERequest) -> Result:
		"""	Copy the necessary fields from an original request. Existing
			fields will not be overwritten.

			This can be used to prepare a response from a request.

			Args:
				originalRequest: The original request to copy from.

			Return:
				Self.
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
			if not self.request.originator:
				self.request.originator = originalRequest.originator
			if not self.request.ec:
				self.request.ec = originalRequest.ec
			if not self.request.rset:
				self.request.rset = originalRequest.rset
		
			# Add Originating Timestamp if present in the original request
			if originalRequest.ot:
				self.request.ot = getResourceDate()

			# Copy request ID
			if originalRequest.rqi:
				self.request.rqi = originalRequest.rqi
		
		return self


	@classmethod
	def exceptionToResult(self, e:Exception) -> Result:
		"""	Transform a Python exception to a result.
	
			Args:
				e: Exception
			Return:
				Result object, with "rsc" set to internal server error, and "dbg" to the exception message.
		"""
		from ..runtime.Logging import Logging
		tb = traceback.format_exc()
		Logging.logErr(tb, exc=e)
		tbs = tb.replace('"', '\\"').replace('\n', '\\n')
		return Result(rsc = ResponseStatusCode.INTERNAL_SERVER_ERROR, dbg = f'encountered exception: {tbs}')
	

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

	gmty:GeometryType = None
	""" geometryType for geo-query. Default is *None*. """

	geom:str = None
	""" geometry for geo-query. Default is *None*. """

	_geom:list = None
	""" Internal attribute to hold a parsed geometry. Default is *None*."""

	gsf:GeoSpatialFunctionType = None
	""" geoSpatialFunction for geo-query. Default is *None*. """


	aq:str = None	# EXPERIMENTAL
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
				 if k is not None and k not in ( 'fu', 'fo', 'lim', 'ofst', 'lvl', 'arp', 'attributes', 'gmty', 'geom', '_geom', 'gsf' ) and v is not None
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
			if k.startswith('_'):	# internal attributes
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
class RequestCredentials:
	"""	Structure that holds the credentials for a request.
	"""

	httpUsername:Optional[str] = None
	"""	Username for HTTP basic authentifcation. """

	httpPassword:Optional[str] = None
	"""	Password for HTTP basic authentication. """

	httpToken:Optional[str] = None
	"""	Token for HTTP bearer token authentication. """


	wsUsername:Optional[str] = None
	"""	Username for WebSockets HTTP basic authentifcation. """

	wsPassword:Optional[str] = None
	"""	Password for WebSockets HTTP basic authentication. """

	wsToken:Optional[str] = None
	"""	Token for WebSockets HTTP bearer token authentication. """


	def getHttpBasic(self) -> str:
		"""	Return the HTTP basic authentication string.
			
			Return:
				The HTTP basic authentication string as base64 encoded string.
		"""
		creds = f'{self.httpUsername}:{self.httpPassword}'
		return base64.b64encode(creds.encode("utf-8")).decode("utf-8")
	

	def getHttpBearerToken(self) -> str:
		"""	Return the HTTP bearer token string.
			
			Return:
				The HTTP bearer token string.
		"""
		return f'Bearer {self.httpToken}'
	
	
	def getWsBasic(self) -> str:
		"""	Return the WebSockets basic authentication string.
			
			Return:
				The WebSockets basic authentication string as base64 encoded string.
		"""
		creds = f'{self.wsUsername}:{self.wsPassword}'
		return f'Basic {base64.b64encode(creds.encode("utf-8")).decode("utf-8")}'
	

	def getWsBearerToken(self) -> str:
		"""	Return the WebSockets bearer token string.
			
			Return:
				The WebSockets bearer token string.
		"""
		return f'Bearer {self.wsToken}'
	

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
	to:Optional[str] = None
	"""	The request's original target. """

	id:Optional[str] = None
	""" Target resource ID. Might be structured or unstructured. Based on the value of `to`. """

	srn:Optional[str] = None
	""" The target's structured resource ID. Might not be present in a request. Based on the value of `to`. """
	
	csi:Optional[str] = None
	""" The CSE-ID of the target's hosting CSI. Might not be present in a request. Based on the value of `to`. """

	# Request attributes
	op:Optional[Operation] = None
	"""	Request Operation. """

	originator:Optional[str] = None 
	"""	Request originator (from, X-M2M-Origin). """

	rsc:ResponseStatusCode = ResponseStatusCode.UNKNOWN
	""" Response Status Code. """

	rqi:Optional[str] = None
	"""	Request Identifier (X-M2M-RI). """
	
	rvi:Optional[str] = None
	"""	Release Version Identifier (X-M2M-RVI). """
	
	ty:Optional[ResourceTypes] = None
	""" Resource type. """

	drt:DesiredIdentifierResultType	= DesiredIdentifierResultType.structured
	"""	Desired Indentifier Result Type (default: structured). """

	_rcnDefault = ResultContentType.discoveryResultReferences
	rcn:Optional[ResultContentType] = None
	""" Result Content Type. """

	rt:ResponseType = ResponseType.blockingRequest
	""" Response Type (default: blocking request)."""

	rp:Optional[str] = None
	""" Result Persistence. """

	_rpts:Optional[str] = None
	""" Internal: Result Persistence (rp) as a timestamp. """

	vsi:Optional[str] = None
	"""	Vendor Information (X-M2M-VSI). """
	
	rqet:Optional[str] = None
	"""	Request Expiration Timestamp in ISO8901 format (X-M2M-RET). """
	
	_rqetUTCts:Optional[float] = None 	# X-M2M-RET as UTC based timestamp
	""" Request Expiration Timestamp as UTC-based timestamp (internal). """
	
	rset:Optional[str] = None 
	""" Result Expiration Time in ISO8901 format or as ms (X-M2M-RST). """

	_rsetUTCts:Optional[float] = None 	# X-M2M-RET as UTC based timestamp
	""" Result Expiration Timestamp as UTC-based timestamp (internal). """

	ot:Optional[str] = None  
	"""	Originating Timestamp in ISO8901 format. """
	
	oet:Optional[str] = None
	""" Operation Execution Time in ISO8901 format or as ms (X-M2M-OET). """
	
	rtu:Optional[list[str]] = None
	""" The notificationURI element of the Response Type parameter(X-M2M-RTU). """

	ct:Optional[ContentSerializationType] = None
	"""	Content Serialization Type. """

	ec:Optional[EventCategory] = None
	"""	Event Category. """

	sqi:Optional[bool] = None
	""" Semantic Query Indicator """

	ma:Optional[str] = None
	"""	maxAge """

	_ma:Optional[float] = None
	""" maxAge duration converted """

	pc:Optional[JSON] = None
	""" The request's primitive content as a dictionary. """
	
	# Generics, internals
	originalData:Optional[bytes] = None 
	""" The request's original data. """

	originalRequest:Optional[JSON] = None
	""" The original request after dissection as a dictionary. """

	requestType:RequestType	= RequestType.NOTSET
	""" The struture is for a request or a response. """

	selectedAttributes:list[str] = field(default_factory = list)
	""" Selected attributes that filter the resource attributes in the response. This list refers to the resource attributes, ie. one level below the resource. """

	#
	#	HTTP specifics
	#

	httpAccept:Optional[list[str]] = None
	"""	http Accept header media type. """

	#
	#	CoAP specifics
	#

	coapAccept:Optional[ContentSerializationType] = None
	""" CoAP Accept Option media type. """


	#
	#	Helpers
	#

	_outgoing:bool = False
	""" Whether this is a request sent by the CSE. """

	_directURL:Optional[str] = None
	""" The direct URL of the request. """

	_ot:Optional[float] = None
	""" The timestamp when this request object was created. """

	_attributeList:list[str] = None
	""" List of attribute names if this is a partial request. Otherwise not set. """

	credentials:Optional[RequestCredentials] = None
	""" Request credentials for HTTP, WebSockets etc. """

	rq_authn:bool = False
	""" Whether the request is authenticated. See TS-0003, clause 7.1.2. """



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
	"""	Attribute policy for a single resource attribute.
	"""
	
	# !!! DON'T CHANGE the order of the attributes!

	type:BasicType
	""" Type of the attribute. """
	cardinality:Cardinality
	""" Cardinality of the attribute. """
	optionalCreate:RequestOptionality
	""" Optionality of the attribute for create requests. """
	optionalUpdate:RequestOptionality
	""" Optionality of the attribute for update requests. """
	optionalDiscovery:RequestOptionality
	""" Optionality of the attribute for discovery requests. """
	announcement:Announced
	""" Whether the attribute is announced. """
	sname:str 					= None 	# short name
	""" Short name of the attribute. """
	lname:str 					= None	# longname
	""" Long name of the attribute. """
	namespace:str				= None	# namespace
	""" Namespace of the attribute. """
	typeShortname:str   					= None	# namespace:type name
	""" Type name of the attribute. """
	rtypes:List[ResourceTypes]	= None	# Optional list of multiple resourceTypes
	""" List of resource types that this attribute is valid for. """
	ctype:str					= None	# Definition for a complex type attribute
	""" Definition name for a complex type attribute. """
	typeName:str				= None	# The type as written in the definition
	""" The type as written in the definition. """
	fname:str					= None 	# Name of the definition file
	""" Name of the definition file. """
	ltype:BasicType				= None	# sub-type of a list
	""" Sub-type of a list as writen in the definition. """
	etype:str					= None	# name of the enum type
	""" Name of the enum type (if the attribute is of type *enum*). """
	lTypeName:str				= None	# sub-type of a list as writen in the definition
	""" Sub-type of a list as writen in the definition. """
	evalues:dict[int, str]		= None 	# Dict of enum values and interpretations
	""" Dict of enum values and interpretations. """
	ptype:Type					= None	# Implementation type of the enum values
	""" Implementation type of the enum values. """

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


AttributePolicyDict:TypeAlias = Dict[str, AttributePolicy]
"""	Represent a dictionary of attribute policies used in validation. """

ResourceAttributePolicyDict:TypeAlias = Dict[Tuple[Union[ResourceTypes, str], str], AttributePolicy]
"""	Represent a dictionary of attribute policies used in validation. """

FlexContainerAttributes:TypeAlias = Dict[str, Dict[str, AttributePolicy]]
""" Type definition for a dictionary of attribute policies for a flexContainer. """

FlexContainerSpecializations:TypeAlias = Dict[str, Tuple[str, str]]
""" Type definition for a dictionary of specializations for a flexContainer. """


##############################################################################
#
#	Generic Types
#

class LogLevel(ACMEIntEnum):
	"""	Log levels.

		These are the standard log levels, plus an additional *OFF* level.
	"""
	INFO 	= logging.INFO
	"""	Info level. """

	DEBUG 	= logging.DEBUG
	"""	Debug level. """

	ERROR 	= logging.ERROR
	"""	Error level. """

	WARNING = logging.WARNING
	"""	Warning level. """

	OFF		= sys.maxsize
	"""	Off level. """
	

	def next(self) -> LogLevel:
		"""	Return next log level. This cycles through the levels.
		"""
		return {
			LogLevel.DEBUG:		LogLevel.INFO,
			LogLevel.INFO:		LogLevel.WARNING,
			LogLevel.WARNING:	LogLevel.ERROR,
			LogLevel.ERROR:		LogLevel.OFF,
			LogLevel.OFF:		LogLevel.DEBUG,
		}[self]


	@classmethod
	def toLogLevel(cls, logLevel:str) -> Optional[LogLevel]:
		"""	Convert a string to a log level.

			Args:
				logLevel: String representation of a log level.

			Return:
				Log level or *None*.
		"""

		logLevel = logLevel.lower()
		# logLevel = (Configuration._argsLoglevel or logLevel) 	# command line args override config
		match logLevel:
			case 'off':
				return LogLevel.OFF
			case 'info':
				return LogLevel.INFO
			case 'warn' | 'warning':
				return LogLevel.WARNING
			case 'error':
				return LogLevel.ERROR
			case 'debug':
				return LogLevel.DEBUG
			case _:
				return None


class BindingType(ACMEIntEnum):
	""" Type of Binding connection.
	"""
	UNKNOWN = auto()
	""" No binding. """
	HTTP = auto()
	"""	HTTP. """
	COAP = auto()
	"""	COAP. """
	MQTT = auto()
	"""	MQTT. """
	WS = auto()
	"""	WebSockets. """


class AuthorizationResult(ACMEIntEnum):
	""" Type of internal Authorization evaluation.
	"""
	NOTSET = auto()
	""" Authorization is unknown. May be even not enabled. """
	AUTHORIZED = auto()
	"""	Authorization is granted. """
	UNAUTHORIZED = auto()
	"""	Authorization is denied. """


class TreeMode(ACMEIntEnum):
	""" Available modes do display the resource tree in the console.
	"""

	NORMAL				= auto()
	"""	Mode - Normal """

	CONTENT				= auto()
	""" Mode - Show content """

	COMPACT				= auto()
	""" Mode - Compact """

	CONTENTONLY			= auto()
	"""	Mode - Content only """


	def __str__(self) -> str:
		"""	String representation of the TreeMode.

			Return:
				String representation.
		"""
		return self.name


	def succ(self) -> TreeMode:
		"""	Return the next enum value, and cycle to the beginning when reaching the end.

			Return:
				TreeMode value.
		"""
		members:list[TreeMode] = list(self.__class__)
		index = members.index(self) + 1
		return members[index] if index < len(members) else members[0]
	

	# @classmethod
	# def to(cls, t:str) -> TreeMode:
	# 	"""	Return the enum from a string.

	# 		Args:
	# 			t: String representation of an enum value.

	# 		Return:
	# 			Enum value or *None*.
	# 	"""
	# 	return dict(cls.__members__.items()).get(t.upper())


	@classmethod
	def names(cls) -> list[str]:
		"""	Return all the enum names.

			Return:
				List of enum value.
		"""
		return list(cls.__members__.keys())
	

Parameters:TypeAlias = Dict[str, str]
"""	Type definition for a dictionary of parameters. """
JSON:TypeAlias = Dict[str, Any]
"""	Type definition for a JSON type, which is just a dictionary. """
JSONLIST:TypeAlias = List[JSON]
"""	Type definition for a list of JSON types. """
ReqResp:TypeAlias = Dict[str, Union[int, str, List[str], JSON]]
"""	Type definition for a dictionary of request/response parameters. """

RequestCallback = namedtuple('RequestCallback', 'ownRequest dispatcherRequest sendRequest coapEvent httpEvent mqttEvent wsEvent')
""" Type definition for a callback function to handle outgoing requests. """
RequestHandler:TypeAlias = Dict[Operation, RequestCallback]
""" Type definition for a map between operations and handler for outgoing request operations. """

RequestResponse = namedtuple('RequestResponse', 'request result')
""" Type definition for a request/response pair. """
RequestResponseList:TypeAlias = List[RequestResponse]
""" Type definition for a list of request/response pairs. """

FactoryCallableT:TypeAlias = Callable[ [ Dict[str, object], str, bool], object ]
"""	Type definition for a factory callback to create and initializy a Resource instance. """


