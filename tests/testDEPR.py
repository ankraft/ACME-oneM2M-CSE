#
#	testDEPR.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Dependency functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, Permission
from acme.etc.Types import EvalMode, Operation, EvalCriteriaOperator
from init import *



class TestDEPR(unittest.TestCase):

	ae 			= None
	aeRI		= None
	ae2 		= None
	cnt			= None
	cntRI		= None
	cntRI2		= None
	cnt2URL		= None
	actrRI2		= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		
		# Target Structure:
		# 
		#  AE       
   		#    ACP    
   		#    CNT    
     	#      ACTR 
   		#    CNT2
		# 	   ACTR2   
		#
		# Checks are on cbs for <depr> resources

		testCaseStart('Setup TestACTR')
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		cls.aeRI = findXPath(cls.ae, 'm2m:ae/ri')
	
		dct = 	{ 'm2m:cnt' : { 
				'rn' : cntRN,
			}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED
		cls.cntRI = findXPath(cls.cnt, 'm2m:cnt/ri')

		# create second CNT with ACP assigned
		dct = 	{ 'm2m:cnt' : { 
				'rn' : cntRN+'2',
			}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED
		cls.cntRI2 = findXPath(cls.cnt, 'm2m:cnt/ri')
		cls.cnt2URL = f'{aeURL}/{cntRN}2'

		# create <actr>
		dct = 	{ 'm2m:actr' : { 
					'rn' : actrRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThan,
						'sbjt': 'cni',
						'thld': 0	# react immediately
					},
					'evm': EvalMode.periodic,
					'ecp': requestCheckDelay * 2 * 1000,	# 2 seconds
					'orc': cls.aeRI,
					'apv': {
						'op': Operation.UPDATE,
						'fr': cls.originator,
						'to': cls.aeRI,
						'rqi': '1234',
						'rvi': RELEASEVERSION,
						'pc': { 
							'm2m:ae': {
								'lbl': [ 'aLabel' ]
						}},
					},

				}}
		r, rsc = CREATE(cntURL, cls.originator, T.ACTR, dct)
		assert rsc == RC.CREATED

		r, rsc = CREATE(cls.cnt2URL, cls.originator, T.ACTR, dct)
		assert rsc == RC.CREATED
		cls.actrRI2 = findXPath(r, 'm2m:actr/ri')

		testCaseEnd('Setup TestACTR')



	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestDEPR')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestDEPR')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)

	#########################################################################
	# 
	#	Test invalid <action> creations
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDEPRUnderAE(self) -> None:
		"""	CREATE <DEPR> under AE -> Fail """
		dct = 	{ 'm2m:depr' : { 
					'rn' : f'{deprRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'thld': 'x'	
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(aeURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.INVALID_CHILD_RESOURCE_TYPE, r)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDEPRWrongRRIFail(self) -> None:
		"""	CREATE <DEPR> with wrong rri -> Fail """
		dct = 	{ 'm2m:depr' : { 
					'rn' : f'{deprRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'thld': 'x'	
					},
					'sfc': True,
					'rri': 'wrong',
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDEPRWrongSBJTFail(self) -> None:
		"""	CREATE <DEPR> with wrong sbjt -> Fail """
		dct = 	{ 'm2m:depr' : { 
					'rn' : f'{deprRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'wrong',
						'thld': 'x'	
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDEPRWrongTHLDTypeFail(self) -> None:
		"""	CREATE <DEPR> with wrong thld type -> Fail """
		dct = 	{ 'm2m:depr' : { 
					'rn' : f'{deprRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'cni',
						'thld': 'x'	
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDEPR(self) -> None:
		"""	CREATE <DEPR>"""
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThanEqual,
						'sbjt': 'cbs',
						'thld': 1
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# DELETE again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	#	Test <dependency> UPDATE
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDEPRWrongTypeFail(self) -> None:
		"""	UPDATE <DEPR> - wrong resource type -> Fail """
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThanEqual,
						'sbjt': 'cbs',
						'thld': 1
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# UPDATE
		dct = 	{ 'm2m:depr' : { 
					'sfc': False,
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.CONTENTS_UNACCEPTABLE, r)

		# DELETE again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDEPRsfc(self) -> None:
		"""	UPDATE <DEPR> - sfc attribute """
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThanEqual,
						'sbjt': 'cbs',
						'thld': 1
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# UPDATE
		dct = 	{ 'm2m:depr' : { 
					'sfc': False,
				}}
		r, rsc = UPDATE(deprURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# DELETE again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDEPRrri(self) -> None:
		"""	UPDATE <DEPR> - rri attribute """
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThanEqual,
						'sbjt': 'cbs',
						'thld': 1
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# UPDATE
		dct = 	{ 'm2m:depr' : { 
					'rri': TestDEPR.cntRI2,
				}}
		r, rsc = UPDATE(deprURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# DELETE again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDEPRevc(self) -> None:
		"""	UPDATE <DEPR> - evc attribute """
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThanEqual,
						'sbjt': 'cbs',
						'thld': 1
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# UPDATE
		dct = 	{ 'm2m:depr' : { 
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'cbs',
						'thld': 1
					},
				}}
		r, rsc = UPDATE(deprURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# DELETE again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)

	#
	#	Test <action> dependency UPDATE
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRdepWrongFail(self) -> None:
		"""	UPDATE <ACTR> - dep attribute with wrong reference -> Fail"""

		# UPDATE
		dct = 	{ 'm2m:actr' : { 
					'dep': [ 'wrong' ],
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRdep(self) -> None:
		"""	UPDATE <ACTR> - dep attribute with correct reference"""

		# Create <DEPR>
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThanEqual,
						'sbjt': 'cbs',
						'thld': 1
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		_ri = findXPath(r, 'm2m:depr/ri')

		# UPDATE <ACTR>
		dct = 	{ 'm2m:actr' : { 
					'dep': [ _ri ],
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/dep'), [ _ri ])

		# DELETE <DEPR> again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	#	Test <action> & <dependency>
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_ACTRDEPRsfcTrue(self) -> None:
		"""	Test ACTR & DEPR - 1 DEPR, sfc = True """

		self._restartWindow()

		# Create <DEPR>
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThanEqual,
						'sbjt': 'cbs',
						'thld': 1
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		_ri = findXPath(r, 'm2m:depr/ri')

		# UPDATE <ACTR>
		dct = 	{ 'm2m:actr' : { 
					'dep': [ _ri ],
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/dep'), [ _ri ])

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> label expected
		self._retrieveAEandCheckLabel(True)
		self._removeAElabel()

		# DELETE <DEPR> again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_ACTRDEPRsfcFalse(self) -> None:
		"""	Test ACTR & DEPR - 1 DEPR, sfc = False """

		self._restartWindow()

		# Create <DEPR>
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThanEqual,
						'sbjt': 'cbs',
						'thld': 1
					},
					'sfc': False,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		_ri = findXPath(r, 'm2m:depr/ri')

		# UPDATE <ACTR>
		dct = 	{ 'm2m:actr' : { 
					'dep': [ _ri ],
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/dep'), [ _ri ])

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> label expected
		self._retrieveAEandCheckLabel(True)
		self._removeAElabel()

		# DELETE <DEPR> again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)




	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_ACTRDEPRsfcTrueMissingConditionFail(self) -> None:
		"""	Test ACTR & DEPR - 1 DEPR, sfc = True, missing condition -> Fail"""

		# Create <DEPR>
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'lbl',
						'thld': ['test']
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		_ri = findXPath(r, 'm2m:depr/ri')

		# UPDATE <ACTR>
		dct = 	{ 'm2m:actr' : { 
					'dep': [ _ri ],
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/dep'), [ _ri ])

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> NO label expected
		self._retrieveAEandCheckLabel(False)

		# DELETE <DEPR> again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_ACTRDEPRsfcTrueAddedCondition(self) -> None:
		"""	Test ACTR & DEPR - 1 DEPR, sfc = True, missing condition first and added later"""

		# Create <DEPR>
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'lbl',
						'thld': ['test']
					},
					'sfc': True,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		_ri = findXPath(r, 'm2m:depr/ri')

		# UPDATE <ACTR>
		dct = 	{ 'm2m:actr' : { 
					'dep': [ _ri ],
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/dep'), [ _ri ])

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> NO label expected
		self._retrieveAEandCheckLabel(False)

		# UPDATE <CNT> with label
		# This should already trigger a successfull <ACTR> and <DEPR> evaluation
		dct = 	{ 'm2m:cnt' : {
					'lbl': ['test'],
				}}
		r, rsc = UPDATE(cntURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Read and test <ae> -> label expected
		testSleep(requestCheckDelay)
		self._retrieveAEandCheckLabel(True)
		self._removeAElabel()

		# UPDATE <CNT> and remove label
		dct = 	{ 'm2m:cnt' : {
					'lbl': None,
				}}
		r, rsc = UPDATE(cntURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# DELETE <DEPR> again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_ACTRDEPRsfcFalseAddedCondition(self) -> None:
		"""	Test ACTR & DEPR - 1 DEPR, sfc = False, missing condition first and added later"""

		# Create <DEPR>
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'lbl',
						'thld': ['test']
					},
					'sfc': False,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		_ri = findXPath(r, 'm2m:depr/ri')

		# UPDATE <ACTR>
		dct = 	{ 'm2m:actr' : { 
					'dep': [ _ri ],
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/dep'), [ _ri ])

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> NO label expected
		self._retrieveAEandCheckLabel(False)

		# UPDATE <CNT> with label
		# This should already trigger a successfull <ACTR> and <DEPR> evaluation
		dct = 	{ 'm2m:cnt' : {
					'lbl': ['test'],
				}}
		r, rsc = UPDATE(cntURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Read and test <ae> -> label expected
		testSleep(requestCheckDelay)
		self._retrieveAEandCheckLabel(True)
		self._removeAElabel()

		# UPDATE <CNT> and remove label
		dct = 	{ 'm2m:cnt' : {
					'lbl': None,
				}}
		r, rsc = UPDATE(cntURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# DELETE <DEPR> again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_ACTRDEPRsfcFalseTwoDependenciesOneChangeFail(self) -> None:
		"""	Test ACTR & DEPR - 2 DEPR, sfc = False, only 1 condition met -> Fail"""

		# Create 2 <DEPR>
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'lbl',
						'thld': ['test']
					},
					'sfc': False,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		_ri = findXPath(r, 'm2m:depr/ri')

		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN+'2',
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThan,
						'sbjt': 'cbs',
						'thld': 0
					},
					'sfc': False,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		_ri2 = findXPath(r, 'm2m:depr/ri')

		# UPDATE <ACTR>
		dct = 	{ 'm2m:actr' : { 
					'dep': [ _ri, _ri2 ],
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/dep'), [ _ri, _ri2 ])

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> NO label expected
		self._retrieveAEandCheckLabel(False)

		# UPDATE <CNT> and remove label
		dct = 	{ 'm2m:cnt' : {
					'lbl': None,
				}}
		r, rsc = UPDATE(cntURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# DELETE <DEPR> again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)
		r, rsc = DELETE(deprURL+'2', TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_ACTRDEPRsfcFalseTwoDependencies(self) -> None:
		"""	Test ACTR & DEPR - 2 DEPR, sfc = False"""

		# Create 2 <DEPR>
		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'lbl',
						'thld': ['test']
					},
					'sfc': False,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		_ri = findXPath(r, 'm2m:depr/ri')

		dct = 	{ 'm2m:depr' : { 
					'rn' : deprRN+'2',
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThan,
						'sbjt': 'cbs',
						'thld': 0
					},
					'sfc': False,
					'rri': TestDEPR.cntRI,
				}}
		r, rsc = CREATE(actrURL, TestDEPR.originator, T.DEPR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		_ri2 = findXPath(r, 'm2m:depr/ri')

		# UPDATE <ACTR>
		dct = 	{ 'm2m:actr' : { 
					'dep': [ _ri, _ri2 ],
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/dep'), [ _ri, _ri2 ])

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> NO label expected
		self._retrieveAEandCheckLabel(False)

		# UPDATE <CNT> with label
		# This should now trigger a successfull <ACTR> and <DEPR> evaluation
		dct = 	{ 'm2m:cnt' : {
					'lbl': ['test'],
				}}
		r, rsc = UPDATE(cntURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# Read and test <ae> -> label expected
		testSleep(requestCheckDelay)
		self._retrieveAEandCheckLabel(True)
		self._removeAElabel()

		# UPDATE <CNT> and remove label
		dct = 	{ 'm2m:cnt' : {
					'lbl': None,
				}}
		r, rsc = UPDATE(cntURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)

		# DELETE <DEPR> again
		r, rsc = DELETE(deprURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)
		r, rsc = DELETE(deprURL+'2', TestDEPR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	#########################################################################

	# Some utility functions first
	def _createCIN(self) -> None:
		dct = 	{ 'm2m:cin': {
			'cnf': 'text/plain:0',
			'con': 'AnyValue'
		}}
		r, rsc = CREATE(cntURL, TestDEPR.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	def _retrieveAEandCheckLabel(self, lblExpected:bool) -> None:
		r, rsc = RETRIEVE(aeURL, TestDEPR.originator)
		self.assertEqual(rsc, RC.OK, r)

		if lblExpected:
			self.assertIsNotNone(lbl := findXPath(r, 'm2m:ae/lbl'))
			self.assertEqual(lbl, [ 'aLabel' ])
		else:
			self.assertIsNone(findXPath(r, 'm2m:ae/lbl'), r)
	

	def _removeAElabel(self) -> None:
		dct = 	{ 'm2m:ae': {
					'lbl': None
		}}
		r, rsc = UPDATE(aeURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/lbl'))
	

	def _restartWindow(self) -> None:
		"""	Update once <ACTR> with periodic mode"""
		dct = 	{ 'm2m:actr' : { 
					'evm': EvalMode.periodic,
				}}
		r, rsc = UPDATE(actrURL, TestDEPR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evm'), EvalMode.periodic)

	


	#########################################################################

def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
		
	# basic tests - CREATE
	addTest(suite, TestDEPR('test_createDEPRUnderAE'))
	addTest(suite, TestDEPR('test_createDEPRWrongRRIFail'))
	addTest(suite, TestDEPR('test_createDEPRWrongSBJTFail'))
	addTest(suite, TestDEPR('test_createDEPRWrongTHLDTypeFail'))
	addTest(suite, TestDEPR('test_createDEPR'))

	# basic tests - UPDATE
	addTest(suite, TestDEPR('test_updateDEPRWrongTypeFail'))
	addTest(suite, TestDEPR('test_updateDEPRsfc'))
	addTest(suite, TestDEPR('test_updateDEPRrri'))
	addTest(suite, TestDEPR('test_updateDEPRevc'))
	
	# update <ACTR> with dependencies
	addTest(suite, TestDEPR('test_updateACTRdepWrongFail'))
	addTest(suite, TestDEPR('test_updateACTRdep'))

	# Test <action> & <dependency>
	addTest(suite, TestDEPR('test_ACTRDEPRsfcTrue'))
	addTest(suite, TestDEPR('test_ACTRDEPRsfcFalse'))
	addTest(suite, TestDEPR('test_ACTRDEPRsfcTrueMissingConditionFail'))
	addTest(suite, TestDEPR('test_ACTRDEPRsfcTrueAddedCondition'))
	addTest(suite, TestDEPR('test_ACTRDEPRsfcFalseAddedCondition'))
	addTest(suite, TestDEPR('test_ACTRDEPRsfcFalseTwoDependenciesOneChangeFail'))
	addTest(suite, TestDEPR('test_ACTRDEPRsfcFalseTwoDependencies'))


	


	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)