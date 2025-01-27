#
#	testFCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for FCNT functionality & notifications
#

import unittest, sys
import requests
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *


CND = 'org.onem2m.common.moduleclass.temperature'

class TestFCNT_FCI(unittest.TestCase):

	ae 			= None 
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestFCNT_FCI')
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
					'rr': False,
					'srv': [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		testCaseEnd('Setup TestFCNT_FCI')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestFCNT_FCI')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestFCNT_FCI')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTwithMniMissingFciedFail(self) -> None:
		"""	Create a <FCNT> with MNI but without FCIED -> Fail """
		self.assertIsNotNone(TestFCNT_FCI.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5,
					'mni'	: 10
				}}
		r, rsc = CREATE(aeURL, TestFCNT_FCI.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTwithMbsMissingFciedFail(self) -> None:
		"""	Create a <FCNT> with MBS but without FCIED -> Fail """
		self.assertIsNotNone(TestFCNT_FCI.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5,
					'mbs'	: 100
				}}
		r, rsc = CREATE(aeURL, TestFCNT_FCI.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTwithMiaMissingFciedFail(self) -> None:
		"""	Create a <FCNT> with MIA but without FCIED -> Fail """
		self.assertIsNotNone(TestFCNT_FCI.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5,
					'mia'	: 10
				}}
		r, rsc = CREATE(aeURL, TestFCNT_FCI.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTwithMni0Fail(self) -> None:
		"""	Create a <FCNT> with MNI = 0 and FCIED = False -> Fail """
		self.assertIsNotNone(TestFCNT_FCI.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5,
					'fcied'	: False,
					'mni'	: 0
				}}
		r, rsc = CREATE(aeURL, TestFCNT_FCI.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTwithMbs0Fail(self) -> None:
		"""	Create a <FCNT> with MBS = 0 and FCIED = False -> Fail """
		self.assertIsNotNone(TestFCNT_FCI.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5,
					'fcied'	: False,
					'mbs'	: 0
				}}
		r, rsc = CREATE(aeURL, TestFCNT_FCI.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTwithMia0Fail(self) -> None:
		"""	Create a <FCNT> with MIA = 0 and FCIED = False -> Fail """
		self.assertIsNotNone(TestFCNT_FCI.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5,
					'fcied'	: False,
					'mia'	: 0
				}}
		r, rsc = CREATE(aeURL, TestFCNT_FCI.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTwithMniFciedFalse(self) -> None:
		"""	Create a <FCNT> with MNI for use with <FCI> but with FCIED set to false """
		self.assertIsNotNone(TestFCNT_FCI.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5,
					'fcied'	: False,
					'mni'	: 10
				}}
		r, rsc = CREATE(aeURL, TestFCNT_FCI.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.CREATED)

		# Delete again
		_, rsc = DELETE(fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTwithMniFciedTrue(self) -> None:
		"""	Create a <FCNT> with MNI for use with <FCI> but with FCIED set to true """
		self.assertIsNotNone(TestFCNT_FCI.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5,
					'fcied'	: True,
					'mni'	: 10
				}}
		r, rsc = CREATE(aeURL, TestFCNT_FCI.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.CREATED)

		# Don't delete, Result wil be used in the next tests


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesFCNT(self) -> None:
		"""	Validate <FCNT> attributes """
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'cod:tempe/ty'), T.FCNT, r)
		self.assertEqual(findXPath(r, 'cod:tempe/pi'), findXPath(TestFCNT_FCI.ae,'m2m:ae/ri'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/rn'), fcntRN, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/ct'), r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/lt'), r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/et'), r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/st'), r)
		self.assertIsNone(findXPath(r, 'cod:tempe/cr'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/cnd'), CND, r)
		self.assertEqual(findXPath(r, 'cod:tempe/curT0'), 23.0, r)
		self.assertIsNone(findXPath(r, 'cod:tempe/tarTe'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/unit'), 1, r)
		self.assertEqual(findXPath(r, 'cod:tempe/minVe'), -100.0, r)
		self.assertEqual(findXPath(r, 'cod:tempe/maxVe'), 100.0, r)
		self.assertEqual(findXPath(r, 'cod:tempe/steVe'), 0.5, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/st'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/st'), 0, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/fcied'), r)
		self.assertTrue(findXPath(r, 'cod:tempe/fcied'), r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/mni'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/mni'), 10, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cni'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 1, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cbs'), r)
		self.assertGreater(findXPath(r, 'cod:tempe/cbs'), 0, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveLatestFCI(self) -> None:
		"""	RETRIEVE the latest <FCI> """
		r, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK, r)

		# test resource attributes
		self.assertIsNotNone(findXPath(r, 'cod:tempe/ty'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/ty'), ResourceTypes.FCI, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/st'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/st'), 0, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/org'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/org'), TestFCNT_FCI.originator, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cs'), r)

		# test custom attributes
		self.assertEqual(findXPath(r, 'cod:tempe/curT0'), 23.0, r)
		self.assertIsNone(findXPath(r, 'cod:tempe/tarTe'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/unit'), 1, r)
		self.assertEqual(findXPath(r, 'cod:tempe/minVe'), -100.0, r)
		self.assertEqual(findXPath(r, 'cod:tempe/maxVe'), 100.0, r)
		self.assertEqual(findXPath(r, 'cod:tempe/steVe'), 0.5, r)



		# TODO check child FCI (only one) is created via latest? own test?



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNT(self) -> None:
		"""	Update <FCNT> """
		dct = 	{ 'cod:tempe' : {
					'tarTe':   5.0,	# Add new attribute
					'curT0'	: 17.0,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)		# retrieve fcnt again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/tarTe'))
		self.assertIsInstance(findXPath(r, 'cod:tempe/tarTe'), float)
		self.assertEqual(findXPath(r, 'cod:tempe/tarTe'), 5.0)
		self.assertEqual(findXPath(r, 'cod:tempe/curT0'), 17.0)
		self.assertEqual(findXPath(r, 'cod:tempe/st'), 1, r)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 2)
		self.assertGreater(findXPath(r, 'cod:tempe/cbs'), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFCNTLatest(self) -> None:
		"""	Retrieve <FCI> via <FCNT>/la """
		r, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe'))
		self.assertIsNotNone(findXPath(r, 'cod:tempe/curT0'))
		self.assertEqual(findXPath(r, 'cod:tempe/curT0'), 17.0, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFCNTOldest(self) -> None:
		"""	Retrieve <FCI> via <FCNT>/ol """
		r, rsc = RETRIEVE(f'{fcntURL}/ol', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe'))
		self.assertIsNotNone(findXPath(r, 'cod:tempe/curT0'))
		self.assertEqual(findXPath(r, 'cod:tempe/curT0'), 23.0, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTMniReduce(self) -> None:
		""" Update <FCNT> reduce MNI = 1"""
		dct = 	{ 'cod:tempe' : {
					'mni':   1,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)		# retrieve fcnt again
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'cod:tempe/mni'), 1)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 1)

		rla, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(rla)

		rol, rsc = RETRIEVE(f'{fcntURL}/ol', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(rol)

		# al == ol ?
		self.assertEqual(findXPath(rla, 'cod:tempe/ri'), findXPath(rol, 'cod:tempe/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateLBL(self) -> None:
		""" Update <FCNT> LBL """

		""" Retrieve <FCNT> """
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		cni = findXPath(r, 'cod:tempe/cni')
		cbs = findXPath(r, 'cod:tempe/cbs')
		st = findXPath(r, 'cod:tempe/st')

		""" Update <FCNT> LBL """
		dct = 	{ 'cod:tempe' : {
					'lbl':	[ 'aLabel' ],
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIn('aLabel', findXPath(r, 'cod:tempe/lbl'))

		rla, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(rla)
		self.assertIsNotNone(findXPath(rla, 'cod:tempe/lbl'))
		self.assertIn('aLabel', findXPath(rla, 'cod:tempe/lbl'))
		self.assertEqual(st + 1, findXPath(rla, 'cod:tempe/st'))

		""" Retrieve <FCNT> and compare cni and cbs """
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(cni + 1, findXPath(r, 'cod:tempe/cni'), r)
		self.assertLess(cbs, findXPath(r, 'cod:tempe/cbs'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateNothing(self) -> None:
		""" Update <FCNT> with no changes """

		""" Retrieve <FCNT> """
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		cni = findXPath(r, 'cod:tempe/cni')
		cbs = findXPath(r, 'cod:tempe/cbs')
		st = findXPath(r, 'cod:tempe/st')

		""" Update <FCNT> LBL """
		dct:dict = 	{ 'cod:tempe' : {
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertIn('aLabel', findXPath(r, 'cod:tempe/lbl'))
		self.assertEqual(cni, findXPath(r, 'cod:tempe/cni'), r)
		self.assertEqual(cbs, findXPath(r, 'cod:tempe/cbs'), r)
		self.assertEqual(st+1, findXPath(r, 'cod:tempe/st'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateMNInoFCICreated(self) -> None:
		""" Update MNI, no <FCI> shall be created """
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)
		cni = findXPath(r, 'cod:tempe/cni')

		dct = 	{ 'cod:tempe' : {
					'mni':	10,				# Increase mni again
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertEqual(cni, findXPath(r, 'cod:tempe/cni'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCIFail(self) -> None:
		"""	Create a <FCI> -> Fail """
		self.assertIsNotNone(TestFCNT_FCI.ae)
		dct = 	{ 'cod:tempe' : { 
					'curT0'	: 23.0,
				}}
		r, rsc = CREATE(fcntURL, TestFCNT_FCI.originator, T.FCI, dct)
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCIFail(self) -> None:
		"""	Update a <FCI> -> Fail """
		self.assertIsNotNone(TestFCNT_FCI.ae)
		# Retrieve the latest FCI
		rla, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK, rla)
		self.assertIsNotNone(rla)
		self.assertIsNotNone(findXPath(rla, 'cod:tempe'))
		# Update the latest
		dct = 	{ 'cod:tempe' : { 
					'curT0'	: 5.0,
				}}
		r, rsc = UPDATE(f'{fcntURL}/{findXPath(rla, "cod:tempe/rn")}', TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTMniNull(self) -> None:
		""" Update <FCNT> : set MNI to null"""
		dct = 	{ 'cod:tempe' : {
					'mni':   None,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)

		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)		# retrieve fcnt again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNone(findXPath(r, 'cod:tempe/mni'), r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cni'), r)

		# latest / oldest still there
		rla, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)

		rol, rsc = RETRIEVE(f'{fcntURL}/ol', TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTMbsSmallFail(self) -> None:
		""" Update <FCNT> : set MBS to CS-1 bytes -> Fail"""
		# retrieve fcnt first to get the current cs
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)		# retrieve fcnt again
		self.assertEqual(rsc, RC.OK)
		cs = findXPath(r, 'cod:tempe/cs')

		dct = 	{ 'cod:tempe' : {
					'mbs':   cs-1,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTMbsLarger(self) -> None:
		""" Update <FCNT> : set MBS to CS+1 bytes"""
		# retrieve fcnt first to get the current cs
		r, rsc = RETRIEVE(fcntURL, TestFCNT_FCI.originator)		# retrieve fcnt again
		self.assertEqual(rsc, RC.OK)
		cs = findXPath(r, 'cod:tempe/cs')

		dct = 	{ 'cod:tempe' : {
					'mbs':   cs+1,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(cs+1, findXPath(r, 'cod:tempe/mbs'), r)
		self.assertEqual(1, findXPath(r, 'cod:tempe/cni'), r)

		r, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)		# retrieve at least one la
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTFciedFalse(self) -> None:
		""" Update <FCNT> : set FCIED to false, MNI to 10"""
		# First update the FCNT: add mni, remove cbs, update custom attribute
		dct = 	{ 'cod:tempe' : {
					'mni': 		10,
					'mbs':		None,	# remove restriction
					'curT0':	17.0,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cni'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 2, r)
		self.assertIsNone(findXPath(r, 'cod:tempe/mbs'), r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/mni'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/mni'), 10, r)


		# Update FCIED to false
		dct = 	{ 'cod:tempe' : {
					'fcied':	False,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/mni'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/mni'), 10, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cni'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 1, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cbs'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/cbs'), findXPath(r, 'cod:tempe/cs'), r)

		r, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)		# retrieve no latest
		self.assertEqual(rsc, RC.OK)

		r, rsc = RETRIEVE(f'{fcntURL}/ol', TestFCNT_FCI.originator)		# retrieve no oldest
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTMniWithoutFciedFail(self) -> None:
		""" Update <FCNT> : MNI to 10 without FCIED -> Fail"""

		dct = 	{ 'cod:tempe' : {
					'mni':	10,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)
		self.assertIsNone(findXPath(r, 'cod:tempe/fcied'), r)
		self.assertIsNone(findXPath(r, 'cod:tempe/mni'), r)

		r, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)		# retrieve no latest
		self.assertEqual(rsc, RC.NOT_FOUND)

		r, rsc = RETRIEVE(f'{fcntURL}/ol', TestFCNT_FCI.originator)		# retrieve no oldest
		self.assertEqual(rsc, RC.NOT_FOUND)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTFciedRemoved(self) -> None:
		""" Update <FCNT> : remove FCIED"""
		dct = 	{ 'cod:tempe' : {
					'fcied':	None,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNone(findXPath(r, 'cod:tempe/mbs'), r)
		self.assertIsNone(findXPath(r, 'cod:tempe/mni'), r)
		self.assertIsNone(findXPath(r, 'cod:tempe/mia'), r)
		self.assertIsNone(findXPath(r, 'cod:tempe/cni'), r)
		self.assertIsNone(findXPath(r, 'cod:tempe/cbs'), r)

		r, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)		# retrieve no latest
		self.assertEqual(rsc, RC.NOT_FOUND)

		r, rsc = RETRIEVE(f'{fcntURL}/old', TestFCNT_FCI.originator)		# retrieve no oldest
		self.assertEqual(rsc, RC.NOT_FOUND)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTFciedFalsePreviousNull(self) -> None:
		""" Update <FCNT> : set FCIED to None (remove), then to false (1 <FCIN>)"""
		# First update the FCNT: remove fcied etc
		dct = 	{ 'cod:tempe' : {
					'fcied': None,	# remove fcied
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNone(findXPath(r, 'cod:tempe/mbs'), r)
		self.assertIsNone(findXPath(r, 'cod:tempe/cbs'), r)
		self.assertIsNone(findXPath(r, 'cod:tempe/mni'), r)
		self.assertIsNone(findXPath(r, 'cod:tempe/cni'), r)

		# There should be no child resource
		r, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)		# retrieve no latest
		self.assertEqual(rsc, RC.NOT_FOUND)


		# Update FCIED to false. There should be only one child resource
		dct = 	{ 'cod:tempe' : {
					'fcied':	False,	# type:ignore
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT_FCI.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cni'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/cni'), 1, r)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/cbs'), r)
		self.assertEqual(findXPath(r, 'cod:tempe/cbs'), findXPath(r, 'cod:tempe/cs'), r)

		r, rsc = RETRIEVE(f'{fcntURL}/la', TestFCNT_FCI.originator)		# retrieve no latest
		self.assertEqual(rsc, RC.OK)

		r, rsc = RETRIEVE(f'{fcntURL}/ol', TestFCNT_FCI.originator)		# retrieve no oldest
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteFCNT(self) -> None:
		""" Delete <FCNT> """
		_, rsc = DELETE(fcntURL, TestFCNT_FCI.originator)
		self.assertEqual(rsc, RC.DELETED)


def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestFCNT_FCI, [
			
		# CREATE tests
		'test_createFCNTwithMniMissingFciedFail',
		'test_createFCNTwithMbsMissingFciedFail',
		'test_createFCNTwithMiaMissingFciedFail',
		'test_createFCNTwithMni0Fail',
		'test_createFCNTwithMbs0Fail',
		'test_createFCNTwithMia0Fail',
		'test_createFCNTwithMniFciedFalse',
		'test_createFCNTwithMniFciedTrue',

		# RETRIEVE tests
		'test_attributesFCNT',
		'test_retrieveLatestFCI',

		# UPDATE tests
		'test_updateFCNT',
		'test_retrieveFCNTLatest',
		'test_retrieveFCNTOldest',
		'test_updateLBL',
		'test_updateNothing',

		# create and update FCI
		'test_createFCIFail',
		'test_updateFCIFail',

		# Test various attribute combinations
		'test_updateFCNTMniReduce',
		'test_updateMNInoFCICreated',
		'test_updateFCNTMniNull',

		'test_updateFCNTMbsSmallFail',
		'test_updateFCNTMbsLarger',

		# Update fcied
		'test_updateFCNTFciedFalse',
		'test_updateFCNTFciedRemoved',	# After this no more fci present
		'test_updateFCNTMniWithoutFciedFail',
		'test_updateFCNTFciedFalsePreviousNull',

		# DELETE tests
		'test_deleteFCNT',

	])
	
	# Run tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)

