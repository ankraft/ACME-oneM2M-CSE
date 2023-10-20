#
#	testCRS.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CRS functionality & notifications
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import DesiredIdentifierResultType as DRT, NotificationEventType as NET, ResourceTypes as T, ResponseStatusCode as RC, TimeWindowType
from acme.etc.Types import ResultContentType as RCN
from acme.etc.DateUtils import getResourceDate
from init import *

cntRN1 = f'{cntRN}1'
cntRN2 = f'{cntRN}2'
cntRN3 = f'{cntRN}3'
subRN1 = f'{subRN}1'
subRN2 = f'{subRN}2'

class TestCRS(unittest.TestCase):
	ae 				= None
	cnt1 			= None
	cnt2 			= None
	cnt3 			= None
	cnt1RI 			= None
	cnt2RI 			= None
	cnt3RI 			= None
	sub1 			= None
	sub2 			= None
	sub1RI 			= None
	sub2RI 			= None
	crs 			= None
	originator 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestCRS')

		# Start notification server
		startNotificationServer()

		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'


		# create AE
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ],
					'poa' : [ NOTIFICATIONSERVER ],
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		# create CNT1 & CNT2 & CNT3
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN1
				}}
		cls.cnt1, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		cls.cnt1RI = findXPath(cls.cnt1, 'm2m:cnt/ri')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN2
				}}
		cls.cnt2, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		cls.cnt2RI = findXPath(cls.cnt2, 'm2m:cnt/ri')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN3
				}}
		cls.cnt3, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		cls.cnt3RI = findXPath(cls.cnt3, 'm2m:cnt/ri')

		testCaseEnd('Setup TestCRS')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			stopNotificationServer()
			return
		testCaseStart('TearDown TestCRS')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()
		testCaseEnd('TearDown TestCRS')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################
	#
	#	RRAT testing
	#

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
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


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
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


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
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


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
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


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
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSemptyEncsFail(self) -> None:
		"""	CREATE <CRS> with empty encs -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCRS',
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {},
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSWrongNumberEncsFail(self) -> None:
		"""	CREATE <CRS> with wrong number of encs -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCRS',
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': { 
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							},
							{
								'net': [ NET.createDirectChild ],
							},
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithRratsFail(self) -> None:
		"""	CREATE <CRS> with rrats -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
					'rrat2': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)


	#
	#	RRAT testing
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithRrat(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window"""
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# check subscriptions
		self.assertIsNotNone(rrats := findXPath(TestCRS.crs, 'm2m:crs/rrats'))
		self.assertEqual(len(rrats), 2)
		self.assertEqual(rrats[0], self._testSubscriptionForCnt(cntRN1), TestCRS.crs)
		self.assertEqual(rrats[1], self._testSubscriptionForCnt(cntRN2))
		self._testSubscriptionForCnt(cntRN3, False)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithSingleRratAndNSI(self) -> None:
		"""	CREATE <CRS> with a single rrat, one encs, periodic window, NSI enabled"""
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						},
					'nse' : True
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# check subscriptions
		self.assertIsNotNone(rrats := findXPath(TestCRS.crs, 'm2m:crs/rrats'))
		self.assertEqual(len(rrats), 1)
		self.assertEqual(rrats[0], self._testSubscriptionForCnt(cntRN1), TestCRS.crs)
		self._testSubscriptionForCnt(cntRN3, False)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithRratSlidingStatsEnabled(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, sliding window, stats enabled"""
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ TestCRS.originator ],
					'twt': 2,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						},
					'nse': True
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)
		self.assertTrue(findXPath(TestCRS.crs, 'm2m:crs/nse'))

		# check subscriptions
		self.assertIsNotNone(rrats := findXPath(TestCRS.crs, 'm2m:crs/rrats'))

		self.assertEqual(len(rrats), 2)
		self.assertEqual(rrats[0], self._testSubscriptionForCnt(cntRN1), TestCRS.crs)
		self.assertEqual(rrats[1], self._testSubscriptionForCnt(cntRN2))
		self._testSubscriptionForCnt(cntRN3, False)
		self.assertTrue(findXPath(TestCRS.crs, 'm2m:crs/nse'))
		self.assertIsNone(findXPath(TestCRS.crs, 'm2m:crs/nsi'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithNewRratFail(self) -> None:
		"""	UPDATE <CRS> with a new rrat -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'rrat': [ self.cnt1RI, self.cnt2RI, self.cnt3RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithrratsFail(self) -> None:
		"""	UPDATE <CRS> with a rrats -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'rrats': [ self.cnt1RI, self.cnt2RI, self.cnt3RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithNecFail(self) -> None:
		"""	UPDATE <CRS> with nec -> Fails"""
		dct = 	{ 'm2m:crs' : { 
			        'nec': 1
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithEncsFail(self) -> None:
		"""	UPDATE <CRS> with encs -> Fails"""
		dct = 	{ 'm2m:crs' : { 
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithDeletedEncsFail(self) -> None:
		"""	UPDATE <CRS> with deleted encs while rrat is present -> Fails"""
		dct = 	{ 'm2m:crs' : { 
			        'encs': None
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithRratAndEt(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, and et set"""
		et = getResourceDate(60)	# 1 minute in the future
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'et' : et, 
					'nu' : [ TestCRS.originator ],
					'twt' : 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
						]
					}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)
		self.assertEqual(findXPath(TestCRS.crs, 'm2m:crs/et'), et)
		self.assertIsNotNone(rrats := findXPath(TestCRS.crs, 'm2m:crs/rrats'))

		# check both subscriptions' et
		r, rsc = RETRIEVE(f'{CSEURL}/{rrats[0][1:]}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, TestCRS.crs)
		self.assertEqual(findXPath(r, 'm2m:sub/et'), et)
		r, rsc = RETRIEVE(f'{CSEURL}/{rrats[1][1:]}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, TestCRS.crs)
		self.assertEqual(findXPath(r, 'm2m:sub/et'), et)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithRratWrongTarget(self) -> None:
		"""	CREATE <CRS> with rrat with wrong target"""
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ TestCRS.originator ],
					'twt' : 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ 'wrongRI' ],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
						]
					}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CROSS_RESOURCE_OPERATION_FAILURE, TestCRS.crs)

	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCRSwithRrat(self) -> None:
		"""	DELETE <CRS> with rrat"""
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)
		self._testSubscriptionForCnt(cntRN1, False)
		self._testSubscriptionForCnt(cntRN2, False)
		self._testSubscriptionForCnt(cntRN3, False)


	#########################################################################
	#
	#	SRAT testing
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithSratNonSubFail(self) -> None:
		"""	CREATE <CRS> with srat pointing to non-<sub> -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'srat': [ self.cnt1RI ],	# Fail, no subscription
				}
		}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)
		self._testSubscriptionForCnt(cntRN1, False)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSubscriptions(self) -> None:
		"""	CREATE <SUB> resources for with srat tests"""

		# create SUB1 & SUB2
		dct = { 'm2m:sub' : {
					'rn' : subRN1,
					'nu' : [ NOTIFICATIONSERVER ],
					'enc' : {
						'net': [ NET.createDirectChild ],
					},
				}}
		TestCRS.sub1, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, self.sub1)
		TestCRS.sub1RI = findXPath(self.sub1, 'm2m:sub/ri')

		dct = { 'm2m:sub' : {
					'rn' : subRN2,
					'nu' : [ NOTIFICATIONSERVER ],
					'enc' : {
						'net': [ NET.createDirectChild ],
					},
				}}
		TestCRS.sub2, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, self.sub2)
		TestCRS.sub2RI = findXPath(self.sub2, 'm2m:sub/ri')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithSrat(self) -> None:
		"""	CREATE <CRS> with srat """
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ TestCRS.originator ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'srat': [ self.sub1RI ],
				}
		}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# check subscriptions
		self._testSubscriptionForCnt(cntRN1)
		self._testSubscriptionForCnt(cntRN2)
		self._testSubscriptionForCnt(cntRN3, False)

		# retrieve subs and check them directly
		spCrsRi = toSPRelative(findXPath(TestCRS.crs, 'm2m:crs/ri'))

		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/nu'))
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/acrs'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithNewSratFail(self) -> None:
		"""	UPDATE <CRS> with a new srat -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'srat': [ self.sub1RI, self.sub2RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCRSwithSrat(self) -> None:
		"""	DELETE <CRS> with srat"""
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)

		# retrieve subs and check them directly
		spCrsRi = toSPRelative(findXPath(TestCRS.crs, 'm2m:crs/ri'))

		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertNotIn(spCrsRi, findXPath(r, 'm2m:sub/nu'), r)
		self.assertIsNone(findXPath(r, 'm2m:sub/acrs'), r)

		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub2RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertNotIn(spCrsRi, findXPath(r, 'm2m:sub/nu'), r)
		self.assertIsNone(findXPath(r, 'm2m:sub/acrs'), r)

		# Check CNT's <sub>
		self._testSubscriptionForCnt(cntRN3, False)		# should not be there


	#########################################################################
	#
	#	Delete Subscriptions
	# 

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteRratSubscription(self) -> None:
		"""	DELETE <SUB> resource (<CRS> and second <SUB> shall be deleted as well)"""
		self.assertIsNotNone(rrats := findXPath(TestCRS.crs, 'm2m:crs/rrats'))
		self.assertEqual(len(rrats), 2)

		r, rsc = DELETE(f'{CSEURL}/{rrats[0][1:]}', TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)

		# Look for the other subscription and crs
		r, rsc = RETRIEVE(f'{CSEURL}/{rrats[1][1:]}', TestCRS.originator)
		self.assertEqual(rsc, RC.NOT_FOUND, r)
		r, rsc = RETRIEVE(f'{crsURL}', TestCRS.originator)
		self.assertEqual(rsc, RC.NOT_FOUND, r)

		TestCRS.sub1RI = None
		TestCRS.sub2RI = None


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSrat2Subscriptions(self) -> None:
		"""	CREATE <CRS> with two <SUB> in srat"""
		self.assertIsNotNone(self.sub1RI)
		self.assertIsNotNone(self.sub2RI)
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ TestCRS.originator ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'srat': [ self.sub1RI, self.sub2RI ],	
				}}
		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSratSubscription(self) -> None:
		"""	DELETE <SUB> resource (CRS and second SUB shall be deleted as well)"""
		self.assertIsNotNone(srat := findXPath(TestCRS.crs, 'm2m:crs/srat'))
		self.assertEqual(len(srat), 2)

		r, rsc = DELETE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)

		# Look for the other subscription and crs
		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub2RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		r, rsc = RETRIEVE(f'{crsURL}', TestCRS.originator)
		self.assertEqual(rsc, RC.NOT_FOUND, r)

		TestCRS.sub1RI = None # Only sub1 is deleted, not sub2


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSubscriptions(self) -> None:
		"""	DELETE <SUB> resources if present"""
		if TestCRS.sub1RI:
			r, rsc = DELETE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator)
			self.assertEqual(rsc, RC.DELETED, r)
			TestCRS.sub1RI = None

		if TestCRS.sub2RI:
			r, rsc = DELETE(f'{csiURL}/{TestCRS.sub2RI}', TestCRS.originator)
			self.assertEqual(rsc, RC.DELETED, r)
			TestCRS.sub2RI = None


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSubAcrs(self) -> None:
		"""	UPDATE <SUB> acrs (delete <CRS>)"""
		dct:JSON = { 'm2m:sub' : {
					'acrs' : []
		}}
		r, rsc = UPDATE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertNotIn(findXPath(TestCRS.crs, 'm2m:crs/ri'), findXPath(r, 'm2m:sub/acrs'))

		# Check that CRS was deleted
		r, rsc = RETRIEVE(f'{crsURL}', TestCRS.originator)
		self.assertEqual(rsc, RC.NOT_FOUND, r)
		# Check that CRS was removed from second <SUB>
		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub2RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertTrue( not findXPath(r, 'm2m:sub/acrs')) # either None or empty

	#########################################################################
	#
	#	Sliding Window notifications testing
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSingleNotificationNoNotification(self) -> None:
		"""	CREATE <CIN> to raise a single notification (no notification from crs)"""
		clearLastNotification()
		dct:JSON = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, self.sub1)
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(getLastNotification())


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTwoSingleNotificationNoNotifications(self) -> None:
		"""	CREATE two <CIN> with delay to raise two notification (no notification from crs)"""
		clearLastNotification()
		dct:JSON = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}

		# CIN to first CNT
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, self.sub1)
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(getLastNotification())

		# CIN two second CNT
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, self.sub1)
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(getLastNotification())


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTwoNotificationOneNotification(self) -> None:
		"""	CREATE two <CIN> to raise two notifications (plus one notification from crs)"""
		clearLastNotification()

		# Restart the window timer
		dct:JSON = 	{ 'm2m:crs' : { 
			'twt': (_twt := findXPath(TestCRS.crs, 'm2m:crs/twt')),
			'tws': (_tws := f'PT{crsTimeWindowSize}S'),
		}}
		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCRS.crs)
		self.assertEqual(findXPath(TestCRS.crs, 'm2m:crs/twt'), _twt)
		self.assertEqual(findXPath(TestCRS.crs, 'm2m:crs/tws'), _tws)

		# Create 
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)	

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSPeriodicWindowSize(self) -> None:
		"""	UPDATE CRS with new Periodic window size and create two notifications"""
		
		# update 
		tws = f'PT{crsTimeWindowSize * 2}S'
		dct:JSON = { 'm2m:crs' : {
					'tws' : tws,
		}}
		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCRS.crs)
		self.assertEqual(findXPath(TestCRS.crs, 'm2m:crs/tws'), tws)

		clearLastNotification()

		# create <cin>
		dct = { 'm2m:cin' : {
					'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)	

		# wait and check notification at around half the time
		testSleep(crsTimeWindowSize * 1.2)
		self.assertIsNone(notification := getLastNotification())

		# wait second half
		testSleep(crsTimeWindowSize * 1.2)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri')))



	#########################################################################
	#
	#	Sliding window testing
	#


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_enableSlidingWindow(self) -> None:
		"""	UPDATE <CRS> with a twt = SLIDING"""
		dct = 	{ 'm2m:crs' : { 
					'twt': TimeWindowType.SLIDINGWINDOW,
					'tws': f'PT{crsTimeWindowSize * 2}S'
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSSlidingWindowSize(self) -> None:
		"""	UPDATE CRS with new Sliding window size and create two notifications"""
		
		# update 
		tws = f'PT{crsTimeWindowSize * 2}S'
		dct:JSON = { 'm2m:crs' : {
					'tws' : tws,
		}}
		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCRS.crs)
		self.assertEqual(findXPath(TestCRS.crs, 'm2m:crs/tws'), tws)

		clearLastNotification()

		# create <cin>
		dct = { 'm2m:cin' : {
					'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification at half the time
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(notification := getLastNotification())

		# wait a bit longer to wait the second notification
		testSleep(crsTimeWindowSize * 0.2)
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)	

		testSleep(crsTimeWindowSize * 0.8)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri')))


	#########################################################################
	#
	#	Notification Stats
	#



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCRSwithNSENSINone(self) -> None:
		"""	RETRIEVE <CRS> with NSE set to True and no NSI"""
		TestCRS.crs, rsc = RETRIEVE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.OK, TestCRS.crs)

		self.assertTrue(findXPath(TestCRS.crs, 'm2m:crs/nse'))
		self.assertIsNone(findXPath(TestCRS.crs, 'm2m:crs/nsi'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithDeletedNse(self) -> None:
		"""	UPDATE <CRS> with deleted NSE"""
		dct = 	{ 'm2m:crs' : { 
					'nse': None,
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCRS.crs)
		self.assertIsNone(findXPath(TestCRS.crs, 'm2m:crs/nse'), TestCRS.crs)
		self.assertIsNone(findXPath(TestCRS.crs, 'm2m:crs/nsi'), TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithDeletedNsi(self) -> None:
		"""	UPDATE <CRS> with deleted NSI -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'nsi': None,
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testEmptyNsi(self) -> None:
		"""	Test for empty NSI """
		TestCRS.crs, rsc = RETRIEVE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.OK, TestCRS.crs)
		self.assertTrue(findXPath(TestCRS.crs, 'm2m:crs/nse'))
		self.assertIsNone(findXPath(TestCRS.crs, 'm2m:crs/nsi'), TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithEnableNSE(self) -> None:
		"""	UPDATE <CRS> with NSE set to True"""
		dct = 	{ 'm2m:crs' : { 
					'nse': True,
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCRS.crs)
		self.assertIsNotNone(findXPath(TestCRS.crs, 'm2m:crs/nse'), TestCRS.crs)
		# nsi must be empty
		self.assertIsNone(findXPath(TestCRS.crs, 'm2m:crs/nsi'), TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testNonEmptyNsi(self) -> None:
		"""	Test for non-empty NSE """
		TestCRS.crs, rsc = RETRIEVE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.OK, TestCRS.crs)
		self.assertTrue(findXPath(TestCRS.crs, 'm2m:crs/nse'))
		self.assertEqual(len( nsi := findXPath(TestCRS.crs, 'm2m:crs/nsi')), 1, TestCRS.crs)
		self.assertEqual(findXPath(nsi, '{0}/tg'), TestCRS.originator, TestCRS.crs)	
		self.assertEqual(findXPath(nsi, '{0}/rqs'), 1)	
		self.assertEqual(findXPath(nsi, '{0}/rsr'), 1)	
		self.assertEqual(findXPath(nsi, '{0}/noec'), 1)	


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithNseFalse(self) -> None:
		"""	UPDATE <CRS> with NSE False"""
		dct = 	{ 'm2m:crs' : { 
					'nse': False,
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCRS.crs)
		self.assertFalse(findXPath(TestCRS.crs, 'm2m:crs/nse'))
		self.assertEqual(len( nsi := findXPath(TestCRS.crs, 'm2m:crs/nsi')), 1)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithNseTrue(self) -> None:
		"""	UPDATE <CRS> with NSE True"""
		dct = 	{ 'm2m:crs' : { 
					'nse': True,
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCRS.crs)
		self.assertTrue(findXPath(TestCRS.crs, 'm2m:crs/nse', TestCRS.crs))
		# nsi must be empty
		self.assertIsNone(findXPath(TestCRS.crs, 'm2m:sub/nsi'), TestCRS.crs)


	#########################################################################
	#
	#	Expiration Counter
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithExpiration(self) -> None:
		"""	CREATE <CRS> with expiration """
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ TestCRS.originator ],
					'twt': 2,	# SLIDINGWINDOW
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						},
					'exc': 2
				}}
		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# create CIN to cause notifications
		for _ in range(2):
			dct = 	{ 'm2m:cin' : {
				'con' : 'AnyValue',
			}}
			r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED, self.sub1)
			r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED, self.sub1)
			testSleep(crsTimeWindowSize + 1.0)
		
		# Check that the <crs> is not present anymore
		TestCRS.crs, rsc = RETRIEVE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.NOT_FOUND, TestCRS.crs)


	#########################################################################
	#
	#	Deletion Notification
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testCRSwithSu(self) -> None:
		""" CREATE <CRS> subscriber URI and DELETE"""
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ TestCRS.originator ],
					'twt': 2,	# SLIDINGWINDOW
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						},
					'su': TestCRS.originator
				}}
		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)
		self.assertEqual(findXPath(TestCRS.crs, 'm2m:crs/su'), TestCRS.originator)

		clearLastNotification()
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)
		notification = getLastNotification(wait = notificationDelay)
		self.assertTrue(findXPath(notification, 'm2m:sgn/sud'))



	#########################################################################
	#
	#	TimeWindowInterpretation
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCorrectEEM12345TWT1(self) -> None:
		"""	CREATE <CRS> with EEM (1,2,3,4,5) and TWT 1 (PERIODIC)"""
		for eem in (1,2,3,4,5):
			dct = 	{ 'm2m:crs' : { 
						'rn' : crsRN,
						'nu' : [ TestCRS.originator ],
						'twt': 1,	# PERIODIC
						'eem': eem,
						'tws' : f'PT{crsTimeWindowSize}S',
						'rrat': [ self.cnt1RI, self.cnt2RI],
						'encs': {
							'enc' : [
								{
									'net': [ NET.createDirectChild ],
								}
								]
							},
						'su': TestCRS.originator
					}}
			TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
			self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

			# DELETE again
			r, rsc = DELETE(crsURL, TestCRS.originator)
			self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCorrectEEM125TWT2(self) -> None:
		"""	CREATE <CRS> with EEM (1,2,5) and TWT 2 (SLIDINGWINDOW)"""
		for eem in (1,2,5):
			dct = 	{ 'm2m:crs' : { 
						'rn' : crsRN,
						'nu' : [ TestCRS.originator ],
						'twt': 2,	# SLIDINGWINDOW
						'eem': eem,
						'tws' : f'PT{crsTimeWindowSize}S',
						'rrat': [ self.cnt1RI, self.cnt2RI],
						'encs': {
							'enc' : [
								{
									'net': [ NET.createDirectChild ],
								}
								]
							},
						'su': TestCRS.originator
					}}
			TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
			self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

			# DELETE again
			r, rsc = DELETE(crsURL, TestCRS.originator)
			self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createWrongEEM34TWT2(self) -> None:
		"""	CREATE <CRS> with EEM (3,4) and TWT 2 (SLIDINGWINDOW) -> Fail"""
		for eem in (3,4):
			dct = 	{ 'm2m:crs' : { 
						'rn' : crsRN,
						'nu' : [ TestCRS.originator ],
						'twt': 2,	# SLIDINGWINDOW
						'eem': eem,
						'tws' : f'PT{crsTimeWindowSize}S',
						'rrat': [ self.cnt1RI, self.cnt2RI],
						'encs': {
							'enc' : [
								{
									'net': [ NET.createDirectChild ],
								}
								]
							},
						'su': TestCRS.originator
					}}
			TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
			self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCorrectEEM12345TWT1(self) -> None:
		"""	UPDATE <CRS> with EEM (1,2,3,4,5) and TWT 1 (PERIODIC)"""

		# First create correct CRS
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ TestCRS.originator ],
					'twt': 1,	# PERIODIC
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						},
					'su': TestCRS.originator
				}}
		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# Loop and UPDATE
		for eem in (1,2,3,4,5):
			# UPDATE with wrong eem
			dct = 	{ 'm2m:crs' : { 
						'eem': eem,	
					}}
			TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
			self.assertEqual(rsc, RC.UPDATED, TestCRS.crs)

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCorrectEEM125TWT2(self) -> None:
		"""	UPDATE <CRS> with EEM (1,2,5) and TWT 2 (SLIDINGWINDOW)"""

		# First create correct CRS
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ TestCRS.originator ],
					'twt': 2, # SLIDINGWINDOW
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						},
					'su': TestCRS.originator
				}}
		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# Loop and UPDATE
		for eem in (1,2,5):
			# UPDATE with wrong eem
			dct = 	{ 'm2m:crs' : { 
						'eem': eem,	
					}}
			TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
			self.assertEqual(rsc, RC.UPDATED, TestCRS.crs)
		

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateWrongEEM34TWT2(self) -> None:
		"""	UPDATE <CRS> with EEM (3,4) and TWT 2 (SLIDINGWINDOW) -> Fail"""
		# First create correct CRS
		dct = 	{ 'm2m:crs' : {
					'rn' : crsRN,
					'nu' : [ TestCRS.originator ],
					'twt': 2,	# SLIDINGWINDOW
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
					'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						},
					'su': TestCRS.originator
				}}
		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)
				
		# Loop and UPDATE
		for eem in (3,4):
			dct = 	{ 'm2m:crs' : { 
						'eem': eem,	
					}}
			TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct) # type: ignore
			self.assertEqual(rsc, RC.BAD_REQUEST, TestCRS.crs)

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator) # type: ignore
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicAllSomeEventsPresentAll(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, all or some events present, all events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ], # type: ignore
					'twt': 1, # periodic
					'eem': 2, # ALL_OR_SOME_EVENTS_PRESENT
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct) # type: ignore
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct) # type: ignore
		self.assertEqual(rsc, RC.CREATED, r)
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct) # type: ignore
		self.assertEqual(rsc, RC.CREATED, r)	

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri'))) # type: ignore

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator) # type: ignore
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicAllSomeEventsPresentSome(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, all or some events present, some events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ], # type: ignore
					'twt': 1, # periodic
					'eem': 2, # ALL_OR_SOME_EVENTS_PRESENT
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri')))

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicAllSomeEventsPresentNone(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, all or some events present, no events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1, # periodic
					'eem': 2, # ALL_OR_SOME_EVENTS_PRESENT
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create NO event

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(notification := getLastNotification())

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicAllSomeEventsMissingAll(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, all or some events missing, all events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1, # periodic
					'eem': 3, # All_OR_SOME_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(notification := getLastNotification())

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicAllSomeEventsMissingSome(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, all or some events missing, some events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1, # periodic
					'eem': 3, # All_OR_SOME_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri')))

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicAllSomeEventsMissingNone(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, all or some events missing, no event"""
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1, # periodic
					'eem': 3, # All_OR_SOME_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create NO CIN

		# wait and check notification
		clearLastNotification()
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri')))

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicAllEventsMissingAll(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, all events missing, all events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1, # periodic
					'eem': 4, # All_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(notification := getLastNotification())

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicAllEventsMissingSome(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, all events missing, some events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1, # periodic
					'eem': 4, # ALL_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(notification := getLastNotification())

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicAllEventsMissingNone(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, all events missing, no event"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1, # periodic
					'eem': 4, # ALL_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create NO CIN

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri')))

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSSlidingAllSomeEventsPresentAll(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, sliding window, all or some events present, all events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ], # type: ignore
					'twt': 2, # sliding
					'eem': 2, # ALL_OR_SOME_EVENTS_PRESENT
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct) # type: ignore
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct) # type: ignore
		self.assertEqual(rsc, RC.CREATED, r)
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct) # type: ignore
		self.assertEqual(rsc, RC.CREATED, r)	

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri'))) # type: ignore

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator) # type: ignore
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSSlidingAllSomeEventsPresentSome(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, sliding window, all or some events present, some events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ], # type: ignore
					'twt': 2, # sliding
					'eem': 2, # ALL_OR_SOME_EVENTS_PRESENT
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri')))

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSSlidingAllSomeEventsPresentNone(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, sliding window, all or some events present, no events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 2, # sliding
					'eem': 2, # ALL_OR_SOME_EVENTS_PRESENT
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create NO event

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(notification := getLastNotification())

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicSomeEventsMissingAll(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, some events missing, all events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1, # periodic
					'eem': 5, # SOME_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(notification := getLastNotification())

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicSomeEventsMissingSome(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, some events missing, some events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1, # periodic
					'eem': 5, # SOME_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri')))

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSPeriodicSomeEventsMissingNone(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, periodic window, some events missing, no event"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 1, # periodic
					'eem': 5, # SOME_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create NO CIN

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(notification := getLastNotification())

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSSlidingSomeEventsMissingAll(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, sliding window, some events missing, all events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 2, # sliding
					'eem': 5, # SOME_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(notification := getLastNotification())

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSSlidingSomeEventsMissingSome(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, sliding window, some events missing, some events"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 2, # sliding
					'eem': 5, # SOME_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create one CIN
		dct = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNotNone(notification := getLastNotification())
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn'))
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), toSPRelative(findXPath(self.crs, 'm2m:crs/ri')))

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSSlidingSomeEventsMissingNone(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, sliding window, some events missing, no event"""
		clearLastNotification()
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ '/id-in/'+TestCRS.originator ],
					'twt': 2, # sliding
					'eem': 5, # SOME_EVENTS_MISSING
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, TestCRS.crs)

		# NO subscription checking here. Done in other tests already

		# Create NO CIN

		# wait and check notification
		testSleep(crsTimeWindowSize + 1.0)
		self.assertIsNone(notification := getLastNotification())

		# DELETE again
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.DELETED, r)

	#########################################################################

	def _testSubscriptionForCnt(self, cnt:str, present:bool = True) -> str:
		"""	Test whether there is exactly one or none subscription for a container.
			
			Args:
				cnt: ResourceID of the container.
				present: Whether the <SUB> shall or shall not be present
			Return:
				The resourceID of the found <SUB> resource
		"""
		r, rsc = RETRIEVE(f'{aeURL}/{cnt}?fu=1&rcn={int(RCN.childResourceReferences)}&ty={int(T.SUB)}&drt={int(DRT.unstructured)}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'), r)
		self.assertIsNotNone(rrf := findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 1 if present else 0, r)
		return findXPath(rrf, '{0}/val')	# first in the list

	#########################################################################


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
	
	# General test cases
	addTest(suite, TestCRS('test_createCRSmissingRratSratFail'))
	addTest(suite, TestCRS('test_createCRSmissingNuFail'))
	addTest(suite, TestCRS('test_createCRSmissingTwtFail'))
	addTest(suite, TestCRS('test_createCRSwrongTwtFail'))
	addTest(suite, TestCRS('test_createCRSmissingTwsFail'))
	addTest(suite, TestCRS('test_createCRSemptyEncsFail'))
	addTest(suite, TestCRS('test_createCRSWrongNumberEncsFail'))
	addTest(suite, TestCRS('test_createCRSwithRratsFail'))

	# Test rrat
	addTest(suite, TestCRS('test_createCRSwithRrat'))
	addTest(suite, TestCRS('test_updateCRSwithNewRratFail'))
	addTest(suite, TestCRS('test_updateCRSwithrratsFail'))
	addTest(suite, TestCRS('test_updateCRSwithNecFail'))
	addTest(suite, TestCRS('test_updateCRSwithEncsFail'))
	addTest(suite, TestCRS('test_updateCRSwithDeletedEncsFail'))
	addTest(suite, TestCRS('test_deleteCRSwithRrat'))
	addTest(suite, TestCRS('test_createCRSwithRratAndEt'))
	addTest(suite, TestCRS('test_deleteCRSwithRrat'))
	addTest(suite, TestCRS('test_createCRSwithRratWrongTarget'))

	addTest(suite, TestCRS('test_createCRSwithSingleRratAndNSI'))
	addTest(suite, TestCRS('test_createTwoNotificationOneNotification'))
	addTest(suite, TestCRS('test_deleteCRSwithRrat'))


	# Test srat
	addTest(suite, TestCRS('test_createCRSwithSratNonSubFail'))
	addTest(suite, TestCRS('test_createSubscriptions'))
	addTest(suite, TestCRS('test_createCRSwithSrat'))
	addTest(suite, TestCRS('test_updateCRSwithNewSratFail'))
	addTest(suite, TestCRS('test_deleteCRSwithSrat'))
	addTest(suite, TestCRS('test_deleteSubscriptions'))


	# Test Delete and Update via Subscription
	addTest(suite, TestCRS('test_createCRSwithRrat'))
	addTest(suite, TestCRS('test_deleteRratSubscription'))

	addTest(suite, TestCRS('test_createSubscriptions'))			# create subs again
	addTest(suite, TestCRS('test_createSrat2Subscriptions'))
	addTest(suite, TestCRS('test_deleteSratSubscription'))
	addTest(suite, TestCRS('test_deleteSubscriptions'))

	addTest(suite, TestCRS('test_createSubscriptions'))			# create subs again
	addTest(suite, TestCRS('test_createSrat2Subscriptions'))		# create crs again
	addTest(suite, TestCRS('test_updateSubAcrs'))
	addTest(suite, TestCRS('test_deleteSubscriptions'))

	# Test Periodic Window
	addTest(suite, TestCRS('test_createCRSwithRrat'))
	addTest(suite, TestCRS('test_createSingleNotificationNoNotification'))
	addTest(suite, TestCRS('test_createTwoSingleNotificationNoNotifications'))
	addTest(suite, TestCRS('test_createTwoNotificationOneNotification'))
	addTest(suite, TestCRS('test_updateCRSPeriodicWindowSize'))

	# Test Sliding Window
	addTest(suite, TestCRS('test_enableSlidingWindow'))
	addTest(suite, TestCRS('test_createSingleNotificationNoNotification'))
	addTest(suite, TestCRS('test_createTwoSingleNotificationNoNotifications'))
	addTest(suite, TestCRS('test_createTwoNotificationOneNotification'))
	addTest(suite, TestCRS('test_updateCRSSlidingWindowSize'))
	addTest(suite, TestCRS('test_deleteCRSwithRrat'))

	# Test Notification Stats
	addTest(suite, TestCRS('test_createCRSwithRratSlidingStatsEnabled'))		# Sliding
	addTest(suite, TestCRS('test_retrieveCRSwithNSENSINone'))
	addTest(suite, TestCRS('test_createTwoNotificationOneNotification'))
	addTest(suite, TestCRS('test_deleteCRSwithRrat'))

	addTest(suite, TestCRS('test_createCRSwithRratSlidingStatsEnabled'))		# Sliding
	addTest(suite, TestCRS('test_updateCRSwithDeletedNse'))
	addTest(suite, TestCRS('test_updateCRSwithDeletedNsi'))
	addTest(suite, TestCRS('test_updateCRSwithEnableNSE'))
	addTest(suite, TestCRS('test_testEmptyNsi'))
	addTest(suite, TestCRS('test_createTwoNotificationOneNotification'))
	addTest(suite, TestCRS('test_testNonEmptyNsi'))
	addTest(suite, TestCRS('test_updateCRSwithNseFalse'))
	addTest(suite, TestCRS('test_updateCRSwithNseTrue'))	# NSI should be empty
	addTest(suite, TestCRS('test_testEmptyNsi'))
	addTest(suite, TestCRS('test_createTwoNotificationOneNotification'))
	addTest(suite, TestCRS('test_testNonEmptyNsi'))
	addTest(suite, TestCRS('test_updateCRSwithNseTrue'))	# NSI should be empty
	addTest(suite, TestCRS('test_testEmptyNsi'))
	addTest(suite, TestCRS('test_deleteCRSwithRrat'))

	# Test Expiration
	addTest(suite, TestCRS('test_createCRSwithExpiration'))

	# Test Deletion Notification
	addTest(suite, TestCRS('test_testCRSwithSu'))

	# Test eventEvaluationMode create and update
	addTest(suite, TestCRS('test_createCorrectEEM12345TWT1'))
	addTest(suite, TestCRS('test_createCorrectEEM125TWT2'))
	addTest(suite, TestCRS('test_createWrongEEM34TWT2'))

	addTest(suite, TestCRS('test_updateCorrectEEM12345TWT1'))
	addTest(suite, TestCRS('test_updateCorrectEEM125TWT2'))
	addTest(suite, TestCRS('test_updateWrongEEM34TWT2'))

	# Test eventEvaluationMode: Periodic ALL_OR_SOME_EVENTS_PRESENT
	addTest(suite, TestCRS('test_createCRSPeriodicAllSomeEventsPresentAll'))
	addTest(suite, TestCRS('test_createCRSPeriodicAllSomeEventsPresentSome'))
	addTest(suite, TestCRS('test_createCRSPeriodicAllSomeEventsPresentNone'))

	# Test eventEvaluationMode: Sliding ALL_OR_SOME_EVENTS_PRESENT
	addTest(suite, TestCRS('test_createCRSSlidingAllSomeEventsPresentAll'))
	addTest(suite, TestCRS('test_createCRSSlidingAllSomeEventsPresentSome'))
	addTest(suite, TestCRS('test_createCRSSlidingAllSomeEventsPresentNone'))


	# Test eventEvaluationMode: Periodic ALL_OR_SOME_EVENTS_MISSING
	addTest(suite, TestCRS('test_createCRSPeriodicAllSomeEventsMissingAll'))
	addTest(suite, TestCRS('test_createCRSPeriodicAllSomeEventsMissingSome'))
	addTest(suite, TestCRS('test_createCRSPeriodicAllSomeEventsMissingNone'))

	# No test for eventEvaluationMode: Sliding ALL_OR_SOME_EVENTS_MISSING and All_EVENTS_MISSING necessary

	# Test eventEvaluationMode: Periodic All_EVENTS_MISSING
	addTest(suite, TestCRS('test_createCRSPeriodicAllEventsMissingAll'))
	addTest(suite, TestCRS('test_createCRSPeriodicAllEventsMissingSome'))
	addTest(suite, TestCRS('test_createCRSPeriodicAllEventsMissingNone'))

	# Test eventEvaluationMode: Periodic SOME_EVENTS_MISSING
	addTest(suite, TestCRS('test_createCRSPeriodicSomeEventsMissingAll'))
	addTest(suite, TestCRS('test_createCRSPeriodicSomeEventsMissingSome'))
	addTest(suite, TestCRS('test_createCRSPeriodicSomeEventsMissingNone'))

	# Test eventEvaluationMode: Sliding SOME_EVENTS_MISSING
	addTest(suite, TestCRS('test_createCRSSlidingSomeEventsMissingAll'))
	addTest(suite, TestCRS('test_createCRSSlidingSomeEventsMissingSome'))
	addTest(suite, TestCRS('test_createCRSSlidingSomeEventsMissingNone'))


	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
