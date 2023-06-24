#
#	testTSB.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for TimeSyncBeacon
#

import unittest, sys
import isodate
if '..' not in sys.path:
	sys.path.append('..')
from init import *
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, BeaconCriteria
from typing import Tuple


# TODO update
# TODO LOS

class TestTSB(unittest.TestCase):

	ae 			= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestTSB')
		# create other resources
		dct =	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
			 		'rr'  : True,
			 		'srv' : [ RELEASEVERSION ],
			 		#'poa' : [ NOTIFICATIONSERVER ]
			 		'poa' : [ ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		# Start notification server
		startNotificationServer()
		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'
		testCaseEnd('Setup TestTSB')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			stopNotificationServer()
			return
		testCaseStart('TearDown TestTSB')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()
		testCaseEnd('TearDown TestTSB')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSB(self) -> None:
		""" Create <TSB> """
		dct = 	{ 'm2m:tsb' : { 
					'rn'	: tsbRN,
					'bcnc'	: BeaconCriteria.PERIODIC,
        			'bcnu'	: [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(aeURL, TestTSB.originator, T.TSB, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:tsb/ri'))
		self.assertIsNotNone(findXPath(r, 'm2m:tsb/bcnc'))
		self.assertEqual(findXPath(r, 'm2m:tsb/bcnc'), BeaconCriteria.PERIODIC)
		# Delete again
		r, rsc = DELETE(tsBURL, TestTSB.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSBEmptyNuFail(self) -> None:
		""" Create <TSB> with empty nu -> Fail """
		dct = 	{ 'm2m:tsb' : { 
					'rn'	: tsbRN,
					'bcnc'	: BeaconCriteria.PERIODIC,
        			'bcnu'	: [  ]
				}}
		r, rsc = CREATE(aeURL, TestTSB.originator, T.TSB, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSBBcniFail(self) -> None:
		""" Create <TSB> with wrong bcni -> FAIL"""
		dct = 	{ 'm2m:tsb' : { 
					'rn'	: tsbRN,
					'bcnc'	: BeaconCriteria.LOSS_OF_SYNCHRONIZATION,
					'bcni'	: 'PT10S',
					'bcnr'	: TestTSB.originator,
        			'bcnu'	: [ NOTIFICATIONSERVER ]

				}}
		r, rsc = CREATE(aeURL, TestTSB.originator, T.TSB, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSBLOSNoBcnrFail(self) -> None:
		""" Create <TSB> with wrong bcnt -> FAIL"""
		dct = 	{ 'm2m:tsb' : { 
					'rn'	: tsbRN,
					'bcnc'	: BeaconCriteria.PERIODIC,
					'bcnt'	: 10,
        			'bcnu'	: [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(aeURL, TestTSB.originator, T.TSB, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSBBcntNoBcnrFail(self) -> None:
		""" Create <TSB> with LossOfSync and no bcnr -> FAIL"""
		dct = 	{ 'm2m:tsb' : { 
					'rn'	: tsbRN,
					'bcnc'	: BeaconCriteria.LOSS_OF_SYNCHRONIZATION,
					'bcnt'	: 10,
        			'bcnu'	: [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(aeURL, TestTSB.originator, T.TSB, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSBBcniDefault(self) -> None:
		""" Create <TSB> Periodic with default bcni"""
		dct = 	{ 'm2m:tsb' : { 
					'rn'	: tsbRN,
					'bcnc'	: BeaconCriteria.PERIODIC,
					'bcnu'	: [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(aeURL, TestTSB.originator, T.TSB, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNone(findXPath(r, 'm2m:tsb/bcnt'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:tsb/bcni'), r)
		self.assertIsInstance(findXPath(r, 'm2m:tsb/bcni'), str, r)
		# Delete again
		r, rsc = DELETE(tsBURL, TestTSB.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSBBcntDefault(self) -> None:
		""" Create <TSB> LossOfSync with default bcnt"""
		dct = 	{ 'm2m:tsb' : { 
					'rn'	: tsbRN,
					'bcnc'	: BeaconCriteria.LOSS_OF_SYNCHRONIZATION,
					'bcnr'	: TestTSB.originator,
					'bcnu'	: [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(aeURL, TestTSB.originator, T.TSB, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNone(findXPath(r, 'm2m:tsb/bcni'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:tsb/bcnt'), r)
		self.assertGreater(findXPath(r, 'm2m:tsb/bcnt'), 0, r)
		# Delete again
		r, rsc = DELETE(tsBURL, TestTSB.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSBPeriodic(self) -> None:
		""" Create <TSB> with periodic notification"""
		clearLastNotification()
		dct = 	{ 'm2m:tsb' : { 
					'rn'	: tsbRN,
					'bcnc'	: BeaconCriteria.PERIODIC,
					'bcni'	: f'PT{tsbPeriodicInterval}S',
        			'bcnu'	: [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(aeURL, TestTSB.originator, T.TSB, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:tsb/ri'))
		self.assertIsNotNone(findXPath(r, 'm2m:tsb/bcnc'))
		self.assertIsNotNone(findXPath(r, 'm2m:tsb/bcni'))
		self.assertEqual(findXPath(r, 'm2m:tsb/bcni'), f'PT{tsbPeriodicInterval}S', r)
		self.assertEqual(findXPath(r, 'm2m:tsb/bcnc'), BeaconCriteria.PERIODIC)

		# Check notification
		testSleep(tsbPeriodicInterval * 2)	# wait a moment
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:tsbn'), lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:tsbn/tbr'), lastNotification)
		self.assertEqual(findXPath(lastNotification, 'm2m:tsbn/tbr'), findXPath(r, 'm2m:tsb/ri'), lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:tsbn/ctm'), lastNotification)
		try:
			raised = False
			isodate.parse_time(findXPath(lastNotification, 'm2m:tsbn/ctm'))
		except:
			raised = True
		finally:
			self.assertFalse(raised, f'Error parsing timestamp: {lastNotification}')

		# Delete again
		r, rsc = DELETE(tsBURL, TestTSB.originator)
		self.assertEqual(rsc, RC.DELETED, r)


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()

	addTest(suite, TestTSB('test_createTSB'))
	addTest(suite, TestTSB('test_createTSBEmptyNuFail'))
	addTest(suite, TestTSB('test_createTSBBcniFail'))
	addTest(suite, TestTSB('test_createTSBLOSNoBcnrFail'))
	addTest(suite, TestTSB('test_createTSBBcniDefault'))
	addTest(suite, TestTSB('test_createTSBBcntDefault'))
	addTest(suite, TestTSB('test_createTSBPeriodic'))

	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)

