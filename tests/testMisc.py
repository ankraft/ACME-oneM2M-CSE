#
#	testMisc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Miscellaneous unit tests
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
import isodate
from typing import Tuple
from acme.etc.Types import NotificationEventType, ResponseStatusCode as RC, ResourceTypes as T
from acme.etc.DateUtils import getResourceDate
from init import *

# TODO move a couple of tests to a http or general request test


class TestMisc(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestMisc')
		# Start notification server
		startNotificationServer()
		testCaseEnd('Setup TestMisc')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestMisc')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		# Stop notification server
		stopNotificationServer()
		testCaseEnd('TearDown TestMisc')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPRVI(self) -> None:
		"""	Check RVI parameter in response """
		_, rsc = RETRIEVE(cseURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIn(C.hfRVI, lastHeaders())
		self.assertEqual(lastHeaders()[C.hfRVI], RELEASEVERSION)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPRET(self) -> None:
		"""	Check Request Expiration Timeout in request"""
		_, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfRET : getResourceDate(10)}) # request expiration in 10 seconds
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPVSI(self) -> None:
		"""	Check Vendor Information in request"""
		vsi = 'some vendor information'
		r, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfVSI : vsi})
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(lastHeaders()[C.hfVSI], vsi)


	def test_checkHTTPRETRelative(self) -> None:
		"""	Check Request Expiration Timeout in request (relative)"""
		_, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfRET : '10000'}) # request expiration in 10 seconds
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPRETWrong(self) -> None:
		"""	Check Request Expiration Timeout in request (past date) -> Fail"""
		_, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfRET : getResourceDate(-10)}) # request expiration in 10 seconds
		self.assertEqual(rsc, RC.requestTimeout)


	def test_checkHTTPRETRelativeWrong(self) -> None:
		"""	Check Request Expiration Timeout in request (relative, past date) -> Fail"""
		_, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfRET : '-10000'}) # request expiration in 10 seconds
		self.assertEqual(rsc, RC.requestTimeout)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPRVIWrongInRequest(self) -> None:
		"""	Check Wrong RVI version parameter in request -> Fail"""
		_, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfRVI : '1'})
		self.assertEqual(rsc, RC.releaseVersionNotSupported)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createUnknownResourceType(self) -> None:
		"""	Create an unknown resource type -> Fail """
		dct = 	{ 'foo:bar' : { 
					'rn' : 'foo',
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, 999, dct)	# type: ignore [arg-type]
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createEmpty(self) -> None:
		"""	Create with empty content -> Fail """
		dct = 	None
		r, rsc = CREATE(cseURL, ORIGINATOR, T.AE, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateEmpty(self) -> None:
		"""	Update with empty content -> Fail """
		dct = 	None
		r, rsc = UPDATE(cseURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAlphaResourceType(self) -> None:
		""" Create a resource with alphanumerical type -> Fail """
		dct = 	{ 'foo:bar' : { 
					'rn' : 'foo',
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, 'wrong', dct)	# type: ignore # Ignore type of type
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createWithWrongResourceType(self) -> None:
		"""	Create resource with not matching name and type -> Fail """
		dct = 	{ 'm2m:ae' : { 
					'rn' : 'foo',
				}}
		_, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(BINDING in [ 'http', 'https' ], 'Only when testing with http(s) binding')
	def test_checkHTTPmissingOriginator(self) -> None:
		"""	Check missing originator in request"""
		_, rsc = RETRIEVE(cseURL, None, headers={C.hfRET : getResourceDate(10)}) # request expiration in 10 seconds
		self.assertEqual(rsc, RC.badRequest)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkResponseOT(self) -> None:
		"""	Check Originating Timestamp in response """
		r, rsc = RETRIEVE(cseURL, ORIGINATOR, headers = { C.hfOT : DateUtils.getResourceDate() } )
		self.assertEqual(rsc, RC.OK)
		self.assertIn(C.hfOT, lastHeaders())
		try:
			raised = False
			isodate.parse_time(lastHeaders()[C.hfOT])
		except:
			raised = True
		finally:
			self.assertFalse(raised, f'Error parsing timestamp: {lastHeaders()[C.hfOT]}')
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkTargetRVI(self) -> None:
		"""	Check that RVI of the target is used in a request"""
		clearLastNotification()

		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
				 	'rr': True,
				 	'srv': [ '2' ],
					'poa': [ NOTIFICATIONSERVER ]
				}}
		ae, rsc = CREATE(cseURL, 'Crvi', T.AE, dct)
		self.assertEqual(rsc, RC.created, ae)

		# Send a notification to the AE. Content is not important here
		dct = 	{	'm2m:sgn' : {
					'nev' : {
						'rep' : {},
						'net' : NotificationEventType.resourceUpdate
					},
				}
			}

		r, rsc = NOTIFY(aeURL, 'Crvi', data = dct)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(getLastNotification(wait = notificationDelay), r)
		self.assertIsNotNone(getLastNotificationHeaders(), r)
		self.assertIsNotNone(rvi := getLastNotificationHeaders().get('X-M2M-RVI'), r)
		self.assertEqual(rvi, '2', r)

		# Remove AE
		r, rsc = DELETE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_validateListFail(self) -> None:
		"""	Check that list types are validated -> Fail"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
				 	'rr': True,
				 	'srv': [ '2' ],
					'lbl': [ 'aLabel', 23 ]
				}}
		ae, rsc = CREATE(cseURL, 'Crvi', T.AE, dct)
		self.assertEqual(rsc, RC.badRequest, ae)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_resourceWithoutRN(self) -> None:
		"""	Create and retrieve a <CNT> without RN"""
		dct = 	{ 'm2m:cnt' : {			# type:ignore [var-annotated]
				}}
		cnt, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.created, cnt)
		rn = findXPath(cnt, 'm2m:cnt/rn')
		url = f'{CSEURL}{CSERN}/{rn}'
		cnt2, rsc = RETRIEVE(url, ORIGINATOR)
		self.assertEqual(rsc, RC.OK, cnt2)
		r, rsc = DELETE(url, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_subWithoutRN(self) -> None:
		"""	Create and retrieve a <SUB> without RN"""
		dct = 	{ 'm2m:sub' : { 
					'nu': [ NOTIFICATIONSERVER ],
				}}

		sub, rsc = CREATE(cseURL, ORIGINATOR, T.SUB, dct)
		self.assertEqual(rsc, RC.created, sub)
		rn = findXPath(sub, 'm2m:sub/rn')
		url = f'{CSEURL}{CSERN}/{rn}'
		sub2, rsc = RETRIEVE(url, ORIGINATOR)
		self.assertEqual(rsc, RC.OK, sub2)
		r, rsc = DELETE(url, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted, r)
		

# TODO test for creating a resource with missing type parameter
# TODO test json with comments
# TODO test for ISO8601 format validation

def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
		
	addTest(suite, TestMisc('test_checkHTTPRVI'))
	addTest(suite, TestMisc('test_checkHTTPRET'))
	addTest(suite, TestMisc('test_checkHTTPVSI'))
	addTest(suite, TestMisc('test_checkHTTPRETRelative'))
	addTest(suite, TestMisc('test_checkHTTPRETWrong'))
	addTest(suite, TestMisc('test_checkHTTPRETRelativeWrong'))
	addTest(suite, TestMisc('test_checkHTTPRVIWrongInRequest'))
	addTest(suite, TestMisc('test_createUnknownResourceType'))
	addTest(suite, TestMisc('test_createEmpty'))
	addTest(suite, TestMisc('test_updateEmpty'))
	addTest(suite, TestMisc('test_createAlphaResourceType'))
	addTest(suite, TestMisc('test_createWithWrongResourceType'))
	addTest(suite, TestMisc('test_checkHTTPmissingOriginator'))
	addTest(suite, TestMisc('test_checkResponseOT'))
	addTest(suite, TestMisc('test_checkTargetRVI'))
	addTest(suite, TestMisc('test_validateListFail'))
	addTest(suite, TestMisc('test_resourceWithoutRN'))
	addTest(suite, TestMisc('test_subWithoutRN'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
