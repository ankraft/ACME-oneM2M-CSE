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
from init import *


class TestSUB(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		# look for notification server
		hasNotificationServer = False
		try:
			r = requests.post(NOTIFICATIONSERVER, data='{}')
			hasNotificationServer = True
		except Exception as e:
			pass
		finally:	
			assert hasNotificationServer, 'Notification server cannot be reached'

		# create other resources
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		jsn = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', C.tAE, jsn)	# AE to work under
		assert rsc == C.rcCreated, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, C.tCNT, jsn)
		assert rsc == C.rcCreated, 'cannot create container'
		cls.cntRI = findXPath(cls.cnt, 'm2m:cnt/ri')


	@classmethod
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		

	def test_createSUB(self):
		self.assertIsNotNone(TestSUB.cse)
		self.assertIsNotNone(TestSUB.ae)
		self.assertIsNotNone(TestSUB.cnt)
		jsn = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        "enc": {
			            "net": [ 1, 3 ]
        			},
        			"nu": [ NOTIFICATIONSERVER ],
					'su': NOTIFICATIONSERVER
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, C.tSUB, jsn)
		self.assertEqual(rsc, C.rcCreated)


	def test_retrieveSUB(self):
		_, rsc = RETRIEVE(subURL, TestSUB.originator)
		self.assertEqual(rsc, C.rcOK)


	def test_retrieveSUBWithWrongOriginator(self):
		_, rsc = RETRIEVE(subURL, 'Cwrong')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	def test_attributesSUB(self):
		r, rsc = RETRIEVE(subURL, TestSUB.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:sub/ty'), C.tSUB)
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


	def test_createSUBWrong(self):
		jsn = 	{ 'm2m:sub' : { 
					'rn' : '%sWrong' % subRN,
			        "enc": {
			            "net": [ 1, 3 ]
        			},
        			"nu": [ NOTIFICATIONSERVERW ]
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, C.tSUB, jsn)
		self.assertNotEqual(rsc, C.rcCreated)
		self.assertEqual(rsc, C.rcSubscriptionVerificationInitiationFailed)
		

	def test_updateSUB(self):
		jsn = 	{ 'm2m:sub' : { 
					'exc': 5
				}}
		r, rsc = UPDATE(subURL, TestSUB.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		self.assertIsInstance(findXPath(r, 'm2m:sub/exc'), int)
		self.assertEqual(findXPath(r, 'm2m:sub/exc'), 5)

# add cin to cnt
# remove sub with wrong originator
# remove sub


# TODO expirationCounter


if __name__ == '__main__':
	suite = unittest.TestSuite()
	suite.addTest(TestSUB('test_createSUB'))
	suite.addTest(TestSUB('test_retrieveSUB'))
	suite.addTest(TestSUB('test_retrieveSUBWithWrongOriginator'))
	suite.addTest(TestSUB('test_attributesSUB'))
	suite.addTest(TestSUB('test_createSUBWrong'))
	suite.addTest(TestSUB('test_updateSUB'))
	unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)


