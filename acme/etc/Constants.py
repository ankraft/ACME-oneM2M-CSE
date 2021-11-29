#
#	Constants.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various CSE and oneM2M constants
#

from .Types import ResourceTypes as T, ContentSerializationType as CST

class Constants(object):

	# ACME Version
	version								= '0.10.0-dev'
	


	# TODO move to types

	#
	#	Supported content serializations
	#

	supportedContentSerializations 		= [ CST.JSON.toHeader(), CST.CBOR.toHeader(), 'application/vnd.onem2m-res+json', 'application/vnd.onem2m-res+cbor' ]
	supportedContentSerializationsSimple = [ CST.JSON.toSimple(), CST.CBOR.toSimple() ]

	supportedContentHeaderFormat 		= [ CST.JSON.toHeader(), CST.CBOR.toHeader(),'application/vnd.onem2m-res+json', 'application/vnd.onem2m-res+cbor' ]
	supportedContentHeaderFormatTuple	= tuple(supportedContentHeaderFormat)


	# TODO move to types, own enum?

	#
	#	HTTP Header Fields
	#

	hfOrigin						= 'X-M2M-Origin'
	hfRI 							= 'X-M2M-RI'
	hfRVI							= 'X-M2M-RVI'
	hfEC 							= 'X-M2M-EC'
	hfcEC 							= 'Event Category'
	hfvECLatest 					= '4'
	hfRET 							= 'X-M2M-RET'
	hfRST 							= 'X-M2M-RST'
	hfOET 							= 'X-M2M-OET'
	hfRTU 							= 'X-M2M-RTU'
	hfRSC 							= 'X-M2M-RSC'
	hfVSI 							= 'X-M2M-VSI'
	hfAccept						= 'Accept'
			

	#
	#	Supported URL schemes
	#
	supportedSchemes = ['http', 'https', 'mqtt', 'mqtts']	# Supported by the CSE
	# TODO add Coap here later


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

	# max length of identifiers
	maxIDLength	= 10


	
