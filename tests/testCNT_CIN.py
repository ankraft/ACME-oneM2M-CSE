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
from acme.etc.Types import NotificationEventType, ResourceTypes as T, ResponseStatusCode as RC, ResultContentType
from init import *


maxBS = 30
testValue = 'aValue'

class TestCNT_CIN(unittest.TestCase):

	ae 			= None
	originator 	= None
	cnt 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestCNT_CIN')
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mni' : 3
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		assert findXPath(cls.cnt, 'm2m:cnt/mni') == 3, 'mni is not correct'

		# Start notification server
		startNotificationServer()
		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'
		testCaseEnd('Setup TestCNT_CIN')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			stopNotificationServer()
			return
		testCaseStart('TearDown TestCNT_CIN')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()
		testCaseEnd('TearDown TestCNT_CIN')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCIN(self) -> None:
		"""	Create <CIN> under <CNT> """
		self.assertIsNotNone(TestCNT_CIN.ae)
		self.assertIsNotNone(TestCNT_CIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : testValue
				}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/ri'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), testValue)
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
		self.assertEqual(rsc, RC.CREATED)
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
		self.assertEqual(rsc, RC.CREATED)
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
		self.assertEqual(rsc, RC.CREATED)
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
		self.assertEqual(rsc, RC.OK, r)
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
		self.assertEqual(rsc, RC.UPDATED)
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
	def test_deleteCINCheckCNT(self) -> None:
		""" Delete <CIN> resource and check whether cni and cbs are of the parent are updated """
		dct = 	{ 'm2m:cin' : {
			'rn'  : cinRN,
			'con' : 'AnyValue'
		}}
		r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Get cni and cbs from parent container
		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(_cni := findXPath(r, 'm2m:cnt/cni'))
		self.assertIsNotNone(_cbs := findXPath(r, 'm2m:cnt/cbs'))

		# Check cni and cbs
		_, rsc = DELETE(cinURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.DELETED)

		# Check cni and cbs again
		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertNotEqual(_cni, findXPath(r, 'm2m:cnt/cni'))
		self.assertNotEqual(_cbs, findXPath(r, 'm2m:cnt/cbs'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNT(self) -> None:
		"""	Delete <CNT> """
		_, rsc = DELETE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithMBS(self) -> None:
		"""	Create <CNT> with mbs"""
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mbs' : maxBS
				}}
		TestCNT_CIN.cnt, rsc = CREATE(aeURL, TestCNT_CIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/mbs'))
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/mbs'), maxBS)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINexactSize(self) -> None:
		"""	Add <CIN> to <CNT> with exact max size"""
		dct = 	{ 'm2m:cin' : {
					'con' : 'x' * maxBS
				}}
		_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINtooBig(self) -> None:
		"""	Add <CIN> to <CNT> with size > mbs -> Fail """
		dct = 	{ 'm2m:cin' : {
					'con' : 'x' * (maxBS + 1)
				}}
		_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.NOT_ACCEPTABLE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINsForCNTwithSize(self) -> None:
		"""	Add multiple <CIN>s to <CNT> with size restrictions """
		# First fill up the container
		for _ in range(int(maxBS / 3)):
			dct = 	{ 'm2m:cin' : {
						'con' : 'x' * int(maxBS / 3)
					}}
			_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED)
		
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
		self.assertEqual(rsc, RC.CREATED)

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
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'))
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'), True)

		# Add CINs
		for i in range(5):
			dct = 	{ 'm2m:cin' : {
						'rn'  : f'{i}',
						'con' : f'{i}',
					}}
			_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithDISRFail(self) -> None:
		"""	Retrieve <CIN> with disr = True -> FAIL """
		r, rsc = RETRIEVE(f'{cntURL}/3', TestCNT_CIN.originator)	# Retrieve some <cin>
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveLAwithDISRFail(self) -> None:
		"""	Retrieve <CNT>.LA with disr = True -> FAIL """
		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveOLwithDISRFail(self) -> None:
		"""	Retrieve <CNT>.OL with disr = True -> FAIL """
		r, rsc = RETRIEVE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCINwithDISRFail(self) -> None:
		"""	Discover <CIN> with disr = True -> FAIL """
		r, rsc = RETRIEVE(f'{cntURL}?rcn={int(ResultContentType.childResourceReferences)}', TestCNT_CIN.originator)	# Discover
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCINwithDISRFail(self) -> None:
		"""	Delete <CIN> with disr = True -> Fail"""
		r, rsc = DELETE(f'{cntURL}/3', TestCNT_CIN.originator)	# delete a <cin>
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteLAwithDISRFail(self) -> None:
		"""	Delete <la> with disr = True -> Fail"""
		r, rsc = DELETE(f'{cntURL}/la', TestCNT_CIN.originator)	# delete latest <cin>
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTwithDISRFalse(self) -> None:
		"""	Update <CNT> with disr = False. Delete all <CIN>"""
		dct = 	{ 'm2m:cnt' : {
					'disr' : False,
				}}
		TestCNT_CIN.cnt, rsc = UPDATE(cntURL, TestCNT_CIN.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCNT_CIN.cnt)
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'), False)
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/cni'), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTwithDISRNullFalse(self) -> None:
		"""	Update <CNT> with disr = Null/False and add <CIN>"""
		dct:JSON = 	{ 'm2m:cnt' : {
					'disr' : None,
				}}
		TestCNT_CIN.cnt, rsc = UPDATE(cntURL, TestCNT_CIN.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCNT_CIN.cnt)
		self.assertIsNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'))

		# Add CINs
		for i in range(0,5):
			dct = 	{ 'm2m:cin' : {
						'rn'  : f'{i}',
						'con' : f'{i}',
					}}
			r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED, r)

		# Update now with False
		dct = 	{ 'm2m:cnt' : {
					'disr' : False,
				}}
		TestCNT_CIN.cnt, rsc = UPDATE(cntURL, TestCNT_CIN.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCNT_CIN.cnt)
		self.assertIsNotNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'))
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'), False)

		# Add CINs
		for i in range(5,10):
			dct = 	{ 'm2m:cin' : {
						'rn'  : f'{i}',
						'con' : f'{i}',
					}}
			r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithDISRAllowed(self) -> None:
		"""	Retrieve <CIN> with disr = False"""
		r, rsc = RETRIEVE(f'{cntURL}/3', TestCNT_CIN.originator)	# Retrieve some <cin>
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTwithCINandDisr(self) -> None:
		"""	Delete <CNT> with <CIN> and disr = True """
		
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN + '_1',
					'disr' : True
				}}
		TestCNT_CIN.cnt, rsc = CREATE(aeURL, TestCNT_CIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'))
		self.assertEqual(findXPath(TestCNT_CIN.cnt, 'm2m:cnt/disr'), True)

		# Add CINs
		for i in range(5):
			dct = 	{ 'm2m:cin' : {
						'rn'  : f'{i}',
						'con' : f'{i}',
					}}
			_, rsc = CREATE(cntURL + '_1', TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED)

		# Delete <CNT> again -> Fail
		r, rsc = DELETE(cntURL + '_1', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED)

		# Update CNT now with False
		dct = 	{ 'm2m:cnt' : {
					'disr' : False,
				}}
		TestCNT_CIN.cnt, rsc = UPDATE(cntURL + '_1', TestCNT_CIN.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, TestCNT_CIN.cnt)
		
		# Delete <CNT> again
		r, rsc = DELETE(cntURL + '_1', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.DELETED)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_autoDeleteCINnoNotifiction(self) -> None:
		"""	Automatic delete of <CIN> must not generate a notification for deleteDirectChild """

		# Create <CNT>
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mni' : 3
				}}
		TestCNT_CIN.cnt, rsc = CREATE(aeURL, TestCNT_CIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
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
		self.assertEqual(rsc, RC.CREATED, r)

		# Add more <CIN> than the capacity allows, so that some <CIN> will be deleted by the CSE
		clearLastNotification()
		for i in range(5):
			dct = 	{ 'm2m:cin' : {
						'con' : f'{i}',	
					}}
			_, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED)
		
		self.assertIsNone(getLastNotification(wait = notificationDelay))	# No notifications


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNT5CIN(self) -> None:
		""" Create <CNT> and 5 <CIN> """
		# Create <CNT>
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'mni' : 10
				}}
		TestCNT_CIN.cnt, rsc = CREATE(aeURL, TestCNT_CIN.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, TestCNT_CIN.cnt)

		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : testValue
				}}
		for _ in range(5):
			r, rsc = CREATE(cntURL, TestCNT_CIN.originator, T.CIN, dct)
			self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTOl(self) -> None:
		""" Delete <CNT>.OL """

		# get cni and cbs from parent container
		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		cni = findXPath(r, 'm2m:cnt/cni')
		cbs = findXPath(r, 'm2m:cnt/cbs')

		# Retrieve oldest
		ol, rsc = RETRIEVE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)

		# Delete oldest
		_, rsc = DELETE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.DELETED)

		# Retrieve new oldest and compare
		r, rsc = RETRIEVE(f'{cntURL}/ol', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertNotEqual(findXPath(r, 'm2m:cin/ri'), findXPath(ol, 'm2m:cin/ri'))

		# Compare container's cni and cbs after delete
		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(cni - 1, findXPath(r, 'm2m:cnt/cni'))
		self.assertEqual(cbs - len(testValue), findXPath(r, 'm2m:cnt/cbs'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTLA(self) -> None:
		""" Delete <CNT>.LA """

		# get cni and cbs from parent container
		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		cni = findXPath(r, 'm2m:cnt/cni')
		cbs = findXPath(r, 'm2m:cnt/cbs')

		# Retrieve latest
		ol, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)

		# Delete latest
		_, rsc = DELETE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.DELETED)

		# Retrieve new latest and compare
		r, rsc = RETRIEVE(f'{cntURL}/la', TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertNotEqual(findXPath(r, 'm2m:cin/ri'), findXPath(ol, 'm2m:cin/ri'))

		# Compare container's cni and cbs after delete
		r, rsc = RETRIEVE(cntURL, TestCNT_CIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(cni - 1, findXPath(r, 'm2m:cnt/cni'))
		self.assertEqual(cbs - len(testValue), findXPath(r, 'm2m:cnt/cbs'))


def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestCNT_CIN, [
			
		'test_addCIN',
		'test_addMoreCIN',
		'test_retrieveCNTLa',
		'test_retrieveCNTOl',
		'test_changeCNTMni',
		'test_deleteCINCheckCNT',
		'test_deleteCNT',

		'test_createCNTwithMBS',
		'test_createCINexactSize',
		'test_createCINtooBig',
		'test_createCINsForCNTwithSize',
		'test_deleteCNT',

		'test_createCNTwithDISR',
		'test_retrieveCINwithDISRFail',
		'test_retrieveLAwithDISRFail',
		'test_retrieveOLwithDISRFail',
		'test_discoverCINwithDISRFail',
		'test_deleteCINwithDISRFail',
		'test_deleteLAwithDISRFail',
		'test_updateCNTwithDISRFalse',
		'test_updateCNTwithDISRNullFalse',
		'test_retrieveCINwithDISRAllowed',
		'test_deleteCNT',
		'test_deleteCNTwithCINandDisr',

		'test_autoDeleteCINnoNotifiction',
		'test_deleteCNT',

		'test_createCNT5CIN',
		'test_deleteCNTOl',
		'test_deleteCNTLA',
		'test_deleteCNT',
	])

	# Run the tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
