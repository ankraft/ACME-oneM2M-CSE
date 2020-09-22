#
#	testExpiration.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Remote CSE functionality. Tests are skipped if there is no
#	remote CSE
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from init import *

expirationCheckDelay = 2
expirationSleep = expirationCheckDelay * 3


# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

# Reconfigure the server to check faster for expirations. This is set to the
# old value in the tearDowndClass() method.
orgExpCheck = setExpirationCheck(expirationCheckDelay)


class TestExpiration(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, 'Cannot retrieve CSEBase: %s' % cseURL
		jsn = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, jsn)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		if orgExpCheck != -1:
			setExpirationCheck(orgExpCheck)
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipIf(orgExpCheck == -1, 'Couldn\'t reconfigure expiration check')
	def test_expireCNT(self):
		self.assertIsNotNone(TestExpiration.cse)
		self.assertIsNotNone(TestExpiration.ae)
		jsn = 	{ 'm2m:cnt' : { 
					'et' : getDate(expirationCheckDelay), # 2 seconds in the future
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.created)
		time.sleep(expirationSleep)	# give the server a moment to expire the resource
		
		r, rsc = RETRIEVE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.notFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipIf(orgExpCheck == -1, 'Couldn\'t reconfigure expiration check')
	def test_expireCNTAndCIN(self):
		self.assertIsNotNone(TestExpiration.cse)
		self.assertIsNotNone(TestExpiration.ae)
		jsn = 	{ 'm2m:cnt' : { 
					'et' : getDate(expirationCheckDelay), # 2 seconds in the future
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.created)
		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'AnyValue'
				}}
		for _ in range(0, 5):
			r, rsc = CREATE(cntURL, TestExpiration.originator, T.CNT, jsn)
			self.assertEqual(rsc, RC.created)
			cinRn = findXPath(r, 'm2m:cin/rn')
		self.assertIsNotNone(cinRn)

		r, rsc = RETRIEVE('%s/%s' % (cntURL, cinRn), TestExpiration.originator)
		self.assertEqual(rsc, RC.OK)
		time.sleep(expirationSleep)	# give the server a moment to expire the resource

		r, rsc = RETRIEVE(cntURL, TestExpiration.originator)	# retrieve CNT again
		self.assertEqual(rsc, RC.notFound)

		r, rsc = RETRIEVE('%s/%s' % (cntURL, cinRn), TestExpiration.originator)	# retrieve CIN again
		self.assertEqual(rsc, RC.notFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTWithToLargeET(self):
		self.assertIsNotNone(TestExpiration.cse)
		self.assertIsNotNone(TestExpiration.ae)
		jsn = 	{ 'm2m:cnt' : { 
					'et' : '99991231T235959',	# wrongly updated
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertLess(findXPath(r, 'm2m:cnt/et'), '99991231T235959')
		r, rsc = DELETE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTExpirationInThePast(self):
		self.assertIsNotNone(TestExpiration.cse)
		self.assertIsNotNone(TestExpiration.ae)
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'et' : getDate(-60) # 1 minute in the past
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.badRequest)



def run():
	suite = unittest.TestSuite()
	suite.addTest(TestExpiration('test_expireCNT'))
	suite.addTest(TestExpiration('test_expireCNTAndCIN'))
	suite.addTest(TestExpiration('test_createCNTWithToLargeET'))
	suite.addTest(TestExpiration('test_createCNTExpirationInThePast'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)