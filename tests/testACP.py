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

	cse 			= None
	ae 				= None
	acp 			= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}'


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(acpURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACP(self) -> None:
		"""	Create an <ACP> """
		dct = 	{ "m2m:acp": {
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
		TestACP.acp, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, dct)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveACP(self) -> None:
		"""	Retrieve the <ACP> """
		_, rsc = RETRIEVE(acpURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveACPwrongOriginator(self) -> None:
		"""	Retrieve the <ACP> with wrong originator """
		_, rsc = RETRIEVE(acpURL, 'wrongoriginator')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesACP(self) -> None:
		"""	Check the <ACP>'s attributes """
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
	def test_updateACP(self) -> None:
		"""	Update the <ACP> """
		dct = 	{ 'm2m:acp' : {
					'lbl' : [ 'aTag' ]
				}}
		acp, rsc = UPDATE(acpURL, self.acpORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(findXPath(acp, 'm2m:acp/lbl'))
		self.assertEqual(len(findXPath(acp, 'm2m:acp/lbl')), 1)
		self.assertIn('aTag', findXPath(acp, 'm2m:acp/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACPwrongOriginator(self) -> None:
		"""	Update the <ACP> with wrong originator """
		dct = 	{ 'm2m:acp' : {
					'lbl' : [ 'bTag' ]
				}}
		r, rsc = UPDATE(acpURL, 'wrong', dct)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addACPtoAE(self) -> None:
		"""	Reference the <ACP> in a new <AE> """
		self.assertIsNotNone(TestACP.acp)
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ '3' ],
				 	'acpi': [ findXPath(TestACP.acp, 'm2m:acp/ri') ]
				}}
		TestACP.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(TestACP.ae, 'm2m:ae/acpi'))
		self.assertIsInstance(findXPath(TestACP.ae, 'm2m:ae/acpi'), list)
		self.assertGreater(len(findXPath(TestACP.ae, 'm2m:ae/acpi')), 0)
		self.assertIn(findXPath(TestACP.acp, 'm2m:acp/ri'), findXPath(TestACP.ae, 'm2m:ae/acpi'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_removeACPfromAE(self) -> None:
		""" Remove the <ACP> reference from an <AE> """
		self.assertIsNotNone(TestACP.acp)
		self.assertIsNotNone(TestACP.ae)
		acpi = findXPath(TestACP.ae, 'm2m:ae/acpi').copy()
		acpi.remove(findXPath(TestACP.acp, 'm2m:acp/ri'))
		dct = 	{ 'm2m:ae' : {
				 	'acpi': acpi
				}}
		r, rsc = UPDATE(aeURL, findXPath(TestACP.ae, 'm2m:ae/aei'), dct)
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)	# missing self-privileges
		_, rsc = UPDATE(aeURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACPwrongOriginator(self) -> None:
		""" Delete <ACP> with wrong originator """
		_, rsc = DELETE(acpURL, 'wrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACP(self) -> None:
		""" Delete <ACP> with correct originator """
		_, rsc = DELETE(acpURL, self.acpORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


def run() -> Tuple[int, int, int]:
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
