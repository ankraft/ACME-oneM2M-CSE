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
from init import *


class TestCIN(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		jsn = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', C.tAE, jsn)	# AE to work under
		assert rsc == C.rcCreated, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, C.tCNT, jsn)
		assert rsc == C.rcCreated, 'cannot create container'


	@classmethod
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	def test_createCIN(self):
		self.assertIsNotNone(TestCIN.cse)
		self.assertIsNotNone(TestCIN.ae)
		self.assertIsNotNone(TestCIN.cnt)
		jsn = 	{ 'm2m:cin' : {
					'rn'  : cinRN,
					'cnf' : 'a',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, C.tCNT, jsn)
		self.assertEqual(rsc, C.rcCreated)


	def test_retrieveCIN(self):
		_, rsc = RETRIEVE(cinURL, TestCIN.originator)
		self.assertEqual(rsc, C.rcOK)


	def test_attributesCIN(self):
		r, rsc = RETRIEVE(cinURL, TestCIN.originator)
		self.assertEqual(rsc, C.rcOK)

		# TEST attributess
		self.assertEqual(findXPath(r, 'm2m:cin/ty'), C.tCIN)
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


	def test_updateCIN(self):
		jsn = 	{ 'm2m:cin' : {
					'con' : 'NewValue'
				}}
		r, rsc = UPDATE(cinURL, TestCIN.originator, jsn)
		self.assertEqual(rsc, C.rcOperationNotAllowed)


	def test_createCINUnderAE(self):
		jsn = 	{ 'm2m:cin' : {
					'rn'  : cinRN,
					'cnf' : 'a',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(aeURL, TestCIN.originator, C.tCNT, jsn)
		self.assertEqual(rsc, C.rcInvalidChildResourceType)


	def test_deleteCIN(self):
		_, rsc = DELETE(cntURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)

# More tests of la, ol etc in testCNT_CNI.py

if __name__ == '__main__':
	suite = unittest.TestSuite()
	suite.addTest(TestCIN('test_createCIN'))
	suite.addTest(TestCIN('test_retrieveCIN'))
	suite.addTest(TestCIN('test_attributesCIN'))
	suite.addTest(TestCIN('test_updateCIN'))
	suite.addTest(TestCIN('test_createCINUnderAE'))
	suite.addTest(TestCIN('test_deleteCIN'))
	unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)

