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

nodeID  = 'urn:sn:1234'
nod2RN 	= 'test2NOD'
nod2URL = '%s/%s' % (cseURL, nod2RN)


class TestNOD(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)

	@classmethod
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not
		DELETE(nod2URL, ORIGINATOR)	# Just delete the Node 2 and everything below it. Ignore whether it exists or not


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
		TestNOD.ae, rsc = CREATE(cseURL, 'C', C.tAE, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(TestNOD.ae, 'm2m:ae/nl'))
		self.assertEqual(findXPath(TestNOD.ae, 'm2m:ae/nl'), TestNOD.nodeRI)
		self.assertIsNotNone(findXPath(TestNOD.ae, 'm2m:ae/ri'))
		self.assertIsNotNone(findXPath(TestNOD.ae, 'm2m:ae/aei'))
		TestNOD.aeRI = findXPath(TestNOD.ae, 'm2m:ae/ri')
		TestNOD.originator = findXPath(TestNOD.ae, 'm2m:ae/aei')

		nod, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(nod, 'm2m:nod/hael'))
		self.assertIn(findXPath(TestNOD.ae, 'm2m:ae/ri'), findXPath(nod, 'm2m:nod/hael'))	# ae.ri in nod.hael?


	def test_deleteAEForNOD(self):
		_, rsc = DELETE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)

		nod, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNone(findXPath(nod, 'm2m:nod/hael'))	# should have been the only AE, so the attribute should now be removed


	def test_moveAEToNOD2(self):
		# create AE again
		self.test_createAEForNOD()

		# create second node
		jsn = 	{ 'm2m:nod' : { 
			'rn' 	: nod2RN,
			'ni'	: 'second'
		}}
		nod2, rsc = CREATE(cseURL, ORIGINATOR, C.tNOD, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(nod2, 'm2m:nod/ri'))
		self.assertEqual(findXPath(nod2, 'm2m:nod/rn'), nod2RN)
		node2RI = findXPath(nod2, 'm2m:nod/ri')

		# move AE to second NOD
		jsn = 	{ 'm2m:ae' : { 
			'nl' : node2RI
		}}
		r, rsc = UPDATE(aeURL, TestNOD.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/nl'))
		self.assertEqual(findXPath(r, 'm2m:ae/nl'), node2RI)

		# Check first NOD
		nod, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNone(findXPath(nod, 'm2m:nod/hael'))	# should have been the only AE, so the attribute should now be removed

		# Check second NOD
		nod2, rsc = RETRIEVE(nod2URL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(nod2, 'm2m:nod/hael')) 	
		self.assertEqual(len(findXPath(nod2, 'm2m:nod/hael')), 1)
		self.assertIn(TestNOD.aeRI, findXPath(nod2, 'm2m:nod/hael'))


	def test_deleteNOD2(self):
		_, rsc = DELETE(nod2URL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)

		# Check AE
		ae, rsc = RETRIEVE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNone(findXPath(ae, 'm2m:ae/nl'))	# should have been the only AE, so the attribute should now be removed


	def test_deleteNOD(self):
		_, rsc = DELETE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)


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
	suite.addTest(TestNOD('test_moveAEToNOD2'))
	suite.addTest(TestNOD('test_deleteNOD2'))
	suite.addTest(TestNOD('test_deleteNOD'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures)


if __name__ == '__main__':
	_, errors = run()
	sys.exit(errors)
