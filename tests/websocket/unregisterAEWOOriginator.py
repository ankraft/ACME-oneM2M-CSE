#
#	unregisterAEWOOriginator.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for unregistering an AE without an originator in the WS connection

from wsrequests import *

if __name__ == '__main__':

	# open a new connection without originator. This is OK for an AE registration
	openConnection()	
	expectRSC(r := registerAE(), 2001, 'Register AE')
	orig = getOriginator(r)
	closeConnection()

	# open a new connection without originator!
	openConnection()	
	expectRSC(unregisterAE(aeName, orig, 'unregister AE w/o WS originator'), 2002, 'Expected Fail! Unregister AE', doexit = False)
	closeConnection()

	# Cleanup
	cleanup(aeName, orig)
