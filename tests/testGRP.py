#
#	testGRP.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for GRP functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *


# TODO add different resource (fcnt)
# TODO remove different resource
#



class TestGRP(unittest.TestCase):

	ae 			= None
	cnt1 		= None
	cnt2 		= None
	cnt1RI 		= None
	cnt2RI 		= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestGRP')
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		cls._createContainers()
		testCaseEnd('Setup TestGRP')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestGRP')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestGRP')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@classmethod
	def _createContainers(cls) -> None:
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt1, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		cls.cnt1RI = findXPath(cls.cnt1, 'm2m:cnt/ri')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}2'
				}}
		cls.cnt2, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		cls.cnt2RI = findXPath(cls.cnt2, 'm2m:cnt/ri')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createGRP(self) -> None:
		""" Create <GRP> """
		self.assertIsNotNone(TestGRP.ae)
		self.assertIsNotNone(TestGRP.cnt1)
		self.assertIsNotNone(TestGRP.cnt2)
		dct = 	{ 'm2m:grp' : { 
					'rn' : grpRN,
					'mt' : T.MIXED,
					'mnm': 10,
					'mid': [ TestGRP.cnt1RI, TestGRP.cnt2RI ]
				}}
		r, rsc = CREATE(aeURL, TestGRP.originator, T.GRP, dct)
		self.assertEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveGRP(self) -> None:
		""" Retrieve <GRP> """
		_, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveGRPWithWrongOriginator(self) -> None:
		"""	Retrieve <GRP> with wrong originator """
		_, rsc = RETRIEVE(grpURL, 'Cwrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesGRP(self) -> None:
		""" Validate <GRP> attributes """
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:grp/ty'), T.GRP)
		self.assertEqual(findXPath(r, 'm2m:grp/pi'), findXPath(TestGRP.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'm2m:grp/rn'), grpRN)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:grp/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:grp/et'))
		self.assertIsNone(findXPath(r, 'm2m:grp/cr'))
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
	def test_updateGRP(self) -> None:
		""" Update <GRP> """
		dct = 	{ 'm2m:grp' : { 
					'mnm': 15
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/mnm'), 15)


	# Update a GRP with container. Should fail.
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateGRPwithCNT(self) -> None:
		""" Update <GRP> with <CNT> -> Fail """
		dct = 	{ 'm2m:cnt' : { 
					'lbl' : [ 'wrong' ]
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, dct)
		self.assertNotEqual(rsc, RC.UPDATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCNTtoGRP(self) -> None:
		"""	Add <CNT> to <GRP> """
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 2)

		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}3' 
				}}
		self.cnt3, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.cnt3RI = findXPath(self.cnt3, 'm2m:cnt/ri')
		mid = findXPath(r, 'm2m:grp/mid')
		mid.append(self.cnt3RI)

		dct = 	{ 'm2m:grp' : { 
					'mid'  : mid
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 3)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addCINviaFOPT(self) -> None:
		"""	Add <CIN> to <CNT>s in <GRP> """
		# add CIN via fopt
		dct = 	{ 'm2m:cin' : {
					'cnf' : 'text/plain:0',
					'con' : 'aValue'
				}}
		r, rsc = CREATE(f'{grpURL}/fopt', TestGRP.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), RC.CREATED)
			self.assertIsNotNone(findXPath(c, 'pc/m2m:cin'))
			to = findXPath(c, 'pc/m2m:cin/ri')
			self.assertIsNotNone(to)
			r, rsc = RETRIEVE(f'{CSEURL}{to}', TestGRP.originator)	# retrieve the CIN by the returned ri
			self.assertEqual(rsc, RC.OK)
			self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')

		# try to retrieve the created CIN's directly 
		r, rsc = RETRIEVE(f'{cntURL}/la', TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		r, rsc = RETRIEVE(f'{cntURL}2/la', TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')
		r, rsc = RETRIEVE(f'{cntURL}3/la', TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveLAviaFOPT(self) -> None:
		"""	Retrieve <CNT>'s LA """
		# Retrieve via fopt
		r, rsc = RETRIEVE(f'{grpURL}/fopt/la', TestGRP.originator)
		self.assertEqual(rsc, RC.OK, r)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), RC.OK)
			self.assertIsNotNone(findXPath(c, 'pc/m2m:cin'))
			to = findXPath(c, 'pc/m2m:cin/ri')
			self.assertIsNotNone(to)
			r, rsc = RETRIEVE(f'{CSEURL}{to}', TestGRP.originator)	# retrieve the CIN by the returned ri
			self.assertEqual(rsc, RC.OK)
			self.assertEqual(findXPath(r, 'm2m:cin/con'), 'aValue')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCNTviaFOPT(self) -> None:
		"""	Update all <CNT>s in <GRP> """
		# add CIN via fopt
		dct = 	{ 'm2m:cnt' : {
					'lbl' :  [ 'aTag' ]
				}}
		r, rsc = UPDATE(f'{grpURL}/fopt', TestGRP.originator, dct)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), RC.UPDATED)
			self.assertIsNotNone(findXPath(c, 'pc/m2m:cnt'))
			to = findXPath(c, 'pc/m2m:cnt/ri')
			self.assertIsNotNone(to)
			r, rsc = RETRIEVE(f'{CSEURL}{to}', TestGRP.originator)	# retrieve the CIN by the returned ri
			self.assertEqual(rsc, RC.OK)
			self.assertTrue('aTag' in findXPath(r, 'm2m:cnt/lbl'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addExistingCNTtoGRP(self) -> None:
		"""	Add same CNT> to <GRP> again """
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		cnm = findXPath(r, 'm2m:grp/cnm')
		mid = findXPath(r, 'm2m:grp/mid')
		mid.append(self.cnt1RI)
		self.assertEqual(len(mid), cnm+1)
		dct = 	{ 'm2m:grp' : { 
					'mid'  : mid
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), cnm) # == old cnm


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTviaFOPT(self) -> None:
		""" Delete all <CNT> via <GRP> """
		r, rsc = DELETE(f'{grpURL}/fopt', TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 3)

		# check the returned structure
		for c in rsp:
			self.assertEqual(findXPath(c, 'rsc'), RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteGRPByUnknownOriginator(self) -> None:
		"""	Delete <GRP> by wrong originator """
		_, rsc = DELETE(grpURL, 'Cwrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteGRPByAssignedOriginator(self) -> None:
		""" Delete <GRP> by correct originator """
		_, rsc = DELETE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createGRP2(self) -> None:
		""" Create another <GRP> """
		# Re-create containers
		TestGRP._createContainers()
		# Create another grp
		dct = 	{ 'm2m:grp' : { 
					'rn' : grpRN,
					'mt' : T.MIXED,
					'mnm': 2,
					'mid': [ TestGRP.cnt1RI, TestGRP.cnt2RI ]
				}}
		r, rsc = CREATE(aeURL, TestGRP.originator, T.GRP, dct)
		self.assertEqual(rsc, RC.CREATED)
	
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addTooManyCNTToGRP2(self) -> None:
		""" Update <GRP> with too many MID -> Fail """
		# Add another <CNT>
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}3'
				}}
		TestGRP.cnt3, rsc = CREATE(aeURL, TestGRP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)
		TestGRP.cnt3RI = findXPath(TestGRP.cnt3, 'm2m:cnt/ri')

		dct2 = 	{ 'm2m:grp' : { 
					'mid': [ TestGRP.cnt1RI, TestGRP.cnt2RI, TestGRP.cnt3RI ]
				}}
		_, rsc = UPDATE(grpURL, TestGRP.originator, dct2)
		self.assertEqual(rsc, RC.MAX_NUMBER_OF_MEMBER_EXCEEDED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_addDeleteContainerCheckMID(self) -> None:
		"""	Add and delete <CNT>, check <GRP> MID"""
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 2)

		# Add container
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : f'{cntRN}4' 
				}}
		self.cnt4, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, self.cnt4)
		self.cnt4RI = findXPath(self.cnt4, 'm2m:cnt/ri')
	
		# Add container to group
		mid = findXPath(r, 'm2m:grp/mid')
		mid.append(self.cnt4RI)
		dct = 	{ 'm2m:grp' : { 
					'mid'  : mid
				}}
		r, rsc = UPDATE(grpURL, TestGRP.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 3)

		# Delete container
		r, rsc = DELETE(f'{aeURL}/{cntRN}4', self.originator)
		self.assertEqual(rsc, RC.DELETED)

		# Check group 
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 2)
		self.assertNotIn(self.cnt4RI, findXPath(r, 'm2m:grp/mid'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesGRP2(self) -> None:
		""" Validate <GRP> attributes after failed MID update"""
		r, rsc = RETRIEVE(grpURL, TestGRP.originator)

		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:grp/ty'), T.GRP)
		self.assertEqual(findXPath(r, 'm2m:grp/pi'), findXPath(TestGRP.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'm2m:grp/rn'), grpRN)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:grp/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:grp/et'))
		self.assertIsNone(findXPath(r, 'm2m:grp/cr'))
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mt'))
		self.assertEqual(findXPath(r, 'm2m:grp/mt'), T.MIXED)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/mnm'), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/cnm'))
		self.assertEqual(findXPath(r, 'm2m:grp/cnm'), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:grp/mid'))
		self.assertIsInstance(findXPath(r, 'm2m:grp/mid'), list)
		self.assertEqual(len(findXPath(r, 'm2m:grp/mid')), 2)
		self.assertIsNone(findXPath(r, 'm2m:grp/st'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createGRPWithCreatorWrong(self) -> None:
		""" Create <GRP> with creator attribute (wrong) -> Fail """
		dct = 	{ 'm2m:grp' : { 
					'mnm': 10,
					'mid': [],
					'cr' : 'wrong'
				}}
		r, rsc = CREATE(aeURL, TestGRP.originator, T.GRP, dct)				# Not allowed
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createGRPWithCreator(self) -> None:
		""" Create <GRP> with creator attribute set to Null """
		dct = 	{ 'm2m:grp' : { 
					'mnm': 10,
					'mid': [],
					'cr' : None
				}}
		r, rsc = CREATE(aeURL, TestGRP.originator, T.GRP, dct)	
		self.assertEqual(rsc, RC.CREATED)
		self.assertEqual(findXPath(r, 'm2m:grp/cr'), TestGRP.originator)	# Creator should now be set to originator

		# Check whether creator is there in a RETRIEVE
		r, rsc = RETRIEVE(f'{aeURL}/{findXPath(r, "m2m:grp/rn")}', TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:grp/cr'), TestGRP.originator)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTviaFopt(self) -> None:
		""" CREATE <CNT> under other <CNT>s via fopt """
		dct = 	{ 'm2m:cnt' : { 
					'rn': 'container'
				}}
		r, rsc = CREATE(f'{grpURL}/fopt', TestGRP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 2)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCNTviaFopt(self) -> None:
		""" RETRIEVE <CNT> under other <CNT>s via fopt """
		r, rsc = RETRIEVE(f'{grpURL}/fopt/container', TestGRP.originator)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 2)
		for r in rsp:
			self.assertEqual(findXPath(r, 'rsc'), RC.OK)
			pc = findXPath(r, 'pc')
			self.assertIsNotNone(pc)
			self.assertIsNotNone(findXPath(pc, 'm2m:cnt'))
			self.assertEqual(findXPath(pc, 'm2m:cnt/rn'), 'container')
			self.assertEqual(findXPath(pc, 'm2m:cnt/ty'), T.CNT)
			self.assertEqual(findXPath(pc, 'm2m:cnt/cni'), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTCNTviaFopt(self) -> None:
		""" CREATE <CNT> under other <CNT>/<CNT>s via fopt """
		dct = 	{ 'm2m:cnt' : { 
					'rn': 'container'
				}}
		r, rsc = CREATE(f'{grpURL}/fopt/container', TestGRP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.OK)
		rsp = findXPath(r, 'm2m:agr/m2m:rsp')
		self.assertIsNotNone(rsp)
		self.assertIsInstance(rsp, list)
		self.assertEqual(len(rsp), 2)

#TODO check GRP itself: members


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
		
	addTest(suite, TestGRP('test_createGRP'))
	addTest(suite, TestGRP('test_retrieveGRP'))
	addTest(suite, TestGRP('test_retrieveGRPWithWrongOriginator'))
	addTest(suite, TestGRP('test_attributesGRP'))
	addTest(suite, TestGRP('test_updateGRP'))
	addTest(suite, TestGRP('test_updateGRPwithCNT'))
	addTest(suite, TestGRP('test_addCNTtoGRP'))
	addTest(suite, TestGRP('test_addCINviaFOPT'))
	addTest(suite, TestGRP('test_retrieveLAviaFOPT'))
	addTest(suite, TestGRP('test_updateCNTviaFOPT'))
	addTest(suite, TestGRP('test_addExistingCNTtoGRP'))
	addTest(suite, TestGRP('test_deleteCNTviaFOPT'))
	addTest(suite, TestGRP('test_deleteGRPByUnknownOriginator'))
	addTest(suite, TestGRP('test_deleteGRPByAssignedOriginator'))

	addTest(suite, TestGRP('test_createGRP2'))	# create <GRP> again
	addTest(suite, TestGRP('test_addTooManyCNTToGRP2'))
	addTest(suite, TestGRP('test_attributesGRP2'))

	addTest(suite, TestGRP('test_createGRPWithCreatorWrong'))
	addTest(suite, TestGRP('test_createGRPWithCreator'))
	addTest(suite, TestGRP('test_deleteGRPByAssignedOriginator'))

	addTest(suite, TestGRP('test_createGRP'))	# create <GRP> again
	addTest(suite, TestGRP('test_addDeleteContainerCheckMID'))	
	addTest(suite, TestGRP('test_deleteGRPByAssignedOriginator'))

	# Test fopt
	addTest(suite, TestGRP('test_createGRP'))	# create <GRP> again
	addTest(suite, TestGRP('test_createCNTviaFopt'))
	addTest(suite, TestGRP('test_retrieveCNTviaFopt'))
	addTest(suite, TestGRP('test_createCNTCNTviaFopt'))
	addTest(suite, TestGRP('test_deleteGRPByAssignedOriginator'))



	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
