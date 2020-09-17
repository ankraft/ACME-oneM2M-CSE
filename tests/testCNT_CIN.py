#
#	testCNT_CIN.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CNT & CIN functionality
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


class TestCNT_CIN(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, 'Cannot retrieve CSEBase: %s' % cseURL

		jsn = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, jsn)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mni' : 3
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, jsn)
		assert rsc == RC.created, 'cannot create container'
		assert findXPath(cls.cnt, 'm2m:cnt/mni') == 3, 'mni is not correct'


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCIN(self):
		self.assertIsNotNone(TestCNT_CIN.cse)
		self.assertIsNotNone(TestCNT_CIN.ae)
		self.assertIsNotNone(TestCNT_CIN.cnt)
		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'aValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/ri'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		self.cinARi = findXPath(r, 'm2m:cin/ri')			# store ri

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 1)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addMoreCIN(self):
		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'bValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'bValue')

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 2)

		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'cValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'cValue')

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 3)


		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'dValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 3)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_rerieveCNTLa(self):
		r, rsc = RETRIEVE('%s/la' % cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_rerieveCNTOl(self):
		r, rsc = RETRIEVE('%s/ol' % cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'bValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_changeCNTMni(self):
		jsn = 	{ 'm2m:cnt' : {
					'mni' : 1
 				}}
		cnt, rsc = UPDATE(cntURL, TestCNT_CIN.originator, jsn)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(cnt)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mni'))
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mni'), 1)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/cni'))
		self.assertEqual(findXPath(cnt, 'm2m:cnt/cni'), 1)

		r, rsc = RETRIEVE('%s/la' % cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')

		r, rsc = RETRIEVE('%s/ol' % cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestCNT_CIN('test_addCIN'))
	suite.addTest(TestCNT_CIN('test_addMoreCIN'))
	suite.addTest(TestCNT_CIN('test_rerieveCNTLa'))
	suite.addTest(TestCNT_CIN('test_rerieveCNTOl'))
	suite.addTest(TestCNT_CIN('test_changeCNTMni'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
