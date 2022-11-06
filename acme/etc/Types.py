#
#	Types.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various CSE and oneM2M types
#

from __future__ import annotations
from dataclasses import dataclass, field, astuple
import enum
from typing import Tuple, cast, Dict, Any, List, Union
from enum import IntEnum,  auto
from http import HTTPStatus
from collections import namedtuple


class ACMEIntEnum(IntEnum):

	@classmethod
	def has(cls, value:int|str|List[int|str]|Tuple[int|str]) -> bool:
		"""	Check whether the enum type has an entry with
			either the given int value or string name. 

			`value` can also be a tuple of values to test. In this
			case, all the values in the tuple must exist
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
	def to(cls, name:str|Tuple[str], insensitive:bool=False) -> Any:
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

# TODO : Optimize tpe -> ResourceType mapping

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
	FCNT	 		= 28
	TS				= 29
	TSI   			= 30
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
	# TODO refactor this into a separate type

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
	NYCFC			= 1023	# myCertFileCred

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
	NYCFCAnnc		= -30023



	def tpe(self) -> str:
		return ResourceTypes._names[self.value] 					#  type: ignore


	def announced(self) -> ResourceTypes:
		if self.value in ResourceTypes._announcedMappings:			#  type: ignore
			return ResourceTypes._announcedMappings[self.value] 	#  type: ignore
		return ResourceTypes.UNKNOWN


	def fromAnnounced(self) -> ResourceTypes:
		"""	Get the orginal resource type for an announced type.

			Return:
				Not-announced resource type, or UNKNOWN
		"""
		for (k, v) in ResourceTypes._announcedMappings.items():		#  type: ignore
			if self.value == v:
				return k
		return ResourceTypes.UNKNOWN


	def isAnnounced(self) -> bool:
		"""	Test whether this type is an announced resource type.
		
			Return:
				True if the type is an announced resource type.
		"""
		return self.value in ResourceTypes._announcedSetFull 		# type: ignore
	
	
	def isVirtual(self) -> bool:
		"""	Test whether this type is virtual resource type.
		
			Return:
				True if the type is a virtual resource type.
		"""
		return self.value in ResourceTypes._virtualResourcesSet		#  type: ignore


	@classmethod
	def fromTPE(cls, tpe:str) -> ResourceTypes:
		try:
			return next(key for key, value in ResourceTypes._names.items() if value == tpe)	# type: ignore
		except StopIteration:
			return None


	@classmethod
	def isVirtualResource(cls, ty:int) -> bool:
		"""	Check whether `ty` is a virtual resource.
		"""
		return ty in ResourceTypes._virtualResourcesSet				#  type: ignore


	@classmethod
	def isVirtualResourceName(cls, name:str) -> bool:
		"""	Check whether `name` is the name of a virtual resource.
		"""
		return name in ResourceTypes._virtualResourcesNames			#  type: ignore
	

	@classmethod
	def isCreatorAllowed(self, ty:int) -> bool:
		"""	Check whether the type `ty` allows the 'creator' attribute.
		"""
		return ty in ResourceTypes._creatorAllowed					# type: ignore


	@classmethod
	def supportedResourceTypes(self) -> list[ResourceTypes]:
		"""	Return the supported resource types, including the 
			announced resource types.
		"""
		return ResourceTypes._supportedResourceTypes				# type: ignore


	@classmethod
	def isInstanceResource(cls, ty:int) -> bool:
		"""	Test whether this is an instance data resource type

			Args:
				ty: Type to test
			Return:
				Boolean
		"""
		return ty in ResourceTypes._instanceResourcesSet	# type: ignore


ResourceTypes._announcedMappings = {								#  type: ignore
	ResourceTypes.ACP 		: ResourceTypes.ACPAnnc,
	ResourceTypes.AE 		: ResourceTypes.AEAnnc,
	ResourceTypes.CNT		: ResourceTypes.CNTAnnc,
	ResourceTypes.CIN 		: ResourceTypes.CINAnnc,
	ResourceTypes.CSEBase 	: ResourceTypes.CSEBaseAnnc,
	ResourceTypes.GRP		: ResourceTypes.GRPAnnc,
	ResourceTypes.MGMTOBJ	: ResourceTypes.MGMTOBJAnnc,
	ResourceTypes.NOD		: ResourceTypes.NODAnnc,
	ResourceTypes.CSR		: ResourceTypes.CSRAnnc,
	ResourceTypes.FCNT		: ResourceTypes.FCNTAnnc,
	ResourceTypes.TS 		: ResourceTypes.TSAnnc,
	ResourceTypes.TSI 		: ResourceTypes.TSIAnnc,
	ResourceTypes.TSB 		: ResourceTypes.TSBAnnc,
	ResourceTypes.ACTR 		: ResourceTypes.ACTRAnnc,

	# ManagementObjs
	ResourceTypes.FWR		: ResourceTypes.FWRAnnc,
	ResourceTypes.SWR		: ResourceTypes.SWRAnnc,
	ResourceTypes.MEM		: ResourceTypes.MEMAnnc,
	ResourceTypes.ANI		: ResourceTypes.ANIAnnc,
	ResourceTypes.ANDI		: ResourceTypes.ANDIAnnc,
	ResourceTypes.BAT		: ResourceTypes.BATAnnc,
	ResourceTypes.DVI		: ResourceTypes.DVIAnnc,
	ResourceTypes.DVC		: ResourceTypes.DVCAnnc,
	ResourceTypes.RBO		: ResourceTypes.RBOAnnc,
	ResourceTypes.EVL		: ResourceTypes.EVLAnnc,
	ResourceTypes.NYCFC		: ResourceTypes.NYCFCAnnc,
}


ResourceTypes._announcedSetFull = [									#  type: ignore
	ResourceTypes.ACPAnnc, ResourceTypes.ACTRAnnc, ResourceTypes.AEAnnc, ResourceTypes.CNTAnnc,
	ResourceTypes.CINAnnc,
	ResourceTypes.CSEBaseAnnc, ResourceTypes.GRPAnnc, ResourceTypes.MGMTOBJAnnc, ResourceTypes.NODAnnc, 
	ResourceTypes.CSRAnnc, ResourceTypes.FCNTAnnc, ResourceTypes.TSAnnc, 
	ResourceTypes.TSBAnnc, ResourceTypes.TSIAnnc,

	ResourceTypes.FWRAnnc, ResourceTypes.SWRAnnc, ResourceTypes.MEMAnnc, ResourceTypes.ANIAnnc,
	ResourceTypes.ANDIAnnc, ResourceTypes.BATAnnc, ResourceTypes.DVIAnnc, ResourceTypes.DVCAnnc, 
	ResourceTypes.RBOAnnc, ResourceTypes.EVLAnnc, ResourceTypes.NYCFCAnnc,
]


# List of announceable resource types in order
ResourceTypes._announcedResourceTypes = [ 							#  type: ignore
	ResourceTypes.ACPAnnc, ResourceTypes.AEAnnc, ResourceTypes.CNTAnnc, ResourceTypes.CINAnnc,
	ResourceTypes.GRPAnnc, ResourceTypes.MGMTOBJAnnc, ResourceTypes.NODAnnc,
	ResourceTypes.CSRAnnc, ResourceTypes.FCNTAnnc, ResourceTypes.ACTRAnnc, 
	ResourceTypes.TSBAnnc
]


# Supported resource types by this CSE, including the announced resource types
ResourceTypes._supportedResourceTypes = [							#  type: ignore
	ResourceTypes.ACP, ResourceTypes.AE, ResourceTypes.CNT, ResourceTypes.CIN, 
	ResourceTypes.CSEBase, ResourceTypes.GRP, ResourceTypes.MGMTOBJ, ResourceTypes.NOD,
	ResourceTypes.PCH, ResourceTypes.CSR, ResourceTypes.REQ, ResourceTypes.SUB,
	ResourceTypes.FCNT, ResourceTypes.FCI, ResourceTypes.TS, ResourceTypes.TSI,
	ResourceTypes.TSB, ResourceTypes.ACTR,
] + ResourceTypes._announcedResourceTypes							#  type: ignore


# List of virtual resources
ResourceTypes._virtualResourcesSet = [								#  type: ignore
	ResourceTypes.CNT_LA, ResourceTypes.CNT_OL,
	ResourceTypes.FCNT_LA, ResourceTypes.FCNT_OL,
	ResourceTypes.TS_LA, ResourceTypes.TS_OL,
	ResourceTypes.GRP_FOPT,
	ResourceTypes.PCH_PCU 
]


ResourceTypes._instanceResourcesSet = [								#  type: ignore
	ResourceTypes.CIN, ResourceTypes.FCI, ResourceTypes.TSI
]


# List of possible virtual resource names
ResourceTypes._virtualResourcesNames = [							#  type: ignore
	'la', 'ol', 'fopt', 'pcu' 
]


# Mapping between oneM2M resource types to type identifies
ResourceTypes._names 	= {											# type: ignore
		ResourceTypes.UNKNOWN		: 'unknown',
		ResourceTypes.ALL 			: 'all',

		ResourceTypes.MIXED			: 'mixed',
		ResourceTypes.ACP 			: 'm2m:acp',
		ResourceTypes.ACTR			: 'm2m:actr',
		ResourceTypes.AE 			: 'm2m:ae',
		ResourceTypes.CNT			: 'm2m:cnt',
		ResourceTypes.CIN 			: 'm2m:cin',
		ResourceTypes.CSEBase		: 'm2m:cb',
		ResourceTypes.CSR 			: 'm2m:csr',
		ResourceTypes.FCI			: 'm2m:fci',				# not an official shortname
		ResourceTypes.FCNT			: 'm2m:fcnt',				# not an official shortname
		ResourceTypes.GRP			: 'm2m:grp',
		ResourceTypes.MGMTOBJ		: 'm2m:mgo',				# not an official shortname
		ResourceTypes.NOD			: 'm2m:nod',
		ResourceTypes.PCH			: 'm2m:pch',
		ResourceTypes.REQ			: 'm2m:req',
		ResourceTypes.TS 			: 'm2m:ts',
		ResourceTypes.TSB 			: 'm2m:tsb',
		ResourceTypes.TSI 			: 'm2m:tsi',
		ResourceTypes.SUB			: 'm2m:sub',

		ResourceTypes.ACPAnnc 		: 'm2m:acpA',
		ResourceTypes.ACTRAnnc 		: 'm2m:actrA',
		ResourceTypes.AEAnnc 		: 'm2m:aeA',
		ResourceTypes.CNTAnnc 		: 'm2m:cntA',
		ResourceTypes.CINAnnc 		: 'm2m:cinA',
		ResourceTypes.CSEBaseAnnc	: 'm2m:cbA',
		ResourceTypes.GRPAnnc 		: 'm2m:grpA',
		ResourceTypes.MGMTOBJAnnc 	: 'm2m:mgoA',
		ResourceTypes.NODAnnc 		: 'm2m:nodA',
		ResourceTypes.CSRAnnc 		: 'm2m:csrA',
		ResourceTypes.FCNTAnnc 		: 'm2m:fcntA',
		ResourceTypes.TSAnnc 		: 'm2m:tsA',
		ResourceTypes.TSBAnnc 		: 'm2m:tsbA',
		ResourceTypes.TSIAnnc 		: 'm2m:tsiA',

		ResourceTypes.CNT_OL		: 'm2m:ol',
		ResourceTypes.CNT_LA		: 'm2m:la',
		ResourceTypes.GRP_FOPT		: 'm2m:fopt',
		ResourceTypes.FCNT_OL		: 'm2m:ol',
		ResourceTypes.FCNT_LA		: 'm2m:la',
		ResourceTypes.PCH_PCU		: 'm2m:pcu',
		ResourceTypes.TS_OL			: 'm2m:ol',
		ResourceTypes.TS_LA			: 'm2m:la',

		# MgmtObj Specializations

		ResourceTypes.FWR			: 'm2m:fwr',
		ResourceTypes.SWR			: 'm2m:swr',
		ResourceTypes.MEM			: 'm2m:mem',
		ResourceTypes.ANI			: 'm2m:ani',
		ResourceTypes.ANDI			: 'm2m:andi',
		ResourceTypes.BAT			: 'm2m:bat',
		ResourceTypes.DVI			: 'm2m:dvi',
		ResourceTypes.DVC			: 'm2m:dvc',
		ResourceTypes.RBO			: 'm2m:rbo',
		ResourceTypes.EVL			: 'm2m:evl',
		ResourceTypes.NYCFC			: 'm2m:nycfc',

		ResourceTypes.FWRAnnc		: 'm2m:fwrA',
		ResourceTypes.SWRAnnc		: 'm2m:swrA',
		ResourceTypes.MEMAnnc		: 'm2m:memA',
		ResourceTypes.ANIAnnc		: 'm2m:aniA',
		ResourceTypes.ANDIAnnc		: 'm2m:andiA',
		ResourceTypes.BATAnnc		: 'm2m:batA',
		ResourceTypes.DVIAnnc		: 'm2m:dviA',
		ResourceTypes.DVCAnnc		: 'm2m:dvcA',
		ResourceTypes.RBOAnnc		: 'm2m:rboA',
		ResourceTypes.EVLAnnc		: 'm2m:evlA',
		ResourceTypes.NYCFCAnnc		: 'm2m:nycfcA',

	}

# List of resource types for which "creator" is allowed
# Also add later: eventConfig, statsCollect, statsConfig, semanticDescriptor,
# notificationTargetPolicy, crossResourceSubscription, backgroundDataTransfer
ResourceTypes._creatorAllowed = [ 							#  type: ignore
		ResourceTypes.ACTR, ResourceTypes.CIN, ResourceTypes.CNT, ResourceTypes.GRP, 	
		ResourceTypes.SUB, ResourceTypes.FCNT, ResourceTypes.TS 
]
	


class BasicType(ACMEIntEnum):
	""" Basic resource types """
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
	time			= timestamp	# alias type for time
	date			= timestamp	# alias type for date

	@classmethod
	def to(cls, name:str|Tuple[str], insensitive:bool=True) -> BasicType:
		return super().to(name, insensitive=insensitive)


class Cardinality(ACMEIntEnum):
	""" Resource attribute cardinalities """
	CAR1			= auto()
	CAR1L			= auto()
	CAR1LN			= auto() # mandatory list AND not empty
	CAR01			= auto()
	CAR01L			= auto()
	CAR1N			= auto() # mandatory, but may be Null/None


	@classmethod
	def hasCar(cls, name:str) -> bool:
		"""	Check whether an Cardinality without the 'car'
			prefix exists. 
			
			Example: `hasCar('01')`
		"""
		return cls.has(f'CAR{name}')
	
	
	@classmethod
	def to(cls, name:str|Tuple[str], insensitive:bool=True) -> Cardinality:

		def _prepare(name:str) -> str:
			return name if name.lower().startswith('car') else f'CAR{name}'
		
		if isinstance(name, str):
			# handle and prepare as string
			return super().to(_prepare(name), insensitive=insensitive)
		else:
			# handle and prepare as tuple of strings
			return super().to(cast(Tuple[str], tuple([ _prepare(n) for n in name ])), insensitive=insensitive)


class RequestOptionality(ACMEIntEnum):
	""" request optionalities """
	NP				= auto()
	O 				= auto()
	M 				= auto()


class Announced(ACMEIntEnum):
	""" anouncent attribute indications """
	NA				= auto()
	OA				= auto()
	MA				= auto()


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
	maxNumberOfMemberExceeded					= 6010
	invalidArguments							= 6023
	insufficientArguments						= 6024

	UNKNOWN										= -1


	def httpStatusCode(self) -> int:
		""" Map the oneM2M RSC to an http status code. """
		return ResponseStatusCode._httpStatusCodes[self.value]					# type: ignore



#
#	Mapping of oneM2M return codes to http status codes
#

ResponseStatusCode._httpStatusCodes = {																		# type: ignore
		ResponseStatusCode.OK 										: HTTPStatus.OK,						# OK
		ResponseStatusCode.deleted 									: HTTPStatus.OK,						# DELETED
		ResponseStatusCode.updated 									: HTTPStatus.OK,						# UPDATED
		ResponseStatusCode.created									: HTTPStatus.CREATED,					# CREATED
		ResponseStatusCode.accepted 								: HTTPStatus.ACCEPTED, 					# ACCEPTED
		ResponseStatusCode.acceptedNonBlockingRequestSynch 			: HTTPStatus.ACCEPTED,					# ACCEPTED FOR NONBLOCKINGREQUESTSYNCH
		ResponseStatusCode.acceptedNonBlockingRequestAsynch			: HTTPStatus.ACCEPTED,					# ACCEPTED FOR NONBLOCKINGREQUESTASYNCH
		ResponseStatusCode.badRequest								: HTTPStatus.BAD_REQUEST,				# BAD REQUEST
		ResponseStatusCode.contentsUnacceptable						: HTTPStatus.BAD_REQUEST,				# NOT ACCEPTABLE
		ResponseStatusCode.insufficientArguments 					: HTTPStatus.BAD_REQUEST,				# INSUFFICIENT ARGUMENTS
		ResponseStatusCode.invalidArguments							: HTTPStatus.BAD_REQUEST,				# INVALID ARGUMENTS
		ResponseStatusCode.maxNumberOfMemberExceeded				: HTTPStatus.BAD_REQUEST, 				# MAX NUMBER OF MEMBER EXCEEDED
		ResponseStatusCode.groupMemberTypeInconsistent				: HTTPStatus.BAD_REQUEST,				# GROUP MEMBER TYPE INCONSISTENT
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
	"""	Eval Criteria Operator """
	equal				= 1
	notEqual			= 2
	greaterThan			= 3
	lessThan			= 4
	greaterThanEqual	= 5
	lessThanEqual		= 6


class EvalMode(ACMEIntEnum):
	"""	Eval Mode """
	off					= 0
	once				= 1
	periodic			= 2
	continous 			= 3


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
	discoveryResultReferences				= 11


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
		return Operation._permissionsMapping[self.value]	#  type: ignore


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
	def toOperation(cls, v:int|None) -> Operation|None:
		"""	Convert an integer or None to an Operation. Returns an Operation or None.
		"""
		return Operation(v) if v is not None else None


# Mapping between request operations and permissions
Operation._permissionsMapping =	{				# type: ignore
	Operation.RETRIEVE	: Permission.RETRIEVE,
	Operation.CREATE 	: Permission.CREATE,
	Operation.UPDATE 	: Permission.UPDATE,
	Operation.DELETE 	: Permission.DELETE,
	Operation.NOTIFY 	: Permission.NOTIFY,
	Operation.DISCOVERY : Permission.DISCOVERY,
}


##############################################################################
#
#	ResponseType 
#

class ResponseType(ACMEIntEnum):
	"""	Reponse Types """
	nonBlockingRequestSynch		= 1
	nonBlockingRequestAsynch	= 2
	blockingRequest				= 3	# default
	flexBlocking				= 4
	noResponse					= 5
	

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
	def getType(cls, hdr:str, default:ContentSerializationType=None) -> ContentSerializationType:
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
			return self.value in [ NotificationEventType.resourceUpdate, NotificationEventType.resourceDelete, NotificationEventType.createDirectChild, NotificationEventType.deleteDirectChild ]
		elif nct == NotificationContentType.modifiedAttributes:
			return self.value in [ NotificationEventType.resourceUpdate, NotificationEventType.blockingUpdate ]
		elif nct == NotificationContentType.ri:
			return self.value in [ NotificationEventType.resourceUpdate, NotificationEventType.resourceDelete, NotificationEventType.createDirectChild, NotificationEventType.deleteDirectChild ]
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
		self.missingDataList		= []
		self.timeWindowEndTimestamp	= None
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
	""" TimeSyncBeacon criteria """
	PERIODIC = 1	# default
	LOSS_OF_SYNCHRONIZATION = 2


##############################################################################
#
#	Result and Argument and Header Data Classes
#


@dataclass
class Result:
	resource:Resource				= None		# type: ignore # Actually this is a Resource type, but have a circular import problem.
	data:Any|List[Any]|Tuple|JSON	= None 		# Anything, or list of anything, or a JSON dictionary	
	rsc:ResponseStatusCode			= ResponseStatusCode.UNKNOWN	#	The resultStatusCode of a Result
	dbg:str 						= None
	request:CSERequest				= None  	# may contain the processed incoming request object
	embeddedRequest:CSERequest 		= None		# May contain a request as a response, e.g. when polling
	status:bool 					= None


	def errorResultCopy(self) -> Result:
		""" Copy only the rsc and dbg to a new result instance.

			Return:
				Result instance.
		"""
		return Result(status = self.status, rsc = self.rsc, dbg = self.dbg)
	

	@classmethod
	def errorResult(cls, rsc:ResponseStatusCode = ResponseStatusCode.badRequest, dbg:str = '', request:CSERequest = None, data:Any = None) -> Result:
		"""	Create and return a Result object with `status = False` and RSC and debug
			message set.

			Args:
				rsc: ResponseStatusCode to return as an error.
				dbg: String with the debug message.
				request: CSERequest to return.
			Return:
				Error Result instance.
		"""
		return Result(status = False, rsc = rsc, request = request, dbg = dbg, data = data) 


	@classmethod
	def successResult(cls) -> Result:
		"""	Create and return a Result object with `status = True`.

			Return:
				Success Result instance. This is always the same Result instance!
		"""
		return _successResult


	def toData(self, ct:ContentSerializationType=None) -> str|bytes|JSON:
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
			if originalRequest.headers:
				if not self.request.headers.requestIdentifier:
					self.request.headers.requestIdentifier = originalRequest.headers.requestIdentifier
				if not self.request.headers.releaseVersionIndicator:
					self.request.headers.releaseVersionIndicator = originalRequest.headers.releaseVersionIndicator
				if not self.request.headers.vendorInformation:
					self.request.headers.vendorInformation = originalRequest.headers.vendorInformation
				if not self.request.headers.accept:
					self.request.headers.accept = originalRequest.headers.accept
				if not self.request.headers.contentType:
					self.request.headers.contentType = originalRequest.headers.contentType
				if not self.request.headers.originator:
					self.request.headers.originator = originalRequest.headers.originator
				
				# TODO more headers?
			if originalRequest.parameters:
				for k,v in originalRequest.parameters.items():	# don't overwrite existing parameters
					if k not in self.request.parameters:
						self.request.parameters[k] = v


# Result instance to be re-used all over the place
_successResult = Result(status = True)


##############################################################################
#
#	Requests
#

class RequestType(ACMEIntEnum):
	REQUEST							= auto()
	RESPONSE 						= auto()
	NOTSET	 						= auto()


@dataclass
class RequestArguments:
	fu:FilterUsage 					= FilterUsage.conditionalRetrieval
	drt:DesiredIdentifierResultType	= DesiredIdentifierResultType.structured
	fo:FilterOperation 				= FilterOperation.AND
	rcn:ResultContentType 			= ResultContentType.discoveryResultReferences
	rt:ResponseType					= ResponseType.blockingRequest 					# response type
	rp:str 							= None 											# result persistence
	rpts:str 						= None 											# ... as a timestamp (internal)
	handling:Conditions 			= field(default_factory=dict)
	conditions:Conditions 			= field(default_factory=dict)
	attributes:Parameters 			= field(default_factory=dict)


@dataclass
class RequestHeaders:
	originator:str 							= None 	# X-M2M-Origin, from
	requestIdentifier:str 					= None	# X-M2M-RI
	contentType:str 						= None	# Content-Type
	accept:list[str]						= None	# Accept
	resourceType:ResourceTypes				= None
	requestExpirationTimestamp:str 			= None 	# X-M2M-RET
	_retUTCts:float							= None 	# X-M2M-RET as UTC based timestamp
	""" request expiration timeout as UTC-based timestamp """
	resultExpirationTimestamp:str			= None 	# X-M2M-RST
	operationExecutionTime:str 				= None 	# X-M2M-OET
	releaseVersionIndicator:str 			= None 	# X-M2M-RVI
	responseTypeNUs:list[str]				= None	# X-M2M-RTU
	vendorInformation:str					= None	# X-M2M-VSI
	originatingTimestamp:str				= None  # ot in request


@dataclass
class CSERequest:
	headers:RequestHeaders 			= field(default_factory=RequestHeaders)	# always initialize with a new(!) RequestHeaders object	
	args:RequestArguments 			= field(default_factory=RequestArguments)
	ct:ContentSerializationType		= None
	originalHttpArgs:Any 			= None	# Actually a MultiDict
	originalData:bytes				= None 	# The request original data
	originalRequest:JSON			= None 	# The original request after dissection as a dictionary
	pc:JSON 						= None	# The request's primitive content as a dictionary
	id:str 							= None 	# target ID / to
	srn:str 						= None 	# target structured resource name
	to:str 							= None	# original to
	csi:str 						= None 	# target csi
	op:Operation					= None	# request operation
	rsc:ResponseStatusCode			= ResponseStatusCode.UNKNOWN	# Response Status Code
	parameters:Parameters			= field(default_factory=dict)	# Any additional parameters
	requestType:RequestType			= RequestType.NOTSET
	isResponse:bool					= False	# Default this is a request


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

	def select(self, index:int) -> Any:
		"""	Return the n-th attributes in the dataclass.

			Args:
				index: Attribute index
			Return:
				n-th attribute from the dataclass
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


Parameters=Dict[str,str]
Conditions=Dict[str, Any]
JSON=Dict[str, Any]
JSONLIST=List[JSON]
ReqResp=Dict[str, Union[int, str, List[str], JSON]]

RequestCallback = namedtuple('RequestCallback', 'ownRequest dispatcherRequest')
RequestHandler = Dict[Operation, RequestCallback]
""" Handle an outgoing request operation. """

