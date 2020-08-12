#
#	Constante.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various CSE and oneM2M constants
#

from Types import ResourceTypes as T

class Constants(object):


	# List of virtual resources

	virtualResources 				= [ T.CNT_LA, T.CNT_OL, T.FCNT_LA, T.FCNT_OL, T.GRP_FOPT, T.PCH_PCU ]
	virtualResourcesNames 			= [ 'la', 'ol', 'fopt', 'pcu' ]

	# Supported by this CSE
	supportedResourceTypes 			= [ T.ACP, T.AE, T.CNT, T.CIN, T.CSEBase, T.GRP, T.MGMTOBJ, T.NOD, T.CSR, T.SUB, T.FCNT, T.FCI ]
	stateTagResourceTypes 			= [ T.CNT, T.CIN, T.FCNT, T.FCI ]	# those resource types allow state tags
	supportedContentSerializations 	= [ 'application/json' ]
	supportedContentHeaderFormat 	= [ 'application/json', 'application/vnd.onem2m-res+json' ]
	supportedReleaseVersions 		= [ '3' ]

	# List of announceable resource types
	announcedResourceTypes 			= [ T.ACPAnnc, T.AEAnnc, T.CNTAnnc, T.CINAnnc, T.GRPAnnc, T.MGMTOBJAnnc, T.NODAnnc, T.CSRAnnc, T.FCNTAnnc, T.FCIAnnc ]

	# List of resource types for which "creator" is allowed
	# Also add later: eventConfig, pollingChannel, statsCollect, statsConfig, semanticDescriptor,
	# notificationTargetPolicy, timeSeries, crossResourceSubscription, backgroundDataTransfer
	creatorAllowed = [ T.CIN, T.CNT, T.GRP, T.SUB, T.FCNT ]




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
	rcConflict						= 4105
	rcSecurityAssociationRequired	= 4107
	rcInvalidChildResourceType		= 4108
	rcGroupMemberTypeInconsistent	= 4110
	rcInternalServerError			= 5000
	rcNotImplemented				= 5001
	rcTargetNotReachable 			= 5103
	rcReceiverHasNoPrivileges		= 5105
	rcAlreadyExists					= 5106
	rcTargetNotSubscribable			= 5203
	rcSubscriptionVerificationInitiationFailed = 5204
	rcNotAcceptable 				= 5207
	rcMaxNumberOfMemberExceeded		= 6010
	rcInvalidArguments				= 6023
	rcInsufficientArguments			= 6024

	# Operations
	opRETRIEVE						= 0
	opCREATE 						= 1
	opUPDATE						= 2
	opDELETE						= 3
	opDISCOVERY						= 4


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
	hfRVI							= 'X-M2M-RVI'
	hfvContentType					= 'application/json'
	hfvRVI 							= '3'

	# Subscription-related

	# notificationContentTypes
	nctAll 							= 1
	nctModifiedAttributes			= 2
	nctRI 							= 3
	nctTriggerPayload				= 4
	

	# eventNotificationCriteria/NotificationEventTypes
	netResourceUpdate				= 1	# default
	netResourceDelete				= 2	
	netCreateDirectChild			= 3
	netDeleteDirectChild			= 4	
	netRetrieveCNTNoChild			= 5	# TODO not supported yet

	# Result Content types
	rcnNothing								= 0
	rcnAttributes 							= 1
	rcnHierarchicalAddress					= 2
	rcnHierarchicalAddressAttributes		= 3
	rcnAttributesAndChildResources			= 4	
	rcnAttributesAndChildResourceReferences	= 5
	rcnChildResourceReferences				= 6
	rcnOriginalResource 					= 7
	rcnChildResources						= 8
	rcnModifiedAttributes					= 9
	rcnDiscoveryResultReferences			= 11

	# Desired Identifier Result Type
	drtStructured					= 1 # default
	drtUnstructured					= 2

	# Filter Usage
	fuDiscoveryCriteria				= 1
	fuConditionalRetrieval			= 2 # default
	fuIPEOnDemandDiscovery			= 3

	# Filter Operation
	foAND 							= 1 # default
	foOR 							= 2
	foXOR 							= 3

	# Group related

	# consistencyStrategy
	csyAbandonMember				= 1	# default
	csyAbandonGroup					= 2
	csySetMixed						= 3

	#
	#	Magic strings
	#

	# Additional JSON fields
	jsnIsImported						= '__imported__'

	acpPrefix 						= 'acp_'



	