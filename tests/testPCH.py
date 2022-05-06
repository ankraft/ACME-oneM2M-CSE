#
#	testPCH.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for PollingChannel functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, Permission
from init import *

aeRN2 = f'{aeRN}2'
ae2URL = f'{aeURL}2'

class TestPCH(unittest.TestCase):

	ae 			= None
	ae2 		= None
	acp			= None
	acpRI		= None
	originator 	= None
	originator2	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyAppId',
				 	'rr'  : True,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		# Create 2nd AE

		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN2, 
					'api' : 'NMyAppId',
				 	'rr'  : True,
				 	'srv' : [ '3' ]
				}}
		cls.ae2, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator2 = findXPath(cls.ae2, 'm2m:ae/aei')

		# Add permissions for second AE to first AE
		dct = 	{ "m2m:acp": {
			"rn": acpRN,
			"pv": {
				"acr": [ { 	
					"acor": [ cls.originator, cls.originator2 ],
					"acop": Permission.ALL
				}
				]
			},
			"pvs": { 
				"acr": [ {
					"acor": [ cls.originator ],
					"acop": Permission.ALL
				} ]
			},
		}}
		cls.acp, rsc = CREATE(aeURL, cls.originator, T.ACP, dct)
		assert rsc == RC.created, 'cannot create ACP'
		cls.acpRI = findXPath(cls.acp, 'm2m:acp/ri')

		# Add acpi to second AE 
		dct = 	{ 'm2m:ae' : {
					'acpi' : [ cls.acpRI ]
				}}
		cls.ae, rsc = UPDATE(aeURL, cls.originator, dct)
		assert rsc == RC.updated, 'cannot update AE'


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(ae2URL, ORIGINATOR)	# Just delete the 2nd AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createPCHwithWrongOriginatorFail(self) -> None:
		"""	Create <PCH> with valid but different originator -> Fail"""
		self.assertIsNotNone(TestPCH.ae)
		dct = 	{ 'm2m:pch' : { 
					'rn' : pchRN,
				}}
		r, rsc = CREATE(aeURL, ORIGINATOR, T.PCH, dct)	# Admin, should still fail
		self.assertEqual(rsc, RC.originatorHasNoPrivilege, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createPCH(self) -> None:
		"""	Create <PCH>"""
		self.assertIsNotNone(TestPCH.ae)
		dct = 	{ 'm2m:pch' : { 
					'rn' : pchRN,
				}}
		r, rsc = CREATE(aeURL, TestPCH.originator, T.PCH, dct)
		self.assertEqual(rsc, RC.created, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSecondPCHFail(self) -> None:
		"""	Create second <PCH> (but only one is allowed) -> Fail"""
		self.assertIsNotNone(TestPCH.ae)
		dct = 	{ 'm2m:pch' : { 
					'rn' : f'{pchRN}2',
				}}
		_, rsc = CREATE(aeURL, TestPCH.originator, T.PCH, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createPCHunderCSEBaseFail(self) -> None:
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
		r, rsc = RETRIEVE(pchURL, TestPCH.originator)
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrievePCHwithWrongOriginatorFail(self) -> None:
		""" Retrieve <PCH> with wrong originator -> Fail"""
		_, rsc = RETRIEVE(pchURL, 'wrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrievePCHWithAE2Fail(self) -> None:
		""" Retrieve <PCH> with <AE> 2 -> Fail """
		r, rsc = RETRIEVE(pchURL, TestPCH.originator2)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege, r)


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
	def test_setAggreagstionState(self) -> None:
		"""	Set <PCH> pcra attribute"""
		dct = 	{ 'm2m:pch' : { 
					'pcra' : True,
				}}
		r, rsc = UPDATE(pchURL, TestPCH.originator, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertEqual(findXPath(r, 'm2m:pch/pcra'), True)

	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_getAggreagstionState(self) -> None:
		"""	Get <PCH> pcra attribute"""
		r, rsc = RETRIEVE(pchURL, TestPCH.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:pch/pcra'), True)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deletePCHwrongOriginatorFail(self) -> None:
		""" Delete <PCH> with wrong originator -> Fail """
		_, rsc = DELETE(pchURL, 'wrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deletePCH(self) -> None:
		""" Delete <PCH> with correct originator """
		_, rsc = DELETE(pchURL, self.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrievePCUAfterDeleteFail(self) -> None:
		""" Retrieve <PCU> after delete -> Fail """
		_, rsc = RETRIEVE(pcuURL, self.originator)
		self.assertEqual(rsc, RC.notFound)



def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()

	# basic tests
	suite.addTest(TestPCH('test_createPCHwithWrongOriginatorFail'))
	suite.addTest(TestPCH('test_createPCH'))
	suite.addTest(TestPCH('test_createSecondPCHFail'))
	suite.addTest(TestPCH('test_createPCHunderCSEBaseFail'))
	suite.addTest(TestPCH('test_retrievePCH'))
	suite.addTest(TestPCH('test_retrievePCHwithWrongOriginatorFail'))
	suite.addTest(TestPCH('test_retrievePCHWithAE2Fail'))
	suite.addTest(TestPCH('test_attributesPCH'))

	suite.addTest(TestPCH('test_setAggreagstionState'))
	suite.addTest(TestPCH('test_getAggreagstionState'))

	# delete tests
	suite.addTest(TestPCH('test_deletePCHwrongOriginatorFail'))
	suite.addTest(TestPCH('test_deletePCH'))

	suite.addTest(TestPCH('test_retrievePCUAfterDeleteFail'))


	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)

