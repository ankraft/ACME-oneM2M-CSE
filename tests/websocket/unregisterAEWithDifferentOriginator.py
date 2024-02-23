#
#	unregisterAEWithDifferentOriginator.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for unregister an AE with a different originator in the resource as in the WS connection

from wsrequests import *

if __name__ == '__main__':

	# open a new connection without originator. This is OK for an AE registration
	openConnection()	
	expectRSC(r := registerAE(), 2001, 'Register AE')
	orig = getOriginator(r)
	closeConnection()

	# open a new connection without originator!
	openConnection('CDifferentOriginator')	
	expectRSC(unregisterAE(aeName, orig, 'unregister AE w/ different WS originator'), 2002, 'Unregister AE')
	closeConnection()

