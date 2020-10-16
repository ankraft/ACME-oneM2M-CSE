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

class TestREQ(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		# create other resources
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, 'Cannot retrieve CSEBase: %s' % cseURL

		jsn = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyAppId',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, jsn)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		disableShortExpirations()
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not




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
		r, rsc = RETRIEVE('%s?rt=%d&rp=%s' % (cseURL, ResponseType.nonBlockingRequestSynch, requestETDuration), ORIGINATOR)
		rid = lastRequestID()
		self.assertEqual(rsc, RC.accepedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE('%s/%s' % (csiURL, requestURI), ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/lbl'))
		self.assertIn(ORIGINATOR, findXPath(r, 'm2m:req/lbl'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/op'))
		self.assertEqual(findXPath(r, 'm2m:req/op'), Operation.RETRIEVE)
		self.assertIsNotNone(findXPath(r, 'm2m:req/tg'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/or'))
		self.assertEqual(findXPath(r, 'm2m:req/or'), ORIGINATOR)
		self.assertIsNotNone(findXPath(r, 'm2m:req/rid'))
		self.assertEqual(findXPath(r, 'm2m:req/rid'), rid)	# test the request ID from the original request
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi/rt'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi/rt/rtv'))
		self.assertEqual(findXPath(r, 'm2m:req/mi/rt/rtv'), ResponseType.nonBlockingRequestSynch) 
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi/rp'), requestETDuration)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rid'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rid'), rid)	# test the request ID from the original request
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc/m2m:cb'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/pc/m2m:cb/ty'), T.CSEBase)

		# retrieve and check ACP
		self.assertIsNotNone(findXPath(r, 'm2m:req/acpi'))
		self.assertEqual(len(findXPath(r, 'm2m:req/acpi')), 1)
		acpi = findXPath(r, 'm2m:req/acpi/{0}')
		r, rsc = RETRIEVE('%s/%s' % (URL, acpi), ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:acp'))

		# Test PV
		found = False
		for a in findXPath(r, 'm2m:acp/pv/acr'):
			if findXPath(a, 'acop') == (Permission.RETRIEVE + Permission.UPDATE + Permission.DELETE) and ORIGINATOR in findXPath(a, 'acor'):
				found = True
				break
		self.assertTrue(found)
		# test PVS
		found = False
		for a in findXPath(r, 'm2m:acp/pvs/acr'):
			if findXPath(a, 'acop') == (Permission.UPDATE) and ORIGINATOR in findXPath(a, 'acor'):
				found = True
				break
		self.assertTrue(found)
			

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnknownNBSynch(self):
		r, rsc = RETRIEVE('%swrong?rt=%d&rp=%s' % (cseURL, ResponseType.nonBlockingRequestSynch, requestETDuration), ORIGINATOR)
		rid = lastRequestID()
		self.assertEqual(rsc, RC.accepedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE('%s/%s' % (csiURL, requestURI), ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.notFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAENBSynch(self):
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE('%s?rt=%d&rp=%s' % (aeURL, ResponseType.nonBlockingRequestSynch, requestETDuration), TestREQ.originator, T.CNT, jsn)
		rid = lastRequestID()
		self.assertEqual(rsc, RC.accepedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE('%s/%s' % (csiURL, requestURI), ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc/m2m:cnt'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/pc/m2m:cnt/ty'), T.CNT)


# CREATE resource synch. check return, retrieve request, check request
# UPDATE resource synch. check return, retrieve request, check request
# DELETE resource synch. check return, retrieve request, check request
# RETRIEVE resource synch. wait too long, retrieve request, check et etc -> fail

# test flexblocking


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestREQ('test_createREQFail'))
	suite.addTest(TestREQ('test_retrieveCSENBSynch'))
	suite.addTest(TestREQ('test_retrieveUnknownNBSynch'))
	suite.addTest(TestREQ('test_createAENBSynch'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)

