#
#	testNOD.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for NOD functionality & notifications
#

import unittest, sys
import requests
sys.path.append('../acme')
from Constants import Constants as C
from init import *

nodeID = 'urn:sn:1234'

class TestNOD(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)

	@classmethod
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not


	def test_createNOD(self):
		self.assertIsNotNone(TestNOD.cse)
		jsn = 	{ 'm2m:nod' : { 
					'rn' 	: nodRN,
					'ni'	: nodeID
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, C.tNOD, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/ri'))
		TestNOD.nodeRI = findXPath(r, 'm2m:nod/ri')


	def test_retrieveNOD(self):
		_, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)


	def test_retrieveNODWithWrongOriginator(self):
		_, rsc = RETRIEVE(nodURL, 'Cwrong')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	def test_attributesNOD(self):
		r, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:nod/ty'), C.tNOD)
		self.assertEqual(findXPath(r, 'm2m:nod/pi'), findXPath(TestNOD.cse,'m2m:cb/ri'))
		self.assertEqual(findXPath(r, 'm2m:nod/rn'), nodRN)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:nod/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:nod/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:nod/ni'))
		self.assertEqual(findXPath(r, 'm2m:nod/ni'), nodeID)


	def test_updateNODLbl(self):
		jsn = 	{ 'm2m:nod' : {
					'lbl' : [ 'aTag' ]
				}}
		r, rsc = UPDATE(nodURL, ORIGINATOR, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		r, rsc = RETRIEVE(nodURL, ORIGINATOR)		# retrieve updated ae again
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/lbl'))
		self.assertIsInstance(findXPath(r, 'm2m:nod/lbl'), list)
		self.assertGreater(len(findXPath(r, 'm2m:nod/lbl')), 0)
		self.assertTrue('aTag' in findXPath(r, 'm2m:nod/lbl'))


	def test_updateNODUnknownAttribute(self):
		jsn = 	{ 'm2m:nod' : {
					'unknown' : 'unknown'
				}}
		r, rsc = UPDATE(nodURL, ORIGINATOR, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	def test_createAEForNOD(self):
		jsn = 	{ 'm2m:ae' : {
			'rn'	: aeRN, 
			'api'	: 'NMyApp1Id',
		 	'rr'	: False,
		 	'srv'	: [ '3' ],
		 	'nl' 	: TestNOD.nodeRI
		}}
		ae, rsc = CREATE(cseURL, 'C', C.tAE, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/nl'))
		self.assertEqual(findXPath(ae, 'm2m:ae/nl'), TestNOD.nodeRI)
		self.assertIsNotNone(findXPath(ae, 'm2m:ae/ri'))
		TestNOD.aeRI = findXPath(ae, 'm2m:ae/ri')

		nod, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(nod, 'm2m:nod/hael'))
		self.assertIn(findXPath(ae, 'm2m:ae/ri'), findXPath(nod, 'm2m:nod/hael'))	# ae.ri in nod.hael?


	def test_deleteAEForNOD(self):
		_, rsc = DELETE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)

		nod, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNone(findXPath(nod, 'm2m:nod/hael'))	# should have been the only AE, so the attribute should now be removed

# TODO create a second node and move the AE to that node. Check the NL and HAELs
# TODO Delete second Node, check AE.nl


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestNOD('test_createNOD'))
	suite.addTest(TestNOD('test_retrieveNOD'))
	suite.addTest(TestNOD('test_retrieveNODWithWrongOriginator'))
	suite.addTest(TestNOD('test_attributesNOD'))
	suite.addTest(TestNOD('test_updateNODLbl'))
	suite.addTest(TestNOD('test_updateNODUnknownAttribute'))
	suite.addTest(TestNOD('test_createAEForNOD'))
	suite.addTest(TestNOD('test_deleteAEForNOD'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures)

if __name__ == '__main__':
	_, errors = run()
	sys.exit(errors)
