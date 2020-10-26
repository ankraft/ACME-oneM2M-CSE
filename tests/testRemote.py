#
#	testRemote.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Remote CSE functionality. Tests are skipped if there is no
#	remote CSE
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from init import *


# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE or remote CSE running.
noCSE = not connectionPossible(cseURL)
noRemote = not connectionPossible(REMOTEcseURL)


class TestRemote(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def setUpClass(cls) -> None:
		# check connection to CSE's
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, 'Cannot retrieve CSEBase: %s' % cseURL
		cls.remoteCse, rsc = RETRIEVE(REMOTEcseURL, REMOTEORIGINATOR)
		assert rsc == RC.OK, 'Cannot retrieve remote CSEBase: %s' % REMOTEcseURL


	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def tearDownClass(cls) -> None:
		pass
		

	# Retrieve the CSR on the local CSE
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveLocalCSR(self) -> None:
		r, rsc = RETRIEVE(localCsrURL, ORIGINATOR)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:csr/ty'), T.CSR)
		self.assertEqual(findXPath(r, 'm2m:csr/rn'), REMOTECSEID[1:])
		self.assertEqual(findXPath(r, 'm2m:csr/ri'), REMOTECSEID[1:])
		self.assertEqual(findXPath(r, 'm2m:csr/cb'), '%s/%s' % (REMOTECSEID, REMOTECSERN))
		self.assertEqual(findXPath(r, 'm2m:csr/csi'), REMOTECSEID)
		self.assertIsNotNone(findXPath(r, 'm2m:csr/acpi'))
		self.assertIsInstance(findXPath(r, 'm2m:csr/acpi'), list)
		self.assertGreater(len(findXPath(r, 'm2m:csr/acpi')), 0)
		for a in findXPath(r, 'm2m:csr/acpi'):
			self.assertTrue(a.startswith('%s/' % CSEID))
		self.assertIsNotNone(findXPath(r, 'm2m:csr/poa'))
		self.assertIsInstance(findXPath(r, 'm2m:csr/poa'), list)
		self.assertGreater(len(findXPath(r, 'm2m:csr/poa')), 0)


	# Retrieve the own CSR on the remote CSE
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveRemoteCSR(self) -> None:
		r, rsc = RETRIEVE(remoteCsrURL, ORIGINATOR)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:csr/ty'), T.CSR)
		self.assertEqual(findXPath(r, 'm2m:csr/rn'), CSEID[1:])
		self.assertEqual(findXPath(r, 'm2m:csr/ri'), CSEID[1:])
		self.assertEqual(findXPath(r, 'm2m:csr/cb'), '%s/%s' % (CSEID, CSERN))
		self.assertEqual(findXPath(r, 'm2m:csr/csi'), CSEID)
		self.assertIsNotNone(findXPath(r, 'm2m:csr/acpi'))
		self.assertIsInstance(findXPath(r, 'm2m:csr/acpi'), list)
		self.assertGreater(len(findXPath(r, 'm2m:csr/acpi')), 0)
		for a in findXPath(r, 'm2m:csr/acpi'):
			self.assertTrue(a.startswith('%s/' % REMOTECSEID))
		self.assertIsNotNone(findXPath(r, 'm2m:csr/poa'))
		self.assertIsInstance(findXPath(r, 'm2m:csr/poa'), list)
		self.assertGreater(len(findXPath(r, 'm2m:csr/poa')), 0)


def run() -> None:
	suite = unittest.TestSuite()
	suite.addTest(TestRemote('test_retrieveLocalCSR'))
	suite.addTest(TestRemote('test_retrieveRemoteCSR'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
