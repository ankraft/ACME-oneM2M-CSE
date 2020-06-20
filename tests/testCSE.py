#
#	testCSE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CSE functionality
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from init import *

class TestCSE(unittest.TestCase):

	def test_retrieveCSE(self):
		_, rsc = RETRIEVE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)


	def test_retrieveCSEWithWrongOriginator(self):
		_, rsc = RETRIEVE(cseURL, 'CWron')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	def test_cseAttributes(self):
		r, rsc = RETRIEVE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:cb/csi')[0], '/')
		self.assertEqual(findXPath(r, 'm2m:cb/csi'), CSEID)
		self.assertEqual(findXPath(r, 'm2m:cb/pi'), '')
		self.assertEqual(findXPath(r, 'm2m:cb/rr'), False)
		self.assertEqual(findXPath(r, 'm2m:cb/rn'), CSERN)
		self.assertEqual(findXPath(r, 'm2m:cb/ty'), 5)
		self.assertEqual(findXPath(r, 'm2m:cb/ri'), CSEID[1:])
		self.assertIsNotNone(findXPath(r, 'm2m:cb/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:cb/cst'))
		self.assertIsNotNone(findXPath(r, 'm2m:cb/srt'))
		self.assertIsNotNone(findXPath(r, 'm2m:cb/srv'))


	def test_cseDelete(self):
		_, rsc = DELETE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOperationNotAllowed)


	def test_cseUpdate(self):
		jsn = 	{ 'm2m:cse' : {
					'lbl' : [ 'aTag' ]
				}}
		_, rsc = UPDATE(cseURL, ORIGINATOR, jsn)
		self.assertEqual(rsc, C.rcOperationNotAllowed)


if __name__ == '__main__':
	suite = unittest.TestSuite()
	suite.addTest(TestCSE('test_retrieveCSE'))
	suite.addTest(TestCSE('test_retrieveCSEWithWrongOriginator'))
	suite.addTest(TestCSE('test_cseAttributes'))
	suite.addTest(TestCSE('test_cseDelete'))
	suite.addTest(TestCSE('test_cseUpdate'))
	unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)

