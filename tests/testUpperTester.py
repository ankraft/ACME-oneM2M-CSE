#
#	testUpperTester.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Upper Tester functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from init import *
from acme.etc.Types import CSEStatus
from acme.etc.Types import ResponseStatusCode as RC
from acme.etc.Constants import Constants as C
from typing import Tuple


class TestUpperTester(unittest.TestCase):

	ae 			= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		pass


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		pass


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkStatus(self) -> None:
		""" Check CSE status via UT interface """#
		resp = requests.post(UTURL, headers = { UTCMD: f'status'})
		self.assertEqual(resp.status_code, 200)
		self.assertIn(C.hfRSC, resp.headers)
		self.assertEqual(resp.headers[C.hfRSC], '2000')
		self.assertIn(resp.headers[UTRSP], ['STOPPED', 'STARTING', 'RUNNING', 'STOPPING', 'RESETTING'])
		self.assertTrue(CSEStatus.has(resp.headers[UTRSP]))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_performReset(self) -> None:
		""" Perform a CSE reset via UT interface """

		# Retrieve CSE
		cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(oldCt := findXPath(cse, 'm2m:cb/ct'))

		# Reset
		resp = requests.post(UTURL, headers = { UTCMD: f'Reset'})
		self.assertEqual(resp.status_code, 200)
		self.assertIn(C.hfRSC, resp.headers)
		self.assertEqual(resp.headers[C.hfRSC], '2000')

		# Retrieve CSE again and compare ct
		cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(newCt := findXPath(cse, 'm2m:cb/ct'))
		self.assertGreater(newCt, oldCt)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_enableShortRequestExpiration(self) -> None:
		""" Enable short request expiration interval via UT interface """#
		resp = requests.post(UTURL, headers = { UTCMD: f'enableShortRequestExpiration 5'})
		self.assertEqual(resp.status_code, 200)
		self.assertIn(C.hfRSC, resp.headers)
		self.assertEqual(resp.headers[C.hfRSC], '2000')
		self.assertIsNotNone(resp.headers[UTRSP])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_disableShortRequestExpiration(self) -> None:
		""" Disable short request expiration interval via UT interface """#
		resp = requests.post(UTURL, headers = { UTCMD: f'disableShortRequestExpiration'})
		self.assertEqual(resp.status_code, 200)
		self.assertIn(C.hfRSC, resp.headers)
		self.assertEqual(resp.headers[C.hfRSC], '2000')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_enableShortResourceExpiration(self) -> None:
		""" Enable short resource expiration interval via UT interface """#
		resp = requests.post(UTURL, headers = { UTCMD: f'enableShortResourceExpiration 5'})
		self.assertEqual(resp.status_code, 200)
		self.assertIn(C.hfRSC, resp.headers)
		self.assertEqual(resp.headers[C.hfRSC], '2000')
		self.assertIsNotNone(resp.headers[UTRSP])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_disableShortResourceExpiration(self) -> None:
		""" Disable short request expiration interval via UT interface """#
		resp = requests.post(UTURL, headers = { UTCMD: f'disableShortResourceExpiration'})
		self.assertEqual(resp.status_code, 200)
		self.assertIn(C.hfRSC, resp.headers)
		self.assertEqual(resp.headers[C.hfRSC], '2000')


def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()

	suite.addTest(TestUpperTester('test_checkStatus'))
	suite.addTest(TestUpperTester('test_performReset'))
	suite.addTest(TestUpperTester('test_enableShortRequestExpiration'))
	suite.addTest(TestUpperTester('test_disableShortRequestExpiration'))
	suite.addTest(TestUpperTester('test_enableShortResourceExpiration'))
	suite.addTest(TestUpperTester('test_disableShortResourceExpiration'))

	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
