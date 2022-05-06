#
#	testAE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for AE functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *


class TestAE(unittest.TestCase):

	cse 		= None
	ae 			= None
	originator 	= None
	originator2	= None
	aeACPI 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		cls.originator 	= None 	# actually the AE.aei
		cls.aeACPI 		= None
		cls.cse, rsc 	= RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}'


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAE(self) -> None:
		""" Create/register an <AE> """
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.created, r)
		TestAE.originator = findXPath(r, 'm2m:ae/aei')
		TestAE.aeACPI = findXPath(r, 'm2m:ae/acpi')
		self.assertIsNotNone(TestAE.originator, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEUnderAE(self) -> None:
		""" Create/register an <AE> under an <AE> -> Fail """
		dct = 	{ 'm2m:ae' : {
					'rn': f'{aeRN}', 
					'api': 'NMyApp2Id',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		r, rsc = CREATE(aeURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.invalidChildResourceType, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEAgain(self) -> None:
		""" Create/register an <AE> with same rn again -> Fail """
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.conflict)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEWithExistingOriginator(self) -> None:
		""" Create/register an <AE> with same originator again -> Fail """
		dct = 	{ 'm2m:ae' : {
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		r, rsc = CREATE(cseURL, TestAE.originator, T.AE, dct)
		self.assertEqual(rsc, RC.originatorHasAlreadyRegistered)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveAE(self) -> None:
		""" Retrieve <AE> """
		r, rsc = RETRIEVE(aeURL, TestAE.originator)
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveAEWithWrongOriginator(self) -> None:
		""" Retrieve <AE> with wrong originator -> Fail """
		_, rsc = RETRIEVE(aeURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesAE(self) -> None:
		""" Retrieve <AE> and check attributes """
		r, rsc = RETRIEVE(aeURL, TestAE.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/aei'))
		self.assertEqual(findXPath(r, 'm2m:ae/ty'), T.AE)
		self.assertTrue(findXPath(r, 'm2m:ae/aei').startswith('C'))
		self.assertEqual(findXPath(r, 'm2m:ae/api'), 'NMyApp1Id')
		self.assertIsNotNone(findXPath(r, 'm2m:ae/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/et'))
		self.assertLessEqual(findXPath(r, 'm2m:ae/ct'), findXPath(r, 'm2m:ae/lt'))
		self.assertLess(findXPath(r, 'm2m:ae/ct'), findXPath(r, 'm2m:ae/et'))
		self.assertEqual(findXPath(r, 'm2m:ae/rr'), False)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/srv'))
		self.assertEqual(findXPath(r, 'm2m:ae/srv'), [ '3' ])
		self.assertIsNone(findXPath(r, 'm2m:ae/st'))
		self.assertEqual(findXPath(r, 'm2m:ae/pi'), findXPath(TestAE.cse,'m2m:cb/ri'))
		#self.assertIsNotNone(findXPath(r, 'm2m:ae/acpi'))
		#self.assertIsInstance(findXPath(r, 'm2m:ae/acpi'), list)
		#self.assertGreater(len(findXPath(r, 'm2m:ae/acpi')), 0)
		self.assertIsNone(findXPath(r, 'm2m:ae/st'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAELbl(self) -> None:
		""" Update <AE> with lbl """
		dct = 	{ 'm2m:ae' : {
					'lbl' : [ 'aTag' ]
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, dct)
		self.assertEqual(rsc, RC.updated)
		r, rsc = RETRIEVE(aeURL, TestAE.originator)		# retrieve updated ae again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lbl'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/lbl'), list)
		self.assertGreater(len(findXPath(r, 'm2m:ae/lbl')), 0)
		self.assertTrue('aTag' in findXPath(r, 'm2m:ae/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAETy(self) -> None:
		""" Update <AE> with ty=CSEBase -> Fail """
		dct = 	{ 'm2m:ae' : {
					'ty' : int(T.CSEBase)
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEPi(self) -> None:
		""" Update <AE> with pi=wrong -> Fail """
		dct = 	{ 'm2m:ae' : {
					'pi' : 'wrongID'
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEUnknownAttribute(self) -> None:
		""" Update <AE> with unknown attribute -> Fail """
		dct = 	{ 'm2m:ae' : {
					'unknown' : 'unknown'
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEByUnknownOriginator(self) -> None:
		""" Delete <AE> with wrong originator -> Fail """
		_, rsc = DELETE(aeURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEByAssignedOriginator(self) -> None:
		""" Delete <AE> with correct originator -> <AE> deleted """
		_, rsc = DELETE(aeURL, TestAE.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEWrongCSZ(self) -> None:
		""" Create <AE> with wrong csz content -> Fail """
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ],
					'csz': [ 'wrong' ]
				}}
		_, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAECSZ(self) -> None:
		""" Create <AE> with correct csz value"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ],
					'csz': [ 'application/cbor', 'application/json' ]
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.created)
		TestAE.originator2 = findXPath(r, 'm2m:ae/aei')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAECSZ(self) -> None:
		""" Delete <AE> with csr -> <AE> deleted """
		_, rsc = DELETE(aeURL, TestAE.originator2)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAENoAPI(self) -> None:
		""" Create <AE> with missing api attribute -> Fail"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		_, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertNotEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEAPIWrongPrefix(self) -> None:
		""" Create <AE> with unknown api prefix -> Fail"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'Xwrong',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		_, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertNotEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEAPICorrectR(self) -> None:
		""" Create <AE> with correct api value (Registered)"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'Rabc.com.example.acme',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/aei'))
		_, rsc = DELETE(aeURL, findXPath(ae, 'm2m:ae/aei'))
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEAPICorrectN(self) -> None:
		""" Create <AE> with correct api value (Non-Registered)"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'Nacme',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/aei'))
		_, rsc = DELETE(aeURL, findXPath(ae, 'm2m:ae/aei'))
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAENoOriginator(self) -> None:
		""" Create <AE> without an Originator"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'Nacme',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		ae, rsc = CREATE(cseURL, None, T.AE, dct)
		self.assertEqual(rsc, RC.created, ae)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/aei'))
		_, rsc = DELETE(aeURL, findXPath(ae, 'm2m:ae/aei'))
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEEmptyOriginator(self) -> None:
		""" Create <AE> with an empty Originator"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'Nacme',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		ae, rsc = CREATE(cseURL, '', T.AE, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/aei'))
		_, rsc = DELETE(aeURL, findXPath(ae, 'm2m:ae/aei'))
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEInvalidRNFail(self) -> None:
		""" Create <AE> with an invalid rn -> Fail"""
		dct = 	{ 'm2m:ae' : {
					'rn': 'test?',	# not from unreserved character
					'api': 'Nacme',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		ae, rsc = CREATE(cseURL, '', T.AE, dct)
		self.assertEqual(rsc, RC.contentsUnacceptable)


# TODO register multiple AEs

def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestAE('test_createAE'))
	suite.addTest(TestAE('test_createAEUnderAE'))
	suite.addTest(TestAE('test_createAEAgain'))
	suite.addTest(TestAE('test_createAEWithExistingOriginator'))
	suite.addTest(TestAE('test_retrieveAE'))
	suite.addTest(TestAE('test_retrieveAEWithWrongOriginator'))
	suite.addTest(TestAE('test_attributesAE'))
	suite.addTest(TestAE('test_updateAELbl'))
	suite.addTest(TestAE('test_updateAETy'))
	suite.addTest(TestAE('test_updateAEPi'))
	suite.addTest(TestAE('test_updateAEUnknownAttribute'))
	suite.addTest(TestAE('test_deleteAEByUnknownOriginator'))
	suite.addTest(TestAE('test_deleteAEByAssignedOriginator'))
	suite.addTest(TestAE('test_createAEWrongCSZ'))
	suite.addTest(TestAE('test_createAECSZ'))	
	suite.addTest(TestAE('test_deleteAECSZ'))	
	suite.addTest(TestAE('test_createAENoAPI'))	
	suite.addTest(TestAE('test_createAEAPIWrongPrefix'))	
	suite.addTest(TestAE('test_createAEAPICorrectR'))	
	suite.addTest(TestAE('test_createAEAPICorrectN'))	
	suite.addTest(TestAE('test_createAENoOriginator'))	
	suite.addTest(TestAE('test_createAEEmptyOriginator'))	
	suite.addTest(TestAE('test_createAEInvalidRNFail'))	
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
