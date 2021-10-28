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
from typing import Tuple
from acme.etc.Types import ResultContentType as RCN
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from acme.etc.Types import DesiredIdentifierResultType, FilterOperation
from acme.etc.DateUtils import getResourceDate
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
		cls.crTimestamp1 = getResourceDate(-timeDelta)	# first timestamp

		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : True,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		# create first container & CIN
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN,
					'lbl' : [ 'cntLbl' ]
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
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
		assert rsc == RC.created, 'cannot create container'
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
		assert rsc == RC.created, 'cannot create Node'
		dct =  { 'm2m:mem' : {
			'mgd' : T.MEM,
			'rn' : memRN,
			'dc' : 'aMem',
			'mma' : 1234,
			'mmt' : 4321
		}}
		_, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		assert rsc == RC.created, 'cannot create m2m:mem'
		dct =  { 'm2m:bat' : {
					'mgd' : T.BAT,
					'rn'  : batRN,
					'dc'  : 'aBat',
					'btl' : 23,
					'bts' : 5
				}}
		_, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		assert rsc == RC.created, 'cannot create m2m:bat'
		dct =  { 'm2m:bat' : {
			'mgd' : T.BAT,
			'rn'  : bat2RN,
			'dc'  : 'aBat',
			'btl' : 23,
			'bts' : 5
		}}
		_, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		assert rsc == RC.created, 'cannot create m2m:bat (2)'

		cls.crTimestamp2 = getResourceDate()	# Second timestamp


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveUnknownResource(self) -> None:
		""" Retrieve unknown resource -> Fail """
		# Before first timestamp
		r, rsc = RETRIEVE(f'{aeURL}_unknown', TestDiscovery.originator)
		self.assertEqual(rsc, RC.notFound, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverUnknownResource(self) -> None:
		""" Discover unknown resource -> Not found"""
		# Before first timestamp
		r, rsc = RETRIEVE(f'{aeURL}_unknown?fu=1', TestDiscovery.originator)
		self.assertEqual(rsc, RC.notFound, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverUnknownAttribute(self) -> None:
		""" Discover with unknown attribute -> Fail"""
		# Before first timestamp
		r, rsc = RETRIEVE(f'{aeURL}?xxx=yyy', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNIwithWrongSZB(self) -> None:
		"""	Retrieve with wrong SZB -> Fail """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResourceReferences)}&szb=-1', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest)


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
		self.assertEqual(rsc, RC.badRequest)


	# attributesAndChildResources (fail for discovery)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN4(self) -> None:
		""" Discover <CNT> under <AE> & wrong rcn=4 -> Fail """
		_, rsc = RETRIEVE(f'{aeURL}?fu=1&rcn={int(RCN.attributesAndChildResources)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest)


	# attributesAndChildResourceReferences (fail for discovery)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN5(self) -> None:
		""" Discover <CNT> under <AE> & wrong rcn=5 -> Fail """
		_, rsc = RETRIEVE(f'{aeURL}?fu=1&rcn={int(RCN.attributesAndChildResourceReferences)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest)


	# childResources
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN8(self) -> None:
		""" Discover <CNT> under <AE> & wrong rcn=8 -> Fail """
		_, rsc = RETRIEVE(f'{aeURL}?fu=1&rcn={int(RCN.childResources)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest)


	# modifiedAttributes (fail for retrieve)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_discoverCNTunderAEWrongRCN9(self) -> None:
		""" Discover <CNT> under <AE> & wrong rcn=9 -> Fail """
		_, rsc = RETRIEVE(f'{aeURL}?u=1&rcn={int(RCN.modifiedAttributes)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest)


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
		self.assertEqual(rsc, RC.badRequest)


	# discoveryResultReferences (fail for retrieve)
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTunderAEWrongRCN11(self) -> None:
		""" Retrieve <CNT> under <AE> & wrong rcn=11 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.discoveryResultReferences)}&ty={int(T.CNT)}', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest)


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
		self.assertEqual(rsc, RC.badRequest)

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
		self.assertEqual(rsc, RC.created)
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.childResources)}&ty={int(T.CNT)}&lbl=cntLbl&arp=arpCnt', TestDiscovery.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:ae/m2m:cnt/{0}/rn'), cntARPRN)
		_, rsc = DELETE(f'{cntURL}/arpCnt', TestDiscovery.originator) # cleanup
		self.assertEqual(rsc, RC.deleted)


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
		self.assertEqual(rsc, RC.created)
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
		self.assertEqual(rsc, RC.updated)
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
		self.assertEqual(rsc, RC.badRequest)


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
		self.assertEqual(rsc, RC.created)
		self.assertIsNone(r)
		# self.assertEqual(len(r), 0, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithWrongArgument(self) -> None:
		""" Retrieve <AE> with wrong argument & rcn=1 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributes)}&wrong=wrong', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithWrongFU(self) -> None:
		""" Retrieve <AE> with wrong fu & rcn=1 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributes)}&fu=4223', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithWrongDRT(self) -> None:
		""" Retrieve <AE> with wrong drt & rcn=1 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributes)}&drt=4223', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWithWrongFO(self) -> None:
		""" Retrieve <AE> with wrong fo & rcn=1 """
		_, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.attributes)}&fo=4223', TestDiscovery.originator)
		self.assertEqual(rsc, RC.badRequest)


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



def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
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
	suite.addTest(TestDiscovery('test_retrieveCNTorCINunderAE2'))
	suite.addTest(TestDiscovery('test_retrieveCINandLBLunderAE'))
	suite.addTest(TestDiscovery('test_retrieveCINandLBLunderAE2'))
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
	suite.addTest(TestDiscovery('test_createCNTwithRCN0'))
	suite.addTest(TestDiscovery('test_updateCNTwithWrongRCN2'))
	suite.addTest(TestDiscovery('test_retrieveWithWrongArgument'))
	suite.addTest(TestDiscovery('test_retrieveWithWrongFU'))
	suite.addTest(TestDiscovery('test_retrieveWithWrongDRT'))
	suite.addTest(TestDiscovery('test_retrieveWithWrongFO'))
	suite.addTest(TestDiscovery('test_retrieveMgmtObjsRCN8'))
	suite.addTest(TestDiscovery('test_retrieveCINmatchLabel'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
