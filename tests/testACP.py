#
#	testACP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for ACP functionality
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T
from init import *

class TestACP(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == C.rcOK, 'Cannot retrieve CSEBase: %s' % cseURL


	@classmethod
	def tearDownClass(cls):
		DELETE(acpURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not


	def test_createACP(self):
		jsn = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ { 	"acor": [ ORIGINATOR ],
									"acop": 63
								} ]
					},
					"pvs": { 
						"acr": [ {
							"acor": [ ORIGINATOR ],
							"acop": 63
						} ]
					},
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, jsn)
		self.assertEqual(rsc, C.rcCreated)


	def test_retrieveACP(self):
		_, rsc = RETRIEVE(acpURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)


	def test_retrieveACPwrongOriginator(self):
		_, rsc = RETRIEVE(acpURL, 'wrongoriginator')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	def test_attributesACP(self):
		r, rsc = RETRIEVE(acpURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:acp/ty'), T.ACP)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/et'))
		self.assertLessEqual(findXPath(r, 'm2m:acp/ct'), findXPath(r, 'm2m:acp/lt'))
		self.assertLess(findXPath(r, 'm2m:acp/ct'), findXPath(r, 'm2m:acp/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv'), dict)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr'), list)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}'), dict)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acor'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}/acor'), list)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acor/{0}'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}/acor/{0}'), str)
		self.assertEqual(findXPath(r, 'm2m:acp/pv/acr/{0}/acor/{0}'), ORIGINATOR)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'), int)
		self.assertEqual(findXPath(r, 'm2m:acp/pv/acr/{0}/acop'), 63)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs'), dict)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs/acr'), list)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor'), list)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor/{0}'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor/{0}'), str)
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor/{0}'), ORIGINATOR)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'), int)
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'), 63)


	def test_updateACP(self):
		jsn = 	{ 'm2m:acp' : {
					'lbl' : [ 'aTag' ]
				}}
		r, rsc = UPDATE(acpURL, ORIGINATOR, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		
# update. correct, wrong originator
# DELETE ACP
# Create AE implicte ACP
# DELETE ACP for that AE. Access to AE? How?

def run():
	suite = unittest.TestSuite()
	suite.addTest(TestACP('test_createACP'))
	suite.addTest(TestACP('test_retrieveACP'))
	suite.addTest(TestACP('test_retrieveACPwrongOriginator'))
	suite.addTest(TestACP('test_attributesACP'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
