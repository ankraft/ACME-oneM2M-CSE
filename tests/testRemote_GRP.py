#
#	testRemote_Annc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Announcementfunctionality to a remote CSE. Tests are
#	skipped if there is no remote CSE.
#


import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *


class TestRemote_GRP(unittest.TestCase):

	remoteCse 		= None
	ae				= None
	grp				= None


	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestRemote_GRP')
		# check connection to CSE's
		cls.remoteCse, rsc = RETRIEVE(REMOTEcseURL, REMOTEORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve remote CSEBase: {REMOTEcseURL}'
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		testCaseEnd('Setup TestRemote_GRP')


	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestRemote_GRP')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestRemote_GRP')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	# Create an AE with AT, but no AA
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createGrp(self) -> None:
		""" Create <GRP> with local CSEBase and remote CSR """
		dct = 	{ 'm2m:grp' : { 
					'rn' : grpRN,
					'mt' : T.MIXED,
					'mnm': 10,
					'mid': [ f'{CSEID}/{CSERN}', f'{REMOTECSEID}{CSEID}' ]
				}}
		r, rsc = CREATE(aeURL, CSEID, T.GRP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mid'))
		self.assertIsInstance(findXPath(r, 'm2m:grp/mid'), list)
		self.assertEqual(len(findXPath(r, 'm2m:grp/mid')), 2, r)
		self.assertIn(CSERI, findXPath(r, 'm2m:grp/mid'))
		self.assertIn(f'{REMOTECSEID}{CSEID}', findXPath(r, 'm2m:grp/mid'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFOPT(self) -> None:
		"""	Retrieve <GRP>/fopt """
		# Retrieve via fopt
		r, rsc = RETRIEVE(f'{grpURL}/fopt', CSEID)
		self.assertEqual(rsc, RC.OK, r)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp',r)
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 2)
		# Look for both csi
		for res in rsp:
			if (_csi := findXPath(res, 'pc/m2m:cb/csi')):
				self.assertEqual(_csi, CSEID, r)
			elif (_csi := findXPath(res, 'pc/m2m:csr/csi')):
				self.assertEqual(_csi, CSEID, r)


def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestRemote_GRP, [
	
		# Note, that the following tests are run with the CSE-ID as originator, so the CSE-ID is used
		# as originator for the requests. This is necessary to create the group with the CSE and the remote CSE as members.
		# This is to avoid complicated setup with ACPs and so on.

		# create a group with the CSE and the remote CSE as members
		'test_createGrp',
		'test_retrieveFOPT',

	])

	# Run the tests
	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
