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
from Types import ResourceTypes as T, ResponseCode as RC
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)


nod2RN 	= 'test2NOD'
nod2URL = f'{cseURL}/{nod2RN}'


class TestNOD(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}'
		

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not
		DELETE(nod2URL, ORIGINATOR)	# Just delete the Node 2 and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNOD(self):
		self.assertIsNotNone(TestNOD.cse)
		jsn = 	{ 'm2m:nod' : { 
					'rn' 	: nodRN,
					'ni'	: nodeID
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/ri'))
		TestNOD.nodeRI = findXPath(r, 'm2m:nod/ri')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveNOD(self):
		_, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveNODWithWrongOriginator(self):
		_, rsc = RETRIEVE(nodURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesNOD(self):
		r, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:nod/ty'), T.NOD)
		self.assertEqual(findXPath(r, 'm2m:nod/pi'), findXPath(TestNOD.cse,'m2m:cb/ri'))
		self.assertEqual(findXPath(r, 'm2m:nod/rn'), nodRN)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:nod/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:nod/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:nod/ni'))
		self.assertEqual(findXPath(r, 'm2m:nod/ni'), nodeID)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateNODLbl(self):
		jsn = 	{ 'm2m:nod' : {
					'lbl' : [ 'aTag' ]
				}}
		r, rsc = UPDATE(nodURL, ORIGINATOR, jsn)
		self.assertEqual(rsc, RC.updated)
		r, rsc = RETRIEVE(nodURL, ORIGINATOR)		# retrieve updated ae again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/lbl'))
		self.assertIsInstance(findXPath(r, 'm2m:nod/lbl'), list)
		self.assertGreater(len(findXPath(r, 'm2m:nod/lbl')), 0)
		self.assertTrue('aTag' in findXPath(r, 'm2m:nod/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateNODUnknownAttribute(self):
		jsn = 	{ 'm2m:nod' : {
					'unknown' : 'unknown'
				}}
		r, rsc = UPDATE(nodURL, ORIGINATOR, jsn)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEForNOD(self):
		jsn = 	{ 'm2m:ae' : {
			'rn'	: aeRN, 
			'api'	: 'NMyApp1Id',
		 	'rr'	: False,
		 	'srv'	: [ '3' ],
		 	'nl' 	: TestNOD.nodeRI
		}}
		TestNOD.ae, rsc = CREATE(cseURL, 'C', T.AE, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(TestNOD.ae, 'm2m:ae/nl'))
		self.assertEqual(findXPath(TestNOD.ae, 'm2m:ae/nl'), TestNOD.nodeRI)
		self.assertIsNotNone(findXPath(TestNOD.ae, 'm2m:ae/ri'))
		self.assertIsNotNone(findXPath(TestNOD.ae, 'm2m:ae/aei'))
		TestNOD.aeRI = findXPath(TestNOD.ae, 'm2m:ae/ri')
		TestNOD.originator = findXPath(TestNOD.ae, 'm2m:ae/aei')

		nod, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(nod, 'm2m:nod/hael'))
		self.assertIn(findXPath(TestNOD.ae, 'm2m:ae/ri'), findXPath(nod, 'm2m:nod/hael'))	# ae.ri in nod.hael?


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEForNOD(self):
		_, rsc = DELETE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)

		nod, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNone(findXPath(nod, 'm2m:nod/hael'))	# should have been the only AE, so the attribute should now be removed


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_moveAEToNOD2(self):
		# create AE again
		self.test_createAEForNOD()

		# create second node
		jsn = 	{ 'm2m:nod' : { 
			'rn' 	: nod2RN,
			'ni'	: 'second'
		}}
		nod2, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(nod2, 'm2m:nod/ri'))
		self.assertEqual(findXPath(nod2, 'm2m:nod/rn'), nod2RN)
		node2RI = findXPath(nod2, 'm2m:nod/ri')

		# move AE to second NOD
		jsn = 	{ 'm2m:ae' : { 
			'nl' : node2RI
		}}
		r, rsc = UPDATE(aeURL, TestNOD.originator, jsn)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/nl'))
		self.assertEqual(findXPath(r, 'm2m:ae/nl'), node2RI)

		# Check first NOD
		nod, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNone(findXPath(nod, 'm2m:nod/hael'))	# should have been the only AE, so the attribute should now be removed

		# Check second NOD
		nod2, rsc = RETRIEVE(nod2URL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(nod2, 'm2m:nod/hael')) 	
		self.assertEqual(len(findXPath(nod2, 'm2m:nod/hael')), 1)
		self.assertIn(TestNOD.aeRI, findXPath(nod2, 'm2m:nod/hael'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteNOD2(self):
		_, rsc = DELETE(nod2URL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)

		# Check AE
		ae, rsc = RETRIEVE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNone(findXPath(ae, 'm2m:ae/nl'))	# should have been the only AE, so the attribute should now be removed


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteNOD(self):
		_, rsc = DELETE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


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
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
