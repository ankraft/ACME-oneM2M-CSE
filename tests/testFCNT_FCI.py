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

CND = 'org.onem2m.home.moduleclass.temperature'

class TestFCNT_FCI(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
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
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	def test_createFCNT(self):
		self.assertIsNotNone(TestFCNT_FCI.cse)
		self.assertIsNotNone(TestFCNT_FCI.ae)
		jsn = 	{ 'hd:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5,
					'mni'	: 10
				}}
		r, rsc = CREATE(aeURL, TestFCNT_FCI.originator, T.FCNT, jsn)
		self.assertEqual(rsc, C.rcCreated)


	def test_attributesFCNT(self):
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'hd:tempe/ty'), T.FCNT)
		self.assertEqual(findXPath(r, 'hd:tempe/pi'), findXPath(TestFCNT_FCI.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'hd:tempe/rn'), fcntRN)
		self.assertIsNotNone(findXPath(r, 'hd:tempe/ct'))
		self.assertIsNotNone(findXPath(r, 'hd:tempe/lt'))
		self.assertIsNotNone(findXPath(r, 'hd:tempe/et'))
		self.assertIsNotNone(findXPath(r, 'hd:tempe/st'))
		self.assertEqual(findXPath(r, 'hd:tempe/cr'), TestFCNT_FCI.originator)
		self.assertEqual(findXPath(r, 'hd:tempe/cnd'), CND)
		self.assertEqual(findXPath(r, 'hd:tempe/curT0'), 23.0)
		self.assertIsNone(findXPath(r, 'hd:tempe/tarTe'))
		self.assertEqual(findXPath(r, 'hd:tempe/unit'), 1)
		self.assertEqual(findXPath(r, 'hd:tempe/minVe'), -100.0)
		self.assertEqual(findXPath(r, 'hd:tempe/maxVe'), 100.0)
		self.assertEqual(findXPath(r, 'hd:tempe/steVe'), 0.5)
		self.assertIsNotNone(findXPath(r, 'hd:tempe/st'))
		self.assertEqual(findXPath(r, 'hd:tempe/st'), 0)
		self.assertIsNotNone(findXPath(r, 'hd:tempe/mni'))
		self.assertEqual(findXPath(r, 'hd:tempe/mni'), 10)
		self.assertIsNotNone(findXPath(r, 'hd:tempe/cni'))
		self.assertEqual(findXPath(r, 'hd:tempe/cni'), 1)

	def test_updateFCNT(self):
		jsn = 	{ 'hd:tempe' : {
					'tarTe':   5.0,
					'curT0'	: 17.0,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)		# retrieve fcnt again
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'hd:tempe/tarTe'))
		self.assertIsInstance(findXPath(r, 'hd:tempe/tarTe'), float)
		self.assertEqual(findXPath(r, 'hd:tempe/tarTe'), 5.0)
		self.assertEqual(findXPath(r, 'hd:tempe/curT0'), 17.0)
		self.assertEqual(findXPath(r, 'hd:tempe/st'), 1)
		self.assertEqual(findXPath(r, 'hd:tempe/cni'), 2)


	def test_retrieveFCNTLaOl(self):
		r, rsc = RETRIEVE('%s/la' % fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'hd:tempe/curT0'))
		self.assertEqual(findXPath(r, 'hd:tempe/curT0'), 17.0)

		r, rsc = RETRIEVE('%s/ol' % fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'hd:tempe/curT0'))
		self.assertEqual(findXPath(r, 'hd:tempe/curT0'), 23.0)


	def test_updateFCNTMni(self):
		jsn = 	{ 'hd:tempe' : {
					'mni':   1,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)		# retrieve fcnt again
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'hd:tempe/mni'), 1)
		self.assertEqual(findXPath(r, 'hd:tempe/cni'), 1)
		self.assertEqual(findXPath(r, 'hd:tempe/st'), 2)

		rla, rsc = RETRIEVE('%s/la' % fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(r)

		rol, rsc = RETRIEVE('%s/ol' % fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(r)

		# al == ol ?
		self.assertEqual(findXPath(rla, 'hd:tempe/ri'), findXPath(rol, 'hd:tempe/ri'))


	def test_deleteFCNT(self):
		_, rsc = DELETE(fcntURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestFCNT_FCI('test_createFCNT'))
	suite.addTest(TestFCNT_FCI('test_attributesFCNT'))
	suite.addTest(TestFCNT_FCI('test_updateFCNT'))
	suite.addTest(TestFCNT_FCI('test_retrieveFCNTLaOl'))
	suite.addTest(TestFCNT_FCI('test_updateFCNTMni'))
	suite.addTest(TestFCNT_FCI('test_deleteFCNT'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)

