#
#	config.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configurations for unit tests
#

BINDING						= 'http'

if BINDING == 'mqtt':

	PROTOCOL				= 'mqtt'	# possible values: http, https, mqtt
	CONFIGPROTOCOL			= 'http'	# possible values: http, https, mqtt
	NOTIFICATIONPROTOCOL	= 'http'	# possible values: http, https, mqtt
	REMOTEPROTOCOL			= 'http'	# possible values: http, https, mqtt

elif BINDING == 'http':

	PROTOCOL				= 'http'	# possible values: http, https, mqtt
	CONFIGPROTOCOL			= 'http'	# possible values: http, https, mqtt
	NOTIFICATIONPROTOCOL	= 'http'	# possible values: http, https, mqtt
	REMOTEPROTOCOL			= 'http'	# possible values: http, https, mqtt

elif BINDING == 'https':

	PROTOCOL				= 'https'	# possible values: http, https, mqtt
	CONFIGPROTOCOL			= 'https'	# possible values: http, https, mqtt
	NOTIFICATIONPROTOCOL	= 'http'	# possible values: http, https, mqtt
	REMOTEPROTOCOL			= 'http'	# possible values: http, https, mqtt

else:
	assert False, 'Supported values for BINDING are "mqtt", "http", and "https"'

# TODO ENCODING 			= 


#
#	CSE SuT
#

SERVER				= f'{PROTOCOL}://localhost:8080'	# Remember: no trailing '/' 
CONFIGSERVER		= f'{CONFIGPROTOCOL}://localhost:8080'
ROOTPATH			= '/'
CSERN				= 'cse-in'
CSERI				= 'id-in'
CSEID				= '/id-in'
SPID 				= 'acme.example.com'
ORIGINATOR			= 'CAdmin'
ORIGINATORResp		= 'CTester'


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



#
#	OAuth2 authentication
#

doOAuth 			= False
oauthServerUrl		= ''
oauthClientID 		= ''
oauthClientSecret 	= ''


#
#	Remote CSE
#

REMOTESERVER		= f'{REMOTEPROTOCOL}://localhost:8081'
REMOTEROOTPATH		= '/'
REMOTECSERN			= 'cse-mn'
REMOTECSERI			= 'id-mn'
REMOTECSEID			= '/id-mn'
REMOTESPID 			= 'sp-mn'
REMOTEORIGINATOR	= 'CAdmin'


#
#	Notification Server
#

NOTIFICATIONPORT 	= 9990
NOTIFICATIONSERVER	= f'{NOTIFICATIONPROTOCOL}://localhost:{NOTIFICATIONPORT}' 
NOTIFICATIONSERVERW	= f'{NOTIFICATIONPROTOCOL}://localhost:6666'


#
#	Upper Tester
#

UTURL = f'{CONFIGSERVER}{ROOTPATH}__ut__'
UTCMD = 'X-M2M-UTCMD'
UTRSP = 'X-M2M-UTRSP'
