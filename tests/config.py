#
#	config.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configurations for unit tests
#

BINDING						= 'http'	# possible values: http, https, mqtt

match BINDING:
	case 'mqtt':
		PROTOCOL				= 'mqtt'	
		CONFIGPROTOCOL			= 'http'
		NOTIFICATIONPROTOCOL	= 'http'
		REMOTEPROTOCOL			= 'http'
	case 'http':
		PROTOCOL				= 'http'
		CONFIGPROTOCOL			= 'http'
		NOTIFICATIONPROTOCOL	= 'http'
		REMOTEPROTOCOL			= 'http'
	case 'https':
		PROTOCOL				= 'https'
		CONFIGPROTOCOL			= 'https'
		NOTIFICATIONPROTOCOL	= 'http'
		REMOTEPROTOCOL			= 'http'
	case _:
		assert False, 'Supported values for BINDING are "mqtt", "http", and "https"'

# TODO ENCODING 			= 

#
#	General Configurations
#

SPID 					= 'acme.example.com'# Service Provide ID
APPID					= 'NMyApp1Id'		# Application ID
ORIGINATOR				= 'CAdmin'			# Admin originator
ORIGINATORSelfReg		= 'C'				# Originator for self registration
ORIGINATOREmpty			= ''				# Originator for empty originator/self registration 
ORIGINATORNotifResp		= 'CTester'			# Originator for Notification responses
RECONFIGURATIONENABLED	= True				# The CSE allowes for reconfigurations via Upper Tester
UPPERTESTERENABLED		= True				# Enable or Disable Upper Tester extensions
RELEASEVERSION			= '4'				# Supported Release Version for requests & registrations


#
#	CSE SuT
#

CSEURL					= f'{PROTOCOL}://localhost:8080/'	# CSE Server address.
CSERN					= 'cse-in'			# CSEBase Resource Name
CSERI					= 'id-in'			# CSEBase Resource ID
CSEID					= '/id-in'			# CSE-ID

##############################################################################

#
#	MQTT (if configured)
#

mqttAddress			= 'mqtt'
mqttPort			= 1883
mqttClientID		= 'CacmeTest'
mqttUsername		= 'test'
mqttPassword		= 'mqtt'


MQTTREQUESTTOPIC	= f'/oneM2M/req/$ORIGINATOR${CSEID}/json'
MQTTRESPONSETOPIC	= f'/oneM2M/resp/$ORIGINATOR${CSEID}/json'
MQTTREGREQUESTTOPIC	= f'/oneM2M/reg_req/{mqttClientID}{CSEID}/json'
MQTTREGRESPONSETOPIC= f'/oneM2M/reg_resp/{mqttClientID}{CSEID}/json'


##############################################################################

#
#	OAuth2 authentication
#	When using OAuth to access a CSE
#

doOAuth 			= False
oauthServerUrl		= ''
oauthClientID 		= ''
oauthClientSecret 	= ''


#
#	HTTP Basic authentication
#

doHttpBasicAuth		= False
httpUserName 		= 'test'
httpPassword 		= 'testPassword'

#
#	HTTP Token authentication
#
doHttpTokenAuth		= False
httpAuthToken		= 'testToken'


#
#	Remote CSE
#	For testing remote CSE registrations
#

REMOTECSEURL		= f'{REMOTEPROTOCOL}://localhost:8081/'
REMOTECSERN			= 'cse-mn'
REMOTECSERI			= 'id-mn'
REMOTECSEID			= '/id-mn'
REMOTESPID 			= 'sp-mn'
REMOTEAPPID			= 'NMNApp1Id'
REMOTEORIGINATOR	= 'CAdmin'


#
#	Notification Server
#

NOTIFICATIONPORT 	= 9990
NOTIFICATIONSERVER	= f'{NOTIFICATIONPROTOCOL}://localhost:{NOTIFICATIONPORT}' 
NOTIFICATIONSERVERW	= f'{NOTIFICATIONPROTOCOL}://localhost:6666'
NOTIFICATIONDELAY   = 0.5	# Time to wait for some async notifications


#
#	Upper Tester
#
UTURL	= f'{CONFIGPROTOCOL}://localhost:8080/__ut__'	# CSE's Upper Tester URL
UTCMD	= 'X-M2M-UTCMD'
UTRSP	= 'X-M2M-UTRSP'
