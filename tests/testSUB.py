#
#	testSUB.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for SUB functionality & notifications
#

import unittest, sys
import requests
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T, NotificationContentType, ResponseCode as RC
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

numberOfBatchNotifications = 5
durationForBatchNotifications = 2
durationForBatchNotificationsISO8601 = 'PT2S'

class TestSUB(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		# Start notification server
		startNotificationServer()

		# look for notification server
		hasNotificationServer = False
		try:
			r = requests.post(NOTIFICATIONSERVER, data='{"test": "test"}', verify=verifyCertificate)
			hasNotificationServer = True
		except Exception as e:
			pass
		finally:	
			assert hasNotificationServer, 'Notification server cannot be reached'

		# create other resources
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase: {cseURL}'

		jsn = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, jsn)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, jsn)
		assert rsc == RC.created, 'cannot create container'
		cls.cntRI = findXPath(cls.cnt, 'm2m:cnt/ri')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()

	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUB(self):
		self.assertIsNotNone(TestSUB.cse)
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		jsn = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1, 3 ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, jsn)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveSUB(self):
		_, rsc = RETRIEVE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveSUBWithWrongOriginator(self):
		_, rsc = RETRIEVE(subURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesSUB(self):
		r, rsc = RETRIEVE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:sub/ty'), T.SUB)
		self.assertEqual(findXPath(r, 'm2m:sub/pi'), findXPath(TestSUB.cnt,'m2m:cnt/ri'))
		self.assertEqual(findXPath(r, 'm2m:sub/rn'), subRN)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:sub/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:sub/et'))
		self.assertEqual(findXPath(r, 'm2m:sub/cr'), TestSUB.originator)
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
	def test_createSUBWrong(self):
		jsn = 	{ 'm2m:sub' : { 
					'rn' : f'{subRN}Wrong',
			        'enc': {
			            'net': [ 1, 2, 3, 4 ]
        			},
        			'nu': [ NOTIFICATIONSERVERW ]
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, jsn)
		self.assertNotEqual(rsc, RC.created)
		self.assertEqual(rsc, RC.subscriptionVerificationInitiationFailed)
		

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSUB(self):
		jsn = 	{ 'm2m:sub' : { 
					'exc': 5
				}}
		r, rsc = UPDATE(subURL, TestSUB.originator, jsn)
		self.assertEqual(rsc, RC.updated)
		self.assertIsInstance(findXPath(r, 'm2m:sub/exc'), int)
		self.assertEqual(findXPath(r, 'm2m:sub/exc'), 5)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNT(self):
		jsn = 	{ 'm2m:cnt' : {
					'lbl' : [ 'aTag' ],
					'mni' : 10,
					'mbs' : 9999
 				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
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
	def test_addCIN2CNT(self):
		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'aValue'
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.CIN, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/ri'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cin/con'), 'aValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_removeCNT(self):
		r, rsc = DELETE(cntURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		self.assertEqual(rsc, RC.deleted)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sud'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCNTAgain(self):
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		TestSUB.cnt, rsc = CREATE(aeURL, TestSUB.originator, T.CNT, jsn)
		assert rsc == RC.created, 'cannot create container'
		TestSUB.cntRI = findXPath(TestSUB.cnt, 'm2m:cnt/ri')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBByUnknownOriginator(self):
		_, rsc = DELETE(subURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBByAssignedOriginator(self):
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBModifedAttributes(self):
		jsn = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1, 3 ]
        			},
        			'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nct': NotificationContentType.modifiedAttributes
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:sub/nct'), NotificationContentType.modifiedAttributes)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBModifedAttributes(self):
		jsn = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1, 3 ]
        			},
        			'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nct': NotificationContentType.modifiedAttributes
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:sub/nct'), NotificationContentType.modifiedAttributes)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTModifiedAttributes(self):
		jsn = 	{ 'm2m:cnt' : {
					'lbl' : [ 'bTag' ]
 				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
		self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/lbl'), [ 'bTag'])
		self.assertIsNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/ty'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTSameModifiedAttributes(self):
		jsn = 	{ 'm2m:cnt' : {
					'lbl' : [ 'bTag' ]
 				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
		self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/lbl'), [ 'bTag'])
		self.assertIsNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/ty'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBRI(self):
		jsn = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1, 3 ]
        			},
        			'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nct': NotificationContentType.ri
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertEqual(findXPath(r, 'm2m:sub/nct'), NotificationContentType.ri)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTRI(self):
		jsn = 	{ 'm2m:cnt' : {
					'lbl' : [ 'aTag' ]
 				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
		self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:uri'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:uri').endswith(findXPath(cnt, 'm2m:cnt/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBForBatchNotificationNumber(self):
		self.assertIsNotNone(TestSUB.cse)
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		jsn = 	{ 'm2m:sub' : { 
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
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn'))
		self.assertEqual(findXPath(r, 'm2m:sub/bn/num'), numberOfBatchNotifications)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn/dur'))
		self.assertGreater(findXPath(r, 'm2m:sub/bn/dur'), 0)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTBatch(self):
		for i in range(0, numberOfBatchNotifications):
			jsn = 	{ 'm2m:cnt' : {
						'lbl' : [ '%d' % i ]
					}}
			cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
			self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn'))
		notifications = findXPath(lastNotification, 'm2m:agn')
		for i in range(0, numberOfBatchNotifications):	# check availability and correct order
			self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{%d}/nev/rep/m2m:cnt/lbl' % i))
			self.assertEqual(findXPath(lastNotification, 'm2m:agn/m2m:sgn/{%d}/nev/rep/m2m:cnt/lbl/{0}' % i), '%d' % i)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBForBatchReceiveRemainingNotifications(self):
		# Generate one last notification
		jsn = 	{ 'm2m:cnt' : {
					'lbl' : [ '99' ]
				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
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
	def test_createSUBForBatchNotificationDuration(self):
		self.assertIsNotNone(TestSUB.cse)
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		jsn = 	{ 'm2m:sub' : { 
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
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn'))
		self.assertIsNone(findXPath(r, 'm2m:sub/bn/num'))
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn/dur'))
		self.assertEqual(findXPath(r, 'm2m:sub/bn/dur'), durationForBatchNotificationsISO8601)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTBatchDuration(self):
		for i in range(0, numberOfBatchNotifications):
			jsn = 	{ 'm2m:cnt' : {
						'lbl' : [ '%d' % i ]
					}}
			cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
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
	def test_deleteSUBForBatchNotificationDuration(self):
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithEncAtr(self):
		self.assertIsNotNone(TestSUB.cse)
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		jsn = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 1 ],
			            'atr': ['lbl' ]
					},
					'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/enc/atr'))
		self.assertEqual(findXPath(r, 'm2m:sub/enc/atr'), [ 'lbl' ])
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWithEncAtrLbl(self):
		clearLastNotification()
		jsn = 	{ 'm2m:cnt' : {
					'lbl' : [ 'hello' ]
				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
		self.assertEqual(rsc, RC.updated)

		lastNotification = getLastNotification()	# Notifications should not have arrived yes
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/lbl'), [ 'hello'])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTWithEncAtrLblWrong(self):
		clearLastNotification() # clear notification first, we don't want to receive a notification
		jsn = 	{ 'm2m:cnt' : {
					'mni' : 99
				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
		self.assertEqual(rsc, RC.updated)

		lastNotification = getLastNotification()	# Notifications should not have arrived yes
		self.assertIsNone(lastNotification)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBWithEncAtr(self):
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBBatchNotificationNumberWithLn(self):
		self.assertIsNotNone(TestSUB.cse)
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		jsn = 	{ 'm2m:sub' : { 
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
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/bn'))
		self.assertEqual(findXPath(r, 'm2m:sub/bn/num'), numberOfBatchNotifications)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/ln'))
		self.assertEqual(findXPath(r, 'm2m:sub/ln'), True)
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTBatchWithLn(self):
		for i in range(0, numberOfBatchNotifications):	# Adding more notification
			jsn = 	{ 'm2m:cnt' : {
						'lbl' : [ '%d' % i ]
					}}
			cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
			self.assertEqual(rsc, RC.updated)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:agn/m2m:sgn'))
		self.assertEqual(len(findXPath(lastNotification, 'm2m:agn/m2m:sgn')), 1)	 # ... but expecting only one
		lastNotificationHeaders = getLastNotificationHeaders()
		self.assertIsNotNone(lastNotificationHeaders['X-M2M-EC'])
		self.assertEqual(lastNotificationHeaders['X-M2M-EC'], '4') # 'latest'


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBBatchNotificationNumberWithLn(self):
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUBWithEncChty(self):
		self.assertIsNotNone(TestSUB.cse)
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		jsn = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ 3 ],	# create direct child resource
						'chty': [ 3 ] 	# only cnt
					},
					'ln': True,
					'nu': [ NOTIFICATIONSERVER ]
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, T.SUB, jsn)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/enc/chty'))
		self.assertEqual(findXPath(r, 'm2m:sub/enc/chty'), [ 3 ])
		lastNotification = getLastNotification()
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/vrq'))
		self.assertTrue(findXPath(lastNotification, 'm2m:sgn/sur').endswith(findXPath(r, 'm2m:sub/ri')))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINWithEncChty(self):
		clearLastNotification()	# clear the notification first
		for i in range(0, numberOfBatchNotifications):	# Adding more notification
			jsn = 	{ 'm2m:cnt' : {
						'lbl' : [ '%d' % i ]
					}}
			cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
			self.assertEqual(rsc, RC.updated)
		self.assertIsNone(getLastNotification())	# this shouldn't have caused a notification


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTWithEncChty(self):
		clearLastNotification()	# clear the notification first
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}Sub'
				}}
		TestSUB.cnt, rsc = CREATE(cntURL, TestSUB.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.created)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)		# this must have caused a notification
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'))
		self.assertEqual(findXPath(lastNotification, 'm2m:sgn/nev/rep/m2m:cnt/rn'), f'{cntRN}Sub')
		_, rsc = DELETE(f'{cntURL}/{cntRN}Sub', TestSUB.originator)	# delete the sub-cnt
		self.assertEqual(rsc, RC.deleted)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSUBWithEncChty(self):
		# Delete the sub
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, RC.deleted)

# TODO expirationCounter
# TODO check different NET's (ae->cnt->sub, add cnt to cnt)

def run():
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


	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)

