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
from init import *


class TestGRP(unittest.TestCase):

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
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt1, rsc = CREATE(aeURL, cls.originator, C.tCNT, jsn)
		assert rsc == C.rcCreated, 'cannot create container'
		cls.cnt1RI = findXPath(cls.cnt1, 'm2m:cnt/ri')
		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : '%s2' % cntRN
				}}
		cls.cnt2, rsc = CREATE(aeURL, cls.originator, C.tCNT, jsn)
		assert rsc == C.rcCreated, 'cannot create container'
		cls.cnt2RI = findXPath(cls.cnt2, 'm2m:cnt/ri')


	@classmethod
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		

	def test_createGRP(self):
		self.assertIsNotNone(TestGRP.cse)
		self.assertIsNotNone(TestGRP.ae)
		self.assertIsNotNone(TestGRP.cnt1)
		self.assertIsNotNone(TestGRP.cnt2)
		jsn = 	{ 'm2m:grp' : { 
					'rn' : grpRN,
					'mt' : C.tMIXED,
					'mnm': 10,
					'mid': [ TestGRP.cnt1RI, TestGRP.cnt2RI ]
				}}
		r, rsc = CREATE(aeURL, TestGRP.originator, C.tGRP, jsn)
		self.assertEqual(rsc, C.rcCreated)


	def test_retrieveGRP(self):
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


	# Update a GRP with container. Should fail.
	def test_updateGRPwithCNT(self):
		jsn = 	{ 'm2m:cnt' : { 
					'lbl' : [ 'wrong' ]
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, jsn)
		self.assertNotEqual(rsc, C.rcUpdated)


	def test_addCNTtoGRP(self):
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 2)

		jsn = 	{ 'm2m:cnt' : { 
					'rn'  : '%s3' % cntRN
				}}
		self.cnt3, rsc = CREATE(aeURL, self.originator, C.tCNT, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.cnt3RI = findXPath(self.cnt3, 'm2m:cnt/ri')
		mid = findXPath(r, 'm2m:grp/mid')
		mid.append(self.cnt3RI)

		jsn = 	{ 'm2m:grp' : { 
					'mid'  : mid
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 3)


	def test_addCINviaFOPT(self):
		# add CIN via fopt
		jsn = 	{ 'm2m:cin' : {
					'cnf' : 'a',
					'con' : 'aValue'
				}}
		r, rsc = CREATE('%s/fopt' % grpURL, TestGRP.originator, C.tCNT, jsn)
		self.assertEqual(rsc, C.rcOK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), C.rcCreated)
			self.assertIsNotNone(findXPath(c, 'pc/m2m:cin'))
			to = findXPath(c, 'to')
			self.assertIsNotNone(to)
			r, rsc = RETRIEVE('%s%s' % (URL, to), TestGRP.originator)	# retrieve the CIN by the returned ri
			self.assertEqual(rsc, C.rcOK)
			self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')

		# try to retrieve the created CIN's directly 
		r, rsc = RETRIEVE('%s/la' % cntURL, TestGRP.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		r, rsc = RETRIEVE('%s2/la' % cntURL, TestGRP.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		r, rsc = RETRIEVE('%s3/la' % cntURL, TestGRP.originator)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')


	def test_retrieveLAviaFOPT(self):
		# Retrieve via fopt
		r, rsc = RETRIEVE('%s/fopt/la' % grpURL, TestGRP.originator)
		self.assertEqual(rsc, C.rcOK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), C.rcOK)
			self.assertIsNotNone(findXPath(c, 'pc/m2m:cin'))
			to = findXPath(c, 'to')
			self.assertIsNotNone(to)
			r, rsc = RETRIEVE('%s%s' % (URL, to), TestGRP.originator)	# retrieve the CIN by the returned ri
			self.assertEqual(rsc, C.rcOK)
			self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')


	def test_updateCNTviaFOPT(self):
		# add CIN via fopt
		jsn = 	{ 'm2m:cnt' : {
					'lbl' :  [ 'aTag' ]
				}}
		r, rsc = UPDATE('%s/fopt' % grpURL, TestGRP.originator, jsn)
		self.assertEqual(rsc, C.rcOK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), C.rcUpdated)
			self.assertIsNotNone(findXPath(c, 'pc/m2m:cnt'))
			to = findXPath(c, 'to')
			self.assertIsNotNone(to)
			r, rsc = RETRIEVE('%s%s' % (URL, to), TestGRP.originator)	# retrieve the CIN by the returned ri
			self.assertEqual(rsc, C.rcOK)
			self.assertTrue('aTag' in findXPath(r, 'm2m:cnt/lbl'))


	def test_addExistingCNTtoGRP(self):
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, C.rcOK)
		cnm = findXPath(r, 'm2m:grp/cnm')
		mid = findXPath(r, 'm2m:grp/mid')
		mid.append(self.cnt1RI)
		self.assertEqual(len(mid), cnm+1)
		jsn = 	{ 'm2m:grp' : { 
					'mid'  : mid
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, jsn)
		self.assertEqual(rsc, C.rcUpdated)
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), cnm) # == old cnm


# TODO add different resource (fcnt)
# TODO remove different resource
#


	def test_deleteCNTviaFOPT(self):
		r, rsc = DELETE('%s/fopt' % grpURL, TestGRP.originator)
		self.assertEqual(rsc, C.rcOK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), C.rcDeleted)


	def test_deleteGRPByUnknownOriginator(self):
		_, rsc = DELETE(grpURL, 'Cwrong')
		self.assertEqual(rsc, C.rcOriginatorHasNoPrivilege)


	def test_deleteGRPByAssignedOriginator(self):
		_, rsc = DELETE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, C.rcDeleted)


		#TODO check GRP itself: members


if __name__ == '__main__':
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

	unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)

