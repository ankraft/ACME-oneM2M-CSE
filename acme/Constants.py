#
#	Constants.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various CSE and oneM2M constants
#

from Types import ResourceTypes as T, ContentSerializationType as CST

class Constants(object):

	# ACME Version
	version						= '0.7.3'

	# Supported release vesions
	supportedReleaseVersions = ['2a', '3', '4']

	
	# List of virtual resources

	virtualResources 				= [ T.CNT_LA, T.CNT_OL, T.FCNT_LA, T.FCNT_OL, T.GRP_FOPT, T.PCH_PCU ]
	virtualResourcesNames 			= [ 'la', 'ol', 'fopt', 'pcu' ]

	# List of announceable resource types
	announcedResourceTypes 			= [ T.ACPAnnc, T.AEAnnc, T.CNTAnnc, T.CINAnnc, T.GRPAnnc, T.MGMTOBJAnnc, T.NODAnnc, T.CSRAnnc, T.FCNTAnnc, T.FCIAnnc ]

	# Supported resource types by this CSE
	supportedResourceTypes 			= [	# Supported normal resource
										T.ACP, T.AE, T.CNT, T.CIN, T.CSEBase, T.GRP, T.MGMTOBJ, T.NOD, T.CSR, 
										T.REQ, T.SUB, T.FCNT, T.FCI
									  ]
	supportedResourceTypes			+= announcedResourceTypes	# add announced resource types as well

	stateTagResourceTypes 			= [ T.CNT, T.CIN, T.FCNT, T.FCI, T.REQ ]	# those resource types allow state tags
	supportedContentSerializations 	= [ CST.JSON.toHeader(), CST.CBOR.toHeader(), 'application/vnd.onem2m-res+json', 'application/vnd.onem2m-res+cbor' ]
	supportedContentSerializationsSimple = [ CST.JSON.toSimple(), CST.CBOR.toSimple() ]

	supportedContentHeaderFormat 	= [ CST.JSON.toHeader(), CST.CBOR.toHeader(),'application/vnd.onem2m-res+json', 'application/vnd.onem2m-res+cbor' ]

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
	hfEC 							= 'X-M2M-EC'
	hfcEC 							= 'Event Category'
	hfvECLatest 					= '4'
	hfRET 							= 'X-M2M-RET'
	hfRST 							= 'X-M2M-RST'
	hfOET 							= 'X-M2M-OET'
	hfRTU 							= 'X-M2M-RTU'
	hfAccept						= 'Accept'
			

	#
	#	Supported URL schemes
	#
	supportedSchemes = ['http', 'https']	# Supported by the CSE
	# TODO add Coap here later

	#
	#	Supported content serializations
	#

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

	# Additional internal resource fields
	isImported					= '__imported__'

	acpPrefix 					= 'acp_'

	invalidValue 				= '__iNvAliD___'


	# max length of identifiers
	maxIDLength	= 10


	