#
#	tesGRP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for GRP functionality
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)


class TestGRP(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, 'Cannot retrieve CSEBase: %s' % cseURL

		jsn = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, jsn)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt1, rsc = CREATE(aeURL, cls.originator, T.CNT, jsn)
		assert rsc == RC.created, 'cannot create container'
		cls.cnt1RI = findXPath(cls.cnt1, 'm2m:cnt/ri')
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : '%s2' % cntRN
				}}
		cls.cnt2, rsc = CREATE(aeURL, cls.originator, T.CNT, jsn)
		assert rsc == RC.created, 'cannot create container'
		cls.cnt2RI = findXPath(cls.cnt2, 'm2m:cnt/ri')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createGRP(self):
		self.assertIsNotNone(TestGRP.cse)
		self.assertIsNotNone(TestGRP.ae)
		self.assertIsNotNone(TestGRP.cnt1)
		self.assertIsNotNone(TestGRP.cnt2)
		jsn = 	{ 'm2m:grp' : { 
					'rn' : grpRN,
					'mt' : T.MIXED,
					'mnm': 10,
					'mid': [ TestGRP.cnt1RI, TestGRP.cnt2RI ]
				}}
		r, rsc = CREATE(aeURL, TestGRP.originator, T.GRP, jsn)
		self.assertEqual(rsc, RC.created)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveGRP(self):
		_, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveGRPWithWrongOriginator(self):
		_, rsc = RETRIEVE(grpURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesGRP(self):
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:grp/ty'), T.GRP)
		self.assertEqual(findXPath(r, 'm2m:grp/pi'), findXPath(TestGRP.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'm2m:grp/rn'), grpRN)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:grp/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:grp/et'))
		self.assertEqual(findXPath(r, 'm2m:grp/cr'), TestGRP.originator)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mt'))
		self.assertEqual(findXPath(r, 'm2m:grp/mt'), T.MIXED)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/mnm'), 10)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mid'))
		self.assertIsInstance(findXPath(r, 'm2m:grp/mid'), list)
		self.assertEqual(len(findXPath(r, 'm2m:grp/mid')), 2)
		self.assertIsNone(findXPath(r, 'm2m:grp/st'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateGRP(self):
		jsn = 	{ 'm2m:grp' : { 
					'mnm': 15
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, jsn)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/mnm'), 15)


	# Update a GRP with container. Should fail.
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateGRPwithCNT(self):
		jsn = 	{ 'm2m:cnt' : { 
					'lbl' : [ 'wrong' ]
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, jsn)
		self.assertNotEqual(rsc, RC.updated)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCNTtoGRP(self):
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 2)

		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : '%s3' % cntRN
				}}
		self.cnt3, rsc = CREATE(aeURL, self.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.created)
		self.cnt3RI = findXPath(self.cnt3, 'm2m:cnt/ri')
		mid = findXPath(r, 'm2m:grp/mid')
		mid.append(self.cnt3RI)

		jsn = 	{ 'm2m:grp' : { 
					'mid'  : mid
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, jsn)
		self.assertEqual(rsc, RC.updated)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 3)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCINviaFOPT(self):
		# add CIN via fopt
		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'aValue'
				}}
		r, rsc = CREATE('%s/fopt' % grpURL, TestGRP.originator, T.CNT, jsn)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), RC.created)
			self.assertIsNotNone(findXPath(c, 'pc/m2m:cin'))
			to = findXPath(c, 'to')
			self.assertIsNotNone(to)
			r, rsc = RETRIEVE('%s%s' % (URL, to), TestGRP.originator)	# retrieve the CIN by the returned ri
			self.assertEqual(rsc, RC.OK)
			self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')

		# try to retrieve the created CIN's directly 
		r, rsc = RETRIEVE('%s/la' % cntURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		r, rsc = RETRIEVE('%s2/la' % cntURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		r, rsc = RETRIEVE('%s3/la' % cntURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveLAviaFOPT(self):
		# Retrieve via fopt
		r, rsc = RETRIEVE('%s/fopt/la' % grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), RC.OK)
			self.assertIsNotNone(findXPath(c, 'pc/m2m:cin'))
			to = findXPath(c, 'to')
			self.assertIsNotNone(to)
			r, rsc = RETRIEVE('%s%s' % (URL, to), TestGRP.originator)	# retrieve the CIN by the returned ri
			self.assertEqual(rsc, RC.OK)
			self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTviaFOPT(self):
		# add CIN via fopt
		jsn = 	{ 'm2m:cnt' : {
					'lbl' :  [ 'aTag' ]
				}}
		r, rsc = UPDATE('%s/fopt' % grpURL, TestGRP.originator, jsn)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), RC.updated)
			self.assertIsNotNone(findXPath(c, 'pc/m2m:cnt'))
			to = findXPath(c, 'to')
			self.assertIsNotNone(to)
			r, rsc = RETRIEVE('%s%s' % (URL, to), TestGRP.originator)	# retrieve the CIN by the returned ri
			self.assertEqual(rsc, RC.OK)
			self.assertTrue('aTag' in findXPath(r, 'm2m:cnt/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addExistingCNTtoGRP(self):
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		cnm = findXPath(r, 'm2m:grp/cnm')
		mid = findXPath(r, 'm2m:grp/mid')
		mid.append(self.cnt1RI)
		self.assertEqual(len(mid), cnm+1)
		jsn = 	{ 'm2m:grp' : { 
					'mid'  : mid
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, jsn)
		self.assertEqual(rsc, RC.updated)
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), cnm) # == old cnm


# TODO add different resource (fcnt)
# TODO remove different resource
#


	def test_deleteCNTviaFOPT(self):
		r, rsc = DELETE('%s/fopt' % grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), RC.deleted)


	def test_deleteGRPByUnknownOriginator(self):
		_, rsc = DELETE(grpURL, 'Cwrong')
		self.assertEqual(rsc, RC.originatorHasNoPrivilege)


	def test_deleteGRPByAssignedOriginator(self):
		_, rsc = DELETE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.deleted)


		#TODO check GRP itself: members


def run():
	suite = unittest.TestSuite()
	suite.addTest(TestGRP('test_createGRP'))
	suite.addTest(TestGRP('test_retrieveGRP'))
	suite.addTest(TestGRP('test_retrieveGRPWithWrongOriginator'))
	suite.addTest(TestGRP('test_attributesGRP'))
	suite.addTest(TestGRP('test_updateGRP'))
	suite.addTest(TestGRP('test_updateGRPwithCNT'))
	suite.addTest(TestGRP('test_addCNTtoGRP'))
	suite.addTest(TestGRP('test_addCINviaFOPT'))
	suite.addTest(TestGRP('test_retrieveLAviaFOPT'))
	suite.addTest(TestGRP('test_updateCNTviaFOPT'))
	suite.addTest(TestGRP('test_addExistingCNTtoGRP'))
	suite.addTest(TestGRP('test_deleteCNTviaFOPT'))
	suite.addTest(TestGRP('test_deleteGRPByUnknownOriginator'))
	suite.addTest(TestGRP('test_deleteGRPByAssignedOriginator'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
