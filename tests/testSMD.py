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
rdfxml_1 = """<?xml version="1.0" encoding="utf-8"?>
<rdf:RDF
xmlns:m2m="https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#"
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
>
<rdf:Description rdf:about="http://www.XYZ.com/WashingMachines#XYZ_CoolWASH_RETRIEVE-MonitoringFunction-WashingMachineStatus_RESOURCE_ID">
<rdf:type rdf:resource="https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#Operation"/>
<rdf:type rdf:resource="https://saref.etsi.org/core/GetCommand"/>
<m2m:oneM2MTargetURI>/myWashingMachine/status/la</m2m:oneM2MTargetURI>
<m2m:oneM2MMethod>RETRIEVE</m2m:oneM2MMethod>
</rdf:Description>
</rdf:RDF>"""
rdfxml_1_B64 = base64.b64encode(rdfxml_1.encode('UTF-8')).decode('UTF-8')


rdfxml_2 = """<?xml version="1.0" encoding="utf-8"?>
<rdf:RDF
xmlns:m2m="https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#"
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
>
<rdf:Description rdf:about="http://www.XYZ.com/WashingMachines#XYZ_CoolWASH_CREATE-MonitoringFunction-WashingMachineStatus_RESOURCE_ID">
<rdf:type rdf:resource="https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#Operation"/>
<rdf:type rdf:resource="https://saref.etsi.org/core/GetCommand"/>
<m2m:oneM2MTargetURI>/myWashingMachine/status/la</m2m:oneM2MTargetURI>
<m2m:oneM2MMethod>CREATE</m2m:oneM2MMethod>
</rdf:Description>
</rdf:RDF>"""
rdfxml_2_B64 = base64.b64encode(rdfxml_2.encode('UTF-8')).decode('UTF-8')


# Queries

query_query = """PREFIX sn:<http://www.XYZ.com/WashingMachines#XYZ_Cool>  
PREFIX m2m: <https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#>  
select  ?wm ?res where { 
    ?wm a m2m:Operation .
    ?wm m2m:oneM2MTargetURI ?res
    FILTER(contains(?res, "myWashingMachine"))
}"""
query_query_URL = urllib.parse.quote(query_query)

query_discovery =  """
PREFIX sn:<http://www.XYZ.com/WashingMachines#XYZ_Cool>
PREFIX m2m:<https://git.onem2m.org/MAS/BaseOntology/raw/master/base_ontology.owl#>
select  ?wm ?res where {
	?wm m2m:oneM2MMethod ?res
	FILTER(contains(?res, "RETRIEVE"))
}"""
query_discovery_URL = urllib.parse.quote(query_discovery)


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
					'api' : APPID,
				 	'rr'  : True,
				 	'srv' : [ RELEASEVERSION ],
					'poa' : [ NOTIFICATIONSERVER ],
				}}
		cls.ae, rsc = CREATE(cseURL, ORIGINATORSelfReg, T.AE, dct)	# AE to work under
		assert rsc == RC.CREATED, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		testCaseEnd('Setup TestCRS')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
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
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSMDdspNotBase64Fail(self) -> None:
		"""	CREATE <SMD> with DSP not encoded as base64 -> FAIL"""
		dct = 	{ 'm2m:smd' : { 
					'rn' : 'failSMD',
					'dcrp' : 2,
					'dsp' : 'wrong',
				}}
		r, rsc = CREATE(aeURL, TestSMD.originator, T.SMD, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


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
					'dsp' : rdfxml_1_B64,
				}}
		r, rsc = CREATE(aeURL, TestSMD.originator, T.SMD, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		# TODO optional self.assertIsNotNone(findXPath(r, 'm2m:smd/svd'))
		# TODO optuional self.assertIsNotNone(findXPath(r, 'm2m:smd/vlde'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSMD(self) -> None:
		"""	DELETE <SMD>"""
		r, rsc = DELETE(smdURL, TestSMD.originator)
		self.assertEqual(rsc, RC.DELETED, r)


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
		self.assertEqual(rsc, RC.CREATED, r)

		# Try to create SMD under ACP
		dct = 	{ 'm2m:smd' : { 
					'rn' : smdRN,
					'dcrp' : 2,
					#'dsp' : 'Y29ycmVjdA==',
				}}
		r, rsc = CREATE(f'{aeURL}/{acpRN}', TestSMD.originator, T.SMD, dct)
		self.assertEqual(rsc, RC.INVALID_CHILD_RESOURCE_TYPE, r)

		# Delete ACP
		r, rsc = DELETE(f'{aeURL}/{acpRN}', TestSMD.originator)
		self.assertEqual(rsc, RC.DELETED, r)


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
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSMDwithVLDEtrue(self) -> None:
		"""	UPDATE <SMD> with VLDE set to True"""
		dct = 	{ 'm2m:smd' : { 
					'vlde' : True,
				}}
		r, rsc = UPDATE(smdURL, TestSMD.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:smd/vlde'))
		self.assertIsInstance(findXPath(r, 'm2m:smd/vlde'), bool)
		self.assertTrue(findXPath(r, 'm2m:smd/vlde'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateSMDwithVLDEfalse(self) -> None:
		"""	UPDATE <SMD> with VLDE set to False"""
		dct = 	{ 'm2m:smd' : { 
					'vlde' : False,
				}}
		r, rsc = UPDATE(smdURL, TestSMD.originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:smd/vlde'))
		self.assertIsInstance(findXPath(r, 'm2m:smd/vlde'), bool)
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
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_semanticQueryOnlySQIFail(self) -> None:
		"""	Semantic query with only SQI -> Fail"""
		r, rsc = RETRIEVE(f'{aeURL}?sqi=true', TestSMD.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_semanticQueryOnlySMFFail(self) -> None:
		"""	Semantic query with only SMF -> Fail"""
		r, rsc = RETRIEVE(f'{aeURL}?smf={query_query_URL}', TestSMD.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_semanticQueryAsDiscoveryFail(self) -> None:
		"""	Semantic query as Discovery -> Fail"""
		r, rsc = RETRIEVE(f'{aeURL}?fu=1&sqi=true&rcn={int(RCN.semanticContent)}&smf={query_query_URL}', TestSMD.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_semanticQuery(self) -> None:
		"""	Semantic query as Discovery"""
		r, rsc = RETRIEVE(f'{aeURL}?sqi=true&rcn={int(RCN.semanticContent)}&smf={query_query_URL}', TestSMD.originator)
		# r, rsc = RETRIEVE(f'{aeURL}?sqi=true&rcn={int(RCN.semanticContent)}&smf={query_discovery_URL}', TestSMD.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(qres := findXPath(r, 'm2m:qres'))
		self.assertTrue(qres.startswith('<?xml'), qres)
		self.assertTrue(qres.endswith('</sparql>'), qres)

	#########################################################################

# TODO check not-present of semanticOpExec when RETRIEVE

# TODO Update of smd
# TODO Delete of smd
# TODO non-failing semantic discovery



def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
	
	# General attribute test cases
	addTest(suite, TestSMD('test_createSMDdcrpIRIFail'))
	addTest(suite, TestSMD('test_createSMDdspNotBase64Fail'))

	# Create tests
	addTest(suite, TestSMD('test_createSMDdspBase64'))
	addTest(suite, TestSMD('test_deleteSMD'))
	addTest(suite, TestSMD('test_createSMDunderACPFail'))

	# Update tests
	addTest(suite, TestSMD('test_createSMDdspBase64'))
	addTest(suite, TestSMD('test_updateSMDwithSOEandDSPFail'))
	addTest(suite, TestSMD('test_updateSMDwithVLDEtrue'))
	addTest(suite, TestSMD('test_updateSMDwithVLDEfalse'))

	# Semantic query tests
	addTest(suite, TestSMD('test_semanticQueryOnlyRCNFail'))
	addTest(suite, TestSMD('test_semanticQueryOnlySQIFail'))
	addTest(suite, TestSMD('test_semanticQueryOnlySMFFail'))
	addTest(suite, TestSMD('test_semanticQueryAsDiscoveryFail'))
	addTest(suite, TestSMD('test_semanticQuery'))

	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()

if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
