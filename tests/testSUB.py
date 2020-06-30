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
        			"nu": [ NOTIFICATIONSERVER ]
				}}

		r, rsc = CREATE(aeURL, TestSUB.originator, C.tSUB, jsn)
		self.assertEqual(rsc, C.rcCreated)






	def test_retrieveSUB(self):
		_, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, C.rcOK)


	def test_retrieveGRPWithWrongOriginator(self):
		_, rsc = RETRIEVE(grpURL, 'Cwrong')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	def test_attributesGRP(self):
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:grp/ty'), C.tGRP)
		self.assertEqual(findXPath(r, 'm2m:grp/pi'), findXPath(TestGRP.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'm2m:grp/rn'), grpRN)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:grp/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:grp/et'))
		self.assertEqual(findXPath(r, 'm2m:grp/cr'), TestGRP.originator)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mt'))
		self.assertEqual(findXPath(r, 'm2m:grp/mt'), C.tMIXED)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/mnm'), 10)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mid'))
		self.assertIsInstance(findXPath(r, 'm2m:grp/mid'), list)
		self.assertEqual(len(findXPath(r, 'm2m:grp/mid')), 2)


	def test_updateGRP(self):
		jsn = 	{ 'm2m:grp' : { 
					'mnm': 15
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/mnm'), 15)

if __name__ == '__main__':
	suite = unittest.TestSuite()
	suite.addTest(TestSUB('test_createSUB'))

	unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)


