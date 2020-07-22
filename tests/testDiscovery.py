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
from Types import ResourceTypes as T
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
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, jsn)	# AE to work under
		assert rsc == C.rcCreated, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		# create first container & CIN
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, jsn)
		assert rsc == C.rcCreated, 'cannot create container'
		# create 5 contentInstances with different labels
		for i in range(0,5):
			jsn = 	{ 'm2m:cin' : {
						'cnf' : 'a',
						'con' : 'aValue',
						'lbl' : [ 'tag:%d' %i ]
					}}
			r, rsc = CREATE(cntURL, TestDiscovery.originator, T.CIN, jsn)

		# create second container & CIN
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cnt2RN,
				}}
		cls.cnt2, rsc = CREATE(aeURL, cls.originator, T.CNT, jsn)
		assert rsc == C.rcCreated, 'cannot create container'
		# create 5 contentInstances with different labels
		for i in range(0,5):
			jsn = 	{ 'm2m:cin' : {
						'cnf' : 'b',
						'con' : 'bValue',
						'lbl' : [ 'tag:%d' %i ]
					}}
			r, rsc = CREATE('%s2' % cntURL, TestDiscovery.originator, T.CIN, jsn)

	@classmethod
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	# rcnChildResourceReferences
	def test_discoverCNTUnderAERCN6(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d&ty=%d' % (aeURL, C.rcnChildResourceReferences, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:rrl/{0}/nm'), findXPath(r, 'm2m:rrl/{1}/nm'))
		self.assertIn(findXPath(r, 'm2m:rrl/{0}/nm'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:rrl/{1}/nm'), (cntRN, cnt2RN))
		self.assertEqual(findXPath(r, 'm2m:rrl/{0}/typ'), 3)
		self.assertEqual(findXPath(r, 'm2m:rrl/{1}/typ'), 3)
		self.assertNotEqual(findXPath(r, 'm2m:rrl/{0}/val'), findXPath(r, 'm2m:rrl/{1}/val'))
		self.assertIn(findXPath(r, 'm2m:rrl/{0}/val').split('/')[-1], (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:rrl/{1}/val').split('/')[-1], (cntRN, cnt2RN))


	#rcnDiscoveryResultReferences
	def test_discoveryCNTUnderAERCN11(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d&ty=%d' % (aeURL, C.rcnDiscoveryResultReferences, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:uril'))
		self.assertEqual(len(findXPath(r, 'm2m:uril')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:uril/{0}'), findXPath(r, 'm2m:uril/{1}'))
		self.assertGreater(len(findXPath(r, 'm2m:uril/{0}').split('/')), 2)
		self.assertGreater(len(findXPath(r, 'm2m:uril/{1}').split('/')), 2)
		self.assertIn(findXPath(r, 'm2m:uril/{0}').split('/')[-1], (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:uril/{1}').split('/')[-1], (cntRN, cnt2RN))


	# rcnAttributes (fail fail for discovery)
	def test_discoverCNTUnderAEWrongRCN1(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d&ty=%d' % (aeURL, C.rcnAttributes, T.CNT), TestDiscovery.originator)
		self.assertNotEqual(rsc, C.rcOK)


	# rcnAttributesAndChildResources (fail for discovery)
	def test_discoverCNTUnderAEWrongRCN4(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d&ty=%d' % (aeURL, C.rcnAttributesAndChildResources, T.CNT), TestDiscovery.originator)
		self.assertNotEqual(rsc, C.rcOK)


	# rcnAttributesAndChildResourceReferences (fail for discovery)
	def test_discoverCNTUnderAEWrongRCN5(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d&ty=%d' % (aeURL, C.rcnAttributesAndChildResourceReferences, T.CNT), TestDiscovery.originator)
		self.assertNotEqual(rsc, C.rcOK)


	# rcnChildResources
	def test_discoverCNTUnderAEWrongRCN8(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d&ty=%d' % (aeURL, C.rcnChildResources, T.CNT), TestDiscovery.originator)
		self.assertNotEqual(rsc, C.rcOK)


	# rcnModifiedAttributes (fail for retrieve)
	def test_discoverCNTUnderAEWrongRCN9(self):
		r, rsc = RETRIEVE('%s?u=1&rcn=%d&ty=%d' % (aeURL, C.rcnModifiedAttributes, T.CNT), TestDiscovery.originator)
		self.assertNotEqual(rsc, C.rcOK)


	# rcnChildResourceReferences
	def test_retrieveCNTUnderAERCN6(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnChildResourceReferences, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:rrl/{0}/nm'), findXPath(r, 'm2m:rrl/{1}/nm'))
		self.assertIn(findXPath(r, 'm2m:rrl/{0}/nm'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:rrl/{1}/nm'), (cntRN, cnt2RN))
		self.assertEqual(findXPath(r, 'm2m:rrl/{0}/typ'), 3)
		self.assertEqual(findXPath(r, 'm2m:rrl/{1}/typ'), 3)
		self.assertNotEqual(findXPath(r, 'm2m:rrl/{0}/val'), findXPath(r, 'm2m:rrl/{1}/val'))
		self.assertIn(findXPath(r, 'm2m:rrl/{0}/val').split('/')[-1], (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:rrl/{1}/val').split('/')[-1], (cntRN, cnt2RN))


	# rcnAttributes
	def test_retrieveCNTUnderAERCN1(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnAttributes, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertEqual(findXPath(r, 'm2m:ae/rn'), aeRN)


	# rcnAttributesAndChildResources
	def test_retrieveCNTUnderAERCN4(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnAttributesAndChildResources, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertEqual(findXPath(r, 'm2m:ae/rn'), aeRN)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt')), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertNotEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertIn(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'), (cntRN, cnt2RN))


	# rcnAttributesAndChildResourceReferences
	def test_retrieveCNTUnderAERCN5(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnAttributesAndChildResourceReferences, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertEqual(findXPath(r, 'm2m:ae/rn'), aeRN)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/ch'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/ch')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:ae/ch/{0}/nm'), findXPath(r, 'm2m:ae/ch/{1}/nm'))
		self.assertIn(findXPath(r, 'm2m:ae/ch/{0}/nm'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:ae/ch/{1}/nm'), (cntRN, cnt2RN))
		self.assertEqual(findXPath(r, 'm2m:ae/ch/{0}/typ'), 3)
		self.assertEqual(findXPath(r, 'm2m:ae/ch/{1}/typ'), 3)
		self.assertNotEqual(findXPath(r, 'm2m:ae/ch/{0}/val'), findXPath(r, 'm2m:ae/ch/{1}/val'))
		self.assertIn(findXPath(r, 'm2m:ae/ch/{0}/val').split('/')[-1], (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:ae/ch/{1}/val').split('/')[-1], (cntRN, cnt2RN))


	# rcnChildResources
	def test_retrieveCNTUnderAERCN8(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnChildResources, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNone(findXPath(r, 'm2m:ae/rn'), aeRN) # don't find other AE attributes
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt')), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertNotEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertIn(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'), (cntRN, cnt2RN))


	# rcnModifiedAttributes (fail for retrieve)
	def test_retrieveCNTUnderAEWrongRCN9(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnModifiedAttributes, T.CNT), TestDiscovery.originator)
		self.assertNotEqual(rsc, C.rcOK)


	# rcnDiscoveryResultReferences (fail for retrieve)
	def test_retrieveCNTUnderAEWrongRCN11(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnDiscoveryResultReferences, T.CNT), TestDiscovery.originator)
		self.assertNotEqual(rsc, C.rcOK)


	def test_retrieveCNTUnderCSE(self):
		r, rsc = RETRIEVE('%s?rcn=8&ty=%d' % (cseURL, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:cb'))
		self.assertIsNotNone(findXPath(r, 'm2m:cb/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:cb/m2m:cnt')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:cb/m2m:cnt/{0}/rn'), findXPath(r, 'm2m:cb/m2m:cnt/{1}/rn'))
		self.assertIn(findXPath(r, 'm2m:cb/m2m:cnt/{0}/rn'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:cb/m2m:cnt/{1}/rn'), (cntRN, cnt2RN))


	def test_retrieveCINUnderAE(self):
		r, rsc = RETRIEVE('%s?rcn=8&ty=%d' % (aeURL, T.CIN), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cin')), 10)


	def test_retrieveCINByLBLUnderAE(self):
		r, rsc = RETRIEVE('%s?rcn=8&lbl=tag:0' % aeURL, TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cin')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:ae/m2m:cin/{0}/rn'), findXPath(r, 'm2m:ae/m2m:cin/{1}/rn'))
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cin/{0}/lbl/{0}'), 'tag:0')
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cin/{1}/lbl/{0}'), 'tag:0')


	def test_retrieveCNTByCNIUnderAE(self):
		r, rsc = RETRIEVE('%s?rcn=8&cni=5' % aeURL, TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/cni'), 5)
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cnt/{1}/cni'), 5)

	def test_retrieveCNTByCNIUnderAEEmpty(self):
		r, rsc = RETRIEVE('%s?rcn=8&cni=10' % aeURL, TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'))


# test crb,cra - ct
# test ms, us - lt
# test cty - cnf
# test fo = or, and




def run():
	suite = unittest.TestSuite()
	suite.addTest(TestDiscovery('test_discoverCNTUnderAERCN6'))
	suite.addTest(TestDiscovery('test_discoveryCNTUnderAERCN11'))
	suite.addTest(TestDiscovery('test_discoverCNTUnderAEWrongRCN1'))
	suite.addTest(TestDiscovery('test_discoverCNTUnderAEWrongRCN4'))
	suite.addTest(TestDiscovery('test_discoverCNTUnderAEWrongRCN5'))
	suite.addTest(TestDiscovery('test_discoverCNTUnderAEWrongRCN8'))
	suite.addTest(TestDiscovery('test_discoverCNTUnderAEWrongRCN9'))
	suite.addTest(TestDiscovery('test_retrieveCNTUnderAERCN6'))
	suite.addTest(TestDiscovery('test_retrieveCNTUnderAERCN1'))
	suite.addTest(TestDiscovery('test_retrieveCNTUnderAERCN4'))
	suite.addTest(TestDiscovery('test_retrieveCNTUnderAERCN5'))
	suite.addTest(TestDiscovery('test_retrieveCNTUnderAERCN8'))
	suite.addTest(TestDiscovery('test_retrieveCNTUnderAEWrongRCN9'))
	suite.addTest(TestDiscovery('test_retrieveCNTUnderAEWrongRCN11'))
	suite.addTest(TestDiscovery('test_retrieveCNTUnderCSE'))
	suite.addTest(TestDiscovery('test_retrieveCINUnderAE'))
	suite.addTest(TestDiscovery('test_retrieveCINByLBLUnderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNTByCNIUnderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNTByCNIUnderAEEmpty'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures)


if __name__ == '__main__':
	_, errors = run()
	sys.exit(errors)
