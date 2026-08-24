#
#testTGR.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for TriggerRequest (TGR) resource type.
#

from socket import timeout
import unittest, sys

if '..' not in sys.path:
	sys.path.append('..')
from acmecse.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, TriggerPurpose, TriggerStatus, Operation
from acmecse.etc.Constants import Constants as C
from init import *

#
#	NOTE
#
#	The tests in this file are only meant to work together with the default TriggerRequest handler plugin. 
#	If another TriggerRequest handler plugin is used, the tests may fail because the behaviour for the different states
#	of the TriggerRequest resource depend on the naming scheme of the M2M-EXT-ID of the AE and TriggerRequest resources. 
#


triggerSleepTime = 3 # seconds to wait for the trigger to be processed

newUpdateBehavior = False	
""" If True, the new update behavior is used, where the trigger request can only be updated/replaced 
	if it is still in the PROCESSING state. The trigger request is processed immediately after the update."""

class TestTGR(unittest.TestCase):

	ae = None
	originator = None

	
	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestTGR')
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ],
					'mei' : f'23@{C.exampleDomain}',
					'tri' : 23,
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, f'cannot create parent AE: {cls.ae}'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		testCaseEnd('Setup TestTGR')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestTGR')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestTGR')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)



	#########################################################################
	#
	#	Basic tests

# TODO: test missing tvt
# TODO test missing any of tri, tia, tio, tirt
# TODO test unknown mei domain
# TODO differet UPDATE test for inverse update behavior

	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_createTGRnoTargetFail(self) -> None:
		"""	CREATE <TGR> but no target resource with the target tri exists -> Fail"""
		dct = 	{ 'm2m:tgr' : { 
					'rn' : tgrRN,
					'mei' : f'23@{C.exampleDomain}',
					'tri' : 42,
					'tvt' : 'PT30S',
				}}
		r, rsc = CREATE(aeURL, self.originator, T.TGR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_createTGR(self) -> None:
		"""	CREATE <TGR> """
		dct = 	{ 'm2m:tgr' : { 
					'rn' : tgrRN,
					'mei' : f'23@{C.exampleDomain}',
					'tri' : 23,
					'tvt' : 'PT30S',
				}}
		r, rsc = CREATE(aeURL, self.originator, T.TGR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:tgr/tst'), TriggerStatus.PROCESSING.value, r)

		# DELETE the TGR to clean up
		r, rsc = DELETE(f'{aeURL}/{tgrRN}', self.originator)
		self.assertEqual(rsc, RC.DELETED, r)



	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_createTGRforCRUD(self) -> None:
		"""	CREATE <TGR> for triggerPurpose "executeCRUD" """
		dct = 	{ 'm2m:tgr' : { 
					'rn' : tgrRN,
					'mei' : f'23@{C.exampleDomain}',
					'tri' : 23,
					'tvt' : 'PT30S',	# This might be corrected by the CSE
					'tpe' : TriggerPurpose.executeCRUD,
					'tiae' : 'AE1',
					'tia' : self.originator,
					'tio' : int(Operation.CREATE),
					'tirt' : T.AE,
				}}
		r, rsc = CREATE(aeURL, self.originator, T.TGR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DELETE the TGR to clean up
		r, rsc = DELETE(f'{aeURL}/{tgrRN}', self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_createTGRWithUnknownDomainFail(self) -> None:
		"""	CREATE <TGR> with unknown domain -> Fail"""

		# Update the AE to have a known M2M-EXT-ID for the default TriggerRequest handler
		dct:JSON = 	{ 'm2m:ae' : {
					'mei' : '42@unknown.domain',
				}}
		r, rsc = UPDATE(aeURL, self.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Create a TriggerRequest that will be processed by the default TriggerRequest handler and will result in a TRIGGER_DELIVERED status
		dct = 	{ 'm2m:tgr' : { 
					'rn' : tgrRN,
					'mei' : f'42@unknown.domain',
					'tri' : 23,
					'tvt' : 'PT30S',	# This might be corrected by the CSE
					'tpe' : TriggerPurpose.establishConnection,
					'tiae' : 'AE1',
					'tia' : self.originator,
					'tio' : int(Operation.CREATE),
					'tirt' : T.AE,
				}}
		r, rsc = CREATE(aeURL, self.originator, T.TGR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:tgr/tst'), TriggerStatus.ERROR_NSE_NOT_FOUND.value, r)

		# DELETE the TGR to clean up
		r, rsc = DELETE(f'{aeURL}/{tgrRN}', self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	#	CREATE tests
	#

	def _runTriggerTypeCreateTest(self, triggerType: TriggerStatus, 
							   	  timeout: int = 30,
								  updatePrepare: bool = False) -> None:
		"""	Run a CREATE test for a specific triggerType. This is a helper function to avoid code duplication. 

			Args:
				triggerType: The triggerType to test. This is used to set the M2M-EXT-ID of the AE and TriggerRequest resources.
				timeout: Timeout of the trigger request in seconds.
				updatePrepare: Whether to update the TriggerRequest resource after creation. Set to False if you want to check the status immediately.
		"""

		# Update the AE to have a known M2M-EXT-ID for the default TriggerRequest handler
		dct:JSON = 	{ 'm2m:ae' : {
					'mei' : f'{triggerType.name}@{C.exampleDomain}',
				}}
		r, rsc = UPDATE(aeURL, self.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Create a TriggerRequest that will be processed by the default TriggerRequest handler and will result in a TRIGGER_DELIVERED status
		dct = 	{ 'm2m:tgr' : { 
					'rn' : tgrRN,
					'mei' : f'{triggerType.name}@{C.exampleDomain}',
					'tri' : 23,
					'tvt' : f'PT{timeout}S',	# This might be corrected by the CSE
					'tpe' : TriggerPurpose.establishConnection,
				}}
		r, rsc = CREATE(aeURL, self.originator, T.TGR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Wait for the trigger to be processed
		if not updatePrepare:
			testSleep(triggerSleepTime)  # Wait for the trigger to be processed

			# Check the status of the TriggerRequest
			r, rsc = RETRIEVE(f'{aeURL}/{tgrRN}', self.originator)
			self.assertEqual(rsc, RC.OK, r)
			self.assertEqual(findXPath(r, 'm2m:tgr/tst'), triggerType.value, r)

			# DELETE the TGR to clean up
			r, rsc = DELETE(f'{aeURL}/{tgrRN}', self.originator)
			self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_createTGRWithTriggerDelivered(self) -> None:
		"""	CREATE <TGR> with expected trigger result: TRIGGER_DELIVERED"""
		self._runTriggerTypeCreateTest(TriggerStatus.TRIGGER_DELIVERED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_createTGRWithTriggerFailed(self) -> None:
		"""	CREATE <TGR> with expected trigger result: TRIGGER_FAILED"""
		self._runTriggerTypeCreateTest(TriggerStatus.TRIGGER_FAILED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_createTGRWithTriggerReplaced(self) -> None:
		"""	CREATE <TGR> with expected trigger result: TRIGGER_REPLACED"""
		self._runTriggerTypeCreateTest(TriggerStatus.TRIGGER_REPLACED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_createTGRWithTriggerUnconfirmed(self) -> None:
		"""	CREATE <TGR> with expected trigger result: TRIGGER_UNCONFIRMED"""
		self._runTriggerTypeCreateTest(TriggerStatus.TRIGGER_UNCONFIRMED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_createTGRWithTriggerExpired(self) -> None:
		"""	CREATE <TGR> with expected trigger result: TRIGGER_EXPIRED"""
		self._runTriggerTypeCreateTest(TriggerStatus.TRIGGER_EXPIRED, 1)

	#
	#	UPDATE tests
	#

	def _runTriggerTypeUpdateTest(self, triggerType: TriggerStatus, 
							   	  delete: bool = True) -> None:
		"""	Run an UPDATE test for a specific triggerType. This is a helper function to avoid code duplication. 

			Args:
				triggerType: The triggerType to test. This is used to set the M2M-EXT-ID of the AE and TriggerRequest resources.
				delete: Whether to delete the TriggerRequest resource after the test. Set to False if you want to update it later.
		"""

		dct = 	{ 'm2m:tgr' : { 
					'tpe' : TriggerPurpose.registrationRequest,
		}}
		r, rsc = UPDATE(f'{aeURL}/{tgrRN}', self.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:tgr/tst'), TriggerStatus.PROCESSING.value, r)

		# Wait for the trigger to be processed
		testSleep(triggerSleepTime)

		# Check the status of the TriggerRequest
		r, rsc = RETRIEVE(f'{aeURL}/{tgrRN}', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:tgr/tst'), triggerType.value, r)

		# DELETE the TGR to clean up
		if delete:
			r, rsc = DELETE(f'{aeURL}/{tgrRN}', self.originator)
			self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_updateTGRWithTriggerDelivered(self) -> None:
		"""	UPDATE <TGR> with expected trigger result: TRIGGER_DELIVERED"""

		# First create an initial TriggerRequest 
		self._runTriggerTypeCreateTest(TriggerStatus.TRIGGER_DELIVERED, updatePrepare=True)

		# ... then update it to trigger a new request and check the result again
		self._runTriggerTypeUpdateTest(TriggerStatus.TRIGGER_DELIVERED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_updateTGRWithTriggerFailed(self) -> None:
		"""	UPDATE <TGR> with expected trigger result: TRIGGER_FAILED"""

		# First create an initial TriggerRequest 
		self._runTriggerTypeCreateTest(TriggerStatus.TRIGGER_FAILED, updatePrepare=True)

		# ... then update it to trigger a new request and check the result again
		self._runTriggerTypeUpdateTest(TriggerStatus.TRIGGER_FAILED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_updateTGRWithTriggerReplaced(self) -> None:
		"""	UPDATE <TGR> with expected trigger result: TRIGGER_REPLACED"""

		# First create an initial TriggerRequest 
		self._runTriggerTypeCreateTest(TriggerStatus.TRIGGER_REPLACED, updatePrepare=True)

		# ... then update it to trigger a new request and check the result again
		self._runTriggerTypeUpdateTest(TriggerStatus.TRIGGER_REPLACED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_updateTGRWithTriggerUnconfirmed(self) -> None:
		"""	UPDATE <TGR> with expected trigger result: TRIGGER_UNCONFIRMED"""

		# First create an initial TriggerRequest 
		self._runTriggerTypeCreateTest(TriggerStatus.TRIGGER_UNCONFIRMED, updatePrepare=True)

		# ... then update it to trigger a new request and check the result again
		self._runTriggerTypeUpdateTest(TriggerStatus.TRIGGER_UNCONFIRMED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_updateTGRWithTriggerExpired(self) -> None:
		"""	UPDATE <TGR> with expected trigger result: TRIGGER_EXPIRED"""

		# First create an initial TriggerRequest 
		self._runTriggerTypeCreateTest(TriggerStatus.TRIGGER_EXPIRED, timeout=1, updatePrepare=True)

		# ... then update it to trigger a new request and check the result again
		self._runTriggerTypeUpdateTest(TriggerStatus.TRIGGER_EXPIRED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_updateTGRWhileProcessingFail(self) -> None:
		"""	UPDATE <TGR> while in PROCESSING state -> Fail"""

		# Update the AE to have a known M2M-EXT-ID for the default TriggerRequest handler
		dct:JSON = 	{ 'm2m:ae' : {
					'mei' : f'TRIGGER_DELIVERED@{C.exampleDomain}',
				}}
		r, rsc = UPDATE(aeURL, self.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Create a TriggerRequest that will be processed by the default TriggerRequest handler and will result in a TRIGGER_DELIVERED status
		dct = 	{ 'm2m:tgr' : { 
					'rn' : tgrRN,
					'mei' : f'TRIGGER_DELIVERED@{C.exampleDomain}',
					'tri' : 23,
					'tvt' : f'PT2S',	# This might be corrected by the CSE
					'tpe' : TriggerPurpose.establishConnection,
				}}
		r, rsc = CREATE(aeURL, self.originator, T.TGR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		if newUpdateBehavior:

			# DONT Wait for the trigger to be processed but immediately 
			# UPDATE the TriggerRequest
			dct = 	{ 'm2m:tgr' : { 
						'tpe' : TriggerPurpose.establishConnection,
					}}
			r, rsc = UPDATE(f'{aeURL}/{tgrRN}', self.originator, dct)
			self.assertEqual(rsc, RC.UNABLE_TO_REPLACE_REQUEST, r)

		else:
			# In this case we change the test behaviour: We are testing to replace it AFTER
			# it was processed. First, we wait
			testSleep(triggerSleepTime)

			dct = 	{ 'm2m:tgr' : { 
						'tpe' : TriggerPurpose.establishConnection,
					}}
			r, rsc = UPDATE(f'{aeURL}/{tgrRN}', self.originator, dct)
			self.assertEqual(rsc, RC.UNABLE_TO_REPLACE_REQUEST, r)


		# DELETE the TGR to clean up
		r, rsc = DELETE(f'{aeURL}/{tgrRN}', self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	#	RETRIEVE tests
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_retrieveTGRWhileProcessing(self) -> None:
		"""	RETRIEVE <TGR> while in PROCESSING state"""

		# Update the AE to have a known M2M-EXT-ID for the default TriggerRequest handler
		dct:JSON = 	{ 'm2m:ae' : {
					'mei' : f'TRIGGER_DELIVERED@{C.exampleDomain}',
				}}
		r, rsc = UPDATE(aeURL, self.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Create a TriggerRequest that will be processed by the default TriggerRequest handler and will result in a TRIGGER_DELIVERED status
		dct = 	{ 'm2m:tgr' : { 
					'rn' : tgrRN,
					'mei' : f'TRIGGER_DELIVERED@{C.exampleDomain}',
					'tri' : 23,
					'tvt' : f'PT2S',	# This might be corrected by the CSE
					'tpe' : TriggerPurpose.establishConnection,
				}}
		r, rsc = CREATE(aeURL, self.originator, T.TGR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DONT Wait for the trigger to be processed but immediately 
		# check the status of the TriggerRequest
		r, rsc = RETRIEVE(f'{aeURL}/{tgrRN}', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:tgr/tst'), TriggerStatus.PROCESSING.value, r)

		# DELETE the TGR to clean up
		r, rsc = DELETE(f'{aeURL}/{tgrRN}', self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	#	DELETE tests
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(cseType =='IN', 'TGR resource type is only allowed on an IN-CSE')
	def test_deleteTGRWhileProcessing(self) -> None:
		"""	DELETE <TGR> while in PROCESSING state"""

		# Update the AE to have a known M2M-EXT-ID for the default TriggerRequest handler
		dct:JSON = 	{ 'm2m:ae' : {
					'mei' : f'TRIGGER_DELIVERED@{C.exampleDomain}',
				}}
		r, rsc = UPDATE(aeURL, self.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Create a TriggerRequest that will be processed by the default TriggerRequest handler and will result in a TRIGGER_DELIVERED status
		dct = 	{ 'm2m:tgr' : { 
					'rn' : tgrRN,
					'mei' : f'TRIGGER_DELIVERED@{C.exampleDomain}',
					'tri' : 23,
					'tvt' : f'PT2S',	# This might be corrected by the CSE
					'tpe' : TriggerPurpose.establishConnection,
				}}
		r, rsc = CREATE(aeURL, self.originator, T.TGR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DONT Wait for the trigger to be processed but immediately 
		# DELETE the TriggerRequest
		r, rsc = DELETE(f'{aeURL}/{tgrRN}', self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestTGR, [

		# basic tests
		
		'test_createTGRnoTargetFail',
		'test_createTGR',
		'test_createTGRforCRUD',

		# CREATE tests

		'test_createTGRWithUnknownDomainFail',
		'test_createTGRWithTriggerDelivered',
		'test_createTGRWithTriggerFailed',
		'test_createTGRWithTriggerReplaced',
		'test_createTGRWithTriggerUnconfirmed',
		'test_createTGRWithTriggerExpired',

		# UPDATE tests

		'test_updateTGRWithTriggerDelivered',
		'test_updateTGRWithTriggerFailed',
		'test_updateTGRWithTriggerReplaced',
		'test_updateTGRWithTriggerUnconfirmed',
		'test_updateTGRWithTriggerExpired',
		'test_updateTGRWhileProcessingFail',

		# RETRIEVE tests

		'test_retrieveTGRWhileProcessing',

		# DELETE tests
		'test_deleteTGRWhileProcessing',
	
	])

	# Run tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)