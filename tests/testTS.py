#
#	testTS.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for TS functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from init import *
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from typing import Tuple


class TestTS(unittest.TestCase):

	ae 			= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('TearDown TestTS')
		# create other resources
		dct =	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
			 		'rr'  : True,
			 		'srv' : [ RELEASEVERSION ],
			 		'poa' : [ NOTIFICATIONSERVER ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		testCaseEnd('Setup TestTS')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestTS')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestTS')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTS(self) -> None:
		""" Create <TS> """
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'rn'	: tsRN,
					'pei'	: 10000,
					'mdd'	: True,
					'mdt'	: 5001,
					'mdn'	: 10,
					'cnf'	: 'text/plain:0'
				}}
		r, rsc = CREATE(aeURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesTS(self) -> None:
		"""	Retrieve <TS> attributes """
		r, rsc = RETRIEVE(tsURL, TestTS.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'm2m:ts/ty'), T.TS)
		self.assertEqual(findXPath(r, 'm2m:ts/pi'), findXPath(TestTS.ae,'m2m:ae/ri'))
		self.assertEqual(findXPath(r, 'm2m:ts/cni'), 0)
		self.assertEqual(findXPath(r, 'm2m:ts/cbs'), 0)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/cnf'))
		self.assertEqual(findXPath(r, 'm2m:ts/cnf'), 'text/plain:0')
		self.assertEqual(findXPath(r, 'm2m:ts/pei'), 10000)
		self.assertEqual(findXPath(r, 'm2m:ts/peid'), 5000)
		self.assertTrue(findXPath(r, 'm2m:ts/mdd'))
		self.assertEqual(findXPath(r, 'm2m:ts/mdn'), 10)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'))		# empty mdlt is not created by default
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdt'))
		self.assertEqual(findXPath(r, 'm2m:ts/mdt'), 5001)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSunderTS(self) -> None:
		""" Create <TS> under <TS> -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'rn'	: tsRN,
				}}
		r, rsc = CREATE(tsURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.INVALID_CHILD_RESOURCE_TYPE, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmni(self) -> None:
		""" Update <TS> mni"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mni'	: 10
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:ts/mni'), 10)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmbs(self) -> None:
		""" Update <TS> mbs"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mbs'	: 1000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(r)
		self.assertEqual(findXPath(r, 'm2m:ts/mbs'), 1000)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSpeiFail(self) -> None:
		""" Update <TS> pei -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'pei'	: 1000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSpeidFail(self) -> None:
		""" Update <TS> peid -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'peid'	: 1000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddTrue(self) -> None:
		""" Update <TS> mdd = True"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdd'	: True,
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddTrueAndMdtFail(self) -> None:
		""" Update <TS> mdd = True with mdt -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdn'	: 2000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddTrueAndMdnFail(self) -> None:
		""" Update <TS> mdd = True with mdn -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdn'	: 2000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddTrueAndMdnNoneFail(self) -> None:
		""" Update <TS> mdd = True with remove mdn -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdn'	: None
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddTrueAndPeiFail(self) -> None:
		""" Update <TS> mdd = True with pei -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'pei'	: 2000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddTrueAndPeidFail(self) -> None:
		""" Update <TS> mdd = True with peid -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'pei'	: 200
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddFalse(self) -> None:
		""" Update <TS> mdd"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdd'	: False
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddWithMdtFail(self) -> None:
		""" Update <TS> mdd with mdt -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdd'	: False,
					'mdt'	: 2000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddWithMdnFail(self) -> None:
		""" Update <TS> mdd with mdn -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdd'	: False,
					'mdn'	: 10
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddWithPeiFail(self) -> None:
		""" Update <TS> mdd with pei -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdd'	: False,
					'pei'	: 1000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddWithPeidFail(self) -> None:
		""" Update <TS> mdd with peid -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdd'	: False,
					'peid'	: 200
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmddWithWrongPeiPeidFail(self) -> None:
		""" Update <TS> mdd with wrong pei and peid -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'pei'	: 2000,
					'peid'	: 2000
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmdn(self) -> None:
		""" Update <TS> mdd"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdn'	: 5
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdn'), 5)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmdc(self) -> None:
		""" Update <TS> mdc -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdc'	: 5
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSmdlt(self) -> None:
		""" Update <TS> mdlt -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 			# type: ignore [var-annotated]
					'mdlt'	: [ ]
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTScnf(self) -> None:
		""" Update <TS> cnf -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'cnf'	: 'application/wrong'
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSremoveMdn(self) -> None:
		""" Update <TS> remove mdn """
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdn'	: None
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		# self.assertIsNone(findXPath(r, 'm2m:ts/mdc'), r)
		# self.assertIsNone(findXPath(r, 'm2m:ts/mdn'), r)
		# self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdn'), r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteTS(self) -> None:
		"""	Delete <TS> """
		_, rsc = DELETE(tsURL, TestTS.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSnoMdd(self) -> None:
		""" Create <TS> without MDD"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'rn'	: tsRN,
				}}
		r, rsc = CREATE(aeURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdd'), r)
		self.assertFalse(findXPath(r, 'm2m:ts/mdd'), r)
		#TODO after discussion with Bob. Decide whether to have or don't have initial
		# self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'), r)
		# self.assertIsNone(findXPath(r, 'm2m:ts/mdc'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateTSMddwrong(self) -> None:
		""" Update <TS> MDD -> Fail """
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'mdd'	: True
				}}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSwithPeid(self) -> None:
		""" Create <TS> with peid == pei/2"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'pei'	: 1000,
					'peid'	: 500,
				}}
		r, rsc = CREATE(aeURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSwithPeidWrong(self) -> None:
		""" Create <TS> with peid > pei/2 -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'pei'	: 1000,
					'peid'	: 501,
				}}
		r, rsc = CREATE(aeURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSwithCnfWrong(self) -> None:
		""" Create <TS> with wrong cnf -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = 	{ 'm2m:ts' : { 
					'cnf'	: 'wrong',
				}}
		r, rsc = CREATE(aeURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createTSwithMissingMdtFail(self) -> None:
		""" Create <TS> with missing mdt -> Fail"""
		self.assertIsNotNone(TestTS.ae)
		dct = {	'm2m:ts': {
					'rn':'TimeSeries2',
					'mni': 10,
					'pei': 5000,                          # milliseconds
					'peid': 200,                          # milliseconds
					'mdd': True
				}
			}
		r, rsc = CREATE(aeURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_MddMdltMdcHandling(self) -> None:
		""" Check mdd handling with mdlt and mdc """
		self.assertIsNotNone(TestTS.ae)
		dct = {	'm2m:ts': {
					'rn': tsRN,
					'mdt': 2000,
				}
			}
		r, rsc = CREATE(aeURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdd'), r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0, r)

		# set mdd to False
		dct2 = {	'm2m:ts': {
					'mdd': False,
				}
			}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct2)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdd'), r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0, r)

		# add mdd with True
		dct2 = {	'm2m:ts': {
					'mdd': True,
				}
			}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct2)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdd'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0, r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'), r)

		# set mdd to False again (mdlt, mdc stay in the resource)
		dct2 = {	'm2m:ts': {
					'mdd': False,
				}
			}
		r, rsc = UPDATE(tsURL, TestTS.originator, dct2)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdd'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0, r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updatePeiCheckPeid(self) -> None:
		""" UPDATE <TS> with pei -> check peid """
		self.assertIsNotNone(TestTS.ae)

		# create <TS> with pei
		dct = {	'm2m:ts': {
					'rn':'TimeSeries3',
				}
			}
		r, rsc = CREATE(aeURL, TestTS.originator, T.TS, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNone(findXPath(r, 'm2m:ts/peid'), r)

		# update pei
		dct2 = {	'm2m:ts': {
					'pei': 1000,                          # milliseconds
			}}
		r, rsc = UPDATE(f'{aeURL}/TimeSeries3', TestTS.originator, dct2)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/peid'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/peid'), 500, r)
		self.assertIsNone(findXPath(r, 'm2m:ts/mdlt'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:ts/mdc'), r)
		self.assertEqual(findXPath(r, 'm2m:ts/mdc'), 0, r)



def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
	
	addTest(suite, TestTS('test_createTS'))
	addTest(suite, TestTS('test_attributesTS'))
	addTest(suite, TestTS('test_createTSunderTS'))
	addTest(suite, TestTS('test_updateTSmni'))
	addTest(suite, TestTS('test_updateTSmbs'))
	addTest(suite, TestTS('test_updateTSpeiFail'))
	addTest(suite, TestTS('test_updateTSpeidFail'))

	addTest(suite, TestTS('test_updateTSmddTrue'))
	addTest(suite, TestTS('test_updateTSmddTrueAndMdtFail'))
	addTest(suite, TestTS('test_updateTSmddTrueAndMdnFail'))
	addTest(suite, TestTS('test_updateTSmddTrueAndMdnNoneFail'))
	addTest(suite, TestTS('test_updateTSmddTrueAndPeiFail'))
	addTest(suite, TestTS('test_updateTSmddTrueAndPeidFail'))
	
	addTest(suite, TestTS('test_updateTSmddFalse'))
	addTest(suite, TestTS('test_updateTSmddWithMdtFail'))
	addTest(suite, TestTS('test_updateTSmddWithMdnFail'))
	addTest(suite, TestTS('test_updateTSmddWithPeiFail'))
	addTest(suite, TestTS('test_updateTSmddWithPeidFail'))
	addTest(suite, TestTS('test_updateTSmddWithWrongPeiPeidFail'))

	
	addTest(suite, TestTS('test_updateTSmdn'))
	addTest(suite, TestTS('test_updateTSmdc'))
	addTest(suite, TestTS('test_updateTSmdlt'))
	addTest(suite, TestTS('test_updateTSremoveMdn'))
	addTest(suite, TestTS('test_updateTScnf'))
	addTest(suite, TestTS('test_deleteTS'))
	addTest(suite, TestTS('test_createTSnoMdd'))
	addTest(suite, TestTS('test_updateTSMddwrong'))
	addTest(suite, TestTS('test_createTSwithPeid'))
	addTest(suite, TestTS('test_createTSwithPeidWrong'))
	addTest(suite, TestTS('test_createTSwithCnfWrong'))

	addTest(suite, TestTS('test_createTSwithMissingMdtFail'))

	addTest(suite, TestTS('test_deleteTS'))
	addTest(suite, TestTS('test_MddMdltMdcHandling'))

	addTest(suite, TestTS('test_updatePeiCheckPeid'))


	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)

