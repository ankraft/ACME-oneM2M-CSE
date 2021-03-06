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
from typing import Tuple
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from init import *


class TestRemote(unittest.TestCase):

	remoteCse 	= None

	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def setUpClass(cls) -> None:
		# check connection to CSE's
		cls.remoteCse, rsc = RETRIEVE(REMOTEcseURL, REMOTEORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve remote CSEBase: {REMOTEcseURL}'


	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def tearDownClass(cls) -> None:
		pass
		

	# Retrieve the CSR on the local CSE
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveLocalCSR(self) -> None:
		"""	Retrieve the local registree CSR """
		r, _ = RETRIEVE(localCsrURL, ORIGINATOR)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:csr/ty'), T.CSR)
		self.assertEqual(findXPath(r, 'm2m:csr/rn'), REMOTECSEID[1:])
		self.assertEqual(findXPath(r, 'm2m:csr/ri'), REMOTECSEID[1:])
		self.assertEqual(findXPath(r, 'm2m:csr/cb'), f'{REMOTECSEID}/{REMOTECSERN}')
		self.assertEqual(findXPath(r, 'm2m:csr/csi'), REMOTECSEID)
		# self.assertIsNotNone(findXPath(r, 'm2m:csr/acpi'))
		# self.assertIsInstance(findXPath(r, 'm2m:csr/acpi'), list)
		# self.assertGreater(len(findXPath(r, 'm2m:csr/acpi')), 0)
		# for a in findXPath(r, 'm2m:csr/acpi'):
		# 	self.assertTrue(a.startswith(f'{CSEID}/'))
		self.assertIsNotNone(findXPath(r, 'm2m:csr/poa'))
		self.assertIsInstance(findXPath(r, 'm2m:csr/poa'), list)
		self.assertGreater(len(findXPath(r, 'm2m:csr/poa')), 0)


	# Retrieve the own CSR on the remote CSE
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveRemoteCSR(self) -> None:
		""" Retrieve own remote CSE """
		r, _ = RETRIEVE(remoteCsrURL, ORIGINATOR)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:csr/ty'), T.CSR)
		self.assertEqual(findXPath(r, 'm2m:csr/rn'), CSEID[1:])
		self.assertEqual(findXPath(r, 'm2m:csr/ri'), CSEID[1:])
		self.assertEqual(findXPath(r, 'm2m:csr/cb'), f'{CSEID}/{CSERN}')
		self.assertEqual(findXPath(r, 'm2m:csr/csi'), CSEID)
		# self.assertIsNotNone(findXPath(r, 'm2m:csr/acpi'))
		# self.assertIsInstance(findXPath(r, 'm2m:csr/acpi'), list)
		# self.assertGreater(len(findXPath(r, 'm2m:csr/acpi')), 0)
		# for a in findXPath(r, 'm2m:csr/acpi'):
		# 	self.assertTrue(a.startswith(f'{REMOTECSEID}/'))
		self.assertIsNotNone(findXPath(r, 'm2m:csr/poa'))
		self.assertIsInstance(findXPath(r, 'm2m:csr/poa'), list)
		self.assertGreater(len(findXPath(r, 'm2m:csr/poa')), 0)


def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestRemote('test_retrieveLocalCSR'))
	suite.addTest(TestRemote('test_retrieveRemoteCSR'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
