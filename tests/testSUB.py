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
		# Start notification server
		startNotificationServer()

		# look for notification server
		hasNotificationServer = False
		try:
			r = requests.post(NOTIFICATIONSERVER, data='{"test": "test"}')
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
		stopNotificationServer()

		

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
			            "net": [ 1, 2, 3, 4 ]
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


	def test_updateCNT(self):
		jsn = 	{ 'm2m:cnt' : {
					'lbl' : [ 'aTag' ],
					'mni' : 10,
					'mbs' : 9999
 				}}
		cnt, rsc = UPDATE(cntURL, TestSUB.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		cnt, rsc = RETRIEVE(cntURL, TestSUB.originator)		# retrieve cnt again
		self.assertEqual(rsc, C.rcOK)
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


	def test_addCIN2CNT(self):
		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'aValue'
				}}
		r, rsc = CREATE(cntURL, TestSUB.originator, C.tCIN, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/ri'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')


	def test_removeCNT(self):
		r, rsc = DELETE(cntURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		self.assertEqual(rsc, C.rcDeleted)


	def test_addCNTAgain(self):
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		TestSUB.cnt, rsc = CREATE(aeURL, TestSUB.originator, C.tCNT, jsn)
		assert rsc == C.rcCreated, 'cannot create container'
		TestSUB.cntRI = findXPath(TestSUB.cnt, 'm2m:cnt/ri')


	def test_deleteSUBByUnknownOriginator(self):
		_, rsc = DELETE(subURL, 'Cwrong')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	def test_deleteSUBByAssignedOriginator(self):
		_, rsc = DELETE(subURL, TestSUB.originator)
		self.assertEqual(rsc, C.rcDeleted)


# TODO expirationCounter

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
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures)

if __name__ == '__main__':
	_, errors = run()
	sys.exit(errors)

