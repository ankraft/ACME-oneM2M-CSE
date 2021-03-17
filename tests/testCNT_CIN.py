#
#	testCNT_CIN.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CNT & CIN functionality
#

import unittest, sys
sys.path.append('../acme')
from typing import Tuple
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from init import *


maxBS = 30

class TestCNT_CIN(unittest.TestCase):

	ae 			= None
	originator 	= None
	cnt 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mni' : 3
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		assert findXPath(cls.cnt, 'm2m:cnt/mni') == 3, 'mni is not correct'


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCIN(self) -> None:
		"""	Create <CIN> under <CNT> """
		self.assertIsNotNone(TestCNT_CIN.ae)
		self.assertIsNotNone(TestCNT_CIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'aValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/ri'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		self.cinARi = findXPath(r, 'm2m:cin/ri')			# store ri

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 1)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addMoreCIN(self) -> None:
		"""	Create more <CIN>s under <CNT> """
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'bValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'bValue')

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 2)

		dct = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'cValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'cValue')

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 3)

		dct = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'dValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 3)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTLa(self) -> None:
		"""	Retrieve <CNT>.LA """
		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTOl(self) -> None:
		""" Retrieve <CNT>.OL """
		r, rsc = RETRIEVE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'bValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_changeCNTMni(self) -> None:
		"""	Change <CNT>.MNI to 1 -> OL == LA """
		dct = 	{ 'm2m:cnt' : {
					'mni' : 1
 				}}
		cnt, rsc = UPDATE(cntURL, TestCNT_CIN.originator, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(cnt)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mni'))
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mni'), 1)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/cni'))
		self.assertEqual(findXPath(cnt, 'm2m:cnt/cni'), 1)

		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')

		r, rsc = RETRIEVE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNT(self) -> None:
		"""	Delete <CNT> """
		_, rsc = DELETE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithMBS(self) -> None:
		"""	Create <CNT> with mbs"""
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mbs' : maxBS
				}}
		TestCNT_CIN.cnt, rsc = CREATE(aeURL, TestCNT_CIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/mbs'))
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/mbs'), maxBS)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINexactSize(self) -> None:
		"""	Add <CIN> to <CNT> with exact max size"""
		dct = 	{ 'm2m:cin' : {
					'con' : 'x' * maxBS
				}}
		_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINtooBig(self) -> None:
		"""	Add <CIN> to <CNT> with size > mbs -> Fail """
		dct = 	{ 'm2m:cin' : {
					'con' : 'x' * (maxBS + 1)
				}}
		_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.notAcceptable)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINsForCNTwithSize(self) -> None:
		"""	Add multiple <CIN>s to <CNT> with size restrictions """
		# First fill up the container
		for _ in range(int(maxBS / 3)):
			dct = 	{ 'm2m:cin' : {
						'con' : 'x' * int(maxBS / 3)
					}}
			_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.created)
		
		# Test latest CIN for x
		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertTrue(findXPath(r, 'm2m:cin/con').startswith('x'))
		self.assertEqual(len(findXPath(r, 'm2m:cin/con')), int(maxBS / 3))

		# Add another CIN
		dct = 	{ 'm2m:cin' : {
					'con' : 'y' * int(maxBS / 3)
				}}
		_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)

		# Test latest CIN for y
		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertTrue(findXPath(r, 'm2m:cin/con').startswith('y'))
		self.assertEqual(len(findXPath(r, 'm2m:cin/con')), int(maxBS / 3))

		# Test CNT
		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 3)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cbs'))
		self.assertEqual(findXPath(r, 'm2m:cnt/cbs'), maxBS)


def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestCNT_CIN('test_addCIN'))
	suite.addTest(TestCNT_CIN('test_addMoreCIN'))
	suite.addTest(TestCNT_CIN('test_retrieveCNTLa'))
	suite.addTest(TestCNT_CIN('test_retrieveCNTOl'))
	suite.addTest(TestCNT_CIN('test_changeCNTMni'))
	suite.addTest(TestCNT_CIN('test_deleteCNT'))
	suite.addTest(TestCNT_CIN('test_createCNTwithMBS'))
	suite.addTest(TestCNT_CIN('test_createCINexactSize'))
	suite.addTest(TestCNT_CIN('test_createCINtooBig'))
	suite.addTest(TestCNT_CIN('test_createCINsForCNTwithSize'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
