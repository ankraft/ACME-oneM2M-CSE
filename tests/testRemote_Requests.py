#
#	testRemote_Requests.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for various requests to a remote CSE. Tests are
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
		testCaseStart('Setup TestRemote_Requests')
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

		testCaseEnd('Setup TestRemote_Requests')


	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestRemote_Requests')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not

		testCaseEnd('TearDown TestRemote_Requests')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_forwardCreateCNT(self) -> None:
		"""	CREATE <AE> and <CNT> on the remote CSE via a forwarded request"""

		# Register AE
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN,
					'api' : APPID,
					'rr'  : True,
					'srv' : [ RELEASEVERSION ]
				}}
		r, rsc = CREATE(REMOTEcseURL, f'{CSEID}/Cremote', ResourceTypes.AE, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct =	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}

		_ae = f'{CSEURL}{REMOTECSEID}/{REMOTECSERN}/{aeRN}'

		# CREATE a <CNT> on the remote CSE via a forwarded request
		# r, rsc = CREATE(_ae, '/id-mn/Cremote', ResourceTypes.CNT, dct)
		r, rsc = CREATE(_ae, f'{CSEID}/Cremote', ResourceTypes.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Unregister AE
		# r, rsc = DELETE(_ae, '/id-mn/Cremote')
		r, rsc = DELETE(_ae, f'{CSEID}/Cremote')
		self.assertEqual(rsc, RC.DELETED, r)




def run(testFailFast:bool) -> TestResult:

	suite = unittest.TestSuite()
	addTests(suite, TestRemote_GRP, [
		'test_forwardCreateCNT'
	])

	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
