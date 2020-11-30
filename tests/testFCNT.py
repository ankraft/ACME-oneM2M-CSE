#
#	testFCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for FCNT functionality & notifications
#

import unittest, sys
import requests
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)


CND = 'org.onem2m.home.moduleclass.temperature'

class TestFCNT(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, 'cannot retrieve CSEBase'

		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
					'rr': False,
					'srv': [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNT(self):
		self.assertIsNotNone(TestFCNT.cse)
		self.assertIsNotNone(TestFCNT.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curTe'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFCNT(self):
		_, rsc = RETRIEVE(fcntURL, TestFCNT.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFCNTWithWrongOriginator(self):
		_, rsc = RETRIEVE(fcntURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesFCNT(self):
		r, rsc = RETRIEVE(fcntURL, TestFCNT.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'cod:tempe/ty'), T.FCNT)
		self.assertEqual(findXPath(r, 'cod:tempe/pi'), findXPath(TestFCNT.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'cod:tempe/rn'), fcntRN)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/ct'))
		self.assertIsNotNone(findXPath(r, 'cod:tempe/lt'))
		self.assertIsNotNone(findXPath(r, 'cod:tempe/et'))
		self.assertEqual(findXPath(r, 'cod:tempe/cr'), TestFCNT.originator)
		self.assertEqual(findXPath(r, 'cod:tempe/cnd'), CND)
		self.assertEqual(findXPath(r, 'cod:tempe/curTe'), 23.0)
		self.assertIsNone(findXPath(r, 'cod:tempe/tarTe'))
		self.assertEqual(findXPath(r, 'cod:tempe/unit'), 1)
		self.assertEqual(findXPath(r, 'cod:tempe/minVe'), -100.0)
		self.assertEqual(findXPath(r, 'cod:tempe/maxVe'), 100.0)
		self.assertEqual(findXPath(r, 'cod:tempe/steVe'), 0.5)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/st'))
		self.assertEqual(findXPath(r, 'cod:tempe/st'), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNT(self):
		dct = 	{ 'cod:tempe' : {
					'tarTe':	5.0
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, dct)
		self.assertEqual(rsc, RC.updated)
		r, rsc = RETRIEVE(fcntURL, TestFCNT.originator)		# retrieve fcnt again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/tarTe'))
		self.assertIsInstance(findXPath(r, 'cod:tempe/tarTe'), float)
		self.assertEqual(findXPath(r, 'cod:tempe/tarTe'), 5.0)
		self.assertEqual(findXPath(r, 'cod:tempe/curTe'), 23.0)
		self.assertEqual(findXPath(r, 'cod:tempe/st'), 1)
		self.assertGreater(findXPath(r, 'cod:tempe/lt'), findXPath(r, 'cod:tempe/ct'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTwithCnd(self):
		dct = 	{ 'cod:tempe' : {
					'cnd' : CND,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTwithWrongType(self):
		dct = 	{ 'cod:tempe' : {
					'tarTe':	'5.0'
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, dct)
		self.assertEqual(rsc, RC.badRequest)

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTwithUnkownAttribute(self):
		dct = 	{ 'cod:tempe' : {
					'wrong':	'aValue'
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTUnknown(self):
		dct = 	{ 'cod:unknown' : { 
					'rn'	: 'unknown',
					'cnd' 	: 'unknown', 
					'attr'	: 'aValuealue',
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTUnderFCNT(self):
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(fcntURL, TestFCNT.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTUnderFCNT(self):
		_, rsc = DELETE(f'{fcntURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTUnderFCNT(self):
		dct = 	{ 'cod:tempe' : { 
					'cnd' 	: CND, 
					'rn' : fcntRN,
				}}
		r, rsc = CREATE(fcntURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteFCNTUnderFCNT(self):
		_, rsc = DELETE(f'{fcntURL}/{fcntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteFCNT(self):
		_, rsc = DELETE(fcntURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)



def run():
	suite = unittest.TestSuite()
	suite.addTest(TestFCNT('test_createFCNT'))
	suite.addTest(TestFCNT('test_retrieveFCNT'))
	suite.addTest(TestFCNT('test_retrieveFCNTWithWrongOriginator'))
	suite.addTest(TestFCNT('test_attributesFCNT'))
	suite.addTest(TestFCNT('test_updateFCNT'))
	suite.addTest(TestFCNT('test_updateFCNTwithCnd'))
	suite.addTest(TestFCNT('test_updateFCNTwithWrongType'))
	suite.addTest(TestFCNT('test_updateFCNTwithUnkownAttribute'))
	suite.addTest(TestFCNT('test_createFCNTUnknown'))
	suite.addTest(TestFCNT('test_createCNTUnderFCNT'))
	suite.addTest(TestFCNT('test_deleteCNTUnderFCNT'))
	suite.addTest(TestFCNT('test_createFCNTUnderFCNT'))
	suite.addTest(TestFCNT('test_deleteFCNTUnderFCNT'))
	suite.addTest(TestFCNT('test_deleteFCNT'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)

