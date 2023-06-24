#
#	testCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CNT functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *


class TestCNT(unittest.TestCase):

	ae 				= None
	originator 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup testCNT')
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		testCaseEnd('Setup testCNT')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown testCNT')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)
		testCaseEnd('TearDown testCNT')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNT(self) -> None:
		"""	Create <CNT> """
		self.assertIsNotNone(TestCNT)
		self.assertIsNotNone(TestCNT.ae)
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, TestCNT.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNT(self) -> None:
		""" Retrieve <CNT> """
		_, rsc = RETRIEVE(cntURL, TestCNT.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTWithWrongOriginator(self) -> None:
		"""	Retrieve <CNT> with wrong originator -> Fail """
		_, rsc = RETRIEVE(cntURL, 'Cwrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesCNT(self) -> None:
		""" Test <CNT> attributes """
		r, rsc = RETRIEVE(cntURL, TestCNT.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/ty'), T.CNT)
		self.assertEqual(findXPath(r, 'm2m:cnt/pi'), findXPath(TestCNT.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/st'))
		self.assertIsNone(findXPath(r, 'm2m:cnt/cr'))
		self.assertEqual(findXPath(r, 'm2m:cnt/cbs'), 0)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 0)
		self.assertIsNone(findXPath(r, 'm2m:cnt/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNT(self) -> None:
		"""	Update <CNT> """
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'aTag' ],
					'mni' : 10,
					'mbs' : 9999
 				}}
		cnt, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		cnt, rsc = RETRIEVE(cntURL, TestCNT.originator)		# retrieve cnt again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/lbl'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/lbl'), list)
		self.assertGreater(len(findXPath(cnt, 'm2m:cnt/lbl')), 0)
		self.assertTrue('aTag' in findXPath(cnt, 'm2m:cnt/lbl'))
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mni'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/mni'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mni'), 10)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mbs'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/mbs'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mbs'), 9999)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/st'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/st'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/st'), 1)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTTy(self) -> None:
		"""	Update <CNT> TY -> Fail """
		dct = 	{ 'm2m:cnt' : {
					'ty' : T.CSEBase
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTPi(self) -> None:
		"""	Update <CNT> PI -> Fail """
		dct = 	{ 'm2m:cnt' : {
					'pi' : 'wrongID'
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTUnknownAttribute(self) -> None:
		"""	Update <CNT> unknown attribute -> Fail """
		dct = 	{ 'm2m:cnt' : {
					'unknown' : 'unknown'
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWrongMNI(self) -> None:
		"""	Update <CNT> wrong MNI -> Fail """
		dct = 	{ 'm2m:cnt' : {
					'mni' : -1
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTempty(self) -> None:
		"""	Update <CNT> empty content """
		dct:JSON = { 'm2m:cnt' : {
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTUnderCNT(self) -> None:
		""" Create <CNT> under <CNT> """
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(cntURL, TestCNT.originator, T.CNT, dct) 
		self.assertEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTUnderCNT(self) -> None:
		"""	Retrieve <CNT> under <CNT> """
		_, rsc = RETRIEVE(f'{cntURL}/{cntRN}', TestCNT.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTUnderCNT(self) -> None:
		"""	Delete <CNT> under <CNT> """
		_, rsc = DELETE(f'{cntURL}/{cntRN}', TestCNT.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTWithCreatorWrong(self) -> None:
		""" Create <CNT> with creator attribute (wrong) -> Fail """
		dct = 	{ 'm2m:cnt' : { 
					'cr' : 'wrong'
				}}
		r, rsc = CREATE(aeURL, TestCNT.originator, T.CNT, dct) 				# Not allowed
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTWithCreator(self) -> None:
		""" Create <CNT> with creator attribute set to Null """
		dct = 	{ 'm2m:cnt' : { 
					'cr' : None
				}}
		r, rsc = CREATE(aeURL, TestCNT.originator, T.CNT, dct) 
		self.assertEqual(rsc, RC.CREATED)
		self.assertEqual(findXPath(r, 'm2m:cnt/cr'), TestCNT.originator, r)	# Creator should now be set to originator

		# Check whether creator is there in a RETRIEVE
		r, rsc = RETRIEVE(f'{aeURL}/{findXPath(r, "m2m:cnt/rn")}', TestCNT.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/cr'), TestCNT.originator)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTByUnknownOriginator(self) -> None:
		"""	Delete <CNT> with wrong originator -> Fail """
		_, rsc = DELETE(cntURL, 'Cwrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTByAssignedOriginator(self) -> None:
		"""	Delete <CNT> with correct originator """
		_, rsc = DELETE(cntURL, TestCNT.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTUnderCSE(self) -> None:
		"""	Create <CNT> under <CB> with admin Originator """
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct) # With Admin originator !!
		self.assertEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTUnderCSE(self) -> None:
		"""	Retrieve <CNT> under <CB> with admin Originator """
		_, rsc = RETRIEVE(f'{cseURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTUnderCSE(self) -> None:
		"""	Delete <CNT> under <CB> with admin Originator"""
		_, rsc = DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(BINDING in [ 'http', 'https' ], 'Only when testing with http(s) binding')
	def test_createCNTWithoutOriginator(self) -> None:
		"""	Create <CNT> under <CB> without an Originator -> Fail"""
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(cseURL, None, T.CNT, dct) # Without originator !!
		self.assertNotEqual(rsc, RC.CREATED)

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithWrongTPE(self) -> None:
		"""	Create <CNT> with wrong TPE -> Fail"""
		dct = 	{ 'wrong' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct) # Without originator !!
		self.assertNotEqual(rsc, RC.CREATED)


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
		
	addTest(suite, TestCNT('test_createCNT'))
	addTest(suite, TestCNT('test_retrieveCNT'))
	addTest(suite, TestCNT('test_retrieveCNTWithWrongOriginator'))
	addTest(suite, TestCNT('test_attributesCNT'))
	addTest(suite, TestCNT('test_updateCNT'))
	addTest(suite, TestCNT('test_updateCNTTy'))
	addTest(suite, TestCNT('test_updateCNTempty'))
	addTest(suite, TestCNT('test_updateCNTPi'))
	addTest(suite, TestCNT('test_updateCNTUnknownAttribute'))
	addTest(suite, TestCNT('test_updateCNTWrongMNI'))
	addTest(suite, TestCNT('test_createCNTUnderCNT'))
	addTest(suite, TestCNT('test_retrieveCNTUnderCNT'))
	addTest(suite, TestCNT('test_deleteCNTUnderCNT'))
	addTest(suite, TestCNT('test_createCNTWithCreatorWrong'))
	addTest(suite, TestCNT('test_createCNTWithCreator'))

	addTest(suite, TestCNT('test_deleteCNTByUnknownOriginator'))
	addTest(suite, TestCNT('test_deleteCNTByAssignedOriginator'))
	addTest(suite, TestCNT('test_createCNTUnderCSE'))
	addTest(suite, TestCNT('test_retrieveCNTUnderCSE'))
	addTest(suite, TestCNT('test_deleteCNTUnderCSE'))

	addTest(suite, TestCNT('test_createCNTWithoutOriginator'))
	addTest(suite, TestCNT('test_createCNTwithWrongTPE'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
