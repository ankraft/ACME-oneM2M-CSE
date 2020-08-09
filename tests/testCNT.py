#
#	testCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CNT functionality
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

class TestCNT(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == C.rcOK, 'Cannot retrieve CSEBase: %s' % cseURL

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
		DELETE('%s/%s' % (cseURL, cntRN), ORIGINATOR)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNT(self):
		self.assertIsNotNone(TestCNT.cse)
		self.assertIsNotNone(TestCNT.ae)
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(aeURL, TestCNT.originator, T.CNT, jsn)
		self.assertEqual(rsc, C.rcCreated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNT(self):
		_, rsc = RETRIEVE(cntURL, TestCNT.originator)
		self.assertEqual(rsc, C.rcOK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTWithWrongOriginator(self):
		_, rsc = RETRIEVE(cntURL, 'Cwrong')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesCNT(self):
		r, rsc = RETRIEVE(cntURL, TestCNT.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:cnt/ty'), T.CNT)
		self.assertEqual(findXPath(r, 'm2m:cnt/pi'), findXPath(TestCNT.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/st'))
		self.assertEqual(findXPath(r, 'm2m:cnt/cr'), TestCNT.originator)
		self.assertEqual(findXPath(r, 'm2m:cnt/cbs'), 0)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 0)
		self.assertGreater(findXPath(r, 'm2m:cnt/mbs'), 0)
		self.assertGreater(findXPath(r, 'm2m:cnt/mni'), 0)
		self.assertIsNone(findXPath(r, 'm2m:cnt/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNT(self):
		jsn = 	{ 'm2m:cnt' : {
					'lbl' : [ 'aTag' ],
					'mni' : 10,
					'mbs' : 9999
 				}}
		cnt, rsc = UPDATE(cntURL, TestCNT.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		cnt, rsc = RETRIEVE(cntURL, TestCNT.originator)		# retrieve cnt again
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/lbl'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/lbl'), list)
		self.assertGreater(len(findXPath(cnt, 'm2m:cnt/lbl')), 0)
		self.assertTrue('aTag' in findXPath(cnt, 'm2m:cnt/lbl'))
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mni'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/mni'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mni'), 10)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mbs'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/mbs'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mbs'), 9999)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/st'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/st'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/st'), 1)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTTy(self):
		jsn = 	{ 'm2m:cnt' : {
					'ty' : T.CSEBase
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTPi(self):
		jsn = 	{ 'm2m:cnt' : {
					'pi' : 'wrongID'
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTUnknownAttribute(self):
		jsn = 	{ 'm2m:cnt' : {
					'unknown' : 'unknown'
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWrongMNI(self):
		jsn = 	{ 'm2m:cnt' : {
					'mni' : -1
				}}
		r, rsc = UPDATE(cntURL, TestCNT.originator, jsn)
		self.assertEqual(rsc, C.rcBadRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTUnderCNT(self):
		self.assertIsNotNone(TestCNT.cse)
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(cntURL, TestCNT.originator, T.CNT, jsn) 
		self.assertEqual(rsc, C.rcCreated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTUnderCNT(self):
		_, rsc = RETRIEVE('%s/%s' % (cntURL, cntRN), ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTUnderCNT(self):
		_, rsc = DELETE('%s/%s' % (cntURL, cntRN), ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTByUnknownOriginator(self):
		_, rsc = DELETE(cntURL, 'Cwrong')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTByAssignedOriginator(self):
		_, rsc = DELETE(cntURL, TestCNT.originator)
		self.assertEqual(rsc, C.rcDeleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTUnderCSE(self):
		self.assertIsNotNone(TestCNT.cse)
		jsn = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, jsn) # With Admin originator
		self.assertEqual(rsc, C.rcCreated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTUnderCSE(self):
		_, rsc = RETRIEVE('%s/%s' % (cseURL, cntRN), ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTUnderCSE(self):
		_, rsc = DELETE('%s/%s' % (cseURL, cntRN), ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestCNT('test_createCNT'))
	suite.addTest(TestCNT('test_retrieveCNT'))
	suite.addTest(TestCNT('test_retrieveCNTWithWrongOriginator'))
	suite.addTest(TestCNT('test_attributesCNT'))
	suite.addTest(TestCNT('test_updateCNT'))
	suite.addTest(TestCNT('test_updateCNTTy'))
	suite.addTest(TestCNT('test_updateCNTPi'))
	suite.addTest(TestCNT('test_updateCNTUnknownAttribute'))
	suite.addTest(TestCNT('test_updateCNTWrongMNI'))
	suite.addTest(TestCNT('test_createCNTUnderCNT'))
	suite.addTest(TestCNT('test_retrieveCNTUnderCNT'))
	suite.addTest(TestCNT('test_deleteCNTUnderCNT'))
	suite.addTest(TestCNT('test_deleteCNTByUnknownOriginator'))
	suite.addTest(TestCNT('test_deleteCNTByAssignedOriginator'))
	suite.addTest(TestCNT('test_createCNTUnderCSE'))
	suite.addTest(TestCNT('test_retrieveCNTUnderCSE'))
	suite.addTest(TestCNT('test_deleteCNTUnderCSE'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
