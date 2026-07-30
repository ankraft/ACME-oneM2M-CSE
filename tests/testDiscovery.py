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
if '..' not in sys.path:
	sys.path.append('..')
from acmecse.etc.Types import ResultContentType as RCN
from acmecse.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from acmecse.etc.Types import DesiredIdentifierResultType, FilterOperation
from acmecse.etc.DateUtils import getResourceDate
from init import *


cnt2RN = f'{cntRN}2' 
cnt3RN = f'{cntRN}3'
cnt4RN = f'{cntRN}4'
cntARPRN = 'arpCnt'
bat2RN	= f'{batRN}2'
nodeID  = 'urn:sn:1234'


class TestDiscovery(unittest.TestCase):

	ae 				= None
	cnt 			= None
	cnt2 			= None
	originator 		= None
	crTimestamp1	= None
	crTimestamp2	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestDiscovery')
		cls.crTimestamp1 = getResourceDate(-timeDelta)	# first timestamp

		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		# create first container & CIN
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'lbl' : [ 'cntLbl' ]
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		# create 5 contentInstances with different labels
		for i in range(0,5):
			dct = 	{ 'm2m:cin' : {
						'cnf' : 'text/plain:0',
						'con' : 'aValue',
						'lbl' : [ 'tag:%d' %i ]
					}}
			_, rsc = CREATE(cntURL, TestDiscovery.originator, T.CIN, dct)

		# create second container & CIN
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cnt2RN,
				}}
		cls.cnt2, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		# create 5 contentInstances with different labels
		for i in range(0,5):
			dct = 	{ 'm2m:cin' : {
						'cnf' : 'text/x-plain:0',
						'con' : 'bValue',
						'lbl' : [ 'tag:%d' %i ]
					}}
			_, rsc = CREATE(f'{cntURL}2', TestDiscovery.originator, T.CIN, dct)
		
		# create Node & MgmtObjs
		dct = 	{ 'm2m:nod' : { 
			'rn' 	: nodRN,
			'ni'	: nodeID
		}}
		_, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, dct)
		assert rsc == RC.CREATED, 'cannot create Node'
		dct =  { 'm2m:mem' : {
			'mgd' : T.MEM,
			'rn' : memRN,
			'dc' : 'aMem',
			'mma' : 1234,
			'mmt' : 4321
		}}
		_, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		assert rsc == RC.CREATED, 'cannot create m2m:mem'
		dct =  { 'm2m:bat' : {
					'mgd' : T.BAT,
					'rn'  : batRN,
					'dc'  : 'aBat',
					'btl' : 23,
					'bts' : 5
				}}
		_, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		assert rsc == RC.CREATED, 'cannot create m2m:bat'
		dct =  { 'm2m:bat' : {
			'mgd' : T.BAT,
			'rn'  : bat2RN,
			'dc'  : 'aBat',
			'btl' : 23,
			'bts' : 5
		}}
		_, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		assert rsc == RC.CREATED, 'cannot create m2m:bat (2)'

		cls.crTimestamp2 = getResourceDate()	# Second timestamp
		testCaseEnd('Setup TestDiscovery')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestDiscovery')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestDiscovery')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnknownResource(self) -> None:
		""" Retrieve unknown resource -> Fail """
		# Before first timestamp
		r, rsc = RETRIEVE(f'{aeURL}_unknown', TestDiscovery.originator)
		self.assertEqual(rsc, RC.NOT_FOUND, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverUnknownResource(self) -> None:
		""" Discover unknown resource -> Not found"""
		# Before first timestamp
		r, rsc = RETRIEVE(f'{aeURL}_unknown?fu=1', TestDiscovery.originator)
		self.assertEqual(rsc, RC.NOT_FOUND, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverUnknownAttribute(self) -> None:
		""" Discover with unknown attribute -> Fail"""
		# Before first timestamp
		r, rsc = RETRIEVE(f'{aeURL}?xxx=yyy', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithWrongSZB(self) -> None:
		"""	Retrieve with wrong SZB -> Fail """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&szb=-1', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	# childResourceReferences
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAERCN6(self) -> None:
		"""	Discover <CNT> under <AE> & rcn=6 """
		r, rsc = RETRIEVE(f'{aeURL}?fu=1&rcn={int(RCN.childResourceReferences)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:rrl/rrf/{0}/nm'), findXPath(r, 'm2m:rrl/rrf/{1}/nm'))
		self.assertIn(findXPath(r, 'm2m:rrl/rrf/{0}/nm'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:rrl/rrf/{1}/nm'), (cntRN, cnt2RN))
		self.assertEqual(findXPath(r, 'm2m:rrl/rrf/{0}/typ'), 3)
		self.assertEqual(findXPath(r, 'm2m:rrl/rrf/{1}/typ'), 3)
		self.assertNotEqual(findXPath(r, 'm2m:rrl/rrf/{0}/val'), findXPath(r, 'm2m:rrl/rrf/{1}/val'))
		self.assertIn(findXPath(r, 'm2m:rrl/rrf/{0}/val').split('/')[-1], (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:rrl/rrf/{1}/val').split('/')[-1], (cntRN, cnt2RN))


	#discoveryResultReferences
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoveryCNTunderAERCN11(self) -> None:
		""" Discover <CNT> under <AE> & rcn=11 """
		r, rsc = RETRIEVE(f'{aeURL}?fu=1&rcn={int(RCN.discoveryResultReferences)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:uril'))
		self.assertEqual(len(findXPath(r, 'm2m:uril')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:uril/{0}'), findXPath(r, 'm2m:uril/{1}'))
		self.assertGreater(len(findXPath(r, 'm2m:uril/{0}').split('/')), 2)
		self.assertGreater(len(findXPath(r, 'm2m:uril/{1}').split('/')), 2)
		self.assertIn(findXPath(r, 'm2m:uril/{0}').split('/')[-1], (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:uril/{1}').split('/')[-1], (cntRN, cnt2RN))


	# attributes (fail fail for discovery)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN1(self) -> None:
		""" Discover <CNT> under <AE> & wrong rcn=1 -> Fail """
		_, rsc = RETRIEVE(f'{aeURL}?fu=1&rcn={int(RCN.attributes)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	# attributesAndChildResources (fail for discovery)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN4(self) -> None:
		""" Discover <CNT> under <AE> & wrong rcn=4 -> Fail """
		_, rsc = RETRIEVE(f'{aeURL}?fu=1&rcn={int(RCN.attributesAndChildResources)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	# attributesAndChildResourceReferences (fail for discovery)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN5(self) -> None:
		""" Discover <CNT> under <AE> & wrong rcn=5 -> Fail """
		_, rsc = RETRIEVE(f'{aeURL}?fu=1&rcn={int(RCN.attributesAndChildResourceReferences)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	# childResources
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN8(self) -> None:
		""" Discover <CNT> under <AE> & wrong rcn=8 -> Fail """
		_, rsc = RETRIEVE(f'{aeURL}?fu=1&rcn={int(RCN.childResources)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	# modifiedAttributes (fail for retrieve)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN9(self) -> None:
		""" Discover <CNT> under <AE> & wrong rcn=9 -> Fail """
		_, rsc = RETRIEVE(f'{aeURL}?u=1&rcn={int(RCN.modifiedAttributes)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	# childResourceReferences
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAERCN6(self) -> None:
		""" Retrive <CNT> under <AE> & rcn=6 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:rrl/rrf/{0}/nm'), findXPath(r, 'm2m:rrl/rrf/{1}/nm'))
		self.assertIn(findXPath(r, 'm2m:rrl/rrf/{0}/nm'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:rrl/rrf/{1}/nm'), (cntRN, cnt2RN))
		self.assertEqual(findXPath(r, 'm2m:rrl/rrf/{0}/typ'), 3)
		self.assertEqual(findXPath(r, 'm2m:rrl/rrf/{1}/typ'), 3)
		self.assertNotEqual(findXPath(r, 'm2m:rrl/rrf/{0}/val'), findXPath(r, 'm2m:rrl/rrf/{1}/val'))
		self.assertIn(findXPath(r, 'm2m:rrl/rrf/{0}/val').split('/')[-1], (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:rrl/rrf/{1}/val').split('/')[-1], (cntRN, cnt2RN))


	# attributes
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAERCN1(self) -> None:
		""" Retrieve <CNT> under <AE> & rcn=1 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributes)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'), r)
		self.assertEqual(findXPath(r, 'm2m:ae/rn'), aeRN)


	# attributesAndChildResources
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAERCN4(self) -> None:
		""" Retrieve <CNT> under <AE> & rcn=4 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributesAndChildResources)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertEqual(findXPath(r, 'm2m:ae/rn'), aeRN)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt')), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertNotEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertIn(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'), (cntRN, cnt2RN))


	# attributesAndChildResourceReferences
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAERCN5(self) -> None:
		""" Retrieve <CNT> under <AE> & rcn=5 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributesAndChildResourceReferences)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertEqual(findXPath(r, 'm2m:ae/rn'), aeRN)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/ch'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/ch')), 2, r)
		self.assertNotEqual(findXPath(r, 'm2m:ae/ch/{0}/nm'), findXPath(r, 'm2m:ae/ch/{1}/nm'))
		self.assertIn(findXPath(r, 'm2m:ae/ch/{0}/nm'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:ae/ch/{1}/nm'), (cntRN, cnt2RN))
		self.assertEqual(findXPath(r, 'm2m:ae/ch/{0}/typ'), 3)
		self.assertEqual(findXPath(r, 'm2m:ae/ch/{1}/typ'), 3)
		self.assertNotEqual(findXPath(r, 'm2m:ae/ch/{0}/val'), findXPath(r, 'm2m:ae/ch/{1}/val'))
		self.assertIn(findXPath(r, 'm2m:ae/ch/{0}/val').split('/')[-1], (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:ae/ch/{1}/val').split('/')[-1], (cntRN, cnt2RN))


	# childResources
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAERCN8(self) -> None:
		""" Retrieve <CNT> under <AE> & rcn=8 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResources)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNone(findXPath(r, 'm2m:ae/rn'), aeRN) # don't find other AE attributes
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt')), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertNotEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertIn(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'), (cntRN, cnt2RN))


	# modifiedAttributes (fail for retrieve)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAEWrongRCN9(self) -> None:
		""" Retrieve <CNT> under <AE> & wrong rcn=9 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.modifiedAttributes)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	# discoveryResultReferences (fail for retrieve)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAEWrongRCN11(self) -> None:
		""" Retrieve <CNT> under <AE> & wrong rcn=11 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.discoveryResultReferences)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderCSE(self) -> None:
		""" Retrieve <CNT> under <CSE> & rcn=8 """
		r, rsc = RETRIEVE(f'{cseURL}?rcn={int(RCN.childResources)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cb'))
		self.assertIsNotNone(findXPath(r, 'm2m:cb/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:cb/m2m:cnt')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:cb/m2m:cnt/{0}/rn'), findXPath(r, 'm2m:cb/m2m:cnt/{1}/rn'))
		self.assertIn(findXPath(r, 'm2m:cb/m2m:cnt/{0}/rn'), (cntRN, cnt2RN))
		self.assertIn(findXPath(r, 'm2m:cb/m2m:cnt/{1}/rn'), (cntRN, cnt2RN))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINunderAE(self) -> None:
		""" Retrieve <CIN> under <AE> & rcn=8 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResources)}&ty={int(T.CIN)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cin'), r)
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cin')), 10)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINbyLBLunderAE(self) -> None:
		""" Retrieve <CIN> under <AE> by lbl & rcn=8 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResources)}&lbl=tag:0', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cin')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:ae/m2m:cin/{0}/rn'), findXPath(r, 'm2m:ae/m2m:cin/{1}/rn'))
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cin/{0}/lbl/{0}'), 'tag:0')
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cin/{1}/lbl/{0}'), 'tag:0')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTbyCNIunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> by correct cni & rcn=8 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResources)}&cni=5', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt')), 2)
		self.assertNotEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), findXPath(r, 'm2m:ae/m2m:cnt/{1}/rn'))
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/cni'), 5)
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cnt/{1}/cni'), 5)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTbyCNIunderAEEmpty(self) -> None:
		""" Retrieve <CNT> under <AE> by false cni & rcn=8 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResources)}&cni=10', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'), r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'))


	# same as above but with references
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTbyCNIunderAEEmpty2(self) -> None:
		""" Retrieve <CNT> under <AE> by false cni & rcn=6 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&cni=10', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTorCINunderAE(self) -> None:
		""" Retrieve <CNT> or <CIN> under <AE> & rcn=6 & '+' operator """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&ty={int(T.CNT)}+{int(T.CIN)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 12)
		self.assertEqual(sum(x['typ'] == T.CNT for x in findXPath(r, 'm2m:rrl/rrf')), 2)
		self.assertEqual(sum(x['typ'] == T.CIN for x in findXPath(r, 'm2m:rrl/rrf')), 10)


	# This one tests a different argument handling (2 * ty)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTorCINunderAE2(self) -> None:
		"""	Retrieve <CNT> or <CIN> under <AE>2 & rcn=6 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&ty={int(T.CNT)}&ty={int(T.CIN)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 12, r)
		self.assertEqual(sum(x['typ'] == T.CNT for x in findXPath(r, 'm2m:rrl/rrf')), 2)
		self.assertEqual(sum(x['typ'] == T.CIN for x in findXPath(r, 'm2m:rrl/rrf')), 10)

	
	# Find both CIN with a tag:0 label
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINandLBLunderAE(self) -> None:
		""" Retrieve <CIN> under <AE> by lbl & rcn=6 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&ty={int(T.CIN)}&lbl=tag:0', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 2)
		self.assertEqual(sum(x['typ'] == T.CNT for x in findXPath(r, 'm2m:rrl/rrf')), 0)
		self.assertEqual(sum(x['typ'] == T.CIN for x in findXPath(r, 'm2m:rrl/rrf')), 2)


	# Find four CIN with a tag:0 or tag:1 label. Use + encoding for the label
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINandLBLunderAE2(self) -> None:
		""" Retrieve <CIN> under <AE> by multiple lbl & rcn=6 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&ty={int(T.CIN)}&lbl=tag:0+tag:1', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 4)
		self.assertEqual(sum(x['typ'] == T.CNT for x in findXPath(r, 'm2m:rrl/rrf')), 0)
		self.assertEqual(sum(x['typ'] == T.CIN for x in findXPath(r, 'm2m:rrl/rrf')), 4)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTorLBLunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> by label or type & rcn=6 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&ty={int(T.CNT)}&lbl=tag:0&fo={int(FilterOperation.OR)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 4)
		self.assertEqual(sum(x['typ'] == T.CNT for x in findXPath(r, 'm2m:rrl/rrf')), 2)
		self.assertEqual(sum(x['typ'] == T.CIN for x in findXPath(r, 'm2m:rrl/rrf')), 2)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithCRBunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> by crb & rcn=6 """
		# Before first timestamp
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&crb={TestDiscovery.crTimestamp1}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 0)

		# Before second timestamp
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&crb={TestDiscovery.crTimestamp2}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertGreater(len(findXPath(r, 'm2m:rrl/rrf')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithCRAunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> by cra & rcn=6 """
		# Before first timestamp
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&cra={TestDiscovery.crTimestamp1}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertGreater(len(findXPath(r, 'm2m:rrl/rrf')), 0)

		# Before second timestamp
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&cra={TestDiscovery.crTimestamp2}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithCTYunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> with cty=text/plain:0 & rcn=6 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&cty=text/plain:0', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 5, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithSZBunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> with szb & rcn=6 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&szb=100', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 10)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithSZAunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> with sza & rcn=6 """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&sza=3', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 10)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithMSunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> with ms & rcn=6 """
		# After first timestamp
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&ms={TestDiscovery.crTimestamp1}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertGreater(len(findXPath(r, 'm2m:rrl/rrf')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithUSunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> with us & rcn=6 """
		# After first timestamp
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&us={TestDiscovery.crTimestamp1}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 0)

		# After second timestamp
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&us={TestDiscovery.crTimestamp2}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertGreater(len(findXPath(r, 'm2m:rrl/rrf')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithEXBunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> with exb & rcn=6 """
		# Before first timestamp
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&exb={TestDiscovery.crTimestamp1}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithEXAunderAE(self) -> None:
		""" Retrieve <CNT> under <AE> with exa & rcn=6 """
		# After first timestamp
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&exa={TestDiscovery.crTimestamp1}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertGreater(len(findXPath(r, 'm2m:rrl/rrf')), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAEStructured(self) -> None:
		""" Retrieve <CNT> under <AE> & rcn=6 & structured """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&ty={int(T.CNT)}&drt={int(DesiredIdentifierResultType.structured)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 2, r)
		cnt1 = f'/{aeRN}/{cntRN}'
		cnt2 = f'/{aeRN}/{cnt2RN}'
		self.assertTrue(findXPath(r, 'm2m:rrl/rrf/{0}/val').endswith(cnt1) or findXPath(r, 'm2m:rrl/rrf/{0}/val').endswith(cnt2))
		self.assertTrue(findXPath(r, 'm2m:rrl/rrf/{1}/val').endswith(cnt1) or findXPath(r, 'm2m:rrl/rrf/{1}/val').endswith(cnt2))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAEUnstructured(self) -> None:
		""" Retrieve <CNT> under <AE> & rcn=6 & unstructured """
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&ty={int(T.CNT)}&drt={int(DesiredIdentifierResultType.unstructured)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 2)
		cnt1 = f'/{aeRN}/{cntRN}'
		cnt2 = f'/{aeRN}/{cnt2RN}'
		self.assertFalse(findXPath(r, 'm2m:rrl/rrf/{0}/val').endswith(cnt1) or findXPath(r, 'm2m:rrl/rrf/{0}/val').endswith(cnt2))
		self.assertFalse(findXPath(r, 'm2m:rrl/rrf/{1}/val').endswith(cnt1) or findXPath(r, 'm2m:rrl/rrf/{1}/val').endswith(cnt2))


	# rcnAttributesAndChildResources (fail for discovery)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_rcn4WithDifferentFUs(self) -> None:
		""" Retrieve all resources under <AE> & rcn=4 & various fu """
		# No FU
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributesAndChildResources)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(len(r), 1)
		self.assertIsNotNone(findXPath(r, 'm2m:ae'))
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt')), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{0}/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt/{0}/m2m:cin')), 5)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt/{1}/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:ae/m2m:cnt/{1}/m2m:cin')), 5)

		# Fu=1
		r, rsc = RETRIEVE(f'{aeURL}?fu=1&rcn={int(RCN.attributesAndChildResources)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)

		# FU=2
		r, rsc = RETRIEVE(f'{aeURL}?fu=2&rcn={int(RCN.attributesAndChildResources)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
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
	def test_appendArp(self) -> None:
		""" Append arp to result """
		# create container under cnt1
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntARPRN,
				}}
		_, rsc = CREATE(cntURL, TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResources)}&ty={int(T.CNT)}&lbl=cntLbl&arp=arpCnt', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), cntARPRN)
		_, rsc = DELETE(f'{cntURL}/arpCnt', TestDiscovery.originator) # cleanup
		self.assertEqual(rsc, RC.DELETED)


	# Test CREATE and RCN=9 (modifiedAttributes)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithRCN9(self) -> None:
		""" Create <CNT> under <AE> & rcn=9 """
		# create another container
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cnt3RN,
					'mni' : 42,
					'lbl' : [ 'test' ]
				}}
		r, rsc = CREATE(f'{aeURL}?rcn={int(RCN.modifiedAttributes)}', TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNone(findXPath(r, 'm2m:cnt/mni'))
		self.assertIsNone(findXPath(r, 'm2m:cnt/lbl'))
		# test only some attributes the should be in the reply
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/st'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/ri'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/lt'))


	# Test UPDATE and RCN=9 (modifiedAttributes)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTwithRCN9(self) -> None:
		""" Update <CNT> & rcn=9 """
		# create another container
		dct = 	{ 'm2m:cnt' : { 
					'mni' : 23,
					'lbl' : [ 'test' ]
				}}
		r, rsc = UPDATE(f'{aeURL}/{cnt3RN}?rcn={int(RCN.modifiedAttributes)}', TestDiscovery.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNone(findXPath(r, 'm2m:cnt/mni'), r)
		self.assertIsNone(findXPath(r, 'm2m:cnt/lbl'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/st'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/lt'))


	# Test UPDATE and RCN=9 (modifiedAttributes)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTwithWrongRCN2(self) -> None:
		""" Update <CNT> & rcn=2 -> Fail """
		# create another container
		dct = 	{ 'm2m:cnt' : { 
					'mni' : 23,
					'lbl' : [ 'test2' ]
				}}
		_, rsc = UPDATE(f'{aeURL}/{cnt3RN}?rcn={int(RCN.hierarchicalAddress)}', TestDiscovery.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	# Test CREATE and RCN=0 (nothing)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithRCN0(self) -> None:
		""" Create <CNT> under <AE> & rcn=0 (nothing) """
		# create another container
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cnt4RN,
					'mni' : 42,
					'lbl' : [ 'test' ]
				}}
		r, rsc = CREATE(f'{aeURL}?rcn={int(RCN.nothing)}', TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNone(r)
		# self.assertEqual(len(r), 0, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithWrongArgument(self) -> None:
		""" Retrieve <AE> with wrong argument & rcn=1 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributes)}&wrong=wrong', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithWrongFU(self) -> None:
		""" Retrieve <AE> with wrong fu & rcn=1 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributes)}&fu=4223', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithWrongDRT(self) -> None:
		""" Retrieve <AE> with wrong drt & rcn=1 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributes)}&drt=4223', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithWrongFO(self) -> None:
		""" Retrieve <AE> with wrong fo & rcn=1 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributes)}&fo=4223', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveMgmtObjsRCN8(self) -> None:
		""" Retrieve <mgmtObj> under <NOD> & rcn=8 """
		r, rsc = RETRIEVE(f'{nodURL}?rcn={int(RCN.childResources)}&ty={int(T.MGMTOBJ)}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		# Excpected: m2m:bat and m2m:mem are separate fields
		self.assertIsNotNone(findXPath(r, 'm2m:nod'))
		self.assertIsNotNone(findXPath(r, 'm2m:nod/m2m:bat'))
		self.assertEqual(len(findXPath(r, 'm2m:nod/m2m:bat')), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/m2m:mem'))
		self.assertEqual(len(findXPath(r, 'm2m:nod/m2m:mem')), 1)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINmatchLabel(self) -> None:
		""" Retrieve <CIN> under <AE> by CON (match wildcard) """
		r, rsc = RETRIEVE(f'{cntURL}?rcn={int(RCN.childResources)}&con=a*', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/m2m:cin'))
		self.assertEqual(len(findXPath(r, 'm2m:cnt/m2m:cin')), 5)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithRCN2(self) -> None:
		""" Create <CNT> with rcn=2"""
		# create another container
		dct:JSON = 	{ 'm2m:cnt' : { 
				}}
		r, rsc = CREATE(f'{aeURL}?rcn={int(RCN.hierarchicalAddress)}', TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:uri'))
		if BINDING in ['http', 'https']:
			self.assertIn('Content-Location', lastHeaders())
			self.assertEqual(lastHeaders()['Content-Location'], findXPath(r, 'm2m:uri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTwithRCN3(self) -> None:
		""" Create <CNT> with rcn=3"""
		# create another container
		dct:JSON = 	{ 'm2m:cnt' : { 
				}}
		r, rsc = CREATE(f'{aeURL}?rcn={int(RCN.hierarchicalAddressAttributes)}', TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:rce'))
		self.assertIsNotNone(findXPath(r, 'm2m:rce/uri'))
		if BINDING in ['http', 'https']:
			self.assertIn('Content-Location', lastHeaders())
			self.assertEqual(lastHeaders()['Content-Location'], findXPath(r, 'm2m:rce/uri'))


	#
	#	Retrieve empty childResource sets
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnderCNTRCN8(self) -> None:
		""" Retrieve everything under <CNT> & rcn=8 """

		# create <CNT>
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}rcn8',
				}}
		r, rsc = CREATE(aeURL, TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)

		# retrieve <CNT> with rcn=8
		r, rsc = RETRIEVE(f'{cntURL}rcn8?rcn={int(RCN.childResources)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt'))
		self.assertEqual(len(findXPath(r, 'm2m:cnt')), 0)

		# cleanup
		_, rsc = DELETE(f'{cntURL}rcn8', TestDiscovery.originator) # cleanup
		self.assertEqual(rsc, RC.DELETED)


	# childResourceReferences
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnderCNTRCN6(self) -> None:
		""" RETRIEVE everything under <CNT> & rcn=6. Also DELETE with rcn=6 """

		# create <CNT>
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}rcn6',
				}}
		r, rsc = CREATE(aeURL, TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)

		# retrieve <CNT> with rcn=6
		r, rsc = RETRIEVE(f'{cntURL}rcn6?rcn={int(RCN.childResourceReferences)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 0, r)

		# cleanup
		r, rsc = DELETE(f'{cntURL}rcn6?rcn={RCN.childResourceReferences.value}', TestDiscovery.originator) # cleanup
		self.assertEqual(rsc, RC.DELETED)
		self.assertIsNotNone(findXPath(r, 'm2m:rrl'))
		self.assertIsNotNone(findXPath(r, 'm2m:rrl/rrf'))
		self.assertEqual(len(findXPath(r, 'm2m:rrl/rrf')), 0, r)


	# attributesAndChildResourceReferences
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnderCNTRCN5(self) -> None:
		""" Retrieve everything under <CNT> & rcn=5 """

		# create <CNT>
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}rcn5',
				}}
		r, rsc = CREATE(aeURL, TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)

		# retrieve <CNT> with rcn=5
		r, rsc = RETRIEVE(f'{cntURL}rcn5?rcn={int(RCN.attributesAndChildResourceReferences)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt'))
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/ch'))
		self.assertEqual(len(findXPath(r, 'm2m:cnt/ch')), 0, r)

		# cleanup
		_, rsc = DELETE(f'{cntURL}rcn5', TestDiscovery.originator) # cleanup
		self.assertEqual(rsc, RC.DELETED)


#
# Persmission tests
#
		
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTwithRCN12Fail(self) -> None:
		""" Update <CNT> with rcn=12 -> Fail """

		# create <CNT>
		dct:JSON = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}rcn12'
				}}
		r, rsc = CREATE(aeURL, TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)

		# update <CNT> with rcn=12
		dct = 	{ 'm2m:cnt' : { 
					'lbl'  : [ 'test' ]
				}}

		r, rsc = UPDATE(f'{cntURL}rcn12?rcn={int(RCN.permissions)}', TestDiscovery.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)

		# cleanup
		_, rsc = DELETE(f'{cntURL}rcn12', TestDiscovery.originator) # cleanup
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTwithRCN12(self) -> None:
		""" Retrieve <CNT> with rcn=12 """

		# create <CNT>
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}rcn12'
				}}
		r, rsc = CREATE(aeURL, TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)

		# create sub <CNT>
		dct = 	{ 'm2m:cnt' : {
					'rn'  : f'{cnt2RN}rcn12-2'
				}}
		r, rsc = CREATE(f'{cntURL}rcn12', TestDiscovery.originator, T.CNT, dct)
		
		# retrieve <CNT> with rcn=12
		r, rsc = RETRIEVE(f'{cntURL}rcn12?rcn={int(RCN.permissions)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)

		# cleanup
		_, rsc = DELETE(f'{cntURL}rcn12', TestDiscovery.originator) # cleanup
		self.assertEqual(rsc, RC.DELETED)


#
#	ContentFilterQuery tests
#

	# A helper function to create <CIN> under <CNT> with different JSON as content for the 
	# following ContentFilterQuery tests
	def _createCINsForCFQ(self) -> None:
		""" Create <CIN> under <CNT> with different JSON as content """

		# create <CNT>
		dct:JSON = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}cfq'
				}}
		r, rsc = CREATE(aeURL, TestDiscovery.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# create <CIN> resources with different JSON as content

		dct = 	{ 'm2m:cin' : { 
					'rn'  : f'{cinRN}cfq-1',
					'cnf' : 'application/json:0',
					'con' : { 'temperature' : 22, 'humidity' : 50 }
				}}
		r, rsc = CREATE(f'{cntURL}cfq', TestDiscovery.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		dct = 	{ 'm2m:cin' : { 
					'rn'  : f'{cinRN}cfq-2',
					'cnf' : 'application/json:0',
					'con' : { 'temperature' : 25, 'humidity' : 60 }
				}}
		r, rsc = CREATE(f'{cntURL}cfq', TestDiscovery.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# one CIN without cnf attribute
		dct = 	{ 'm2m:cin' : { 
					'rn'  : f'{cinRN}cfq-99',
					'con' : { 'temperature' : 25, 'humidity' : 60 }
				}}
		r, rsc = CREATE(f'{cntURL}cfq', TestDiscovery.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# one CIN without complex cnf attribute
		dct = 	{ 'm2m:cin' : { 
					'rn'  : f'{cinRN}cfq-200',
					'cnf' : 'application/json:0',
					'con' : {
						'sensorType': 'temperature',
						'value': 21.5,
						'unit': 'C',
						'tags': ['outdoor', 'balcony'],
						'readings': [
							{'ts': '20260101T000000', 'v': 21.0},
							{'ts': '20260101T000100', 'v': 21.5},
							{'ts': '20260101T000200', 'v': 22.0},
						],
						'meta': {
							'id': 12345,
							'device.id': 'esp32-01',   	# name containing a dot - requires quoting
							'battery%': 87,            	# name containing a special char per spec list? '%' not listed, no quoting needed
						},
						'status': 'OK',
						'warnings': 'no warnings',
						'message': 'hello "world"',  	# string containing quotes - requires quoting
						'sym': '\u00b0C', 				# string containing a unicode character - requires quoting
						'note': 'AND',					# string containing a reserved word - requires quoting
					}
				}}
		r, rsc = CREATE(f'{cntURL}cfq', TestDiscovery.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	def _cleanupCINsForCFQ(self) -> None:
		""" Cleanup <CIN> under <CNT> with different JSON as content """

		# cleanup
		_, rsc = DELETE(f'{cntURL}cfq', TestDiscovery.originator) # cleanup
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithCFQWrongCFSFail(self) -> None:
		""" Retrieve <CIN> under <CNT> with ContentFilterQuery and wrong CFS-> Fail """

		self._createCINsForCFQ()

		# Retrieve <CNT> with ContentFilterQuery
		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.temperature GT 23&cfs=2', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value EQ', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value EQ 1 AND', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value FOO 1', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=notapath EQ 1', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		# Cleanup
		self._cleanupCINsForCFQ()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithCFQOnlyCFSFail(self) -> None:
		""" Retrieve <CIN> under <CNT> with ContentFilterQuery with only CFS -> Fail """

		self._createCINsForCFQ()

		# Retrieve <CNT> with ContentFilterQuery
		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfs=1', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		# Cleanup
		self._cleanupCINsForCFQ()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithCFQWrongCFQFail(self) -> None:
		""" Retrieve <CIN> under <CNT> with wrong ContentFilterQuery -> Fail """

		self._createCINsForCFQ()

		# Retrieve <CNT> with ContentFilterQuery
		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=wrong query', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		# Cleanup
		self._cleanupCINsForCFQ()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithCFQUnknownKeyFail(self) -> None:
		""" Retrieve <CIN> under <CNT> with ContentFilterQuery with unknown key -> Fail """

		self._createCINsForCFQ()

		# Retrieve <CNT> with ContentFilterQuery
		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.unknownKey GT 23', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:cnt/m2m:cin'), r)

		# Cleanup
		self._cleanupCINsForCFQ()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithCFQsimple(self) -> None:
		""" Retrieve <CIN> under <CNT> with ContentFilterQuery """

		self._createCINsForCFQ()

		# Retrieve <CNT> with ContentFilterQuery
		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.temperature GT 23', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/m2m:cin'), r)
		self.assertEqual(len(findXPath(r, 'm2m:cnt/m2m:cin')), 1, r)
		self.assertEqual(findXPath(r, 'm2m:cnt/m2m:cin/{0}/rn'), f'{cinRN}cfq-2', r)

		# Cleanup
		self._cleanupCINsForCFQ()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithCFQsingleClauseKeyword(self) -> None:
		""" Retrieve <CIN> under <CNT> with ContentFilterQuery - single clause with keyword """

		def _assert(r:JSON, rsc:int, ln:int = 1) -> None:
			self.assertEqual(rsc, RC.OK, r)
			if ln == 0:
				self.assertIsNone(findXPath(r, 'm2m:cnt/m2m:cin'), r)
				return
			self.assertIsNotNone(findXPath(r, 'm2m:cnt/m2m:cin'), r)
			self.assertEqual(len(findXPath(r, 'm2m:cnt/m2m:cin')), 1, r)
			self.assertEqual(findXPath(r, 'm2m:cnt/m2m:cin/{0}/rn'), f'{cinRN}cfq-200', r)


		self._createCINsForCFQ()

		# Retrieve <CNT> with various ContentFilterQuery
		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.status EQ "OK"', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.status EQ "FAIL"', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value EQ 21.5', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value EQ "21.5"', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.status NE "FAIL"', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.status NE "OK"', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value GT 20', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value GT 21.5', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value LT 22', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value LT 21.5', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value GE 21.5', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value GE 21.6', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value LE 21.5', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value LE 21.4', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.sensorType MATCH "temp"', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.sensorType MATCH "humidity"', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.sensorType MATCH "TEMP"', TestDiscovery.originator)
		_assert(r, rsc, 0)	# case sensitive -> no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.status GT 5', TestDiscovery.originator)
		_assert(r, rsc, 0)	# comparing a string field numerically -> no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.readings[1].v EQ 21.5', TestDiscovery.originator)
		_assert(r, rsc)	# nested path clause

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.meta.\'device.id\' EQ "esp32-01"', TestDiscovery.originator)
		_assert(r, rsc)	# path NAME uses single quotes, string VALUE uses double quotes

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.warnings EQ "no warnings"', TestDiscovery.originator)
		_assert(r, rsc) # string containing a space - requires quoting

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.warnings MATCH "no warnings"', TestDiscovery.originator)
		_assert(r, rsc) # string containing a space - requires quoting

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.message EQ "hello \\"world\\""', TestDiscovery.originator)
		_assert(r, rsc) # string containing quotes - requires quoting

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.sym EQ "\\u00b0C"', TestDiscovery.originator)
		_assert(r, rsc) # string containing a unicode character - requires quoting

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.note EQ "AND"', TestDiscovery.originator)
		_assert(r, rsc) # string containing a reserved word - requires quoting

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.x EQ "bad\\escape"', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r) # string containing a bad escape 

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.x EQ "unterminated', TestDiscovery.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r) # string containing an unterminated quote 

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.nope EQ "x"', TestDiscovery.originator)
		_assert(r, rsc, 0) # absent field - no match, but no error

		# Cleanup
		self._cleanupCINsForCFQ()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithCFQpathClause(self) -> None:
		""" Retrieve <CIN> under <CNT> with ContentFilterQuery - single clause with path """

		def _assert(r:JSON, rsc:int, ln:int = 1) -> None:
			self.assertEqual(rsc, RC.OK, r)
			if ln == 0:
				self.assertIsNone(findXPath(r, 'm2m:cnt/m2m:cin'), r)
				return
			self.assertIsNotNone(findXPath(r, 'm2m:cnt/m2m:cin'), r)
			self.assertEqual(len(findXPath(r, 'm2m:cnt/m2m:cin')), 1, r)
			self.assertEqual(findXPath(r, 'm2m:cnt/m2m:cin/{0}/rn'), f'{cinRN}cfq-200', r)

		self._createCINsForCFQ()

		# Retrieve <CNT> with various ContentFilterQuery
		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.meta.id EQ 12345', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.tags[0] EQ "outdoor"', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.meta.\'device.id\' EQ "esp32-01"', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.tags[99] EQ "indoor"', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match for tags[99]

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.value[0] EQ "indoor"', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match for non-list

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.tags.foo EQ "indoor"', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match for non-existing path

		# Cleanup
		self._cleanupCINsForCFQ()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCINwithCFQcombinedClause(self) -> None:
		""" Retrieve <CIN> under <CNT> with ContentFilterQuery - combined clause """

		def _assert(r:JSON, rsc:int, ln:int = 1) -> None:
			self.assertEqual(rsc, RC.OK, r)
			if ln == 0:
				self.assertIsNone(findXPath(r, 'm2m:cnt/m2m:cin'), r)
				return
			self.assertIsNotNone(findXPath(r, 'm2m:cnt/m2m:cin'), r)
			self.assertEqual(len(findXPath(r, 'm2m:cnt/m2m:cin')), 1, r)
			self.assertEqual(findXPath(r, 'm2m:cnt/m2m:cin/{0}/rn'), f'{cinRN}cfq-200', r)

		self._createCINsForCFQ()

		# Retrieve <CNT> with various ContentFilterQuery
		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.status EQ "OK" AND $.value GT 20', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.status EQ "OK" AND $.value GT 100', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.status EQ "FAIL" OR $.value GT 20', TestDiscovery.originator)
		_assert(r, rsc)

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.status EQ "FAIL" OR $.value GT 100', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		r, rsc = RETRIEVE(f'{cntURL}cfq?rcn={int(RCN.childResources)}&cfq=$.status EQ "FAIL" OR $.value GT 20 AND $.sensorType MATCH "humidity"', TestDiscovery.originator)
		_assert(r, rsc, 0)	# no match

		# Cleanup
		self._cleanupCINsForCFQ()


def run(testFailFast:bool) -> TestResult:

		# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestDiscovery, [
		
		'test_retrieveUnknownResource',
		'test_discoverUnknownResource',
		'test_discoverUnknownAttribute',
		'test_retrieveCNIwithWrongSZB',
		'test_discoverCNTunderAERCN6',
		'test_discoveryCNTunderAERCN11',
		'test_discoverCNTunderAEWrongRCN1',
		'test_discoverCNTunderAEWrongRCN4',
		'test_discoverCNTunderAEWrongRCN5',
		'test_discoverCNTunderAEWrongRCN8',
		'test_discoverCNTunderAEWrongRCN9',
		'test_retrieveCNTunderAERCN6',
		'test_retrieveCNTunderAERCN1',
		'test_retrieveCNTunderAERCN4',
		'test_retrieveCNTunderAERCN5',
		'test_retrieveCNTunderAERCN8',
		'test_retrieveCNTunderAEWrongRCN9',
		'test_retrieveCNTunderAEWrongRCN11',
		'test_retrieveCNTunderCSE',
		'test_retrieveCINunderAE',
		'test_retrieveCINbyLBLunderAE',
		'test_retrieveCNTbyCNIunderAE',
		'test_retrieveCNTbyCNIunderAEEmpty',
		'test_retrieveCNTbyCNIunderAEEmpty2',
		'test_retrieveCNTorCINunderAE',
		'test_retrieveCNTorCINunderAE2',
		'test_retrieveCINandLBLunderAE',
		'test_retrieveCINandLBLunderAE2',
		'test_retrieveCNTorLBLunderAE',
		'test_retrieveWithCRBunderAE',
		'test_retrieveWithCRAunderAE',
		'test_retrieveCNIwithCTYunderAE',
		'test_retrieveCNIwithSZBunderAE',
		'test_retrieveCNIwithSZAunderAE',
		'test_retrieveCNIwithMSunderAE',
		'test_retrieveCNIwithUSunderAE',
		'test_retrieveCNIwithEXBunderAE',
		'test_retrieveCNIwithEXAunderAE',
		'test_retrieveCNTunderAEStructured',
		'test_retrieveCNTunderAEUnstructured',
		'test_rcn4WithDifferentFUs',
		'test_appendArp',
		'test_createCNTwithRCN9',
		'test_updateCNTwithRCN9',
		'test_createCNTwithRCN0',
		'test_updateCNTwithWrongRCN2',
		'test_retrieveWithWrongArgument',
		'test_retrieveWithWrongFU',
		'test_retrieveWithWrongDRT',
		'test_retrieveWithWrongFO',
		'test_retrieveMgmtObjsRCN8',
		'test_retrieveCINmatchLabel',
		'test_createCNTwithRCN2',
		'test_createCNTwithRCN3',

		# Retrieve under CNT and expect empty results
		'test_retrieveUnderCNTRCN8',
		'test_retrieveUnderCNTRCN6',
		'test_retrieveUnderCNTRCN5',

		# Retrieve Permissions
		'test_updateCNTwithRCN12Fail',
		# TODO 'test_retrieveCNTwithRCN12'

		# ContentFilterQuery tests
		'test_retrieveCINwithCFQWrongCFSFail',
		'test_retrieveCINwithCFQOnlyCFSFail',
		'test_retrieveCINwithCFQWrongCFQFail',
		'test_retrieveCINwithCFQUnknownKeyFail',
		'test_retrieveCINwithCFQsimple',
		'test_retrieveCINwithCFQsingleClauseKeyword',
		'test_retrieveCINwithCFQpathClause',
		'test_retrieveCINwithCFQcombinedClause',

	])

	# Run tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
