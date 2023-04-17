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
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *

csrOriginator = '/Ctest'

class TestRemote(unittest.TestCase):

	remoteCse 	= None

	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestRemote')
		# check connection to CSE's
		cls.remoteCse, rsc = RETRIEVE(REMOTEcseURL, REMOTEORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve remote CSEBase: {REMOTEcseURL}'
		testCaseEnd('Setup TestRemote')


	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestRemote')
		DELETE(csrURL, ORIGINATOR)
		DELETE(aeURL, ORIGINATOR)
		testCaseEnd('TearDown TestRemote')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	# Retrieve the CSR on the local CSE
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveLocalCSR(self) -> None:
		"""	Retrieve the local registree CSR """
		r, _ = RETRIEVE(localCsrURL, ORIGINATOR)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:csr/ty'), T.CSR, r)
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


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createCSRmissingCSI(self) -> None:
		""" Create a local <CSR> with missing CSI """
		dct = { 'm2m:csr' : {
			'rn': csrRN,
			# missing csi
			'rr': False,
			'cst': 2, 
			'csz': [ 'application/json' ],
			'poa': [ CSEURL ], 
			'srv': [ '2a', '3', '4' ],
			'dcse': [],
		}}
		r, rsc = CREATE(cseURL, csrOriginator, T.CSR, dct)
		if rsc == RC.ORIGINATOR_HAS_NO_PRIVILEGE:
			console.print(f'\n[r]Please add "{csrOriginator[1:]}" to the configuration \[cse.registration].allowedCSROriginators in the IN-CSE\'s ini file')
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createCSRmissingCB(self) -> None:
		""" Create a local <CSR> with missing cb """
		dct = { 'm2m:csr' : {
			'rn': csrRN,
			# missing cb
			'csi': '/wrongCSI',
			'rr': False,
			'cst': 2, 
			'csz': [ 'application/json' ],
			'poa': [ CSEURL ], 
			'srv': [ '2a', '3', '4' ],
			'dcse': [],
		}}
		r, rsc = CREATE(cseURL, csrOriginator, T.CSR, dct)
		if rsc == RC.ORIGINATOR_HAS_NO_PRIVILEGE:
			console.print(f'\n[r]Please add "{csrOriginator[1:]}" to the configuration \[cse.registration].allowedCSROriginators in the IN-CSE\'s ini file')
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createCSRwrongCSI(self) -> None:
		""" Create a local <CSR> with wrong CSI """
		dct = { 'm2m:csr' : {
			'rn': csrRN,
			'cb': '/someCB',
			'csi': 'wrongCSI',	# wrong
			'rr': False,
			'cst': 2, 
			'csz': [ 'application/json' ],
			'poa': [ CSEURL ], 
			'srv': [ '2a', '3', '4' ],
			'dcse': [],
		}}
		r, rsc = CREATE(cseURL, csrOriginator, T.CSR, dct)
		if rsc == RC.ORIGINATOR_HAS_NO_PRIVILEGE:
			console.print(f'\n[r]Please add "{csrOriginator[1:]}" to the configuration \[cse.registration].allowedCSROriginators in the IN-CSE\'s ini file')
		self.assertEqual(rsc, RC.CREATED, r)	# actually, it is overwritten by the CSE

		_, rsc = DELETE(csrURL, csrOriginator)
		self.assertEqual(rsc, RC.DELETED)

	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createCSRnoCsi(self) -> None:
		""" Create a local <CSR> without csi, but allowed originator"""
		dct = { 'm2m:csr' : {
			'rn': csrRN,
			'cb': '/someCB',
			'rr': False,
			'cst': 2, 
			'csz': [ 'application/json' ],
			'poa': [ CSEURL ], 
			'srv': [ '2a', '3', '4' ],
			'dcse': [],
		}}
		r, rsc = CREATE(cseURL, csrOriginator, T.CSR, dct)
		if rsc == RC.ORIGINATOR_HAS_NO_PRIVILEGE:
			console.print('\n[r]Please add "id-nocsi" to the configuration \[cse.registration].allowedCSROriginators in the IN-CSE\'s ini file')
		self.assertEqual(rsc, RC.CREATED, r)
		
		_, rsc = DELETE(csrURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createCSRsameAsAE(self) -> None:
		""" Create a local <CSR> with the same originator as an <AE> -> Fail """

		# Create AE first
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': 'NMyApp1Id',
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		r, rsc = CREATE(cseURL, 'Ctest', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct = { 'm2m:csr' : {
			'rn': csrRN,
			'cb': '/Ctest',
			'rr': False,
			'cst': 2, 
			'csz': [ 'application/json' ],
			'poa': [ CSEURL ], 
			'srv': [ '2a', '3', '4' ],
			'dcse': [],
		}}
		r, rsc = CREATE(cseURL, 'Ctest', T.CSR, dct)
		if rsc == RC.ORIGINATOR_HAS_NO_PRIVILEGE:
			console.print('\n[r]Please add "Ctest" to the configuration \[cse.registration].allowedCSROriginators in the IN-CSE\'s ini file')
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED, r)

		_, rsc = DELETE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)



# TODO Transfer requests

def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
			
	addTest(suite, TestRemote('test_retrieveLocalCSR'))
	addTest(suite, TestRemote('test_retrieveRemoteCSR'))
	addTest(suite, TestRemote('test_createCSRmissingCSI'))
	addTest(suite, TestRemote('test_createCSRmissingCB'))
	addTest(suite, TestRemote('test_createCSRwrongCSI'))
	addTest(suite, TestRemote('test_createCSRnoCsi'))
	addTest(suite, TestRemote('test_createCSRsameAsAE'))
	
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
