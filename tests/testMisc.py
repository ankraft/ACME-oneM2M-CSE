#
#	testMisc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Miscellaneous unit tests
#

import unittest, sys
sys.path.append('../acme')
from typing import Tuple
from Constants import Constants as C
from Types import ResponseCode as RC, ResourceTypes as T
from init import *

class TestMisc(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		pass


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		pass

	# TODO move to http test
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPRVI(self) -> None:
		"""	Check RVI parameter in response """
		_, rsc = RETRIEVE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIn('X-M2M-RVI', lastHeaders())
		self.assertEqual(lastHeaders()['X-M2M-RVI'], RVI)


	# TODO move to http test
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPRVIWrongInRequest(self) -> None:
		"""	Check Wrong RVI version parameter in request -> Fail"""
		_, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={'X-M2M-RVI' : '1'})
		self.assertEqual(rsc, RC.releaseVersionNotSupported)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createUnknownResourceType(self) -> None:
		"""	Create an unknown resource type -> Fail """
		dct = 	{ 'foo:bar' : { 
					'rn' : 'foo',
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, 999, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createEmpty(self) -> None:
		"""	Create with empty content -> Fail """
		dct = 	None
		r, rsc = CREATE(cseURL, ORIGINATOR, T.AE, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateEmpty(self) -> None:
		"""	Update with empty content -> Fail """
		dct = 	None
		r, rsc = UPDATE(cseURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAlphaResourceType(self) -> None:
		""" Create a resource with alphanumerical type -> Fail """
		dct = 	{ 'foo:bar' : { 
					'rn' : 'foo',
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, 'wrong', dct)	# type: ignore # Ignore type of type
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createWithWrongResourceType(self) -> None:
		"""	Create resource w -> Fail """
		dct = 	{ 'm2m:ae' : { 
					'rn' : 'foo',
				}}
		_, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.badRequest)


# TODO test for creating a resource with missing type parameter

def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestMisc('test_checkHTTPRVI'))
	suite.addTest(TestMisc('test_checkHTTPRVIWrongInRequest'))
	suite.addTest(TestMisc('test_createUnknownResourceType'))
	suite.addTest(TestMisc('test_createEmpty'))
	suite.addTest(TestMisc('test_updateEmpty'))
	suite.addTest(TestMisc('test_createAlphaResourceType'))
	suite.addTest(TestMisc('test_createWithWrongResourceType'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
