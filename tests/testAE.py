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
from typing import Tuple, Optional
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
		testCaseStart('Setup TestACP')
		cls.originator 	= None 	# actually the AE.aei
		cls.aeACPI 		= None
		cls.cse, rsc 	= RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}'
		testCaseEnd('Setup TestAE')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestAE')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not
		testCaseEnd('TearDown TestAE')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAE(self) -> None:
		""" Create/register an <AE> """
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct)

		self.assertEqual(rsc, RC.CREATED, r)
		TestAE.originator = findXPath(r, 'm2m:ae/aei')
		TestAE.aeACPI = findXPath(r, 'm2m:ae/acpi')
		self.assertIsNotNone(TestAE.originator, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEUnderAEFail(self) -> None:
		""" Create/register an <AE> under an <AE> -> Fail """
		dct = 	{ 'm2m:ae' : {
					'rn': f'{aeRN}1', 
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		r, rsc = CREATE(aeURL, ORIGINATORSelfReg, T.AE, dct)
		self.assertEqual(rsc, RC.INVALID_CHILD_RESOURCE_TYPE, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEAgainFail(self) -> None:
		""" Create/register an <AE> with same rn again -> Fail """
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct)

		self.assertEqual(rsc, RC.CONFLICT)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEWithExistingOriginatorFail(self) -> None:
		""" Create/register an <AE> with same originator again -> Fail """
		dct = 	{ 'm2m:ae' : {
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		r, rsc = CREATE(cseURL, TestAE.originator, T.AE, dct)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_ALREADY_REGISTERED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAECSIoriginatorFail(self) -> None:
		""" Create/register an <AE> with the CSI originator -> Fail """
		dct = 	{ 'm2m:ae' : {
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		r, rsc = CREATE(cseURL, CSEID[1:], T.AE, dct)
		self.assertEqual(rsc, RC.SECURITY_ASSOCIATION_REQUIRED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveAE(self) -> None:
		""" Retrieve <AE> """
		r, rsc = RETRIEVE(aeURL, TestAE.originator)
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveAEWithWrongOriginator(self) -> None:
		""" Retrieve <AE> with wrong originator -> Fail """
		_, rsc = RETRIEVE(aeURL, 'Cwrong')
		self.assertIn(rsc, [RC.ORIGINATOR_HAS_NO_PRIVILEGE, RC.SERVICE_SUBSCRIPTION_NOT_ESTABLISHED])


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
		self.assertEqual(findXPath(r, 'm2m:ae/srv'), [ RELEASEVERSION ])
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
		self.assertEqual(rsc, RC.UPDATED)
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
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEPi(self) -> None:
		""" Update <AE> with pi=wrong -> Fail """
		dct = 	{ 'm2m:ae' : {
					'pi' : 'wrongID'
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEUnknownAttribute(self) -> None:
		""" Update <AE> with unknown attribute -> Fail """
		dct = 	{ 'm2m:ae' : {
					'unknown' : 'unknown'
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEByUnknownOriginator(self) -> None:
		""" Delete <AE> with wrong originator -> Fail """
		_, rsc = DELETE(aeURL, 'Cwrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEByAssignedOriginator(self) -> None:
		""" Delete <AE> with correct originator -> <AE> deleted """
		_, rsc = DELETE(aeURL, TestAE.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEWrongCSZ(self) -> None:
		""" Create <AE> with wrong csz content -> Fail """
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ],
					'csz': [ 'wrong' ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct)

		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAECSZ(self) -> None:
		""" Create <AE> with correct csz value"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ],
					'csz': [ 'application/cbor', 'application/json' ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct)

		self.assertEqual(rsc, RC.CREATED)
		TestAE.originator2 = findXPath(r, 'm2m:ae/aei')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAECSZ(self) -> None:
		""" Delete <AE> with csr -> <AE> deleted """
		_, rsc = DELETE(aeURL, TestAE.originator2)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAENoAPI(self) -> None:
		""" Create <AE> with missing api attribute -> Fail"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct)

		self.assertNotEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEAPIWrongPrefix(self) -> None:
		""" Create <AE> with unknown api prefix -> Fail"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'Xwrong',
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct)

		self.assertNotEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEAPICorrectR(self) -> None:
		""" Create <AE> with correct api value (Registered)"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'Rabc.com.example.acme',
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		ae, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct)

		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/aei'))
		_, rsc = DELETE(aeURL, findXPath(ae, 'm2m:ae/aei'))
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEAPICorrectN(self) -> None:
		""" Create <AE> with correct api value (Non-Registered)"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'Nacme',
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		ae, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct)

		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/aei'))
		_, rsc = DELETE(aeURL, findXPath(ae, 'm2m:ae/aei'))
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEAPIRVI3LowerCaseR(self) -> None:
		""" Create <AE> with RVI=3 and lower case API"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'racme',
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		headers={ C.hfRVI: '3'	# explicit 3
		}
		ae, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct, headers = headers)

		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/aei'))
		_, rsc = DELETE(aeURL, findXPath(ae, 'm2m:ae/aei'))
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEAPIRVI4LowerCaseRFail(self) -> None:
		""" Create <AE> with RVI=4 and lower case API -> Fail"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'racme',
				 	'rr': False,
				 	'srv': [ '4' ]	# explicit 4
				}}
		headers={ C.hfRVI: '4'	# explicit 4
		}
		ae, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct, headers = headers)

		self.assertEqual(rsc, RC.BAD_REQUEST, ae)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAENoOriginator(self) -> None:
		""" Create <AE> without an Originator"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'Nacme',
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		ae, rsc = CREATE(cseURL, None, T.AE, dct)
		self.assertEqual(rsc, RC.CREATED, ae)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/aei'))
		_, rsc = DELETE(aeURL, findXPath(ae, 'm2m:ae/aei'))
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEEmptyOriginator(self) -> None:
		""" Create <AE> with an empty Originator"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'Nacme',
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		ae, rsc = CREATE(cseURL, ORIGINATOREmpty, T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/aei'))
		_, rsc = DELETE(aeURL, findXPath(ae, 'm2m:ae/aei'))
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEInvalidRNFail(self) -> None:
		""" Create <AE> with an invalid rn -> Fail"""
		
		# With unallowed character
		dct = 	{ 'm2m:ae' : {
					'rn': 'test?',	# not from unreserved character
					'api': 'Nacme',
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		ae, rsc = CREATE(cseURL, ORIGINATOREmpty, T.AE, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)

		# With space
		dct = 	{ 'm2m:ae' : {
					'rn': 'test wrong',	# not from unreserved character
					'api': 'Nacme',
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		ae, rsc = CREATE(cseURL, ORIGINATOREmpty, T.AE, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


# TODO register multiple AEs
# TODO register with S


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()

	addTest(suite, TestAE('test_createAE'))
	addTest(suite, TestAE('test_createAEUnderAEFail'))
	addTest(suite, TestAE('test_createAEAgainFail'))
	addTest(suite, TestAE('test_createAEWithExistingOriginatorFail'))
	addTest(suite, TestAE('test_createAECSIoriginatorFail'))
	addTest(suite, TestAE('test_retrieveAE'))
	addTest(suite, TestAE('test_retrieveAEWithWrongOriginator'))
	addTest(suite, TestAE('test_attributesAE'))
	addTest(suite, TestAE('test_updateAELbl'))
	addTest(suite, TestAE('test_updateAETy'))
	addTest(suite, TestAE('test_updateAEPi'))
	addTest(suite, TestAE('test_updateAEUnknownAttribute'))
	addTest(suite, TestAE('test_deleteAEByUnknownOriginator'))
	addTest(suite, TestAE('test_deleteAEByAssignedOriginator'))
	addTest(suite, TestAE('test_createAEWrongCSZ'))
	addTest(suite, TestAE('test_createAECSZ'))	
	addTest(suite, TestAE('test_deleteAECSZ'))	
	addTest(suite, TestAE('test_createAENoAPI'))	
	addTest(suite, TestAE('test_createAEAPIWrongPrefix'))	
	addTest(suite, TestAE('test_createAEAPICorrectR'))	
	addTest(suite, TestAE('test_createAEAPICorrectN'))	
	addTest(suite, TestAE('test_createAEAPIRVI3LowerCaseR'))	
	addTest(suite, TestAE('test_createAEAPIRVI4LowerCaseRFail'))
	addTest(suite, TestAE('test_createAENoOriginator'))	
	addTest(suite, TestAE('test_createAEEmptyOriginator'))	
	addTest(suite, TestAE('test_createAEInvalidRNFail'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
