#
#	testTS_TCI.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for timeSeriean & timeSeries functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, ResponseType
from init import *

# TODO transfer requests

class TestRequests(unittest.TestCase):

	ae 			= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestRequests')
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		enableShortResourceExpirations()
		testCaseEnd('Setup TestRequests')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			stopNotificationServer()
			return
		testCaseStart('TearDown TestRequests')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()
		disableShortResourceExpirations()
		testCaseEnd('TearDown TestRequests')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_OETnow(self) -> None:
		"""	RETRIEVE <AE> with OET absolute now """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfOET : DateUtils.getResourceDate()})
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_OETpast(self) -> None:
		"""	RETRIEVE <AE> with OET absolute in the past """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfOET : DateUtils.getResourceDate(-10)})
		self.assertEqual(rsc, RC.OK, r)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_OETfuture(self) -> None:
		"""	RETRIEVE <AE> with OET absolute in the future """
		now = DateUtils.utcTime()
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfOET : DateUtils.getResourceDate(expirationCheckDelay)})
		self.assertEqual(rsc, RC.OK, r)
		self.assertGreater(DateUtils.utcTime(), now+expirationCheckDelay)	# check that enough time has past


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_OETfuturePeriod(self) -> None:
		"""	RETRIEVE <AE> with OET period in the future """
		now = DateUtils.utcTime()
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfOET : f'PT{expirationCheckDelay}S'})
		self.assertEqual(rsc, RC.OK, r)
		self.assertGreater(DateUtils.utcTime(), now+expirationCheckDelay)	# check that enough time has past


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_OETfutureSeconds(self) -> None:
		"""	RETRIEVE <AE> with OET seconds in the future """
		now = DateUtils.utcTime()
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfOET : f'{expirationCheckDelay*1000}'})
		self.assertEqual(rsc, RC.OK, r)
		self.assertGreater(DateUtils.utcTime(), now+expirationCheckDelay)	# check that enough time has past


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RETnowFail(self) -> None:
		"""	RETRIEVE <AE> with RQET absolute now -> FAIL """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : DateUtils.getResourceDate()})
		self.assertEqual(rsc, RC.REQUEST_TIMEOUT, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RETpastFail(self) -> None:
		"""	RETRIEVE <AE> with RQET absolute in the past -> FAIL """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : DateUtils.getResourceDate(-10)})
		self.assertEqual(rsc, RC.REQUEST_TIMEOUT, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RETfuture(self) -> None:
		"""	RETRIEVE <AE> with RQET absolute in the future"""
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : DateUtils.getResourceDate(expirationCheckDelay)})
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RETpastSecondsFail(self) -> None:
		"""	RETRIEVE <AE> with RQET seconds in the past -> Fail"""
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : f'{-expirationCheckDelay*1000}'})
		self.assertEqual(rsc, RC.REQUEST_TIMEOUT, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RETfutureSeconds(self) -> None:
		"""	RETRIEVE <AE> with RQET seconds in the future """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : f'{expirationCheckDelay*1000}'})
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_OETRETfutureSeconds(self) -> None:
		"""	RETRIEVE <AE> with OET < RQET seconds in the future """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : f'{expirationCheckDelay*1000*2}', C.hfOET : f'{expirationCheckDelay*1000}'})
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_OETRETfutureSecondsWrongFail(self) -> None:
		"""	RETRIEVE <AE> with OET > RQET seconds in the future -> Fail"""
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : f'{expirationCheckDelay*1000/2}', C.hfOET : f'{expirationCheckDelay*1000}'})
		self.assertEqual(rsc, RC.REQUEST_TIMEOUT, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RSETsmallerThanRETFail(self) -> None:
		"""	RETRIEVE <AE> with RET < RSET - Fail """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : f'{expirationCheckDelay*2000}', C.hfRST : f'{expirationCheckDelay*1000}'})
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RSETpastFail(self) -> None:
		"""	RETRIEVE <AE> with RSET < now - Fail """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRST : f'-{expirationCheckDelay*2000}'})
		self.assertEqual(rsc, RC.REQUEST_TIMEOUT, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RSETNonBlockingSynchFail(self) -> None:
		""" Retrieve <AE> non-blocking synchronous with short RSET -> Fail"""

		_rset = expirationCheckDelay * 1000
		r, rsc = RETRIEVE(f'{aeURL}?rt={int(ResponseType.nonBlockingRequestSynch)}', 
						  TestRequests.originator,
						  headers={ C.hfRST : f'{_rset}'})
		headers = lastHeaders()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC, r)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		self.assertIn(C.hfRST, headers)
		self.assertEqual(headers[C.hfRST], f'{_rset}')
		requestURI = findXPath(r, 'm2m:uri')
	
		# get and check resource
		testSleep(requestExpirationDelay * 2)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestRequests.originator)
		self.assertEqual(rsc, RC.NOT_FOUND, r)


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
		
	addTest(suite, TestRequests('test_OETnow'))
	addTest(suite, TestRequests('test_OETpast'))
	addTest(suite, TestRequests('test_OETfuture'))
	addTest(suite, TestRequests('test_OETfuturePeriod'))
	addTest(suite, TestRequests('test_OETfutureSeconds'))

	addTest(suite, TestRequests('test_RETnowFail'))
	addTest(suite, TestRequests('test_RETpastFail'))
	addTest(suite, TestRequests('test_RETfuture'))
	addTest(suite, TestRequests('test_RETpastSecondsFail'))
	addTest(suite, TestRequests('test_RETfutureSeconds'))

	addTest(suite, TestRequests('test_OETRETfutureSeconds'))
	addTest(suite, TestRequests('test_OETRETfutureSecondsWrongFail'))

	addTest(suite, TestRequests('test_RSETsmallerThanRETFail'))
	addTest(suite, TestRequests('test_RSETpastFail'))

	addTest(suite, TestRequests('test_RSETNonBlockingSynchFail'))
	
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
