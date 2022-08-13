#
#	testSMD.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for SMD functionality 
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import DesiredIdentifierResultType as DRT, NotificationEventType as NET, ResourceTypes as T, ResponseStatusCode as RC
from acme.etc.Types import ResultContentType as RCN, Permission
from init import *



class TestSMD(unittest.TestCase):
	ae 				= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestCRS')

		# create AE
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : True,
				 	'srv' : [ '3' ],
					'poa' : [ NOTIFICATIONSERVER ],
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		testCaseEnd('Setup TestCRS')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		testCaseStart('TearDown TestCRS')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestCRS')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################
	#
	#	General attribute tests
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSMDdcrpIRIFail(self) -> None:
		"""	CREATE <SMD> with dcrp set to IRI -> FAIL"""
		dct = 	{ 'm2m:smd' : { 
					'rn' : 'failSMD',
					'dcrp' : 1,
				}}
		r, rsc = CREATE(aeURL, TestSMD.originator, T.SMD, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSMDdspNotBase64Fail(self) -> None:
		"""	CREATE <SMD> with DSP not encoded as base64 -> FAIL"""
		dct = 	{ 'm2m:smd' : { 
					'rn' : 'failSMD',
					'dcrp' : 2,
					'dsp' : 'wrong',
				}}
		r, rsc = CREATE(aeURL, TestSMD.originator, T.SMD, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	#########################################################################
	#
	#	Create tests
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSMDdspBase64(self) -> None:
		"""	CREATE <SMD> with DSP encoded as base64"""
		dct = 	{ 'm2m:smd' : { 
					'rn' : smdRN,
					'dcrp' : 2,
					'dsp' : 'Y29ycmVjdA==',
				}}
		r, rsc = CREATE(aeURL, TestSMD.originator, T.SMD, dct)
		self.assertEqual(rsc, RC.created, r)
		self.assertIsNotNone(findXPath(r, 'm2m:smd/svd'))
		self.assertIsNotNone(findXPath(r, 'm2m:smd/vlde'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSMD(self) -> None:
		"""	DELETE <SMD>"""
		r, rsc = DELETE(smdURL, TestSMD.originator)
		self.assertEqual(rsc, RC.deleted, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSMDunderACPFail(self) -> None:
		"""	CREATE <SMD> under ACP -> Fail"""
		# create ACP
		dct:JSON = 	{ "m2m:acp": {
			"rn": acpRN,
			"pv": {
			},
			"pvs": { 
				"acr": [ {
					"acor": [ TestSMD.originator],
					"acop": Permission.ALL
				} ]
			},
		}}
		r, rsc = CREATE(aeURL, TestSMD.originator, T.ACP, dct)
		self.assertEqual(rsc, RC.created, r)

		# Try to create SMD under ACP
		dct = 	{ 'm2m:smd' : { 
					'rn' : smdRN,
					'dcrp' : 2,
					#'dsp' : 'Y29ycmVjdA==',
				}}
		r, rsc = CREATE(f'{aeURL}/{acpRN}', TestSMD.originator, T.SMD, dct)
		self.assertEqual(rsc, RC.invalidChildResourceType, r)

		# Delete ACP
		r, rsc = DELETE(f'{aeURL}/{acpRN}', TestSMD.originator)
		self.assertEqual(rsc, RC.deleted, r)


	#########################################################################
	#
	#	Update tests
	#
	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSMDwithSOEandDSPFail(self) -> None:
		"""	UPDATE <SMD> with both SOE and DSP -> Fail"""
		dct = 	{ 'm2m:smd' : { 
					'soe' : 'aValue',
					'dsp' : 'Y29ycmVjdA==',
				}}
		r, rsc = UPDATE(smdURL, TestSMD.originator, dct)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSMDwithVLDEfalse(self) -> None:
		"""	UPDATE <SMD> with VLDE set to False"""
		dct = 	{ 'm2m:smd' : { 
					'vlde' : False,
				}}
		r, rsc = UPDATE(smdURL, TestSMD.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNotNone(findXPath(r, 'm2m:smd/vlde'))
		self.assertFalse(findXPath(r, 'm2m:smd/vlde'))
		self.assertIsNotNone(findXPath(r, 'm2m:smd/svd'))
		self.assertFalse(findXPath(r, 'm2m:smd/svd'))


	#########################################################################

# TODO check not-present of semanticOpExec when RETRIEVE

def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
	
	# Clear counters
	clearSleepTimeCount()

	# General attribute test cases
	suite.addTest(TestSMD('test_createSMDdcrpIRIFail'))
	suite.addTest(TestSMD('test_createSMDdspNotBase64Fail'))

	# Create tests
	suite.addTest(TestSMD('test_createSMDdspBase64'))
	suite.addTest(TestSMD('test_deleteSMD'))
	suite.addTest(TestSMD('test_createSMDunderACPFail'))

	# Update tests
	suite.addTest(TestSMD('test_createSMDdspBase64'))
	suite.addTest(TestSMD('test_updateSMDwithSOEandDSPFail'))
	suite.addTest(TestSMD('test_updateSMDwithVLDEfalse'))

	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(2, True)
	sys.exit(errors)
