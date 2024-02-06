#
#	notificationViaSameWS.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for registering an AE, CNT and SUB and receiving a notification via the same WS connection.
#	The poa uses the 'unreachable' URL, so that the AE is not reachable, but the same WS
#	connection is used to send a notification to the AE.

from wsrequests import *
from time import sleep

if __name__ == '__main__':

	# open a new connection with a "C" originator and register AE
	openConnection('C')	
	expectRSC(r := registerAE('C', unreachablePOA), 2001, 'Register AE', cleanup = lambda: cleanup(aeName))
	orig = getOriginator(r)
	closeConnection()

	# The following re-opens a new connection including the new originator.
	openConnection(orig)
    # Register necessary resources
	expectRSC(r := createSubscription(subName, orig), 2001, 'Create Subscription', cleanup = lambda: cleanup(aeName, orig))
	
	# Open a new connection with the adninOriginator to update the AE, update the AE, and close the connection
	openUpdateConnection(adminOriginator)
	expectRSC(r := updateAE(aeName, adminOriginator), 2004, 'Update AE', cleanup = lambda: cleanup(aeName, orig))
	closeUpdateConnection()

	# Receive the notification
	sleep(timeout)	# Wait a little bit to receive the notification
	receiveNotification(orig)
	sleep(timeout)

	# End and close
	closeConnection()

	# clean up
	cleanup(aeName, orig)

