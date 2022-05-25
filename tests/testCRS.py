#
#	testCRS.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CRS functionality & notifications
#

import unittest, sys, time
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import NotificationEventType as NET, ResourceTypes as T, NotificationContentType, ResponseStatusCode as RC
from acme.etc.Types import ResultContentType as RCN
from init import *

cntRN1 = f'{cntRN}1'
cntRN2 = f'{cntRN}2'
cntRN3 = f'{cntRN}3'

class TestCRS(unittest.TestCase):
	ae 				= None
	cnt1 			= None
	cnt2 			= None
	cnt3 			= None
	cnt1RI 			= None
	cnt2RI 			= None
	cnt3RI 			= None
	crs 			= None
	originator 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		# Start notification server
		startNotificationServer()

		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'

		# create AE
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : True,
				 	'srv' : [ '3' ],
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		# create CNT1 & CNT2 & CNT3
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN1
				}}
		cls.cnt1, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		cls.cnt1RI = findXPath(cls.cnt1, 'm2m:cnt/ri')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN2
				}}
		cls.cnt2, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		cls.cnt2RI = findXPath(cls.cnt2, 'm2m:cnt/ri')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN3
				}}
		cls.cnt3, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		cls.cnt3RI = findXPath(cls.cnt3, 'm2m:cnt/ri')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		#DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)




	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSmissingRratSratFail(self) -> None:
		"""	CREATE <CRS> with both missing rrat and srat -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCRS',
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					# missing rrat/srat
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSmissingNuFail(self) -> None:
		"""	CREATE <CRS> with missing nu -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCRS',
					# missing nu
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI]
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSmissingTwtFail(self) -> None:
		"""	CREATE <CRS> with missing twt -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCRS',
					'nu' : [ NOTIFICATIONSERVER ],
					# missing twt
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI]
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwrongTwtFail(self) -> None:
		"""	CREATE <CRS> with wrong twt -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCRS',
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 99,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI]
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSmissingTwsFail(self) -> None:
		"""	CREATE <CRS> with missing tws -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCRS',
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'rrat': [ self.cnt1RI, self.cnt2RI]
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSemptyEncsFail(self) -> None:
		"""	CREATE <CRS> with empty encs -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCRS',
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': [],
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSWrongNumberEncsFail(self) -> None:
		"""	CREATE <CRS> with wrong number of encs -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCRS',
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': [
						{ 'enc' : {
								'net': [ NET.createDirectChild ],
							}
						},
						{ 'enc' : {
								'net': [ NET.createDirectChild ],
							}
						},
						{ 'enc' : {
								'net': [ NET.createDirectChild ],
							}
						}
					],
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	#
	#	RRAT testing
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithRrat(self) -> None:
		"""	CREATE <CRS> with rrat, one encs"""
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': [
						{ 'enc' : {
								'net': [ NET.createDirectChild ],
							}
						}
					]
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.created, TestCRS.crs)

		# check subscriptions
		self._testSubscriptionForCnt(cntRN1)
		self._testSubscriptionForCnt(cntRN2)
		self._testSubscriptionForCnt(cntRN3, False)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithNewRrat(self) -> None:
		"""	CREATE <CRS> with a new rrat, one encs"""
		dct = 	{ 'm2m:crs' : { 
					'rrat': [ self.cnt1RI, self.cnt2RI, self.cnt3RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.updated, TestCRS.crs)

		# check subscriptions
		self._testSubscriptionForCnt(cntRN1)
		self._testSubscriptionForCnt(cntRN2)
		self._testSubscriptionForCnt(cntRN3)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithLessRrat(self) -> None:
		"""	CREATE <CRS> with a removed rrat, one encs"""
		dct = 	{ 'm2m:crs' : { 
					'rrat': [ self.cnt1RI, self.cnt3RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.updated, TestCRS.crs)

		# check subscriptions
		self._testSubscriptionForCnt(cntRN1)
		self._testSubscriptionForCnt(cntRN2, False)	# should be deleted
		self._testSubscriptionForCnt(cntRN3)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCRSwithRrat(self) -> None:
		"""	DELETE <CRS> with rrat"""
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.deleted, r)
		self._testSubscriptionForCnt(cntRN1, False)
		self._testSubscriptionForCnt(cntRN2, False)
		self._testSubscriptionForCnt(cntRN3, False)


	def _testSubscriptionForCnt(self, cnt:str, present:bool = True) -> None:
		"""	Test whether there is exactly one or none subscription for a container.
		"""
		r, rsc = RETRIEVE(f'{aeURL}/{cnt}?fu=1&rcn={int(RCN.childResourceReferences)}&ty={int(T.SUB)}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 1 if present else 0)


# TODO rrat to unknown cnt
# TODO test  : delete crs, subs need to be removed as well
# TODO test twt missing, oiut of range
# TODO test tws

def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()

	suite.addTest(TestCRS('test_createCRSmissingRratSratFail'))
	suite.addTest(TestCRS('test_createCRSmissingNuFail'))
	suite.addTest(TestCRS('test_createCRSmissingTwtFail'))
	suite.addTest(TestCRS('test_createCRSwrongTwtFail'))
	suite.addTest(TestCRS('test_createCRSmissingTwsFail'))
	suite.addTest(TestCRS('test_createCRSemptyEncsFail'))
	suite.addTest(TestCRS('test_createCRSWrongNumberEncsFail'))

	# Test rrat
	suite.addTest(TestCRS('test_createCRSwithRrat'))
	suite.addTest(TestCRS('test_updateCRSwithNewRrat'))
	suite.addTest(TestCRS('test_updateCRSwithLessRrat'))
	suite.addTest(TestCRS('test_deleteCRSwithRrat'))

	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
