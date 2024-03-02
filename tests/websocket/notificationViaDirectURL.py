#
#	notificationViaDirectURL.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for registering an AE and SUB and receiving a notification via a direct WS connection.
#	The poa uses the a direct ws:// URL, so that the AE is reachable through an own WS server

from wsrequests import *
from config import *
from time import sleep


if __name__ == '__main__':

	# Start the notification server
	startNotificationServer(False)

	# open a new connection with a "C" originator and register AE
	openConnection('C')	
	expectRSC(r := registerAE('C', wsServerPOA), 2001, 'Register AE', cleanup = lambda: cleanup(aeName))
	orig = getOriginator(r)
	closeConnection()

	# The following re-opens a new connection including the new originator.
	openConnection(orig)

    # Register necessary resources
	expectRSC(r := createSubscription(subName, orig, nu = wsServerPOA), 2001, 'Create Subscription', cleanup = lambda: cleanup(aeName, orig))
	
	# Close connection to force a notification to the own WS server
	closeConnection()

	# Open a new connection with the admin originator to update the AE, update the AE, and close the connection
	openUpdateConnection(adminOriginator)
	expectRSC(r := updateAE(aeName, adminOriginator), 2004, 'Update AE', cleanup = lambda: cleanup(aeName, orig))
	closeUpdateConnection()

	# Receive the notification
	sleep(timeout)	# Wait a little bit to receive the notification

	# End and close
	closeConnection()

	# stop the notification server
	stopNotificationServer()

	# clean up
	cleanup(aeName, orig)

