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

		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : True,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()


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


def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestRequests('test_OETnow'))
	suite.addTest(TestRequests('test_OETpast'))
	suite.addTest(TestRequests('test_OETfuture'))
	suite.addTest(TestRequests('test_OETfuturePeriod'))
	suite.addTest(TestRequests('test_OETfutureSeconds'))
	suite.addTest(TestRequests('test_RETnow'))
	suite.addTest(TestRequests('test_RETpast'))
	suite.addTest(TestRequests('test_RETfuture'))
	suite.addTest(TestRequests('test_RETpastSeconds'))
	suite.addTest(TestRequests('test_RETfutureSeconds'))
	suite.addTest(TestRequests('test_OETRETfutureSeconds'))
	suite.addTest(TestRequests('test_OETRETfutureSecondsWrong'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
