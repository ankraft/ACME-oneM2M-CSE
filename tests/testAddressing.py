#
#	testAddressing.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for addressing methods
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *


class TestAddressing(unittest.TestCase):

	ae 			= None
	originator 	= None
	cnt			= None
	cntRI 		= None


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestAddressing')
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		cls.cntRI = findXPath(cls.cnt, 'm2m:cnt/ri')
		testCaseEnd('Setup TestAddressing')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestAddressing')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestAddressing')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_cseRelativeStructured(self) -> None:
		""" Test CSE-relative structured """
		url = f'{CSEURL}{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		url = f'{CSEURL}-/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_cseRelativeUnstructured(self) -> None:
		""" Test CSE-relative unstructured """
		url = f'{CSEURL}{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_spRelativeStructured(self) -> None:
		""" Test SP-relative structured """
		url = f'{CSEURL}{CSEID}/{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		url = f'{CSEURL}{CSEID}/-/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_spRelativeUnstructured(self) -> None:
		""" Test SP-relative unstructured """
		url = f'{CSEURL}{CSEID}/{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_spRelativeCSEIDFail(self) -> None:
		""" Test SP-relative /<cse-id> -> Fail" """
		url = f'{CSEURL}{CSEID}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteStructured(self) -> None:
		""" Test absolute structured """
		url = f'{CSEURL}//{SPID}{CSEID}/{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		url = f'{CSEURL}//{SPID}{CSEID}/-/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteUnstructured(self) -> None:
		""" Test absolute unstructured """
		url = f'{CSEURL}//{SPID}{CSEID}/{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteStructuredWrongSPIDFail(self) -> None:
		""" Test absolute structured with wrong SPID -> Fail"""
		url = f'{CSEURL}//wrong{CSEID}/{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteUnstructuredWrongSPIDFail(self) -> None:
		""" Test absolute unstructured with wrong SPID -> Fail"""
		url = f'{CSEURL}//wrong{CSEID}/{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteCSEIDFail(self) -> None:
		""" Test absolute /cse-id -> Fail" """
		url = f'{CSEURL}//{SPID}{CSEID}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
	
	addTest(suite, TestAddressing('test_cseRelativeStructured'))
	addTest(suite, TestAddressing('test_cseRelativeUnstructured'))
	addTest(suite, TestAddressing('test_spRelativeStructured'))
	addTest(suite, TestAddressing('test_spRelativeUnstructured'))
	addTest(suite, TestAddressing('test_spRelativeCSEIDFail'))
	addTest(suite, TestAddressing('test_absoluteStructuredWrongSPIDFail'))
	addTest(suite, TestAddressing('test_absoluteUnstructuredWrongSPIDFail'))
	addTest(suite, TestAddressing('test_absoluteStructured'))
	addTest(suite, TestAddressing('test_absoluteUnstructured'))
	addTest(suite, TestAddressing('test_absoluteCSEIDFail'))
	
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)

