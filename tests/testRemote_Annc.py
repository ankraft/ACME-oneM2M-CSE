#
#	tesRemote_Annc.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Announcementfunctionality to a remote CSE. Tests are
#	skipped if there is no remote CSE.
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T
from init import *


# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a remote CSE.
noRemote = not connectionPossible(REMOTEcseURL)
# _, rsc = RETRIEVE(REMOTEcseURL, REMOTEORIGINATOR)
# noRemote = rsc != C.rcOK

class TestRemote_Annc(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def setUpClass(cls):
		# check connection to CSE's
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == C.rcOK, 'Cannot retrieve CSEBase: %s' % cseURL
		cls.remoteCse, rsc = RETRIEVE(REMOTEcseURL, REMOTEORIGINATOR)
		assert rsc == C.rcOK, 'Cannot retrieve CSEBase: %s' % REMOTEcseURL


	@classmethod
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not


	# Create an AE with AT, but no AA
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def test_createAnnounceAEwithATwithoutAA(self):
		jsn = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	'NMyApp1Id',
				 	'rr': 	False,
				 	'srv': 	[ '3' ],
				 	'at': 	[ REMOTECSEID ]
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/at'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:ae/at')), 2)
		self.assertIn(REMOTECSEID, findXPath(r, 'm2m:ae/at'))

		TestRemote_Annc.remoteAeRI = None
		for x in findXPath(r, 'm2m:ae/at'):
			if x == REMOTECSEID:
				continue
			TestRemote_Annc.remoteAeRI = x
		self.assertIsNotNone(self.remoteAeRI)
		self.assertIsNone(findXPath(r, 'm2m:ae/aa'))
		TestRemote_Annc.ae = r


	# Retrieve the announced AE with AT, but no AA
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def test_retrieveAnnouncedAEwithATwithoutAA(self):
		if TestRemote_Annc.remoteAeRI is None:
			self.skipTest('remote AE.ri not found')
		r, rsc = RETRIEVE('%s/~%s' %(REMOTEURL, TestRemote_Annc.remoteAeRI), CSEID)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:aeA'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/ty'))
		self.assertEqual(findXPath(r, 'm2m:aeA/ty'), T.AEAnnc)
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/pi'))
		self.assertTrue(CSEID.endswith(findXPath(r, 'm2m:aeA/pi')))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lnk'))
		self.assertTrue(findXPath(r, 'm2m:aeA/lnk').endswith( findXPath(TestRemote_Annc.ae, 'm2m:ae/ri') ))


	# Delete the AE with AT, but no AA
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def test_deleteAnnounceAE(self):
		if TestRemote_Annc.remoteAeRI is None:
			self.skipTest('remote AE.ri not found')
		_, rsc = DELETE(aeURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)
		# try to retrieve the announced AE. Should not be found
		r, rsc = RETRIEVE('%s/~%s' %(REMOTEURL, TestRemote_Annc.remoteAeRI), CSEID)
		self.assertEqual(rsc, C.rcNotFound)
		TestRemote_Annc.ae = None


	# Create an AE with AT and AA
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def test_createAnnounceAEwithATwithAA(self):
		jsn = 	{ 'm2m:ae' : {
					'rn': 	aeRN, 
					'api': 	'NMyApp1Id',
				 	'rr': 	False,
				 	'srv': 	[ '3' ],
				 	'lbl':	[ 'aLabel'],
				 	'at': 	[ REMOTECSEID ],
				 	'aa': 	[ 'lbl' ]
				}}
		r, rsc = CREATE(cseURL, 'C', T.AE, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lbl'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/lbl'), list)
		self.assertEqual(len(findXPath(r, 'm2m:ae/lbl')), 1)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/at'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:ae/at')), 2)
		self.assertIn(REMOTECSEID, findXPath(r, 'm2m:ae/at'))
		self.assertIsInstance(findXPath(r, 'm2m:ae/aa'), list)
		self.assertEqual(len(findXPath(r, 'm2m:ae/aa')), 1)
		self.assertIn('lbl', findXPath(r, 'm2m:ae/aa'))

		TestRemote_Annc.remoteAeRI = None
		for x in findXPath(r, 'm2m:ae/at'):
			if x == REMOTECSEID:
				continue
			TestRemote_Annc.remoteAeRI = x
		self.assertIsNotNone(self.remoteAeRI)
		TestRemote_Annc.ae = r


	# Retrieve the announced AE with AT and AA
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def test_retrieveAnnouncedAEwithATwithAA(self):
		if TestRemote_Annc.remoteAeRI is None:
			self.skipTest('remote AE.ri not found')
		r, rsc = RETRIEVE('%s/~%s' %(REMOTEURL, TestRemote_Annc.remoteAeRI), CSEID)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:aeA'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/ty'))
		self.assertEqual(findXPath(r, 'm2m:aeA/ty'), T.AEAnnc)
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/pi'))
		self.assertTrue(CSEID.endswith(findXPath(r, 'm2m:aeA/pi')))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lnk'))
		self.assertTrue(findXPath(r, 'm2m:aeA/lnk').endswith( findXPath(TestRemote_Annc.ae, 'm2m:ae/ri') ))
		self.assertIsNotNone(findXPath(r, 'm2m:aeA/lbl'))
		self.assertEqual(len(findXPath(r, 'm2m:aeA/lbl')), 1)
		self.assertIn('aLabel', findXPath(r, 'm2m:aeA/lbl'))


	# Update an non-AA AE with AA
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def test_addAAtoAnnounceAEwithoutAA(self):
		jsn = 	{ 'm2m:ae' : {
				 	'lbl':	[ 'aLabel'],
				 	'aa': 	[ 'lbl' ]
				}}
		r, rsc = UPDATE(aeURL, ORIGINATOR, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/lbl'))



# add ae without AT, with AA, AT later
# update ae
# add to AA
# remove from AA
# remove whole AA
# remove from AT
# remove whole AT
# rcn=7 (original resource)



	# Create a Node with AT
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def test_createAnnounceNode(self):
		jsn = 	{ 'm2m:nod' : {
					'rn': 	nodRN, 
					'ni': 	'aNI', 
				 	'at': 	[ REMOTECSEID ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:nod/at'))
		self.assertIsInstance(findXPath(r, 'm2m:nod/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:nod/at')), 2)
		self.assertIn(REMOTECSEID, findXPath(r, 'm2m:nod/at'))

		TestRemote_Annc.remoteNodRI = None
		for x in findXPath(r, 'm2m:nod/at'):
			if x == REMOTECSEID:
				continue
			TestRemote_Annc.remoteNodRI = x
		self.assertIsNotNone(self.remoteNodRI)
		self.assertIsNone(findXPath(r, 'm2m:Nod/aa'))
		TestRemote_Annc.node = r


	# Retrieve the announced Node with AT
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def test_retrieveAnnouncedNode(self):
		if TestRemote_Annc.remoteNodRI is None:
			self.skipTest('remote Node.ri not found')
		r, rsc = RETRIEVE('%s/~%s' %(REMOTEURL, TestRemote_Annc.remoteNodRI), CSEID)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:nodA'))
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/ty'))
		self.assertEqual(findXPath(r, 'm2m:nodA/ty'), T.NODAnnc)
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/pi'))
		self.assertTrue(CSEID.endswith(findXPath(r, 'm2m:nodA/pi')))
		self.assertIsNotNone(findXPath(r, 'm2m:nodA/lnk'))
		self.assertTrue(findXPath(r, 'm2m:nodA/lnk').endswith( findXPath(TestRemote_Annc.node, 'm2m:nod/ri') ))

	# Create a mgmtObj under the node
	@unittest.skipIf(noRemote, 'No remote CSEBase')
	def test_announceMgmtobj(self):
		jsn = 	{ 'm2m:bat' : {
					'mgd' : T.BAT,
					'dc'  : 'battery',
					'rn'  : 'battery',
					'btl' : 23,
					'bts' : 1,
				 	'at': 	[ REMOTECSEID ]
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/at'))
		self.assertIsInstance(findXPath(r, 'm2m:bat/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:bat/at')), 2)
		self.assertIn(REMOTECSEID, findXPath(r, 'm2m:bat/at'))

# TODO retrieve mgmtAnnc
# delete node and test annc



def run():
	suite = unittest.TestSuite()

	# create an announced AE, but no extra attributes
	suite.addTest(TestRemote_Annc('test_createAnnounceAEwithATwithoutAA'))
	suite.addTest(TestRemote_Annc('test_retrieveAnnouncedAEwithATwithoutAA'))
	suite.addTest(TestRemote_Annc('test_deleteAnnounceAE'))

	# create an announced AE, including announced attribute
	suite.addTest(TestRemote_Annc('test_createAnnounceAEwithATwithAA'))
	suite.addTest(TestRemote_Annc('test_retrieveAnnouncedAEwithATwithAA'))
	suite.addTest(TestRemote_Annc('test_deleteAnnounceAE'))

	# create an announced AE, add extra announced attribute later
	# suite.addTest(TestRemote_Annc('test_createAnnounceAEwithATwithoutAA'))
	# suite.addTest(TestRemote_Annc('test_addAAtoAnnounceAEwithoutAA'))
	# suite.addTest(TestRemote_Annc('test_retrieveAnnounceAEwithATwithAA'))
	# suite.addTest(TestRemote_Annc('test_deleteAnnounceAE'))

	# create an announced Node
	suite.addTest(TestRemote_Annc('test_createAnnounceNode'))
	suite.addTest(TestRemote_Annc('test_retrieveAnnouncedNode'))
	suite.addTest(TestRemote_Annc('test_announceMgmtobj'))


	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
