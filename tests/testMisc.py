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
from acme.etc.Types import NotificationEventType, ResponseStatusCode as RC, ResourceTypes as T, ResponseType
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
		DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)

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
		r, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfRET : getResourceDate(10)}) # request expiration in 10 seconds
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPVSI(self) -> None:
		"""	Check Vendor Information in request"""
		vsi = 'some vendor information'
		r, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfVSI : vsi})
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(lastHeaders()[C.hfVSI], vsi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPRETRelative(self) -> None:
		"""	Check Request Expiration Timeout in request (relative)"""
		_, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfRET : '10000'}) # request expiration in 10 seconds
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPRETWrong(self) -> None:
		"""	Check Request Expiration Timeout in request (past date) -> Fail"""
		_, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfRET : getResourceDate(-10)}) # request expiration in 10 seconds
		self.assertEqual(rsc, RC.REQUEST_TIMEOUT)


	def test_checkHTTPRETRelativeWrong(self) -> None:
		"""	Check Request Expiration Timeout in request (relative, past date) -> Fail"""
		_, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfRET : '-10000'}) # request expiration in 10 seconds
		self.assertEqual(rsc, RC.REQUEST_TIMEOUT)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkHTTPRVIWrongInRequest(self) -> None:
		"""	Check Wrong RVI version parameter in request -> Fail"""
		_, rsc = RETRIEVE(cseURL, ORIGINATOR, headers={C.hfRVI : '1'})
		self.assertEqual(rsc, RC.RELEASE_VERSION_NOT_SUPPORTED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createUnknownResourceType(self) -> None:
		"""	Create an unknown resource type -> Fail """
		dct = 	{ 'foo:bar' : { 
					'rn' : 'foo',
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, 999, dct)	# type: ignore [arg-type]
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createEmpty(self) -> None:
		"""	Create with empty content -> Fail """
		dct = 	None
		r, rsc = CREATE(cseURL, ORIGINATOR, T.AE, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateEmpty(self) -> None:
		"""	Update with empty content -> Fail """
		dct = 	None
		r, rsc = UPDATE(cseURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipIf(BINDING in [ 'coap', 'coaps' ], 'Not for CoAP binding tests')
	def test_createAlphaResourceType(self) -> None:
		""" Create a resource with alphanumerical type -> Fail """
		dct = 	{ 'foo:bar' : { 
					'rn' : 'foo',
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, 'wrong', dct)	# type: ignore # Ignore type of type
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createWithWrongResourceType(self) -> None:
		"""	Create resource with not matching name and type -> Fail """
		dct = 	{ 'm2m:ae' : { 
					'rn' : 'foo',
				}}
		_, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipUnless(BINDING in [ 'http', 'https' ], 'Only when testing with http(s) binding')
	def test_checkHTTPmissingOriginator(self) -> None:
		"""	Check missing originator in request"""
		_, rsc = RETRIEVE(cseURL, None, headers={C.hfRET : getResourceDate(10)}) # request expiration in 10 seconds
		self.assertEqual(rsc, RC.BAD_REQUEST)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_checkResponseOT(self) -> None:
		"""	Check Originating Timestamp in response """
		r, rsc = RETRIEVE(cseURL, ORIGINATOR, headers = { C.hfOT : DateUtils.getResourceDate() } )
		self.assertEqual(rsc, RC.OK)
		self.assertIn(C.hfOT, lastHeaders())
		try:
			raised = False
			isodate.parse_datetime(lastHeaders()[C.hfOT])
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
		self.assertEqual(rsc, RC.CREATED, ae)

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
		self.assertEqual(rsc, RC.DELETED, r)


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
		self.assertEqual(rsc, RC.BAD_REQUEST, ae)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_resourceWithoutRN(self) -> None:
		"""	Create and retrieve a <CNT> without RN"""
		dct = 	{ 'm2m:cnt' : {			# type:ignore [var-annotated]
				}}
		cnt, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, cnt)
		rn = findXPath(cnt, 'm2m:cnt/rn')
		url = f'{CSEURL}{CSERN}/{rn}'
		cnt2, rsc = RETRIEVE(url, ORIGINATOR)
		self.assertEqual(rsc, RC.OK, cnt2)
		r, rsc = DELETE(url, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_subWithoutRN(self) -> None:
		"""	Create and retrieve a <SUB> without RN"""
		dct = 	{ 'm2m:sub' : { 
					'nu': [ NOTIFICATIONSERVER ],
				}}

		sub, rsc = CREATE(cseURL, ORIGINATOR, T.SUB, dct)
		self.assertEqual(rsc, RC.CREATED, sub)
		rn = findXPath(sub, 'm2m:sub/rn')
		url = f'{CSEURL}{CSERN}/{rn}'
		sub2, rsc = RETRIEVE(url, ORIGINATOR)
		self.assertEqual(rsc, RC.OK, sub2)
		r, rsc = DELETE(url, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipIf(BINDING not in [ 'http', 'https' ], 'only for http')
	def test_createAEContentTypeWithSpacesHeader(self) -> None:
		""" Create <AE> with a content header with spaces (http only)"""
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN,
					'api': 'Nacme',
				 	'rr': False,
				 	'srv': [ RELEASEVERSION ]
				}}
		# Space in Content-Type header field
		ae, rsc = CREATE(cseURL, ORIGINATOREmpty, T.AE, dct, headers={'Content-Type' : 'application/json;       ty=2'})
		self.assertEqual(rsc, RC.CREATED)

		# delete it again
		r, rsc = DELETE(f'{CSEURL}{CSERN}/{aeRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	#	Partial RETRIEVE
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_partialRetrieveCSEBaseSingle(self) -> None:
		""" Partial RETRIEVE of CSEBase with single attribute in atrl argument"""
		r, rsc = RETRIEVE(f'{cseURL}?atrl=rn', ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:cb/rn'), CSERN, r)
		self.assertIsNone(findXPath(r, 'm2m:cb/ri'), r)
		

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_partialRetrieveCSEBaseMultiple(self) -> None:
		""" Partial RETRIEVE of CSEBase with multiple attributes in atrl argument"""
		r, rsc = RETRIEVE(f'{cseURL}?atrl=rn+ty', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cb/rn'), CSERN, r)
		self.assertEqual(findXPath(r, 'm2m:cb/ty'), ResourceTypes.CSEBase, r)
		self.assertIsNone(findXPath(r, 'm2m:cb/ri'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_partialDeleteCSEBaseFail(self) -> None:
		""" Partial DELETE of CSEBase with single attribute in atrl argument -> Fail"""
		r, rsc = DELETE(f'{cseURL}?atrl=rn', ORIGINATOR)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_partialRetrieveCSEBaseWrongRcnFail(self) -> None:
		""" Partial RETRIEVE of CSEBase with single attribute in atrl argument and wrong RCN -> Fail"""
		r, rsc = RETRIEVE(f'{cseURL}?atrl=rn&rcn=2', ORIGINATOR)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_partialRetrieveCSEBaseWrongAttributeFail(self) -> None:
		""" Partial RETRIEVE of CSEBase with single unsupported attribute in atrl argument (http only) -> Fail"""
		r, rsc = RETRIEVE(f'{cseURL}?atrl=mni', ORIGINATOR)	# try to get mni from CSEBase
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_partialRetrieveCSEBaseROAttribute(self) -> None:
		""" Partial RETRIEVE of CSEBase with single RO attribute ctm (http only)"""
		r, rsc = RETRIEVE(f'{cseURL}?atrl=ctm', ORIGINATOR)	# try to get mni from CSEBase
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:cb/ri'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_partialRetrieveCSingleOptionalAttribute(self) -> None:
		""" Partial RETRIEVE of a CNT optional attribute (http only)"""
		dct = 	{ 'm2m:cnt' : {			# type:ignore [var-annotated]
					'rn': cntRN,
				}}
		cnt, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, cnt)

		# RETRIEVE with single optional attribute
		r, rsc = RETRIEVE(f'{cseURL}/{cntRN}?atrl=mni', ORIGINATOR)	# try to get mni from CSEBase
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:cb/ri'), r)

		# delete the CNT again
		r, rsc = DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_partialRetrieveFCNT(self) -> None:
		""" Partial RETRIEVE of a FCNT optional attribute"""
		dct = 	{ 'cod:lock' : {			# type:ignore [var-annotated]
					'rn': fcntRN,
					'cnd': 'org.onem2m.common.moduleclass.lock',
					'lock': False,
				}}
		fcnt, rsc = CREATE(cseURL, ORIGINATOR, T.FCNT, dct)
		self.assertEqual(rsc, RC.CREATED, fcnt)

		# RETRIEVE with single optional attribute
		r, rsc = RETRIEVE(f'{cseURL}/{fcntRN}?atrl=lock', ORIGINATOR)	# try to get mni from CSEBase
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'cod:lock/ri'), r)
		self.assertIsNotNone(findXPath(r, 'cod:lock/lock'), r)

		# delete the CNT again
		r, rsc = DELETE(f'{cseURL}/{fcntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


# TODO test partial RETRIEVE of <CIN> with missing optional attribute



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_notifyAE(self) -> None:
		"""	NOTIFY an <AE>. Test forn non-arguments in the notification POST request """
		clearLastNotification()

		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
				 	'rr': True,
				 	'srv': [ '2' ],
					'poa': [ NOTIFICATIONSERVER ]
				}}
		ae, rsc = CREATE(cseURL, 'Carguments', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED, ae)

		# Send a notification to the AE. Content is not important here
		dct = 	{	'm2m:sgn' : {
					'nev' : {
						'rep' : {},
						'net' : NotificationEventType.resourceUpdate
					},
				}
			}

		r, rsc = NOTIFY(aeURL, 'Carguments', data = dct)
		self.assertEqual(rsc, RC.OK, r)

		notification = getLastNotification(wait = notificationDelay)
		notificationHeaders = getLastNotificationHeaders()
		notificationArgs = getLastNotificationArguments()

		self.assertIsNotNone(notification, r)
		self.assertIsNotNone(notificationHeaders, r)
		self.assertEqual(len(notificationArgs), 0, notificationArgs)

		# Remove AE
		r, rsc = DELETE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	#	No Response
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_noResponseRetrieve(self) -> None:
		"""	RETRIEVE with no response """
		dct = 	{ 'm2m:cnt' : {			# type:ignore [var-annotated]
					'rn': cntRN,
				}}
		cnt, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, cnt)

		# RETRIEVE with single optional attribute
		r, rsc = RETRIEVE(f'{cseURL}/{cntRN}?rt={int(ResponseType.noResponse)}', ORIGINATOR)	# try to get mni from CSEBase
		self.assertEqual(rsc, RC.NO_CONTENT, r)
		self.assertEqual(len(r), 0, r)

		testSleep(requestCheckDelay)

		# delete the CNT again
		r, rsc = DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_noResponseCreate(self) -> None:
		"""	CREATE with no response """
		dct = 	{ 'm2m:cnt' : {			# type:ignore [var-annotated]
					'rn': cntRN,
				}}
		r, rsc = CREATE(f'{cseURL}?rt={int(ResponseType.noResponse)}', ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.NO_CONTENT, r)
		self.assertEqual(len(r), 0, r)

		testSleep(requestCheckDelay)

		# delete the CNT again
		r, rsc = DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_noResponseUpdate(self) -> None:
		"""	UPDATE with no response """
		dct = 	{ 'm2m:cnt' : {			# type:ignore [var-annotated]
					'rn': cntRN,
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct2 = 	{ 'm2m:cnt' : {			# type:ignore [var-annotated]
					'lbl': [ 'test' ],
				}}
		r, rsc = UPDATE(f'{cseURL}/{cntRN}?rt={int(ResponseType.noResponse)}', ORIGINATOR, dct2)
		self.assertEqual(rsc, RC.NO_CONTENT, r)
		self.assertEqual(len(r), 0, r)

		testSleep(requestCheckDelay)

		# delete the CNT again
		r, rsc = DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_noResponseDelete(self) -> None:
		"""	DELETE with no response """
		dct = 	{ 'm2m:cnt' : {			# type:ignore [var-annotated]
					'rn': cntRN,
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		testSleep(requestCheckDelay)

		# delete the CNT again
		r, rsc = DELETE(f'{cseURL}/{cntRN}?rt={int(ResponseType.noResponse)}', ORIGINATOR)
		self.assertEqual(rsc, RC.NO_CONTENT, r)
		self.assertEqual(len(r), 0, r)



# TODO test for creating a resource with missing type parameter
# TODO test json with comments
# TODO test for ISO8601 format validation

def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestMisc, [

		'test_checkHTTPRVI',
		'test_checkHTTPRET',
		'test_checkHTTPVSI',
		'test_checkHTTPRETRelative',
		'test_checkHTTPRETWrong',
		'test_checkHTTPRETRelativeWrong',
		'test_checkHTTPRVIWrongInRequest',
		'test_createUnknownResourceType',
		'test_createEmpty',
		'test_updateEmpty',
		'test_createAlphaResourceType',
		'test_createWithWrongResourceType',
		'test_checkHTTPmissingOriginator',
		'test_checkResponseOT',
		'test_checkTargetRVI',
		'test_validateListFail',
		'test_resourceWithoutRN',
		'test_subWithoutRN',
		'test_createAEContentTypeWithSpacesHeader',

		# Partial retrieve
		'test_partialRetrieveCSEBaseSingle',
		'test_partialRetrieveCSEBaseMultiple',
		'test_partialDeleteCSEBaseFail',
		'test_partialRetrieveCSEBaseWrongRcnFail',
		'test_partialRetrieveCSEBaseWrongAttributeFail',
		'test_partialRetrieveCSEBaseROAttribute',
		'test_partialRetrieveCSingleOptionalAttribute',
		'test_partialRetrieveFCNT',

		# send NOTIFY requests
		'test_notifyAE',

		# No Response
		'test_noResponseRetrieve',
		'test_noResponseCreate',
		'test_noResponseUpdate',
		'test_noResponseDelete',

	])
	
	# Run the tests
	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
