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
from typing import Tuple
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
		""" Create <GRP> with local and remote CSE """
		dct = 	{ 'm2m:grp' : { 
					'rn' : grpRN,
					'mt' : T.CSEBase,
					'mnm': 10,
					'mid': [ f'{CSEID}/{CSERN}', f'{REMOTECSEID}/{REMOTECSERN}' ]
				}}
		r, rsc = CREATE(aeURL, ORIGINATOR, T.GRP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mid'))
		self.assertIsInstance(findXPath(r, 'm2m:grp/mid'), list)
		self.assertEqual(len(findXPath(r, 'm2m:grp/mid')), 2)
		self.assertIn(CSERI, findXPath(r, 'm2m:grp/mid'))
		self.assertIn(f'{REMOTECSEID}/{REMOTECSERN}', findXPath(r, 'm2m:grp/mid'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFOPT(self) -> None:
		"""	Retrieve <GRP>/fopt """
		# Retrieve via fopt
		r, rsc = RETRIEVE(f'{grpURL}/fopt', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 2)
		# Look for both csi
		self.assertIn(findXPath(r, 'm2m:agr/m2m:rsp/{0}/pc/m2m:cb/csi'), [ CSEID, REMOTECSEID ] )
		self.assertIn(findXPath(r, 'm2m:agr/m2m:rsp/{1}/pc/m2m:cb/csi'), [ CSEID, REMOTECSEID ] )


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
	
	# create a group with the CSE and the remote CSE as members
	addTest(suite, TestRemote_GRP('test_createGrp'))
	addTest(suite, TestRemote_GRP('test_retrieveFOPT'))


	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
