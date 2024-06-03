#
#	testFCNT.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for FCNT functionality & notifications
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *


CND = 'org.onem2m.common.moduleclass.temperature'
CNDWRONG = 'wrong'
GISCND = 'someCND'
GISRN  = 'gis'
gisURL = f'{aeURL}/{GISRN}'

class TestFCNT(unittest.TestCase):
	
	ae 			= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestFCNT')
		dct = 	{ 'm2m:ae' : {
					'rn': aeRN, 
					'api': APPID,
					'rr': False,
					'srv': [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		testCaseEnd('Setup TestFCNT')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestFCNT')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestFCNT')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTWrongCND(self) -> None:
		""" Create <FCNT> [cod:tempe] with wrong CND -> Fail"""
		self.assertIsNotNone(TestFCNT.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CNDWRONG, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTWrongTPE(self) -> None:
		""" Create <FCNT> [wrong] with wrong TPE -> Fail"""
		self.assertIsNotNone(TestFCNT.ae)
		dct = 	{ 'wrong' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNT(self) -> None:
		""" Create <FCNT> [cod:tempe] """
		self.assertIsNotNone(TestFCNT.ae)
		dct = 	{ 'cod:tempe' : { 
					'rn'	: fcntRN,
					'cnd' 	: CND, 
					'curT0'	: 23.0,
					'unit'	: 1,
					'minVe'	: -100.0,
					'maxVe' : 100.0,
					'steVe'	: 0.5
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFCNT(self) -> None:
		""" Retrieve <FCNT> """
		r, rsc = RETRIEVE(fcntURL, TestFCNT.originator)
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFCNTWithWrongOriginator(self) -> None:
		"""	Retrieve <FCNT> """
		r, rsc = RETRIEVE(fcntURL, 'Cwrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesFCNT(self) -> None:
		"""	Test <FCNT> attributes """
		r, rsc = RETRIEVE(fcntURL, TestFCNT.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'cod:tempe/ty'), T.FCNT)
		self.assertEqual(findXPath(r, 'cod:tempe/pi'), findXPath(TestFCNT.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'cod:tempe/rn'), fcntRN)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/ct'))
		self.assertIsNotNone(findXPath(r, 'cod:tempe/lt'))
		self.assertIsNotNone(findXPath(r, 'cod:tempe/et'))
		self.assertIsNone(findXPath(r, 'cod:tempe/cr'))
		self.assertEqual(findXPath(r, 'cod:tempe/cnd'), CND)
		self.assertEqual(findXPath(r, 'cod:tempe/curT0'), 23.0)
		self.assertIsNone(findXPath(r, 'cod:tempe/tarTe'))
		self.assertEqual(findXPath(r, 'cod:tempe/unit'), 1)
		self.assertEqual(findXPath(r, 'cod:tempe/minVe'), -100.0)
		self.assertEqual(findXPath(r, 'cod:tempe/maxVe'), 100.0)
		self.assertEqual(findXPath(r, 'cod:tempe/steVe'), 0.5)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/st'))
		self.assertEqual(findXPath(r, 'cod:tempe/st'), 0)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNT(self) -> None:
		"""	Update <FCNT> [cod:tempe] TARTE """
		dct = 	{ 'cod:tempe' : {
					'tarTe':	5.0
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, dct)
		self.assertEqual(rsc, RC.UPDATED)
		r, rsc = RETRIEVE(fcntURL, TestFCNT.originator)		# retrieve fcnt again
		self.assertEqual(rsc, RC.OK)
		self.assertIsNotNone(findXPath(r, 'cod:tempe/tarTe'))
		self.assertIsInstance(findXPath(r, 'cod:tempe/tarTe'), float)
		self.assertEqual(findXPath(r, 'cod:tempe/tarTe'), 5.0)
		self.assertEqual(findXPath(r, 'cod:tempe/curT0'), 23.0)
		self.assertEqual(findXPath(r, 'cod:tempe/st'), 1, r)
		self.assertGreater(findXPath(r, 'cod:tempe/lt'), findXPath(r, 'cod:tempe/ct'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTwithCnd(self) -> None:
		"""	Update <FCNT> [cod:tempe] CND -> Fail """
		dct = 	{ 'cod:tempe' : {
					'cnd' : CND,
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTwithWrongType(self) -> None:
		"""	Update <FCNT> [cod:tempe] TARTE wrong type -> Fail """
		dct = 	{ 'cod:tempe' : {
					'tarTe':	'5.0'
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateFCNTwithUnkownAttribute(self) -> None:
		"""	Update <FCNT> [cod:tempe] unknown attribute -> Fail """

		dct = 	{ 'cod:tempe' : {
					'wrong':	'aValue'
				}}
		r, rsc = UPDATE(fcntURL, TestFCNT.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTUnknown(self) -> None:
		"""	Create unknown <FCNT> -> Fail """
		dct = 	{ 'cod:unknown' : { 
					'rn'	: 'unknown',
					'cnd' 	: 'unknown', 
					'attr'	: 'aValuealue',
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTUnderFCNT(self) -> None:
		"""	Create <CNT> under <FCNT> """
		dct = 	{ 'm2m:cnt' : { 
					'rn' : cntRN
				}}
		r, rsc = CREATE(fcntURL, TestFCNT.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTUnderFCNT(self) -> None:
		"""	Delete <CNT> under FCNT """
		_, rsc = DELETE(f'{fcntURL}/{cntRN}', TestFCNT.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTUnderFCNT(self) -> None:
		""" Create <FCNT> under <FCNT> """
		dct = 	{ 'cod:tempe' : { 
					'cnd' 	: CND, 
					'rn' : fcntRN,
				}}
		r, rsc = CREATE(fcntURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteFCNTUnderFCNT(self) -> None:
		"""	Delete <FCNT> under <FCNT> """
		_, rsc = DELETE(f'{fcntURL}/{fcntRN}', TestFCNT.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteFCNT(self) -> None:
		"""	Delete <FCNT> """
		_, rsc = DELETE(fcntURL, TestFCNT.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createGenericInterworking(self) -> None:
		"""	Create <FCNT> [GIS] """
		dct = 	{ 'm2m:gis' : { 
					'cnd' 	: GISCND,
					'gisn'	: 'abc',
					'rn'	: GISRN
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createGenericInterworkingWrong(self) -> None:
		""" Create <FCNT> [GIS] missing M attributes -> Fail """
		dct = 	{ 'm2m:gis' : { 
					'cnd' 	: GISCND
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createGenericInterworkingWrong2(self) -> None:
		"""	Create <FCNT> [GIS] unknown attribute -> Fail """
		dct = 	{ 'm2m:gis' : { 
					'cnd' 	: GISCND,
					'gisn'	: 'abc',
					'wrong'	: 'wrong'	# Unknown attribute
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createGenericInterworkingOperationInstance(self) -> None:
		"""	Create <FCNT> [GIS] GION & GIOS """
		dct = 	{ 'm2m:gio' : { 
					'cnd' 	: GISCND,
					'gion'	: 'anOperation',
					'gios'	: 'aStatus'
				}}
		r, rsc = CREATE(gisURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createGenericInterworkingOperationInstance2(self) -> None:
		"""	Create <FCNT> [GIS] GION, GIOS, GIIP """
		dct = 	{ 'm2m:gio' : { 
					'cnd' 	: GISCND,
					'gion'	: 'anOperation',
					'giip'	: [ 'link1', 'link2' ],
					'gios'	: 'aStatus'
				}}
		r, rsc = CREATE(gisURL, TestFCNT.originator, T.FCNT, dct)
		self.assertEqual(rsc, RC.CREATED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteGenericInterworking(self) -> None:
		"""	Delete <FCNT> [GIS] """
		_, rsc = DELETE(gisURL, TestFCNT.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTWithCreatorWrong(self) -> None:
		""" Create <FCNT> [GIS] with creator attribute (wrong) -> Fail """
		dct = 	{ 'm2m:gis' : { 
					'cnd' 	: GISCND,
					'cr'	: 'content',
					'gisn'	: 'abc'
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)			# Not allowed
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFCNTWithCreator(self) -> None:
		""" Create <FCNT> [GIS] with creator attribute set to Null """
		dct = 	{ 'm2m:gis' : { 
					'cnd' 	: GISCND,
					'cr'	: None,
					'gisn'	: 'abc'
				}}
		r, rsc = CREATE(aeURL, TestFCNT.originator, T.FCNT, dct)	
		self.assertEqual(rsc, RC.CREATED)
		self.assertEqual(findXPath(r, 'm2m:gis/cr'), TestFCNT.originator)	# Creator should now be set to originator

		# Check whether creator is there in a RETRIEVE
		r, rsc = RETRIEVE(f'{aeURL}/{findXPath(r, "m2m:gis/rn")}', TestFCNT.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:gis/cr'), TestFCNT.originator)



def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestFCNT, [

		'test_createFCNTWrongCND',
		'test_createFCNTWrongTPE',
		'test_createFCNT',
		'test_retrieveFCNT',
		'test_retrieveFCNTWithWrongOriginator',
		'test_attributesFCNT',
		'test_updateFCNT',
		'test_updateFCNTwithCnd',
		'test_updateFCNTwithWrongType',
		'test_updateFCNTwithUnkownAttribute',
		'test_createFCNTUnknown',
		'test_createCNTUnderFCNT',
		'test_deleteCNTUnderFCNT',
		'test_createFCNTUnderFCNT',
		'test_deleteFCNTUnderFCNT',
		'test_deleteFCNT',
		'test_createGenericInterworking',
		'test_createGenericInterworkingWrong',
		'test_createGenericInterworkingWrong2',
		'test_createGenericInterworkingOperationInstance',
		'test_createGenericInterworkingOperationInstance2',
		'test_deleteGenericInterworking',
		'test_createFCNTWithCreatorWrong',
		'test_createFCNTWithCreator',

	])

	# Run tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)

