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
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from rich import print
from acme.etc.Constants import Constants as C
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from acme.etc.DateUtils import getResourceDate
from init import *


CND = 'org.onem2m.common.moduleclass.temperature'

class TestExpiration(unittest.TestCase):

	ae 				= None
	originator 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestExpiration')

		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		testCaseEnd('Setup TestExpiration')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestExpiration')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestExpiration')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_expireCNT(self) -> None:
		""" Create and expire <CNT> """
		self.assertTrue(isTestResourceExpirations())
		self.assertIsNotNone(TestExpiration.ae)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'et' : getResourceDate(expirationCheckDelay) # 2 seconds in the future
				}}
		_, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		testSleep(expirationSleep)	# give the server a moment to expire the resource
		
		_, rsc = RETRIEVE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.NOT_FOUND)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_expireCNTAndCIN(self) -> None:
		""" Create and expire <CNT> and <CIN> """
		self.assertTrue(isTestResourceExpirations())
		self.assertIsNotNone(TestExpiration.ae)
		dct = 	{ 'm2m:cnt' : { 
					'et' : getResourceDate(expirationCheckDelay), # 2 seconds in the future
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'AnyValue'
				}}
		for _ in range(0, 5):
			r, rsc = CREATE(cntURL, TestExpiration.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED)
			cinRn = findXPath(r, 'm2m:cin/rn')
		self.assertIsNotNone(cinRn)

		r, rsc = RETRIEVE(f'{cntURL}/{cinRn}', TestExpiration.originator)
		self.assertEqual(rsc, RC.OK)
		testSleep(expirationSleep)	# give the server a moment to expire the resource

		r, rsc = RETRIEVE(cntURL, TestExpiration.originator)	# retrieve CNT again
		self.assertEqual(rsc, RC.NOT_FOUND)

		r, rsc = RETRIEVE(f'{cntURL}/{cinRn}', TestExpiration.originator)	# retrieve CIN again
		self.assertEqual(rsc, RC.NOT_FOUND)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTWithToLargeET(self) -> None:
		"""	Create <CNT> and long ET -> Corrected ET """
		self.assertIsNotNone(TestExpiration.ae)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'et' : futureTimestamp	# wrongly updated
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertLess(findXPath(r, 'm2m:cnt/et'), futureTimestamp)
		r, rsc = DELETE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTExpirationInThePast(self) -> None:
		"""	Create <CNT> and ET in the past -> Fail """
		self.assertIsNotNone(TestExpiration.ae)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'et' : getResourceDate(-60) # 1 minute in the past
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)
		# should fail


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWithEtNull(self) -> None:
		""" Update <CNT> and remove ET in another update """
		self.assertIsNotNone(TestExpiration.ae)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'et' : getResourceDate(60) # 1 minute in the future
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone((origEt := findXPath(r, 'm2m:cnt/et')))
		dct = 	{ 'm2m:cnt' : { 
					'et' : None # 1 minute in the future
				}}
		r, rsc = UPDATE(cntURL, TestExpiration.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
	
		r, rsc = DELETE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_expireCNTViaMIA(self) -> None:
		""" Expire <CNT> via MIA """
		self.assertTrue(isTestResourceExpirations())
		self.assertIsNotNone(TestExpiration.ae)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'mia': expirationCheckDelay
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertEqual(findXPath(r, 'm2m:cnt/mia'), expirationCheckDelay)

		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'AnyValue'
				}}

		for _ in range(0, 5):
			r, rsc = CREATE(cntURL, TestExpiration.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED)

		testSleep(expirationSleep)	# give the server a moment to expire the CIN's

		r, rsc = RETRIEVE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 0)	# no children anymore

		r, rsc = DELETE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_expireCNTViaMIALarge(self) -> None:
		""" Expire <CNT> via too large MIA """
		self.assertTrue(isTestResourceExpirations())
		self.assertIsNotNone(TestExpiration.ae)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'mia': tooLargeResourceExpirationDelta()
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertEqual(findXPath(r, 'm2m:cnt/mia'), tooLargeResourceExpirationDelta())

		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'AnyValue'
				}}
		tooLargeET = getResourceDate(tooLargeResourceExpirationDelta())
		for _ in range(0, 5):
			r, rsc = CREATE(cntURL, TestExpiration.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED)
			self.assertLess(findXPath(r, 'm2m:cin/et'), tooLargeET)

		testSleep(expirationSleep)	# give the server a moment to expire the CIN's (which should not happen this time)

		r, rsc = RETRIEVE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 5)	# Still all children

		r, rsc = DELETE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_expireFCNTViaMIA(self) -> None:
		""" Expire <FCNT> via MIA """
		self.assertTrue(isTestResourceExpirations())
		self.assertIsNotNone(TestExpiration.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND,
					'mia'	: expirationCheckDelay,
					'curT0'	: 23.0
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'cod:tempe/mia'), expirationCheckDelay)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 1, r)
		self.assertGreater(findXPath(r, 'cod:tempe/cbs'), 0)	

		dct = 	{ 'cod:tempe' : {
					'tarTe':	5.0
				}}
		for _ in range(0, 5):
			r, rsc = UPDATE(fcntURL, TestExpiration.originator, dct)
			self.assertEqual(rsc, RC.UPDATED)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 6)
		self.assertGreater(findXPath(r, 'cod:tempe/cbs'), 0)	

		testSleep(expirationSleep)	# give the server a moment to expire the CIN's

		r, rsc = RETRIEVE(fcntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 0)	# no children anymore
		self.assertEqual(findXPath(r, 'cod:tempe/cbs'), 0)	

		r, rsc = DELETE(fcntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_expirationLaterThanParents(self) -> None:
		""" Create CNT with et later than the parent's et """
		self.assertIsNotNone(TestExpiration.ae)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'et' : (parentET := getResourceDate(60)) # 1 minute in the future
				}}
		r, rsc = CREATE(aeURL, TestExpiration.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'et' : getResourceDate(120) # 2 minutes in the future
				}}
		r, rsc = CREATE(cntURL, TestExpiration.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)

		self.assertIsNotNone((childET := findXPath(r, 'm2m:cnt/et')))
		self.assertEqual(parentET, childET)

		r, rsc = DELETE(cntURL, TestExpiration.originator)
		self.assertEqual(rsc, RC.DELETED)



def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	# Reconfigure the server to check faster for expirations.
	enableShortResourceExpirations()
	if not isTestResourceExpirations():
		print('\n[red reverse] Error configuring the CSE\'s test settings ')
		print('Did you enable [i]remote configuration[/i] for the CSE?\n')
		return 0,0,1,0.0	

	suite = unittest.TestSuite()
			
	addTest(suite, TestExpiration('test_expireCNT'))
	addTest(suite, TestExpiration('test_expireCNTAndCIN'))
	addTest(suite, TestExpiration('test_createCNTWithToLargeET'))
	addTest(suite, TestExpiration('test_createCNTExpirationInThePast'))
	addTest(suite, TestExpiration('test_updateCNTWithEtNull'))
	addTest(suite, TestExpiration('test_expireCNTViaMIA'))
	addTest(suite, TestExpiration('test_expireCNTViaMIALarge'))
	addTest(suite, TestExpiration('test_expireFCNTViaMIA'))
	addTest(suite, TestExpiration('test_expirationLaterThanParents'))


	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	disableShortResourceExpirations()
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)