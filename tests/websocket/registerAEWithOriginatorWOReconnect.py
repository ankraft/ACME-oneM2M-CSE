#
#	registerAEWithOriginatorWOReconnect.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for registering an AE with an originator in the WS connection.
#	The connection is NOT closed after the registration and NO new connection
#	is opened with the originator. This is an error case because the X-M2M-Origin
#	header is missing (it cannot be set afterwards in the WS connection).

from wsrequests import *

if __name__ == '__main__':

	# open a new connection with a "C" originator. 
	openConnection('C')	
	expectRSC(r := registerAE('C'), 2001, 'Register AE')
	orig = getOriginator(r)

	# The following re-opens a new connection including the new originator
	expectRSC(unregisterAE(aeName, orig, 'unregister AE w/ WS originator'), 2002, 'Unregister AE')
	closeConnection()

