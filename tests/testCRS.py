#
#	testCRS.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CRS functionality & notifications
#

import unittest, sys, time
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import NotificationEventType as NET, ResourceTypes as T, NotificationContentType, ResponseStatusCode as RC
from init import *

cntRN1 = f'{cntRN}1'
cntRN2 = f'{cntRN}2'

class TestCRS(unittest.TestCase):
	ae 				= None
	cnt1 			= None
	cnt2 			= None
	cnt1RI 			= None
	cnt2RI 			= None
	originator 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		# Start notification server
		startNotificationServer()

		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'

		# create AE
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : True,
				 	'srv' : [ '3' ],
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		# create CNT1 & CNT2
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN1
				}}
		cls.cnt1, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		cls.cnt1RI = findXPath(cls.cnt1, 'm2m:cnt/ri')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN2
				}}
		cls.cnt2, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		cls.cnt2RI = findXPath(cls.cnt2, 'm2m:cnt/ri')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSmissingRratSratFail(self) -> None:
		"""	CREATE <CRS> with both missing rrat and srat -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCSR',
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					# missing rrat/srat
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSmissingNuFail(self) -> None:
		"""	CREATE <CRS> with missing nu -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCSR',
					# missing nu
					'twt': 1,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI]
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSmissingTwtFail(self) -> None:
		"""	CREATE <CRS> with missing twt -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCSR',
					'nu' : [ NOTIFICATIONSERVER ],
					# missing twt
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI]
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSwrongTwtFail(self) -> None:
		"""	CREATE <CRS> with wrong twt -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCSR',
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 99,
					'tws' : f'PT{crsTimeWindowSize}S',
					'rrat': [ self.cnt1RI, self.cnt2RI]
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCRSmissingTwsFail(self) -> None:
		"""	CREATE <CRS> with missing tws -> FAIL """
		dct = 	{ 'm2m:crs' : { 
					'rn' : 'failCSR',
					'nu' : [ NOTIFICATIONSERVER ],
					'twt': 1,
					'rrat': [ self.cnt1RI, self.cnt2RI]
				}}
		r, rsc = CREATE(aeURL, TestCRS.originator, T.CRS, dct)
		self.assertEqual(rsc, RC.badRequest, r)


# TODO test twt missing, oiut of range
# TODO test tws

def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()

	suite.addTest(TestCRS('test_createCRSmissingRratSratFail'))
	suite.addTest(TestCRS('test_createCRSmissingNuFail'))
	suite.addTest(TestCRS('test_createCRSmissingTwtFail'))
	suite.addTest(TestCRS('test_createCRSwrongTwtFail'))
	suite.addTest(TestCRS('test_createCRSmissingTwsFail'))

	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
