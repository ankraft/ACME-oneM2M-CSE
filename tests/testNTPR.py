#
#	testNTPR.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for notificationTargetMgmtPolicyRef resources
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, NotificationEventType as NET
from init import *
		

class TestNTPR(unittest.TestCase):

	ae = None
	aeRI = None
	sub = None
	subRI = None
	originator = None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup Test NotificationTargetMgmtPolicyRef')

		# Start notification server
		startNotificationServer()

		dct:JSON = { 'm2m:ae' : {
						'rn'  : aeRN, 
						'api' : APPID,
				 		'rr'  : True,
				 		'srv' : [ RELEASEVERSION ]
					}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'

		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		cls.aeRI = findXPath(cls.ae, 'm2m:ae/ri')

		# First create a SUB
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate ]
					},
					'nu': [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER,
					'nse': True
				}}
		cls.sub, rsc = CREATE(aeURL, cls.originator, T.SUB, dct)
		assert rsc == RC.CREATED, 'cannot create subscription'
		cls.subRI = findXPath(cls.sub, 'm2m:sub/ri')

		testCaseEnd('Setup Test NotificationTargetMgmtPolicyRef')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		testCaseStart('TearDown Test NotificationTargetMgmtPolicyRef')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown Test NotificationTargetMgmtPolicyRef')
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
	def test_createNTPR(self) -> None:
		"""	CREATE <NTPR> """
		dct:JSON = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ NOTIFICATIONSERVER ]
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveNTPR(self) -> None:
		"""	RETRIEVE <NTPR>"""

		r, rsc = RETRIEVE(f'{aeURL}/{subRN}/{ntprRN}', self.originator)
		self.assertEqual(rsc, RC.OK, r)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateNTPR(self) -> None:
		"""	UPDATE <NTPR>"""
		dct:JSON = { 'm2m:ntpr': {
			'lbl' : [ 'test' ],
		}}
		r, rsc = UPDATE(f'{aeURL}/{subRN}/{ntprRN}', self.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(lbl := findXPath(r, 'm2m:ntpr/lbl'), r)
		self.assertEqual(lbl, [ 'test' ], r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteNTPR(self) -> None:
		"""	DELETE <NTPR>"""

		r, rsc = DELETE(f'{aeURL}/{subRN}/{ntprRN}', self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


#
#	Advanced tests
#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNTPRDuplicateNotificationTargetURIFail(self) -> None:
		"""	CREATE 2 <NTPR> with duplicate notificationTargetURI -> Fail"""

		# Create a first NTPR
		dct:JSON = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ NOTIFICATIONSERVER ]
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create a second NTPR with the same notificationTargetURI
		# This should fail with CONFLICT
		dct = { 'm2m:ntpr': {
			'rn'  : f'{ntprRN}2',
			'ntu' : [ NOTIFICATIONSERVER ]
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CONFLICT, r)

		# Clean up
		r, rsc = DELETE(f'{aeURL}/{subRN}/{ntprRN}', self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateNTPRDuplicateNotificationTargetURIFail(self) -> None:
		"""	UPDATE 2 <NTPR> with duplicate notificationTargetURI -> Fail"""

		# Create a first NTPR
		dct:JSON = { 'm2m:ntpr': {
			'rn'  : ntprRN,
			'ntu' : [ NOTIFICATIONSERVER ]
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Create a second NTPR with the same notificationTargetURI
		dct = { 'm2m:ntpr': {
			'rn'  : f'{ntprRN}2',
			'ntu' : [ self.originator ]
		}}
		r, rsc = CREATE(f'{aeURL}/{subRN}', self.originator, T.NTPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Update the second NTPR with the same notificationTargetURI
		dct = { 'm2m:ntpr': {
			'ntu' : [ NOTIFICATIONSERVER ]
		}}
		r, rsc = UPDATE(f'{aeURL}/{subRN}/{ntprRN}2', self.originator, dct)
		self.assertEqual(rsc, RC.CONFLICT, r)

		# Clean up
		r, rsc = DELETE(f'{aeURL}/{subRN}/{ntprRN}', self.originator)
		self.assertEqual(rsc, RC.DELETED, r)

		r, rsc = DELETE(f'{aeURL}/{subRN}/{ntprRN}2', self.originator)
		self.assertEqual(rsc, RC.DELETED, r)

	#########################################################################


def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestNTPR, [

		# basic tests
		'test_createNTPR',
		'test_retrieveNTPR',
		'test_updateNTPR',
		'test_deleteNTPR',

		# advanced tests

		'test_createNTPRDuplicateNotificationTargetURIFail',
		'test_updateNTPRDuplicateNotificationTargetURIFail',

	])

	# Run the tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)