 #
#	testRemote_AE.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for S-AE tests
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acmecse.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *


class TestRemote_AE(unittest.TestCase):

	ae				= None
	Saei			= None
	aeri			= None
	remoteCse		= None

	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def setUpClass(cls) -> None:
		# check connection to CSE's
		testCaseStart('Setup TestRemote_AE')
		cls.remoteCse, rsc = RETRIEVE(REMOTEcseURL, REMOTEORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve remote CSEBase: {REMOTEcseURL}'
		testCaseEnd('Setup TestRemote_AE')


	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestRemote_AE')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(f'{REMOTEcseURL}/{aeRN}', REMOTEORIGINATOR)	# Just delete the AE on the remote CSE and everything below it. Ignore whether it exists or not
		DELETE(f'{cseURL}/{TestRemote_AE.Saei}', ORIGINATOR)	# Just delete the AEA
		testCaseEnd('TearDown TestRemote_AE')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_registerAEwithSonRemote(self) -> None:
		""" Register an AE on the remote CSE with "S" as originator """
		dct = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	APPID,
				 	'rr': 	True,
				 	'srv': 	[ RELEASEVERSION ]
				}}
		r, rsc = CREATE(REMOTEcseURL, 'S', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		TestRemote_AE.ae = r
		TestRemote_AE.Saei = findXPath(r, 'm2m:ae/aei')
		TestRemote_AE.aeri = findXPath(r, 'm2m:ae/ri')
		self.assertTrue(TestRemote_AE.Saei.startswith('S'), r)

		# Retrieve the announced AE on the IN-CSE and do some checks
		r, rsc = RETRIEVE(f'{cseURL}/{TestRemote_AE.Saei}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:aeA/aei'), TestRemote_AE.Saei)
		self.assertEqual(findXPath(r, 'm2m:aeA/lnk'), f'{REMOTECSEID}/{TestRemote_AE.aeri}', r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_reregisterAEwithSonRemote(self) -> None:
		""" Re-register an AE on the remote CSE with "<S-stem>" as originator """
		dct = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	APPID,
				 	'rr': 	True,
				 	'srv': 	[ RELEASEVERSION ]
				}}
		r, rsc = CREATE(REMOTEcseURL, TestRemote_AE.Saei, T.AE, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		TestRemote_AE.ae = r
		TestRemote_AE.Saei = findXPath(r, 'm2m:ae/aei')
		TestRemote_AE.aeri = findXPath(r, 'm2m:ae/ri')
		self.assertTrue(TestRemote_AE.Saei.startswith('S'), r)

		# Retrieve the announced AE on the IN-CSE and do some checks
		r, rsc = RETRIEVE(f'{cseURL}/{TestRemote_AE.Saei}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:aeA/aei'), TestRemote_AE.Saei)
		self.assertEqual(findXPath(r, 'm2m:aeA/lnk'), f'{REMOTECSEID}/{TestRemote_AE.aeri}', r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_reregisterAEwithSonCSE(self) -> None:
		""" Re-register an AE on the CSE (ie. a different CSE) with "<S-stem>" as originator """
		dct = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	APPID,
				 	'rr': 	True,
				 	'srv': 	[ RELEASEVERSION ]
				}}
		r, rsc = CREATE(cseURL, TestRemote_AE.Saei, T.AE, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		TestRemote_AE.ae = r
		TestRemote_AE.Saei = findXPath(r, 'm2m:ae/aei')
		TestRemote_AE.aeri = findXPath(r, 'm2m:ae/ri')
		self.assertTrue(TestRemote_AE.Saei.startswith('S'), r)

		# Retrieve the announced AE on the IN-CSE and do some checks
		r, rsc = RETRIEVE(f'{cseURL}/{TestRemote_AE.Saei}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:aeA/aei'), TestRemote_AE.Saei)
		self.assertEqual(findXPath(r, 'm2m:aeA/lnk'), f'{REMOTECSEID}/{TestRemote_AE.aeri}', r)




	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_unregisterAEwithSonRemote(self) -> None:
		""" Unregister the AE on the remote CSE with "S" as originator """
		r, rsc = DELETE(f'{REMOTEcseURL}/{aeRN}', TestRemote_AE.Saei)
		self.assertEqual(rsc, RC.DELETED, r)

		# Retrieve the announced AE on the IN-CSE and do some checks
		r, rsc = RETRIEVE(f'{cseURL}/{TestRemote_AE.Saei}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:aeA/lnk'), 'INACTIVE', r)





# TODO Create an S-AE on IN-CSE
# TODO Create an AeAnnc on a non-IN-CSE with S-Originator -> should fail

def run(testFailFast:bool) -> TestResult:
		# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestRemote_AE, [
		
		# create an announced AE, but no extra attributes
		'test_registerAEwithSonRemote',
		'test_unregisterAEwithSonRemote',
		'test_reregisterAEwithSonRemote',
		'test_unregisterAEwithSonRemote',
		'test_reregisterAEwithSonCSE',

	])

	# Run the tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
