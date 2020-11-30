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

class TestFCNT_FCI(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}'

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
		self.assertIsNotNone(TestFCNT_FCI.cse)
		self.assertIsNotNone(TestFCNT_FCI.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curTe'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5,
					'mni'	: 10
				}}
		r, rsc = CREATE(aeURL, TestFCNT_FCI.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesFCNT(self):
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'cod:tempe/ty'), T.FCNT)
		self.assertEqual(findXPath(r, 'cod:tempe/pi'), findXPath(TestFCNT_FCI.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'cod:tempe/rn'), fcntRN)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/ct'))
		self.assertIsNotNone(findXPath(r, 'cod:tempe/lt'))
		self.assertIsNotNone(findXPath(r, 'cod:tempe/et'))
		self.assertIsNotNone(findXPath(r, 'cod:tempe/st'))
		self.assertEqual(findXPath(r, 'cod:tempe/cr'), TestFCNT_FCI.originator)
		self.assertEqual(findXPath(r, 'cod:tempe/cnd'), CND)
		self.assertEqual(findXPath(r, 'cod:tempe/curTe'), 23.0)
		self.assertIsNone(findXPath(r, 'cod:tempe/tarTe'))
		self.assertEqual(findXPath(r, 'cod:tempe/unit'), 1)
		self.assertEqual(findXPath(r, 'cod:tempe/minVe'), -100.0)
		self.assertEqual(findXPath(r, 'cod:tempe/maxVe'), 100.0)
		self.assertEqual(findXPath(r, 'cod:tempe/steVe'), 0.5)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/st'))
		self.assertEqual(findXPath(r, 'cod:tempe/st'), 0)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/mni'))
		self.assertEqual(findXPath(r, 'cod:tempe/mni'), 10)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cni'))
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 1)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cbs'))
		self.assertGreater(findXPath(r, 'cod:tempe/cbs'), 0)

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNT(self):
		dct = 	{ 'cod:tempe' : {
					'tarTe':   5.0,
					'curTe'	: 17.0,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.updated)
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)		# retrieve fcnt again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/tarTe'))
		self.assertIsInstance(findXPath(r, 'cod:tempe/tarTe'), float)
		self.assertEqual(findXPath(r, 'cod:tempe/tarTe'), 5.0)
		self.assertEqual(findXPath(r, 'cod:tempe/curTe'), 17.0)
		self.assertEqual(findXPath(r, 'cod:tempe/st'), 1)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 2)
		self.assertGreater(findXPath(r, 'cod:tempe/cbs'), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFCNTLaOl(self):
		r, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/curTe'))
		self.assertEqual(findXPath(r, 'cod:tempe/curTe'), 17.0)

		r, rsc = RETRIEVE(f'{fcntURL}/ol', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/curTe'))
		self.assertEqual(findXPath(r, 'cod:tempe/curTe'), 23.0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTMni(self):
		dct = 	{ 'cod:tempe' : {
					'mni':   1,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.updated)
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)		# retrieve fcnt again
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'cod:tempe/mni'), 1)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 1)
		self.assertEqual(findXPath(r, 'cod:tempe/st'), 2)

		rla, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)

		rol, rsc = RETRIEVE(f'{fcntURL}/ol', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)

		# al == ol ?
		self.assertEqual(findXPath(rla, 'cod:tempe/ri'), findXPath(rol, 'cod:tempe/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteFCNT(self):
		_, rsc = DELETE(fcntURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestFCNT_FCI('test_createFCNT'))
	suite.addTest(TestFCNT_FCI('test_attributesFCNT'))
	suite.addTest(TestFCNT_FCI('test_updateFCNT'))
	suite.addTest(TestFCNT_FCI('test_retrieveFCNTLaOl'))
	suite.addTest(TestFCNT_FCI('test_updateFCNTMni'))
	suite.addTest(TestFCNT_FCI('test_deleteFCNT'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)

