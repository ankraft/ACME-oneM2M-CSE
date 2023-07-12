#
#	testREQ.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for REQ functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from rich import print
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, Operation, ResponseType, RequestStatus
from init import *

# Headers for async requests
headers = {
	#C.hfRTU	: NOTIFICATIONSERVER+'&'+NOTIFICATIONSERVER
	C.hfRTU	: NOTIFICATIONSERVER
}
headers2 = {
	C.hfRTU	: NOTIFICATIONSERVER+'&'+NOTIFICATIONSERVER
}
headersRTUEmpty = {
	C.hfRTU	: ''
}


class TestREQ(unittest.TestCase):

	ae 			= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestREQ')
		# Start notification server
		startNotificationServer()

		# look for notification server
		assert isNotificationServerRunning(), 'Notification server cannot be reached'

		# create other resources
		dct =	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
			 		'rr'  : True,
			 		'srv' : [ RELEASEVERSION],
			 		'poa' : [ NOTIFICATIONSERVER ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		testCaseEnd('Setup TestREQ')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			disableShortResourceExpirations()
			return
		testCaseStart('TearDown TestREQ')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		disableShortResourceExpirations()
		testCaseEnd('TearDown TestREQ')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createREQFail(self) -> None:
		"""	Manually create <REQ> -> Fail """
		self.assertTrue(isTestResourceExpirations())
		self.assertIsNotNone(TestREQ.ae)
		dct = 	{ 'm2m:req' : { }}	# type: ignore
		r, rsc = CREATE(cseURL, TestREQ.originator, T.REQ, dct)
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynch(self) -> None:
		""" Retrieve <CB> non-blocking synchronous """
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestSynch)}&rp={requestETDuration}', TestREQ.originator)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC, r)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		testSleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNone(findXPath(r, 'm2m:req/st'))	# test absence of stateTag
		self.assertIsNotNone(findXPath(r, 'm2m:req/lbl'))
		self.assertIn(TestREQ.originator, findXPath(r, 'm2m:req/lbl'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/op'))
		self.assertEqual(findXPath(r, 'm2m:req/op'), Operation.RETRIEVE)
		self.assertIsNotNone(findXPath(r, 'm2m:req/tg'))
		self.assertIsNone(findXPath(r, 'm2m:req/pc'))		# original content should be not set for retrieve
		self.assertIsNotNone(findXPath(r, 'm2m:req/org'))
		self.assertEqual(findXPath(r, 'm2m:req/org'), TestREQ.originator)
		self.assertIsNotNone(findXPath(r, 'm2m:req/rid'))
		self.assertEqual(findXPath(r, 'm2m:req/rid'), rqi, r)	# test the request ID from the original request
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi/rt'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi/rt/rtv'))
		self.assertEqual(findXPath(r, 'm2m:req/mi/rt/rtv'), ResponseType.nonBlockingRequestSynch) 
		self.assertIsNotNone(findXPath(r, 'm2m:req/mi/rp'), requestETDuration)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rqi'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rqi'), rqi)	# test the request ID from the original request
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc/m2m:cb'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/pc/m2m:cb/ty'), T.CSEBase)	# Is the content the CSEBase


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynchValidateREQ(self) -> None:
		""" Retrieve <CB> non-blocking synchronous. Validate <REQ>"""

		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestSynch)}&rp={requestETDuration2}', 
						  TestREQ.originator,
						  headers={ C.hfOET : DateUtils.getResourceDate(requestCheckDelay)})	# set OET to now+requestCheckDelay/2
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC, r)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')
		rqi = lastRequestID()

		# Immediately retrieve <request>
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:req/rs'), r)
		self.assertEqual(findXPath(r, 'm2m:req/rs'), RequestStatus.PENDING, r)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.ACCEPTED)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rqi'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rqi'), rqi)	# test the request ID from the original request


		# get and check <request> after a delay to give the operation time to run
		testSleep(requestCheckDelay * 2)
		r2, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK, r2)
		self.assertIsNotNone(findXPath(r, 'm2m:req/lt'))
		self.assertIsNotNone(findXPath(r2, 'm2m:req/lt'))
		self.assertGreater(findXPath(r2, 'm2m:req/lt'), findXPath(r, 'm2m:req/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/rs'))
		self.assertEqual(findXPath(r2, 'm2m:req/rs'), RequestStatus.COMPLETED)
		self.assertIsNotNone(findXPath(r2, 'm2m:req/ors'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testResultPersistence(self) -> None:
		""" Retrieve <CB> non-blocking synchronous. Test Result Persistent and expiration -> Fail"""
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestSynch)}&rp={requestETDuration}', TestREQ.originator)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC, r)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		testSleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK, r)

		# Wait a bit longer. The <req> should have been deleted.
		testSleep(expirationCheckDelay * 2)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.NOT_FOUND, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynchMissingRP(self) -> None:
		""" Retrieve <CB> non-blocking synchronous, missing rp """
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestSynch)}', TestREQ.originator)
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Default should be applied by the CSE
		# get and check resource
		testSleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynchWrongRT(self) -> None:
		""" Retrieve <CB> non-blocking synchronous, wrong rt -> Fail """
		_, rsc = RETRIEVE(f'{cseURL}?rt=99999', TestREQ.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynchExpireRequest(self) -> None:
		""" Retrieve <CB> non-blocking, but expired <REQ> resource -> Fail """ 
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestSynch)}&rp={requestETDuration}', TestREQ.originator)
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Sleep "too" long
		testSleep(expirationSleep)

		# get and check resource
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.NOT_FOUND)	# <request> should have been deleted


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnknownNBSynch(self) -> None:
		""" Retrieve unknown resource, failure message via <REQ> """
		r, rsc = RETRIEVE(f'{cseURL}wrong?rt={int(ResponseType.nonBlockingRequestSynch)}&rp={requestETDuration}', TestREQ.originator)
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		testSleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.NOT_FOUND)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTNBFlex(self) -> None:
		""" Retrieve <CNT> non-blocking flex """
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.flexBlocking)}&rp={requestETDuration}', TestREQ.originator)
		self.assertIn(rsc, [ RC.OK, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC, RC.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC ] )
		# -> Ignore the result


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTNBFlexIntegerDuration(self) -> None:
		""" Retrieve <CNT> non-blocking flex (duration as integer)"""
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.flexBlocking)}&rp={requestETDurationInteger}', TestREQ.originator)
		self.assertIn(rsc, [ RC.OK, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC, RC.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC ] )
		# -> Ignore the result



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTNBFlexWrongDuration(self) -> None:
		""" Retrieve <CNT> non-blocking flex (duration = xxx) -> Fail"""
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.flexBlocking)}&rp=xxx', TestREQ.originator)
		# r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.flexBlocking)}&rp={requestETDurationInteger}', TestREQ.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST )
		# -> Ignore the result


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTNBSynch(self) -> None:
		""" Create <CNT> non-blocking synchronous """
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(f'{aeURL}?rt={int(ResponseType.nonBlockingRequestSynch)}&rp={requestETDuration}', TestREQ.originator, T.CNT, dct)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'), r)
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		testSleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc'))			# original content should be set for CREATE
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc/m2m:cnt'))	# just a quick check
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc/m2m:cnt'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/pc/m2m:cnt/ty'), T.CNT)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rqi'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTNBSynch(self) -> None:
		""" Update <CNT> non-blocking synchronous """
		dct = 	{ 'm2m:cnt' : { 
					'lbl' : [ 'aLabel' ]
				}}
		r, rsc = UPDATE(f'{cntURL}?rt={int(ResponseType.nonBlockingRequestSynch)}&rp={requestETDuration}', TestREQ.originator, dct)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		testSleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc'))			# original content should be set for UPDATE
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc/m2m:cnt'))	# just a quick check
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.UPDATED)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc/m2m:cnt'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/pc/m2m:cnt/ty'), T.CNT)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/pc/m2m:cnt/lbl'))
		self.assertIn('aLabel', findXPath(r, 'm2m:req/ors/pc/m2m:cnt/lbl'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rqi'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTNBSynch(self) -> None:
		""" Delete <CNT> non-blocking synchronous """
		r, rsc = DELETE(f'{cntURL}?rt={int(ResponseType.nonBlockingRequestSynch)}&rp={requestETDuration}', TestREQ.originator)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		testSleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.DELETED)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rqi'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynchWithRET(self) -> None:
		""" Retrieve <CB> non-blocking synchronous with Request Expiration Timestamp"""
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestSynch)}', TestREQ.originator, headers={C.hfRET : f'{requestETDuration}'})
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC, r)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		testSleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynchWithRETshort(self) -> None:
		""" Retrieve <CB> non-blocking synchronous with short Request Expiration Timestamp -> FAIL """
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestSynch)}', TestREQ.originator, headers={C.hfRET : f'{expirationCheckDelay*1000/2}'})
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC, r)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource. Should not be found anymore
		testSleep(expirationSleep)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.NOT_FOUND, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynchWithVSI(self) -> None:
		""" Retrieve <CB> non-blocking synchronous with Vendor Information"""
		vsi = 'some vendor information'
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestSynch)}', TestREQ.originator, headers={C.hfVSI : vsi})
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_SYNC, r)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		testSleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:req/mi/vsi'), vsi, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBAsynch(self) -> None:
		""" Retrieve <CB> non-blocking asynchronous """
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestAsynch)}&rp={requestETDuration}', TestREQ.originator, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC, r)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		testSleep(requestCheckDelay)
		lastNotification = getLastNotification(wait = notificationDelay)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.OK)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/to'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/to'), TestREQ.originator)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/fr'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/fr'), CSEID)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb/ty'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb/ty'), T.CSEBase)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBAsynch2(self) -> None:
		""" Retrieve <CB> non-blocking asynchronous w/ two RTU URLs"""
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestAsynch)}&rp={requestETDuration}', TestREQ.originator, headers=headers2)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC, r)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		testSleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.OK)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/to'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/to'), TestREQ.originator)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/fr'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/fr'), CSEID)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb/ty'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb/ty'), T.CSEBase)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


	# no notification is sent
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBAsynchEmptyRTU(self) -> None:
		""" Retrieve <CB> non-blocking asynchronous w/ empty RTU """
		clearLastNotification()
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestAsynch)}&rp={requestETDuration}', TestREQ.originator, headers=headersRTUEmpty)
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		testSleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNone(lastNotification)


	# URI is provided by the originator AE.poa
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBAsynchNoRTU(self) -> None:
		""" Retrieve <CB> non-blocking asynchronous w/o RTU """
		clearLastNotification()
		r, rsc = RETRIEVE(f'{cseURL}?rt={int(ResponseType.nonBlockingRequestAsynch)}&rp={requestETDuration}', TestREQ.originator)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		testSleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.OK)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/to'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/to'), TestREQ.originator)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/fr'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/fr'), CSEID)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb/ty'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cb/ty'), T.CSEBase)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnknownNBAsynch(self) -> None:
		""" Retrieve unknown resource non-blocking asynchronous """
		clearLastNotification()
		r, rsc = RETRIEVE(f'{cseURL}wrong?rt={int(ResponseType.nonBlockingRequestAsynch)}&rp={requestETDuration}', TestREQ.originator, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		testSleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.NOT_FOUND)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTNBAsynch(self) -> None:
		""" Create <CNT> non-blocking asynchronous """
		clearLastNotification()
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(f'{aeURL}?rt={int(ResponseType.nonBlockingRequestAsynch)}&rp={requestETDuration}', TestREQ.originator, T.CNT, dct, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		testSleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.CREATED)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/ty'), T.CNT)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTNBAsynch(self) -> None:
		""" Update <CNT> non-blocking asynchronos """
		clearLastNotification()
		dct = 	{ 'm2m:cnt' : { 
					'lbl' : [ 'aLabel' ]
				}}
		r, rsc = UPDATE(f'{cntURL}?rt={int(ResponseType.nonBlockingRequestAsynch)}&rp={requestETDuration}', TestREQ.originator, dct, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		testSleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.UPDATED)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/to'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/to'), TestREQ.originator)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/fr'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/fr'), CSEID)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/ty'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/ty'), T.CNT)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/lbl'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/ty'), T.CNT)
		self.assertIn('aLabel', findXPath(lastNotification, 'm2m:rsp/pc/m2m:cnt/lbl'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTNBASynch(self) -> None:
		""" Delete <CNT> non-blocking asynchronous """
		clearLastNotification()
		r, rsc = DELETE(f'{cntURL}?rt={int(ResponseType.nonBlockingRequestAsynch)}&rp={requestETDuration}', TestREQ.originator, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.ACCEPTED_NON_BLOCKING_REQUEST_ASYNC)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Wait and then check notification
		testSleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.DELETED)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	# Reconfigure the server to check faster for expirations.
	enableShortResourceExpirations()	# switched off in tear-down
	if not isTestResourceExpirations():
		print('\n[red reverse] Error configuring the CSE\'s test settings ')
		print('Did you enable [i]remote configuration[/i] for the CSE?\n')
		return 0,0,1,0.0

	suite = unittest.TestSuite()

	addTest(suite, TestREQ('test_createREQFail'))

	# nonBlockingSync
	addTest(suite, TestREQ('test_retrieveCSENBSynch'))
	addTest(suite, TestREQ('test_retrieveCSENBSynchValidateREQ'))
	addTest(suite, TestREQ('test_retrieveCSENBSynchMissingRP'))
	addTest(suite, TestREQ('test_retrieveCSENBSynchWrongRT'))
	addTest(suite, TestREQ('test_retrieveUnknownNBSynch'))
	addTest(suite, TestREQ('test_retrieveCSENBSynchExpireRequest'))
	addTest(suite, TestREQ('test_testResultPersistence'))
	addTest(suite, TestREQ('test_retrieveCNTNBFlex'))					# flex
	addTest(suite, TestREQ('test_retrieveCNTNBFlexIntegerDuration'))		# flex
	addTest(suite, TestREQ('test_retrieveCNTNBFlexWrongDuration'))		# flex
	addTest(suite, TestREQ('test_createCNTNBSynch'))
	addTest(suite, TestREQ('test_updateCNTNBSynch'))
	addTest(suite, TestREQ('test_deleteCNTNBSynch'))
	addTest(suite, TestREQ('test_retrieveCSENBSynchWithRET'))
	addTest(suite, TestREQ('test_retrieveCSENBSynchWithRETshort'))
	addTest(suite, TestREQ('test_retrieveCSENBSynchWithVSI'))

	# nonBlockingAsync
	addTest(suite, TestREQ('test_retrieveCSENBAsynch'))
	addTest(suite, TestREQ('test_retrieveCSENBAsynch2'))
	addTest(suite, TestREQ('test_retrieveCSENBAsynchEmptyRTU'))
	addTest(suite, TestREQ('test_retrieveCSENBAsynchNoRTU'))
	addTest(suite, TestREQ('test_retrieveUnknownNBAsynch'))
	addTest(suite, TestREQ('test_createCNTNBAsynch'))
	addTest(suite, TestREQ('test_updateCNTNBAsynch'))
	addTest(suite, TestREQ('test_deleteCNTNBASynch'))

	try:
		result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
		printResult(result)
	finally:
		stopNotificationServer()
		testSleep(expirationSleep)	# give the CSE a moment to expire the resource
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)

