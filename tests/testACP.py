#
#	testACP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for ACP functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import Permission, ResourceTypes as T, ResponseStatusCode as RC
from init import *

ae1RN  = f'{aeRN}1'
ae1URL = f'{cseURL}/{ae1RN}'
ae2RN = f'{aeRN}2'
ae2URL = f'{cseURL}/{ae2RN}'
cnt2URL = f'{ae2URL}/{cntRN}'


class TestACP(unittest.TestCase):

	acpORIGINATOR 			= 'CtestOriginator'
	acpORIGINATOR2 			= 'CtestOriginator2'
	acpORIGINATOR3 			= 'CtestOriginator3'
	acpORIGINATORWC 		= 'Canother*'
	acpORIGINATORWC2		= 'Cyet*Originator'
	
	# Originators for wildcard tests
	acpORIGINATORWCTest 	= 'CanotherOriginator'
	acpORIGINATORWC2Test 	= 'CyetAnotherOriginator'
	acpORIGINATORWC3Test 	= 'CyetAnother'	

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
		DELETE(ae1URL, ORIGINATOR)
		DELETE(ae2URL, ORIGINATOR)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACP(self) -> None:
		"""	Create <ACP> """
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ { 	"acor": [ self.acpORIGINATOR, self.acpORIGINATOR2, self.acpORIGINATOR3, self.acpORIGINATORWC, self.acpORIGINATORWC2 ],
									"acop": Permission.ALL
								} ]
					},
					"pvs": { 
						"acr": [ {
							"acor": [ self.acpORIGINATOR, self.acpORIGINATOR2 ],
							"acop": Permission.ALL
						} ]
					},
				}}
		TestACP.acp, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, dct)
		self.assertEqual(rsc, RC.created, TestACP.acp)
	

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
		self.assertEqual(findXPath(r, 'm2m:acp/pv/acr/{0}/acor'), [ self.acpORIGINATOR, self.acpORIGINATOR2, self.acpORIGINATOR3, self.acpORIGINATORWC, self.acpORIGINATORWC2 ])
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'), int)
		self.assertEqual(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'), Permission.ALL)
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
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'), Permission.ALL)


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
	def test_updateAElblWithWildCardOriginator(self) -> None:
		"""	Update <AE> LBL with wildcard Originator """
		dct =	{ 'm2m:ae': {
					'lbl': [ '1Label' ]
				}}
		r, rsc = UPDATE(aeURL, self.acpORIGINATORWCTest, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lbl'), r)
		self.assertEqual(len(findXPath(r, 'm2m:ae/lbl')), 1, r)
		self.assertIn('1Label', findXPath(r, 'm2m:ae/lbl'), 4)

	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAElblWithWildCardOriginator2(self) -> None:
		"""	Update <AE> LBL with wildcard Originator 2"""
		dct =	{ 'm2m:ae': {
					'lbl': [ '2Label' ]
				}}
		r, rsc = UPDATE(aeURL, self.acpORIGINATORWC2Test, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lbl'), r)
		self.assertEqual(len(findXPath(r, 'm2m:ae/lbl')), 1, r)
		self.assertIn('2Label', findXPath(r, 'm2m:ae/lbl'), 4)

	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAElblWithWildCardOriginator3WrongFail(self) -> None:
		"""	Update <AE> LBL with wrong wildcard Originator 3 -> Fail"""
		dct =	{ 'm2m:ae': {
					'lbl': [ '3Label' ]
				}}
		r, rsc = UPDATE(aeURL, self.acpORIGINATORWC3Test, dct)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACPEmptyPVSFail(self) -> None:
		"""	Update <ACP> with empty PVS -> Fail """
		dct = 	{ 'm2m:acp' : {	# type: ignore
					'pvs' : {}
				}}
		acp, rsc = UPDATE(acpURL, self.acpORIGINATOR, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACPNoPVSFail(self) -> None:
		"""	Update <ACP> with None PVS -> Fail """
		dct = 	{ 'm2m:acp' : {
					'pvs' : None
				}}
		_, rsc = UPDATE(acpURL, self.acpORIGINATOR, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPNoPVSFail(self) -> None:
		"""	Create <ACP> with no PVS -> Fail """
		dct = 	{ "m2m:acp": {
					"rn": f'{acpRN}2',
					"pv": {
						"acr": [ { 	"acor": [ ORIGINATOR ],
									"acop": Permission.ALL
								} ]
					}
				}}
		_, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPEmptyPVSFail(self) -> None:
		"""	Create <ACP> with empty PVS -> Fail """
		dct = 	{ "m2m:acp": {
					"rn": f'{acpRN}2',
					"pv": {
						"acr": [ { 	"acor": [ ORIGINATOR ],
									"acop": Permission.ALL
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
	def test_createCNTwithNoACPIAndCustodian(self) -> None:
		"""	Create <CNT> without ACPI / with custodian """
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'cstn': 'someone'
				}}
		r, rsc = CREATE(aeURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNone(findXPath(r, 'm2m:ae/acpi')) # no ACPI?


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTwithNoACPIAndCustodian(self) -> None:
		"""	Retrieve <CNT> without ACPI / with custodian """
		_, rsc = RETRIEVE(cntURL, 'someone')
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTwithNoACPIAndCustodianAEOriginator(self) -> None:
		"""	Retrieve <CNT> without ACPI / with custodian and AE originator -> Fail """
		_, rsc = RETRIEVE(cntURL, TestACP.originator)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTwithNoACPIAndCustodianWrongOriginator(self) -> None:
		"""	Retrieve <CNT> without ACPI / with custodian and wrong originator -> Fail """
		_, rsc = RETRIEVE(cntURL, 'wrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTwithNoACPIAndCustodian(self) -> None:
		"""	Delete <CNT> without ACPI / with custodian"""
		_, rsc = DELETE(cntURL, "someone")
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_removeACPfromAEWrong(self) -> None:
		""" Remove <ACP> reference from <AE> / ACPI only attribute in update / empty list -> Fail"""
		self.assertIsNotNone(TestACP.acp)
		self.assertIsNotNone(TestACP.ae)
		acpi = findXPath(TestACP.ae, 'm2m:ae/acpi').copy()
		acpi.remove(findXPath(TestACP.acp, 'm2m:acp/ri'))
		dct = 	{ 'm2m:ae' : {
			 		'acpi': acpi
				}}
		_, rsc = UPDATE(aeURL, self.acpORIGINATOR, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_removeACPfromAEWrong2(self) -> None:
		""" Remove <ACP> reference from <AE> / ACPI only attribute in update / missing pvs -> Fail """
		self.assertIsNotNone(TestACP.acp)
		self.assertIsNotNone(TestACP.ae)
		acpi = findXPath(TestACP.ae, 'm2m:ae/acpi').copy()
		acpi.remove(findXPath(TestACP.acp, 'm2m:acp/ri'))
		dct = 	{ 'm2m:ae' : {
			 		'acpi': None
				}}
		r, rsc = UPDATE(aeURL, findXPath(TestACP.ae, 'm2m:ae/aei'), dct)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)	# missing self-privileges


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_removeACPfromAE(self) -> None:
		""" Remove <ACP> reference from <AE> / ACPI only attribute in update """
		self.assertIsNotNone(TestACP.acp)
		self.assertIsNotNone(TestACP.ae)
		acpi = findXPath(TestACP.ae, 'm2m:ae/acpi').copy()
		acpi.remove(findXPath(TestACP.acp, 'm2m:acp/ri'))
		dct = 	{ 'm2m:ae' : {
			 		'acpi': None
				}}
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


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPUnderCSEBaseWithOriginator(self) -> None:
		"""	Create <ACP> under CSEBase with AE originator """
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": []
					},
					"pvs": { 
						"acr": [ {
							"acor": [ TestACP.originator ],
							"acop": Permission.ALL
						} ]
					},
				}}
		TestACP.acp, rsc = CREATE(cseURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.created, TestACP.acp)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACPUnderCSEBaseWithOriginator(self) -> None:
		""" Delete <ACP> under CSEBase with AE originator """
		_, rsc = DELETE(acpURL, TestACP.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPUnderAEWithChty(self) -> None:
		"""	Create <ACP> under AE with AE originator and chty """
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ {
							"acor": [ TestACP.originator ],
							"acop": Permission.CREATE,
							"acod": [ {
								"chty": [ T.CNT ]	# Allow only a CNT to be created
							} ]
						}]
					},
					"pvs": { 
						"acr": [ {
							"acor": [ TestACP.originator ],
							"acop": Permission.ALL
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.created, r)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acod'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acod/{0}/chty'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}/acod/{0}/chty'), list)
		self.assertTrue(T.CNT in findXPath(r, 'm2m:acp/pv/acr/{0}/acod/{0}/chty'))
		TestACP.acp = r


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEACPIForChty(self) -> None:
		"""	Update <AE> ACPI with ACP with chty """
		dct =	{ 'm2m:ae': {
					'acpi': [ findXPath(TestACP.acp, 'm2m:acp/ri') ]
				}}
		r, rsc = UPDATE(aeURL, TestACP.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/acpi'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testACPChty(self) -> None:
		"""	Create resources under AE, allowed and not allowed by chty """

		# Try CNT first -> OK
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)

		# Try FCNT next -> Fail
		dct2 = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: 'org.onem2m.home.moduleclass.temperature', 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.FCNT, dct2)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACPUnderAEWithChty(self) -> None:
		""" Delete <ACP> under AE for chty  """
		_, rsc = DELETE(f'{aeURL}/{acpRN}', TestACP.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_accessCINwithDifferentAENoAcpi(self) -> None:
		""" Access CIN with different <AE> and no acpi -> Fail"""

		#	CSEBase                             
		#    ├─ae1                       
		#    │  └─testCNT                 
		#    └─ae2                      
		#       └─acp   
		#       └─cnt   
		#          └─cin

		# Create AE1
		dct = 	{ 'm2m:ae' : {
					'rn': ae1RN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ],
				}}
		ae1, rsc = CREATE(cseURL, 'Cae1', T.AE, dct)
		self.assertEqual(rsc, RC.created, ae1)

		# Create AE2
		dct = 	{ 'm2m:ae' : {
					'rn': ae2RN, 
					'api': 'NMyApp2Id',
				 	'rr': False,
				 	'srv': [ '3' ],
				}}
		ae2, rsc = CREATE(cseURL, 'Cae2', T.AE, dct)
		self.assertEqual(rsc, RC.created, ae2)

		# Create ACP under AE2
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ {
							"acor": [ 'Cae2', 'Cae1' ],
							"acop": Permission.ALL,
						}]
					},
					"pvs": { 
						"acr": [ {
							"acor": ['Cae2' ],
							"acop": Permission.ALL
						} ]
					},
				}}
		acp, rsc = CREATE(ae2URL, 'Cae2', T.ACP, dct)
		self.assertEqual(rsc, RC.created, acp)

		# Create CNT under AE2
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
				}}
		cnt, rsc = CREATE(ae2URL, 'Cae2', T.CNT, dct)
		self.assertEqual(rsc, RC.created, cnt)

		# Add CIN
		dct = 	{ 'm2m:cin' : {
					'con' : 'content'
				}}
		r, rsc = CREATE(cnt2URL, 'Cae2', T.CIN, dct)
		self.assertEqual(rsc, RC.created, r)

		# Retrieve CIN by AE1
		r, rsc = RETRIEVE(f'{cnt2URL}/la', 'Cae1')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_accessCINwithDifferentAEWithAcpi(self) -> None:
		""" Access CIN with different <AE> and with acpi"""

		# Add acpi to CNT
		dct = 	{ 'm2m:cnt' : {
					'acpi': [ f'{CSERN}/{ae2RN}/{acpRN}' ]
				}}
		cnt, rsc = UPDATE(cnt2URL, 'Cae2', dct)
		self.assertEqual(rsc, RC.updated, cnt)

		# Retrieve CIN by AE1
		r, rsc = RETRIEVE(f'{cnt2URL}/la', 'Cae1')
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCINwithDifferentAEWithAcpi(self) -> None:
		""" Discover CIN with different <AE> and with acpi"""

		# Retrieve CIN by AE1
		r, rsc = RETRIEVE(f'{cnt2URL}?fu=1&ty=4', 'Cae1')
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:uril'), r)
		self.assertEqual(len(findXPath(r, 'm2m:uril')), 1, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveACPwithoutRETRIEVEAccessFail(self) -> None:
		"""	Retrieve an ACP without RETRIEVE access in PVS -> Fail """
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {	},
					"pvs": { 
						"acr": [ {
							"acor": [ TestACP.originator ],
							"acop": Permission.allExcept(Permission.RETRIEVE)
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor'))
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor/{0}'), TestACP.originator)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'))
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'), 61) # no RETRIEVE

		# Retrieve the ACP by the originator
		r, rsc = RETRIEVE(f'{aeURL}/{acpRN}', TestACP.originator)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege, r)





# TODO reference a non-acp resource in acpi
# TODO acod/specialization



def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestACP('test_createACP'))
	suite.addTest(TestACP('test_retrieveACP'))
	suite.addTest(TestACP('test_retrieveACPwrongOriginator'))
	suite.addTest(TestACP('test_attributesACP'))
	suite.addTest(TestACP('test_updateACP'))
	suite.addTest(TestACP('test_updateACPwrongOriginator'))
	suite.addTest(TestACP('test_updateACPEmptyPVSFail'))
	suite.addTest(TestACP('test_updateACPNoPVSFail'))
	suite.addTest(TestACP('test_addACPtoAE'))
	suite.addTest(TestACP('test_updateAEACPIWrong'))
	suite.addTest(TestACP('test_updateAEACPIWrong2'))
	suite.addTest(TestACP('test_updateAEACPIWrongOriginator'))
	suite.addTest(TestACP('test_updateAEACPIOtherOriginator'))

	# wildcard tests
	suite.addTest(TestACP('test_updateAElblWithWildCardOriginator'))
	suite.addTest(TestACP('test_updateAElblWithWildCardOriginator2'))
	suite.addTest(TestACP('test_updateAElblWithWildCardOriginator3WrongFail'))

	suite.addTest(TestACP('test_createACPNoPVSFail'))
	suite.addTest(TestACP('test_createACPEmptyPVSFail'))

	suite.addTest(TestACP('test_createCNTwithNoACPI'))
	suite.addTest(TestACP('test_retrieveCNTwithNoACPI'))
	suite.addTest(TestACP('test_retrieveCNTwithNoACPIWrongOriginator'))
	suite.addTest(TestACP('test_deleteCNTwithNoACPI'))

	suite.addTest(TestACP('test_createCNTwithNoACPIAndCustodian'))
	suite.addTest(TestACP('test_retrieveCNTwithNoACPIAndCustodian'))
	suite.addTest(TestACP('test_retrieveCNTwithNoACPIAndCustodianAEOriginator'))
	suite.addTest(TestACP('test_retrieveCNTwithNoACPIAndCustodianWrongOriginator'))
	suite.addTest(TestACP('test_deleteCNTwithNoACPIAndCustodian'))

	suite.addTest(TestACP('test_removeACPfromAEWrong'))
	suite.addTest(TestACP('test_removeACPfromAEWrong2'))
	suite.addTest(TestACP('test_removeACPfromAE'))
	suite.addTest(TestACP('test_deleteACPwrongOriginator'))
	suite.addTest(TestACP('test_deleteACP'))

	suite.addTest(TestACP('test_createACPUnderCSEBaseWithOriginator'))
	suite.addTest(TestACP('test_deleteACPUnderCSEBaseWithOriginator'))

	suite.addTest(TestACP('test_createACPUnderAEWithChty'))
	suite.addTest(TestACP('test_updateAEACPIForChty'))
	suite.addTest(TestACP('test_testACPChty'))
	suite.addTest(TestACP('test_deleteACPUnderAEWithChty'))

	suite.addTest(TestACP('test_accessCINwithDifferentAENoAcpi'))
	suite.addTest(TestACP('test_accessCINwithDifferentAEWithAcpi'))
	suite.addTest(TestACP('test_discoverCINwithDifferentAEWithAcpi'))

	suite.addTest(TestACP('test_retrieveACPwithoutRETRIEVEAccessFail'))


	#suite.addTest(TestACP('test_handleAE'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
