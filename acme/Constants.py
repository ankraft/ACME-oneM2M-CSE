#
#	Constante.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various CSE and oneM2M constante
#

class Constants(object):


	# Type constants

	tUNKNOWN	= -1
	tMIXED		=  0
	tsMIXED		= 'mixed'
	tACP 		=  1
	tsACP 		= 'm2m:acp'
	tAE			=  2
	tsAE 		= 'm2m:ae'
	tCNT		=  3
	tsCNT		= 'm2m:cnt'
	tCIN 		=  4
	tsCIN 		= 'm2m:cin'
	tCSEBase 	=  5
	tsCSEBase	= 'm2m:cb'
	tGRP 		=  9
	tsGRP		= 'm2m:grp'
	tMGMTOBJ	= 13
	tsMGMTOBJ	= 'm2m:mgo'	# not an official shortname
	tNOD		= 14
	tsNOD		= 'm2m:nod'
	tCSR		= 16
	tsCSR 		= 'm2m:csr'
	tSUB		= 23
	tsSUB		= 'm2m:sub'
	tFCNT	 	= 28
	tsFCNT		= 'm2m:fcnt'	# not an official shortname
	tFCI 		= 52
	tsFCI		= 'm2m:fci'		# not an official shortname

	# Virtual resources (proprietary resource types)

	tCNT_OL		=  -20001
	tsCNT_OL	= 'm2m:ol'
	tCNT_LA		=  -20002
	tsCNT_LA	= 'm2m:la'
	tGRP_FOPT	=  -20003
	tsGRP_FOPT	= 'm2m:fopt'
	tFCNT_OL	=  -20004
	tsFCNT_OL	= 'm2m:ol'
	tFCNT_LA	=  -20005
	tsFCNT_LA	= 'm2m:la'

	# <mgmtObj> Specializations

	mgdFWR		= 1001
	tsFWR		= 'm2m:fwr'
	mgdSWR		= 1002
	tsSWR		= 'm2m:swr'
	mgdMEM		= 1003
	tsMEM		= 'm2m:mem'
	mgdANI		= 1004
	tsANI		= 'm2m:ani'
	mgdANDI		= 1005
	tsANDI		= 'm2m:andi'
	mgdBAT		= 1006
	tsBAT		= 'm2m:bat'
	mgdDVI 		= 1007
	tsDVI		= 'm2m:dvi'
	mgdDVC 		= 1008
	tsDVC		= 'm2m:dvc'
	mgdRBO 		= 1009
	tsRBO		= 'm2m:rbo'
	mgdEVL 		= 1010
	tsEVL		= 'm2m:evl'

	# List of virtual resources

	tVirtualResources = [ tCNT_LA, tCNT_OL, tGRP_FOPT ]

	# Supported by this CSE
	supportedResourceTypes = [ tACP, tAE, tCNT, tCIN, tCSEBase, tGRP, tMGMTOBJ, tNOD, tCSR, tSUB, tFCNT, tFCI ]
	supportedContentSerializations = [ 'application/json', 'application/vnd.onem2m-res+json' ]
	supportedReleaseVersions = [ '3' ]

	# List of resource types for which "creator" is allowed
	# Also add later: eventConfig, pollingChannel, statsCollect, statsConfig, semanticDescriptor,
	# notificationTargetPolicy, timeSeries, crossResourceSubscription, backgroundDataTransfer
	tCreatorAllowed = [ tCIN, tCNT, tGRP, tSUB, tFCNT ]





	# max length of identifiers
	maxIDLength	= 10


	# Response codes
	rcOK							= 2000
	rcCreated 						= 2001
	rcDeleted 						= 2002
	rcUpdated						= 2004
	rcBadRequest					= 4000
	rcNotFound 						= 4004
	rcOperationNotAllowed			= 4005
	rcContentsUnacceptable			= 4102
	rcOriginatorHasNoPrivilege		= 4103
	rcInvalidChildResourceType		= 4108
	rcGroupMemberTypeInconsistent	= 4110
	rcInternalServerError			= 5000
	rcNotImplemented				= 5001
	rcTargetNotReachable 			= 5103
	rcReceiverHasNoPrivileges		= 5105
	rcAlreadyExists					= 5106
	rcTargetNotSubscribable			= 5203
	rcMaxNumberOfMemberExceeded		= 6010
	rcInvalidArguments				= 6023
	rcInsufficientArguments			= 6024

	# Operations
	opRETRIEVE						= 0
	opCREATE 						= 1
	opUPDATE						= 2
	opDELETE						= 3


	# Permissions
	permNONE						=  0
	permCREATE						=  1
	permRETRIEVE					=  2
	permUPDATE						=  4
	permDELETE 						=  8
	permNOTIFY 						= 16
	permDISCOVERY					= 32
	permALL							= 63


	# CSE Types
	cseTypeIN						=  1
	cseTypeMN						=  2
	cseTypeASN						=  3
	cseTypes 						= [ '', 'IN', 'MN', 'ASN' ]



	# Header Fields
	hfOrigin						= 'X-M2M-Origin'
	hfRI 							= 'X-M2M-RI'
	hfvContentType					= 'application/json'


	# Subscription-related

	# notificationContentTypes
	nctAll 							= 1
	nctModifiedAttributes			= 2
	nctRI 							= 3

	# eventNotificationCriteria/NotificationEventTypes
	netResourceUpdate				= 1	# default
	netResourceDelete				= 2	
	netCreateDirectChild			= 3
	netDeleteDirectChild			= 4	
	netRetrieveCNTNoChild			= 5	# TODO not supported yet

	# Result Content types
	rcnNothing								= 0
	rcnAttributes 							= 1	
	rcnAttributesAndChildResources			= 4	
	rcnAttributesAndChildResourceReferences	= 5
	rcnChildResourceReferences				= 6
	rcnChildResources						= 8
	rcnModifiedAttributes					= 9
	# TODO support other RCN

	# Desired Identifier Result Type
	drtStructured					= 1 # default
	drtUnstructured					= 2

	# Filter Usage
	fuDiscoveryCriteria				= 1
	fuConditionalRetrieval			= 2 # default
	fuIPEOnDemandDiscovery			= 3

	# Group related

	# consistencyStrategy
	csyAbandonMember				= 1	# default
	csyAbandonGroup					= 2
	csySetMixed						= 3



	