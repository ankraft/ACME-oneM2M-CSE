#
#	testCRS.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CRS functionality & notifications
#

import unittest, sys, time
from unittest.result import failfast
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
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
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
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)


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
		self.assertIsNotNone(rrats := findXPath(TestCRS.crs, 'm2m:crs/rrats'))
		self.assertEqual(len(rrats), 2)
		self.assertEqual(rrats[0], self._testSubscriptionForCnt(cntRN1), TestCRS.crs)
		self.assertEqual(rrats[1], self._testSubscriptionForCnt(cntRN2))
		self._testSubscriptionForCnt(cntRN3, False)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithNewRratFail(self) -> None:
		"""	UPDATE <CRS> with a new rrat -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'rrat': [ self.cnt1RI, self.cnt2RI, self.cnt3RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithrratsFail(self) -> None:
		"""	UPDATE <CRS> with a rrats -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'rrats': [ self.cnt1RI, self.cnt2RI, self.cnt3RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithNecFail(self) -> None:
		"""	UPDATE <CRS> with nec -> Fails"""
		dct = 	{ 'm2m:crs' : { 
			        'nec': 1
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)


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
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCRSwithDeletedEncsFail(self) -> None:
		"""	UPDATE <CRS> with deleted encs while rrat is present -> Fails"""
		dct = 	{ 'm2m:crs' : { 
			        'encs': None
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwithRratAndEt(self) -> None:
		"""	CREATE <CRS> with rrat, one encs, and et set"""
		et = getResourceDate(60)	# 1 minute in the future
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'et' : et, 
					'nu' : [ NOTIFICATIONSERVER ],
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
		self.assertEqual(rsc, RC.created, TestCRS.crs)
		self.assertEqual(findXPath(TestCRS.crs, 'm2m:crs/et'), et)
		self.assertIsNotNone(rrats := findXPath(TestCRS.crs, 'm2m:crs/rrats'))

		# check both subscriptions' et
		r, rsc = RETRIEVE(f'{URL}/{rrats[0][1:]}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, TestCRS.crs)
		self.assertEqual(findXPath(r, 'm2m:sub/et'), et)
		r, rsc = RETRIEVE(f'{URL}/{rrats[1][1:]}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, TestCRS.crs)
		self.assertEqual(findXPath(r, 'm2m:sub/et'), et)

	
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
					'srat': [ self.cnt1RI ],	# Fail, no subscription
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
	def test_updateCRSwithNewSratFail(self) -> None:
		"""	UPDATE <CRS> with a new srat -> Fail"""
		dct = 	{ 'm2m:crs' : { 
					'srat': [ self.sub1RI, self.sub2RI ],
				}}

		TestCRS.crs, rsc = UPDATE(crsURL, TestCRS.originator, dct)
		self.assertEqual(rsc, RC.badRequest, TestCRS.crs)


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


	#########################################################################
	#
	#	Delete Subscriptions
	# 

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteRratSubscription(self) -> None:
		"""	DELETE <SUB> resource (<CRS> and second <SUB> shall be deleted as well)"""
		self.assertIsNotNone(rrats := findXPath(TestCRS.crs, 'm2m:crs/rrats'))
		self.assertEqual(len(rrats), 2)

		r, rsc = DELETE(f'{URL}/{rrats[0][1:]}', TestCRS.originator)
		self.assertEqual(rsc, RC.deleted, r)

		# Look for the other subscription and crs
		r, rsc = RETRIEVE(f'{URL}/{rrats[1][1:]}', TestCRS.originator)
		self.assertEqual(rsc, RC.notFound, r)
		r, rsc = RETRIEVE(f'{crsURL}', TestCRS.originator)
		self.assertEqual(rsc, RC.notFound, r)

		TestCRS.sub1RI = None
		TestCRS.sub2RI = None


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSrat2Subscriptions(self) -> None:
		"""	CREATE <CRS> with two <SUB> in srat"""
		self.assertIsNotNone(self.sub1RI)
		self.assertIsNotNone(self.sub2RI)
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'srat': [ self.sub1RI, self.sub2RI ],	
				}}
		TestCRS.crs, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.created, TestCRS.crs)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSratSubscription(self) -> None:
		"""	DELETE <SUB> resource (CRS and second SUB shall be deleted as well)"""
		self.assertIsNotNone(srat := findXPath(TestCRS.crs, 'm2m:crs/srat'))
		self.assertEqual(len(srat), 2)

		r, rsc = DELETE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.deleted, r)

		# Look for the other subscription and crs
		r, rsc = RETRIEVE(f'{csiURL}/{TestCRS.sub2RI}', TestCRS.originator)
		self.assertEqual(rsc, RC.OK, r)
		r, rsc = RETRIEVE(f'{crsURL}', TestCRS.originator)
		self.assertEqual(rsc, RC.notFound, r)

		TestCRS.sub1RI = None # Only sub1 is deleted, not sub2


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSubscriptions(self) -> None:
		"""	DELETE <SUB> resources if present"""
		if TestCRS.sub1RI:
			r, rsc = DELETE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator)
			self.assertEqual(rsc, RC.deleted, r)
			TestCRS.sub1RI = None

		if TestCRS.sub2RI:
			r, rsc = DELETE(f'{csiURL}/{TestCRS.sub2RI}', TestCRS.originator)
			self.assertEqual(rsc, RC.deleted, r)
			TestCRS.sub2RI = None


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSubAcrs(self) -> None:
		"""	UPDATE <SUB> acrs (delete <CRS>)"""
		dct:JSON = { 'm2m:sub' : {
					'acrs' : []
		}}
		r, rsc = UPDATE(f'{csiURL}/{TestCRS.sub1RI}', TestCRS.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertNotIn(findXPath(TestCRS.crs, 'm2m:crs/ri'), findXPath(r, 'm2m:sub/acrs'))

		# Check that CRS was deleted
		r, rsc = RETRIEVE(f'{crsURL}', TestCRS.originator)
		self.assertEqual(rsc, RC.notFound, r)
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
		self.assertEqual(rsc, RC.created, self.sub1)
		time.sleep(crsTimeWindowSize + 1)
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
		"""	CREATE two <CIN> to raise two notifications (plus one notification from crs)"""
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





# TODO test nse - count of verification request
# TODO test nse: delete nse fail
# TODO test nse: set to false
# TODO test nse: set to true
# TODO test nse: set to true again


# TODO tws: change period . What happens?


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
		return findXPath(rrf, '{0}/val')

	#########################################################################

def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()

	suite.addTest(TestCRS('test_createCRSmissingRratSratFail'))
	suite.addTest(TestCRS('test_createCRSmissingNuFail'))
	suite.addTest(TestCRS('test_createCRSmissingTwtFail'))
	suite.addTest(TestCRS('test_createCRSwrongTwtFail'))
	suite.addTest(TestCRS('test_createCRSmissingTwsFail'))
	suite.addTest(TestCRS('test_createCRSemptyEncsFail'))
	suite.addTest(TestCRS('test_createCRSWrongNumberEncsFail'))
	suite.addTest(TestCRS('test_createCRSwithRratsFail'))

	# Test rrat
	suite.addTest(TestCRS('test_createCRSwithRrat'))
	suite.addTest(TestCRS('test_updateCRSwithNewRratFail'))
	suite.addTest(TestCRS('test_updateCRSwithrratsFail'))
	suite.addTest(TestCRS('test_updateCRSwithNecFail'))
	suite.addTest(TestCRS('test_updateCRSwithEncsFail'))
	suite.addTest(TestCRS('test_updateCRSwithDeletedEncsFail'))
	suite.addTest(TestCRS('test_deleteCRSwithRrat'))
	suite.addTest(TestCRS('test_createCRSwithRratAndEt'))
	suite.addTest(TestCRS('test_deleteCRSwithRrat'))

	# Test srat
	suite.addTest(TestCRS('test_createCRSwithSratNonSubFail'))
	suite.addTest(TestCRS('test_createSubscriptions'))
	suite.addTest(TestCRS('test_createCRSwithSrat'))
	suite.addTest(TestCRS('test_updateCRSwithNewSratFail'))
	suite.addTest(TestCRS('test_deleteCRSwithSrat'))
	suite.addTest(TestCRS('test_deleteSubscriptions'))


	# Test Delete and Update via Subscription
	suite.addTest(TestCRS('test_createCRSwithRrat'))
	suite.addTest(TestCRS('test_deleteRratSubscription'))

	suite.addTest(TestCRS('test_createSubscriptions'))			# create subs again
	suite.addTest(TestCRS('test_createSrat2Subscriptions'))
	suite.addTest(TestCRS('test_deleteSratSubscription'))
	suite.addTest(TestCRS('test_deleteSubscriptions'))

	suite.addTest(TestCRS('test_createSubscriptions'))			# create subs again
	suite.addTest(TestCRS('test_createSrat2Subscriptions'))		# create crs again
	suite.addTest(TestCRS('test_updateSubAcrs'))
	suite.addTest(TestCRS('test_deleteSubscriptions'))

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