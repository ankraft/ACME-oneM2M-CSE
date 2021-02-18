#
#	testSUB.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for SUB functionality & notifications
#

import unittest, sys, time
import requests
sys.path.append('../acme')
from typing import Tuple
from Constants import Constants as C
from Types import ResourceTypes as T, NotificationContentType, ResponseCode as RC
from init import *

numberOfBatchNotifications = 5
durationForBatchNotifications = 2
durationForBatchNotificationsISO8601 = 'PT2S'

class TestSUB(unittest.TestCase):

	ae 				= None
	aeNoPoa 		= None
	originator 		= None
	cnt 			= None
	cntRI 			= None
	ae2URL 			= None
	ae2Originator	= None
	excSub 			= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		# Start notification server
		startNotificationServer()

		# look for notification server
		hasNotificationServer = False
		try:
			_ = requests.post(NOTIFICATIONSERVER, data='{"test": "test"}', verify=verifyCertificate)
			hasNotificationServer = True
		except Exception:
			pass
		finally:	
			assert hasNotificationServer, 'Notification server cannot be reached'

		# create other resources
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		dct = 	{ 'm2m:ae' : {
					'rn'  : f'{aeRN}NoPOA', 
					'api' : 'NMyApp1Id',
					'rr'  : False,
					'srv' : [ '3' ]
				}}
		cls.aeNoPoa, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create AE withoutt poa'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		cls.cntRI = findXPath(cls.cnt, 'm2m:cnt/ri')

		# Add another AE URL
		cls.ae2URL = f'{cseURL}/{aeRN}2'



	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(f'{aeURL}NoPOA', ORIGINATOR)	# Just delete the NoPoa AE and everything below it. Ignore whether it exists or not
		DELETE(cls.ae2URL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()

	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUB(self) -> None:
		"""	Create <SUB> under <CNT>. """
		clearLastNotification()	# clear the notification first
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1, 3 ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveSUB(self) -> None:
		"""	Retrieve <SUB>. """
		_, rsc = RETRIEVE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveSUBWithWrongOriginator(self) -> None:
		""" Retrieve <SUB> with wrong originator -> Fail"""
		_, rsc = RETRIEVE(subURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


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


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWrong(self) -> None:
		""" Create <SUB> with unreachable notification URL -> Fail"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : f'{subRN}Wrong',
			        'enc': {
			            'net': [ 1, 2, 3, 4 ]
        			},
        			'nu': [ NOTIFICATIONSERVERW ]
				}}
		_, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertNotEqual(rsc, RC.created)
		self.assertEqual(rsc, RC.subscriptionVerificationInitiationFailed)
		
		# Try to retrieve subscription - Should fail
		_, rsc = RETRIEVE(f'{cntURL}/{subRN}Wrong', TestSUB.originator)
		self.assertEqual(rsc, RC.notFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUB(self) -> None:
		"""	Update <SUB> with exc """
		dct = 	{ 'm2m:sub' : { 
					'exc': 5
				}}
		r, rsc = UPDATE(subURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertIsInstance(findXPath(r, 'm2m:sub/exc'), int)
		self.assertEqual(findXPath(r, 'm2m:sub/exc'), 5)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNT(self) -> None:
		"""	Update <CNT> -> Send notification with full <CNT> resource"""
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'aTag' ],
					'mni' : 10,
					'mbs' : 9999
 				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.updated)
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
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/ty'), T.CNT)
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCIN2CNT(self) -> None:
		""" Add <CNI> to <CNT> -> Send notification withfull <CNI> resource"""
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'aValue'
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/ri'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cin/con'), 'aValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_removeCNT(self) -> None:
		"""	Remove <CNT> -> <SUB> deleted as well. Send deletion notification"""
		r, rsc = DELETE(cntURL, TestSUB.originator)	# Just delete the Container and everything below it. Ignore whether it exists or not
		self.assertEqual(rsc, RC.deleted)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sud'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCNTAgain(self) -> None:
		"""	Add <CNT> again -> Send notification with full <CNT> resource"""
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		TestSUB.cnt, rsc = CREATE(aeURL, TestSUB.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		TestSUB.cntRI = findXPath(TestSUB.cnt, 'm2m:cnt/ri')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBByUnknownOriginator(self) -> None:
		""" Remove <SUB> with wrong originator -> Fail"""
		_, rsc = DELETE(subURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBByAssignedOriginator(self) -> None:
		""" Remove <SUB> with correct originator -> Succeed. Send deletion notification. """
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sud'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBModifedAttributesWrong(self) -> None:
		""" Create <SUB> to monitor only modified attributes and on CREATE of child resource -> Fail """
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 3 ]
        			},
        			'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nct': NotificationContentType.modifiedAttributes
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBModifedAttributes(self) -> None:
		""" Create <SUB> to monitor only modified attributes and on UPDATE of child resource-> Send verification notification """
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1 ]
        			},
        			'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nct': NotificationContentType.modifiedAttributes
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:sub/nct'), NotificationContentType.modifiedAttributes)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTModifiedAttributes(self) -> None:
		""" Update <CNT> -> Send notification with only the updated attributes"""
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'bTag' ]
 				}}
		_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/lbl'), [ 'bTag'])
		self.assertIsNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/ty'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTSameModifiedAttributes(self) -> None:
		""" Update <CNT> again -> Send notification with only the same updated attributes"""
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'bTag' ]
 				}}
		_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/lbl'), [ 'bTag'])
		self.assertIsNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/ty'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBRI(self) -> None:
		""" Create <SUB> to monitor the RI of new or updated resources -> Send verification notification"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1, 3 ]
        			},
        			'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nct': NotificationContentType.ri
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:sub/nct'), NotificationContentType.ri)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTRI(self) -> None:
		""" Update <CNT> with lbl -> Send notification with RI"""
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'aTag' ]
 				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:uri'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:uri').endswith(findXPath(cnt, 'm2m:cnt/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBForBatchNotificationNumber(self) -> None:
		""" Create <SUB> with batch notification set to number -> Send verification notification"""
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1 ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					# No su! bc we want receive the last notification of a batch
					'bn': { 
						'num' : numberOfBatchNotifications
					}
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn'))
		self.assertEqual(findXPath(r, 'm2m:sub/bn/num'), numberOfBatchNotifications)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn/dur'))
		self.assertGreater(findXPath(r, 'm2m:sub/bn/dur'), 0)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTBatch(self) -> None:
		""" Create n <CNT> -> Send only one batch notification with all the notifications"""
		for i in range(0, numberOfBatchNotifications):
			dct = 	{ 'm2m:cnt' : {
						'lbl' : [ '%d' % i ]
					}}
			_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
			self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn'))
		for i in range(0, numberOfBatchNotifications):	# check availability and correct order
			self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{%d}/nev/rep/m2m:cnt/lbl' % i))
			self.assertEqual(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{%d}/nev/rep/m2m:cnt/lbl/{0}' % i), '%d' % i)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBForBatchReceiveRemainingNotifications(self) -> None:
		""" Create 1 <CNT>, then delete batch subscription -> Send outstanding notification in batch notification"""
		# Generate one last notification
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ '99' ]
				}}
		_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.updated)
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)

		# Should have received the outstanding notification
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn'))
		self.assertEqual(len(findXPath(lastNotification, 'm2m:agn')), 1)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{0}/nev/rep/m2m:cnt/lbl'))
		self.assertEqual(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{0}/nev/rep/m2m:cnt/lbl/{0}'), '99')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBForBatchNotificationDuration(self) -> None:
		""" Create <SUB> with batch notification set to delay -> Send verification notification"""
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1 ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					# No su! bc we want receive the last notification of a batch
					'bn': { 
						'dur' : durationForBatchNotificationsISO8601
					}
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn'))
		self.assertIsNone(findXPath(r, 'm2m:sub/bn/num'))
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn/dur'))
		self.assertEqual(findXPath(r, 'm2m:sub/bn/dur'), durationForBatchNotificationsISO8601)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTBatchDuration(self) -> None:
		""" Create n <CNT> -> Send batch notification with all outstanding notifications after the timeout"""
		for i in range(0, numberOfBatchNotifications):
			dct = 	{ 'm2m:cnt' : {
						'lbl' : [ '%d' % i ]
					}}
			_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
			self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()	# Notifications should not have arrived yes
		self.assertIsNone(findXPath(lastNotification, 'm2m:agn'))

		time.sleep(durationForBatchNotifications * 2) 	# wait a moment
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn'))	# Should have arrived now
		for i in range(0, numberOfBatchNotifications):	# check availability and correct order
			self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{%d}/nev/rep/m2m:cnt/lbl' % i))
			self.assertEqual(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{%d}/nev/rep/m2m:cnt/lbl/{0}' % i), '%d' % i)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBForBatchNotificationDuration(self) -> None:
		""" Delete <SUB>"""
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithEncAtr(self) -> None:
		""" Create <SUB> to monitor resource update, only specific attribute -> Send verification notification"""
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1 ],
			            'atr': ['lbl' ]
					},
					'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/enc/atr'))
		self.assertEqual(findXPath(r, 'm2m:sub/enc/atr'), [ 'lbl' ])
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWithEncAtrLbl(self) -> None:
		""" Update the resource with monitored attribute -> Send notification"""
		clearLastNotification()
		dct = 	{ 'm2m:cnt' : {
					'lbl' : [ 'hello' ]
				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.updated)

		lastNotification = getLastNotification()	# Notifications should not have arrived yes
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/lbl'), [ 'hello'])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWithEncAtrLblWrong(self) -> None:
		""" Update the resource with not-monitored attribute -> Send NO notification"""
		clearLastNotification() # clear notification first, we don't want to receive a notification
		dct = 	{ 'm2m:cnt' : {
					'mni' : 99
				}}
		_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
		self.assertEqual(rsc, RC.updated)

		lastNotification = getLastNotification()	# Notifications should not have arrived yes
		self.assertIsNone(lastNotification)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBWithEncAtr(self) -> None:
		""" Delete <SUB> """
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBBatchNotificationNumberWithLn(self) -> None:
		""" Create <SUB> with batch notification set to number and lastNoitification=True -> Send verification notification"""
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1 ],	# update resource
					},
					'ln': True,
					'nu': [ NOTIFICATIONSERVER ],
					'bn': { 
						'num' : numberOfBatchNotifications
					}
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn'))
		self.assertEqual(findXPath(r, 'm2m:sub/bn/num'), numberOfBatchNotifications)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/ln'))
		self.assertEqual(findXPath(r, 'm2m:sub/ln'), True)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTBatchWithLn(self) -> None:
		""" Create n <CNT> -> Send batch notification with only the last outstanding notifications """
		for i in range(0, numberOfBatchNotifications):	# Adding more notification
			dct = 	{ 'm2m:cnt' : {
						'lbl' : [ '%d' % i ]
					}}
			_, rsc = UPDATE(cntURL, TestSUB.originator, dct)
			self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn'))
		self.assertEqual(len(findXPath(lastNotification, 'm2m:agn/m2m:sgn')), 1)	 # ... but expecting only one
		lastNotificationHeaders = getLastNotificationHeaders()
		self.assertIsNotNone(lastNotificationHeaders['X-M2M-EC'])
		self.assertEqual(lastNotificationHeaders['X-M2M-EC'], '4') # 'latest'


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBBatchNotificationNumberWithLn(self) -> None:
		""" Delete <SUB> """
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithEncChty(self) -> None:
		""" Create <SUB> to monitor ceration of child resources with type=container -> Send verification notification"""
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 3 ],	# create direct child resource
						'chty': [ 3 ] 	# only cnt
					},
					'ln': True,
					'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/enc/chty'))
		self.assertEqual(findXPath(r, 'm2m:sub/enc/chty'), [ 3 ])
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINWithEncChty(self) -> None:
		""" Create <CNI> -> Send NO notification"""
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'aValue'
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNone(getLastNotification())	# this shouldn't have caused a notification


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTWithEncChty(self) -> None:
		""" Create <CNT> -> Send notification"""
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}Sub'
				}}
		TestSUB.cnt, rsc = CREATE(cntURL, TestSUB.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)		# this must have caused a notification
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}Sub')
		_, rsc = DELETE(f'{cntURL}/{cntRN}Sub', TestSUB.originator)	# delete the sub-cnt
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBWithEncChty(self) -> None:
		""" Delete <SUB> """
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAESUBwithOriginatorPOA(self) -> None:
		""" Create new <AE> and <SUB>. nu=poa of new originator -> NO verification request"""
		# create a second AE
		dct = 	{ 'm2m:ae' : {
			'rn'  : aeRN+'2', 
			'api' : 'NMyApp1Id',
			'rr'  : False,
			'srv' : [ '3' ],
			'poa' : [ NOTIFICATIONSERVER ]
		}}
		ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.created)
		TestSUB.ae2Originator = findXPath(ae, 'm2m:ae/aei')

		# Create the sub
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN+'POA',
			        'enc': {
			            'net': [ 1, 3 ]
					},
					'nu': [ TestSUB.ae2Originator ],
					'su': NOTIFICATIONSERVER
				}}
		_, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		self.assertIsNone(findXPath(lastNotification, 'm2m:sgn/vrq'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithOriginatorPOA(self) -> None:
		""" Create <CNT> -> Send notification via AE.poa """
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}'
				}}
		TestSUB.cnt, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)		# this must have caused a notification via the poa
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateAECSZwithOriginatorPOA(self) -> None:
		""" Update <AE>'s csz to 'application/cbor' """
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:ae' : { 
					'csz'  : ['application/cbor']
				}}
		r, rsc = UPDATE(TestSUB.ae2URL, TestSUB.ae2Originator, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/csz'))
		self.assertEqual(findXPath(r, 'm2m:ae/csz'), ['application/cbor'])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithOriginatorPOACBOR(self) -> None:
		""" Create <CNT> -> Send notification via <AE>.poa as application/cbor """
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}2'
				}}
		TestSUB.cnt, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		lastHeaders = getLastNotificationHeaders()
		self.assertIsNotNone(lastNotification)		# this must have caused a notification via the poa
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}2')
		self.assertIn('Content-Type', lastHeaders)
		self.assertIn(lastHeaders['Content-Type'], [ 'application/cbor', 'application/vnd.onem2m-res+cbor' ])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEwithOriginatorPOA(self) -> None:
		""" Delete <AE> and <SUB> """
		_, rsc = DELETE(TestSUB.ae2URL, TestSUB.ae2Originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAESUBwithURIctCBOR(self) -> None:
		""" Create new <AE> and <SUB>. nu=uri&ct=cbor -> Send verification request"""
		# create a second AE
		dct = 	{ 'm2m:ae' : {
			'rn'  : aeRN+'2', 
			'api' : 'NMyApp1Id',
			'rr'  : False,
			'srv' : [ '3' ]
		}}
		ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.created)
		TestSUB.ae2URL = f'{cseURL}/{aeRN}2'
		TestSUB.ae2Originator = findXPath(ae, 'm2m:ae/aei')

		# Create the sub
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN+'POA',
			        'enc': {
			            'net': [ 1, 3 ]
					},
					'nu': [ f'{NOTIFICATIONSERVER}?ct=cbor' ],
					'su': NOTIFICATIONSERVER
				}}
		_, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/vrq'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithURIctCBOR(self) -> None:
		""" Create <CNT> -> Send notification via URI as application/cbor """
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}2'
				}}
		TestSUB.cnt, rsc = CREATE(TestSUB.ae2URL, TestSUB.ae2Originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		lastHeaders = getLastNotificationHeaders()
		self.assertIsNotNone(lastNotification)		# this must have caused a notification via the poa
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}2')
		self.assertIn('Content-Type', lastHeaders)
		self.assertIn(lastHeaders['Content-Type'], [ 'application/cbor', 'application/vnd.onem2m-res+cbor' ])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEwithURIctCBOR(self) -> None:
		""" Delete <AE> and subscription """
		_, rsc = DELETE(TestSUB.ae2URL, TestSUB.ae2Originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBwithEXC(self) -> None:
		""" Create new <SUB> with EXC = 2 -> Send verification request"""
		# Create the sub
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN+'EXC',
			        'enc': {
			            'net': [ 1, 3 ]
					},
					'nu': [NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'exc': 2	# Remove after 2 notifications
				}}
		TestSUB.excSub, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/vrq'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTforEXC(self) -> None:
		""" Create 2 <CNT> -> <SUB> with EXC removed """
		# Create a first container
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}3'
				}}
		TestSUB.cnt, rsc = CREATE(aeURL, TestSUB.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/ty'), T.CNT)
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}3')

		# Retrieve subscription
		time.sleep(1) 	# wait a moment
		_, rsc = RETRIEVE(f'{aeURL}/{subRN}EXC', TestSUB.originator)
		self.assertEqual(rsc, RC.OK)

		# Create a second container
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}4'
				}}
		TestSUB.cnt, rsc = CREATE(aeURL, TestSUB.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.created)
		time.sleep(durationForBatchNotifications) 	# wait a moment
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sud'))

		# Retrieve subscription
		time.sleep(1) 	# wait a moment
		_, rsc = RETRIEVE(f'{aeURL}/{subRN}EXC', TestSUB.originator)
		self.assertEqual(rsc, RC.notFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBwithUnknownPoa(self) -> None:
		""" Create new <SUB> with NU to not-existing POA -> Fail """
		# Create the sub
		clearLastNotification()	# clear the notification first
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN+'NOPOA',
			        'enc': {
			            'net': [ 1, 3 ]
					},
					'nu': [ findXPath(TestSUB.aeNoPoa, 'm2m:ae/ri') ]	# this ae has no poa
				}}
		TestSUB.excSub, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.subscriptionVerificationInitiationFailed)
		
	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithCreatorWrong(self) -> None:
		""" Create <SUB> with creator attribute (wrong) -> Fail """
		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
					'cr' : 'wrong',
				}}
		r, rsc = CREATE(aeURL, TestSUB.originator, T.SUB, dct)				# Not allowed
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithCreator(self) -> None:
		""" Create <SUB> with creator attribute set to Null """
		dct = 	{ 'm2m:sub' : { 
					'nu': [NOTIFICATIONSERVER ],
					'cr' : None,
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, dct)	
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:sub/cr'), TestSUB.originator)	# Creator should now be set to originator

		# Check whether creator is there in a RETRIEVE
		r, rsc = RETRIEVE(f'{cntURL}/{findXPath(r, "m2m:sub/rn")}', TestSUB.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:sub/cr'), TestSUB.originator)


# TODO check different NET's (ae->cnt->sub, add cnt to cnt)


def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()

	suite.addTest(TestSUB('test_createSUB'))
	suite.addTest(TestSUB('test_retrieveSUB'))
	suite.addTest(TestSUB('test_retrieveSUBWithWrongOriginator'))
	suite.addTest(TestSUB('test_attributesSUB'))

	suite.addTest(TestSUB('test_createSUBWrong'))
	suite.addTest(TestSUB('test_updateSUB'))
	suite.addTest(TestSUB('test_updateCNT'))
	suite.addTest(TestSUB('test_addCIN2CNT'))
	suite.addTest(TestSUB('test_removeCNT'))
	suite.addTest(TestSUB('test_addCNTAgain'))

	suite.addTest(TestSUB('test_createSUB'))
	suite.addTest(TestSUB('test_deleteSUBByUnknownOriginator'))
	suite.addTest(TestSUB('test_deleteSUBByAssignedOriginator'))

	suite.addTest(TestSUB('test_createSUBModifedAttributesWrong'))
	suite.addTest(TestSUB('test_createSUBModifedAttributes'))
	suite.addTest(TestSUB('test_updateCNTModifiedAttributes'))
	suite.addTest(TestSUB('test_updateCNTSameModifiedAttributes'))
	suite.addTest(TestSUB('test_deleteSUBByAssignedOriginator'))

	suite.addTest(TestSUB('test_createSUBRI'))
	suite.addTest(TestSUB('test_updateCNTRI'))
	suite.addTest(TestSUB('test_deleteSUBByAssignedOriginator'))

	suite.addTest(TestSUB('test_createSUBForBatchNotificationNumber'))
	suite.addTest(TestSUB('test_updateCNTBatch'))
	suite.addTest(TestSUB('test_deleteSUBForBatchReceiveRemainingNotifications'))

	suite.addTest(TestSUB('test_createSUBForBatchNotificationDuration'))
	suite.addTest(TestSUB('test_updateCNTBatchDuration'))
	suite.addTest(TestSUB('test_deleteSUBForBatchNotificationDuration'))

	suite.addTest(TestSUB('test_createSUBWithEncAtr'))	# attribute
	suite.addTest(TestSUB('test_updateCNTWithEncAtrLbl'))
	suite.addTest(TestSUB('test_updateCNTWithEncAtrLblWrong'))
	suite.addTest(TestSUB('test_deleteSUBWithEncAtr'))

	suite.addTest(TestSUB('test_createSUBBatchNotificationNumberWithLn'))	# Batch + latestNotify
	suite.addTest(TestSUB('test_updateCNTBatchWithLn'))
	suite.addTest(TestSUB('test_deleteSUBBatchNotificationNumberWithLn'))

	suite.addTest(TestSUB('test_createSUBWithEncChty'))	# child resource type
	suite.addTest(TestSUB('test_createCINWithEncChty'))
	suite.addTest(TestSUB('test_createCNTWithEncChty'))
	suite.addTest(TestSUB('test_deleteSUBWithEncChty'))

	suite.addTest(TestSUB('test_createAESUBwithOriginatorPOA'))
	suite.addTest(TestSUB('test_createCNTwithOriginatorPOA'))
	suite.addTest(TestSUB('test_updateAECSZwithOriginatorPOA'))
	suite.addTest(TestSUB('test_createCNTwithOriginatorPOACBOR'))
	suite.addTest(TestSUB('test_deleteAEwithOriginatorPOA'))

	suite.addTest(TestSUB('test_createAESUBwithURIctCBOR'))
	suite.addTest(TestSUB('test_createCNTwithURIctCBOR'))
	suite.addTest(TestSUB('test_deleteAEwithURIctCBOR'))

	suite.addTest(TestSUB('test_createSUBwithEXC'))
	suite.addTest(TestSUB('test_createCNTforEXC'))

	suite.addTest(TestSUB('test_createSUBwithUnknownPoa'))
	suite.addTest(TestSUB('test_createSUBWithCreatorWrong'))
	suite.addTest(TestSUB('test_createSUBWithCreator'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
