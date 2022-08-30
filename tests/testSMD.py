#
#	testSMD.py
#
#	(c) 2022 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for SMD functionality 
#

import unittest, sys, base64, urllib.parse
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import DesiredIdentifierResultType as DRT, NotificationEventType as NET, ResourceTypes as T, ResponseStatusCode as RC
from acme.etc.Types import ResultContentType as RCN, Permission
from init import *


#
#	Semantic descriptors & queries
#
rdfxml = """<?xml version="1.0" encoding="utf-8"?>
<rdf:RDF
   xmlns:m2m="https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
>
  <rdf:Description rdf:about="http://www.XYZ.com/WashingMachines#XYZ_CoolWASH_XYZ-MonitoringFunction-WashingMachineStatus_RESOURCE_ID">
    <rdf:type rdf:resource="https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#Operation"/>
    <rdf:type rdf:resource="https://saref.etsi.org/core/GetCommand"/>
    <m2m:oneM2MTargetURI>/myWashingMachine/status/la</m2m:oneM2MTargetURI>
    <m2m:oneM2MMethod>RETRIEVE</m2m:oneM2MMethod>
  </rdf:Description>
  <rdf:Description rdf:about="http://www.XYZ.com/WashingMachines#XYZ_CoolWASH_XYZ-StartStopFunction-TOGGLE_Command_RESOURCE_ID">
    <rdf:type rdf:resource="https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#Operation"/>
    <rdf:type rdf:resource="https://saref.etsi.org/core/ToggleCommand"/>
    <m2m:oneM2MTargetURI>/myWashingMachine/command</m2m:oneM2MTargetURI>
    <m2m:hasDataRestriction>TOGGLE</m2m:hasDataRestriction>
    <m2m:oneM2MMethod>CREATE</m2m:oneM2MMethod>
  </rdf:Description>
  <rdf:Description rdf:about="http://www.XYZ.com/WashingMachines#XYZ_CoolWASH_XYZ-StartStopFunction-ON_Command_RESOURCE_ID">
    <rdf:type rdf:resource="https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#Operation"/>
    <rdf:type rdf:resource="https://saref.etsi.org/core/OnCommand"/>
    <m2m:oneM2MTargetURI>/myWashingMachine/command</m2m:oneM2MTargetURI>
    <m2m:hasDataRestriction>ON</m2m:hasDataRestriction>
    <m2m:oneM2MMethod>CREATE</m2m:oneM2MMethod>
  </rdf:Description>
  <rdf:Description rdf:about="http://www.XYZ.com/WashingMachines#XYZ_CoolWASH_XYZ-StartStopFunction-OFF_Command_RESOURCE_ID">
    <rdf:type rdf:resource="https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#Operation"/>
    <rdf:type rdf:resource="https://saref.etsi.org/core/OffCommand"/>
    <m2m:oneM2MTargetURI>/myWashingMachine/command</m2m:oneM2MTargetURI>
    <m2m:hasDataRestriction>OFF</m2m:hasDataRestriction>
    <m2m:oneM2MMethod>CREATE</m2m:oneM2MMethod>
  </rdf:Description>
</rdf:RDF>"""
rdfxmlB64 = base64.b64encode(rdfxml.encode('UTF-8')).decode('UTF-8')

query = """PREFIX sn:<http://www.XYZ.com/WashingMachines#XYZ_Cool>  
PREFIX m2m: <https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#>  
PREFIX saref: <https://saref.etsi.org/core/>  
select  ?wm ?res where { 
    ?wm a m2m:Operation .
    ?wm m2m:oneM2MTargetURI ?res
    FILTER(contains(?res, "myWashingMachine"))
}"""
queryURL = urllib.parse.quote(query)

###############################################################################

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
					'dcrp' : 4,
					'dsp' : rdfxmlB64,
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
	def test_updateSMDwithVLDEtrue(self) -> None:
		"""	UPDATE <SMD> with VLDE set to True"""
		dct = 	{ 'm2m:smd' : { 
					'vlde' : True,
				}}
		r, rsc = UPDATE(smdURL, TestSMD.originator, dct)
		self.assertEqual(rsc, RC.updated, r)
		self.assertIsNotNone(findXPath(r, 'm2m:smd/vlde'))
		self.assertTrue(findXPath(r, 'm2m:smd/vlde'))


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
	#
	#	Semantic query tests
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_semanticQueryOnlyRCNFail(self) -> None:
		"""	Semantic query with only RCN -> Fail"""
		r, rsc = RETRIEVE(f'{aeURL}?rcn={int(RCN.semanticContent)}', TestSMD.originator)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_semanticQueryOnlySQIFail(self) -> None:
		"""	Semantic query with only SQI -> Fail"""
		r, rsc = RETRIEVE(f'{aeURL}?sqi=1', TestSMD.originator)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_semanticQueryOnlySMFFail(self) -> None:
		"""	Semantic query with only SMF -> Fail"""
		r, rsc = RETRIEVE(f'{aeURL}?smf={queryURL}', TestSMD.originator)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_semanticQueryAsDiscovery(self) -> None:
		"""	Semantic query as Discovery -> Fail"""
		r, rsc = RETRIEVE(f'{aeURL}?fu=1&sqi=1&rcn={int(RCN.semanticContent)}&smf={queryURL}', TestSMD.originator)
		self.assertEqual(rsc, RC.badRequest, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_semanticQuery(self) -> None:
		"""	Semantic query as Discovery"""
		r, rsc = RETRIEVE(f'{aeURL}?sqi=1&rcn={int(RCN.semanticContent)}&smf={queryURL}', TestSMD.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(qres := findXPath(r, 'm2m:qres'))
		self.assertTrue(qres.startswith('<?xml'), qres)
		self.assertTrue(qres.endswith('</sparql>'), qres)

	#########################################################################

# TODO check not-present of semanticOpExec when RETRIEVE

# TODO Update of smd
# TODO Delete of smd



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
	suite.addTest(TestSMD('test_updateSMDwithVLDEtrue'))
	suite.addTest(TestSMD('test_updateSMDwithVLDEfalse'))

	# Semantic query tests
	suite.addTest(TestSMD('test_semanticQueryOnlyRCNFail'))
	suite.addTest(TestSMD('test_semanticQueryOnlySQIFail'))
	suite.addTest(TestSMD('test_semanticQueryOnlySMFFail'))
	suite.addTest(TestSMD('test_semanticQueryAsDiscovery'))
	suite.addTest(TestSMD('test_semanticQuery'))

	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(2, True)
	sys.exit(errors)
