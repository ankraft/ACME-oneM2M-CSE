#
#	testDiscovery.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for discovery requests
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from init import *

cnt2RN = '%s2' % cntRN

class TestDiscovery(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
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

		# create first container & CIN
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, C.tCNT, jsn)
		assert rsc == C.rcCreated, 'cannot create container'
		# create 5 contentInstances with different labels
		for i in range(0,5):
			jsn = 	{ 'm2m:cin' : {
						'cnf' : 'a',
						'con' : 'aValue',
						'lbl' : [ 'tag:%d' %i ]
					}}
			r, rsc = CREATE(cntURL, TestDiscovery.originator, C.tCIN, jsn)

		# create second container & CIN
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cnt2RN,
				}}
		cls.cnt2, rsc = CREATE(aeURL, cls.originator, C.tCNT, jsn)
		assert rsc == C.rcCreated, 'cannot create container'
		# create 5 contentInstances with different labels
		for i in range(0,5):
			jsn = 	{ 'm2m:cin' : {
						'cnf' : 'b',
						'con' : 'bValue',
						'lbl' : [ 'tag:%d' %i ]
					}}
			r, rsc = CREATE('%s2' % cntURL, TestDiscovery.originator, C.tCIN, jsn)

	@classmethod
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	def test_discoverCNTUnderAE(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=8&ty=%d' % (aeURL, C.tCNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:cnt')), 2)
		self.assertEqual(findXPath(r, 'm2m:cnt/{0}/rn'), cntRN)
		self.assertEqual(findXPath(r, 'm2m:cnt/{1}/rn'), cnt2RN)


	def test_discoverCNTUnderCSE(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=8&ty=%d' % (cseURL, C.tCNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:cnt')), 2)
		self.assertEqual(findXPath(r, 'm2m:cnt/{0}/rn'), cntRN)
		self.assertEqual(findXPath(r, 'm2m:cnt/{1}/rn'), cnt2RN)


	def test_discoverCIN(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=8&ty=%d' % (aeURL, C.tCIN), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:cin')), 10)


	def test_discoverCINByLBL(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=8&lbl=tag:0' % aeURL, TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:cin')), 2)
		self.assertEqual(findXPath(r, 'm2m:cin/{0}/lbl/{0}'), 'tag:0')
		self.assertEqual(findXPath(r, 'm2m:cin/{1}/lbl/{0}'), 'tag:0')


# test crb,cra - ct
# test ms, us - lt
# test cty - cnf
# test fo = or, and




def run():
	suite = unittest.TestSuite()
	suite.addTest(TestDiscovery('test_discoverCNTUnderAE'))
	suite.addTest(TestDiscovery('test_discoverCNTUnderCSE'))
	suite.addTest(TestDiscovery('test_discoverCIN'))
	suite.addTest(TestDiscovery('test_discoverCINByLBL'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures)


if __name__ == '__main__':
	_, errors = run()
	sys.exit(errors)
