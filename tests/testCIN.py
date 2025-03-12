#
#	testCIN.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for CIN functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from acme.etc.DateUtils import getResourceDate
from init import *

class TestCIN(unittest.TestCase):

	ae 			= None
	cnt 		= None
	originator 	= None


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestCIN')
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED, 'cannot create container'
		testCaseEnd('Setup TestCIN')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestCIN')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestCIN')



	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)

	
	#########################################################################
	

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCIN(self) -> None:
		""" Create a <CIN> resource """
		self.assertIsNotNone(TestCIN.ae)
		self.assertIsNotNone(TestCIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'rn'  : cinRN,
					'cnf' : 'text/plain:0',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveCIN(self) -> None:
		""" Retrieve <CIN> resource """
		r, rsc = RETRIEVE(cinURL, TestCIN.originator)
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesCIN(self) -> None:
		""" Test <CIN> attributes """
		r, rsc = RETRIEVE(cinURL, TestCIN.originator)
		self.assertEqual(rsc, RC.OK, r)

		# TEST attributess
		self.assertEqual(findXPath(r, 'm2m:cin/ty'), T.CIN)
		self.assertEqual(findXPath(r, 'm2m:cin/pi'), findXPath(TestCIN.cnt,'m2m:cnt/ri'))
		self.assertEqual(findXPath(r, 'm2m:cin/rn'), cinRN)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:cin/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:cin/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:cin/st'))
		self.assertIsNone(findXPath(r, 'm2m:cin/cr'))
		self.assertIsNotNone(findXPath(r, 'm2m:cin/cnf'))
		self.assertEqual(findXPath(r, 'm2m:cin/cnf'), 'text/plain:0')
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'AnyValue')
		self.assertGreater(findXPath(r, 'm2m:cin/cs'), 0)
		self.assertIsNone(findXPath(r, 'm2m:cin/acpi'))



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateCINFail(self) -> None:
		""" Update <CIN> -> Fail """
		dct = 	{ 'm2m:cin' : {
					'con' : 'NewValue'
				}}
		r, rsc = UPDATE(cinURL, TestCIN.originator, dct)
		self.assertEqual(rsc, RC.OPERATION_NOT_ALLOWED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINUnderAE(self) -> None:
		""" Create <CIN> resource under <AE> -> Fail """
		dct = 	{ 'm2m:cin' : {
					'rn'  : cinRN,
					'cnf' : 'text/plain:0',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(aeURL, TestCIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.INVALID_CHILD_RESOURCE_TYPE, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINwithString(self) -> None:
		""" Create a <CIN> resource with string value """
		self.assertIsNotNone(TestCIN.ae)
		self.assertIsNotNone(TestCIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 'AnyValue')	


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINwithInteger(self) -> None:
		""" Create a <CIN> resource with integer value """
		self.assertIsNotNone(TestCIN.ae)
		self.assertIsNotNone(TestCIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'con' : 23
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 23)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINwithFloat(self) -> None:
		""" Create a <CIN> resource with float value """
		self.assertIsNotNone(TestCIN.ae)
		self.assertIsNotNone(TestCIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'con' : 23.17
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 23.17)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINwithBoolean(self) -> None:
		""" Create a <CIN> resource with boolean value """
		self.assertIsNotNone(TestCIN.ae)
		self.assertIsNotNone(TestCIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'con' : True
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), True)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINwithList(self) -> None:
		""" Create a <CIN> resource with list value """
		self.assertIsNotNone(TestCIN.ae)
		self.assertIsNotNone(TestCIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'con' : [ 1, 2, 3, 4, 5 ]
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), [ 1, 2, 3, 4, 5 ])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINwithStructure(self) -> None:
		""" Create a <CIN> resource with dict/JSON structure value """
		self.assertIsNotNone(TestCIN.ae)
		self.assertIsNotNone(TestCIN.cnt)
		dct = 	{ 'm2m:cin' : {
					'con' : { 'a': 1, 'b': 2, 'c': 3 }
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:cin/con'), { 'a': 1, 'b': 2, 'c': 3 })


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCIN(self) -> None:
		""" Delete <CIN> resource """
		_, rsc = DELETE(cinURL, TestCIN.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINWithCreatorWrong(self) -> None:
		""" Create <CIN> with creator attribute (wrong) -> Fail """
		dct = 	{ 'm2m:cin' : { 
					'cr' : 'wrong',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)				# Not allowed
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINWithCnfWrong1(self) -> None:
		""" Create <CIN> with cnf attribute (wrong 1) -> Fail """
		dct = 	{ 'm2m:cin' : { 
					'cnf' : 'text',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)				# Not allowed
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINWithCnfWrong2(self) -> None:
		""" Create <CIN> with cnf attribute (wrong 2) -> Fail """
		dct = 	{ 'm2m:cin' : { 
					'cnf' : 'text:0',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)				# Not allowed
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINWithCnfWrong3(self) -> None:
		""" Create <CIN> with cnf attribute (wrong 4) -> Fail """
		dct = 	{ 'm2m:cin' : { 
					'cnf' : 'text/plain',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)				# Not allowed
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINWithCnfWrong4(self) -> None:
		""" Create <CIN> with cnf attribute (wrong 5) -> Fail """
		dct = 	{ 'm2m:cin' : { 
					'cnf' : 'text/plain:0:0:0',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)				# Not allowed
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINWithCnfWrong5(self) -> None:
		""" Create <CIN> with cnf attribute (wrong 6) -> Fail """
		dct = 	{ 'm2m:cin' : { 
					'cnf' : 'text/plain:9',
					'con' : 'AnyValue'
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)				# Not allowed
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINWithCreator(self) -> None:
		""" Create <CIN> with creator attribute set to Null """
		dct = 	{ 'm2m:cin' : { 
					'con' : 'AnyValue',
					'cr' : None
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)	
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:cin/cr'), TestCIN.originator)	# Creator should now be set to originator

		# Check whether creator is there in a RETRIEVE
		r, rsc = RETRIEVE(f'{cntURL}/{findXPath(r, "m2m:cin/rn")}', TestCIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cin/cr'), TestCIN.originator)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createRetrieveCINWithDcnt(self) -> None:
		""" Create and Retrieve <CIN> with deletionCnt attribute set """
		dct = 	{ 'm2m:cin' : { 
					'rn' : 'dcntTest',
					'con' : 'AnyValue',
					'dcnt' : 5
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)	
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:cin/dcnt'), 5)					# dcnt should be set to 5

		# Check dcnt in a RETRIEVE
		for i in range(5, 0, -1):
			r, rsc = RETRIEVE(f'{cntURL}/dcntTest', TestCIN.originator)
			self.assertEqual(rsc, RC.OK)
			self.assertEqual(findXPath(r, 'm2m:cin/dcnt'), i, r)				# dcnt should decrease

		# The next RETRIEVE should fail since it should been deleted with last RETRIEVE
		r, rsc = RETRIEVE(f'{cntURL}/dcntTest', TestCIN.originator)
		self.assertEqual(rsc, RC.NOT_FOUND)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINwithAcpi(self) -> None:
		""" Create a <CIN> with acpi attribute set -> Fail"""
		dct = 	{ 'm2m:cin' : { 
					'rn' : 'dcntTest',
					'con' : 'AnyValue',
					'acpi' : [ 'someACP' ]
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)	
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCINwithDgt(self) -> None:
		""" Create a <CIN> resource with dgt attribute"""
		self.assertIsNotNone(TestCIN.ae)
		self.assertIsNotNone(TestCIN.cnt)
		dgt = getResourceDate()
		dct = 	{ 'm2m:cin' : {
					'rn'  : f'{cinRN}dgt',
					'cnf' : 'text/plain:0',
					'con' : 'AnyValue',
					'dgt' : dgt
				}}
		r, rsc = CREATE(cntURL, TestCIN.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# RETRIEVE the CIN with the dgt
		r, rsc = RETRIEVE(f'{cntURL}/{cinRN}dgt', TestCIN.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cin/dgt'), dgt)



# More tests of la, ol etc in testCNT_CNI.py

def run(testFailFast:bool) -> TestResult:
	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestCIN, [
		'test_createCIN',
		'test_retrieveCIN',
		'test_attributesCIN',
		'test_updateCINFail',
		'test_createCINUnderAE',

		# Various content types
		'test_createCINwithString',
		'test_createCINwithInteger',
		'test_createCINwithFloat',
		'test_createCINwithBoolean',
		'test_createCINwithList',
		'test_createCINwithStructure',


		'test_deleteCIN',
		'test_createCINWithCreatorWrong',
		'test_createCINWithCnfWrong1',
		'test_createCINWithCnfWrong2',
		'test_createCINWithCnfWrong3',
		'test_createCINWithCnfWrong4',
		'test_createCINWithCnfWrong5',
		'test_createCINWithCreator',
		'test_createRetrieveCINWithDcnt',
		'test_createCINwithAcpi',
		'test_createCINwithDgt'
	])
	
	# Run tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
