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
from acme.etc.Types import NotificationEventType as NET, ResourceTypes as T, ResponseStatusCode as RC, TimeWindowType
from acme.etc.Types import ResultContentType as RCN
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
		# Start notification server
		startNotificationServer()

		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'

		testCaseStart('Setup TestCRS')

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

		testCaseEnd('Setup TestCRS')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		testCaseStart('TearDown TestCRS')
		#DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestCRS')
		stopNotificationServer()


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
			        'encs': {},
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
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
							]
						}
				}}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.created, TestCRS.crs)

		# check subscriptions
		self._testSubscriptionForCnt(cntRN1)
		self._testSubscriptionForCnt(cntRN2)
		self._testSubscriptionForCnt(cntRN3, False)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithNewRrat(self) -> None:
		"""	UPDATE <CRS> with a new rrat, one encs"""
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
		"""	UPDATE <CRS> with a removed rrat, one encs"""
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
	def test_updateCRSwithWrongRratFail(self) -> None:
		"""	CREATE <CRS> with a wrong rrat (check rollback) -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'rrat': [ self.cnt1RI, self.cnt2RI, 'wrongRI' ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.crossResourceOperationFailure, TestCRS.crs)

		# check subscriptions (should be still the old ones!)
		self._testSubscriptionForCnt(cntRN1)		# should still be there
		self._testSubscriptionForCnt(cntRN2, False)	# should not be added
		self._testSubscriptionForCnt(cntRN3)		# should still be there



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithDeletedEncFail(self) -> None:
		"""	UPDATE <CRS> with deleted enc while rrat is present -> Fails"""
		dct = 	{ 'm2m:crs' : { 
			        'encs': None
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)

	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithWrongNumberOfEncFail(self) -> None:
		"""	UPDATE <CRS> with wrong number of enc -> Fails"""
		dct = 	{ 'm2m:crs' : { 
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

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCRSwithRrat(self) -> None:
		"""	DELETE <CRS> with rrat"""
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.deleted, r)
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
					'srat': [ self.cnt1RI ],	# should succeed
				}
		}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)
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
		self.assertEqual(rsc, RC.created, self.sub1)
		TestCRS.sub1RI = findXPath(self.sub1, 'm2m:sub/ri')

		dct = { 'm2m:sub' : {
					'rn' : subRN2,
					'nu' : [ NOTIFICATIONSERVER ],
					'enc' : {
						'net': [ NET.createDirectChild ],
					},
				}}
		TestCRS.sub2, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created, self.sub2)
		TestCRS.sub2RI = findXPath(self.sub2, 'm2m:sub/ri')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithSrat(self) -> None:
		"""	CREATE <CRS> with srat """
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'srat': [ self.sub1RI ],
				}
		}

		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.created, TestCRS.crs)

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
	def test_updateCRSwithNewSrat(self) -> None:
		"""	UPDATE <CRS> with a new srat"""
		dct = 	{ 'm2m:crs' : { 
					'srat': [ self.sub1RI, self.sub2RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.updated, TestCRS.crs)

		# retrieve subs and check them directly
		spCrsRi = toSPRelative(findXPath(TestCRS.crs, 'm2m:crs/ri'))

		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/nu'))
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/acrs'))

		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub2RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/nu'))
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/acrs'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithRemovedSrat(self) -> None:
		"""	UPDATE <CRS> with a new srat"""
		dct = 	{ 'm2m:crs' : { 
					'srat': [ self.sub1RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.updated, TestCRS.crs)

		# retrieve subs and check them directly
		spCrsRi = toSPRelative(findXPath(TestCRS.crs, 'm2m:crs/ri'))

		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/nu'))
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/acrs'))

		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub2RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertNotIn(spCrsRi, findXPath(r, 'm2m:sub/nu'))
		self.assertIsNone(findXPath(r, 'm2m:sub/acrs'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithWrongSratFail(self) -> None:
		"""	UPDATE <CRS> with a new srat -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'srat': [ self.sub1RI, self.cnt1RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithRratAndSrat(self) -> None:
		"""	UPDATE <CRS> with a new rrat and srat"""
		dct = 	{ 'm2m:crs' : { 
					'rrat': [ self.cnt3RI ],
					'srat': [ self.sub1RI, self.sub2RI ],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.createDirectChild ],
							}
						]
					}
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.updated, TestCRS.crs)

		# retrieve subs and check them directly
		spCrsRi = toSPRelative(findXPath(TestCRS.crs, 'm2m:crs/ri'))

		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/nu'))
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/acrs'))

		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub2RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/nu'))
		self.assertIn(spCrsRi, findXPath(r, 'm2m:sub/acrs'))

		# check CNT's sub
		self._testSubscriptionForCnt(cntRN3)		# should be there


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCRSwithSrat(self) -> None:
		"""	DELETE <CRS> with srat"""
		r, rsc = DELETE(crsURL, TestCRS.originator)
		self.assertEqual(rsc, RC.deleted, r)

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


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSubscriptions(self) -> None:
		"""	DELETE <SUB> resource"""
		r, rsc = DELETE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.deleted, r)
		TestCRS.sub1RI = None

		# TODO delete the following when the <sub> deletion functionality is implemented 

		r, rsc = DELETE(f'{csiURL}/{TestCRS.sub2RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.deleted, r)
		TestCRS.sub2RI = None



	def _testSubscriptionForCnt(self, cnt:str, present:bool = True) -> None:
		"""	Test whether there is exactly one or none subscription for a container.
		"""
		r, rsc = RETRIEVE(f'{aeURL}/{cnt}?fu=1&rcn={int(RCN.childResourceReferences)}&ty={int(T.SUB)}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 1 if present else 0)


# TODO test sub delete - acrs working? Delete a sub and check the <crs> resource


	#########################################################################
	#
	#	Periodic notifications testing
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSingleNotificationNoNotification(self) -> None:
		"""	CREATE <CIN> to raise a single notification (no notification from crs)"""
		clearLastNotification()
		dct:JSON = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created, self.sub1)
		time.sleep(crsTimeWindowSize + 1)
		self.assertIsNone(getLastNotification())


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTwoSingleNotificationNoNotifications(self) -> None:
		"""	CREATE two <CIN> with delay to raise a two notification (no notification from crs)"""
		clearLastNotification()
		dct:JSON = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}

		# CIN to first CNT
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created, self.sub1)
		time.sleep(crsTimeWindowSize + 1)
		self.assertIsNone(getLastNotification())

		# CIN two second CNT
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created, self.sub1)
		time.sleep(crsTimeWindowSize + 1)
		self.assertIsNone(getLastNotification())


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTwoNotificationOneNotification(self) -> None:
		"""	CREATE two <CIN> to raise two notifications (plus notification from crs)"""
		clearLastNotification()
		
		# Create 
		dct:JSON = 	{ 'm2m:cin' : {
			'con' : 'AnyValue',
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN1}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created, r)
		r, rsc = CREATE(f'{aeURL}/{cntRN2}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created, r)	

		# wait and check notification
		time.sleep(crsTimeWindowSize + 1)
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
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.updated, TestCRS.crs)





# TODO tws: change period . What happens?
# TODO delete sub
# TODO empty sub.acrs


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
	suite.addTest(TestCRS('test_updateCRSwithWrongRratFail'))
	suite.addTest(TestCRS('test_updateCRSwithDeletedEncFail'))
	suite.addTest(TestCRS('test_updateCRSwithWrongNumberOfEncFail'))
	suite.addTest(TestCRS('test_deleteCRSwithRrat'))

	# Test srat
	suite.addTest(TestCRS('test_createCRSwithSratNonSubFail'))
	suite.addTest(TestCRS('test_createSubscriptions'))
	suite.addTest(TestCRS('test_createCRSwithSrat'))
	suite.addTest(TestCRS('test_updateCRSwithNewSrat'))
	suite.addTest(TestCRS('test_updateCRSwithRemovedSrat'))
	suite.addTest(TestCRS('test_updateCRSwithWrongSratFail'))
	suite.addTest(TestCRS('test_updateCRSwithRratAndSrat'))
	suite.addTest(TestCRS('test_deleteCRSwithSrat'))
	suite.addTest(TestCRS('test_deleteSubscriptions'))	# TODO change this to one! subscrription delete and move up one test case

	# Test Periodic Window
	suite.addTest(TestCRS('test_createCRSwithRrat'))
	suite.addTest(TestCRS('test_createSingleNotificationNoNotification'))
	suite.addTest(TestCRS('test_createTwoSingleNotificationNoNotifications'))
	suite.addTest(TestCRS('test_createTwoNotificationOneNotification'))

	# Test Sliding Window
	suite.addTest(TestCRS('test_enableSlidingWindow'))
	suite.addTest(TestCRS('test_createSingleNotificationNoNotification'))
	suite.addTest(TestCRS('test_createTwoSingleNotificationNoNotifications'))
	suite.addTest(TestCRS('test_createTwoNotificationOneNotification'))


	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
