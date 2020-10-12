#
#	Types.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various CSE and oneM2M types
#

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List
from enum import IntEnum, Enum, auto
from flask import Request


#
#	Resource Types
#

class ResourceTypes(IntEnum):

	UNKNOWN		= -1

	# Resource Types

	MIXED		=  0
	ACP 		=  1
	AE			=  2
	CNT			=  3
	CIN 		=  4
	CSEBase 	=  5
	GRP 		=  9
	MGMTOBJ		= 13
	NOD			= 14
	PCH 		= 15
	CSR			= 16
	REQ 		= 17
	SUB			= 23
	FCNT	 	= 28
	FCI 		= 58


	# Virtual resources (proprietary resource types)

	CNT_OL		=  -20001
	CNT_LA		=  -20002
	GRP_FOPT	=  -20003
	FCNT_OL		=  -20004
	FCNT_LA		=  -20005
	PCH_PCU		=  -20006

	# <mgmtObj> Specializations

	FWR			= 1001
	SWR			= 1002
	MEM			= 1003
	ANI			= 1004
	ANDI		= 1005
	BAT			= 1006
	DVI 		= 1007
	DVC 		= 1008
	RBO 		= 1009
	EVL 		= 1010
	NYCFC		= 1023	# myCertFileCred

	# Announced Resources

	ACPAnnc 	= 10001
	AEAnnc 		= 10002	
	CNTAnnc 	= 10003
	CINAnnc 	= 10004
	GRPAnnc 	= 10009
	MGMTOBJAnnc = 10013
	NODAnnc 	= 10014
	CSRAnnc 	= 10016
	FCNTAnnc 	= 10028
	FCIAnnc 	= 10058

	FWRAnnc		= -30001
	SWRAnnc		= -30002
	MEMAnnc		= -30003
	ANIAnnc		= -30004
	ANDIAnnc	= -30005
	BATAnnc		= -30006
	DVIAnnc		= -30007
	DVCAnnc		= -30008
	RBOAnnc		= -30009
	EVLAnnc		= -30010
	NYCFCAnnc	= -30023


	def tpe(self) -> str:
		return ResourceTypes._names[self.value] 				#  type: ignore


	def announced(self) -> ResourceTypes:
		if self.value in ResourceTypes._announcedMappings:		#  type: ignore
			return ResourceTypes._announcedMappings[self.value] 	#  type: ignore
		return ResourceTypes.UNKNOWN


	def announcedMgd(self, mgd:int) -> ResourceTypes:
		if mgd in ResourceTypes._announcedMappingsMGD:		#  type: ignore
			return ResourceTypes._announcedMappingsMGD[mgd] 	#  type: ignore
		return ResourceTypes.UNKNOWN


	def isAnnounced(self) -> bool:
		return self.value in ResourceTypes._announcedSet 		# type: ignore



ResourceTypes._announcedMappings = {							#  type: ignore
	ResourceTypes.ACP 		: ResourceTypes.ACPAnnc,
	ResourceTypes.AE 		: ResourceTypes.AEAnnc,
	ResourceTypes.CNT		: ResourceTypes.CNTAnnc,
	ResourceTypes.CIN 		: ResourceTypes.CINAnnc,
	ResourceTypes.GRP		: ResourceTypes.GRPAnnc,
	ResourceTypes.MGMTOBJ	: ResourceTypes.MGMTOBJAnnc,
	ResourceTypes.NOD		: ResourceTypes.NODAnnc,
	ResourceTypes.CSR		: ResourceTypes.CSRAnnc,
	ResourceTypes.FCNT		: ResourceTypes.FCNTAnnc,
	ResourceTypes.FCI		: ResourceTypes.FCIAnnc,
}


ResourceTypes._announcedMappingsMGD = {							#  type: ignore
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

ResourceTypes._announcedSet = [									#  type: ignore
	ResourceTypes.ACPAnnc, ResourceTypes.AEAnnc, ResourceTypes.CNTAnnc, ResourceTypes.CINAnnc,
	ResourceTypes.GRPAnnc, ResourceTypes.MGMTOBJAnnc, ResourceTypes.NODAnnc, 
	ResourceTypes.CSRAnnc, ResourceTypes.FCNTAnnc, ResourceTypes.FCIAnnc,

	ResourceTypes.FWRAnnc, ResourceTypes.SWRAnnc, ResourceTypes.MEMAnnc, ResourceTypes.ANIAnnc,
	ResourceTypes.ANDIAnnc, ResourceTypes.BATAnnc, ResourceTypes.DVIAnnc, ResourceTypes.DVCAnnc, 
	ResourceTypes.RBOAnnc, ResourceTypes.EVLAnnc, ResourceTypes.NYCFCAnnc,
]


ResourceTypes._names 	= {										# type: ignore
		ResourceTypes.UNKNOWN		: 'unknown',

		ResourceTypes.MIXED			: 'mixed',
		ResourceTypes.ACP 			: 'm2m:acp',
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
		ResourceTypes.SUB			: 'm2m:sub',

		ResourceTypes.ACPAnnc 		: 'm2m:acpA',
		ResourceTypes.AEAnnc 		: 'm2m:aeA',
		ResourceTypes.CNTAnnc 		: 'm2m:cntA',
		ResourceTypes.CINAnnc 		: 'm2m:cinA',
		ResourceTypes.GRPAnnc 		: 'm2m:grpA',
		ResourceTypes.MGMTOBJAnnc 	: 'm2m:mgoA',
		ResourceTypes.NODAnnc 		: 'm2m:nodA',
		ResourceTypes.CSRAnnc 		: 'm2m:csrA',
		ResourceTypes.FCNTAnnc 		: 'm2m:fcntA',
		ResourceTypes.FCIAnnc 		: 'm2m:fciA',

		ResourceTypes.CNT_OL		: 'm2m:ol',
		ResourceTypes.CNT_LA		: 'm2m:la',
		ResourceTypes.GRP_FOPT		: 'm2m:fopt',
		ResourceTypes.FCNT_OL		: 'm2m:ol',
		ResourceTypes.FCNT_LA		: 'm2m:la',
		ResourceTypes.PCH_PCU		: 'm2m:pcu',

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




class BasicType(IntEnum):
	""" Basic resource types """
	positiveInteger	= auto()
	nonNegInteger	= auto()
	unsignedInt		= auto()
	unsignedLong	= auto()
	string 			= auto()
	timestamp		= auto()
	list 			= auto()
	dict 			= auto()
	anyURI			= auto()
	boolean			= auto()
	float 			= auto()
	geoCoordinates	= auto()


class Cardinality(IntEnum):
	""" Resource attribute cardinalities """
	car1			= auto()
	car1L			= auto()
	car01			= auto()
	car01L			= auto()
	car1N			= auto() # mandatory, but may be Null/None


class RequestOptionality(IntEnum):
	""" request optionalities """
	NP				= auto()
	O 				= auto()
	M 				= auto()


class Announced(IntEnum):
	""" anouncent attribute indications """
	NA				= auto()
	OA				= auto()
	MA				= auto()


##############################################################################
#
#	Response Codes
#


class ResponseCode(IntEnum):
	""" Response codes """
	accepted									= 1000
	accepedNonBlockingRequestSynch				= 1001
	accepedNonBlockingRequestAsynch				= 1002
	OK											= 2000
	created 									= 2001
	deleted 									= 2002
	updated										= 2004
	badRequest									= 4000
	notFound 									= 4004
	operationNotAllowed							= 4005
	subscriptionCreatorHasNoPrivilege			= 4101
	contentsUnacceptable						= 4102
	originatorHasNoPrivilege					= 4103
	conflict									= 4105
	securityAssociationRequired					= 4107
	invalidChildResourceType					= 4108
	groupMemberTypeInconsistent					= 4110
	internalServerError							= 5000
	notImplemented								= 5001
	targetNotReachable 							= 5103
	receiverHasNoPrivileges						= 5105
	alreadyExists								= 5106
	targetNotSubscribable						= 5203
	subscriptionVerificationInitiationFailed	= 5204
	subscriptionHostHasNoPrivilege				= 5205
	notAcceptable 								= 5207
	maxNumberOfMemberExceeded					= 6010
	invalidArguments							= 6023
	insufficientArguments						= 6024


	def httpStatusCode(self) -> int:
		""" Map the oneM2M RSC to an http status code. """
		return ResponseCode._httpStatusCodes[self.value]					# type: ignore



#
#	Mapping of oneM2M return codes to http status codes
#

ResponseCode._httpStatusCodes = {											# type: ignore
		ResponseCode.OK 										: 200,		# OK
		ResponseCode.deleted 									: 200,		# DELETED
		ResponseCode.updated 									: 200,		# UPDATED
		ResponseCode.created									: 201,		# CREATED
		ResponseCode.accepted 									: 202, 		# ACCEPTED
		ResponseCode.accepedNonBlockingRequestSynch 			: 202,		# ACCEPTED FOR NONBLOCKINGREQUESTSYNCH
		ResponseCode.accepedNonBlockingRequestAsynch			: 202,		# ACCEPTED FOR NONBLOCKINGREQUESTASYNCH
		ResponseCode.badRequest									: 400,		# BAD REQUEST
		ResponseCode.contentsUnacceptable						: 400,		# NOT ACCEPTABLE
		ResponseCode.insufficientArguments 						: 400,		# INSUFFICIENT ARGUMENTS
		ResponseCode.invalidArguments							: 400,		# INVALID ARGUMENTS
		ResponseCode.maxNumberOfMemberExceeded					: 400, 		# MAX NUMBER OF MEMBER EXCEEDED
		ResponseCode.groupMemberTypeInconsistent				: 400,		# GROUP MEMBER TYPE INCONSISTENT
		ResponseCode.originatorHasNoPrivilege					: 403,		# ORIGINATOR HAS NO PRIVILEGE
		ResponseCode.invalidChildResourceType					: 403,		# INVALID CHILD RESOURCE TYPE
		ResponseCode.targetNotReachable							: 403,		# TARGET NOT REACHABLE
		ResponseCode.alreadyExists								: 403,		# ALREAD EXISTS
		ResponseCode.targetNotSubscribable						: 403,		# TARGET NOT SUBSCRIBABLE
		ResponseCode.receiverHasNoPrivileges					: 403,		# RECEIVER HAS NO PRIVILEGE
		ResponseCode.securityAssociationRequired				: 403,		# SECURITY ASSOCIATION REQUIRED
		ResponseCode.subscriptionCreatorHasNoPrivilege			: 403,		# SUBSCRIPTION CREATOR HAS NO PRIVILEGE
		ResponseCode.subscriptionHostHasNoPrivilege				: 403,		# SUBSCRIPTION HOST HAS NO PRIVILEGE
		ResponseCode.notFound									: 404,		# NOT FOUND
		ResponseCode.operationNotAllowed						: 405,		# OPERATION NOT ALLOWED
		ResponseCode.notAcceptable 								: 406,		# NOT ACCEPTABLE
		ResponseCode.conflict									: 409,		# CONFLICT
		ResponseCode.internalServerError 						: 500,		# INTERNAL SERVER ERROR
		ResponseCode.subscriptionVerificationInitiationFailed	: 500,		# SUBSCRIPTION_VERIFICATION_INITIATION_FAILED
		ResponseCode.notImplemented								: 501,		# NOT IMPLEMENTED
	}



##############################################################################
#
#	Discovery & Filter
#

class ResultContentType(IntEnum):
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


class FilterOperation(IntEnum):
	"""	Filter Operation """
	AND 			= 1 # default
	OR 				= 2
	XOR 			= 3


class FilterUsage(IntEnum):
	"""	Filter Usage """
	discoveryCriteria		= 1
	conditionalRetrieval	= 2 # default
	ipeOnDemandDiscovery	= 3


class DesiredIdentifierResultType(IntEnum):
	""" Desired Identifier Result Type """
	structured		= 1 # default
	unstructured	= 2



##############################################################################
#
#	CSE related
#

class CSEType(IntEnum):
	""" CSE Types """
	IN					=  1
	MN					=  2
	ASN					=  3


##############################################################################
#
#	Permission related
#

class Permission(IntEnum):
	""" Permissions """
	NONE				=  0
	CREATE				=  1
	RETRIEVE			=  2
	UPDATE				=  4
	DELETE 				=  8
	NOTIFY 				= 16
	DISCOVERY			= 32
	ALL					= 63


##############################################################################
#
#	Operation related
#

class Operation(IntEnum):
	# Operations
	CREATE 				= 1
	RETRIEVE			= 2
	UPDATE				= 3
	DELETE				= 4
	NOTIFY 				= 6
	DISCOVERY			= 5


	def permission(self) -> Permission:
		""" Return the corresponding permission for an operation """
		return Operation._permissionsMapping[self.value]	#  type: ignore


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

class ResponseType(IntEnum):
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

class RequestStatus(IntEnum):
	"""	Reponse Types """
	COMPLETED			= 1
	FAILED				= 2
	PENDING				= 3
	FORWARDED			= 4
	PARTIALLY_COMPLETED	= 5


##############################################################################
#
#	Group related
#

class ConsistencyStrategy(IntEnum):
	"""	Consistency Strategy """
	abandonMember		= 1	# default
	abandonGroup		= 2
	setMixed			= 3

##############################################################################
#
#	Subscription related
#

class NotificationContentType(IntEnum):
	"""	Notification Content Types """
	all					= 1
	modifiedAttributes	= 2
	ri 					= 3
	triggerPayload		= 4
	

class NotificationEventType(IntEnum):
	""" eventNotificationCriteria/NotificationEventTypes """
	resourceUpdate		= 1	# default
	resourceDelete		= 2	
	createDirectChild	= 3
	deleteDirectChild	= 4	
	retrieveCNTNoChild	= 5	# TODO not supported yet
	triggerReceivedForAE= 6 # TODO not supported yet
	blockingUpdate 		= 7 # TODO not supported yet



##############################################################################
#
#	Result and Argument and Header Data Classes
#


@dataclass
class Result:
	resource 	: Any			= None		# Actually this is a Resource type, but have a circular import problem.
	jsn 		: dict 			= None
	lst 		: List[Any]   	= None		# List of Anything
	rsc 		: ResponseCode	= ResponseCode.OK	# OK
	dbg 		: str 			= None
	request 	: Request 		= None  	# may contain the original http request object
	status 		: bool 			= None
	originator 	: str 			= None


	def errorResult(self) -> Result:
		""" Copy only the rsc and dbg to a new result instance.
		"""
		return Result(rsc=self.rsc, dbg=self.dbg)


@dataclass
class RequestArguments:
	fu 							: FilterUsage 					= FilterUsage.conditionalRetrieval
	drt 						: DesiredIdentifierResultType	= DesiredIdentifierResultType.structured
	fo 							: FilterOperation 				= FilterOperation.AND
	rcn 						: ResultContentType 			= ResultContentType.discoveryResultReferences
	rt 							: ResponseType					= ResponseType.blockingRequest 					# response type
	rp 							: str 							= None 											# result persistence
	rpts 						: str 							= None 											# ... as a timestamp
	handling 					: dict 							= field(default_factory=dict)
	conditions 					: dict 							= field(default_factory=dict)
	attributes 					: dict 							= field(default_factory=dict)
	operation 					: Operation 					= None
	request 					: Request 						= None


@dataclass
class RequestHeaders:
	originator 					: str 			= None 	# X-M2M-Origin
	requestIdentifier			: str 			= None	# X-M2M-RI
	contentType 				: str 			= None	# Content-Type
	resourceType 				: ResourceTypes	= None
	requestExpirationTimestamp	: str 			= None 	# X-M2M-RET
	responseExpirationTimestamp	: str 			= None 	# X-M2M-RST
	operationExecutionTime		: str 			= None 	# X-M2M-OET
	releaseVersionIndicator		: str 			= None 	# X-M2M-RVI
	responseTypeURI				: List[str]		= field(default_factory=list)	# X-M2M-RTU

