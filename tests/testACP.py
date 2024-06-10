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
from acme.etc.Types import Permission, ResourceTypes as T, ResponseStatusCode as RC
from init import *

ae1RN  = f'{aeRN}1'
ae1URL = f'{cseURL}/{ae1RN}'
ae2RN = f'{aeRN}2'
ae2URL = f'{cseURL}/{ae2RN}'
cnt2URL = f'{ae2URL}/{cntRN}'
grp2URL = f'{cseURL}/{grpRN}'


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
	grp 			= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestACP')
		pass
		testCaseEnd('Setup TestACP')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestACP')
		DELETE(acpURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not
		DELETE(ae1URL, ORIGINATOR)
		DELETE(ae2URL, ORIGINATOR)
		DELETE(grp2URL, ORIGINATOR)
		DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)
		testCaseEnd('TearDown TestACP')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)

	
	def printTitle(self) -> None:
		print("=========")


	#########################################################################


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
		self.assertEqual(rsc, RC.CREATED, TestACP.acp)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveACP(self) -> None:
		"""	Retrieve <ACP> """
		_, rsc = RETRIEVE(acpURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveACPwrongOriginator(self) -> None:
		"""	Retrieve <ACP> with wrong originator """
		_, rsc = RETRIEVE(acpURL, 'wrongoriginator')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


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
		self.assertEqual(rsc, RC.UPDATED)
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
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addACPtoAE(self) -> None:
		"""	Reference <ACP> in a new <AE> """
		self.assertIsNotNone(TestACP.acp)
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ],
				 	'acpi': [ findXPath(TestACP.acp, 'm2m:acp/ri') ]
				}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')
		self.assertEqual(rsc, RC.CREATED)
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
		self.assertNotEqual(rsc, RC.UPDATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEACPIWrong2(self) -> None:
		"""	Update <AE> ACPI with reference to non-existing <ACP> -> Fail """
		dct =	{ 'm2m:ae': {
					'acpi': [ 'anID' ]
				}}
		r, rsc = UPDATE(aeURL, self.acpORIGINATOR, dct)
		self.assertNotEqual(rsc, RC.UPDATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEACPIWrongOriginator(self) -> None:
		"""	Update <AE> ACPI with third not allowed Originator -> Fail """
		dct =	{ 'm2m:ae': {
					'acpi': [ findXPath(TestACP.acp, 'm2m:acp/ri') ]
				}}
		r, rsc = UPDATE(aeURL, self.acpORIGINATOR3, dct)
		self.assertNotEqual(rsc, RC.UPDATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEACPIOtherOriginator(self) -> None:
		"""	Update <AE> ACPI with second allowed originator"""
		dct =	{ 'm2m:ae': {
					'acpi': [ findXPath(TestACP.acp, 'm2m:acp/ri') ]
				}}
		r, rsc = UPDATE(aeURL, self.acpORIGINATOR2, dct)
		self.assertEqual(rsc, RC.UPDATED)

	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAElblWithWildCardOriginator(self) -> None:
		"""	Update <AE> LBL with wildcard Originator """
		dct =	{ 'm2m:ae': {
					'lbl': [ '1Label' ]
				}}
		r, rsc = UPDATE(aeURL, self.acpORIGINATORWCTest, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
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
		self.assertEqual(rsc, RC.UPDATED)
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
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACPEmptyPVSFail(self) -> None:
		"""	Update <ACP> with empty PVS -> Fail """
		dct = 	{ 'm2m:acp' : {	# type: ignore
					'pvs' : {}
				}}
		acp, rsc = UPDATE(acpURL, self.acpORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACPNoPVSFail(self) -> None:
		"""	Update <ACP> with None PVS -> Fail """
		dct = 	{ 'm2m:acp' : {
					'pvs' : None
				}}
		_, rsc = UPDATE(acpURL, self.acpORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


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
		self.assertEqual(rsc, RC.BAD_REQUEST)


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
		self.assertEqual(rsc, RC.BAD_REQUEST)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithNoACPI(self) -> None:
		"""	Create <CNT> without ACPI """
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
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
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTwithNoACPI(self) -> None:
		"""	Delete <CNT> without ACPI """
		_, rsc = DELETE(cntURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithNoACPIAndCustodian(self) -> None:
		"""	Create <CNT> without ACPI / with custodian """
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN,
					'cstn': 'someone'
				}}
		r, rsc = CREATE(aeURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
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
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTwithNoACPIAndCustodianWrongOriginator(self) -> None:
		"""	Retrieve <CNT> without ACPI / with custodian and wrong originator -> Fail """
		_, rsc = RETRIEVE(cntURL, 'wrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTwithNoACPIAndCustodian(self) -> None:
		"""	Delete <CNT> without ACPI / with custodian"""
		_, rsc = DELETE(cntURL, "someone")
		self.assertEqual(rsc, RC.DELETED)


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
		self.assertEqual(rsc, RC.BAD_REQUEST)


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
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)	# missing self-privileges


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
		self.assertEqual(rsc, RC.UPDATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACPwrongOriginator(self) -> None:
		""" Delete <ACP> with wrong originator -> Fail """
		_, rsc = DELETE(acpURL, 'wrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACP(self) -> None:
		""" Delete <ACP> with correct originator """
		_, rsc = DELETE(acpURL, self.acpORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


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
		self.assertEqual(rsc, RC.CREATED, TestACP.acp)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACPUnderCSEBaseWithOriginator(self) -> None:
		""" Delete <ACP> under CSEBase with AE originator """
		_, rsc = DELETE(acpURL, TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


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
		self.assertEqual(rsc, RC.CREATED, r)
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
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/acpi'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testACPChty(self) -> None:
		"""	Create resources under AE, allowed and not allowed by chty """

		# Try CNT first -> OK
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)

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
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACPUnderAEWithChty(self) -> None:
		""" Delete <ACP> under AE for chty  """
		_, rsc = DELETE(f'{aeURL}/{acpRN}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


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
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ],
				}}
		ae1, rsc = CREATE(cseURL, 'Cae1', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED, ae1)

		# Create AE2
		dct = 	{ 'm2m:ae' : {
					'rn': ae2RN, 
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ],
				}}
		ae2, rsc = CREATE(cseURL, 'Cae2', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED, ae2)

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
		self.assertEqual(rsc, RC.CREATED, acp)

		# Create CNT under AE2
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
				}}
		cnt, rsc = CREATE(ae2URL, 'Cae2', T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, cnt)

		# Add CIN
		dct = 	{ 'm2m:cin' : {
					'con' : 'content'
				}}
		r, rsc = CREATE(cnt2URL, 'Cae2', T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve CIN by AE1
		r, rsc = RETRIEVE(f'{cnt2URL}/la', 'Cae1')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_accessCINwithDifferentAEWithAcpi(self) -> None:
		""" Access CIN with different <AE> and with acpi"""

		# Add acpi to CNT
		dct = 	{ 'm2m:cnt' : {
					'acpi': [ f'{CSERN}/{ae2RN}/{acpRN}' ]
				}}
		cnt, rsc = UPDATE(cnt2URL, 'Cae2', dct)
		self.assertEqual(rsc, RC.UPDATED, cnt)

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
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor'))
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor/{0}'), TestACP.originator)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'))
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'), 61) # no RETRIEVE

		# Retrieve the ACP by the originator
		r, rsc = RETRIEVE(f'{aeURL}/{acpRN}', TestACP.originator)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPWithWrongTyFail(self) -> None:
		"""	Create <ACP> AE originator and wrong acod.ty -> Fail"""
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ {
							"acor": [ TestACP.originator ],
							"acop": Permission.CREATE,
							"acod": [ {
								"ty": [ T.CIN ],	# acr is only for CIN. Wrong because not a list
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
		r, rsc = CREATE(cseURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPWithTy(self) -> None:
		"""	Create <ACP> AE originator and acod.ty"""
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ {
							"acor": [ TestACP.originator ],
							"acop": Permission.RETRIEVE + Permission.CREATE,
							"acod": [ {
								"ty": T.CNT,	# acr is only for CNT
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
		r, rsc = CREATE(cseURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acod'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acod/{0}/chty'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}/acod/{0}/chty'), list)
		self.assertTrue(T.CNT in findXPath(r, 'm2m:acp/pv/acr/{0}/acod/{0}/chty'))
		TestACP.acp = r

		# Just delete the CNT
		DELETE(cntURL, TestACP.originator)

		# Add a container with the acpi set to the ACP
		dct = { "m2m:cnt": { 
					"rn": cntRN,
					"acpi": [ findXPath(TestACP.acp, 'm2m:acp/ri') ]
			} }
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Try to create a CIN -> Fail
		dct = { "m2m:cin": { "con": "test" } }
		r, rsc = CREATE(cntURL, TestACP.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# try to retrieve the CNT -> Fail
		r, rsc = RETRIEVE(cntURL, TestACP.originator)
		self.assertEqual(rsc, RC.OK, r)


#
#	Test ACP with acor & Groups
#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testACPacorGRP(self) -> None:
		"""	Test when GRP is a member of ACP.acor"""

		#
		#	CSEBase                             
		#    ├─ae                       
		#    ├─grp                       
		#    ├─acp                       
		#    └─cnt                      

		DELETE(aeURL, ORIGINATOR)
		DELETE(acpURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		# grp with AE as member
		dct = 	{ 'm2m:grp' : { 
					'rn' : grpRN,
					'mt' : T.MIXED,
					'mnm': 1,
					'mid': [ findXPath(TestACP.ae, 'm2m:ae/ri') ]
				}}
		TestACP.grp, rsc = CREATE(cseURL, ORIGINATOR, T.GRP, dct)
		grpRi = findXPath(TestACP.grp, 'm2m:grp/ri')
		self.assertEqual(rsc, RC.CREATED)

		# ACP with pv/acr/acor to the grp
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ {
							"acor": [ grpRi ],
							"acop": Permission.RETRIEVE + Permission.CREATE,
						}]
					},
					"pvs": { 
						"acr": [ {
							"acor": [ TestACP.originator ],
							"acop": Permission.ALL
						} ]
					},
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# CNT with acpi to the ACP
		dct = 	{ "m2m:cnt": {
					"rn": cntRN,
					"acpi": [ acpRi ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create a CIN under the CNT with the AE as originator -> OK
		dct = 	{ "m2m:cin": {
					"con": "test"
				}}
		r, rsc = CREATE(f'{cseURL}/{cntRN}', TestACP.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create a CIN under the CNT with unknown originator -> Fail
		dct = 	{ "m2m:cin": {
					"con": "test"
				}}
		r, rsc = CREATE(f'{cseURL}/{cntRN}', 'wrong', T.CIN, dct)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# cleanup
		DELETE(aeURL, ORIGINATOR)
		DELETE(acpURL, ORIGINATOR)
		DELETE(grp2URL, ORIGINATOR)
		DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)

	
	#
	#	AccessControlAttributes
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACA(self) -> None:
		"""	Create an ACP with aca attribute"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.RETRIEVE,
							'aca': [ 'lbl' ]	# only grant RETRIEVE permission to the label
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acor'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/aca'))
		self.assertEqual(findXPath(r, 'm2m:acp/pv/acr/{0}/aca'), ['lbl'])

		# Delete the AE+ACP again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACPwithACA(self) -> None:
		"""	Update an ACP with aca attribute"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.RETRIEVE,
							'aca': [ 'lbl' ]	# only grant RETRIEVE permission to the label
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acor'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/aca'))
		self.assertEqual(findXPath(r, 'm2m:acp/pv/acr/{0}/aca'), ['lbl'])

		# Delete the AE+ACP again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACARetrieveCntFail(self) -> None:
		"""	Create an ACP with aca attribut, create and retrieve CNT -> Fail"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.RETRIEVE,
							'aca': [ 'lbl' ]	# only grant RETRIEVE permission to the label
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi ]

				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve full resource -> Fail
		r, rsc = RETRIEVE(cntURL, 'Cae1')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACARetrieveCnt(self) -> None:
		"""	Create an ACP with aca attribut, create and retrieve CNT"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.RETRIEVE,
							# The following list may be updated for other tests
							'aca': [ 'rn', 'acpi', 'ri', 'et', 'ct', 'pi', 'lt', 'ty', 'lbl', 'cni', 'cbs', 'st' ]	# grant access to all attributes.
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi ]

				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve full resource -> Fail
		r, rsc = RETRIEVE(cntURL, 'Cae1')
		self.assertEqual(rsc, RC.OK, r)

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACARetrieveCntPartial(self) -> None:
		"""	Create an ACP with aca attribut, create and partial retrieve CNT"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.RETRIEVE,
							# The following list may be updated for other tests
							'aca': [ 'lbl']	# grant access to all attributes.
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi ]

				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve only lbl -> OK
		r, rsc = RETRIEVE(f'{cntURL}?atrl=lbl', 'Cae1')
		self.assertEqual(rsc, RC.OK, r)

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACARetrieveCntPartialFail(self) -> None:
		"""	Create an ACP with aca attribut, create and partial retrieve CNT -> Fail"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.RETRIEVE,
							# The following list may be updated for other tests
							'aca': [ 'lbl']	# grant access to all attributes.
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi ]

				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve rn -> FAIL
		r, rsc = RETRIEVE(f'{cntURL}?atrl=rn', 'Cae1')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACAAndSimpleACPRetrieveCntPartial(self) -> None:
		"""	Create an ACP with aca attribut and a simple ACP, create and partial retrieve CNT"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.RETRIEVE,
							# The following list may be updated for other tests
							'aca': [ 'lbl']	# grant access to all attributes.
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN+'2',
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.RETRIEVE,
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi2 = findXPath(r, 'm2m:acp/ri')


		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi, acpRi2 ]
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve rn -> FAIL
		r, rsc = RETRIEVE(f'{cntURL}?atrl=rn', 'Cae1')
		self.assertEqual(rsc, RC.OK, r)

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACADeleteCntFail(self) -> None:
		"""	Create an ACP with aca attribut, create and delete CNT -> Fail"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.DELETE,
							'aca': [ 'lbl' ]	# only grant DELETE permission to the label
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi ]
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve full resource -> Fail
		r, rsc = DELETE(cntURL, 'Cae1')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACADeleteCnt(self) -> None:
		"""	Create an ACP with aca attribut, create and delete CNT"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.DELETE,
							# The following list may be updated for other tests
							'aca': [ 'rn', 'acpi', 'ri', 'et', 'ct', 'pi', 'lt', 'ty', 'lbl', 'cni', 'cbs', 'st' ]	# grant access to all attributes.
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi ]
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve full resource -> Fail
		r, rsc = DELETE(cntURL, 'Cae1')
		self.assertEqual(rsc, RC.DELETED, r)

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACACREATECntFail(self) -> None:
		"""	Create an ACP with aca attribut, create new CNT with not allowed attribute -> Fail"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.CREATE,
							'aca': [ 'lbl', 'rn' ]	# only grant CREATE permission for the label and rn
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi ]
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# create a second CNT under the CNT with a not-allowed attribute -> Fail
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'mni': 10,
				}}
		r, rsc = CREATE(cntURL, 'Cae1', T.CNT, dct)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACACREATECnt(self) -> None:
		"""	Create an ACP with aca attribut, create new CNT with only allowed attributes"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.CREATE,
							'aca': [ 'lbl', 'rn', 'mni' ]	# only grant CREATE permission for the label and rn and mni
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi ]
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# create a second CNT under the CNT with a not-allowed attribute -> Fail
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'mni': 10,
				}}
		r, rsc = CREATE(cntURL, 'Cae1', T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/rn'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/lbl'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/mni'))
		self.assertIsNone(findXPath(r, 'm2m:cnt/ri'))
		self.assertIsNone(findXPath(r, 'm2m:cnt/pi'))
		self.assertIsNone(findXPath(r, 'm2m:cnt/ct'))
		self.assertIsNone(findXPath(r, 'm2m:cnt/lt'))
		self.assertIsNone(findXPath(r, 'm2m:cnt/st'))

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACAUPDATECntFail(self) -> None:
		"""	Create an ACP with aca attribut, update CNT with not allowed attribute -> Fail"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.UPDATE,
							'aca': [ 'lbl' ]	# only grant UPDARE permission for the label
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi ]
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Update CNT's mni 	-> Fail
		dct = 	{ 'm2m:cnt' : {
					'mni': 10
				}}
		r, rsc = UPDATE(cntURL, 'Cae1', dct)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACPwithACAUPDATECnt(self) -> None:
		"""	Create an ACP with aca attribut, update CNT with allowed attribute -> Fail"""

		DELETE(aeURL, ORIGINATOR)
		dct = 	{ 'm2m:ae' : {
			'rn': aeRN, 
			'api': APPID,
			'rr': False,
			'srv': [ RELEASEVERSION ],
		}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestACP.originator = findXPath(TestACP.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:acp': {
					'rn': acpRN,
					'pv': {							
						'acr': [ {
							'acor': [ 'Cae1' ],	# different originator
							'acop': Permission.UPDATE,
							'aca': [ 'lbl' ]	# only grant UPDARE permission for the label
						} ],
					},
					'pvs': { 
						'acr': [ {
							'acor': [ TestACP.originator ],
							'acop': Permission.ALL,
						} ]
					},
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		acpRi = findXPath(r, 'm2m:acp/ri')

		# Create a CNT under the AE -> OK
		dct = 	{ 'm2m:cnt' : {
					'rn': cntRN,
					'lbl': [ 'test' ],
					'acpi': [ acpRi ]
				}}
		r, rsc = CREATE(aeURL, TestACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Update CNT's mni 	-> Fail
		dct = 	{ 'm2m:cnt' : {
					'lbl': [ 'test2' ]
				}}
		r, rsc = UPDATE(cntURL, 'Cae1', dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Delete the AE+ACP+CNT again
		_, rsc = DELETE(f'{aeURL}', TestACP.originator)
		self.assertEqual(rsc, RC.DELETED)



# TODO reference a non-acp resource in acpi
# TODO acod/specialization



def run(testFailFast:bool) -> TestResult:
	suite = unittest.TestSuite()

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestACP, [

		# Basic ACP tests
		'test_createACP',
		'test_retrieveACP',
		'test_retrieveACPwrongOriginator',
		'test_attributesACP',
		'test_updateACP',
		'test_updateACPwrongOriginator',
		'test_updateACPEmptyPVSFail',
		'test_updateACPNoPVSFail',
		'test_addACPtoAE',
		'test_updateAEACPIWrong',
		'test_updateAEACPIWrong2',
		'test_updateAEACPIWrongOriginator',
		'test_updateAEACPIOtherOriginator',

		# wildcard tests
		'test_updateAElblWithWildCardOriginator',
		'test_updateAElblWithWildCardOriginator2',
		'test_updateAElblWithWildCardOriginator3WrongFail',

		'test_createACPNoPVSFail',
		'test_createACPEmptyPVSFail',

		'test_createCNTwithNoACPI',
		'test_retrieveCNTwithNoACPI',
		'test_retrieveCNTwithNoACPIWrongOriginator',
		'test_deleteCNTwithNoACPI',

		'test_createCNTwithNoACPIAndCustodian',
		'test_retrieveCNTwithNoACPIAndCustodian',
		'test_retrieveCNTwithNoACPIAndCustodianAEOriginator',
		'test_retrieveCNTwithNoACPIAndCustodianWrongOriginator',
		'test_deleteCNTwithNoACPIAndCustodian',

		'test_removeACPfromAEWrong',
		'test_removeACPfromAEWrong2',
		'test_removeACPfromAE',
		'test_deleteACPwrongOriginator',
		'test_deleteACP',

		'test_createACPUnderCSEBaseWithOriginator',
		'test_deleteACPUnderCSEBaseWithOriginator',

		'test_createACPUnderAEWithChty',
		'test_updateAEACPIForChty',
		'test_testACPChty',
		'test_deleteACPUnderAEWithChty',

		'test_accessCINwithDifferentAENoAcpi',
		'test_accessCINwithDifferentAEWithAcpi',
		'test_discoverCINwithDifferentAEWithAcpi',

		'test_retrieveACPwithoutRETRIEVEAccessFail',

		'test_createACPWithWrongTyFail',
		'test_createACPWithTy',

		# ACP with GRP tests 
		'test_testACPacorGRP',

		# ACP with accessControlAttributes
		'test_createACPwithACA',
		'test_updateACPwithACA',
		'test_createACPwithACARetrieveCntFail',
		'test_createACPwithACARetrieveCnt',
		'test_createACPwithACARetrieveCntPartial',
		'test_createACPwithACARetrieveCntPartialFail',
		'test_createACPwithACAAndSimpleACPRetrieveCntPartial',
		'test_createACPwithACADeleteCntFail',
		'test_createACPwithACADeleteCnt',
		'test_createACPwithACACREATECntFail',
		'test_createACPwithACACREATECnt',
		'test_createACPwithACAUPDATECntFail',
		'test_createACPwithACAUPDATECnt',
	])

	# Run tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
