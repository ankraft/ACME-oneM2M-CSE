 #
#	testDAC.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for DynamicCondynamicAuthorization functionality
#

import unittest, sys

if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.DateUtils import toISO8601Date
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, TimeWindowType
from acme.etc.Types import NotificationEventType, NotificationEventType as NET
from init import *


class TestDAC(unittest.TestCase):

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
		testCaseStart('Setup TestDAC')

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
	
		testCaseEnd('Setup TestDAC')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		testCaseStart('TearDown TestDAC')
		DELETE(dacURL, ORIGINATOR)	# Just delete the DAC and everything below it. Ignore whether it exists or not
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestDAC')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDACunderCSEFail(self) -> None:
		"""	CREATE invalid <DAC> under CSEBase -> Fail"""
		dct = 	{ 'm2m:dac' : {
					'rn' : dacRN,
					'dae': False
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.DAC, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDACunderCSE(self) -> None:
		"""	CREATE invalid <DAC> under CSEBase"""
		dct = 	{ 'm2m:dac' : {
					'rn' : dacRN,
					'dae': False,
					'dap': [ 'aURL' ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.DAC, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveDACunderCSE(self) -> None:
		"""	RETRIEVE <DAC> under CSEBase"""
		r, rsc = RETRIEVE(dacURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:dac/rn'), dacRN, r)
		self.assertEqual(findXPath(r, 'm2m:dac/dae'), False, r)
		self.assertEqual(findXPath(r, 'm2m:dac/dap'), [ 'aURL' ], r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDACunderCSEFail(self) -> None:
		"""	UPDATE invalid <DAC> under CSEBase - remove mandatory attribute -> Fail"""
		dct = 	{ 'm2m:dac' : {
					'dap': None
				}}
		r, rsc = UPDATE(dacURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDACunderCSE2Fail(self) -> None:
		"""	UPDATE invalid <DAC> under CSEBase - empty list  -> Fail"""
		dct = 	{ 'm2m:dac' : { # type: ignore
					'dap': []
				}}
		r, rsc = UPDATE(dacURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDACunderCSE(self) -> None:
		"""	UPDATE valid <DAC> under CSEBase"""
		ts = toISO8601Date(utcTimestamp() + 5000)
		dct = 	{ 'm2m:dac' : {
					'dae': True,
					'dap': [ 'aURL2', 'aURL3' ],
					'dal': ts
				}}
		r, rsc = UPDATE(dacURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		r, rsc = RETRIEVE(dacURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:dac/rn'), dacRN, r)
		self.assertEqual(findXPath(r, 'm2m:dac/dae'), True, r)
		self.assertEqual(findXPath(r, 'm2m:dac/dap'), [ 'aURL2', 'aURL3' ], r)
		self.assertEqual(findXPath(r, 'm2m:dac/dal'), ts, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteDACunderCSE(self) -> None:
		"""	DELETE <DAC> under CSEBase"""
		r, rsc = DELETE(dacURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDACunderAE(self) -> None:
		"""	CREATE <DAC> under AE"""
		dct = 	{ 'm2m:dac' : {
					'rn' : dacRN,
					'dae': False,
					'dap': [ 'aURL' ]
				}}
		r, rsc = CREATE(aeURL, ORIGINATOR, T.DAC, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveDACunderAE(self) -> None:
		"""	RETRIEVE <DAC> under AE"""
		r, rsc = RETRIEVE(f'{aeURL}/{dacRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:dac/rn'), dacRN, r)
		self.assertEqual(findXPath(r, 'm2m:dac/dae'), False, r)
		self.assertEqual(findXPath(r, 'm2m:dac/dap'), [ 'aURL' ], r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDACunderAE(self) -> None:
		"""	UPDATE <DAC> under AE"""
		ts = toISO8601Date(utcTimestamp() + 5000)
		dct = 	{ 'm2m:dac' : {
					'dae': True,
					'dap': [ 'aURL2', 'aURL3' ],
					'dal': ts
				}}
		r, rsc = UPDATE(f'{aeURL}/{dacRN}', ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		r, rsc = RETRIEVE(f'{aeURL}/{dacRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:dac/rn'), dacRN, r)
		self.assertEqual(findXPath(r, 'm2m:dac/dae'), True, r)
		self.assertEqual(findXPath(r, 'm2m:dac/dap'), [ 'aURL2', 'aURL3' ], r)
		self.assertEqual(findXPath(r, 'm2m:dac/dal'), ts, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteDACunderAE(self) -> None:
		"""	DELETE <DAC> under AE"""
		r, rsc = DELETE(f'{aeURL}/{dacRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)

		
def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestDAC, [

		# basic tests
		'test_createDACunderCSEFail',
		'test_createDACunderCSE',
		'test_retrieveDACunderCSE',
		'test_updateDACunderCSEFail',
		'test_updateDACunderCSE2Fail',
		'test_updateDACunderCSE',
		'test_deleteDACunderCSE',

		'test_createDACunderAE',
		'test_retrieveDACunderAE',
		'test_updateDACunderAE',
		'test_deleteDACunderAE',

	])

	# Run tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)