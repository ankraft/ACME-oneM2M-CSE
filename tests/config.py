#
#	config.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Configurations for unit tests
#

PROTOCOL			= 'http'	# possible values: http, https
# TODO ENCODING 			= 


# 
#	CSE SuT
#

SERVER				= f'{PROTOCOL}://localhost:8080'	# Remember: no trailing '/' 
ROOTPATH			= '/'
CSERN				= 'cse-in'
CSEID				= '/id-in'
SPID 				= 'sp-in'
ORIGINATOR			= 'CAdmin'


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

REMOTESERVER		= f'{PROTOCOL}://localhost:8081'
REMOTEROOTPATH		= '/'
REMOTECSERN			= 'cse-mn'
REMOTECSEID			= '/id-mn'
REMOTESPID 			= 'sp-mn'
REMOTEORIGINATOR	= 'CAdmin'


#
#	Notification Server
#

NOTIFICATIONPORT 	= 9990
NOTIFICATIONSERVER	= f'{PROTOCOL}://localhost:{NOTIFICATIONPORT}' 
NOTIFICATIONSERVERW	= f'{PROTOCOL}://localhost:6666'

