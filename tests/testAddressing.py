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

		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : True,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		cls.cntRI = findXPath(cls.cnt, 'm2m:cnt/ri')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_cseRelativeStructured(self) -> None:
		""" Test CSE-relative structured """
		url = f'{URL}{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		url = f'{URL}-/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_cseRelativeUnstructured(self) -> None:
		""" Test CSE-relative unstructured """
		url = f'{URL}{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_spRelativeStructured(self) -> None:
		""" Test SP-relative structured """
		url = f'{URL}{CSEID}/{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		url = f'{URL}{CSEID}/-/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_spRelativeUnstructured(self) -> None:
		""" Test SP-relative unstructured """
		url = f'{URL}{CSEID}/{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteStructured(self) -> None:
		""" Test absolute structured """
		url = f'{URL}//{SPID}{CSEID}/{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		url = f'{URL}//{SPID}{CSEID}/-/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteUnstructured(self) -> None:
		""" Test absolute unstructured """
		url = f'{URL}//{SPID}{CSEID}/{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteStructuredWrongSPIDFail(self) -> None:
		""" Test absolute structured with wrong SPID -> Fail"""
		url = f'{URL}//wrong{CSEID}/{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteUnstructuredWrongSPIDFail(self) -> None:
		""" Test absolute unstructured with wrong SPID -> Fail"""
		url = f'{URL}//wrong{CSEID}/{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.badRequest)



def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestAddressing('test_cseRelativeStructured'))
	suite.addTest(TestAddressing('test_cseRelativeUnstructured'))
	suite.addTest(TestAddressing('test_spRelativeStructured'))
	suite.addTest(TestAddressing('test_spRelativeUnstructured'))
	suite.addTest(TestAddressing('test_absoluteStructuredWrongSPIDFail'))
	suite.addTest(TestAddressing('test_absoluteUnstructuredWrongSPIDFail'))
	suite.addTest(TestAddressing('test_absoluteStructured'))
	suite.addTest(TestAddressing('test_absoluteUnstructured'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)

