#
#	testCIN.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CIN functionality
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

class TestCIN(unittest.TestCase):

	cse 		= None
	ae 			= None
	cnt 		= None
	originator 	= None


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}' 

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
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCIN(self) -> None:
		""" Create a <CIN> resource """
		self.assertIsNotNone(TestCIN.ae)
		self.assertIsNotNone(TestCIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'rn'  : cinRN,
					'cnf' : 'a',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCIN(self) -> None:
		""" Retrieve <CIN> resource """
		_, rsc = RETRIEVE(cinURL, TestCIN.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesCIN(self) -> None:
		""" Test <CIN> attributes """
		r, rsc = RETRIEVE(cinURL, TestCIN.originator)
		self.assertEqual(rsc, RC.OK)

		# TEST attributess
		self.assertEqual(findXPath(r, 'm2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(r, 'm2m:cin/pi'), findXPath(TestCIN.cnt,'m2m:cnt/ri'))
		self.assertEqual(findXPath(r, 'm2m:cin/rn'), cinRN)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:cin/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:cin/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:cin/st'))
		self.assertEqual(findXPath(r, 'm2m:cin/cr'), TestCIN.originator)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/cnf'))
		self.assertEqual(findXPath(r, 'm2m:cin/cnf'), 'a')
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'AnyValue')
		self.assertGreater(findXPath(r, 'm2m:cin/cs'), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCIN(self) -> None:
		""" Update <CIN> -> Fail """
		dct = 	{ 'm2m:cin' : {
					'con' : 'NewValue'
				}}
		r, rsc = UPDATE(cinURL, TestCIN.originator, dct)
		self.assertEqual(rsc, RC.operationNotAllowed)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINUnderAE(self) -> None:
		""" Create <CIN> resource under <AE> -> Fail """
		dct = 	{ 'm2m:cin' : {
					'rn'  : cinRN,
					'cnf' : 'a',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(aeURL, TestCIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.invalidChildResourceType)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCIN(self) -> None:
		""" Delete <CIN> resource """
		_, rsc = DELETE(cntURL, TestCIN.originator)
		self.assertEqual(rsc, RC.deleted)

# More tests of la, ol etc in testCNT_CNI.py

def run() -> Tuple [int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestCIN('test_createCIN'))
	suite.addTest(TestCIN('test_retrieveCIN'))
	suite.addTest(TestCIN('test_attributesCIN'))
	suite.addTest(TestCIN('test_updateCIN'))
	suite.addTest(TestCIN('test_createCINUnderAE'))
	suite.addTest(TestCIN('test_deleteCIN'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
