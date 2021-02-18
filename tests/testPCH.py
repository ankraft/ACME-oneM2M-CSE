#
#	testPCH.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for PollingChannel functionality
#

import unittest, sys, time
import requests
sys.path.append('../acme')
from typing import Tuple
from Constants import Constants as C
from Types import ResourceTypes as T, NotificationContentType, ResponseCode as RC, Operation, ResponseType, Permission
from init import *


class TestPCH(unittest.TestCase):

	ae 			= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyAppId',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createPCHwithWrongOriginator(self) -> None:
		"""	Create <PCH> with valid but different originator -> Fail"""
		self.assertIsNotNone(TestPCH.ae)
		dct = 	{ 'm2m:pch' : { 
					'rn' : pchRN,
				}}
		_, rsc = CREATE(aeURL, ORIGINATOR, T.PCH, dct)	# Admin, should still fail
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createPCH(self) -> None:
		"""	Create <PCH>"""
		self.assertIsNotNone(TestPCH.ae)
		dct = 	{ 'm2m:pch' : { 
					'rn' : pchRN,
				}}
		_, rsc = CREATE(aeURL, TestPCH.originator, T.PCH, dct)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSecondPCH(self) -> None:
		"""	Create second <PCH> -> Fail"""
		self.assertIsNotNone(TestPCH.ae)
		dct = 	{ 'm2m:pch' : { 
					'rn' : f'{pchRN}2',
				}}
		_, rsc = CREATE(aeURL, TestPCH.originator, T.PCH, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createPCHunderCSEBase(self) -> None:
		"""	Create <PCH> under <CSEBase> -> Fail """
		self.assertIsNotNone(TestPCH.ae)
		dct = 	{ 'm2m:pch' : { 
					'rn' : pchRN,
				}}
		_, rsc = CREATE(cseURL, ORIGINATOR, T.PCH, dct)
		self.assertEqual(rsc, RC.invalidChildResourceType)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrievePCH(self) -> None:
		""" Retrieve <PCH> """
		_, rsc = RETRIEVE(pchURL, TestPCH.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrievePCHwithWrongOriginator(self) -> None:
		""" Retrieve <PCH> """
		_, rsc = RETRIEVE(pchURL, 'wrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesPCH(self) -> None:
		"""	Test <PCH>'s attributes """
		r, rsc = RETRIEVE(pchURL, TestPCH.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:pch/ty'), T.PCH)
		self.assertIsNotNone(findXPath(r, 'm2m:pch/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:pch/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:pch/et'))
		self.assertLessEqual(findXPath(r, 'm2m:pch/ct'), findXPath(r, 'm2m:pch/lt'))
		self.assertLess(findXPath(r, 'm2m:pch/ct'), findXPath(r, 'm2m:pch/et'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deletePCHwrongOriginator(self) -> None:
		""" Delete <PCH> with wrong originator -> Fail """
		_, rsc = DELETE(pchURL, 'wrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deletePCH(self) -> None:
		""" Delete <PCH> with correct originator """
		_, rsc = DELETE(pchURL, self.originator)
		self.assertEqual(rsc, RC.deleted)

# TODO Non-Blocking async request, then retrieve notification via pcu
# TODO multiple non-blocking async requests, then retrieve notification via pcu

# TODO retrieve via PCU *after* delete

def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()

	# basic tests
	suite.addTest(TestPCH('test_createPCHwithWrongOriginator'))
	suite.addTest(TestPCH('test_createPCH'))
	suite.addTest(TestPCH('test_createSecondPCH'))
	suite.addTest(TestPCH('test_createPCHunderCSEBase'))
	suite.addTest(TestPCH('test_retrievePCH'))
	suite.addTest(TestPCH('test_retrievePCHwithWrongOriginator'))
	suite.addTest(TestPCH('test_attributesPCH'))

	# delete tests
	suite.addTest(TestPCH('test_deletePCHwrongOriginator'))
	suite.addTest(TestPCH('test_deletePCH'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)

