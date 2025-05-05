#
#	testNTSR.py
#
#	(c) 20205 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for notificationTargetSelfReference resources and handling
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import NotificationEventType as NET, ResourceTypes as T, NotificationContentType, ResponseStatusCode as RC, Permission
from init import *

class TestNTSR(unittest.TestCase):

	ae = None
	ae2 = None
	originator = None
	originator2 = None
	aeURL2 = None
	acp = None
	acpRI = None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		# Start notification server
		startNotificationServer()

		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'

		testCaseStart('Setup NotificationTargetSelfReference')
		# create resources
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ],
					'poa' : [ NOTIFICATIONSERVER ],
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		# Second AE
		dct = 	{ 'm2m:ae' : {
					'rn'  : f'{aeRN}2', 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ],
					'poa' : [ NOTIFICATIONSERVER ],
				}}
		cls.ae2, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator2 = findXPath(cls.ae2, 'm2m:ae/aei')
		cls.aeURL2 = f'{cseURL}/{aeRN}2'

		# Give the second AE access to the first AE
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ { 	"acor": [ cls.originator, cls.originator2 ],
									"acop": Permission.ALL
								} ]
					},
					"pvs": { 
						"acr": [ {
							"acor": [ cls.originator ],
							"acop": Permission.ALL
						} ]
					},
				}}
		cls.acp, rsc = CREATE(aeURL, cls.originator, T.ACP, dct)
		assert rsc == RC.CREATED, 'cannot create parent ACP'
		cls.acpRI = findXPath(cls.acp, 'm2m:acp/ri')

		testCaseEnd('Setup Test NotificationTargetSelfReference')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			stopNotificationServer()
			return
		testCaseStart('TearDown NotificationTargetSelfReference')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(cls.aeURL2, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(ntpURL, ORIGINATOR)	
		testCaseEnd('TearDown NotificationTargetSelfReference')
		stopNotificationServer()


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################
	
	#
	#	Basic tests
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveNTSRFail(self) -> None:
		"""	Retrieve <ntsr> -> Fail """
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ NOTIFICATIONSERVER ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# retrieve NTSR
		r, rsc = RETRIEVE(f'{aeURL}/{subRN}/ntsr' , TestNTSR.originator)
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED, r)

		# delete resource
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNTSRFail(self) -> None:
		"""	CREATE <ntsr> -> Fail """
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ NOTIFICATIONSERVER ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send an UPDATE
		dct = 	{ 'm2m:ntsr': {
					'rn': 'test',
				}}
		r, rsc = CREATE(f'{aeURL}/{subRN}' , TestNTSR.originator, T.NTSR, dct)
		self.assertNotEqual(rsc, RC.CREATED, r)

		# delete resource
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateNTSRFail(self) -> None:
		"""	UPDATE <ntsr> -> Fail """
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ NOTIFICATIONSERVER ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send an UPDATE
		dct = 	{ 'm2m:ntsr': {
					'lbl': [ 'test' ],
				}}
		r, rsc = UPDATE(f'{aeURL}/{subRN}/ntsr' , TestNTSR.originator, dct)
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED, r)

		# delete resource
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	Unsubscribe tests
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeUsingSystemDefault(self) -> None:
		"""	Unsubscribe using system default NTP (action=reject)"""
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# No further references and policies
		# Assume that the system NTP is created with action=reject

		# Send a DELETE
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr' , TestNTSR.originator)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# delete resource
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)


	# @unittest.skipIf(noCSE, 'No CSEBase')
	# def test_unsubscribeUsingSystemDefault(self) -> None:
	# 	"""	Unsubscribe using system default NTP """
	# 	dct:JSON = 	{ 'm2m:sub' : { 
	# 				'rn' : subRN,
	# 				'nu': [ self.originator2 ],
	# 				'acpi': [ TestNTSR.acpRI ],
	# 			}}
	# 	r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
	# 	self.assertEqual(rsc, RC.CREATED, r)

	# 	# No further references and policies

	# 	# Send a DELETE by originator2
	# 	r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr' , TestNTSR.originator2)
	# 	self.assertEqual(rsc, RC.DELETED, r)

	# 	# check subscription
	# 	r, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
	# 	self.assertEqual(rsc, RC.OK, r)
	# 	self.assertIsNotNone(findXPath(r, 'm2m:sub/nu'), r)
	# 	self.assertEqual(len(findXPath(r, 'm2m:sub/nu')), 0, r)

	# 	# delete resource
	# 	r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
	# 	self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeUsingCreatorDefaultAccept(self) -> None:
		"""	Unsubscribe using creator default NTP (accept) """

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# This time use accept
			'plbl': 'Default',
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.DELETED, r)

		# check subscription
		r, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/nu'), r)
		self.assertEqual(len(findXPath(r, 'm2m:sub/nu')), 0, r)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeUsingCreatorDefaultReject(self) -> None:
		"""	Unsubscribe using creator default NTP (reject) """

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 2,				# This time use reject
			'plbl': 'Default',
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# check subscription
		r, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:sub/nu'), r)
		self.assertEqual(len(findXPath(r, 'm2m:sub/nu')), 1, r)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeUsingCreatorDefaultSeekAuthorizationAccept(self) -> None:
		"""	Unsubscribe using creator default NTP (seek authorization & accept) """

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 3,				# This time use inform & reject
			'plbl': 'Default',
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Clear the last notification. Notification will positively respond to next notification
		clearLastNotification()

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.DELETED, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 0, sub)
		subRI = findXPath(sub, 'm2m:sub/ri')

		# check notification
		testSleep(notificationDelay)
		notification = getLastNotification()
		self.assertIsNotNone(notification, 'No notification received')
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), f'{CSEID}/{subRI}', notification)
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn/tra'), notification)
		self.assertTrue(findXPath(notification, 'm2m:sgn/tra'), notification)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeUsingCreatorDefaultSeekAuthorizationReject(self) -> None:
		"""	Unsubscribe using creator default NTP (seek authorization & reject) """

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 3,				# This time use inform & reject
			'plbl': 'Default',
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Clear the last notification. Notification will positively respond to next notification
		clearLastNotification(nextResult=RC.ORIGINATOR_HAS_NO_PRIVILEGE)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 1, sub)
		subRI = findXPath(sub, 'm2m:sub/ri')

		# check notification
		testSleep(notificationDelay)
		notification = getLastNotification()
		self.assertIsNotNone(notification, 'No notification received')
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), f'{CSEID}/{subRI}', notification)
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn/tra'), notification)
		self.assertTrue(findXPath(notification, 'm2m:sgn/tra'), notification)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeUsingCreatorDefaultInformReject(self) -> None:
		"""	Unsubscribe using creator default NTP (inform & reject) """

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 4,				# This time use inform & reject
			'plbl': 'Default',
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Clear the last notification 
		clearLastNotification()

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 1, sub)
		subRI = findXPath(sub, 'm2m:sub/ri')

		# check notification
		testSleep(notificationDelay)
		notification = getLastNotification()
		self.assertIsNotNone(notification, 'No notification received')
		self.assertEqual(findXPath(notification, 'm2m:sgn/sur'), f'{CSEID}/{subRI}', notification)
		self.assertIsNotNone(findXPath(notification, 'm2m:sgn/trr'), notification)
		self.assertTrue(findXPath(notification, 'm2m:sgn/trr'), notification)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeUsingNTPRMatching(self) -> None:
		"""	Unsubscribe using NTPR (accept) """

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.DELETED, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 0, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)
		

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeUsingNTPRNoNPI(self) -> None:
		"""	Unsubscribe using NTPR (accept), no NPI, fallback to system default """

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		# This should fallback to the system default NTP (which should be reject)
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 1, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeUsingNTPRNotMatchingNTU(self) -> None:
		"""	Unsubscribe using NTPR (accept), no matching NTU, fallback to system default """

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ 'Cother' ],	# Some other originator
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 1, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWrongNTPReference(self) -> None:
		"""	Unsubscribe referencing a non-existing NTP, fallback to system default """

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Don't create a NTP, but use a non-existing one

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ 'Cother' ],		# Some other originator
			'npi' : 'nonExistingNTP'	# Non-existing NTP reference
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 1, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWithPDRNoRules(self) -> None:
		"""	Unsubscribe using NTP (accept), Policy with no rules"""

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create a single policy resource with a schedule under the NTP
		dct = { 'm2m:pdr': {
			'rn' : pdrRN,
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.DELETED, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 0, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWithPDREmptyRules(self) -> None:
		"""	Unsubscribe using NTP (accept), Policy with Empty rules"""

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create a single policy resource with a schedule under the NTP
		dct = { 'm2m:pdr': {
			'rn' : pdrRN,
			'dr' : {
				'tod' : [], # empty
			}
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.DELETED, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 0, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWithPDRScheduleSimple(self) -> None:
		"""	Unsubscribe using NTP (accept), Policy with single schedule """

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create a single policy resource with a schedule under the NTP
		dct = { 'm2m:pdr': {
			'rn' : pdrRN,
			'dr' : {
				'tod' : [ '* * * * * * *' ], # always match
			}
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.DELETED, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 0, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWithPDRScheduleSimpleWrongTime(self) -> None:
		"""	Unsubscribe using NTP (accept), Policy with single schedule, wrong time"""

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create a single policy resource with a schedule under the NTP
		dct = { 'm2m:pdr': {
			'rn' : pdrRN,
			'dr' : {
				'tod' : [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2) ], # don't match
			}
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 1, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWithPDRScheduleORSingle(self) -> None:
		"""	Unsubscribe using NTP (accept), 1 OR Policy with two schedules"""

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create a single policy resource with 2 schedules under the NTP
		# One schedule matches, the other does not
		dct = { 'm2m:pdr': {
			'rn' : pdrRN,
			'dr' : {
				'tod' : [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2), '* * * * * * *' ], 
			},
			'drr': 2	# OR
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.DELETED, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 0, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWithPDRScheduleANDSingle(self) -> None:
		"""	Unsubscribe using NTP (accept), 1 AND Policy with two schedules"""

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create a single policy resource with 2 schedules under the NTP
		# One schedule matches, the other does not
		dct = { 'm2m:pdr': {
			'rn' : pdrRN,
			'dr' : {
				'tod' : [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2), '* * * * * * *' ], 
			},
			'drr': 1	# AND
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 1, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWithPDRScheduleORDoubleANDAccept(self) -> None:
		"""	Unsubscribe using NTP (accept), 2 AND Policy with two OR schedules each"""

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'rrs': 1,				# AND
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create two policy resource with 2 schedules under the NTP
		# Both policies yield true, One schedule matches, the other does not
		dct = { 'm2m:pdr': {
			'rn' : pdrRN,
			'dr' : {
				'tod' : [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2), '* * * * * * *' ], 
			},
			'drr': 2	# OR
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct = { 'm2m:pdr': {
			'rn' : f'{pdrRN}2',
			'dr' : {
				'tod' : [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2), '* * * * * * *' ], 
			},
			'drr': 2	# OR
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.DELETED, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 0, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWithPDRScheduleORDoubleANDReject(self) -> None:
		"""	Unsubscribe using NTP (reject), 2 AND Policy with two OR schedules each"""

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'rrs': 1,				# AND
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create two policy resource with 2 schedules under the NTP
		# Only the first policy yields true
		dct = { 'm2m:pdr': {
			'rn' : pdrRN,
			'dr' : {
				'tod' : [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2), createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2) ], 	# not matching
			},
			'drr': 2	# OR
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct = { 'm2m:pdr': {
			'rn' : f'{pdrRN}2',
			'dr' : {
				'tod' : [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2), '* * * * * * *' ], # True
			},
			'drr': 2	# OR
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 1, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWithPDRScheduleANDDoubleORAccept(self) -> None:
		"""	Unsubscribe using NTP (accept), 2 OR Policy with two AND schedules each"""

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'rrs': 2,				# OR
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create two policy resource with 2 schedules (AND) under the NTP
		# Only one policiy yields true
		dct = { 'm2m:pdr': {
			'rn' : pdrRN,
			'dr' : {
				'tod' : [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2), '* * * * * * *' ], # False
			},
			'drr': 1	# AND
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct = { 'm2m:pdr': {
			'rn' : f'{pdrRN}2',
			'dr' : {
				'tod' : [ '* * * * * * *', '* * * * * * *' ], 	# True
			},
			'drr': 1	# AND
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.DELETED, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 0, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_unsubscribeWithPDRScheduleANDDoubleORReject(self) -> None:
		"""	Unsubscribe using NTP (reject), 2 OR Policy with two AND schedules each"""

		# create a subscription
		dct:JSON = { 'm2m:sub' : { 
					'rn' : subRN,
					'nu': [ self.originator2 ],
					'acpi': [ TestNTSR.acpRI ],
				}}
		r, rsc = CREATE(aeURL, TestNTSR.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create creator default NTP
		dct = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}',
			'acn' : 1,				# accept
			'plbl': 'NoDefault',	# Not a default label
			'rrs': 2,				# OR
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		ntpRI = findXPath(r, 'm2m:ntp/ri')

		# Create notificationTargetMgmtPolicyRef resource
		dct = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ self.originator2 ],	# originator2
			'npi' : ntpRI
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create two policy resource with 2 schedules (AND) under the NTP
		# Both policies yield false
		dct = { 'm2m:pdr': {
			'rn' : pdrRN,
			'dr' : {
				'tod' : [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2), '* * * * * * *' ], # False
			},
			'drr': 1	# AND
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct = { 'm2m:pdr': {
			'rn' : f'{pdrRN}2',
			'dr' : {
				'tod' : [ createScheduleString(requestCheckDelay * 2, requestCheckDelay * 2), '* * * * * * *' ], # False
			},
			'drr': 1	# AND
		}}
		r, rsc = CREATE(ntpURL, self.originator, T.PDR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Send a DELETE  by originator2
		r, rsc = DELETE(f'{aeURL}/{subRN}/ntsr', TestNTSR.originator2)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)

		# check subscription
		sub, rsc = RETRIEVE(f'{aeURL}/{subRN}', TestNTSR.originator2)
		self.assertEqual(rsc, RC.OK, sub)
		self.assertIsNotNone(findXPath(sub, 'm2m:sub/nu'), sub)
		self.assertEqual(len(findXPath(sub, 'm2m:sub/nu')), 1, sub)

		# delete resources
		r, rsc = DELETE(f'{aeURL}/{subRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED)
		r, rsc = DELETE(f'{cseURL}/{ntpRN}', TestNTSR.originator)
		self.assertEqual(rsc, RC.DELETED, r)

## TODO No referenced NTP found

def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestNTSR, [

		# Basic tests
		'test_retrieveNTSRFail',
		'test_createNTSRFail',
		'test_updateNTSRFail',

		# Unsubscrribe tests
		'test_unsubscribeUsingSystemDefault',

		'test_unsubscribeUsingCreatorDefaultAccept',
		'test_unsubscribeUsingCreatorDefaultReject',
		'test_unsubscribeUsingCreatorDefaultSeekAuthorizationAccept',
		'test_unsubscribeUsingCreatorDefaultSeekAuthorizationReject',
		'test_unsubscribeUsingCreatorDefaultInformReject',

		'test_unsubscribeUsingNTPRMatching',
		'test_unsubscribeUsingNTPRNoNPI',
		'test_unsubscribeUsingNTPRNotMatchingNTU',
		
		'test_unsubscribeWrongNTPReference',

		'test_unsubscribeWithPDRNoRules',
		'test_unsubscribeWithPDREmptyRules',
		'test_unsubscribeWithPDRScheduleSimple',
		'test_unsubscribeWithPDRScheduleSimpleWrongTime',
		'test_unsubscribeWithPDRScheduleORSingle',
		'test_unsubscribeWithPDRScheduleANDSingle',
		'test_unsubscribeWithPDRScheduleORDoubleANDAccept',
		'test_unsubscribeWithPDRScheduleORDoubleANDReject',
		'test_unsubscribeWithPDRScheduleANDDoubleORAccept',
		'test_unsubscribeWithPDRScheduleANDDoubleORReject',

	])

	# Run tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
