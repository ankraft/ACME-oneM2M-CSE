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
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *

nodeID  = 'urn:sn:1234'
nod2RN 	= 'test2NOD'
nod2URL = f'{cseURL}/{nod2RN}'


class TestNOD(unittest.TestCase):

	cse  		= None
	ae 			= None
	nodeRI 		= None
	aeRI 		= None
	originator	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}'
		

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not
		DELETE(nod2URL, ORIGINATOR)	# Just delete the Node 2 and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNOD(self) -> None:
		""" Create <NOD> """
		self.assertIsNotNone(TestNOD.cse)
		dct = 	{ 'm2m:nod' : { 
					'rn' 	: nodRN,
					'ni'	: nodeID
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/ri'))
		TestNOD.nodeRI = findXPath(r, 'm2m:nod/ri')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveNOD(self) -> None:
		""" Retrieve <NOD> """
		_, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveNODWithWrongOriginator(self) -> None:
		""" Retrieve <NOD> with wrong originator -> Fail """
		_, rsc = RETRIEVE(nodURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesNOD(self) -> None:
		""" Retrieve <NOD> and test attributes """
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
	def test_updateNODLbl(self) -> None:
		""" Update <NOD> lbl """
		dct = 	{ 'm2m:nod' : {
					'lbl' : [ 'aTag' ]
				}}
		r, rsc = UPDATE(nodURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		r, rsc = RETRIEVE(nodURL, ORIGINATOR)		# retrieve updated ae again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/lbl'))
		self.assertIsInstance(findXPath(r, 'm2m:nod/lbl'), list)
		self.assertGreater(len(findXPath(r, 'm2m:nod/lbl')), 0)
		self.assertTrue('aTag' in findXPath(r, 'm2m:nod/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateNODUnknownAttribute(self) -> None:
		""" Update <NOD> with unknown attribute -> Fail """
		dct = 	{ 'm2m:nod' : {
					'unknown' : 'unknown'
				}}
		_, rsc = UPDATE(nodURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEForNOD(self) -> None:
		""" Create <AE> for <NOD> & test link """
		dct = 	{ 'm2m:ae' : {
			'rn'	: aeRN, 
			'api'	: 'NMyApp1Id',
		 	'rr'	: False,
		 	'srv'	: [ '3' ],
		 	'nl' 	: TestNOD.nodeRI
		}}
		TestNOD.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(TestNOD.ae, 'm2m:ae/nl'))
		self.assertEqual(findXPath(TestNOD.ae, 'm2m:ae/nl'), TestNOD.nodeRI)
		self.assertIsNotNone(findXPath(TestNOD.ae, 'm2m:ae/ri'))
		self.assertIsNotNone(findXPath(TestNOD.ae, 'm2m:ae/aei'))
		TestNOD.aeRI = findXPath(TestNOD.ae, 'm2m:ae/ri')
		TestNOD.originator = findXPath(TestNOD.ae, 'm2m:ae/aei')

		nod, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(nod, 'm2m:nod/hael'), nod)
		self.assertIn(findXPath(TestNOD.ae, 'm2m:ae/ri'), findXPath(nod, 'm2m:nod/hael'))	# ae.ri in nod.hael?


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEForNOD(self) -> None:
		""" Delete <AE> for <NOD> & test link """
		_, rsc = DELETE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)

		nod, rsc = RETRIEVE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNone(findXPath(nod, 'm2m:nod/hael'))	# should have been the only AE, so the attribute should now be removed


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_moveAEToNOD2(self) -> None:
		""" Create second <NOD> and move <AE> """
		# create AE again
		self.test_createAEForNOD()

		# create second node
		dct = 	{ 'm2m:nod' : { 
			'rn' 	: nod2RN,
			'ni'	: 'second'
		}}
		nod2, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(nod2, 'm2m:nod/ri'))
		self.assertEqual(findXPath(nod2, 'm2m:nod/rn'), nod2RN)
		node2RI = findXPath(nod2, 'm2m:nod/ri')

		# move AE to second NOD
		dct = 	{ 'm2m:ae' : { 
			'nl' : node2RI
		}}
		r, rsc = UPDATE(aeURL, TestNOD.originator, dct)
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
	def test_deleteNOD2(self) -> None:
		""" Delete second <NOD> """
		_, rsc = DELETE(nod2URL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)

		# Check AE
		ae, rsc = RETRIEVE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNone(findXPath(ae, 'm2m:ae/nl'))	# should have been the only AE, so the attribute should now be removed


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteNOD(self) -> None:
		""" Delete <NOD> """
		_, rsc = DELETE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNODEmptyHael(self) -> None:
		""" Create <NOD> with empty hael list -> Fail"""
		self.assertIsNotNone(TestNOD.cse)
		dct = 	{ 'm2m:nod' : { 
					'rn' 	: nodRN,
					'ni'	: nodeID,
					'hael'	: []
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, dct)
		self.assertEqual(rsc, RC.badRequest, r)


def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
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
	suite.addTest(TestNOD('test_createNODEmptyHael'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
