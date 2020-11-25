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
from Types import ResourceTypes as T, ResponseCode as RC
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

class TestACP(unittest.TestCase):

	acpORIGINATOR = 'testOriginator'

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}'


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		DELETE(acpURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACP(self) -> None:
		jsn = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ { 	"acor": [ ORIGINATOR ],
									"acop": 63
								} ]
					},
					"pvs": { 
						"acr": [ {
							"acor": [ self.acpORIGINATOR ],
							"acop": 63
						} ]
					},
				}}
		TestACP.acp, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, jsn)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveACP(self):
		_, rsc = RETRIEVE(acpURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveACPwrongOriginator(self):
		_, rsc = RETRIEVE(acpURL, 'wrongoriginator')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesACP(self):
		r, rsc = RETRIEVE(acpURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
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
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acor/{0}'), self.acpORIGINATOR)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'), int)
		self.assertEqual(findXPath(r, 'm2m:acp/pvs/acr/{0}/acop'), 63)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACP(self):
		jsn = 	{ 'm2m:acp' : {
					'lbl' : [ 'aTag' ]
				}}
		r, rsc = UPDATE(acpURL, self.acpORIGINATOR, jsn)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/lbl'))
		self.assertEqual(len(findXPath(r, 'm2m:acp/lbl'), 1))
		self.assertIn('aTag', findXPath(r, 'm2m:acp/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACPwrongOriginator(self):
		jsn = 	{ 'm2m:acp' : {
					'lbl' : [ 'bTag' ]
				}}
		r, rsc = UPDATE(acpURL, 'wrong', jsn)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addACPtoAE(self):
		self.assertIsNotNone(TestACP.acp)
		jsn = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ],
				 	'acpi': [ findXPath(TestACP.acp, 'm2m:acp/ri') ]
				}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(TestACP.ae, 'm2m:ae/acpi'))
		self.assertIsInstance(findXPath(TestACP.ae, 'm2m:ae/acpi'), list)
		self.assertGreater(len(findXPath(TestACP.ae, 'm2m:ae/acpi')), 0)
		self.assertIn(findXPath(TestACP.acp, 'm2m:acp/ri'), findXPath(TestACP.ae, 'm2m:ae/acpi'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_removeACPfromAE(self):
		self.assertIsNotNone(TestACP.acp)
		self.assertIsNotNone(TestACP.ae)
		acpi = findXPath(TestACP.ae, 'm2m:ae/acpi').copy()
		acpi.remove(findXPath(TestACP.acp, 'm2m:acp/ri'))
		jsn = 	{ 'm2m:ae' : {
				 	'acpi': acpi
				}}
		r, rsc = UPDATE(aeURL, findXPath(TestACP.ae, 'm2m:ae/aei'), jsn)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)	# missing self-privileges
		r, rsc = UPDATE(aeURL, ORIGINATOR, jsn)
		self.assertEqual(rsc, RC.updated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACPwrongOriginator(self):
		r, rsc = DELETE(acpURL, 'wrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACP(self):
		r, rsc = DELETE(acpURL, self.acpORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestACP('test_createACP'))
	suite.addTest(TestACP('test_retrieveACP'))
	suite.addTest(TestACP('test_retrieveACPwrongOriginator'))
	suite.addTest(TestACP('test_attributesACP'))
	suite.addTest(TestACP('test_updateACPwrongOriginator'))
	suite.addTest(TestACP('test_addACPtoAE'))
	suite.addTest(TestACP('test_removeACPfromAE'))
	suite.addTest(TestACP('test_deleteACPwrongOriginator'))
	suite.addTest(TestACP('test_deleteACP'))
	#suite.addTest(TestACP('test_handleAE'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
