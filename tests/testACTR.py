#
#	testACTR.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for Action functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, Permission
from acme.etc.Types import EvalMode, Operation, EvalCriteriaOperator
from init import *



# TODO Add 2. CNT + ACP with NO RETRIEVE access + tests

# TODO check apv originator



class TestACTR(unittest.TestCase):

	ae 			= None
	aeRI		= None
	ae2 		= None
	cnt			= None
	cntRI		= None
	cntRI2		= None
	cntRI3		= None
	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
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

		# create ACP to test access control
		dct = 	{ "m2m:acp": {
			"rn": acpRN,
			"pv": {
				"acr": [ { 	"acor": [ cls.originator ],
							"acop": Permission.ALL - Permission.RETRIEVE
						} ]
			},
			"pvs": { 
				"acr": [ {
					"acor": [ cls.originator],
					"acop": Permission.ALL
				} ]
			},
		}}
		r, rsc = CREATE(aeURL, ORIGINATOR, T.ACP, dct)
		assert rsc == RC.CREATED
		acpRI = findXPath(r, 'm2m:acp/ri')


		# create second CNT with ACP assigned
		dct = 	{ 'm2m:cnt' : { 
				'rn' : cntRN+'2',
				'acpi': [ acpRI ],
			}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.CREATED
		cls.cntRI2 = findXPath(cls.cnt, 'm2m:cnt/ri')

		testCaseEnd('Setup TestACTR')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestACTR')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestACTR')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################


	#
	#	Test invalid <action> creations
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRWrongORCFail(self) -> None:
		"""	Create <ACTR> with wrong ORC -> Fail """
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'thld': 'x'	
					},
					'evm': EvalMode.off,
					'orc': 'todo',
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					} 
				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRNoAccessORCFail(self) -> None:
		"""	Create <ACTR> with ORC and no access -> Fail"""
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'thld': 'x'	
					},
					'evm': EvalMode.off,
					'orc': TestACTR.cntRI2,	# no access
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					} 
				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRNoAccessSRIFail(self) -> None:
		"""	Create <ACTR> with SRI and no access -> Fail"""
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'thld': 'x'	
					},
					'evm': EvalMode.off,
					'sri': TestACTR.cntRI2,	# no access
					'orc': TestACTR.cntRI,	# access
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					} 
				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRWrongEVCAttributeFail(self) -> None:
		"""	Create <ACTR> with wrong EVC attribute -> Fail """
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'wrong': 'x'	# wrong attribute
					},
					'evm': EvalMode.continous,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					} 
				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRInvalidAPVFail(self) -> None:
		"""	Create <ACTR> with invalid APV attribute -> Fail """
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'thld': 'x'	
					},
					'evm': EvalMode.off,
					'orc': TestACTR.cntRI,
					'apv': {
						# empty 
					} 
				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRInvalidFromFail(self) -> None:
		"""	Create <ACTR> with invalid APV.from attribute -> Fail """
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'thld': 'x'	
					},
					'evm': EvalMode.off,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': 'Cwrong',
						'to': TestACTR.cntRI,
						'rqi': '1234',
					} 
				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRInvalidEVMRangeFail(self) -> None:
		"""	Create <ACTR> with invalid EVM attribute range -> Fail """
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'thld': 'x'	
					},
					'evm': 99,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					} 
				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRInvalidEVMandECP1Fail(self) -> None:
		"""	Create <ACTR> with EVM=off attribute and ECP is present-> Fail """
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evm': EvalMode.off,
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'thld': 'x'	
					},
					'ecp': actionPeriod,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					} 
				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRInvalidEVMandECP2Fail(self) -> None:
		"""	Create <ACTR> with EVM=once attribute and ECP is present-> Fail """
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evm': EvalMode.once,
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'rn',
						'thld': 'x'	
					},
					'ecp': 99,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					} 
				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRwithInvalidSBJTFail(self) -> None:
		"""	Create valid <ACTR> with invalid SBJT -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'wrong',
						'thld': 'x'
					},
					'evm': EvalMode.off,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					},
					'sri': TestACTR.cntRI,

				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRwithInvalidTHLDFail(self) -> None:
		"""	Create valid <ACTR> with invalid THLD -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'cni',
						'thld': -99		# should be nonNegativeInteger
					},
					'evm': EvalMode.off,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					},
					'sri': TestACTR.cntRI,

				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRwithInvalidOPTRFail(self) -> None:
		"""	Create valid <ACTR> with invalid OPTR -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : f'{actrRN}wrong',
					'evc' : { 
						'optr': EvalCriteriaOperator.lessThan,
						'sbjt': 'lbl',
						'thld': [ 'aLabel' ]
					},
					'evm': EvalMode.off,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					},
					'sri': TestACTR.cntRI,

				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

	#
	#	Valid <action> creation
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRnoSRI(self) -> None:
		"""	Create valid <ACTR> with no SRI"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : actrRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'lbl',
						'thld': [ 'aLabel' ]
					},
					'evm': EvalMode.off,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					} 
				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evm'), EvalMode.off, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/optr'), EvalCriteriaOperator.equal, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/sbjt'), 'lbl', r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/thld'), [ 'aLabel' ], r)
		self.assertEqual(findXPath(r, 'm2m:actr/orc'), TestACTR.cntRI, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/op'), Operation.RETRIEVE, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/fr'), TestACTR.originator, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/to'), TestACTR.cntRI, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/rqi'), '1234', r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRwithSRI(self) -> None:
		"""	Create valid <ACTR> with SRI"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : actrRN+'sri',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'cni',
						'thld': 3
					},
					'evm': EvalMode.off,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					},
					'sri': TestACTR.cntRI,

				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evm'), EvalMode.off, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/optr'), EvalCriteriaOperator.equal, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/sbjt'), 'cni', r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/thld'), 3, r)
		self.assertEqual(findXPath(r, 'm2m:actr/orc'), TestACTR.cntRI, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/op'), Operation.RETRIEVE, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/fr'), TestACTR.originator, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/to'), TestACTR.cntRI, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/rqi'), '1234', r)
		self.assertEqual(findXPath(r, 'm2m:actr/sri'), TestACTR.cntRI, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRwithSRIOnce(self) -> None:
		"""	Create valid <ACTR> with SRI and once mode"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : actrRN+'sriOnce',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'cni',
						'thld': 3
					},
					'evm': EvalMode.once,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					},
					'sri': TestACTR.cntRI,

				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evm'), EvalMode.once, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/optr'), EvalCriteriaOperator.equal, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/sbjt'), 'cni', r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/thld'), 3, r)
		self.assertEqual(findXPath(r, 'm2m:actr/orc'), TestACTR.cntRI, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/op'), Operation.RETRIEVE, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/fr'), TestACTR.originator, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/to'), TestACTR.cntRI, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/rqi'), '1234', r)
		self.assertEqual(findXPath(r, 'm2m:actr/sri'), TestACTR.cntRI, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRwithSRIPeriodic(self) -> None:
		"""	Create valid <ACTR> with SRI and periodic mode"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : actrRN+'sriPeriodic',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'cni',
						'thld': 3
					},
					'ecp': actionPeriod,
					'evm': EvalMode.periodic,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					},
					'sri': TestACTR.cntRI,

				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evm'), EvalMode.periodic, r)
		self.assertEqual(findXPath(r, 'm2m:actr/ecp'), actionPeriod, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/optr'), EvalCriteriaOperator.equal, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/sbjt'), 'cni', r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/thld'), 3, r)
		self.assertEqual(findXPath(r, 'm2m:actr/orc'), TestACTR.cntRI, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/op'), Operation.RETRIEVE, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/fr'), TestACTR.originator, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/to'), TestACTR.cntRI, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/rqi'), '1234', r)
		self.assertEqual(findXPath(r, 'm2m:actr/sri'), TestACTR.cntRI, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createACTRwithSRIContinuous(self) -> None:
		"""	Create valid <ACTR> with SRI and continious mode"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'rn' : actrRN+'sriContinuous',
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'cni',
						'thld': 3
					},
					'ecp': 10,
					'evm': EvalMode.continous,
					'orc': TestACTR.cntRI,
					'apv': {
						'op': Operation.RETRIEVE,
						'fr': TestACTR.originator,
						'to': TestACTR.cntRI,
						'rqi': '1234',
					},
					'sri': TestACTR.cntRI,

				}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evm'), EvalMode.continous, r)
		self.assertEqual(findXPath(r, 'm2m:actr/ecp'), 10, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/optr'), EvalCriteriaOperator.equal, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/sbjt'), 'cni', r)
		self.assertEqual(findXPath(r, 'm2m:actr/evc/thld'), 3, r)
		self.assertEqual(findXPath(r, 'm2m:actr/orc'), TestACTR.cntRI, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/op'), Operation.RETRIEVE, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/fr'), TestACTR.originator, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/to'), TestACTR.cntRI, r)
		self.assertEqual(findXPath(r, 'm2m:actr/apv/rqi'), '1234', r)
		self.assertEqual(findXPath(r, 'm2m:actr/sri'), TestACTR.cntRI, r)


	#
	#	Update <action>
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTROnceECPFail(self) -> None:
		"""	Update once <ACTR> with once mode and ECP -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'evm': EvalMode.once,
					'ecp': 10,
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRContinuousWithOnceFail(self) -> None:
		"""	Update continous <ACTR> with once mode -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'evm': EvalMode.once,
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriContinuous"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRonceWrongSRIFail(self) -> None:
		"""	Update once <ACTR> with wrong SRI -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'sri': 'wrong',
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRonceWrongORCFail(self) -> None:
		"""	Update once <ACTR> with wrong ORC -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'orc': 'wrong',
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRonceWrongSBJTFail(self) -> None:
		"""	Update once <ACTR> with wrong EVC/SBJT -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'evc' : { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'wrong',
						'thld': 3
					},
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRonceSRIWrongSBJTFail(self) -> None:
		"""	Update once <ACTR> with correct new SRI and wrong EVC/SBJT -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'sri': TestACTR.aeRI,
					'evc': { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'wrong',
						'thld': 3
					},
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRonceNewSRIOldWrongSBJTFail(self) -> None:
		"""	Update once <ACTR> with correct new SRI and old now wrong EVC/SBJT -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'sri': TestACTR.aeRI,
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRonceNewEVCWrongTHLDFail(self) -> None:
		"""	Update once <ACTR> with new EVC and wrong EVC/THLD -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'evc': { 
						'optr': EvalCriteriaOperator.equal,
						'sbjt': 'cni',
						'thld': "wrong"
					},
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRonceORCNullFail(self) -> None:
		"""	Update once <ACTR> with with a NULL ORC -> Fail"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'orc': None,
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRConceWithOnce(self) -> None:
		"""	Update once <ACTR> with once mode"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'evm': EvalMode.once,
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evm'), EvalMode.once)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRConceWithPeriodic(self) -> None:
		"""	Update once <ACTR> with periodic mode"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'evm': EvalMode.periodic,
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evm'), EvalMode.periodic)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRConceWithContinuous(self) -> None:
		"""	Update once <ACTR> with contiuous mode"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'evm': EvalMode.continous,
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evm'), EvalMode.continous)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateACTRConceWithOff(self) -> None:
		"""	Update once <ACTR> with off mode"""
		self.assertIsNotNone(TestACTR.ae)
		dct = 	{ 'm2m:actr' : { 
					'evm': EvalMode.off,
				}}
		r, rsc = UPDATE(f'{aeURL}/{actrRN+"sriOnce"}', TestACTR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:actr/evm'), EvalMode.off)


	#
	#	Delete <action>
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACTRnoSRI(self) -> None:
		"""	Delete <ACTR> with no SRI"""
		self.assertIsNotNone(TestACTR.ae)
		r, rsc = DELETE(f'{aeURL}/{actrRN}', TestACTR.originator)	# 
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACTRwithSRI(self) -> None:
		"""	Delete <ACTR> with SRI"""
		self.assertIsNotNone(TestACTR.ae)
		r, rsc = DELETE(f'{aeURL}/{actrRN}sri', TestACTR.originator)	# 
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACTRwithSRIOnce(self) -> None:
		"""	Delete <ACTR> with SRI and once mode"""
		self.assertIsNotNone(TestACTR.ae)
		r, rsc = DELETE(f'{aeURL}/{actrRN}sriOnce', TestACTR.originator)	# 
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACTRwithSRIPeriodic(self) -> None:
		"""	Delete <ACTR> with SRI and periodic mode"""
		self.assertIsNotNone(TestACTR.ae)
		r, rsc = DELETE(f'{aeURL}/{actrRN}sriPeriodic', TestACTR.originator)	# 
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteACTRwithSRIContinuous(self) -> None:
		"""	Create valid <ACTR> with SRI and continuous mode"""
		self.assertIsNotNone(TestACTR.ae)
		r, rsc = DELETE(f'{aeURL}/{actrRN}sriContinuous', TestACTR.originator)	# 
		self.assertEqual(rsc, RC.DELETED, r)





	#
	#	Test parent <actions>
	#

	cntURL3 = None

	# Some utility functions first
	def _createCIN(self) -> None:
		dct = 	{ 'm2m:cin': {
			'cnf': 'text/plain:0',
			'con': 'AnyValue'
		}}
		r, rsc = CREATE(TestACTR.cntURL3, TestACTR.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	def _retrieveAEandCheckLabel(self, lblExpected:bool) -> None:
		r, rsc = RETRIEVE(aeURL, TestACTR.originator)
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
		r, rsc = UPDATE(aeURL, TestACTR.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/lbl'))
	
	
	def _checkActrResponse(self) -> None:
		r, rsc = RETRIEVE(f'{TestACTR.cntURL3}/{actrRN}', TestACTR.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(air := findXPath(r, 'm2m:actr/air'), r)
		self.assertEqual(findXPath(air, 'rsc'), RC.UPDATED, r)
		self.assertEqual(findXPath(air, 'pc/m2m:ae/lbl'), [ 'aLabel' ], r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testACTROnce(self) -> None:
		"""	Create and test <ACTR> under a <CNT> in once mode"""

		TestACTR.cntURL3 = f'{aeURL}/{cntRN+"3"}'

		# create <cnt>
		dct:JSON = 	{ 'm2m:cnt' : { 
					'rn' : cntRN+'3'
			}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		TestACTR.cntRI3 = findXPath(r, 'm2m:cnt/ri')

		# create <actr>
		dct = 	{ 'm2m:actr' : { 
					'rn' : actrRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThan,
						'sbjt': 'cni',
						'thld': 1
					},
					'evm': EvalMode.once,
					'orc': TestACTR.aeRI,
					'apv': {
						'op': Operation.UPDATE,
						'fr': TestACTR.originator,
						'to': TestACTR.aeRI,
						'rqi': '1234',
						'rvi': RELEASEVERSION,
						'pc': { 
							'm2m:ae': {
								'lbl': [ 'aLabel' ]
						}},
					},
					'sri': TestACTR.cntRI3,

				}}
		r, rsc = CREATE(TestACTR.cntURL3, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> NO label expected
		self._retrieveAEandCheckLabel(False)

		# create 2nd <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> label expected
		self._retrieveAEandCheckLabel(True)
		self._removeAElabel()

		# Read and test <actr>
		self._checkActrResponse()

		# remove <cnt> & <actr>
		r, rsc = DELETE(TestACTR.cntURL3, TestACTR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testACTRParentOnce(self) -> None:
		"""	Create and test <ACTR> under a <CNT> in once mode and parent subject"""

		TestACTR.cntURL3 = f'{aeURL}/{cntRN+"3"}'

		# create <cnt>
		dct:JSON = 	{ 'm2m:cnt' : { 
					'rn' : cntRN+'3'
			}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		TestACTR.cntRI3 = findXPath(r, 'm2m:cnt/ri')

		# create <actr>
		dct = 	{ 'm2m:actr' : { 
					'rn' : actrRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThan,
						'sbjt': 'cni',
						'thld': 1
					},
					'evm': EvalMode.once,
					'orc': TestACTR.aeRI,
					'apv': {
						'op': Operation.UPDATE,
						'fr': TestACTR.originator,
						'to': TestACTR.aeRI,
						'rqi': '1234',
						'rvi': RELEASEVERSION,
						'pc': { 
							'm2m:ae': {
								'lbl': [ 'aLabel' ]
						}},
					},
				}}
		r, rsc = CREATE(TestACTR.cntURL3, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> NO label expected
		self._retrieveAEandCheckLabel(False)

		# create 2nd <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> label expected
		self._retrieveAEandCheckLabel(True)
		self._removeAElabel()

		# Read and test <actr>
		self._checkActrResponse()

		# remove <cnt> & <actr>
		r, rsc = DELETE(TestACTR.cntURL3, TestACTR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testACTRContinuous(self) -> None:
		"""	Create and test <ACTR> under a <CNT> in continuous mode"""

		TestACTR.cntURL3 = f'{aeURL}/{cntRN+"3"}'

		# create <cnt>
		dct:JSON = 	{ 'm2m:cnt' : { 
					'rn' : cntRN+'3'
			}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		TestACTR.cntRI3 = findXPath(r, 'm2m:cnt/ri')

		# create <actr>
		dct = 	{ 'm2m:actr' : { 
					'rn' : actrRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThan,
						'sbjt': 'cni',
						'thld': 1
					},
					'evm': EvalMode.continous,
					'ecp': 2,
					'orc': TestACTR.aeRI,
					'apv': {
						'op': Operation.UPDATE,
						'fr': TestACTR.originator,
						'to': TestACTR.aeRI,
						'rqi': '1234',
						'rvi': RELEASEVERSION,
						'pc': { 
							'm2m:ae': {
								'lbl': [ 'aLabel' ]
						}},
					},
					'sri': TestACTR.cntRI3,

				}}
		r, rsc = CREATE(TestACTR.cntURL3, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> NO label expected
		self._retrieveAEandCheckLabel(False)

		# create 2nd <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> label expected, and 
		self._retrieveAEandCheckLabel(True)
		self._checkActrResponse()	# Read and test <actr>
		self._removeAElabel()		# Remove lbl

		# create 3nd <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> NO label expected (no continuous)
		self._retrieveAEandCheckLabel(False)

		# remove <cnt> & <actr>
		r, rsc = DELETE(TestACTR.cntURL3, TestACTR.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testACTRPeriodic(self) -> None:
		"""	Create and test <ACTR> under a <CNT> in periodic mode"""

		TestACTR.cntURL3 = f'{aeURL}/{cntRN+"3"}'

		# create <cnt>
		dct:JSON = 	{ 'm2m:cnt' : { 
					'rn' : cntRN+'3'
			}}
		r, rsc = CREATE(aeURL, TestACTR.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		TestACTR.cntRI3 = findXPath(r, 'm2m:cnt/ri')

		# create <actr>
		dct = 	{ 'm2m:actr' : { 
					'rn' : actrRN,
					'evc' : { 
						'optr': EvalCriteriaOperator.greaterThan,
						'sbjt': 'cni',
						'thld': 0	# react immediately
					},
					'evm': EvalMode.periodic,
					'ecp': requestCheckDelay * 4 * 1000,	# 2 seconds
					'orc': TestACTR.aeRI,
					'apv': {
						'op': Operation.UPDATE,
						'fr': TestACTR.originator,
						'to': TestACTR.aeRI,
						'rqi': '1234',
						'rvi': RELEASEVERSION,
						'pc': { 
							'm2m:ae': {
								'lbl': [ 'aLabel' ]
						}},
					},
					'sri': TestACTR.cntRI3,

				}}
		r, rsc = CREATE(TestACTR.cntURL3, TestACTR.originator, T.ACTR, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		#
		#	Test 2 events within the same period
		#

		# create 1st <cin>
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> Label expected
		self._retrieveAEandCheckLabel(True)
		self._removeAElabel()		# Remove lbl

		# create 2nd <cin> within same period
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> NO Label expected
		self._retrieveAEandCheckLabel(False)
		
		#
		#	Next event in the next period
		#

		# Wait until next perio
		testSleep(requestCheckDelay * 2)

		# create 3rd <cin> within next period
		self._createCIN()
		testSleep(requestCheckDelay)

		# Read and test <ae> -> Label expected
		self._retrieveAEandCheckLabel(True)

		# remove <cnt> & <actr>
		r, rsc = DELETE(TestACTR.cntURL3, TestACTR.originator)
		self.assertEqual(rsc, RC.DELETED, r)



# TODO test with parent subject
# TODO test action priorities


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
		
	# basic tests
	addTest(suite, TestACTR('test_createACTRWrongORCFail'))
	addTest(suite, TestACTR('test_createACTRNoAccessORCFail'))
	addTest(suite, TestACTR('test_createACTRNoAccessSRIFail'))
	addTest(suite, TestACTR('test_createACTRWrongEVCAttributeFail'))
	addTest(suite, TestACTR('test_createACTRInvalidAPVFail'))
	addTest(suite, TestACTR('test_createACTRInvalidFromFail'))
	addTest(suite, TestACTR('test_createACTRInvalidEVMRangeFail'))
	addTest(suite, TestACTR('test_createACTRInvalidEVMandECP1Fail'))
	addTest(suite, TestACTR('test_createACTRInvalidEVMandECP2Fail'))
	addTest(suite, TestACTR('test_createACTRwithInvalidSBJTFail'))
	addTest(suite, TestACTR('test_createACTRwithInvalidTHLDFail'))
	addTest(suite, TestACTR('test_createACTRwithInvalidOPTRFail'))

	# create tests
	addTest(suite, TestACTR('test_createACTRnoSRI'))
	addTest(suite, TestACTR('test_createACTRwithSRI'))
	addTest(suite, TestACTR('test_createACTRwithSRIOnce'))
	addTest(suite, TestACTR('test_createACTRwithSRIPeriodic'))
	addTest(suite, TestACTR('test_createACTRwithSRIContinuous'))

	# update tests
	addTest(suite, TestACTR('test_updateACTROnceECPFail'))
	addTest(suite, TestACTR('test_updateACTRContinuousWithOnceFail'))
	addTest(suite, TestACTR('test_updateACTRonceWrongSRIFail'))
	addTest(suite, TestACTR('test_updateACTRonceWrongORCFail'))
	addTest(suite, TestACTR('test_updateACTRonceWrongSBJTFail'))
	addTest(suite, TestACTR('test_updateACTRonceSRIWrongSBJTFail'))
	addTest(suite, TestACTR('test_updateACTRonceNewSRIOldWrongSBJTFail'))
	addTest(suite, TestACTR('test_updateACTRonceNewEVCWrongTHLDFail'))
	addTest(suite, TestACTR('test_updateACTRonceORCNullFail'))
	addTest(suite, TestACTR('test_updateACTRConceWithOnce'))
	addTest(suite, TestACTR('test_updateACTRConceWithPeriodic'))
	addTest(suite, TestACTR('test_updateACTRConceWithContinuous'))
	addTest(suite, TestACTR('test_updateACTRConceWithOff'))


	# delete tests
	addTest(suite, TestACTR('test_deleteACTRnoSRI'))
	addTest(suite, TestACTR('test_deleteACTRwithSRI'))
	addTest(suite, TestACTR('test_deleteACTRwithSRIOnce'))
	addTest(suite, TestACTR('test_deleteACTRwithSRIPeriodic'))
	addTest(suite, TestACTR('test_deleteACTRwithSRIContinuous'))

	# parent subject
	addTest(suite, TestACTR('test_testACTROnce'))
	addTest(suite, TestACTR('test_testACTRParentOnce'))
	addTest(suite, TestACTR('test_testACTRContinuous'))
	addTest(suite, TestACTR('test_testACTRPeriodic'))

	#addTest(suite, TestACTR('test_createCIN'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)