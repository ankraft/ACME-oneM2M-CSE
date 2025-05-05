#
#	testPDR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for policyDeletionRUles resources
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, ProcessControl, ProcessState
from init import *
		

class TestPDF(unittest.TestCase):

	ae = None
	aeRI = None
	ntp = None
	ntpRI = None

	originator = None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup Test PolicyDeletionRules')

		# Start notification server
		#startNotificationServer()

		dct:JSON = { 'm2m:ae' : {
						'rn'  : aeRN, 
						'api' : APPID,
				 		'rr'  : True,
				 		'srv' : [ RELEASEVERSION ]
					}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'

		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		cls.aeRI = findXPath(cls.ae, 'm2m:ae/ri')

		dct = { 'm2m:ntp': {
			'rn'  : ntpRN,
			'acn' : 1,
			'plbl': 'test',
			'cr' : None,
		}}
		cls.ntp, rsc = CREATE(cseURL, cls.originator, T.NTP, dct)
		cls.ntpRI = findXPath(cls.ntp, 'm2m:ntp/ri')


		testCaseEnd('Setup Test PolicyDeletionRules')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		testCaseStart('TearDown Test PolicyDeletionRules')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(ntpURL, ORIGINATOR)	
		testCaseEnd('TearDown Test TestLocation')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)

	#########################################################################

	#
	#	Basic tests
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createPDR(self) -> None:
		"""	CREATE <PDR> """

		dct:JSON = { 'm2m:pdr': {
			'rn'  : pdrRN,
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrievePDR(self) -> None:
		"""	RETRIEVE <PDR>"""

		r, rsc = RETRIEVE(pdrURL, self.originator)
		self.assertEqual(rsc, RC.OK, r)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updatePDR(self) -> None:
		"""	UPDATE <PDR>"""
		dct:JSON = { 'm2m:pdr': {
			'lbl' : [ 'test' ],
		}}
		r, rsc = UPDATE(pdrURL, self.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(lbl := findXPath(r, 'm2m:pdr/lbl'), r)
		self.assertEqual(lbl, [ 'test' ], r)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deletePDR(self) -> None:
		"""	DELETE <PDR>"""

		r, rsc = DELETE(pdrURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


#
#	Advanced tests
#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTooManyPDRsFail(self) -> None:
		"""	CREATE <PDR> with too many PDRs -> Fail"""

		# Create 2 aditional PDRs. The first two ones should succeed, the third one should fail

		for i in range(2):
			dct:JSON = { 'm2m:pdr': {
				'rn'  : f'{pdrRN}{i}',
			}}
			r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
			self.assertEqual(rsc, RC.CREATED, r)

		dct = { 'm2m:pdr': {
			'rn'  : f'{pdrRN}2',
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CONFLICT, r)

		# delete the PDRs again
		for i in range(2):
			r, rsc = DELETE(f'{pdrURL}{i}', self.originator)
			self.assertEqual(rsc, RC.DELETED, r)

	#########################################################################


def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestPDF, [

		# basic tests
		'test_createPDR',
		'test_retrievePDR',
		'test_updatePDR',
		'test_deletePDR',

		# advanced tests
		'test_createTooManyPDRsFail',

	])

	# Run the tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)