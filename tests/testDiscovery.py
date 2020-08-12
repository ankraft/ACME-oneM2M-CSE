#
#	testDiscovery.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for discovery requests
#
#	==> rcn = original-resource is tested in testRemote_Annc.py
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

cnt2RN = '%s2' % cntRN
cnt3RN = '%s3' % cntRN
cntARPRN = 'arpCnt'

class TestDiscovery(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		cls.crTimestamp1 = getDate()	# first timestamp

		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == C.rcOK, 'Cannot retrieve CSEBase: %s' % cseURL

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
					'lbl' : [ 'cntLbl' ]
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

		cls.crTimestamp2 = getDate()	# Second timestamp


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnknownResource(self):
		# Before first timestamp
		r, rsc = RETRIEVE('%s_unknown' % aeURL, TestDiscovery.originator)
		self.assertEqual(rsc, C.rcNotFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverUnknownResource(self):
		# Before first timestamp
		r, rsc = RETRIEVE('%s_unknown?fu=1' % aeURL, TestDiscovery.originator)
		self.assertEqual(rsc, C.rcNotFound)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverUnknownAttribute(self):
		# Before first timestamp
		r, rsc = RETRIEVE('%s?xxx=yyy' % aeURL, TestDiscovery.originator)
		self.assertEqual(rsc, C.rcBadRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithWrongSZB(self):
		r, rsc = RETRIEVE('%s?rcn=%d&szb=-1' % (aeURL, C.rcnChildResourceReferences), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcBadRequest)


	# rcnChildResourceReferences
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAERCN6(self):
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
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoveryCNTunderAERCN11(self):
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
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN1(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d&ty=%d' % (aeURL, C.rcnAttributes, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcBadRequest)


	# rcnAttributesAndChildResources (fail for discovery)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN4(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d&ty=%d' % (aeURL, C.rcnAttributesAndChildResources, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcBadRequest)


	# rcnAttributesAndChildResourceReferences (fail for discovery)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN5(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d&ty=%d' % (aeURL, C.rcnAttributesAndChildResourceReferences, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcBadRequest)


	# rcnChildResources
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN8(self):
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d&ty=%d' % (aeURL, C.rcnChildResources, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcBadRequest)


	# rcnModifiedAttributes (fail for retrieve)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN9(self):
		r, rsc = RETRIEVE('%s?u=1&rcn=%d&ty=%d' % (aeURL, C.rcnModifiedAttributes, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcBadRequest)


	# rcnChildResourceReferences
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAERCN6(self):
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
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAERCN1(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnAttributes, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertEqual(findXPath(r, 'm2m:ae/rn'), aeRN)


	# rcnAttributesAndChildResources
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAERCN4(self):
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
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAERCN5(self):
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
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAERCN8(self):
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
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAEWrongRCN9(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnModifiedAttributes, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcBadRequest)


	# rcnDiscoveryResultReferences (fail for retrieve)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAEWrongRCN11(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnDiscoveryResultReferences, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcBadRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderCSE(self):
		r, rsc = RETRIEVE('%s?rcn=%s&ty=%d' % (cseURL, C.rcnChildResources, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:cb'))
		self.assertIsNotNone(findXPath(r, 'm2m:cb/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:cb/m2m:cnt')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:cb/m2m:cnt/{0}/rn'), findXPath(r, 'm2m:cb/m2m:cnt/{1}/rn'))
		self.assertIn(findXPath(r, 'm2m:cb/m2m:cnt/{0}/rn'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:cb/m2m:cnt/{1}/rn'), (cntRN, cnt2RN))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINunderAE(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d' % (aeURL, C.rcnChildResources, T.CIN), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cin')), 10)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINbyLBLunderAE(self):
		r, rsc = RETRIEVE('%s?rcn=%d&lbl=tag:0' % (aeURL, C.rcnChildResources), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cin')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:ae/m2m:cin/{0}/rn'), findXPath(r, 'm2m:ae/m2m:cin/{1}/rn'))
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cin/{0}/lbl/{0}'), 'tag:0')
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cin/{1}/lbl/{0}'), 'tag:0')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTbyCNIunderAE(self):
		r, rsc = RETRIEVE('%s?rcn=%d&cni=5' % (aeURL, C.rcnChildResources), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/cni'), 5)
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cnt/{1}/cni'), 5)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTbyCNIunderAEEmpty(self):
		r, rsc = RETRIEVE('%s?rcn=%d&cni=10' % (aeURL, C.rcnChildResources), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'))


	# same as above but with references
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTbyCNIunderAEEmpty2(self):
		r, rsc = RETRIEVE('%s?rcn=%d&cni=10' % (aeURL, C.rcnChildResourceReferences), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTorCINunderAE(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d&ty=%d' % (aeURL, C.rcnChildResourceReferences, T.CNT, T.CIN), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 12)
		self.assertEqual(sum(x['typ'] == T.CNT for x in findXPath(r, 'm2m:rrl')), 2)
		self.assertEqual(sum(x['typ'] == T.CIN for x in findXPath(r, 'm2m:rrl')), 10)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINandLBLunderAE(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d&lbl=tag:0' % (aeURL, C.rcnChildResourceReferences, T.CIN), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 2)
		self.assertEqual(sum(x['typ'] == T.CNT for x in findXPath(r, 'm2m:rrl')), 0)
		self.assertEqual(sum(x['typ'] == T.CIN for x in findXPath(r, 'm2m:rrl')), 2)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTorLBLunderAE(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d&lbl=tag:0&fo=%d' % (aeURL, C.rcnChildResourceReferences, T.CNT, C.foOR), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 4)
		self.assertEqual(sum(x['typ'] == T.CNT for x in findXPath(r, 'm2m:rrl')), 2)
		self.assertEqual(sum(x['typ'] == T.CIN for x in findXPath(r, 'm2m:rrl')), 2)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithCRBunderAE(self):
		# Before first timestamp
		r, rsc = RETRIEVE('%s?rcn=%d&crb=%s' % (aeURL, C.rcnChildResourceReferences, TestDiscovery.crTimestamp1), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 0)

		# Before second timestamp
		r, rsc = RETRIEVE('%s?rcn=%d&crb=%s' % (aeURL, C.rcnChildResourceReferences, TestDiscovery.crTimestamp2), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertGreater(len(findXPath(r, 'm2m:rrl')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithCRAunderAE(self):
		# Before first timestamp
		r, rsc = RETRIEVE('%s?rcn=%d&cty=a' % (aeURL, C.rcnChildResourceReferences), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertGreater(len(findXPath(r, 'm2m:rrl')), 0)

		# Before second timestamp
		r, rsc = RETRIEVE('%s?rcn=%d&cra=%s' % (aeURL, C.rcnChildResourceReferences, TestDiscovery.crTimestamp2), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithCTYunderAE(self):
		r, rsc = RETRIEVE('%s?rcn=%d&cty=a' % (aeURL, C.rcnChildResourceReferences), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 5)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithSZBunderAE(self):
		r, rsc = RETRIEVE('%s?rcn=%d&szb=100' % (aeURL, C.rcnChildResourceReferences), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 10)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithSZAunderAE(self):
		r, rsc = RETRIEVE('%s?rcn=%d&sza=3' % (aeURL, C.rcnChildResourceReferences), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 10)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithMSunderAE(self):
		# After first timestamp
		r, rsc = RETRIEVE('%s?rcn=%d&ms=%s' % (aeURL, C.rcnChildResourceReferences, TestDiscovery.crTimestamp1), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertGreater(len(findXPath(r, 'm2m:rrl')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithUSunderAE(self):
		# After first timestamp
		r, rsc = RETRIEVE('%s?rcn=%d&us=%s' % (aeURL, C.rcnChildResourceReferences, TestDiscovery.crTimestamp1), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 0)

		# After second timestamp
		r, rsc = RETRIEVE('%s?rcn=%d&us=%s' % (aeURL, C.rcnChildResourceReferences, TestDiscovery.crTimestamp2), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertGreater(len(findXPath(r, 'm2m:rrl')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithEXBunderAE(self):
		# Before first timestamp
		r, rsc = RETRIEVE('%s?rcn=%d&exb=%s' % (aeURL, C.rcnChildResourceReferences, TestDiscovery.crTimestamp1), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithEXAunderAE(self):
		# After first timestamp
		r, rsc = RETRIEVE('%s?rcn=%d&exa=%s' % (aeURL, C.rcnChildResourceReferences, TestDiscovery.crTimestamp1), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertGreater(len(findXPath(r, 'm2m:rrl')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAEStructured(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d&drt=%d' % (aeURL, C.rcnChildResourceReferences, T.CNT, C.drtStructured), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 2)
		cnt1 = '/%s/%s' % (aeRN, cntRN)
		cnt2 = '/%s/%s' % (aeRN, cnt2RN)
		self.assertTrue(findXPath(r, 'm2m:rrl/{0}/val').endswith(cnt1) or findXPath(r, 'm2m:rrl/{0}/val').endswith(cnt2))
		self.assertTrue(findXPath(r, 'm2m:rrl/{1}/val').endswith(cnt1) or findXPath(r, 'm2m:rrl/{1}/val').endswith(cnt2))

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAEUnstructured(self):
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d&drt=%d' % (aeURL, C.rcnChildResourceReferences, T.CNT, C.drtUnstructured), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl')), 2)
		cnt1 = '/%s/%s' % (aeRN, cntRN)
		cnt2 = '/%s/%s' % (aeRN, cnt2RN)
		self.assertFalse(findXPath(r, 'm2m:rrl/{0}/val').endswith(cnt1) or findXPath(r, 'm2m:rrl/{0}/val').endswith(cnt2))
		self.assertFalse(findXPath(r, 'm2m:rrl/{1}/val').endswith(cnt1) or findXPath(r, 'm2m:rrl/{1}/val').endswith(cnt2))


	# rcnAttributesAndChildResources (fail for discovery)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_rcn4WithDifferentFUs(self):
		# No FU
		r, rsc = RETRIEVE('%s?rcn=%d' % (aeURL, C.rcnAttributesAndChildResources), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(len(r), 1)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt')), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{0}/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt/{0}/m2m:cin')), 5)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{1}/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt/{1}/m2m:cin')), 5)

		# Fu=1
		r, rsc = RETRIEVE('%s?fu=1&rcn=%d' % (aeURL, C.rcnAttributesAndChildResources), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcBadRequest)

		# FU=2
		r, rsc = RETRIEVE('%s?fu=2&rcn=%d' % (aeURL, C.rcnAttributesAndChildResources), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(len(r), 1)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt')), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{0}/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt/{0}/m2m:cin')), 5)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{1}/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt/{1}/m2m:cin')), 5)


	# Test adding arp
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_appendArp(self):
		# create container under cnt1
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntARPRN,
				}}
		arpCnt, rsc = CREATE(cntURL, TestDiscovery.originator, T.CNT, jsn)
		self.assertEqual(rsc, C.rcCreated)
		r, rsc = RETRIEVE('%s?rcn=%d&ty=%d&lbl=cntLbl&arp=arpCnt' % (aeURL, C.rcnChildResources, T.CNT), TestDiscovery.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), cntARPRN)
		_, rsc = DELETE('%s/arpCnt' % cntURL, TestDiscovery.originator) # cleanup
		self.assertEqual(rsc, C.rcDeleted)


	# Test CREATE and RCN=9 (modifiedAttributes)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithRCN9(self):
		# create another container
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cnt3RN,
					'mni' : 42,
					'lbl' : [ 'test' ]
				}}
		r, rsc = CREATE('%s?rcn=%d' % (aeURL, C.rcnModifiedAttributes), TestDiscovery.originator, T.CNT, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNone(findXPath(r, 'm2m:cnt/mni'))
		self.assertIsNone(findXPath(r, 'm2m:cnt/lbl'))


	# Test UPDATE and RCN=9 (modifiedAttributes)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTwithRCN9(self):
		# create another container
		jsn = 	{ 'm2m:cnt' : { 
					'mni' : 23,
					'lbl' : [ 'test' ]
				}}
		r, rsc = UPDATE('%s/%s?rcn=%d' % (aeURL, cnt3RN, C.rcnModifiedAttributes), TestDiscovery.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/mni'))
		self.assertEqual(findXPath(r, 'm2m:cnt/mni'), 23)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/lbl'))
		self.assertEqual(findXPath(r, 'm2m:cnt/lbl'), [ 'test' ])
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/st'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/lt'))




def run():
	suite = unittest.TestSuite()
	suite.addTest(TestDiscovery('test_retrieveUnknownResource'))
	suite.addTest(TestDiscovery('test_discoverUnknownResource'))
	suite.addTest(TestDiscovery('test_discoverUnknownAttribute'))
	suite.addTest(TestDiscovery('test_retrieveCNIwithWrongSZB'))
	suite.addTest(TestDiscovery('test_discoverCNTunderAERCN6'))
	suite.addTest(TestDiscovery('test_discoveryCNTunderAERCN11'))
	suite.addTest(TestDiscovery('test_discoverCNTunderAEWrongRCN1'))
	suite.addTest(TestDiscovery('test_discoverCNTunderAEWrongRCN4'))
	suite.addTest(TestDiscovery('test_discoverCNTunderAEWrongRCN5'))
	suite.addTest(TestDiscovery('test_discoverCNTunderAEWrongRCN8'))
	suite.addTest(TestDiscovery('test_discoverCNTunderAEWrongRCN9'))
	suite.addTest(TestDiscovery('test_retrieveCNTunderAERCN6'))
	suite.addTest(TestDiscovery('test_retrieveCNTunderAERCN1'))
	suite.addTest(TestDiscovery('test_retrieveCNTunderAERCN4'))
	suite.addTest(TestDiscovery('test_retrieveCNTunderAERCN5'))
	suite.addTest(TestDiscovery('test_retrieveCNTunderAERCN8'))
	suite.addTest(TestDiscovery('test_retrieveCNTunderAEWrongRCN9'))
	suite.addTest(TestDiscovery('test_retrieveCNTunderAEWrongRCN11'))
	suite.addTest(TestDiscovery('test_retrieveCNTunderCSE'))
	suite.addTest(TestDiscovery('test_retrieveCINunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCINbyLBLunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNTbyCNIunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNTbyCNIunderAEEmpty'))
	suite.addTest(TestDiscovery('test_retrieveCNTbyCNIunderAEEmpty2'))
	suite.addTest(TestDiscovery('test_retrieveCNTorCINunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCINandLBLunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNTorLBLunderAE'))
	suite.addTest(TestDiscovery('test_retrieveWithCRBunderAE'))
	suite.addTest(TestDiscovery('test_retrieveWithCRAunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNIwithCTYunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNIwithSZBunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNIwithSZAunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNIwithMSunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNIwithUSunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNIwithEXBunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNIwithEXAunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCNTunderAEStructured'))
	suite.addTest(TestDiscovery('test_retrieveCNTunderAEUnstructured'))
	suite.addTest(TestDiscovery('test_rcn4WithDifferentFUs'))
	suite.addTest(TestDiscovery('test_appendArp'))
	suite.addTest(TestDiscovery('test_createCNTwithRCN9'))
	suite.addTest(TestDiscovery('test_updateCNTwithRCN9'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
