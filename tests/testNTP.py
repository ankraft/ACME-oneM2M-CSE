#
#	testNTP.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for notificationTargetPolicy resources
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, ProcessControl, ProcessState
from init import *
		

_defaultNTPRN = 'defaultNTP'
""" Default NTP resource name. This may vary for different implementations. """


class TestNTP(unittest.TestCase):

	ae 			= None
	aeRI		= None

	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup Test NotificationTargetPolicy')

		# Start notification server
		#startNotificationServer()

		dct:JSON = 	{ 'm2m:ae' : {
						'rn'  : aeRN, 
						'api' : APPID,
						'rr'  : True,
						'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'

		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		cls.aeRI = findXPath(cls.ae, 'm2m:ae/ri')


		testCaseEnd('Setup Test NotificationTargetPolicy')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		testCaseStart('TearDown Test NotificationTargetPolicy')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(ntpURL, ORIGINATOR)	
		DELETE(f'{ntpURL}2', ORIGINATOR)
		testCaseEnd('TearDown Test NotificationTargetPolicy')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)

	#########################################################################

	#
	#	Basic tests
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNTPWithAdminCreatorFail(self) -> None:
		"""	CREATE <NTP> with CSE admin creator -> Fail"""

		dct:JSON = { 'm2m:ntp': {
			'rn'  : ntpRN,
			'acn' : 1,
			'plbl': 'test',
			'cr' : None,

		}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.NTP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNTP(self) -> None:
		"""	CREATE <NTP> """

		dct:JSON = { 'm2m:ntp': {
			'rn'  : ntpRN,
			'acn' : 1,
			'plbl': 'test',
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveNTP(self) -> None:
		"""	RETRIEVE <NTP>"""

		r, rsc = RETRIEVE(ntpURL, self.originator)
		self.assertEqual(rsc, RC.OK, r)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateNTP(self) -> None:
		"""	UPDATE <NTP>"""
		dct:JSON = { 'm2m:ntp': {
			'lbl' : [ 'test' ],
		}}
		r, rsc = UPDATE(ntpURL, self.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(lbl := findXPath(r, 'm2m:ntp/lbl'), r)
		self.assertEqual(lbl, [ 'test' ], r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteNTP(self) -> None:
		"""	DELETE <NTP>"""

		r, rsc = DELETE(ntpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNTPwithSameCreatorAndLabelFail(self) -> None:
		"""	CREATE <NTP> with the same creator and same label -> Fail"""

		dct:JSON = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}2',
			'acn' : 1,
			'plbl': 'test',
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateNTPwithSameCreatorAndLabelFail(self) -> None:
		"""	UPDATE <NTP> with the same creator and same label -> Fail"""

		# First create a correct <NTP> resource
		dct:JSON = { 'm2m:ntp': {
			'rn'  : f'{ntpRN}2',
			'acn' : 1,
			'plbl': 'test2',	# This label is different
			'cr' : None,
		}}
		r, rsc = CREATE(cseURL, self.originator, T.NTP, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Now try to update it with the same creator and an existing label
		dct = { 'm2m:ntp': {
			'plbl': 'test',	# This label is the same as an existing one
		}}
		r, rsc = UPDATE(f'{ntpURL}2', self.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


		# DELETE the <NTP> resource
		r, rsc = DELETE(f'{ntpURL}2', self.originator)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSystemDefaultNTPFail(self) -> None:
		"""	DELETE <NTP> with system default NTP -> Fail"""

		r, rsc = DELETE(f'{cseURL}/{_defaultNTPRN}', ORIGINATOR) # delete the NTP
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

	#########################################################################


def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestNTP, [

		# basic tests
		'test_createNTPWithAdminCreatorFail',
		'test_createNTP',
		'test_retrieveNTP',
		'test_updateNTP',
		'test_deleteNTP',

		# Advanved tests
		'test_createNTP',	# recreate
		'test_createNTPwithSameCreatorAndLabelFail',
		'test_updateNTPwithSameCreatorAndLabelFail',
		'test_deleteSystemDefaultNTPFail',	# delete system default NTP
		
	])

	# Run the tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)