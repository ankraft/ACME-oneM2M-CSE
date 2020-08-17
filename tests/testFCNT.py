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
from Types import ResourceTypes as T
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
		assert rsc == C.rcOK, 'cannot retrieve CSEBase'

		jsn = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
					'rr': False,
					'srv': [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, jsn)	# AE to work under
		assert rsc == C.rcCreated, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNT(self):
		self.assertIsNotNone(TestFCNT.cse)
		self.assertIsNotNone(TestFCNT.ae)
		jsn = 	{ 'hd:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, jsn)
		self.assertEqual(rsc, C.rcCreated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFCNT(self):
		_, rsc = RETRIEVE(fcntURL, TestFCNT.originator)
		self.assertEqual(rsc, C.rcOK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFCNTWithWrongOriginator(self):
		_, rsc = RETRIEVE(fcntURL, 'Cwrong')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesFCNT(self):
		r, rsc = RETRIEVE(fcntURL, TestFCNT.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'hd:tempe/ty'), T.FCNT)
		self.assertEqual(findXPath(r, 'hd:tempe/pi'), findXPath(TestFCNT.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'hd:tempe/rn'), fcntRN)
		self.assertIsNotNone(findXPath(r, 'hd:tempe/ct'))
		self.assertIsNotNone(findXPath(r, 'hd:tempe/lt'))
		self.assertIsNotNone(findXPath(r, 'hd:tempe/et'))
		self.assertEqual(findXPath(r, 'hd:tempe/cr'), TestFCNT.originator)
		self.assertEqual(findXPath(r, 'hd:tempe/cnd'), CND)
		self.assertEqual(findXPath(r, 'hd:tempe/curT0'), 23.0)
		self.assertIsNone(findXPath(r, 'hd:tempe/tarTe'))
		self.assertEqual(findXPath(r, 'hd:tempe/unit'), 1)
		self.assertEqual(findXPath(r, 'hd:tempe/minVe'), -100.0)
		self.assertEqual(findXPath(r, 'hd:tempe/maxVe'), 100.0)
		self.assertEqual(findXPath(r, 'hd:tempe/steVe'), 0.5)
		self.assertIsNotNone(findXPath(r, 'hd:tempe/st'))
		self.assertEqual(findXPath(r, 'hd:tempe/st'), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNT(self):
		jsn = 	{ 'hd:tempe' : {
					'tarTe':	5.0
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		r, rsc = RETRIEVE(fcntURL, TestFCNT.originator)		# retrieve fcnt again
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'hd:tempe/tarTe'))
		self.assertIsInstance(findXPath(r, 'hd:tempe/tarTe'), float)
		self.assertEqual(findXPath(r, 'hd:tempe/tarTe'), 5.0)
		self.assertEqual(findXPath(r, 'hd:tempe/curT0'), 23.0)
		self.assertEqual(findXPath(r, 'hd:tempe/st'), 1)
		self.assertGreater(findXPath(r, 'hd:tempe/lt'), findXPath(r, 'hd:tempe/ct'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTwithCnd(self):
		jsn = 	{ 'hd:tempe' : {
					'cnd' : CND,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTwithWrongType(self):
		jsn = 	{ 'hd:tempe' : {
					'tarTe':	'5.0'
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, jsn)
		self.assertEqual(rsc, C.rcBadRequest)

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTwithUnkownAttribute(self):
		jsn = 	{ 'hd:tempe' : {
					'wrong':	'aValue'
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTUnknown(self):
		jsn = 	{ 'hd:unknown' : { 
					'rn'	: 'unknown',
					'cnd' 	: 'unknown', 
					'attr'	: 'aValuealue',
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTUnderFCNT(self):
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(fcntURL, TestFCNT.originator, T.CNT, jsn)
		self.assertEqual(rsc, C.rcCreated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTUnderFCNT(self):
		_, rsc = DELETE('%s/%s' % (fcntURL, cntRN), ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTUnderFCNT(self):
		jsn = 	{ 'hd:tempe' : { 
					'cnd' 	: CND, 
					'rn' : fcntRN,
				}}
		r, rsc = CREATE(fcntURL, TestFCNT.originator, T.FCNT, jsn)
		self.assertEqual(rsc, C.rcCreated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteFCNTUnderFCNT(self):
		_, rsc = DELETE('%s/%s' % (fcntURL, fcntRN), ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteFCNT(self):
		_, rsc = DELETE(fcntURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)



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
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)

