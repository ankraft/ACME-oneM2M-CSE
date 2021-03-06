#
#	testREQ.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for REQ functionality
#

import unittest, sys, time
import requests
sys.path.append('../acme')
from typing import Tuple, Dict
from Constants import Constants as C
from Types import ResourceTypes as T, NotificationContentType, ResponseCode as RC, Operation, ResponseType, Permission
from init import *

# Headers for async requests
headers = {
	C.hfRTU	: NOTIFICATIONSERVER
}
headersEmpty = {
	C.hfRTU	: ''
}

class TestREQ(unittest.TestCase):

	ae 			= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		# Start notification server
		startNotificationServer()

		# create other resources
		dct =	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyAppId',
			 		'rr'  : False,
			 		'srv' : [ '3' ],
			 		'poa' : [ NOTIFICATIONSERVER ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		time.sleep(expirationSleep)	# give the server a moment to expire the resource
		disableShortExpirations()
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		stopNotificationServer()



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createREQFail(self) -> None:
		"""	Manually create <REQ> -> Fail """
		self.assertTrue(isTestExpirations())
		self.assertIsNotNone(TestREQ.ae)
		dct = 	{ 'm2m:req' : { }}	# type: ignore
		r, rsc = CREATE(cseURL, TestREQ.originator, T.REQ, dct)
		self.assertEqual(rsc, RC.operationNotAllowed)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynch(self) -> None:
		""" Retrieve <CB> non-blocking synchronous """
		r, rsc = RETRIEVE(f'{cseURL}?rt={ResponseType.nonBlockingRequestSynch:d}&rp={requestETDuration}', TestREQ.originator)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/lbl'))
		self.assertIn(TestREQ.originator, findXPath(r, 'm2m:req/lbl'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/op'))
		self.assertEqual(findXPath(r, 'm2m:req/op'), Operation.RETRIEVE)
		self.assertIsNotNone(findXPath(r, 'm2m:req/tg'))
		self.assertIsNone(findXPath(r, 'm2m:req/pc'))		# original content should be not set for retrieve
		self.assertIsNotNone(findXPath(r, 'm2m:req/org'))
		self.assertEqual(findXPath(r, 'm2m:req/org'), TestREQ.originator)
		self.assertIsNotNone(findXPath(r, 'm2m:req/rid'))
		self.assertEqual(findXPath(r, 'm2m:req/rid'), rqi)	# test the request ID from the original request
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
	def test_retrieveCSENBSynchMissingRP(self) -> None:
		""" Retrieve <CB> non-blocking synchronous, missing rp """
		r, rsc = RETRIEVE(f'{cseURL}?rt={ResponseType.nonBlockingRequestSynch:d}', TestREQ.originator)
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Default should be applied by the CSE
		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynchWrongRT(self) -> None:
		""" Retrieve <CB> non-blocking synchronous, wrong rt -> Fail """
		_, rsc = RETRIEVE(f'{cseURL}?rt=99999', TestREQ.originator)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBSynchExpireRequest(self) -> None:
		""" Retrieve <CB> non-blocking, but expired <REQ> resource -> Fail """ 
		r, rsc = RETRIEVE(f'{cseURL}?rt={ResponseType.nonBlockingRequestSynch:d}&rp={requestETDuration}', TestREQ.originator)
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Sleep "too" long
		time.sleep(expirationSleep)

		# get and check resource
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.notFound)	# <request> should have been deleted


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnknownNBSynch(self) -> None:
		""" Retrieve unknown resource, failure message via <REQ> """
		r, rsc = RETRIEVE(f'{cseURL}wrong?rt={ResponseType.nonBlockingRequestSynch:d}&rp={requestETDuration}', TestREQ.originator)
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.notFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTNBFlex(self) -> None:
		""" Retrieve <CNT> non-blocking flex """
		r, rsc = RETRIEVE(f'{cseURL}?rt={ResponseType.flexBlocking:d}&rp={requestETDuration}', TestREQ.originator)
		self.assertIn(rsc, [ RC.OK, RC.acceptedNonBlockingRequestSynch, RC.acceptedNonBlockingRequestAsynch ] )
		# -> Ignore the result


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTNBSynch(self) -> None:
		""" Create <CNT> non-blocking synchronous """
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(f'{aeURL}?rt={ResponseType.nonBlockingRequestSynch:d}&rp={requestETDuration}', TestREQ.originator, T.CNT, dct)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc'))			# original content should be set for CREATE
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc/m2m:cnt'))	# just a quick check
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.created)
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
		r, rsc = UPDATE(f'{cntURL}?rt={ResponseType.nonBlockingRequestSynch:d}&rp={requestETDuration}', TestREQ.originator, dct)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc'))			# original content should be set for UPDATE
		self.assertIsNotNone(findXPath(r, 'm2m:req/pc/m2m:cnt'))	# just a quick check
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.updated)
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
		r, rsc = DELETE(f'{cntURL}?rt={ResponseType.nonBlockingRequestSynch:d}&rp={requestETDuration}', TestREQ.originator)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestSynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# get and check resource
		time.sleep(requestCheckDelay)
		r, rsc = RETRIEVE(f'{csiURL}/{requestURI}', TestREQ.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:req'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors'))
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rsc'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rsc'), RC.deleted)
		self.assertIsNotNone(findXPath(r, 'm2m:req/ors/rqi'))
		self.assertEqual(findXPath(r, 'm2m:req/ors/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBAsynch(self) -> None:
		""" Retrieve <CB> non-blocking asynchronous """
		r, rsc = RETRIEVE(f'{cseURL}?rt={ResponseType.nonBlockingRequestAsynch:d}&rp={requestETDuration}', TestREQ.originator, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.OK)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/to'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/to'), CSEID[1:])
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/fr'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/fr'), TestREQ.originator)
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
		r, rsc = RETRIEVE(f'{cseURL}?rt={ResponseType.nonBlockingRequestAsynch:d}&rp={requestETDuration}', TestREQ.originator, headers=headersEmpty)
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNone(lastNotification)


	# URI is provided by the originator AE.poa
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCSENBAsynchNoRTU(self) -> None:
		""" Retrieve <CB> non-blocking asynchronous w/o RTU """
		clearLastNotification()
		r, rsc = RETRIEVE(f'{cseURL}?rt={ResponseType.nonBlockingRequestAsynch:d}&rp={requestETDuration}', TestREQ.originator)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.OK)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/to'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/to'), CSEID[1:])
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/fr'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/fr'), TestREQ.originator)
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
		r, rsc = RETRIEVE(f'{cseURL}wrong?rt={ResponseType.nonBlockingRequestAsynch:d}&rp={requestETDuration}', TestREQ.originator, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.notFound)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTNBAsynch(self) -> None:
		""" Create <CNT> non-blocking asynchronous """
		clearLastNotification()
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(f'{aeURL}?rt={ResponseType.nonBlockingRequestAsynch:d}&rp={requestETDuration}', TestREQ.originator, T.CNT, dct, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.created)
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
		r, rsc = UPDATE(f'{cntURL}?rt={ResponseType.nonBlockingRequestAsynch:d}&rp={requestETDuration}', TestREQ.originator, dct, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.updated)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/pc'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/fr'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/fr'), TestREQ.originator)
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
		r, rsc = DELETE(f'{cntURL}?rt={ResponseType.nonBlockingRequestAsynch:d}&rp={requestETDuration}', TestREQ.originator, headers=headers)
		rqi = lastRequestID()
		self.assertEqual(rsc, RC.acceptedNonBlockingRequestAsynch)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		requestURI = findXPath(r, 'm2m:uri')

		# Wait and then check notification
		time.sleep(requestCheckDelay)
		lastNotification = getLastNotification()
		self.assertIsNotNone(lastNotification)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp'))
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rsc'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rsc'), RC.deleted)
		self.assertIsNotNone(findXPath(lastNotification, 'm2m:rsp/rqi'))
		self.assertEqual(findXPath(lastNotification, 'm2m:rsp/rqi'), rqi)


def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	# Reconfigure the server to check faster for expirations.
	enableShortExpirations()

	suite = unittest.TestSuite()

	suite.addTest(TestREQ('test_createREQFail'))

	# nonBlockingSync
	suite.addTest(TestREQ('test_retrieveCSENBSynch'))
	suite.addTest(TestREQ('test_retrieveCSENBSynchMissingRP'))
	suite.addTest(TestREQ('test_retrieveCSENBSynchWrongRT'))
	suite.addTest(TestREQ('test_retrieveUnknownNBSynch'))
	suite.addTest(TestREQ('test_retrieveCSENBSynchExpireRequest'))
	suite.addTest(TestREQ('test_retrieveCNTNBFlex'))		# flex
	suite.addTest(TestREQ('test_createCNTNBSynch'))
	suite.addTest(TestREQ('test_updateCNTNBSynch'))
	suite.addTest(TestREQ('test_deleteCNTNBSynch'))

	# nonBlockingAsync
	suite.addTest(TestREQ('test_retrieveCSENBAsynch'))
	suite.addTest(TestREQ('test_retrieveCSENBAsynchEmptyRTU'))
	suite.addTest(TestREQ('test_retrieveCSENBAsynchNoRTU'))
	suite.addTest(TestREQ('test_retrieveUnknownNBAsynch'))
	suite.addTest(TestREQ('test_createCNTNBAsynch'))
	suite.addTest(TestREQ('test_updateCNTNBAsynch'))
	suite.addTest(TestREQ('test_deleteCNTNBASynch'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	disableShortExpirations()
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)

