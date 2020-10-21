#
#	testREQ.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for REQ functionality
#

import unittest, sys, time
import requests
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T, NotificationContentType, ResponseCode as RC, Operation, ResponseType, Permission
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

# Reconfigure the server to check faster for expirations.
enableShortExpirations()

# Headers for async requests
headers = {
	C.hfRTU	: NOTIFICATIONSERVER
}
headersEmpty = {
	C.hfRTU	: ''
}

class TestREQ(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		# Start notification server
		startNotificationServer()

		# create other resources
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, 'Cannot retrieve CSEBase: %s' % cseURL

		jsn = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyAppId',
				 	'rr'  : False,
				 	'srv' : [ '3' ],
				 	'poa' : [ NOTIFICATIONSERVER ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, jsn)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		time.sleep(expirationSleep)	# give the server a moment to expire the resource
		disableShortExpirations()
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()



	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(isTestExpirations(), 'Couldn\'t reconfigure expiration check')
	def test_createREQFail(self):
		self.assertIsNotNone(TestREQ.ae)
		jsn = 	{ 'm2m:req' : { 
				}}
		r, rsc = CREATE(cseURL, TestREQ.originator, T.REQ, jsn)
		self.assertEqual(rsc, RC.operationNotAllowed)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynch(self):
		r, rsc = RETRIEVE('%s?rt=%d&rp=%s' % (cseURL, ResponseType.nonBlockingRequestSynch, requestETDuration), TestREQ.originator)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE('%s/%s' % (csiURL, requestURI), TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/lbl'))
		self.assertIn(TestREQ.originator, findXPath(r, 'm2m:req/lbl'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/op'))
		self.assertEqual(findXPath(r, 'm2m:req/op'), Operation.RETRIEVE)
		self.assertIsNotNone(findXPath(r, 'm2m:req/tg'))
		self.assertIsNone(findXPath(r, 'm2m:req/pc'))		# original content should be not set for retrieve
		self.assertIsNotNone(findXPath(r, 'm2m:req/org'))
		self.assertEqual(findXPath(r, 'm2m:req/org'), TestREQ.originator)
		self.assertIsNotNone(findXPath(r, 'm2m:req/rid'))
		self.assertEqual(findXPath(r, 'm2m:req/rid'), rqi)	# test the request ID from the original request
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi/rt'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi/rt/rtv'))
		self.assertEqual(findXPath(r, 'm2m:req/mi/rt/rtv'), ResponseType.nonBlockingRequestSynch) 
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi/rp'), requestETDuration)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rqi'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rqi'), rqi)	# test the request ID from the original request
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc/m2m:cb'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/pc/m2m:cb/ty'), T.CSEBase)

		# retrieve with ORIGINATOR and check ACP
		self.assertIsNotNone(findXPath(r, 'm2m:req/acpi'))
		self.assertEqual(len(findXPath(r, 'm2m:req/acpi')), 1)
		acpi = findXPath(r, 'm2m:req/acpi/{0}')
		r, rsc = RETRIEVE('%s/%s' % (URL, acpi), ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:acp'))

		# Test PV
		found = False
		for a in findXPath(r, 'm2m:acp/pv/acr'):
			if findXPath(a, 'acop') == (Permission.RETRIEVE + Permission.UPDATE + Permission.DELETE) and TestREQ.originator in findXPath(a, 'acor'):
				found = True
				break
		self.assertTrue(found)
		# test PVS
		found = False
		for a in findXPath(r, 'm2m:acp/pvs/acr'):
			if findXPath(a, 'acop') == (Permission.UPDATE) and TestREQ.originator in findXPath(a, 'acor'):
				found = True
				break
		self.assertTrue(found)

		# retrieve with AE's originator. Should fail
		r, rsc = RETRIEVE('%s/%s' % (URL, acpi), TestREQ.originator)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnknownNBSynch(self):
		r, rsc = RETRIEVE('%swrong?rt=%d&rp=%s' % (cseURL, ResponseType.nonBlockingRequestSynch, requestETDuration), TestREQ.originator)
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE('%s/%s' % (csiURL, requestURI), TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.notFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTNBFlex(self):
		r, rsc = RETRIEVE('%s?rt=%d&rp=%s' % (cseURL, ResponseType.flexBlocking, requestETDuration), TestREQ.originator)
		self.assertIn(rsc, [ RC.OK, RC.acceptedNonBlockingRequestSynch, RC.acceptedNonBlockingRequestAsynch ] )
		# -> Ignore the result


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTNBSynch(self):
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE('%s?rt=%d&rp=%s' % (aeURL, ResponseType.nonBlockingRequestSynch, requestETDuration), TestREQ.originator, T.CNT, jsn)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE('%s/%s' % (csiURL, requestURI), TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc'))			# original content should be set for CREATE
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc/m2m:cnt'))	# just a quick check
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc/m2m:cnt'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/pc/m2m:cnt/ty'), T.CNT)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rqi'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTNBSynch(self):
		jsn = 	{ 'm2m:cnt' : { 
					'lbl' : [ 'aLabel' ]
				}}
		r, rsc = UPDATE('%s?rt=%d&rp=%s' % (cntURL, ResponseType.nonBlockingRequestSynch, requestETDuration), TestREQ.originator, jsn)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE('%s/%s' % (csiURL, requestURI), TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc'))			# original content should be set for UPDATE
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc/m2m:cnt'))	# just a quick check
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.updated)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc/m2m:cnt'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/pc/m2m:cnt/ty'), T.CNT)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc/m2m:cnt/lbl'))
		self.assertIn('aLabel', findXPath(r, 'm2m:req/ors/pc/m2m:cnt/lbl'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rqi'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTNBSynch(self):
		r, rsc = DELETE('%s?rt=%d&rp=%s' % (cntURL, ResponseType.nonBlockingRequestSynch, requestETDuration), TestREQ.originator)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE('%s/%s' % (csiURL, requestURI), TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.deleted)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rqi'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBAsynch(self):
		r, rsc = RETRIEVE('%s?rt=%d&rp=%s' % (cseURL, ResponseType.nonBlockingRequestAsynch, requestETDuration), TestREQ.originator, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.OK)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/to'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/to'), CSEID[1:])
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/fr'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/fr'), TestREQ.originator)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb/ty'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb/ty'), T.CSEBase)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


	# no notification is sent
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBAsynchEmptyRTU(self):
		clearLastNotification()
		r, rsc = RETRIEVE('%s?rt=%d&rp=%s' % (cseURL, ResponseType.nonBlockingRequestAsynch, requestETDuration), TestREQ.originator, headers=headersEmpty)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNone(lastNotification)


	# URI is provided by the originator AE.poa
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBAsynchNoRTU(self):
		clearLastNotification()
		r, rsc = RETRIEVE('%s?rt=%d&rp=%s' % (cseURL, ResponseType.nonBlockingRequestAsynch, requestETDuration), TestREQ.originator)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.OK)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/to'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/to'), CSEID[1:])
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/fr'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/fr'), TestREQ.originator)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb/ty'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb/ty'), T.CSEBase)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnknownNBAsynch(self):
		r, rsc = RETRIEVE('%swrong?rt=%d&rp=%s' % (cseURL, ResponseType.nonBlockingRequestAsynch, requestETDuration), TestREQ.originator, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.notFound)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTNBAsynch(self):
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE('%s?rt=%d&rp=%s' % (aeURL, ResponseType.nonBlockingRequestAsynch, requestETDuration), TestREQ.originator, T.CNT, jsn, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.created)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/ty'), T.CNT)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTNBAsynch(self):
		jsn = 	{ 'm2m:cnt' : { 
					'lbl' : [ 'aLabel' ]
				}}
		r, rsc = UPDATE('%s?rt=%d&rp=%s' % (cntURL, ResponseType.nonBlockingRequestAsynch, requestETDuration), TestREQ.originator, jsn, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.updated)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/fr'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/fr'), TestREQ.originator)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/ty'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/ty'), T.CNT)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/lbl'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/ty'), T.CNT)
		self.assertIn('aLabel', findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/lbl'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTNBASynch(self):
		r, rsc = DELETE('%s?rt=%d&rp=%s' % (cntURL, ResponseType.nonBlockingRequestAsynch, requestETDuration), TestREQ.originator, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.deleted)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)

# RETRIEVE resource synch. wait too long, retrieve request, check et etc -> fail



def run():
	suite = unittest.TestSuite()

	suite.addTest(TestREQ('test_createREQFail'))

	# nonBlockingSync
	suite.addTest(TestREQ('test_retrieveCSENBSynch'))
	suite.addTest(TestREQ('test_retrieveUnknownNBSynch'))
	suite.addTest(TestREQ('test_retrieveCNTNBFlex'))		# flex
	suite.addTest(TestREQ('test_createCNTNBSynch'))
	suite.addTest(TestREQ('test_updateCNTNBSynch'))
	suite.addTest(TestREQ('test_deleteCNTNBSynch'))

	# nonBlockingAsync
	suite.addTest(TestREQ('test_retrieveCSENBAsynch'))
	suite.addTest(TestREQ('test_retrieveCSENBAsynchEmptyRTU'))
	suite.addTest(TestREQ('test_retrieveCSENBAsynchNoRTU'))
	suite.addTest(TestREQ('test_retrieveUnknownNBAsynch'))
	suite.addTest(TestREQ('test_createCNTNBAsynch'))
	suite.addTest(TestREQ('test_updateCNTNBAsynch'))
	suite.addTest(TestREQ('test_deleteCNTNBASynch'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)

