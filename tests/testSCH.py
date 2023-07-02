 #
#	testSCH.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Schedule functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, Permission
from acme.etc.Types import EvalMode, Operation, EvalCriteriaOperator
from init import *

nodeID  = 'urn:sn:1234'


class TestSCH(unittest.TestCase):

	ae 			= None
	aeRI		= None
	ae2 		= None
	nod 		= None
	nodRI		= None


	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestSCH')
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		cls.aeRI = findXPath(cls.ae, 'm2m:ae/ri')
	

		dct = 	{ 'm2m:nod' : { 
					'rn' 	: nodRN,
					'ni'	: nodeID
				}}
		cls.nod, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, dct)
		assert rsc == RC.CREATED
		cls.nodRI = findXPath(cls.nod, 'm2m:nod/ri')

		testCaseEnd('Setup TestSCH')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestSCH')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(nodURL, ORIGINATOR)	# Just delete the NOD and everything below it. Ignore whether it exists or not
		DELETE(f'{cseURL}/{schRN}', ORIGINATOR)
		testCaseEnd('TearDown TestSCH')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################

# TODO validate schedule element format *****

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderCBwithNOCFail(self) -> None:
		"""	CREATE invalid <SCH> with "nco" under CSEBase -> Fail"""
		self.assertIsNotNone(TestSCH.ae)
		dct = 	{ 'm2m:sch' : {
					'rn' : schRN,
					'se': { 'sce': [ '* * * * * * *' ] },
					'nco': True
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CONTENTS_UNACCEPTABLE, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderNODwithNOCUnsupportedFail(self) -> None:
		"""	CREATE <SCH> with nco under NOD (unsupported) -> Fail"""
		self.assertIsNotNone(TestSCH.ae)
		dct = 	{ 'm2m:sch' : {
					'rn' : schRN,
					'se': { 'sce': [ '* * * * * * *' ] },
					'nco': True
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.NOT_IMPLEMENTED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSCHunderCBwithoutNCO(self) -> None:
		"""	CREATE <SCH> without "nco" under CSEBase"""
		self.assertIsNotNone(TestSCH.ae)
		dct = 	{ 'm2m:sch' : {
					'rn' : schRN,
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DELETE again
		r, rsc = DELETE(f'{cseURL}/{schRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSCHunderCBwithNCOFail(self) -> None:
		"""	UPDATE <SCH> without "nco" under CSEBase -> Fail"""
		self.assertIsNotNone(TestSCH.ae)
		dct:JSON = 	{ 'm2m:sch' : {
					'rn' : schRN,
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# UPDATE with nco
		dct = 	{ 'm2m:sch' : {
					'nco': True
				}}
		r, rsc = UPDATE(f'{cseURL}/{schRN}', ORIGINATOR, dct)
		self.assertEqual(rsc, RC.CONTENTS_UNACCEPTABLE, r)

		# DELETE again
		r, rsc = DELETE(f'{cseURL}/{schRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSCHunderNODwithNOCUnsupportedFail(self) -> None:
		"""	CREATE <SCH> with nco under NOD (unsupported-> Fail"""
		self.assertIsNotNone(TestSCH.ae)
		dct:JSON = 	{ 'm2m:sch' : {
					'rn' : schRN,
					'se': { 'sce': [ '* * * * * * *' ] }
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.SCH, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# UPDATE with nco
		dct = 	{ 'm2m:sch' : {
					'nco': True
				}}
		r, rsc = UPDATE(f'{nodURL}/{schRN}', ORIGINATOR, dct)
		self.assertEqual(rsc, RC.NOT_IMPLEMENTED, r)

		# DELETE again
		r, rsc = DELETE(f'{nodURL}/{schRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)




def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()

	# basic tests
	addTest(suite, TestSCH('test_createSCHunderCBwithNOCFail'))
	addTest(suite, TestSCH('test_createSCHunderNODwithNOCUnsupportedFail'))
	addTest(suite, TestSCH('test_createSCHunderCBwithoutNCO'))
	addTest(suite, TestSCH('test_updateSCHunderCBwithNCOFail'))
	addTest(suite, TestSCH('test_updateSCHunderNODwithNOCUnsupportedFail'))


	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)