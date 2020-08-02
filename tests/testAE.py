#
#	testAE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for AE functionality
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T
from init import *

class TestAE(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		TestAE.originator 	= None 	# actually the AE.aei
		TestAE.aeACPI 		= None
		TestAE.cse, rsc 	= RETRIEVE(cseURL, ORIGINATOR)


	@classmethod
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not


	def test_createAE(self):
		self.assertIsNotNone(TestAE.cse)
		jsn = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, jsn)
		self.assertEqual(rsc, C.rcCreated)
		TestAE.originator = findXPath(r, 'm2m:ae/aei')
		TestAE.aeACPI = findXPath(r, 'm2m:ae/acpi')
		self.assertIsNotNone(TestAE.originator)


	def test_createAEUnderAE(self):
		jsn = 	{ 'm2m:ae' : {
					'rn': '%s2' % aeRN, 
					'api': 'NMyApp2Id',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		r, rsc = CREATE(aeURL, 'C', T.AE, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	def test_retrieveAE(self):
		_, rsc = RETRIEVE(aeURL, TestAE.originator)
		self.assertEqual(rsc, C.rcOK)


	def test_retrieveAEWithWrongOriginator(self):
		_, rsc = RETRIEVE(aeURL, 'Cwrong')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	def test_attributesAE(self):
		r, rsc = RETRIEVE(aeURL, TestAE.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/aei'))
		self.assertEqual(findXPath(r, 'm2m:ae/ty'), T.AE)
		self.assertTrue(findXPath(r, 'm2m:ae/aei').startswith('C'))
		self.assertEqual(findXPath(r, 'm2m:ae/api'), 'NMyApp1Id')
		self.assertIsNotNone(findXPath(r, 'm2m:ae/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/et'))
		self.assertLessEqual(findXPath(r, 'm2m:ae/ct'), findXPath(r, 'm2m:ae/lt'))
		self.assertLess(findXPath(r, 'm2m:ae/ct'), findXPath(r, 'm2m:ae/et'))
		self.assertEqual(findXPath(r, 'm2m:ae/rr'), False)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/srv'))
		self.assertEqual(findXPath(r, 'm2m:ae/srv'), [ '3' ])
		self.assertIsNone(findXPath(r, 'm2m:ae/st'))
		self.assertEqual(findXPath(r, 'm2m:ae/pi'), findXPath(TestAE.cse,'m2m:cb/ri'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/acpi'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/acpi'), list)
		self.assertGreater(len(findXPath(r, 'm2m:ae/acpi')), 0)
		self.assertIsNone(findXPath(r, 'm2m:ae/st'))



	def test_updateAELbl(self):
		jsn = 	{ 'm2m:ae' : {
					'lbl' : [ 'aTag' ]
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		r, rsc = RETRIEVE(aeURL, TestAE.originator)		# retrieve updated ae again
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lbl'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/lbl'), list)
		self.assertGreater(len(findXPath(r, 'm2m:ae/lbl')), 0)
		self.assertTrue('aTag' in findXPath(r, 'm2m:ae/lbl'))


	def test_updateAETy(self):
		jsn = 	{ 'm2m:ae' : {
					'ty' : int(T.CSEBase)
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	def test_updateAEPi(self):
		jsn = 	{ 'm2m:ae' : {
					'pi' : 'wrongID'
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	def test_updateAEUnknownAttribute(self):
		jsn = 	{ 'm2m:ae' : {
					'unknown' : 'unknown'
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, jsn)
		self.assertEqual(rsc, C.rcBadRequest)

	def test_deleteAEByUnknownOriginator(self):
		_, rsc = DELETE(aeURL, 'Cwrong')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	def test_deleteAEByAssignedOriginator(self):
		_, rsc = DELETE(aeURL, TestAE.originator)
		self.assertEqual(rsc, C.rcDeleted)


	def test_retrieveAEACP(self):
		self.assertIsNotNone(TestAE.aeACPI)
		self.assertIsInstance(TestAE.aeACPI, list)
		self.assertGreater(len(TestAE.aeACPI), 0)
		_, rsc = RETRIEVE('%s%s' % (URL, TestAE.aeACPI[0]), TestAE.originator)	# AE's own originator fails
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)
		acp, rsc = RETRIEVE('%s%s' % (URL, TestAE.aeACPI[0]), ORIGINATOR)	# but Admin should succeed
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(acp, 'm2m:acp/rn'), 'acp_%s' % aeRN)
		for acr in findXPath(acp, 'm2m:acp/pv/acr'):
			if TestAE.originator in acr['acor']:
				break
		else:
			self.fail('Originator not in ACP:acr:acor')


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestAE('test_createAE'))
	suite.addTest(TestAE('test_createAEUnderAE'))
	suite.addTest(TestAE('test_retrieveAE'))
	suite.addTest(TestAE('test_retrieveAEWithWrongOriginator'))
	suite.addTest(TestAE('test_attributesAE'))
	suite.addTest(TestAE('test_updateAELbl'))
	suite.addTest(TestAE('test_updateAETy'))
	suite.addTest(TestAE('test_updateAEPi'))
	suite.addTest(TestAE('test_updateAEUnknownAttribute'))
	suite.addTest(TestAE('test_retrieveAEACP'))
	suite.addTest(TestAE('test_deleteAEByUnknownOriginator'))
	suite.addTest(TestAE('test_deleteAEByAssignedOriginator'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
