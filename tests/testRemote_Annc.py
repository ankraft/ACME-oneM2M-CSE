#
#	testRemote_Annc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Announcementfunctionality to a remote CSE. Tests are
#	skipped if there is no remote CSE.
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import AnnounceSyncType, ResultContentType as RCN
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *


class TestRemote_Annc(unittest.TestCase):

	acpORIGINATOR 	= 'testOriginator'
	ae				= None
	node 			= None
	bat 			= None
	acp 			= None
	cnt 			= None
	remoteCse 		= None
	remoteCbARI 	= None
	remoteAeRI		= None
	remoteCntRI		= None
	remoteNodRI		= None
	remoteBatRI 	= None
	remoteAcpRI 	= None


	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def setUpClass(cls) -> None:
		# check connection to CSE's
		testCaseStart('Setup TestRemote_Annc')
		cls.remoteCse, rsc = RETRIEVE(REMOTEcseURL, REMOTEORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve remote CSEBase: {REMOTEcseURL}'
		testCaseEnd('Setup TestRemote_Annc')


	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestRemote_Annc')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not
		DELETE(acpURL, ORIGINATOR)	# Just delete the ACP 
		DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)		# Delete the extra container
		testCaseEnd('TearDown TestRemote_Annc')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	#
	#	create an announced AE, but no extra attributes
	#

	# Create an AE with AT, but no AA
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnounceAEwithATwithoutAA(self) -> None:
		""" Create and announce <AE> (AT, no AA) """
		dct = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	APPID,
				 	'rr': 	False,
				 	'srv': 	[ RELEASEVERSION ],
				 	'at': 	[ REMOTECSEID ]
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/at'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:ae/at')), 1)
		self.assertTrue(findXPath(r, 'm2m:ae/at/{0}').startswith(f'{REMOTECSEID}/'), r)
		TestRemote_Annc.remoteAeRI = findXPath(r, 'm2m:ae/at')[0]
		self.assertIsNotNone(self.remoteAeRI)
		self.assertIsNone(findXPath(r, 'm2m:ae/aa'))
		TestRemote_Annc.ae = r


	# Retrieve the announced AE with AT, but no AA
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedAEwithATwithoutAA(self) -> None:
		""" Retrieve announced <AE> from remote (AT, no AA) """
		if TestRemote_Annc.remoteAeRI is None:
			self.skipTest('remote AE.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}{TestRemote_Annc.remoteAeRI}', CSEID)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:aeA'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/ty'))
		self.assertEqual(findXPath(r, 'm2m:aeA/ty'), T.AEAnnc)
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/pi'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lnk'))
		self.assertTrue(findXPath(r, 'm2m:aeA/lnk').endswith( findXPath(TestRemote_Annc.ae, 'm2m:ae/ri') ))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/srv'))	# MA attribute
		self.assertEqual(findXPath(r, 'm2m:aeA/srv'), [ RELEASEVERSION ])
		self.assertIsNotNone(pi := findXPath(r, 'm2m:aeA/pi'))
		TestRemote_Annc.remoteCbARI = pi


	# Retrieve the CSEBaseAnnc
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveCSEBaseAnnc(self) -> None:
		""" Retrieve CSEBaseAnnc """
		r, rsc = RETRIEVE(f'{REMOTECSEURL}{TestRemote_Annc.remoteCbARI}', CSEID)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cbA'))
		self.assertIsNotNone(findXPath(r, 'm2m:cbA/lnk'))
		self.assertIsNotNone(findXPath(r, 'm2m:cbA/srv'))
		self.assertIsNotNone(findXPath(r, 'm2m:cbA/ri'))
		self.assertEqual(findXPath(r, 'm2m:cbA/ty'), T.CSEBaseAnnc)


	# Delete the AE with AT, but no AA
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_deleteAnnounceAE(self) -> None:
		""" Delete announced <AE> """
		if TestRemote_Annc.remoteAeRI is None:
			self.skipTest('remote AE.ri not found')
		_, rsc = DELETE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)
		# try to retrieve the announced AE. Should not be found
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteAeRI}', CSEID)
		self.assertEqual(rsc, RC.NOT_FOUND)
		TestRemote_Annc.ae = None


	#
	#	create an announced AE, including announced attribute
	#

	#
	#	Perhaps the following three (fail) tests should be moved to somewhere else
	#	But using the "aa" attribute seems to be the easiest way to test the
	#	"ncname" validation.
	#

	# Create an AE with AT and AA, but wrong char in attribute
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnounceAEwithATwithWrongAA1Fail(self) -> None:
		""" Create and announce <AE> (AT, AA) with wrong char in attribute -> Fail """
		dct = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	APPID,
				 	'rr': 	False,
				 	'srv': 	[ RELEASEVERSION ],
				 	'lbl':	[ 'aLabel'],
				 	'at': 	[ REMOTECSEID ],
				 	'aa': 	[ 'lbl', 'lb+l']	# wrong attribute
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	# Create an AE with AT and AA, but space in attribute
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnounceAEwithATwithWrongAA2Fail(self) -> None:
		""" Create and announce <AE> (AT, AA) with space in attribute -> Fail """
		dct = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	APPID,
				 	'rr': 	False,
				 	'srv': 	[ RELEASEVERSION ],
				 	'lbl':	[ 'aLabel'],
				 	'at': 	[ REMOTECSEID ],
				 	'aa': 	[ 'lbl', 'lb l']	# wrong attribute
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	# Create an AE with AT and AA, but leading digit in attribute
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnounceAEwithATwithWrongAA3Fail(self) -> None:
		""" Create and announce <AE> (AT, AA) with space in attribute -> Fail """
		dct = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	APPID,
				 	'rr': 	False,
				 	'srv': 	[ RELEASEVERSION ],
				 	'lbl':	[ 'aLabel'],
				 	'at': 	[ REMOTECSEID ],
				 	'aa': 	[ 'lbl', '1lbl']	# wrong attribute
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	# Create an AE with AT and AA
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnounceAEwithATwithAA(self) -> None:
		""" Create and announce <AE> (AT, AA) """
		dct = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	APPID,
				 	'rr': 	False,
				 	'srv': 	[ RELEASEVERSION ],
				 	'lbl':	[ 'aLabel'],
				 	'at': 	[ REMOTECSEID ],
				 	'aa': 	[ 'lbl' ]
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lbl'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/lbl'), list)
		self.assertEqual(len(findXPath(r, 'm2m:ae/lbl')), 1)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/at'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:ae/at')), 1)
		self.assertIsInstance(findXPath(r, 'm2m:ae/aa'), list)
		self.assertEqual(len(findXPath(r, 'm2m:ae/aa')), 1)
		self.assertIn('lbl', findXPath(r, 'm2m:ae/aa'))
		self.assertTrue(findXPath(r, 'm2m:ae/at')[0].startswith(f'{REMOTECSEID}/'), r)
		TestRemote_Annc.remoteAeRI = findXPath(r, 'm2m:ae/at')[0]
		self.assertIsNotNone(self.remoteAeRI)
		TestRemote_Annc.ae = r


	# Retrieve the announced AE with AT and AA
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedAEwithATwithAA(self) -> None:
		"""	Retrieve announced <AE> from remote (AT, AA) """
		if TestRemote_Annc.remoteAeRI is None:
			self.skipTest('remote AE.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteAeRI}', CSEID)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:aeA'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/ty'))
		self.assertEqual(findXPath(r, 'm2m:aeA/ty'), T.AEAnnc)
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/pi'))
		self.assertEqual(findXPath(r, 'm2m:aeA/pi'), TestRemote_Annc.remoteCbARI)
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lnk'))
		self.assertTrue(findXPath(r, 'm2m:aeA/lnk').endswith( findXPath(TestRemote_Annc.ae, 'm2m:ae/ri') ))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lbl'))
		self.assertEqual(len(findXPath(r, 'm2m:aeA/lbl')), 1)
		self.assertIn('aLabel', findXPath(r, 'm2m:aeA/lbl'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/srv'))	# MA attribute
		self.assertEqual(findXPath(r, 'm2m:aeA/srv'), [ RELEASEVERSION ])



	# Update an non-AA AE with AA
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_addAAtoAnnounceAEwithoutAA(self) -> None:
		""" Add AA to <AE> with missing AA """
		dct = 	{ 'm2m:ae' : {
				 	'lbl':	[ 'aLabel'],
				 	'aa': 	[ 'lbl' ]
				}}
		r, rsc = UPDATE(aeURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lbl'))


	#
	#	create an announced AE, including NA announced attribute
	#

	# Create an AE with non-announceable attributes
	# AA should be corrected, null, but still present when rcn=modifiedAttributes
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnounceAEwithNAAttributes(self) -> None:
		""" Create <AE> with AA with NA attributes. AA shall be empty, but present in result """
		dct = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	APPID,
				 	'rr': 	False,
				 	'srv': 	[ RELEASEVERSION ],
				 	'at': 	[ REMOTECSEID ],
				 	'aa': 	[ 'rn', 'ri', 'pi', 'ct','lt','acpi' ]
				}}
		r, rsc = CREATE(f'{cseURL}?rcn={int(RCN.modifiedAttributes)}', 'C', T.AE, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/at'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:ae/at')), 1)
		self.assertTrue(findXPath(r, 'm2m:ae/at')[0].startswith(f'{REMOTECSEID}/'))
		TestRemote_Annc.remoteAeRI = findXPath(r, 'm2m:ae/at')[0]
		self.assertIsNotNone(self.remoteAeRI)

		# aa should be in the resource, but null
		self.assertIn('aa', findXPath(r, 'm2m:ae')) 
		self.assertIsNone(findXPath(r, 'm2m:ae/aa'), r)	# This must be None/Null!
		TestRemote_Annc.ae = r


	#
	#	create an announced AE, with non-resource announcedAttributes
	#

	# Create an AE with non-resource attributes
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnounceAEwithNonResourceAttributes(self) -> None:
		""" Create <AE> with AA with unknown resource attributes -> Fail"""
		dct = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	APPID,
				 	'rr': 	False,
				 	'srv': 	[ RELEASEVERSION ],
				 	'at': 	[ REMOTECSEID ],
				 	'aa': 	[ 'rn', 'ri', 'pi', 'ct', 'lt', 'acpi', 'st' ]
				}}
		r, rsc = CREATE(f'{cseURL}?rcn={int(RCN.modifiedAttributes)}', 'C', T.AE, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)



	# Update an non-AA AE with AA
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_addLBLtoAnnouncedAE(self) -> None:
		""" Add AA to <AE> without AA (Update) """
		dct = 	{ 'm2m:ae' : {
				 	'lbl':	[ 'aLabel']	# LBL is conditional announced, so no need for adding it to aa
				}}
		r, rsc = UPDATE(aeURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lbl'))
		self.assertEqual(findXPath(r, 'm2m:ae/lbl'), [ 'aLabel' ])

		# retrieve the announced AE
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteAeRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lbl'))
		self.assertEqual(findXPath(r, 'm2m:aeA/lbl'), [ 'aLabel' ])


	# Remove annouced attribute from original resource
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_removeLBLfromAnnouncedAE(self) -> None:
		""" Remove annouced attribute from original resource """
		dct = 	{ 'm2m:ae' : {
					'lbl': None
				}}
		r, rsc = UPDATE(aeURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNone(findXPath(r, 'm2m:ae/lbl'))

		# retrieve the announced AE
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteAeRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNone(findXPath(r, 'm2m:aeA/lbl'))


	#
	#	create an announced Node & MgmtObj [bat]
	#

	# Create a Node with AT
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnounceNode(self) -> None:
		""" Create announced <node> """
		dct = 	{ 'm2m:nod' : {
					'rn': 	nodRN, 
					'ni': 	'aNI', 
				 	'at': 	[ REMOTECSEID ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/at'))
		self.assertIsInstance(findXPath(r, 'm2m:nod/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:nod/at')), 1)
		self.assertTrue(findXPath(r, 'm2m:nod/at')[0].startswith(f'{REMOTECSEID}/'))
		TestRemote_Annc.remoteNodRI = findXPath(r, 'm2m:nod/at')[0]
		self.assertIsNotNone(self.remoteNodRI)
		self.assertIsNone(findXPath(r, 'm2m:nod/aa'))
		TestRemote_Annc.node = r


	# Retrieve the announced Node with AT
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedNode(self) -> None:
		""" Retrieve announced <node> """
		if TestRemote_Annc.remoteNodRI is None:
			self.skipTest('remote Node.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteNodRI}', CSEID)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:nodA'))
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/ty'))
		self.assertEqual(findXPath(r, 'm2m:nodA/ty'), T.NODAnnc)
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/pi'))
		self.assertEqual(findXPath(r, 'm2m:nodA/pi'), TestRemote_Annc.remoteCbARI)
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/lnk'))
		self.assertTrue(findXPath(r, 'm2m:nodA/lnk').endswith( findXPath(TestRemote_Annc.node, 'm2m:nod/ri') ))


	# Create a mgmtObj under the node
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_announceMgmtobj(self) -> None:
		""" Create announced <mgmtObj> [Battery] """
		dct = 	{ 'm2m:bat' : {
					'mgd' : T.BAT,
					'dc'  : 'battery',
					'rn'  : batRN,
					'btl' : 23,
					'bts' : 1,
				 	'at'  : [ REMOTECSEID ],
				 	'aa'  : [ 'btl']
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/at'))
		self.assertIsInstance(findXPath(r, 'm2m:bat/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:bat/at')), 1)
		self.assertEqual(findXPath(r, 'm2m:bat/btl'), 23)
		self.assertEqual(findXPath(r, 'm2m:bat/bts'), 1)
		self.assertTrue(findXPath(r, 'm2m:bat/at')[0].startswith(f'{REMOTECSEID}/'), r)
		TestRemote_Annc.remoteBatRI = findXPath(r, 'm2m:bat/at')[0]
		self.assertIsNotNone(TestRemote_Annc.remoteBatRI)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/aa'))
		self.assertEqual(len(findXPath(r, 'm2m:bat/aa')), 1)
		self.assertIn('btl', findXPath(r, 'm2m:bat/aa'))
		TestRemote_Annc.bat = r


	# Retrieve the announced mgmtobj 
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedMgmtobj(self) -> None:
		""" Retrieve announced [Battery] and test attributes """
		if TestRemote_Annc.remoteBatRI is None:
			self.skipTest('remote bat.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:batA'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:batA/ty'))
		self.assertEqual(findXPath(r, 'm2m:batA/ty'), T.MGMTOBJAnnc)
		self.assertIsNotNone(findXPath(r, 'm2m:batA/mgd'))
		self.assertEqual(findXPath(r, 'm2m:batA/mgd'), T.BAT)
		self.assertIsNotNone(findXPath(r, 'm2m:batA/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:batA/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:batA/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:batA/pi'))
		self.assertIsNotNone(findXPath(r, 'm2m:batA/lnk'))
		self.assertTrue(findXPath(r, 'm2m:batA/lnk').endswith( findXPath(TestRemote_Annc.bat, 'm2m:bat/ri') ))
		self.assertIsNotNone(findXPath(r, 'm2m:batA/btl'))
		self.assertEqual(findXPath(r, 'm2m:batA/btl'), 23)
		self.assertIsNone(findXPath(r, 'm2m:batA/bts'))
		self.assertTrue(TestRemote_Annc.remoteNodRI.endswith(findXPath(r, 'm2m:batA/pi')))


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveRCNOriginalResource(self) -> None:
		""" Retrieve original resource from remote CSE """
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}?rcn={int(RCN.originalResource)}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:bat'))
		self.assertIsNotNone(findXPath(r, 'm2m:bat/ty'))
		self.assertEqual(findXPath(r, 'm2m:bat/ty'), T.MGMTOBJ)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/mgd'))
		self.assertEqual(findXPath(r, 'm2m:bat/mgd'), T.BAT)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/aa'))
		self.assertIsNotNone(findXPath(r, 'm2m:bat/at'))


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveRCNOriginalResourceFail(self) -> None:
		""" Retrieve original resource for remote CSEBase -> Fail """
		r, rsc = RETRIEVE(f'{REMOTEcseURL}?rcn={int(RCN.originalResource)}', ORIGINATOR)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_deleteRCNOriginalResourceFail(self) -> None:
		""" Delete original resource from remote CSE -> Fail """
		r, rsc = DELETE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}?rcn={int(RCN.originalResource)}', ORIGINATOR)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_updateMgmtObjAttribute(self) -> None:
		"""	Update [Battery] """
		dct = 	{ 'm2m:bat' : {
					'btl' : 42,
					'bts' : 2
				}}
		r, rsc = UPDATE(batURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertEqual(findXPath(r, 'm2m:bat/btl'), 42)
		self.assertEqual(findXPath(r, 'm2m:bat/bts'), 2)
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:batA/btl'))
		self.assertEqual(findXPath(r, 'm2m:batA/btl'), 42)
		self.assertIsNone(findXPath(r, 'm2m:batA/bts'))


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_addMgmtObjAttribute(self) -> None:
		""" Announce new (mgmtObj) attributes for [Battery] """
		dct = 	{ 'm2m:bat' : {
					'aa' : [ 'btl', 'bts']
				}}
		r, rsc = UPDATE(batURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertEqual(findXPath(r, 'm2m:bat/btl'), 42)
		self.assertEqual(findXPath(r, 'm2m:bat/bts'), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/aa'))
		self.assertEqual(len(findXPath(r, 'm2m:bat/aa')), 2)
		self.assertIn('btl', findXPath(r, 'm2m:bat/aa'))
		self.assertIn('bts', findXPath(r, 'm2m:bat/aa'))

		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:batA/btl'))
		self.assertEqual(findXPath(r, 'm2m:batA/btl'), 42)
		self.assertIsNotNone(findXPath(r, 'm2m:batA/bts'))
		self.assertEqual(findXPath(r, 'm2m:batA/bts'), 2)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_removeMgmtObjAttribute(self) -> None:
		""" Unannounce(mgmtObj) attribute for [Battery] """
		dct = 	{ 'm2m:bat' : {
					'aa' : [ 'bts']
				}}
		r, rsc = UPDATE(batURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertEqual(findXPath(r, 'm2m:bat/btl'), 42)
		self.assertEqual(findXPath(r, 'm2m:bat/bts'), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/aa'))
		self.assertEqual(len(findXPath(r, 'm2m:bat/aa')), 1)
		self.assertNotIn('btl', findXPath(r, 'm2m:bat/aa'))
		self.assertIn('bts', findXPath(r, 'm2m:bat/aa'))

		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNone(findXPath(r, 'm2m:batA/btl'))
		self.assertIsNotNone(findXPath(r, 'm2m:batA/bts'))
		self.assertEqual(findXPath(r, 'm2m:batA/bts'), 2)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_removeMgmtObjAA(self) -> None:
		""" Unanounce all AA announced attributes for [Battery] """
		dct = 	{ 'm2m:bat' : {
					'aa' : None
				}}
		r, rsc = UPDATE(batURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertEqual(findXPath(r, 'm2m:bat/btl'), 42)
		self.assertEqual(findXPath(r, 'm2m:bat/bts'), 2)
		self.assertIsNone(findXPath(r, 'm2m:bat/aa'))

		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNone(findXPath(r, 'm2m:batA/btl'))
		self.assertIsNone(findXPath(r, 'm2m:batA/bts'))


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_removeMgmtObjCSIfromAT(self) -> None:
		""" Unanounce [Battery] (remove target CSI from AT) """
		dct = 	{ 'm2m:bat' : {
					'at' : None 			# remove attribute
				}}
		r, rsc = UPDATE(batURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNone(findXPath(r, 'm2m:bat/at'), r)

		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.NOT_FOUND)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_addMgmtObjCSItoAT(self) -> None:
		""" Announce [Battery] again to remote CSE (add target to AT) """
		dct = 	{ 'm2m:bat' : {
					'at' : [ REMOTECSEID ] 			# with REMOTECSEID added
				}}
		r, rsc = UPDATE(batURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertEqual(len(findXPath(r, 'm2m:bat/at')), 1)

		TestRemote_Annc.remoteBatRI = None
		for x in findXPath(r, 'm2m:bat/at'):
			if x == REMOTECSEID:
				continue
			if x.startswith(f'{REMOTECSEID}/'):
				TestRemote_Annc.remoteBatRI = x
		self.assertIsNotNone(self.remoteBatRI)
		TestRemote_Annc.bat = r

		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_removeMgmtObjAT(self) -> None:
		""" Remove At attribute from [Battery] (unanounce) """
		dct = 	{ 'm2m:bat' : {
					'at' : None 			# with at removed
				}}
		r, rsc = UPDATE(batURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNone(findXPath(r, 'm2m:bat/at'))

		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.NOT_FOUND)
		TestRemote_Annc.bat = None
		TestRemote_Annc.remoteBatRI = None


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_deleteAnnounceNode(self) -> None:
		""" Delete announced <node> """
		if TestRemote_Annc.node is None:
			self.skipTest('node not found')
		_, rsc = DELETE(nodURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)
		# try to retrieve the announced Node. Should not be found
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteNodRI}', CSEID)
		self.assertEqual(rsc, RC.NOT_FOUND)
		TestRemote_Annc.node = None
		TestRemote_Annc.remoteNodRI = None
		# Actually, the mgmtobj should been deleted by now in another test case
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteBatRI}', ORIGINATOR)
		self.assertEqual(rsc, RC.NOT_FOUND)
		TestRemote_Annc.bat = None
		TestRemote_Annc.remoteBatRI = None


	#
	#	create an announced ACP
	#

	# Create an ACP 
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnouncedACP(self) -> None:
		""" Create an announced <ACP> """
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ { 	"acor": [ ORIGINATOR ],
									"acop": 63
								} ]
					},
					"pvs": { 
						"acr": [ {
							"acor": [ self.acpORIGINATOR ],
							#"acor": [ 'all' ],
							"acop": 63
						} ]
					},
				 	'at': 	[ REMOTECSEID ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/at'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:acp/at')), 1)
		self.assertTrue(findXPath(r, 'm2m:acp/at')[0].startswith(f'{REMOTECSEID}/'))
		TestRemote_Annc.remoteAcpRI = findXPath(r, 'm2m:acp/at')[0]
		self.assertIsNotNone(self.remoteAcpRI)
		self.assertIsNone(findXPath(r, 'm2m:acp/aa'))
		TestRemote_Annc.acp = r


	# Retrieve the announced ACP
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedACP(self) -> None:
		""" Retrieve remote <ACPA> """
		if TestRemote_Annc.remoteAcpRI is None:
			self.skipTest('remote ACP.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteAcpRI}', 'other')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteAcpRI}', self.acpORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:acpA'))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/ty'))
		self.assertEqual(findXPath(r, 'm2m:acpA/ty'), T.ACPAnnc)
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/pi'))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/lnk'))
		self.assertTrue(findXPath(r, 'm2m:acpA/lnk').endswith( findXPath(TestRemote_Annc.acp, 'm2m:acp/ri') ))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/pv'))	# MA attribute
		self.assertIsInstance(findXPath(r, 'm2m:acpA/pv'), dict)
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/pvs'))	# MA attribute
		self.assertIsInstance(findXPath(r, 'm2m:acpA/pvs'), dict)


	# Retrieve the announced ACP with wrong originator
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedACPwithWrongOriginator(self) -> None:
		""" Retrieve remote <ACPA> with wrong originator """
		if TestRemote_Annc.remoteAcpRI is None:
			self.skipTest('remote ACP.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteAcpRI}', 'wrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	# Retrieve the announced ACP with the CSE-ID
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedACPwithCSI(self) -> None:
		""" Retrieve remote <ACPA> with remote CSE's CSI """
		if TestRemote_Annc.remoteAcpRI is None:
			self.skipTest('remote ACP.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteAcpRI}', CSEID)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_deleteAnnounceACP(self) -> None:
		""" Delete remote <ACPA> directly -> FAIL """
		if TestRemote_Annc.acp is None:
			self.skipTest('acp not found')
		_, rsc = DELETE(acpURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)
		# try to retrieve the announced Node. Should not be found
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteAcpRI}', CSEID)
		self.assertEqual(rsc, RC.NOT_FOUND)
		TestRemote_Annc.acp = None
		TestRemote_Annc.remoteAcpRI = None


	#
	#	create an announced CNT with announcedSyncType = bi-directional
	#

	# Create CNT with announcedSyncType
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnouncedCNTSynced(self) -> None:
		""" Create and announce <CNT> (synced) """
		dct = 	{ 'm2m:cnt' : {
					'rn': 	cntRN, 
					'lbl':	[ 'aLabel' ],
					'mni':	10,
				 	'at': 	[ REMOTECSEID ],
					'aa': 	[ 'mni' ],
					'ast':	AnnounceSyncType.BI_DIRECTIONAL
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/at'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:cnt/at')), 1)
		self.assertTrue(findXPath(r, 'm2m:cnt/at')[0].startswith(f'{REMOTECSEID}/'), r)
		TestRemote_Annc.remoteCntRI = findXPath(r, 'm2m:cnt/at')[0]
		self.assertIsNotNone(self.remoteCntRI)
		TestRemote_Annc.cnt = r


	# Update a remote CNT (synced)
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_updateRemoteCNT(self) -> None:
		""" Update remote CNT (synced) """
		if TestRemote_Annc.cnt is None:
			self.skipTest('cnt not found')
		dct = 	{ 'm2m:cnt' : {
				 	'lbl':	[ 'aLabel', 'bLabel'],
				 	'mni': 	20
				}}
		r, rsc = UPDATE(f'{cseURL}/{cntRN}', ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/lbl'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/lbl'), list)
		self.assertEqual(len(findXPath(r, 'm2m:cnt/lbl')), 2)
		self.assertEqual(findXPath(r, 'm2m:cnt/mni'), 20)


	# Delete CNT with announcedSyncType
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_deleteAnnouncedCNTSynced(self) -> None:
		""" Delete remote CNT (synced) """
		if TestRemote_Annc.cnt is None:
			self.skipTest('cnt not found')
		_, rsc = DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)
		# try to retrieve the announced CNT. Should not be found
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_Annc.remoteCntRI}', CSEID)
		self.assertEqual(rsc, RC.NOT_FOUND)
		TestRemote_Annc.cnt = None
		TestRemote_Annc.remoteCntRI = None


	#
	#	Announcement to hosting CSE
	#

	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_announceToHostingCSE(self) -> None:
		""" Announcement to own CSE """
		dct = 	{ 'm2m:cnt' : {
					'rn': 	cntRN, 
					'lbl':	[ 'aLabel' ],
					'mni':	10,
				 	'at': 	[ CSEID ],
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:cnt/at'))
		self.assertIsInstance(findXPath(r, 'm2m:cnt/at'), list)
		TestRemote_Annc.remoteCntRI = findXPath(r, 'm2m:cnt/at')[0]
		self.assertTrue(TestRemote_Annc.remoteCntRI.startswith(CSEID))
		self.assertGreater(len(TestRemote_Annc.remoteCntRI), len(CSEID), r)	# must be longer if succeeded

		# Retrieve locally announced resource
		r, rsc = RETRIEVE(f'{CSEURL}{TestRemote_Annc.remoteCntRI}', CSEID)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:cntA'))


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_unannounceFromHostingCSE(self) -> None:
		""" Unannouncement from own CSE """
		r, rsc = DELETE(f'{cseURL}/{cntRN}', ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)



# TODO Test: non-resource attribute in "aa" attribute

def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
		
	# create an announced AE, but no extra attributes
	addTest(suite, TestRemote_Annc('test_createAnnounceAEwithATwithoutAA'))
	addTest(suite, TestRemote_Annc('test_retrieveAnnouncedAEwithATwithoutAA'))
	addTest(suite, TestRemote_Annc('test_retrieveCSEBaseAnnc'))
	addTest(suite, TestRemote_Annc('test_deleteAnnounceAE'))

	# create an announced AE, including announced attribute
	addTest(suite, TestRemote_Annc('test_createAnnounceAEwithATwithWrongAA1Fail'))
	addTest(suite, TestRemote_Annc('test_createAnnounceAEwithATwithWrongAA2Fail'))
	addTest(suite, TestRemote_Annc('test_createAnnounceAEwithATwithWrongAA3Fail'))
	addTest(suite, TestRemote_Annc('test_createAnnounceAEwithATwithAA'))
	addTest(suite, TestRemote_Annc('test_retrieveAnnouncedAEwithATwithAA'))
	addTest(suite, TestRemote_Annc('test_deleteAnnounceAE'))

	# create an announced AE, including NA announced attribute
	addTest(suite, TestRemote_Annc('test_createAnnounceAEwithNAAttributes'))
	addTest(suite, TestRemote_Annc('test_addLBLtoAnnouncedAE'))
	addTest(suite, TestRemote_Annc('test_removeLBLfromAnnouncedAE'))
	addTest(suite, TestRemote_Annc('test_deleteAnnounceAE'))

	# create an announced AE, with non-resource announcedAttributes
	addTest(suite, TestRemote_Annc('test_createAnnounceAEwithNonResourceAttributes'))

	# create an announced Node & MgmtObj [bat]
	addTest(suite, TestRemote_Annc('test_createAnnounceNode'))
	addTest(suite, TestRemote_Annc('test_retrieveAnnouncedNode'))
	addTest(suite, TestRemote_Annc('test_announceMgmtobj'))
	addTest(suite, TestRemote_Annc('test_retrieveAnnouncedMgmtobj'))
	addTest(suite, TestRemote_Annc('test_retrieveRCNOriginalResource'))
	addTest(suite, TestRemote_Annc('test_retrieveRCNOriginalResourceFail'))
	addTest(suite, TestRemote_Annc('test_deleteRCNOriginalResourceFail'))
	addTest(suite, TestRemote_Annc('test_updateMgmtObjAttribute'))
	addTest(suite, TestRemote_Annc('test_addMgmtObjAttribute'))
	addTest(suite, TestRemote_Annc('test_removeMgmtObjAttribute'))
	addTest(suite, TestRemote_Annc('test_removeMgmtObjAA'))
	addTest(suite, TestRemote_Annc('test_removeMgmtObjCSIfromAT'))
	addTest(suite, TestRemote_Annc('test_addMgmtObjCSItoAT'))
	addTest(suite, TestRemote_Annc('test_removeMgmtObjAT'))
	addTest(suite, TestRemote_Annc('test_deleteAnnounceNode'))

	# create an announced ACP
	addTest(suite, TestRemote_Annc('test_createAnnouncedACP'))
	addTest(suite, TestRemote_Annc('test_retrieveAnnouncedACPwithWrongOriginator'))
	addTest(suite, TestRemote_Annc('test_retrieveAnnouncedACP'))
	addTest(suite, TestRemote_Annc('test_retrieveAnnouncedACPwithCSI'))
	addTest(suite, TestRemote_Annc('test_deleteAnnounceACP'))

	# create an announced CNT with announcedSyncType = bi-directional
	addTest(suite, TestRemote_Annc('test_createAnnouncedCNTSynced'))
	addTest(suite, TestRemote_Annc('test_updateRemoteCNT'))
	addTest(suite, TestRemote_Annc('test_deleteAnnouncedCNTSynced'))

	# announcement to own CSE
	addTest(suite, TestRemote_Annc('test_announceToHostingCSE'))
	addTest(suite, TestRemote_Annc('test_unannounceFromHostingCSE'))


	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
