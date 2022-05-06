#
#	testCNT_CIN.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CNT & CIN functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import NotificationEventType, ResourceTypes as T, ResponseStatusCode as RC, ResultContentType
from init import *


maxBS = 30

class TestCNT_CIN(unittest.TestCase):

	ae 			= None
	originator 	= None
	cnt 		= None

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
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mni' : 3
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		assert findXPath(cls.cnt, 'm2m:cnt/mni') == 3, 'mni is not correct'

		# Start notification server
		startNotificationServer()
		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCIN(self) -> None:
		"""	Create <CIN> under <CNT> """
		self.assertIsNotNone(TestCNT_CIN.ae)
		self.assertIsNotNone(TestCNT_CIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'aValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/ri'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		self.assertEqual(findXPath(r, 'm2m:cin/cnf'), 'text/plain:0')
		self.cinARi = findXPath(r, 'm2m:cin/ri')			# store ri

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 1)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addMoreCIN(self) -> None:
		"""	Create more <CIN>s under <CNT> """
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'bValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'bValue')

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 2)

		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'cValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'cValue')

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 3)

		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'dValue'
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')

		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/cni'), int)
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 3)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTLa(self) -> None:
		"""	Retrieve <CNT>.LA """
		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTOl(self) -> None:
		""" Retrieve <CNT>.OL """
		r, rsc = RETRIEVE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'bValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_changeCNTMni(self) -> None:
		"""	Change <CNT>.MNI to 1 -> OL == LA """
		dct = 	{ 'm2m:cnt' : {
					'mni' : 1
 				}}
		cnt, rsc = UPDATE(cntURL, TestCNT_CIN.originator, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(cnt)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mni'))
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mni'), 1)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/cni'))
		self.assertEqual(findXPath(cnt, 'm2m:cnt/cni'), 1)

		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')

		r, rsc = RETRIEVE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'dValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNT(self) -> None:
		"""	Delete <CNT> """
		_, rsc = DELETE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithMBS(self) -> None:
		"""	Create <CNT> with mbs"""
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mbs' : maxBS
				}}
		TestCNT_CIN.cnt, rsc = CREATE(aeURL, TestCNT_CIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/mbs'))
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/mbs'), maxBS)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINexactSize(self) -> None:
		"""	Add <CIN> to <CNT> with exact max size"""
		dct = 	{ 'm2m:cin' : {
					'con' : 'x' * maxBS
				}}
		_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINtooBig(self) -> None:
		"""	Add <CIN> to <CNT> with size > mbs -> Fail """
		dct = 	{ 'm2m:cin' : {
					'con' : 'x' * (maxBS + 1)
				}}
		_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.notAcceptable)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINsForCNTwithSize(self) -> None:
		"""	Add multiple <CIN>s to <CNT> with size restrictions """
		# First fill up the container
		for _ in range(int(maxBS / 3)):
			dct = 	{ 'm2m:cin' : {
						'con' : 'x' * int(maxBS / 3)
					}}
			_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.created)
		
		# Test latest CIN for x
		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertTrue(findXPath(r, 'm2m:cin/con').startswith('x'))
		self.assertEqual(len(findXPath(r, 'm2m:cin/con')), int(maxBS / 3))

		# Add another CIN
		dct = 	{ 'm2m:cin' : {
					'con' : 'y' * int(maxBS / 3)
				}}
		_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)

		# Test latest CIN for y
		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertTrue(findXPath(r, 'm2m:cin/con').startswith('y'))
		self.assertEqual(len(findXPath(r, 'm2m:cin/con')), int(maxBS / 3))

		# Test CNT
		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cni'))
		self.assertEqual(findXPath(r, 'm2m:cnt/cni'), 3)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/cbs'))
		self.assertEqual(findXPath(r, 'm2m:cnt/cbs'), maxBS)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithDISR(self) -> None:
		"""	Create <CNT> with disr = True and add <CIN>"""
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'disr' : True
				}}
		TestCNT_CIN.cnt, rsc = CREATE(aeURL, TestCNT_CIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'))
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'), True)

		# Add CINs
		for i in range(5):
			dct = 	{ 'm2m:cin' : {
						'rn'  : f'{i}',
						'con' : f'{i}',
					}}
			_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithDISR(self) -> None:
		"""	Retrieve <CIN> with disr = True -> FAIL """
		r, rsc = RETRIEVE(f'{cntURL}/3', TestCNT_CIN.originator)	# Retrieve some <cin>
		self.assertEqual(rsc, RC.operationNotAllowed)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveLAwithDISR(self) -> None:
		"""	Retrieve <CNT>.LA with disr = True -> FAIL """
		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.operationNotAllowed)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveOLwithDISR(self) -> None:
		"""	Retrieve <CNT>.OL with disr = True -> FAIL """
		r, rsc = RETRIEVE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.operationNotAllowed)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCINwithDISR(self) -> None:
		"""	Discover <CIN> with disr = True -> FAIL """
		r, rsc = RETRIEVE(f'{cntURL}?rcn={int(ResultContentType.childResourceReferences)}', TestCNT_CIN.originator)	# Discover
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTwithDISRFalse(self) -> None:
		"""	Update <CNT> with disr = False. Delete all <CIN>"""
		dct = 	{ 'm2m:cnt' : {
					'disr' : False,
				}}
		TestCNT_CIN.cnt, rsc = UPDATE(cntURL, TestCNT_CIN.originator, dct)
		self.assertEqual(rsc, RC.updated, TestCNT_CIN.cnt)
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'), False)
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/cni'), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTwithDISRNullFalse(self) -> None:
		"""	Update <CNT> with disr = Null/False and add <CIN>"""
		dct:JSON = 	{ 'm2m:cnt' : {
					'disr' : None,
				}}
		TestCNT_CIN.cnt, rsc = UPDATE(cntURL, TestCNT_CIN.originator, dct)
		self.assertEqual(rsc, RC.updated, TestCNT_CIN.cnt)
		self.assertIsNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'))

		# Add CINs
		for i in range(0,5):
			dct = 	{ 'm2m:cin' : {
						'rn'  : f'{i}',
						'con' : f'{i}',
					}}
			r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.created, r)

		# Update now with False
		dct = 	{ 'm2m:cnt' : {
					'disr' : False,
				}}
		TestCNT_CIN.cnt, rsc = UPDATE(cntURL, TestCNT_CIN.originator, dct)
		self.assertEqual(rsc, RC.updated, TestCNT_CIN.cnt)
		self.assertIsNotNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'))
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'), False)

		# Add CINs
		for i in range(5,10):
			dct = 	{ 'm2m:cin' : {
						'rn'  : f'{i}',
						'con' : f'{i}',
					}}
			r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.created, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithDISRAllowed(self) -> None:
		"""	Retrieve <CIN> with disr = False"""
		r, rsc = RETRIEVE(f'{cntURL}/3', TestCNT_CIN.originator)	# Retrieve some <cin>
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_autoDeleteCINnoNotifiction(self) -> None:
		"""	Automatic delete of <CIN> must not generate a notification for deleteDirectChild """

		# Create <CNT>
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mni' : 3
				}}
		TestCNT_CIN.cnt, rsc = CREATE(aeURL, TestCNT_CIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/mni'))
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/mni'), 3)

		# CREATE <SUB>
		dct = 	{ 'm2m:sub' : { 
			        'enc': {
			            'net': [ NotificationEventType.deleteDirectChild ]
        			},
        			'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created, r)

		# Add more <CIN> than the capacity allows, so that some <CIN> will be deleted by the CSE
		clearLastNotification()
		for i in range(5):
			dct = 	{ 'm2m:cin' : {
						'con' : f'{i}',	
					}}
			_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.created)
		
		self.assertIsNone(getLastNotification())	# No notifications


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNT5CIN(self) -> None:
		""" Create <CNT> and 5 <CIN> """
		# Create <CNT>
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mni' : 10
				}}
		TestCNT_CIN.cnt, rsc = CREATE(aeURL, TestCNT_CIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created, TestCNT_CIN.cnt)

		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'aValue'
				}}
		for _ in range(5):
			r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.created, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTOl(self) -> None:
		""" Delete <CNT>.OL """

		# Retrieve oldest
		ol, rsc = RETRIEVE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)

		# Delete oldest
		_, rsc = DELETE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.deleted)

		# Retrieve new oldest and compare
		r, rsc = RETRIEVE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertNotEqual(findXPath(r, 'm2m:cin/ri'), findXPath(ol, 'm2m:cin/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTLA(self) -> None:
		""" Delete <CNT>.LA """

		# Retrieve latest
		ol, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)

		# Delete latest
		_, rsc = DELETE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.deleted)

		# Retrieve new latest and compare
		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertNotEqual(findXPath(r, 'm2m:cin/ri'), findXPath(ol, 'm2m:cin/ri'))



def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()
	suite.addTest(TestCNT_CIN('test_addCIN'))
	suite.addTest(TestCNT_CIN('test_addMoreCIN'))
	suite.addTest(TestCNT_CIN('test_retrieveCNTLa'))
	suite.addTest(TestCNT_CIN('test_retrieveCNTOl'))
	suite.addTest(TestCNT_CIN('test_changeCNTMni'))
	suite.addTest(TestCNT_CIN('test_deleteCNT'))

	suite.addTest(TestCNT_CIN('test_createCNTwithMBS'))
	suite.addTest(TestCNT_CIN('test_createCINexactSize'))
	suite.addTest(TestCNT_CIN('test_createCINtooBig'))
	suite.addTest(TestCNT_CIN('test_createCINsForCNTwithSize'))
	suite.addTest(TestCNT_CIN('test_deleteCNT'))

	suite.addTest(TestCNT_CIN('test_createCNTwithDISR'))
	suite.addTest(TestCNT_CIN('test_retrieveCINwithDISR'))
	suite.addTest(TestCNT_CIN('test_retrieveLAwithDISR'))
	suite.addTest(TestCNT_CIN('test_retrieveOLwithDISR'))
	suite.addTest(TestCNT_CIN('test_discoverCINwithDISR'))
	suite.addTest(TestCNT_CIN('test_updateCNTwithDISRFalse'))
	suite.addTest(TestCNT_CIN('test_updateCNTwithDISRNullFalse'))
	suite.addTest(TestCNT_CIN('test_retrieveCINwithDISRAllowed'))
	suite.addTest(TestCNT_CIN('test_deleteCNT'))

	suite.addTest(TestCNT_CIN('test_autoDeleteCINnoNotifiction'))
	suite.addTest(TestCNT_CIN('test_deleteCNT'))

	suite.addTest(TestCNT_CIN('test_createCNT5CIN'))
	suite.addTest(TestCNT_CIN('test_deleteCNTOl'))
	suite.addTest(TestCNT_CIN('test_deleteCNTLA'))
	suite.addTest(TestCNT_CIN('test_deleteCNT'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
