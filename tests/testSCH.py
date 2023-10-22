 #
#	testSCH.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Schedule functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, TimeWindowType
from acme.etc.Types import NotificationEventType, NotificationEventType as NET
from init import *
from datetime import timedelta

nodeID  = 'urn:sn:1234'

def createScheduleString(range:int, delay:int = 0) -> str:
	"""	Create schedule string for range seconds """
	dts = datetime.now(tz = timezone.utc) + timedelta(seconds = delay)
	dte = dts + timedelta(seconds = range)
	return f'{dts.second}-{dte.second} {dts.minute}-{dte.minute} {dts.hour}-{dte.hour} * * * *'
		

class TestSCH(unittest.TestCase):

	ae 			= None
	aeRI		= None
	ae2 		= None
	nod 		= None
	nodRI		= None
	crs			= None
	crsRI		= None


	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestSCH')

		# Start notification server
		startNotificationServer()


		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		cls.aeRI = findXPath(cls.ae, 'm2m:ae/ri')
	

		dct = 	{ 'm2m:nod' : { 
					'rn' 	: nodRN,
					'ni'	: nodeID
				}}
		cls.nod, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, dct)
		assert rsc == RC.CREATED
		cls.nodRI = findXPath(cls.nod, 'm2m:nod/ri')

		dct = 	{ 'm2m:crs' : { 
					'rn' 	: crsRN,
					'nu'	: [ NOTIFICATIONSERVER ],
					'twt'	: TimeWindowType.PERIODICWINDOW,
					'tws'	: f'PT{crsTimeWindowSize}S',
					'rrat'	: [ cls.nodRI ],
			        'encs'	: {
					'enc'	: [
						{
							'net': [ NotificationEventType.createDirectChild ],
						}
						]
					}


				}}
		cls.nod, rsc = CREATE(cseURL, ORIGINATOR, T.CRS, dct)
		assert rsc == RC.CREATED
		cls.crsRI = findXPath(cls.nod, 'm2m:crs/ri')


		testCaseEnd('Setup TestSCH')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			stopNotificationServer()
			return
		testCaseStart('TearDown TestSCH')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(nodURL, ORIGINATOR)	# Just delete the NOD and everything below it. Ignore whether it exists or not
		DELETE(f'{cseURL}/{crsRN}', ORIGINATOR)
		DELETE(f'{cseURL}/{schRN}', ORIGINATOR)
		testCaseEnd('TearDown TestSCH')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################

# TODO validate schedule element format *****

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderCBwithNOCFail(self) -> None:
		"""	CREATE invalid <SCH> with "nco" under CSEBase -> Fail"""
		self.assertIsNotNone(TestSCH.ae)
		dct = 	{ 'm2m:sch' : {
					'rn' : schRN,
					'se': { 'sce': [ '* * * * * * *' ] },
					'nco': True
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CONTENTS_UNACCEPTABLE, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderNODwithNOCUnsupportedFail(self) -> None:
		"""	CREATE <SCH> with nco under NOD (unsupported) -> Fail"""
		self.assertIsNotNone(TestSCH.ae)
		dct = 	{ 'm2m:sch' : {
					'rn' : schRN,
					'se': { 'sce': [ '* * * * * * *' ] },
					'nco': True
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.NOT_IMPLEMENTED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderCBwithoutNCO(self) -> None:
		"""	CREATE <SCH> without "nco" under CSEBase"""
		self.assertIsNotNone(TestSCH.ae)
		dct = 	{ 'm2m:sch' : {
					'rn' : schRN,
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DELETE again
		r, rsc = DELETE(f'{cseURL}/{schRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSCHunderCBwithNCOFail(self) -> None:
		"""	UPDATE <SCH> without "nco" under CSEBase -> Fail"""
		self.assertIsNotNone(TestSCH.ae)
		dct:JSON = 	{ 'm2m:sch' : {
					'rn' : schRN,
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# UPDATE with nco
		dct = 	{ 'm2m:sch' : {
					'nco': True
				}}
		r, rsc = UPDATE(f'{cseURL}/{schRN}', ORIGINATOR, dct)
		self.assertEqual(rsc, RC.CONTENTS_UNACCEPTABLE, r)

		# DELETE again
		r, rsc = DELETE(f'{cseURL}/{schRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSCHunderNODwithNOCUnsupportedFail(self) -> None:
		"""	CREATE <SCH> with nco under NOD (unsupported) -> Fail"""
		self.assertIsNotNone(TestSCH.ae)
		dct:JSON = 	{ 'm2m:sch' : {
					'rn' : schRN,
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# UPDATE with nco
		dct = 	{ 'm2m:sch' : {
					'nco': True
				}}
		r, rsc = UPDATE(f'{nodURL}/{schRN}', ORIGINATOR, dct)
		self.assertEqual(rsc, RC.NOT_IMPLEMENTED, r)

		# DELETE again
		r, rsc = DELETE(f'{nodURL}/{schRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	#	Testing CREATE with different parent types
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderSUBwrongRn(self) -> None:
		"""	CREATE <SCH> with wrong rn under <SUB> -> Fail"""
		# create <SUB>
		dct:JSON = 	{ 'm2m:sub' : { 
					'rn' : f'{subRN}',
			        'enc': {
			            'net': [ NotificationEventType.resourceUpdate ]
        			},
        			'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# create <SCH> with wrong rn
		dct = 	{ 'm2m:sch' : {
					'rn' : 'wrong',
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(f'{cseURL}/{subRN}', ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		# DELETE SUB again
		r, rsc = DELETE(f'{cseURL}/{subRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderSUBemptyRn(self) -> None:
		"""	CREATE <SCH> with empty rn under <SUB>"""
		# create <SUB>
		dct:JSON = 	{ 'm2m:sub' : { 
					'rn' : f'{subRN}',
			        'enc': {
			            'net': [ NotificationEventType.resourceUpdate ]
        			},
        			'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct = 	{ 'm2m:sch' : {
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(f'{cseURL}/{subRN}', ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DELETE again
		r, rsc = DELETE(f'{cseURL}/{subRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderSUBcorrectRn(self) -> None:
		"""	CREATE <SCH> with correct rn under <SUB>"""
		# create <SUB>
		dct:JSON = 	{ 'm2m:sub' : { 
					'rn' : f'{subRN}',
			        'enc': {
			            'net': [ NotificationEventType.resourceUpdate ]
        			},
        			'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct = 	{ 'm2m:sch' : {
					'rn' : 'notificationSchedule',
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(f'{cseURL}/{subRN}', ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DELETE again
		r, rsc = DELETE(f'{cseURL}/{subRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderCRSwrongRn(self) -> None:
		"""	CREATE <SCH> with wrong rn under <CRS> -> Fail"""
		dct:JSON = 	{ 'm2m:sch' : {
					'rn' : 'wrong',
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(f'{cseURL}/{crsRN}', ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderCRSemptyRn(self) -> None:
		"""	CREATE <SCH> with empty rn under <CRS>"""
		dct:JSON = 	{ 'm2m:sch' : {
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(f'{cseURL}/{crsRN}', ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DELETE again
		r, rsc = DELETE(f'{cseURL}/{crsRN}/notificationSchedule', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderCRScorrectRn(self) -> None:
		"""	CREATE <SCH> with correct rn under <CRS>"""
		dct:JSON = 	{ 'm2m:sch' : {
					'rn' : 'notificationSchedule',
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(f'{cseURL}/{crsRN}', ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DELETE again
		r, rsc = DELETE(f'{cseURL}/{crsRN}/notificationSchedule', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderCB(self) -> None:
		"""	CREATE <SCH> under CB"""
		dct:JSON = 	{ 'm2m:sch' : {
					'rn' : 'schedule',
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DELETE again
		r, rsc = DELETE(f'{cseURL}/schedule', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderCBTwiceFail(self) -> None:
		"""	CREATE <SCH> under CB twice -> Fail"""
		dct:JSON = 	{ 'm2m:sch' : {
					'rn' : 'schedule',
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# second create
		dct = 	{ 'm2m:sch' : {
					'rn' : 'schedule2',
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		# DELETE again
		r, rsc = DELETE(f'{cseURL}/schedule', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderNOD(self) -> None:
		"""	CREATE <SCH> under <node>"""
		dct:JSON = 	{ 'm2m:sch' : {
					'rn' : 'schedule',
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DELETE again
		r, rsc = DELETE(f'{nodURL}/schedule', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testSCHunderSUBinsideSchedule(self) -> None:
		"""	CREATE <SCH> under <SUB> and receive notification within schedule """
		# create <SUB>
		dct:JSON = 	{ 'm2m:sub' : { 
					'rn' : f'{subRN}',
			        'enc': {
			            'net': [ NotificationEventType.resourceUpdate ]
        			},
        			'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(aeURL, TestSCH.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct = { 'm2m:sch' : {
					'rn' : 'notificationSchedule',
					'se': { 'sce': [ createScheduleString(requestCheckDelay * 2) ] }
				}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', TestSCH.originator, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Update the AE to trigger a notification immediately
		clearLastNotification()
		dct = { 'm2m:ae' : {
					'lbl' : ['test']
				}}
		r, rsc = UPDATE(aeURL, TestSCH.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Check notification
		testSleep(requestCheckDelay)
		notification = getLastNotification()
		self.assertIsNotNone(notification)	# notification received

		# DELETE again
		r, rsc = DELETE(f'{aeURL}/{subRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testSCHunderSUBoutsideSchedule(self) -> None:
		"""	CREATE <SCH> under <SUB> and receive notification outside schedule """
		# create <SUB>
		dct:JSON = 	{ 'm2m:sub' : { 
					'rn' : f'{subRN}',
			        'enc': {
			            'net': [ NotificationEventType.resourceUpdate ]
        			},
        			'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(aeURL, TestSCH.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# add schedule
		dct = { 'm2m:sch' : {
					'rn' : 'notificationSchedule',
					'se': { 'sce': [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2) ] }
				}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', TestSCH.originator, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Update the AE to trigger a notification immediately
		clearLastNotification()
		dct = { 'm2m:ae' : {
					'lbl' : ['test']
				}}
		r, rsc = UPDATE(aeURL, TestSCH.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Check notification
		testSleep(requestCheckDelay)	# wait a short time but run before the schedule starts
		notification = getLastNotification()
		self.assertIsNone(notification)	# notification received

		# DELETE again
		r, rsc = DELETE(f'{aeURL}/{subRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testSCHunderSUBoutsideScheduleImmediate(self) -> None:
		"""	CREATE <SCH> under <SUB> and receive notification outside schedule, nec = immediate """
		# create <SUB>
		dct:JSON = 	{ 'm2m:sub' : { 
					'rn' : f'{subRN}',
			        'enc': {
			            'net': [ NotificationEventType.resourceUpdate ],
        			},
					'nec': 2, # immediate notification
        			'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(aeURL, TestSCH.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Add schedule
		dct = { 'm2m:sch' : {
					'rn' : 'notificationSchedule',
					'se': { 'sce': [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2) ] }
				}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', TestSCH.originator, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Update the AE to trigger a notification immediately
		clearLastNotification()
		dct = { 'm2m:ae' : {
					'lbl' : ['test']
				}}
		r, rsc = UPDATE(aeURL, TestSCH.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Check notification
		testSleep(requestCheckDelay)	# wait a short time but run before the schedule starts
		notification = getLastNotification()
		self.assertIsNotNone(notification)	# notification received

		# DELETE again
		r, rsc = DELETE(f'{aeURL}/{subRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	#	Testing crossResourceSubscription with schedule
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testSCHunderCRSinsideSchedule(self) -> None:
		"""	CREATE <SCH> under <CRS> and receive notification within schedule """
		# create <crs>
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'eem': 1,	# all events present
					'tws' : f'PT{requestCheckDelay}S',
					'rrat': [ self.aeRI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.resourceUpdate ],
							}
							]
						}
				}}
		r, rsc = CREATE(aeURL, TestSCH.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Add schedule
		dct = { 'm2m:sch' : {
					'rn' : 'notificationSchedule',
					'se': { 'sce': [ createScheduleString(requestCheckDelay * 2) ] }
				}}
		r, rsc = CREATE(f'{aeURL}/{crsRN}', TestSCH.originator, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# # Update the AE to trigger a notification immediately
		clearLastNotification()
		dct = { 'm2m:ae' : {
					'lbl' : ['test']
				}}
		r, rsc = UPDATE(aeURL, TestSCH.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# # Check notification
		testSleep(requestCheckDelay * 2)
		notification = getLastNotification()
		self.assertIsNotNone(notification)	# notification received

		# DELETE again
		r, rsc = DELETE(f'{aeURL}/{crsRN}', TestSCH.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testSCHunderCRSoutsideScheduleFail(self) -> None:
		"""	CREATE <SCH> under <CRS> and receive notification outside schedule -> Fail """
		# create <crs>
		dct = 	{ 'm2m:crs' : { 
					'rn' : crsRN,
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'eem': 1,	# all events present
					'tws' : f'PT{requestCheckDelay}S',
					'rrat': [ self.aeRI],
			        'encs': {
						'enc' : [
							{
								'net': [ NET.resourceUpdate ],
							}
							]
						}
				}}
		r, rsc = CREATE(aeURL, TestSCH.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Add schedule
		dct = { 'm2m:sch' : {
					'rn' : 'notificationSchedule',
					'se': { 'sce': [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 4) ] }	# outside time window
				}}
		r, rsc = CREATE(f'{aeURL}/{crsRN}', TestSCH.originator, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# # Update the AE to trigger a notification immediately, but outside schedule
		clearLastNotification()
		dct = { 'm2m:ae' : {
					'lbl' : ['test']
				}}
		r, rsc = UPDATE(aeURL, TestSCH.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# # Check notification
		testSleep(requestCheckDelay * 2)
		notification = getLastNotification()
		self.assertIsNone(notification)	# NO notification received

		# DELETE again
		r, rsc = DELETE(f'{aeURL}/{crsRN}', TestSCH.originator)
		self.assertEqual(rsc, RC.DELETED, r)


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()

	# basic tests
	addTest(suite, TestSCH('test_createSCHunderCBwithNOCFail'))
	addTest(suite, TestSCH('test_createSCHunderNODwithNOCUnsupportedFail'))
	addTest(suite, TestSCH('test_createSCHunderCBwithoutNCO'))
	addTest(suite, TestSCH('test_updateSCHunderCBwithNCOFail'))
	addTest(suite, TestSCH('test_updateSCHunderNODwithNOCUnsupportedFail'))

	# testing for specific parent types
	addTest(suite, TestSCH('test_createSCHunderSUBwrongRn'))
	addTest(suite, TestSCH('test_createSCHunderSUBemptyRn'))
	addTest(suite, TestSCH('test_createSCHunderSUBcorrectRn'))
	addTest(suite, TestSCH('test_createSCHunderCRSwrongRn'))
	addTest(suite, TestSCH('test_createSCHunderCRSemptyRn'))
	addTest(suite, TestSCH('test_createSCHunderCRScorrectRn'))
	addTest(suite, TestSCH('test_createSCHunderCB'))
	addTest(suite, TestSCH('test_createSCHunderCBTwiceFail'))
	addTest(suite, TestSCH('test_createSCHunderNOD'))

	# testing subscriptions with schedule
	addTest(suite, TestSCH('test_testSCHunderSUBinsideSchedule'))
	addTest(suite, TestSCH('test_testSCHunderSUBoutsideSchedule'))
	addTest(suite, TestSCH('test_testSCHunderSUBoutsideScheduleImmediate'))

	# testing crossResourceSubscription with schedule
	addTest(suite, TestSCH('test_testSCHunderCRSinsideSchedule'))
	addTest(suite, TestSCH('test_testSCHunderCRSoutsideScheduleFail'))

	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)