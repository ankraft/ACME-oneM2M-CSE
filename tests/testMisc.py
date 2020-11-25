#
#	testMisc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Miscellaneous unit tests
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResponseCode as RC
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

class TestMisc(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		pass


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		pass

	# TODO move to http test
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPRVI(self):
		_, rsc = RETRIEVE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIn('X-M2M-RVI', lastHeaders())
		self.assertEqual(lastHeaders()['X-M2M-RVI'], RVI)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createUnknownResourceType(self):
		jsn = 	{ 'foo:bar' : { 
					'rn' : 'foo',
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, 999, jsn)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAlphaResourceType(self):
		jsn = 	{ 'foo:bar' : { 
					'rn' : 'foo',
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, 'wrong', jsn)
		self.assertEqual(rsc, RC.badRequest)


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestMisc('test_checkHTTPRVI'))
	suite.addTest(TestMisc('test_createUnknownResourceType'))
	suite.addTest(TestMisc('test_createAlphaResourceType'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
