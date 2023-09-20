#
#	testSUB.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for SUB functionality & notifications
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import NotificationEventType as NET, ResourceTypes as T, NotificationContentType, ResponseStatusCode as RC
from init import *

numberOfBatchNotifications = 5
durationForBatchNotifications = 2
durationForBatchNotificationsISO8601 = 'PT2S'

class TestSUB(unittest.TestCase):

	ae 				= None
	aeNoPoa 		= None
	aePoa 			= None
	originator 		= None
	originatorPoa 	= None
	cnt 			= None
	cntRI 			= None
	ae2URL 			= None
	aePOAURL		= None
	ae2Originator	= None
	excSub 			= None
	sub 			= None
	ts 				= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		# Start notification server
		startNotificationServer()

		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'

		testCaseStart('Setup TestSub')
		# create other resources
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ],
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		dct = 	{ 'm2m:ae' : {
					'rn'  : f'{aeRN}NoPOA', 
					'api' : APPID,
					'rr'  : True,
					'srv' : [ RELEASEVERSION ]
				}}
		cls.aeNoPoa, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create AE without poa'

		dct = 	{ 'm2m:ae' : {
					'rn'  : f'{aeRN}POA', 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ],
					'poa' : [ NOTIFICATIONSERVER ],
				}}
		cls.aePoa, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE with poa'
		cls.originatorPoa = findXPath(cls.aePoa, 'm2m:ae/aei')

		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		cls.cntRI = findXPath(cls.cnt, 'm2m:cnt/ri')

		# Add another AE URL
		cls.ae2URL = f'{cseURL}/{aeRN}2'
		cls.aePOAURL = f'{cseURL}/{aeRN}POA'

		testCaseEnd('Setup TestSub')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			stopNotificationServer()
			return
		testCaseStart('TearDown TestSub')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(f'{aeURL}NoPOA', ORIGINATOR)	# Just delete the NoPOA AE and everything below it. Ignore whether it exists or not
		DELETE(f'{aeURL}POA', ORIGINATOR)	# Just delete the POA AE and everything below it. Ignore whether it exists or not
		DELETE(f'{aeURL}2', ORIGINATOR)		# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestSub')
		stopNotificationServer()


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################

	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUB(self) -> None:
		"""	CREATE <SUB> under <CNT>. """
		clearLastNotification()	# clear the notification first
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.createDirectChild ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveSUB(self) -> None:
		"""	RETRIEVE <SUB>. """
		_, rsc = RETRIEVE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveSUBWithWrongOriginator(self) -> None:
		""" RETRIEVE <SUB> with wrong originator -> Fail"""
		_, rsc = RETRIEVE(subURL, 'Cwrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesSUB(self) -> None:
		"""	Test <SUB> attributes. """
		r, rsc = RETRIEVE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:sub/ty'), T.SUB)
		self.assertEqual(findXPath(r, 'm2m:sub/pi'), findXPath(TestSUB.cnt,'m2m:cnt/ri'))
		self.assertEqual(findXPath(r, 'm2m:sub/rn'), subRN)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:sub/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:sub/et'))
		self.assertIsNone(findXPath(r, 'm2m:sub/cr'))
		self.assertIsNotNone(findXPath(r, 'm2m:sub/enc/net'))
		self.assertIsInstance(findXPath(r, 'm2m:sub/enc/net'), list)
		self.assertEqual(len(findXPath(r, 'm2m:sub/enc/net')), 2)
		self.assertEqual(findXPath(r, 'm2m:sub/enc/net'), [1, 3])
		self.assertIsNotNone(findXPath(r, 'm2m:sub/nu'))
		self.assertIsInstance(findXPath(r, 'm2m:sub/nu'), list)
		self.assertEqual(findXPath(r, 'm2m:sub/nu'), [ NOTIFICATIONSERVER ])
		self.assertIsNotNone(findXPath(r, 'm2m:sub/nct'))
		self.assertIsInstance(findXPath(r, 'm2m:sub/nct'), int)
		self.assertEqual(findXPath(r, 'm2m:sub/nct'), 1)
		self.assertIsNone(findXPath(r, 'm2m:sub/nse'))
		self.assertIsNone(findXPath(r, 'm2m:sub/nsi'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWrong(self) -> None:
		""" CREATE <SUB> with unreachable notification URL -> Fail"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : f'{subRN}Wrong',
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.resourceDelete, NET.createDirectChild, NET.deleteDirectChild ]
        			},
        			'nu': [ NOTIFICATIONSERVERW ]
				}}
		_, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.SUBSCRIPTION_VERIFICATION_INITIATION_FAILED)
		
		# Try to retrieve subscription - Should fail
		_, rsc = RETRIEVE(f'{cntURL}/{subRN}Wrong', TestSUB.originator)
		self.assertEqual(rsc, RC.NOT_FOUND)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUB(self) -> None:
		"""	UPDATE <SUB> with exc """
		dct = 	{ 'm2m:sub' : { 
					'exc': 5
				}}
		r, rsc = UPDATE(subURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsInstance(findXPath(r, 'm2m:sub/exc'), int)
		self.assertEqual(findXPath(r, 'm2m:sub/exc'), 5)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUBwithNu(self) -> None:
		"""	CREATE <SUB> and update nu. """
		clearLastNotification()	# clear the notification first
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		# create
		dct = 	{ 'm2m:sub' : { 
        			'nu': [ TestSUB.originator ]
				}}
		sub, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, sub)
		subrn = findXPath(sub, 'm2m:sub/rn')

		# update
		dct = 	{ 'm2m:sub' : { 
        			'nu': [ NOTIFICATIONSERVER ]
				}}

		r, rsc = UPDATE(f'{cntURL}/{subrn}', TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertIsNotNone(lastNotification)
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))

		# delete
		_, rsc = DELETE(f'{cntURL}/{subrn}', TestSUB.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNT(self) -> None:
		"""	UPDATE <CNT> -> Send notification with full <CNT> resource"""
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'aTag' ],
					'mni' : 10,
					'mbs' : 9999
 				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		cnt, rsc = RETRIEVE(cntURL, TestSUB.originator)		# retrieve cnt again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/lbl'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/lbl'), list)
		self.assertGreater(len(findXPath(cnt, 'm2m:cnt/lbl')), 0)
		self.assertTrue('aTag' in findXPath(cnt, 'm2m:cnt/lbl'))
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mni'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/mni'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mni'), 10)
		self.assertIsNotNone(findXPath(cnt, 'm2m:cnt/mbs'))
		self.assertIsInstance(findXPath(cnt, 'm2m:cnt/mbs'), int)
		self.assertEqual(findXPath(cnt, 'm2m:cnt/mbs'), 9999)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/ty'), T.CNT)
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCIN2CNT(self) -> None:
		""" CREATE <CNI> to <CNT> -> Send notification withfull <CNI> resource"""
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'aValue'
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/ri'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cin/con'), 'aValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_removeCNT(self) -> None:
		"""	DELETE <CNT> -> <SUB> deleted as well. Send deletion notification"""
		r, rsc = DELETE(cntURL, TestSUB.originator)	# Just delete the Container and everything below it. Ignore whether it exists or not
		self.assertEqual(rsc, RC.DELETED)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sud'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCNTAgain(self) -> None:
		"""	CREATE <CNT> again -> Send notification with full <CNT> resource"""
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		TestSUB.cnt, rsc = CREATE(aeURL, TestSUB.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		TestSUB.cntRI = findXPath(TestSUB.cnt, 'm2m:cnt/ri')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBByUnknownOriginator(self) -> None:
		""" DELETE <SUB> with wrong originator -> Fail"""
		_, rsc = DELETE(subURL, 'Cwrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBByAssignedOriginator(self) -> None:
		""" DELETE <SUB> with correct originator -> Succeed. Send deletion notification. """
		r, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.DELETED, r)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sud'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBModifedAttributesWrong(self) -> None:
		""" CREATE <SUB> to monitor only modified attributes and on CREATE of child resource -> Fail """
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.createDirectChild ]
        			},
        			'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nct': NotificationContentType.modifiedAttributes
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBModifedAttributes(self) -> None:
		""" CREATE <SUB> to monitor only modified attributes and on UPDATE of child resource-> Send verification notification """
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate ]
        			},
        			'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nct': NotificationContentType.modifiedAttributes
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertEqual(findXPath(r, 'm2m:sub/nct'), NotificationContentType.modifiedAttributes)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTModifiedAttributes(self) -> None:
		""" UPDATE <CNT> -> Send notification with only the updated attributes"""
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'bTag' ]
 				}}
		_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/lbl'), [ 'bTag'])
		self.assertIsNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/ty'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTSameModifiedAttributes(self) -> None:
		""" UPDATE <CNT> again -> Send notification with only the same updated attributes"""
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'bTag' ]
 				}}
		_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/lbl'), [ 'bTag'])
		self.assertIsNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/ty'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBRI(self) -> None:
		""" CREATE <SUB> to monitor the RI of new or updated resources -> Send verification notification"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.createDirectChild ]
        			},
        			'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nct': NotificationContentType.ri
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertEqual(findXPath(r, 'm2m:sub/nct'), NotificationContentType.ri)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTRI(self) -> None:
		""" UPDATE <CNT> with lbl -> Send notification with RI"""
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'aTag' ]
 				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:uri'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:uri').endswith(findXPath(cnt, 'm2m:cnt/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBForBatchNotificationNumber(self) -> None:
		""" CREATE <SUB> with batch notification set to number -> Send verification notification"""
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					# No su! bc we want receive the last notification of a batch
					'bn': { 
						'num' : numberOfBatchNotifications
					}
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn'))
		self.assertEqual(findXPath(r, 'm2m:sub/bn/num'), numberOfBatchNotifications)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn/dur'))
		self.assertGreater(findXPath(r, 'm2m:sub/bn/dur'), 0)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTBatch(self) -> None:
		""" CREATE n <CNT> -> Send only one batch notification with all the notifications"""
		for i in range(0, numberOfBatchNotifications):
			dct = 	{ 'm2m:cnt' : {
						'lbl' : [ '%d' % i ]
					}}
			_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
			self.assertEqual(rsc, RC.UPDATED)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn'), lastNotification)
		for i in range(0, numberOfBatchNotifications):	# check availability and correct order
			self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{%d}/nev/rep/m2m:cnt/lbl' % i))
			self.assertEqual(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{%d}/nev/rep/m2m:cnt/lbl/{0}' % i), '%d' % i)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBForBatchReceiveRemainingNotifications(self) -> None:
		""" CREATE 1 <CNT>, then delete batch subscription -> Send outstanding notification in batch notification"""
		# Generate one last notification
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ '99' ]
				}}
		_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.DELETED)

		# Should have received the outstanding notification
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn'))
		self.assertEqual(len(findXPath(lastNotification, 'm2m:agn')), 1)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{0}/nev/rep/m2m:cnt/lbl'))
		self.assertEqual(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{0}/nev/rep/m2m:cnt/lbl/{0}'), '99')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBForBatchNotificationDuration(self) -> None:
		""" CREATE <SUB> with batch notification set to delay -> Send verification notification"""
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					# No su! bc we want receive the last notification of a batch
					'bn': { 
						'dur' : durationForBatchNotificationsISO8601
					}
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn'))
		self.assertIsNone(findXPath(r, 'm2m:sub/bn/num'))
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn/dur'))
		self.assertEqual(findXPath(r, 'm2m:sub/bn/dur'), durationForBatchNotificationsISO8601)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTBatchDuration(self) -> None:
		""" CREATE n <CNT> -> Send batch notification with all outstanding notifications after the timeout"""
		testSleep(durationForBatchNotifications) 	# wait a moment for other notifications
		clearLastNotification()
		for i in range(0, numberOfBatchNotifications):
			dct = 	{ 'm2m:cnt' : {
						'lbl' : [ '%d' % i ]
					}}
			_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
			self.assertEqual(rsc, RC.UPDATED)
		lastNotification = getLastNotification()	# Notifications should not have arrived yes
		self.assertIsNone(lastNotification)
		self.assertIsNone(findXPath(lastNotification, 'm2m:agn'))

		testSleep(durationForBatchNotifications * 2) 	# wait a moment
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn'))	# Should have arrived now
		for i in range(0, numberOfBatchNotifications):	# check availability and correct order
			self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{%d}/nev/rep/m2m:cnt/lbl' % i))
			self.assertEqual(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{%d}/nev/rep/m2m:cnt/lbl/{0}' % i), '%d' % i)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBForBatchNotificationDuration(self) -> None:
		""" DELETE <SUB>"""
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithEncAtr(self) -> None:
		""" CREATE <SUB> to monitor resource update, only specific attribute -> Send verification notification"""
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate ],
			            'atr': ['lbl' ]
					},
					'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/enc/atr'))
		self.assertEqual(findXPath(r, 'm2m:sub/enc/atr'), [ 'lbl' ])
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWithEncAtrLbl(self) -> None:
		""" UPDATE the resource with monitored attribute -> Send notification"""
		clearLastNotification()
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'hello' ]
				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)

		lastNotification = getLastNotification(wait = notificationDelay)	
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/lbl'), [ 'hello'])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWithEncAtrLblWrong(self) -> None:
		""" UPDATE the resource with not-monitored attribute -> Send NO notification"""
		clearLastNotification() # clear notification first, we don't want to receive a notification
		dct = 	{ 'm2m:cnt' : {
					'mni' : 99
				}}
		_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)

		lastNotification = getLastNotification()	# Notifications should not have arrived yes
		self.assertIsNone(lastNotification)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUBWithEncRemoved(self) -> None:
		""" UPDATE <sub> and remove ENC attribute"""
		dct = 	{ 'm2m:sub' : {
					'enc' : None
				}}
		r, rsc = UPDATE(subURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/enc'), r)
		self.assertEqual(findXPath(r, 'm2m:sub/enc/net/{0}'), NET.resourceUpdate, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBWithEncAtr(self) -> None:
		""" DELETE <SUB> """
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBBatchNotificationNumberWithLn(self) -> None:
		""" CREATE <SUB> with batch notification set to number and lastNoitification=True -> Send verification notification"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate ],	# update resource
					},
					'ln': True,
					'nu': [ NOTIFICATIONSERVER ],
					'bn': { 
						'num' : numberOfBatchNotifications
					}
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn'))
		self.assertEqual(findXPath(r, 'm2m:sub/bn/num'), numberOfBatchNotifications)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/ln'))
		self.assertEqual(findXPath(r, 'm2m:sub/ln'), True)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTBatchWithLn(self) -> None:
		""" CREATE n <CNT> -> Send batch notification with only the last outstanding notifications """
		for i in range(0, numberOfBatchNotifications):	# Adding more notification
			dct = 	{ 'm2m:cnt' : {
						'lbl' : [ '%d' % i ]
					}}
			_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
			self.assertEqual(rsc, RC.UPDATED)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn'))
		self.assertEqual(len(findXPath(lastNotification, 'm2m:agn/m2m:sgn')), 1)	 # ... but expecting only one
		lastNotificationHeaders = getLastNotificationHeaders()
		self.assertIsNotNone(lastNotificationHeaders[C.hfEC])
		self.assertEqual(lastNotificationHeaders[C.hfEC], '4') # 'latest'


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBBatchNotificationNumberWithLn(self) -> None:
		""" DELETE <SUB> """
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithEncChty(self) -> None:
		""" CREATE <SUB> to monitor ceration of child resources with type=container -> Send verification notification"""
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.createDirectChild ],	# create direct child resource
						'chty': [ T.CNT ] 	# only cnt
					},
					'ln': True,
					'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/enc/chty'))
		self.assertEqual(findXPath(r, 'm2m:sub/enc/chty'), [ T.CNT ])
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINWithEncChty(self) -> None:
		""" CREATE <CNI> -> Send NO notification"""
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'aValue'
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNone(getLastNotification())	# this shouldn't have caused a notification


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTWithEncChty(self) -> None:
		""" CREATE <CNT> -> Send notification"""
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}Sub'
				}}
		TestSUB.cnt, rsc = CREATE(cntURL, TestSUB.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(lastNotification, lastNotification)		# this must have caused a notification
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}Sub')
		_, rsc = DELETE(f'{cntURL}/{cntRN}Sub', TestSUB.originator)	# delete the sub-cnt
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBWithEncChty(self) -> None:
		""" DELETE <SUB> """
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAESUBwithOriginatorPOA(self) -> None:
		""" CREATE new <AE> and <SUB>. nu=poa of new originator -> NO verification request"""
		# create a second AE
		dct = 	{ 'm2m:ae' : {
			'rn'  : aeRN+'2', 
			'api' : APPID,
			'rr'  : True,
			'srv' : [ RELEASEVERSION ],
			'poa' : [ NOTIFICATIONSERVER ]
		}}
		ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestSUB.ae2Originator = findXPath(ae, 'm2m:ae/aei')

		# Create the sub
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN+'POA',
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.createDirectChild ]
					},
					'nu': [ TestSUB.ae2Originator ],
					'su': NOTIFICATIONSERVER
				}}
		r, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertIsNone(findXPath(lastNotification, 'm2m:sgn/vrq'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAESUBwithOriginatorPOANotReachable(self) -> None:
		""" CREATE new <AE>, <SUB>, <CNT>. Not request reachable, no notification request"""
		# create a second AE
		dct = 	{ 'm2m:ae' : {
			'rn'  : aeRN+'2', 
			'api' : APPID,
			'rr'  : False,
			'srv' : [ RELEASEVERSION ],
			'poa' : [ NOTIFICATIONSERVER ]
		}}
		ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestSUB.ae2Originator = findXPath(ae, 'm2m:ae/aei')

		# Create the sub
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN+'POA',
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.createDirectChild ]
					},
					'nu': [ TestSUB.ae2Originator ],
					'su': NOTIFICATIONSERVER
				}}
		r, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertIsNone(findXPath(lastNotification, 'm2m:sgn/vrq'))

		# Create the CNT
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}'
				}}
		TestSUB.cnt, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		lastNotification = getLastNotification()
		self.assertIsNone(lastNotification)		# this must have NOT caused a notification via the poa (because not request reachable)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithOriginatorPOA(self) -> None:
		""" CREATE <CNT> -> Send notification via AE.poa """
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}'
				}}
		TestSUB.cnt, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(lastNotification)		# this must have caused a notification via the poa
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAECSZwithOriginatorPOA(self) -> None:
		""" UPDATE <AE>.csz to 'application/cbor' """
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:ae' : { 
					'csz'  : ['application/cbor']
				}}
		r, rsc = UPDATE(TestSUB.ae2URL, TestSUB.ae2Originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/csz'))
		self.assertEqual(findXPath(r, 'm2m:ae/csz'), ['application/cbor'])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithOriginatorPOACBOR(self) -> None:
		""" CREATE <CNT> -> Send notification via <AE>.poa as application/cbor """
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}2'
				}}
		TestSUB.cnt, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		lastNotification = getLastNotification(wait = notificationDelay)
		lastHeaders = getLastNotificationHeaders()
		self.assertIsNotNone(lastNotification)		# this must have caused a notification via the poa
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}2')
		self.assertIn('Content-Type', lastHeaders)
		self.assertIn(lastHeaders['Content-Type'], [ 'application/cbor', 'application/vnd.onem2m-res+cbor' ])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEwithOriginatorPOA(self) -> None:
		""" DELETE <AE> and <SUB> """
		_, rsc = DELETE(TestSUB.ae2URL, TestSUB.ae2Originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAESUBwithURIctCBOR(self) -> None:
		""" CREATE new <AE> and <SUB>. nu=uri&ct=cbor -> Send verification request"""
		# create a second AE
		dct = 	{ 'm2m:ae' : {
			'rn'  : aeRN+'2', 
			'api' : APPID,
			'rr'  : True,
			'srv' : [ RELEASEVERSION ]
		}}
		ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestSUB.ae2URL = f'{cseURL}/{aeRN}2'
		TestSUB.ae2Originator = findXPath(ae, 'm2m:ae/aei')

		# Create the sub
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN+'POA',
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.createDirectChild ]
					},
					'nu': [ f'{NOTIFICATIONSERVER}?ct=cbor' ],
					'su': NOTIFICATIONSERVER
				}}
		_, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/vrq'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithURIctCBOR(self) -> None:
		""" CREATE <CNT> -> Send notification via URI as application/cbor """
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}2'
				}}
		TestSUB.cnt, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		lastNotification = getLastNotification(wait = notificationDelay)
		lastHeaders = getLastNotificationHeaders()
		self.assertIsNotNone(lastNotification)		# this must have caused a notification via the poa
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}2')
		self.assertIn('Content-Type', lastHeaders)
		self.assertIn(lastHeaders['Content-Type'], [ 'application/cbor', 'application/vnd.onem2m-res+cbor' ])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEwithURIctCBOR(self) -> None:
		""" DELETE <AE> and subscription """
		_, rsc = DELETE(TestSUB.ae2URL, TestSUB.ae2Originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBwithEXC(self) -> None:
		""" CREATE new <SUB> with EXC = 2 -> Send verification request"""
		# Create the sub
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN+'EXC',
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.createDirectChild ]
					},
					'nu': [NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'exc': 2	# Remove after 2 notifications
				}}
		TestSUB.excSub, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/vrq'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTforEXC(self) -> None:
		""" CREATE 2 <CNT> -> <SUB> with EXC removed """
		# Create a first container
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}3'
				}}
		TestSUB.cnt, rsc = CREATE(aeURL, TestSUB.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/ty'), T.CNT)
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}3')

		# Retrieve subscription
		testSleep(1) 	# wait a moment
		_, rsc = RETRIEVE(f'{aeURL}/{subRN}EXC', TestSUB.originator)
		self.assertEqual(rsc, RC.OK)

		# Create a second container
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}4'
				}}
		TestSUB.cnt, rsc = CREATE(aeURL, TestSUB.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)

		# Retrieve subscription
		testSleep(1) 	# wait a moment
		_, rsc = RETRIEVE(f'{aeURL}/{subRN}EXC', TestSUB.originator)
		self.assertEqual(rsc, RC.NOT_FOUND)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBwithUnknownPoa(self) -> None:
		""" CREATE new <SUB> with NU to not-existing POA -> Fail """
		# Create the sub
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN+'NOPOA',
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.createDirectChild ]
					},
					'nu': [ findXPath(TestSUB.aeNoPoa, 'm2m:ae/ri') ]	# this ae has no poa
				}}
		TestSUB.excSub, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.SUBSCRIPTION_VERIFICATION_INITIATION_FAILED)
		
	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithCreatorWrong(self) -> None:
		""" CREATE <SUB> with creator attribute (wrong) -> Fail """
		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
					'cr' : 'wrong',
				}}
		r, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)				# Not allowed
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithCreatorNull(self) -> None:
		""" UPDATE <SUB> with creator attribute set to Null """#

		clearLastNotification()
		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
					'cr' : None,
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.CREATED)
		self.assertEqual(findXPath(r, 'm2m:sub/cr'), TestSUB.originator)	# Creator should now be set to originator

		# Check the latest verification Request
		notification = getLastNotification()	# no delay! blocking
		self.assertIsNotNone(notification)
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn/vrq'), notification)
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn/cr'), notification)
		self.assertEqual(findXPath(notification, 'm2m:sgn/cr'), TestSUB.originator, notification)

		# Check whether creator is there in a RETRIEVE
		r, rsc = RETRIEVE(f'{cntURL}/{findXPath(r, "m2m:sub/rn")}', TestSUB.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:sub/cr'), TestSUB.originator)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_notifySUBWithCreatorNull(self) -> None:
		"""Notifification for <SUB> with creator attribute set to Null """#

		clearLastNotification()
		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
					'cr' : None,
			        'enc': {
			            'net': [ NET.resourceUpdate]
					},
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.CREATED)
		self.assertEqual(findXPath(r, 'm2m:sub/cr'), TestSUB.originator)	# Creator should now be set to originator

		# Check the latest verification Request
		notification = getLastNotification()	# no delay! blocking
		self.assertIsNotNone(notification)
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn/vrq'), notification)
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn/cr'), notification)
		self.assertEqual(findXPath(notification, 'm2m:sgn/cr'), TestSUB.originator, notification)

		# UPDATE CNT and generate notification
		clearLastNotification()
		dct = 	{ 'm2m:cnt': {
					'lbl' : [ 'aLabel' ],
				}}
		r, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)

		# Check the latest notification 
		notification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(notification)
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn/cr'), notification)
		self.assertEqual(findXPath(notification, 'm2m:sgn/cr'), TestSUB.originator, notification)
		self.assertEqual(findXPath(notification, 'm2m:sgn/nev/net'), NET.resourceUpdate)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBForMissingDataFail(self) -> None:
		""" CREATE <SUB> for Missing Data under <CNT> -> Fail"""
		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
			        'enc': {
			            'net': [ NET.reportOnGeneratedMissingDataPoints ]
					},				
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBForMissingDataFail2(self) -> None:
		""" CREATE <SUB> for Missing Data under <TS> with missing "missingData" -> Fail"""

		dct = 	{ 'm2m:ts' : { 	# type:ignore[var-annotated]
				}}
		ts, rsc = CREATE(aeURL, TestSUB.originator, T.TS, dct)
		self.assertEqual(rsc, RC.CREATED, ts)

		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
			        'enc': {
			            'net': [ NET.reportOnGeneratedMissingDataPoints ]
					},				
				}}
		r, rsc = CREATE(f'{aeURL}/{findXPath(ts, "m2m:ts/rn")}', TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBForMissingData(self) -> None:
		""" CREATE <SUB> for Missing Data under <TS>"""

		dct = 	{ 'm2m:ts' : {	# type:ignore[var-annotated]
				}}
		TestSUB.ts, rsc = CREATE(aeURL, TestSUB.originator, T.TS, dct)
		self.assertEqual(rsc, RC.CREATED, TestSUB.ts)

		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
			        'enc': {
			            'net': [ NET.reportOnGeneratedMissingDataPoints ],
						'md' : {
							'num' : 5,
							'dur' : 'PT10S'
						},
					},
				}}
		TestSUB.sub, rsc = CREATE(f'{aeURL}/{findXPath(TestSUB.ts, "m2m:ts/rn")}', TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.CREATED, TestSUB.sub)
		self.assertIn(8, findXPath(TestSUB.sub, 'm2m:sub/enc/net'), TestSUB.sub)
		self.assertEqual(findXPath(TestSUB.sub, 'm2m:sub/enc/md/num'), 5, TestSUB.sub)
		self.assertEqual(findXPath(TestSUB.sub, 'm2m:sub/enc/md/dur'), 'PT10S', TestSUB.sub)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUBForMissingData(self) -> None:
		""" UPDATE <SUB> for Missing Data under <TS>"""
		dct = 	{ 'm2m:sub' : { 
			        'enc': {
			            'net': [ NET.reportOnGeneratedMissingDataPoints ],
						'md' : {
							'num' : 10,
							'dur' : 'PT20S'
						},
					}
				}}
		r, rsc = UPDATE(f'{aeURL}/{findXPath(TestSUB.ts, "m2m:ts/rn")}/{findXPath(TestSUB.sub, "m2m:sub/rn")}', TestSUB.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIn(8, findXPath(r, 'm2m:sub/enc/net'), r)
		self.assertEqual(findXPath(r, 'm2m:sub/enc/md/num'), 10, r)
		self.assertEqual(findXPath(r, 'm2m:sub/enc/md/dur'), 'PT20S', r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBForMissingData(self) -> None:
		""" DELETE <SUB> for Missing Data under <TS>"""
		r, rsc = DELETE(f'{aeURL}/{findXPath(TestSUB.ts, "m2m:ts/rn")}/{findXPath(TestSUB.sub, "m2m:sub/rn")}', TestSUB.originator)
		self.assertEqual(rsc, RC.DELETED, r)



# TODO update missing data subscription
# TODO delete missing data subscription
# TODO add test for subscription with enc/md subscription to a non-TS parent

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBForMissingDataWrongDataFail(self) -> None:
		""" CREATE <SUB> for Missing Data under <TS> with various wrong formats -> Fail"""

		dct = 	{ 'm2m:ts' : {	# type:ignore[var-annotated]
				}}
		ts, rsc = CREATE(aeURL, TestSUB.originator, T.TS, dct)
		self.assertEqual(rsc, RC.CREATED, ts)

		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
			        'enc': {
			            'net': [ NET.reportOnGeneratedMissingDataPoints ],
						'md' : {
							'num' : -5,
							'dur' : 'PT10S'
						},
					},
				}}
		r, rsc = CREATE(f'{aeURL}/{findXPath(ts, "m2m:ts/rn")}', TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
			        'enc': {
			            'net': [ NET.reportOnGeneratedMissingDataPoints ],
						'md' : {
							'num' : 5,
						},
					},
				}}
		r, rsc = CREATE(f'{aeURL}/{findXPath(ts, "m2m:ts/rn")}', TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
			        'enc': {
			            'net': [ NET.reportOnGeneratedMissingDataPoints ],
						'md' : {
							'dur' : 'PT10S',
						},
					},
				}}
		r, rsc = CREATE(f'{aeURL}/{findXPath(ts, "m2m:ts/rn")}', TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
			        'enc': {
			            'net': [ NET.reportOnGeneratedMissingDataPoints ],
						'md' : {
							'num' : 5,
							'dur' : '10'
						},
					},
				}}
		r, rsc = CREATE(f'{aeURL}/{findXPath(ts, "m2m:ts/rn")}', TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
			        'enc': {
			            'net': [ NET.reportOnGeneratedMissingDataPoints ],
						'md' : {
							'num' : 5,
							'dur' : 10
						},
					},
				}}
		r, rsc = CREATE(f'{aeURL}/{findXPath(ts, "m2m:ts/rn")}', TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithWrongCHTYFail(self) -> None:
		""" CREATE <SUB> with wrong CHTY -> Fail"""

		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
			        'enc': {
			            'net':  [ NET.deleteDirectChild ],
						'chty': [ T.AE ]
					},
				}}
		TestSUB.sub, rsc = CREATE(f'{aeURL}', TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, TestSUB.sub)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUBWithWrongCHTYFail(self) -> None:
		""" UPDATE <SUB> with wrong CHTY -> Fail"""

		# create a valid SUB
		dct = 	{ 'm2m:sub' : { 
					'rn': 'sub_chty_test',
					'nu': [NOTIFICATIONSERVER ],
			        'enc': {
			            'net':  [ NET.deleteDirectChild ],
						'chty': [ T.CNT ]
					},
				}}
		TestSUB.sub, rsc = CREATE(f'{aeURL}', TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.CREATED, TestSUB.sub)

		# update it with wrong chty
		dct =	{ 'm2m:sub' : {
					'enc': {
						'chty': [ T.AE ]
					},	
				}}
		TestSUB.sub, rsc = UPDATE(f'{aeURL}/sub_chty_test', TestSUB.originator, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, TestSUB.sub)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithStructuredNu(self) -> None:
		""" CREATE <SUB> with structured ID in NU"""
		clearLastNotification()
		dct = 	{ 'm2m:sub' : { 
					'nu': [ f'{CSERN}/{aeRN}POA' ],
			        'enc': {
			            'net':  [ NET.createDirectChild ],
					},
				}}
		r, rsc = CREATE(self.aePOAURL, TestSUB.originatorPoa, T.SUB, dct)	
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNone(getLastNotification(wait = notificationDelay))

		r, rsc = DELETE(f'{self.aePOAURL}/{findXPath(r, "m2m:sub/rn")}', TestSUB.originatorPoa)	
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSubBlockingUpdateWrongNUFail(self) -> None:
		""" CREATE <SUB> for blocking Update with wrong NU -> Fail"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ NOTIFICATIONSERVERW ],
			        'enc': {
			            'net':  [ NET.blockingUpdate ],
					},
				}}
		r, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.SUBSCRIPTION_VERIFICATION_INITIATION_FAILED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSubBlockingUpdateMultipleNUFail(self) -> None:
		""" CREATE <SUB> for blocking Update with multiple NU -> Fail"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ f'{CSERN}/{aeRN}POA', NOTIFICATIONSERVER ],
			        'enc': {
			            'net':  [ NET.blockingUpdate ],
					},
				}}
		r, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSubBlockingUpdateDisallowedAttributeFail(self) -> None:
		""" CREATE <SUB> for blocking Update with disallowed resource attribute -> Fail"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ f'{CSERN}/{aeRN}POA' ],
			        'enc': {
			            'net':  [ NET.blockingUpdate ],
					},
					'bn': { 
						'num' : numberOfBatchNotifications
					}
				}}
		r, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSubBlockingUpdateDisallowedENCAttributeFail(self) -> None:
		""" CREATE <SUB> for blocking Update with disallowed "enc" attribute -> Fail"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ f'{CSERN}/{aeRN}POA' ],
			        'enc': {
			            'net':  [ NET.blockingUpdate ],
						'sza': 0,
					},
				}}
		r, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSubBlockingUpdateDisallowedNCTvaluel(self) -> None:
		""" CREATE <SUB> for blocking Update with disallowed "nct" value -> Fail"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ f'{CSERN}/{aeRN}POA' ],
			        'enc': {
			            'net':  [ NET.blockingUpdate ],
					},
					'nct': NotificationContentType.allAttributes,
				}}
		r, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSubBlockingUpdate(self) -> None:
		""" CREATE <SUB> for blocking Update"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ f'{CSERN}/{aeRN}POA' ],
			        'enc': {
			            'net': [ NET.blockingUpdate ],
						'atr': [ 'lbl' ],
					},
					'nct': NotificationContentType.modifiedAttributes,
				}}
		r, rsc = CREATE(self.aePOAURL, TestSUB.originatorPoa, T.SUB, dct)	
		self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSubBlockingUpdateFail(self) -> None:
		""" UDPATE <SUB> for blocking Update with blocking NET -> Fail"""
		dct = 	{ 'm2m:sub' : { 
			        'enc': {
			            'net':  [ NET.blockingUpdate ],	# any blocking * in UPDATE is not allowed
					},
				}}
		r, rsc = UPDATE(f'{self.aePOAURL}/{subRN}', TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_doBlockingUpdate(self) -> None:
		""" Perform BLOCKING UPDATE on <AE>"""
		clearLastNotification()
		dct =	{ 'm2m:ae' : {
					'lbl' : [ 'aLabel' ]
				}}
		r, rsc = UPDATE(self.aePOAURL, TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.UPDATED, r)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(lastNotification)
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/net'), NET.blockingUpdate)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:ae/lbl'), lastNotification)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_doBlockingUpdateAttributeCondition(self) -> None:
		""" Perform BLOCKING UPDATE on <AE> with not-set attribute condition"""
		clearLastNotification()
		dct =	{ 'm2m:ae' : {
					'apn' : 'somethingElse'
				}}
		r, rsc = UPDATE(self.aePOAURL, TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNone(getLastNotification(wait = notificationDelay))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_doBlockingUpdateNegativeNotificationResponse(self) -> None:
		""" Perform BLOCKING UPDATE on <AE> and receive a negative response"""
		clearLastNotification(nextResult = ResponseStatusCode.OPERATION_NOT_ALLOWED)
		dct =	{ 'm2m:ae' : {
					'lbl' : [ 'aLabel' ]
				}}
		r, rsc = UPDATE(self.aePOAURL, TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.OPERATION_DENIED_BY_REMOTE_ENTITY, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSubBlockingUpdate(self) -> None:
		""" DELETE <SUB> for BLOCKING UPDATE"""
		r, rsc = DELETE(f'{self.aePOAURL}/{subRN}', TestSUB.originatorPoa)
		self.assertEqual(rsc, RC.DELETED, r)


	#########################################################################
	#
	#	NotificationStats tests
	#


	def test_createSUBForNotificationStats(self) -> None:
		"""	CREATE <SUB> under POA <AE> with notificationStats enabled. """
		clearLastNotification()	# clear the notification first
		self.assertIsNotNone(TestSUB.aePoa)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.createDirectChild ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nse': True
				}}
		r, rsc = CREATE(self.aePOAURL, TestSUB.originatorPoa, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/nse'))
		self.assertEqual(findXPath(r, 'm2m:sub/nse'), True)
		self.assertIsNone(findXPath(r, 'm2m:sub/nsi'))
		
		lastNotification = getLastNotification()	# no delay! blocking
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAECheckStats(self) -> None:
		""" UPDATE <AE> and check new stats"""
		dct =	{ 'm2m:ae' : {
					'lbl' : [ 'test' ]
				}}
		r, rsc = UPDATE(f'{self.aePOAURL}', TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.UPDATED, r)

		# retrieve <sub> to get the stats
		testSleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{self.aePOAURL}/{subRN}', TestSUB.originatorPoa)	
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/rqs'), 1, r)		# Change counts if order of TC changes
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/rsr'), 1, r)
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/noec'), 1, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUBNSEFalse(self) -> None:
		""" UPDATE <sub> with nse False"""
		dct =	{ 'm2m:sub' : {
					'nse' : False
				}}
		r, rsc = UPDATE(f'{self.aePOAURL}/{subRN}', TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.UPDATED, r)
		# nsi is kept after nse update to FALSE
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/rqs'), 1, r)		# Change counts if order of TC changes
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/rsr'), 1, r)
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/noec'), 1, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUBNSETrue(self) -> None:
		""" UPDATE <sub> with nse True"""
		dct =	{ 'm2m:sub' : {
					'nse' : True
				}}
		r, rsc = UPDATE(f'{self.aePOAURL}/{subRN}', TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.UPDATED, r)
		# nsi must be empty
		self.assertIsNone(findXPath(r, 'm2m:sub/nsi'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUBNSETrueAgain(self) -> None:
		""" UPDATE <sub> with nse True again"""

		# Create some counts first
		dct:JSON =	{ 'm2m:ae' : {
					'lbl' : [ 'test' ]
				}}
		r, rsc = UPDATE(f'{self.aePOAURL}', TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.UPDATED, r)

		# retrieve <sub> to get the stats
		testSleep(notificationDelay)
		r, rsc = RETRIEVE(f'{self.aePOAURL}/{subRN}', TestSUB.originatorPoa)	
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(len(findXPath(r, 'm2m:sub/nsi')), 1, r)
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/rqs'), 1, r)		# Change counts if order of TC changes
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/rsr'), 1, r)
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/noec'), 1, r)

		# Set nse to True again, and clear the counts
		dct =	{ 'm2m:sub' : {
					'nse' : True
				}}
		r, rsc = UPDATE(f'{self.aePOAURL}/{subRN}', TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.UPDATED, r)
		# nsi must be empty
		self.assertIsNone(findXPath(r, 'm2m:sub/nsi'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUBcountBatchNotifications(self) -> None:
		""" Count batch notifications """

		# Enable batch notifications for the sub, and clear the count
		dct:JSON =	{ 'm2m:sub' : {
					'nse': True,
					'bn': { 
						'num' : numberOfBatchNotifications
					}
				}}
		r, rsc = UPDATE(f'{self.aePOAURL}/{subRN}', TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn/num'), r)
		# nsi must be empty
		self.assertIsNone(findXPath(r, 'm2m:sub/nsi'), r)


		# Make some Updates and cause a batch notification
		for _ in range(numberOfBatchNotifications):
			# Create some counts first
			dct =	{ 'm2m:ae' : {
						'lbl' : [ 'test' ]
					}}
			r, rsc = UPDATE(f'{self.aePOAURL}', TestSUB.originatorPoa, dct)	
			self.assertEqual(rsc, RC.UPDATED, r)
		testSleep(1)	# Just wait a moment to give the CSE some time
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn'), lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn'), lastNotification)
		self.assertEqual(len(findXPath(lastNotification, 'm2m:agn/m2m:sgn')), numberOfBatchNotifications, lastNotification)

		# retrieve <sub> to get the stats
		r, rsc = RETRIEVE(f'{self.aePOAURL}/{subRN}', TestSUB.originatorPoa)	
		self.assertEqual(rsc, RC.OK, r)
		# nsi must now be set
		self.assertIsNotNone(findXPath(r, 'm2m:sub/nsi'), r)
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/rqs'), 5, r)		# Change counts if order of TC changes
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/rsr'), 5, r)
		self.assertEqual(findXPath(r, 'm2m:sub/nsi/{0}/noec'), 5, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUBDeleteNSE(self) -> None:
		""" UPDATE <sub> with deleted nse attribute"""
		dct =	{ 'm2m:sub' : {
					'nse' : None
				}}
		r, rsc = UPDATE(f'{self.aePOAURL}/{subRN}', TestSUB.originatorPoa, dct)	
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNone(findXPath(r, 'm2m:sub/nse'), r)
		self.assertIsNone(findXPath(r, 'm2m:sub/nsi'), r)

#
#	Test defaults
#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBnoNCTwrongNETFail(self) -> None:
		""" CREATE <sub> with no NCT and conflicting NCT -> Fail """
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.blockingUpdate ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nse': True
				}}
		r, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)
	

#
#	Misc tests
#

	def test_deleteNuAttributeFail(self) -> None:
		"""	Delete "nu" attribute from SUB -> Fail """
		clearLastNotification()	# clear the notification first
		self.assertIsNotNone(TestSUB.aePoa)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.createDirectChild ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
				}}
		r, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED)
		dct = 	{ 'm2m:sub' : { 
					'nu' : None
				}}
		r, rsc = UPDATE(f'{aeURL}/{subRN}', TestSUB.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)

		# delete resource
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestSUB.originator)
		self.assertEqual(rsc, RC.DELETED)



	


# TODO check different NET's (ae->cnt->sub, add cnt to cnt)
def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
		
	addTest(suite, TestSUB('test_createSUB'))
	addTest(suite, TestSUB('test_retrieveSUB'))
	addTest(suite, TestSUB('test_retrieveSUBWithWrongOriginator'))
	addTest(suite, TestSUB('test_attributesSUB'))

	addTest(suite, TestSUB('test_createSUBWrong'))
	addTest(suite, TestSUB('test_updateSUB'))
	addTest(suite, TestSUB('test_updateSUBwithNu'))
	addTest(suite, TestSUB('test_updateCNT'))
	addTest(suite, TestSUB('test_addCIN2CNT'))
	addTest(suite, TestSUB('test_removeCNT'))
	addTest(suite, TestSUB('test_addCNTAgain'))

	addTest(suite, TestSUB('test_createSUB'))
	addTest(suite, TestSUB('test_deleteSUBByUnknownOriginator'))
	addTest(suite, TestSUB('test_deleteSUBByAssignedOriginator'))

	addTest(suite, TestSUB('test_createSUBModifedAttributesWrong'))
	addTest(suite, TestSUB('test_createSUBModifedAttributes'))
	addTest(suite, TestSUB('test_updateCNTModifiedAttributes'))
	addTest(suite, TestSUB('test_updateCNTSameModifiedAttributes'))
	addTest(suite, TestSUB('test_deleteSUBByAssignedOriginator'))

	addTest(suite, TestSUB('test_createSUBRI'))
	addTest(suite, TestSUB('test_updateCNTRI'))
	addTest(suite, TestSUB('test_deleteSUBByAssignedOriginator'))

	# Batch Notify
	addTest(suite, TestSUB('test_createSUBForBatchNotificationNumber'))
	addTest(suite, TestSUB('test_updateCNTBatch'))
	addTest(suite, TestSUB('test_deleteSUBForBatchReceiveRemainingNotifications'))

	addTest(suite, TestSUB('test_createSUBForBatchNotificationDuration'))
	addTest(suite, TestSUB('test_updateCNTBatchDuration'))
	addTest(suite, TestSUB('test_deleteSUBForBatchNotificationDuration'))


	addTest(suite, TestSUB('test_createSUBWithEncAtr'))	# attribute
	addTest(suite, TestSUB('test_updateCNTWithEncAtrLbl'))
	addTest(suite, TestSUB('test_updateCNTWithEncAtrLblWrong'))
	addTest(suite, TestSUB('test_updateSUBWithEncRemoved'))	# Check default enc in UPDATE
	addTest(suite, TestSUB('test_deleteSUBWithEncAtr'))

	addTest(suite, TestSUB('test_createSUBBatchNotificationNumberWithLn'))	# Batch + latestNotify
	addTest(suite, TestSUB('test_updateCNTBatchWithLn'))
	addTest(suite, TestSUB('test_deleteSUBBatchNotificationNumberWithLn'))

	addTest(suite, TestSUB('test_createSUBWithEncChty'))	# child resource type
	addTest(suite, TestSUB('test_createCINWithEncChty'))
	addTest(suite, TestSUB('test_createCNTWithEncChty'))
	addTest(suite, TestSUB('test_deleteSUBWithEncChty'))

	addTest(suite, TestSUB('test_createAESUBwithOriginatorPOA'))
	addTest(suite, TestSUB('test_createCNTwithOriginatorPOA'))
	addTest(suite, TestSUB('test_updateAECSZwithOriginatorPOA'))
	addTest(suite, TestSUB('test_createCNTwithOriginatorPOACBOR'))
	addTest(suite, TestSUB('test_deleteAEwithOriginatorPOA'))

	# With non-reqzest reachable 
	addTest(suite, TestSUB('test_createAESUBwithOriginatorPOANotReachable'))
	addTest(suite, TestSUB('test_deleteAEwithOriginatorPOA'))

	addTest(suite, TestSUB('test_createAESUBwithURIctCBOR'))
	addTest(suite, TestSUB('test_createCNTwithURIctCBOR'))
	addTest(suite, TestSUB('test_deleteAEwithURIctCBOR'))

	# ExpirationCounter
	addTest(suite, TestSUB('test_createSUBwithEXC'))
	addTest(suite, TestSUB('test_createCNTforEXC'))

	addTest(suite, TestSUB('test_createSUBwithUnknownPoa'))
	addTest(suite, TestSUB('test_createSUBWithCreatorWrong'))
	addTest(suite, TestSUB('test_createSUBWithCreatorNull'))
	addTest(suite, TestSUB('test_notifySUBWithCreatorNull'))

	# Missing Data
	addTest(suite, TestSUB('test_createSUBForMissingDataFail'))
	addTest(suite, TestSUB('test_createSUBForMissingDataFail2'))
	addTest(suite, TestSUB('test_createSUBForMissingData'))
	addTest(suite, TestSUB('test_updateSUBForMissingData'))
	addTest(suite, TestSUB('test_deleteSUBForMissingData'))
	addTest(suite, TestSUB('test_createSUBForMissingDataWrongDataFail'))

	# Wrong CHTY
	addTest(suite, TestSUB('test_createSUBWithWrongCHTYFail'))
	addTest(suite, TestSUB('test_updateSUBWithWrongCHTYFail'))

	# Structured NU
	addTest(suite, TestSUB('test_createSUBWithStructuredNu'))

	# blocking update tests
	addTest(suite, TestSUB('test_createSubBlockingUpdateWrongNUFail'))
	addTest(suite, TestSUB('test_createSubBlockingUpdateMultipleNUFail'))
	addTest(suite, TestSUB('test_createSubBlockingUpdateDisallowedAttributeFail'))
	addTest(suite, TestSUB('test_createSubBlockingUpdateDisallowedENCAttributeFail'))
	addTest(suite, TestSUB('test_createSubBlockingUpdateDisallowedNCTvaluel'))
	addTest(suite, TestSUB('test_createSubBlockingUpdate'))
	addTest(suite, TestSUB('test_updateSubBlockingUpdateFail'))
	addTest(suite, TestSUB('test_doBlockingUpdate'))
	addTest(suite, TestSUB('test_doBlockingUpdateAttributeCondition'))
	addTest(suite, TestSUB('test_doBlockingUpdateNegativeNotificationResponse'))
	addTest(suite, TestSUB('test_deleteSubBlockingUpdate'))

	# TODO blocking RETRIEVE tests when official

	# NotificationStats tests
	addTest(suite, TestSUB('test_createSUBForNotificationStats'))
	addTest(suite, TestSUB('test_updateAECheckStats'))
	addTest(suite, TestSUB('test_updateSUBNSEFalse'))
	addTest(suite, TestSUB('test_updateSUBNSETrue'))
	addTest(suite, TestSUB('test_updateSUBNSETrueAgain'))
	addTest(suite, TestSUB('test_updateSUBcountBatchNotifications'))
	addTest(suite, TestSUB('test_updateSUBDeleteNSE'))

	# Test defaults
	addTest(suite, TestSUB('test_createSUBnoNCTwrongNETFail'))

	# Misc tests
	addTest(suite, TestSUB('test_deleteNuAttributeFail'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
