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


CND = 'org.onem2m.home.moduleclass.temperature'


# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

# Reconfigure the server to check faster for expirations.
enableShortExpirations()

class TestExpiration(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):

		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}'
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
		disableShortExpirations()
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(isTestExpirations(), 'Couldn\'t reconfigure expiration check')
	def test_expireCNT(self):
		self.assertIsNotNone(TestExpiration.cse)
		self.assertIsNotNone(TestExpiration.ae)
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'et' : getDate(expirationCheckDelay) # 2 seconds in the future
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.created)
		time.sleep(expirationSleep)	# give the server a moment to expire the resource
		
		r, rsc = RETRIEVE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.notFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(isTestExpirations(), 'Couldn\'t reconfigure expiration check')
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

		r, rsc = RETRIEVE(f'{cntURL}/{cinRn}', TestExpiration.originator)
		self.assertEqual(rsc, RC.OK)
		time.sleep(expirationSleep)	# give the server a moment to expire the resource

		r, rsc = RETRIEVE(cntURL, TestExpiration.originator)	# retrieve CNT again
		self.assertEqual(rsc, RC.notFound)

		r, rsc = RETRIEVE(f'{cntURL}/{cinRn}', TestExpiration.originator)	# retrieve CIN again
		self.assertEqual(rsc, RC.notFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTWithToLargeET(self):
		self.assertIsNotNone(TestExpiration.cse)
		self.assertIsNotNone(TestExpiration.ae)
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'et' : '99991231T235959'	# wrongly updated
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
		# should fail


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWithEtNull(self):
		self.assertIsNotNone(TestExpiration.cse)
		self.assertIsNotNone(TestExpiration.ae)
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'et' : getDate(60) # 1 minute in the future
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone((origEt := findXPath(r, 'm2m:cnt/et')))
		jsn = 	{ 'm2m:cnt' : { 
					'et' : None # 1 minute in the future
				}}
		r, rsc = UPDATE(cntURL, TestExpiration.originator, jsn)
		self.assertEqual(rsc, RC.updated)
	
		r, rsc = DELETE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(isTestExpirations(), 'Couldn\'t reconfigure expiration check')
	def test_expireCNTViaMIA(self):
		self.assertIsNotNone(TestExpiration.cse)
		self.assertIsNotNone(TestExpiration.ae)
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'mia': expirationCheckDelay
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cnt/mia'), expirationCheckDelay)

		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'AnyValue'
				}}

		for _ in range(0, 5):
			r, rsc = CREATE(cntURL, TestExpiration.originator, T.CNT, jsn)
			self.assertEqual(rsc, RC.created)

		time.sleep(expirationSleep)	# give the server a moment to expire the CIN's

		r, rsc = RETRIEVE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 0)	# no children anymore

		r, rsc = DELETE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(isTestExpirations(), 'Couldn\'t reconfigure expiration check')
	def test_expireCNTViaMIALarge(self):
		self.assertIsNotNone(TestExpiration.cse)
		self.assertIsNotNone(TestExpiration.ae)
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'mia': tooLargeExpirationDelta()
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cnt/mia'), tooLargeExpirationDelta())

		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'AnyValue'
				}}
		tooLargeET = getDate(tooLargeExpirationDelta())
		for _ in range(0, 5):
			r, rsc = CREATE(cntURL, TestExpiration.originator, T.CNT, jsn)
			self.assertEqual(rsc, RC.created)
			self.assertLess(findXPath(r, 'm2m:cin/et'), tooLargeET)

		time.sleep(expirationSleep)	# give the server a moment to expire the CIN's (which should not happen this time)

		r, rsc = RETRIEVE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 5)	# Still all children

		r, rsc = DELETE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(isTestExpirations(), 'Couldn\'t reconfigure expiration check')
	def test_expireFCNTViaMIA(self):
		self.assertIsNotNone(TestExpiration.cse)
		self.assertIsNotNone(TestExpiration.ae)
		jsn = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND,
					'mia'	: expirationCheckDelay,
					'curTe'	: 23.0
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.FCNT, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'cod:tempe/mia'), expirationCheckDelay)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 1)
		self.assertGreater(findXPath(r, 'cod:tempe/cbs'), 0)	

		jsn = 	{ 'cod:tempe' : {
					'tarTe':	5.0
				}}
		for _ in range(0, 5):
			r, rsc = UPDATE(fcntURL, TestExpiration.originator, jsn)
			self.assertEqual(rsc, RC.updated)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 6)
		self.assertGreater(findXPath(r, 'cod:tempe/cbs'), 0)	

		time.sleep(expirationSleep)	# give the server a moment to expire the CIN's

		r, rsc = RETRIEVE(fcntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 0)	# no children anymore
		self.assertEqual(findXPath(r, 'cod:tempe/cbs'), 0)	

		r, rsc = DELETE(fcntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.deleted)
# TODO same with fcnt

def run():
	suite = unittest.TestSuite()
	suite.addTest(TestExpiration('test_expireCNT'))
	suite.addTest(TestExpiration('test_expireCNTAndCIN'))
	suite.addTest(TestExpiration('test_createCNTWithToLargeET'))
	suite.addTest(TestExpiration('test_createCNTExpirationInThePast'))
	suite.addTest(TestExpiration('test_updateCNTWithEtNull'))
	suite.addTest(TestExpiration('test_expireCNTViaMIA'))
	suite.addTest(TestExpiration('test_expireCNTViaMIALarge'))
	suite.addTest(TestExpiration('test_expireFCNTViaMIA'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)