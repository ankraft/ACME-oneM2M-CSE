#
#	testACP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for ACP functionality
#

import unittest, sys
sys.path.append('../acme')
from typing import Tuple
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from init import *


class TestACP(unittest.TestCase):

	acpORIGINATOR 	= 'CtestOriginator'
	acpORIGINATOR2 	= 'CtestOriginator2'
	acpORIGINATOR3 	= 'CtestOriginator3'

	ae 				= None
	originator 		= None
	acp 			= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		pass


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(acpURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACP(self) -> None:
		"""	Create <ACP> """
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ { 	"acor": [ self.acpORIGINATOR, self.acpORIGINATOR2, self.acpORIGINATOR3 ],
									"acop": 63
								} ]
					},
					"pvs": { 
						"acr": [ {
							"acor": [ self.acpORIGINATOR, self.acpORIGINATOR2 ],
							"acop": 63
						} ]
					},
				}}
		TestACP.acp, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, dct)
		self.assertEqual(rsc, RC.created)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveACP(self) -> None:
		"""	Retrieve <ACP> """
		_, rsc = RETRIEVE(acpURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveACPwrongOriginator(self) -> None:
		"""	Retrieve <ACP> with wrong originator """
		_, rsc = RETRIEVE(acpURL, 'wrongoriginator')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesACP(self) -> None:
		"""	Test <ACP>'s attributes """
		r, rsc = RETRIEVE(acpURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:acp/ty'), T.ACP)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/et'))
		self.assertLessEqual(findXPath(r, 'm2m:acp/ct'), findXPath(r, 'm2m:acp/lt'))
		self.assertLess(findXPath(r, 'm2m:acp/ct'), findXPath(r, 'm2m:acp/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv'), dict)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr'), list)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}'), dict)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acor'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}/acor'), list)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acor/{0}'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}/acor/{0}'), str)
		self.assertEqual(findXPath(r, 'm2m:acp/pv/acr/{0}/acor'), [ self.acpORIGINATOR, self.acpORIGINATOR2, self.acpORIGINATOR3 ])
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'), int)
		self.assertEqual(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'), 63)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs'), dict)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs/acr'), list)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor'), list)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor/{0}'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor/{0}'), str)
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor/{0}'), self.acpORIGINATOR)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'), int)
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'), 63)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACP(self) -> None:
		"""	Update <ACP> """
		dct = 	{ 'm2m:acp' : {
					'lbl' : [ 'aTag' ]
				}}
		acp, rsc = UPDATE(acpURL, self.acpORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(findXPath(acp, 'm2m:acp/lbl'))
		self.assertEqual(len(findXPath(acp, 'm2m:acp/lbl')), 1)
		self.assertIn('aTag', findXPath(acp, 'm2m:acp/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACPwrongOriginator(self) -> None:
		"""	Update <ACP> with wrong originator """
		dct = 	{ 'm2m:acp' : {
					'lbl' : [ 'bTag' ]
				}}
		r, rsc = UPDATE(acpURL, 'wrong', dct)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addACPtoAE(self) -> None:
		"""	Reference <ACP> in a new <AE> """
		self.assertIsNotNone(TestACP.acp)
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ],
				 	'acpi': [ findXPath(TestACP.acp, 'm2m:acp/ri') ]
				}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(TestACP.ae, 'm2m:ae/acpi'))
		self.assertIsInstance(findXPath(TestACP.ae, 'm2m:ae/acpi'), list)
		self.assertGreater(len(findXPath(TestACP.ae, 'm2m:ae/acpi')), 0)
		self.assertIn(findXPath(TestACP.acp, 'm2m:acp/ri'), findXPath(TestACP.ae, 'm2m:ae/acpi'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEACPIWrong(self) -> None:
		"""	Update <AE> ACPI together with second attribute -> Fail """
		dct =	{ 'm2m:ae': {
					'lbl' : [ 'a' ],
					'acpi': [ 'anID' ]
				}}
		_, rsc = UPDATE(aeURL, self.acpORIGINATOR, dct)
		self.assertNotEqual(rsc, RC.updated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEACPIWrong2(self) -> None:
		"""	Update <AE> ACPI with reference to non-existing <ACP> -> Fail """
		dct =	{ 'm2m:ae': {
					'acpi': [ 'anID' ]
				}}
		r, rsc = UPDATE(aeURL, self.acpORIGINATOR, dct)
		self.assertNotEqual(rsc, RC.updated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEACPIWrongOriginator(self) -> None:
		"""	Update <AE> ACPI with third not allowed Originator -> Fail """
		dct =	{ 'm2m:ae': {
					'acpi': [ findXPath(TestACP.acp, 'm2m:acp/ri') ]
				}}
		r, rsc = UPDATE(aeURL, self.acpORIGINATOR3, dct)
		self.assertNotEqual(rsc, RC.updated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEACPIOtherOriginator(self) -> None:
		"""	Update <AE> ACPI with second allowed originator"""
		dct =	{ 'm2m:ae': {
					'acpi': [ findXPath(TestACP.acp, 'm2m:acp/ri') ]
				}}
		r, rsc = UPDATE(aeURL, self.acpORIGINATOR2, dct)
		self.assertEqual(rsc, RC.updated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACPEmptyPVS(self) -> None:
		"""	Update <ACP> with empty PVS -> Fail """
		dct = 	{ 'm2m:acp' : {	# type: ignore
					'pvs' : {}
				}}
		acp, rsc = UPDATE(acpURL, self.acpORIGINATOR, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACPNoPVS(self) -> None:
		"""	Update <ACP> with None PVS -> Fail """
		dct = 	{ 'm2m:acp' : {
					'pvs' : None
				}}
		_, rsc = UPDATE(acpURL, self.acpORIGINATOR, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPNoPVS(self) -> None:
		"""	Create <ACP> with no PVS -> Fail """
		dct = 	{ "m2m:acp": {
					"rn": f'{acpRN}2',
					"pv": {
						"acr": [ { 	"acor": [ ORIGINATOR ],
									"acop": 63
								} ]
					}
				}}
		_, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPEmptyPVS(self) -> None:
		"""	Create <ACP> with empty PVS -> Fail """
		dct = 	{ "m2m:acp": {
					"rn": f'{acpRN}2',
					"pv": {
						"acr": [ { 	"acor": [ ORIGINATOR ],
									"acop": 63
								} ]
					},
					"pvs": {},
				}}
		_, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, dct)
		self.assertEqual(rsc, RC.badRequest)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithNoACPI(self) -> None:
		"""	Create <CNT> without ACPI """
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNone(findXPath(r, 'm2m:ae/acpi')) # no ACPI?


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTwithNoACPI(self) -> None:
		"""	Retrieve <CNT> without ACPI """
		_, rsc = RETRIEVE(cntURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTwithNoACPIWrongOriginator(self) -> None:
		"""	Retrieve <CNT> without ACPI and wrong originator -> Fail """
		_, rsc = RETRIEVE(cntURL, 'wrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTwithNoACPI(self) -> None:
		"""	Delete <CNT> without ACPI """
		_, rsc = DELETE(cntURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithNoACPIAndHolder(self) -> None:
		"""	Create <CNT> without ACPI / with holder """
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'hld': 'someone'
				}}
		r, rsc = CREATE(aeURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNone(findXPath(r, 'm2m:ae/acpi')) # no ACPI?


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTwithNoACPIAndHolder(self) -> None:
		"""	Retrieve <CNT> without ACPI / with holder and holder """
		_, rsc = RETRIEVE(cntURL, 'someone')
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTwithNoACPIAndHolderAEOriginator(self) -> None:
		"""	Retrieve <CNT> without ACPI / with holder and AE originator -> Fail """
		_, rsc = RETRIEVE(cntURL, TestACP.originator)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTwithNoACPIAndHolderWrongOriginator(self) -> None:
		"""	Retrieve <CNT> without ACPI / with holder and wrong originator -> Fail """
		_, rsc = RETRIEVE(cntURL, 'wrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTwithNoACPIAndHolder(self) -> None:
		"""	Delete <CNT> without ACPI / with holder and holder """
		_, rsc = DELETE(cntURL, "someone")
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_removeACPfromAE(self) -> None:
		""" Remove <ACP> reference from <AE> / ACPI only attribute in update """
		self.assertIsNotNone(TestACP.acp)
		self.assertIsNotNone(TestACP.ae)
		acpi = findXPath(TestACP.ae, 'm2m:ae/acpi').copy()
		acpi.remove(findXPath(TestACP.acp, 'm2m:acp/ri'))
		dct = 	{ 'm2m:ae' : {
			 		'acpi': acpi
				}}
		r, rsc = UPDATE(aeURL, findXPath(TestACP.ae, 'm2m:ae/aei'), dct)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)	# missing self-privileges
		_, rsc = UPDATE(aeURL, self.acpORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACPwrongOriginator(self) -> None:
		""" Delete <ACP> with wrong originator -> Fail """
		_, rsc = DELETE(acpURL, 'wrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACP(self) -> None:
		""" Delete <ACP> with correct originator """
		_, rsc = DELETE(acpURL, self.acpORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


# TODO reference a non-acp resource in acpi



def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestACP('test_createACP'))
	suite.addTest(TestACP('test_retrieveACP'))
	suite.addTest(TestACP('test_retrieveACPwrongOriginator'))
	suite.addTest(TestACP('test_attributesACP'))
	suite.addTest(TestACP('test_updateACP'))
	suite.addTest(TestACP('test_updateACPwrongOriginator'))
	suite.addTest(TestACP('test_updateACPEmptyPVS'))
	suite.addTest(TestACP('test_updateACPNoPVS'))
	suite.addTest(TestACP('test_addACPtoAE'))
	suite.addTest(TestACP('test_updateAEACPIWrong'))
	suite.addTest(TestACP('test_updateAEACPIWrong2'))
	suite.addTest(TestACP('test_updateAEACPIWrongOriginator'))
	suite.addTest(TestACP('test_updateAEACPIOtherOriginator'))

	suite.addTest(TestACP('test_createACPNoPVS'))
	suite.addTest(TestACP('test_createACPEmptyPVS'))

	suite.addTest(TestACP('test_createCNTwithNoACPI'))
	suite.addTest(TestACP('test_retrieveCNTwithNoACPI'))
	suite.addTest(TestACP('test_retrieveCNTwithNoACPIWrongOriginator'))
	suite.addTest(TestACP('test_deleteCNTwithNoACPI'))

	suite.addTest(TestACP('test_createCNTwithNoACPIAndHolder'))
	suite.addTest(TestACP('test_retrieveCNTwithNoACPIAndHolder'))
	suite.addTest(TestACP('test_retrieveCNTwithNoACPIAndHolderAEOriginator'))
	suite.addTest(TestACP('test_retrieveCNTwithNoACPIAndHolderWrongOriginator'))
	suite.addTest(TestACP('test_deleteCNTwithNoACPIAndHolder'))

	suite.addTest(TestACP('test_removeACPfromAE'))
	suite.addTest(TestACP('test_deleteACPwrongOriginator'))
	suite.addTest(TestACP('test_deleteACP'))

	#suite.addTest(TestACP('test_handleAE'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
