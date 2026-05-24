#
#	testALST.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for AEContactList (ALST) resource type.
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *

class TestALST(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestALST')
	
		testCaseEnd('Setup TestALST')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestALST')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestALST')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)



	#########################################################################
	#
	#	Basic tests

	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'ALST resource type is only allowed on an IN-CSE')
	def test_createALSTFail(self) -> None:
		"""	CREATE <ALST> via request -> FAIL """
		dct = 	{ 'm2m:alst' : { 
					'rn' : 'failALST',
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.ALST, dct)
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'ALST resource type is only allowed on an IN-CSE')
	def test_deleteALSTFail(self) -> None:
		"""	DELETE <ALST> via request -> FAIL """
		r, rsc = DELETE(f'{cseURL}/{alstRN}', ORIGINATOR)	# type: ignore[name-defined]
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED, r)


def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestALST, [

		# basic tests
		'test_createALSTFail',
		'test_deleteALSTFail',
		# TODO no test for update, because the procedurs in TS-0004 are wrong
	])

	# Run tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)