#
#	Constants.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various CSE and oneM2M constants
#

from Types import ResourceTypes as T

class Constants(object):

	# ACME Version
	version						= '0.5.0'


	# List of virtual resources

	virtualResources 				= [ T.CNT_LA, T.CNT_OL, T.FCNT_LA, T.FCNT_OL, T.GRP_FOPT, T.PCH_PCU ]
	virtualResourcesNames 			= [ 'la', 'ol', 'fopt', 'pcu' ]

	# Supported resource types by this CSE
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


	#
	#	Message Header Fields
	#

	hfOrigin						= 'X-M2M-Origin'
	hfRI 							= 'X-M2M-RI'
	hfRVI							= 'X-M2M-RVI'
	hfvContentType					= 'application/json'
	hfvRVI 							= '3'
	

	#
	#	Configuration meta defaults
	#

	defaultConfigFile			= 'acme.ini'
	defaultImportDirectory		= './init'
	defaultDataDirectory		= './data'
	defaultLogDirectory			= './logs'

	#
	#	Magic strings and numbers
	#

	# Additional JSON fields
	jsnIsImported					= '__imported__'

	acpPrefix 						= 'acp_'


	# max length of identifiers
	maxIDLength	= 10


	