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
from Types import ResourceTypes as T, ResponseCode as RC
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

class TestAE(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		TestAE.originator 	= None 	# actually the AE.aei
		TestAE.aeACPI 		= None
		TestAE.cse, rsc 	= RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, 'Cannot retrieve CSEBase: %s' % cseURL


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAE(self):
		jsn = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, jsn)
		self.assertEqual(rsc, RC.created)
		TestAE.originator = findXPath(r, 'm2m:ae/aei')
		TestAE.aeACPI = findXPath(r, 'm2m:ae/acpi')
		self.assertIsNotNone(TestAE.originator)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEUnderAE(self):
		jsn = 	{ 'm2m:ae' : {
					'rn': '%s2' % aeRN, 
					'api': 'NMyApp2Id',
				 	'rr': False,
				 	'srv': [ '3' ]
				}}
		r, rsc = CREATE(aeURL, 'C', T.AE, jsn)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveAE(self):
		_, rsc = RETRIEVE(aeURL, TestAE.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveAEWithWrongOriginator(self):
		_, rsc = RETRIEVE(aeURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesAE(self):
		r, rsc = RETRIEVE(aeURL, TestAE.originator)
		self.assertEqual(rsc, RC.OK)
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


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAELbl(self):
		jsn = 	{ 'm2m:ae' : {
					'lbl' : [ 'aTag' ]
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, jsn)
		self.assertEqual(rsc, RC.updated)
		r, rsc = RETRIEVE(aeURL, TestAE.originator)		# retrieve updated ae again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lbl'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/lbl'), list)
		self.assertGreater(len(findXPath(r, 'm2m:ae/lbl')), 0)
		self.assertTrue('aTag' in findXPath(r, 'm2m:ae/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAETy(self):
		jsn = 	{ 'm2m:ae' : {
					'ty' : int(T.CSEBase)
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, jsn)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEPi(self):
		jsn = 	{ 'm2m:ae' : {
					'pi' : 'wrongID'
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, jsn)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAEUnknownAttribute(self):
		jsn = 	{ 'm2m:ae' : {
					'unknown' : 'unknown'
				}}
		r, rsc = UPDATE(aeURL, TestAE.originator, jsn)
		self.assertEqual(rsc, RC.badRequest)

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEByUnknownOriginator(self):
		_, rsc = DELETE(aeURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEByAssignedOriginator(self):
		_, rsc = DELETE(aeURL, TestAE.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveAEACP(self):
		self.assertIsNotNone(TestAE.aeACPI)
		self.assertIsInstance(TestAE.aeACPI, list)
		self.assertGreater(len(TestAE.aeACPI), 0)
		_, rsc = RETRIEVE('%s%s' % (URL, TestAE.aeACPI[0]), TestAE.originator)	# AE's own originator fails
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)
		acp, rsc = RETRIEVE('%s%s' % (URL, TestAE.aeACPI[0]), ORIGINATOR)	# but Admin should succeed
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(acp, 'm2m:acp/rn'), 'acp_%s' % aeRN)
		for acr in findXPath(acp, 'm2m:acp/pv/acr'):
			if TestAE.originator in acr['acor']:
				break
		else:
			self.fail('Originator not in ACP:acr:acor')


# TODO register multiple AEs

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
