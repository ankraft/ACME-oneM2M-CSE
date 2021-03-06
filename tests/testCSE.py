#
#	testCSE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CSE functionality
#

import unittest, sys
sys.path.append('../acme')
from typing import Tuple
from Constants import Constants as C
from Types import ResponseCode as RC
from init import *


class TestCSE(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		pass


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		pass


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSE(self) -> None:
		"""	Retrieve <CB> """
		_, rsc = RETRIEVE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSEWithWrongOriginator(self) -> None:
		""" Retrieve <CB> with wrong originator -> Fail """
		_, rsc = RETRIEVE(cseURL, 'CWron')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesCSE(self) -> None:
		"""	Validate <CB> attributes """
		r, rsc = RETRIEVE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cb/csi')[0], '/')
		self.assertEqual(findXPath(r, 'm2m:cb/csi'), CSEID)
		self.assertEqual(findXPath(r, 'm2m:cb/pi'), '')
		self.assertEqual(findXPath(r, 'm2m:cb/rr'), False)
		self.assertEqual(findXPath(r, 'm2m:cb/rn'), CSERN)
		self.assertEqual(findXPath(r, 'm2m:cb/ty'), 5)
		self.assertEqual(findXPath(r, 'm2m:cb/ri'), CSEID[1:])
		self.assertIsNotNone(findXPath(r, 'm2m:cb/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:cb/cst'))
		self.assertIsNotNone(findXPath(r, 'm2m:cb/srt'))
		self.assertIsNotNone(srv := findXPath(r, 'm2m:cb/srv'))
		self.assertIsInstance(srv, list)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_CSESupportedResourceTypes(self) -> None:
		"""	Check <CB> SRT """
		r, rsc = RETRIEVE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(srt := findXPath(r, 'm2m:cb/srt'))
		for t in C.supportedResourceTypes:
			self.assertIn(t, srt)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCSE(self) -> None:
		"""	Delete <CB> -> Fail """
		_, rsc = DELETE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, RC.operationNotAllowed)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCSE(self) -> None:
		"""	Update <CB> -> Fail """
		dct = 	{ 'm2m:cse' : {
					'lbl' : [ 'aTag' ]
				}}
		_, rsc = UPDATE(cseURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.operationNotAllowed)


def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestCSE('test_retrieveCSE'))
	suite.addTest(TestCSE('test_retrieveCSEWithWrongOriginator'))
	suite.addTest(TestCSE('test_attributesCSE'))
	suite.addTest(TestCSE('test_CSESupportedResourceTypes'))
	suite.addTest(TestCSE('test_deleteCSE'))
	suite.addTest(TestCSE('test_updateCSE'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
