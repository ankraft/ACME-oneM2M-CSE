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
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
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
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
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
	def test_RETnow(self) -> None:
		"""	RETRIEVE <AE> with RQET absolute now -> FAIL """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : DateUtils.getResourceDate()})
		self.assertEqual(rsc, RC.requestTimeout, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RETpast(self) -> None:
		"""	RETRIEVE <AE> with RQET absolute in the past -> FAIL """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : DateUtils.getResourceDate(-10)})
		self.assertEqual(rsc, RC.requestTimeout, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RETfuture(self) -> None:
		"""	RETRIEVE <AE> with RQET absolute in the future"""
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : DateUtils.getResourceDate(expirationCheckDelay)})
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_RETpastSeconds(self) -> None:
		"""	RETRIEVE <AE> with RQET seconds in the past """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : f'{-expirationCheckDelay*1000}'})
		self.assertEqual(rsc, RC.requestTimeout, r)


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
	def test_OETRETfutureSecondsWrong(self) -> None:
		"""	RETRIEVE <AE> with OET > RQET seconds in the future """
		r, rsc = RETRIEVE(aeURL, TestRequests.originator, headers={ C.hfRET : f'{expirationCheckDelay*1000/2}', C.hfOET : f'{expirationCheckDelay*1000}'})
		self.assertEqual(rsc, RC.requestTimeout, r)


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
		
	addTest(suite, TestRequests('test_OETnow'))
	addTest(suite, TestRequests('test_OETpast'))
	addTest(suite, TestRequests('test_OETfuture'))
	addTest(suite, TestRequests('test_OETfuturePeriod'))
	addTest(suite, TestRequests('test_OETfutureSeconds'))
	addTest(suite, TestRequests('test_RETnow'))
	addTest(suite, TestRequests('test_RETpast'))
	addTest(suite, TestRequests('test_RETfuture'))
	addTest(suite, TestRequests('test_RETpastSeconds'))
	addTest(suite, TestRequests('test_RETfutureSeconds'))
	addTest(suite, TestRequests('test_OETRETfutureSeconds'))
	addTest(suite, TestRequests('test_OETRETfutureSecondsWrong'))
	
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
