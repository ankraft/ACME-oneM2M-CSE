#
#	Constants.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Various CSE and oneM2M constants
#


class Constants(object):

	# ACME Version
	version							= '0.10.0-dev'
	textLogo						= '[dim][[/dim][red][i]ACME[/i][/red][dim]][/dim]'
	

	#
	#	HTTP Header Fields
	#	These fields are here instead of the httpServer bc they are also used by the test cases.
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
	hfOT 							= 'X-M2M-OT'
	hfAccept						= 'Accept'
			

	#
	#	Supported URL schemes
	#
	supportedSchemes = ['http', 'https', 'mqtt', 'mqtts', 'acme']	# Supported by the CSE


	#
	#	Configuration meta defaults
	#
	#	TODO Perhaps move this to an String Enum when we switch to Python 3.10
	#

	defaultConfigFile			= 'acme.ini.default'
	defaultUserConfigFile		= 'acme.ini'
	defaultImportDirectory		= './init'
	defaultDataDirectory		= './data'
	defaultLogDirectory			= './logs'

	#
	#	Magic strings and numbers
	#

	# max length of identifiers
	maxIDLength	= 10


	
