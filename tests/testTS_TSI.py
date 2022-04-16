#
#	testTS_TCI.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for timeSeriean & timeSeries functionality
#

import unittest, sys, datetime
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from acme.etc.DateUtils import toISO8601Date, getResourceDate
from init import *

maxBS	= 30
maxMdn	= 5
pei 	= int(timeSeriesInterval * 1000)
mdt 	= int(pei * 0.8) # > peid



class TestTS_TSI(unittest.TestCase):

	ae 			= None
	originator 	= None
	sub			= None
	ts 			= None
	sub 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:

		# Start notification server
		startNotificationServer()

		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'

		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : True,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		dct = 	{ 'm2m:ts' : { 
					'rn'  : tsRN,
					'mni' : 3
				}}
		cls.ts, rsc = CREATE(aeURL, cls.originator, T.TS, dct)
		assert rsc == RC.created, 'cannot create <timeSeries>'
		assert findXPath(cls.ts, 'm2m:ts/mni') == 3, 'mni is not correct'


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()



	def _stopMonitoring(self) -> None:
		""" Stop monitoring by setting mdd to False. """
		dct = 	{ 'm2m:ts' : { 
			'mdd' : False
		}}
		r, rsc = UPDATE(tsURL, TestTS_TSI.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertFalse(findXPath(r, 'm2m:ts/mdd'), r)
	
	
	def _startMonitoring(self) -> None:
		""" Stop monitoring by setting mdd to False. """
		dct = 	{ 'm2m:ts' : { 
			'mdd' : True	# Start monitoring
		}}
		r, rsc = UPDATE(tsURL, TestTS_TSI.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertTrue(findXPath(r, 'm2m:ts/mdd'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertEqual(len(findXPath(r, 'm2m:ts/mdlt')), 0, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addTSI(self) -> None:
		"""	CREATE <TSI> under <TS> """
		self.assertIsNotNone(TestTS_TSI.ae)
		self.assertIsNotNone(TestTS_TSI.ts)
		dct = 	{ 'm2m:tsi' : {
					'dgt' : (date := getResourceDate()),
					'con' : 'aValue',
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.created, r)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:tsi/ri'), r)
		self.assertEqual(findXPath(r, 'm2m:tsi/con'), 'aValue', r)
		self.assertEqual(findXPath(r, 'm2m:tsi/dgt'), date, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/cs'), 6, r)
		self.rsiARi = findXPath(r, 'm2m:tsi/ri', r)			# store ri

		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cni'), r)
		self.assertIsInstance(findXPath(r, 'm2m:ts/cni'), int, r)
		self.assertEqual(findXPath(r, 'm2m:ts/cni'), 1, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cbs'), r)
		self.assertIsInstance(findXPath(r, 'm2m:ts/cbs'), int, r)
		self.assertEqual(findXPath(r, 'm2m:ts/cbs'), 6, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addMoreTSI(self) -> None:
		"""	CREATE more <TSI>s under <TS> """
		dct = 	{ 'm2m:tsi' : {
					'dgt' : (date := getResourceDate()),
					'con' : 'bValue'
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.created, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/con'), 'bValue', r)
		self.assertEqual(findXPath(r, 'm2m:tsi/dgt'), date, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/cs'), 6, r)

		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cni'), r)
		self.assertIsInstance(findXPath(r, 'm2m:ts/cni'), int, r)
		self.assertEqual(findXPath(r, 'm2m:ts/cni'), 2, r)
		self.assertEqual(findXPath(r, 'm2m:ts/cbs'), 12, r)

		dct = 	{ 'm2m:tsi' : {
					'dgt' : (date := getResourceDate()),
					'con' : 'cValue'
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.created, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/con'), 'cValue', r)
		self.assertEqual(findXPath(r, 'm2m:tsi/dgt'), date, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/cs'), 6, r)

		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cni'), r)
		self.assertIsInstance(findXPath(r, 'm2m:ts/cni'), int, r)
		self.assertEqual(findXPath(r, 'm2m:ts/cni'), 3)
		self.assertEqual(findXPath(r, 'm2m:ts/cbs'), 18, r)

		dct = 	{ 'm2m:tsi' : {
					'dgt' : (date := getResourceDate()),
					'con' : 'dValue'
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.created, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/con'), 'dValue', r)
		self.assertEqual(findXPath(r, 'm2m:tsi/dgt'), date, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/cs'), 6, r)

		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cni'), r)
		self.assertIsInstance(findXPath(r, 'm2m:ts/cni'), int, r)
		self.assertEqual(findXPath(r, 'm2m:ts/cni'), 3, r)
		self.assertEqual(findXPath(r, 'm2m:ts/cbs'), 18, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveTSLa(self) -> None:
		"""	RETRIEVE <TS>.LA """
		r, rsc = RETRIEVE(f'{tsURL}/la', TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(r, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/ty'), T.TSI, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/con'), 'dValue', r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveTSOl(self) -> None:
		""" RETRIEVE <TS>.OL """
		r, rsc = RETRIEVE(f'{tsURL}/ol', TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(r, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/ty'), T.TSI, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/con'), 'bValue', r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_changeTSMni(self) -> None:
		"""	UPDATE <TS>.MNI to 1 -> OL == LA """
		dct = 	{ 'm2m:ts' : {
					'mni' : 1
 				}}
		r, rsc = UPDATE(tsURL, TestTS_TSI.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNotNone(r, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mni'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mni'), 1, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cni'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/cni'), 1, r)
		self.assertEqual(findXPath(r, 'm2m:ts/cbs'), 6, r)

		r, rsc = RETRIEVE(f'{tsURL}/la', TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(r, r)
		self.assertIsNotNone(findXPath(r, 'm2m:tsi/con'), r)
		self.assertEqual(findXPath(r, 'm2m:tsi/con'), 'dValue', r)

		r, rsc = RETRIEVE(f'{tsURL}/ol', TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(r, r)
		self.assertIsNotNone(findXPath(r, 'm2m:tsi/con'), r)
		self.assertEqual(findXPath(r, 'm2m:tsi/con'), 'dValue', r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteTS(self) -> None:
		"""	DELETE <TS> """
		r, rsc = DELETE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.deleted, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSwithMBS(self) -> None:
		"""	CREATE <TS> with mbs"""
		dct = 	{ 'm2m:ts' : { 
					'rn'  : tsRN,
					'mbs' : maxBS
				}}
		TestTS_TSI.ts, rsc = CREATE(aeURL, TestTS_TSI.originator, T.TS, dct)
		self.assertEqual(rsc, RC.created, TestTS_TSI.ts)
		self.assertIsNotNone(findXPath(TestTS_TSI.ts, 'm2m:ts/mbs'), TestTS_TSI.ts)
		self.assertEqual(findXPath(TestTS_TSI.ts, 'm2m:ts/mbs'), maxBS, TestTS_TSI.ts)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSIexactSize(self) -> None:
		"""	CREATE <TSI> to <TS> with exact max size"""
		dct = 	{ 'm2m:tsi' : {
					'dgt' : getResourceDate(),
					'con' : 'x' * maxBS
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.created, r)
		self.assertEqual(findXPath(r, 'm2m:tsi/cs'), maxBS, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSItooLarge(self) -> None:
		"""	CREATE <TSI> to <TS> with size > mbs -> Fail """
		dct = 	{ 'm2m:tsi' : {
					'dgt' : getResourceDate(),
					'con' : 'x' * (maxBS + 1)
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.notAcceptable, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSIsForTSwithSize(self) -> None:
		"""	CREATE multiple <TSI>s to <TS> with size restrictions """
		# First fill up the container
		for _ in range(int(maxBS / 3)):
			dct = 	{ 'm2m:tsi' : {
						'dgt' : getResourceDate(),
						'con' : 'x' * int(maxBS / 3)
					}}
			r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
			self.assertEqual(rsc, RC.created, r)
		
		# Test latest TSI for x
		r, rsc = RETRIEVE(f'{tsURL}/la', TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:tsi/con'), r)
		self.assertTrue(findXPath(r, 'm2m:tsi/con').startswith('x'), r)
		self.assertEqual(len(findXPath(r, 'm2m:tsi/con')), int(maxBS / 3), r)

		# Add another TSI
		dct = 	{ 'm2m:tsi' : {
					'dgt' : getResourceDate(),
					'con' : 'y' * int(maxBS / 3)
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.created, r)

		# Test latest TSI for y
		r, rsc = RETRIEVE(f'{tsURL}/la', TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:tsi/con'), r)
		self.assertTrue(findXPath(r, 'm2m:tsi/con').startswith('y'), r)
		self.assertEqual(len(findXPath(r, 'm2m:tsi/con')), int(maxBS / 3), r)

		# Test TS
		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cni'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/cni'), 3, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cbs'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/cbs'), maxBS, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSIwithoutDGT(self) -> None:
		"""	CREATE <TSI> without DGT attribute -> Fail """
		dct = 	{ 'm2m:tsi' : {
					'con' : 'wrong'
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSIwithSameDGT(self) -> None:
		"""	CREATE <TSI>s with same DGT attribute -> Fail """
		dct = 	{ 'm2m:tsi' : {
					'dgt' : (date := getResourceDate()),
					'con' : 'first'
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.created, r)
		dct = 	{ 'm2m:tsi' : {
					'dgt' : date,	# same date
					'con' : 'second'
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.conflict, r)	# CONFLICTs


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSIwithSNR(self) -> None:
		"""	CREATE <TSI> with SNR"""
		dct = 	{ 'm2m:tsi' : {
					'dgt' : (date := getResourceDate()),
					'con' : 'aValue',
					'snr' : 1
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.created, r)

		r, rsc = RETRIEVE(f'{tsURL}/la', TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:tsi/snr'), r)
		self.assertEqual(findXPath(r, 'm2m:tsi/snr'), 1, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSwithMonitoring(self) -> None:
		"""	CREATE <TS> with monitoring enabled"""
		dct = 	{ 'm2m:ts' : { 
					'rn'  : tsRN,	
					'pei' : pei,
					'mdd' : True,
					'mdn' : maxMdn,
					'mdt' : mdt

				}}
		TestTS_TSI.ts, rsc = CREATE(aeURL, TestTS_TSI.originator, T.TS, dct)
		self.assertEqual(rsc, RC.created, TestTS_TSI.ts)
		self.assertIsNotNone(findXPath(TestTS_TSI.ts, 'm2m:ts/pei'), TestTS_TSI.ts)
		self.assertEqual(findXPath(TestTS_TSI.ts, 'm2m:ts/pei'), pei, TestTS_TSI.ts)
		self.assertIsNotNone(findXPath(TestTS_TSI.ts, 'm2m:ts/mdd'), TestTS_TSI.ts)
		self.assertTrue(findXPath(TestTS_TSI.ts, 'm2m:ts/mdd'), TestTS_TSI.ts)
		# TODO Discussion whether mdlt is always present
		# self.assertIsNone(findXPath(TestTS_TSI.ts, 'm2m:ts/mdlt'), TestTS_TSI.ts)	# empty mdlt is not created by default
		self.assertIsNotNone(findXPath(TestTS_TSI.ts, 'm2m:ts/mdlt'), TestTS_TSI.ts)
		self.assertIsNotNone(findXPath(TestTS_TSI.ts, 'm2m:ts/mdc'), TestTS_TSI.ts)
		self.assertEqual(findXPath(TestTS_TSI.ts, 'm2m:ts/mdc'), 0, TestTS_TSI.ts)
		self.assertIsNotNone(findXPath(TestTS_TSI.ts, 'm2m:ts/mdt'), TestTS_TSI.ts)
		self.assertEqual(findXPath(TestTS_TSI.ts, 'm2m:ts/mdt'), mdt, TestTS_TSI.ts)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSIinPeriod(self) -> None:
		"""	CREATE 3 <TSI> within the time period"""

		self._startMonitoring()

		date = datetime.datetime.utcnow().timestamp()
		for i in range(3):
			dct = 	{ 'm2m:tsi' : {
						'dgt' : toISO8601Date(date),
						'con' : 'aValue',
						'snr' : i
					}}
			r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
			self.assertEqual(rsc, RC.created, r)
			# time.sleep(pei / 1000)
			time.sleep(timeSeriesInterval - (datetime.datetime.utcnow().timestamp() - date)) # == pei
			date += timeSeriesInterval

		# Check TS for missing TSI
		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0, r)	# MissingDataCount == 0

		self._stopMonitoring()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSIinPeriodDgtTooEarly(self) -> None:
		"""	CREATE 1+3 <TSI> within the time period, but dgt is too early -> Fail"""

		self._startMonitoring()

		dgt = datetime.datetime.utcnow().timestamp() - timeSeriesInterval
		for i in range(4):
			dct = 	{ 'm2m:tsi' : {
						'dgt' : toISO8601Date(dgt),
						'con' : 'aValue',
						'snr' : i
					}}
			r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
			self.assertEqual(rsc, RC.created, r)
			time.sleep(timeSeriesInterval) # == pei
			dgt += timeSeriesInterval

		# Check TS for missing TSI
		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		# The next test 4 instead of 3 bc we sleeped in the above loop, and in the meantime
		# the CSE detected another missing TSI, which is correct.
		self.assertGreaterEqual(findXPath(r, 'm2m:ts/mdc'), 3, r)	# MissingDataCount >= 3

		self._stopMonitoring()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSIinPeriodDgtTooLate(self) -> None:
		"""	CREATE 1+3 <TSI> within the time period, but dgt is too late -> Fail"""

		self._startMonitoring()

		dgt = datetime.datetime.utcnow().timestamp()
		for i in range(4):
			dct = 	{ 'm2m:tsi' : {
						'dgt' : toISO8601Date(dgt),
						'con' : 'aValue',
						'snr' : i
					}}
			r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
			self.assertEqual(rsc, RC.created, r)
			time.sleep(timeSeriesInterval) # == pei
			dgt += timeSeriesInterval * 2	# too late

		# Check TS for missing TSI
		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertGreaterEqual(findXPath(r, 'm2m:ts/mdc'), 3, r)	# MissingDataCount == 3

		self._stopMonitoring()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSIinPeriodDgtWayTooEarly(self) -> None:
		"""	CREATE 1+3 <TSI> within the time period, but dgt is way too early -> Fail"""

		self._startMonitoring()

		dgt = datetime.datetime.utcnow().timestamp()
		for i in range(4):
			dct = 	{ 'm2m:tsi' : {
						'dgt' : toISO8601Date(dgt),
						'con' : 'aValue',
						'snr' : i
					}}
			r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
			self.assertEqual(rsc, RC.created, r)
			time.sleep(timeSeriesInterval) # == pei
			dgt += 1	# minimal different

		# Check TS for missing TSI
		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		# The next test 4 instead of 3 bc we sleeped in the above loop, and in the meantime
		# the CSE detected another missing TSI, which is correct.
		self.assertGreaterEqual(findXPath(r, 'm2m:ts/mdc'), 3, r)	# MissingDataCount >= 3

		self._stopMonitoring()


	def _createTSInotInPeriod(self, expectedMdc:int) -> None:
		"""	CREATE n <TSI> not within the time period """
		dct = 	{ 'm2m:ts' : { 
			'mdd' : True	# Start monitoring
		}}
		r, rsc = UPDATE(tsURL, TestTS_TSI.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdt'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdt'), mdt, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0, r)

		_pei = findXPath(r, 'm2m:ts/pei') / 1000.0
		_mdt = findXPath(r, 'm2m:ts/mdt') / 1000.0 
		for i in range(expectedMdc + 1):	# first doesn't count
			tsidct = { 'm2m:tsi' : {
						'dgt' : (date := getResourceDate()),
						'con' : 'aValue',
						'snr' : i
					}}
			r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, tsidct)
			self.assertEqual(rsc, RC.created, r)
			time.sleep(_pei + (_mdt * 2.0))

			# r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
			# self.assertIsNotNone(findXPath(r, 'm2m:ts/mdlt'), r)
			# self.assertLessEqual(len(findXPath(r, 'm2m:ts/mdlt')), maxMdn, r)

		
		# Check TS for missing TSI
		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		if expectedMdc > maxMdn:
			self.assertGreaterEqual(findXPath(r, 'm2m:ts/mdc'), maxMdn, r)			# MissingDataCount == maxMdn
		else:
			self.assertGreaterEqual(findXPath(r, 'm2m:ts/mdc'), expectedMdc, r)	# MissingDataCount == expectedMdc


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSInotInPeriod(self) -> None:
		"""	CREATE <TSI> not within the time period """
		self._createTSInotInPeriod(3)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSInotInPeriodLarger(self) -> None:
		"""	CREATE more <TSI> not within the time period """
		self._createTSInotInPeriod(maxMdn + 1)	# one more to check list size, 
		# dont remove list for next tests


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipIf(maxMdn < 3, 'mdn is set to < 3')
	def test_updateTSMddEnable(self) -> None:
		"""	UPDATE <TS> set mdd again and enable monitoring """
		dct = 	{ 'm2m:ts' : { 
			'mdd' : True
		}}
		r, rsc = UPDATE(tsURL, TestTS_TSI.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdd'), r)
		self.assertTrue(findXPath(r, 'm2m:ts/mdd'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertEqual(len(findXPath(r, 'm2m:ts/mdlt')),  0, r)
		self._startMonitoring()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createMissingDataSubUnderTS(self) -> None:
		"""	CREATE <sub> for missing data monitoring """
		clearLastNotification()
		dct = 	{ 'm2m:sub' : { 
			'rn' : subRN,
			'enc': {
				'net': [ 8 ],
				'md' : {
					'dur': f'PT{pei*maxMdn/1000}S',
					'num': maxMdn - 2,
				}
			},
			'nu': [ NOTIFICATIONSERVER ]
		}}
		TestTS_TSI.sub, rsc = CREATE(tsURL, TestTS_TSI.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(TestTS_TSI.sub, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createMissingDataForSub(self) -> None:
		"""	CREATE missing data for <sub> monitoring """
		clearLastNotification()

		# Start the timeSeries monitoring
		dgt = datetime.datetime.utcnow().timestamp() 
		dct = 	{ 'm2m:tsi' : {
					'dgt' : toISO8601Date(dgt),
					'con' : 'aValue',
					'snr' : 0
				}}
		r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
		self.assertEqual(rsc, RC.created, r)
		time.sleep(timeSeriesInterval) # == pei
		# time.sleep(timeSeriesInterval + 0.1) # == pei + a short offset
		start = time.time()
		dgt += timeSeriesInterval * 2

		# Add further TSI
		for i in range(0, maxMdn * 2):
			dct = 	{ 'm2m:tsi' : {
						'dgt' : toISO8601Date(dgt),
						'con' : 'aValue',
						'snr' : i
					}}
			r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
			self.assertEqual(rsc, RC.created, r)
			time.sleep(timeSeriesInterval - (time.time() - start) ) # == pei - processing time
			start = time.time()
			dgt += timeSeriesInterval

			# Check notifications
			lastNotification = getLastNotification(True)
			if i % maxMdn == (maxMdn-2-1):
				self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:tsn'), lastNotification)
				self.assertEqual(len(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:tsn/mdlt')), maxMdn-2, lastNotification)
				self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:tsn/mdc'), maxMdn-2, lastNotification)
			elif i % maxMdn >= maxMdn-2:
				self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:tsn'), lastNotification)
				self.assertEqual(len(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:tsn/mdlt')), 1, lastNotification)
				self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:tsn/mdc'), (i%maxMdn)+1, lastNotification)
			else:
				self.assertIsNone(lastNotification, lastNotification)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteMissingDataSubUnderTS(self) -> None:
		"""	DELETE <sub> for missing data monitoring """
		r, rsc = DELETE(f'{tsURL}/{subRN}', TestTS_TSI.originator)
		self.assertEqual(rsc, RC.deleted, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_setMddToFalseAfterAWhile(self) -> None:
		"""	Set MDD to False after a moment. mdlt & mdc shall persist  """
		dct = 	{ 'm2m:ts' : { 
					'rn'  : tsRN,
					'pei' : pei,
					'mdd' : True,
					'mdn' : maxMdn,
					'mdt' : mdt,
				}}
		r, rsc = CREATE(aeURL, TestTS_TSI.originator, T.TS, dct)
		self.assertEqual(rsc, RC.created, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)

		# Add some TSI
		for i in range(0, 5):
			dct = 	{ 'm2m:tsi' : {
						'dgt' : toISO8601Date(datetime.datetime.utcnow().timestamp()),
						'con' : 'aValue',
						'snr' : i
					}}
			r, rsc = CREATE(tsURL, TestTS_TSI.originator, T.TSI, dct)
			self.assertEqual(rsc, RC.created, r)
			time.sleep(0.5)
		time.sleep(timeSeriesInterval * 2)

		# Check TS
		r, rsc = RETRIEVE(tsURL, TestTS_TSI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cni'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertGreater(findXPath(r, 'm2m:ts/mdc'), 0, r)
		self.assertGreater(len(findXPath(r, 'm2m:ts/mdlt')), 0, r)

		# Disable mdd: Expected mdlt, cni are not changed
		dct = 	{ 'm2m:ts' : { 
					'mdd' : False,
				}}
		r, rsc = UPDATE(tsURL, TestTS_TSI.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cni'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertGreater(findXPath(r, 'm2m:ts/mdc'), 0, r)
		self.assertGreater(len(findXPath(r, 'm2m:ts/mdlt')), 0, r)



# TODO: instead of mdt:9999 set the mdn to None etc.


def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestTS_TSI('test_addTSI'))
	suite.addTest(TestTS_TSI('test_addMoreTSI'))
	suite.addTest(TestTS_TSI('test_retrieveTSLa'))
	suite.addTest(TestTS_TSI('test_retrieveTSOl'))
	suite.addTest(TestTS_TSI('test_changeTSMni'))
	suite.addTest(TestTS_TSI('test_deleteTS'))
	
	suite.addTest(TestTS_TSI('test_createTSwithMBS'))
	suite.addTest(TestTS_TSI('test_createTSIexactSize'))
	suite.addTest(TestTS_TSI('test_createTSItooLarge'))
	suite.addTest(TestTS_TSI('test_createTSIsForTSwithSize'))
	suite.addTest(TestTS_TSI('test_createTSIwithoutDGT'))
	suite.addTest(TestTS_TSI('test_createTSIwithSameDGT'))
	suite.addTest(TestTS_TSI('test_createTSIwithSNR'))
	suite.addTest(TestTS_TSI('test_deleteTS'))

	suite.addTest(TestTS_TSI('test_setMddToFalseAfterAWhile'))
	suite.addTest(TestTS_TSI('test_deleteTS'))

	suite.addTest(TestTS_TSI('test_createTSwithMonitoring'))
	suite.addTest(TestTS_TSI('test_createTSIinPeriod'))					# Start monitoring
	suite.addTest(TestTS_TSI('test_createTSInotInPeriod'))				# Start monitoring
	suite.addTest(TestTS_TSI('test_createTSIinPeriodDgtTooEarly'))		# dgt too early
	suite.addTest(TestTS_TSI('test_createTSIinPeriodDgtTooLate'))		# dgt too late
	suite.addTest(TestTS_TSI('test_createTSInotInPeriodLarger'))		# run the test again to overflow mdlt
	suite.addTest(TestTS_TSI('test_createTSIinPeriodDgtWayTooEarly'))	# dgt way to early

	suite.addTest(TestTS_TSI('test_updateTSMddEnable'))

	# Test MissingData subscriptions
	suite.addTest(TestTS_TSI('test_deleteTS'))
	suite.addTest(TestTS_TSI('test_createTSwithMonitoring'))
	suite.addTest(TestTS_TSI('test_createMissingDataSubUnderTS'))
	suite.addTest(TestTS_TSI('test_createMissingDataForSub'))
	suite.addTest(TestTS_TSI('test_deleteMissingDataSubUnderTS'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
