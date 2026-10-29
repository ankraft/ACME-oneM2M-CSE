#
#	testRemote_ACP.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for referencing an <ACP> resource hosted on a remote CSE via "acpi"
#
#	The resource structures used in these tests are:
#
#	Remote CSE:
#		<root>
#			<acpRN> - Remote ACP for AE access. This allows the local CSE to access the remote AEs.
#			<acp1RN> - Remote ACP for specific originators.
#			<acp2RN> - Remote ACP with wildcard rules.
#			<aeRN>RemoteAE1 - Remote AE 1 on the remote CSE. Uses 
#			<aeRN>RemoteAE2 - Remote AE 2 on the remote CSE.
#
#	Local CSE:
#		<root>
#			<ae1RN> - Local AE on the local CSE.
#				<cnt1RN> - Local CNT 1 under the local AE.
#				<cnt2RN> - Local CNT 2 under the local AE.



import unittest, sys
if '..' not in sys.path:
	sys.path.insert(0, '..')
from acmecse.etc.Types import Permission, ResourceTypes as T, ResponseStatusCode as RC
from init import *

acp1RN = f'{acpRN}Remote1'
acp2RN = f'{acpRN}Remote2'
ae1RN  = f'{aeRN}RemoteACP'
cnt1RN = f'{cntRN}RemoteACP1'
cnt2RN = f'{cntRN}RemoteACP2'

# Plain originators used as exact-match acor entries. These don't need to be
# registered anywhere: ACP matching only compares the "From" string against
# the acor list, so any string works for the exact-match / multi-rule test.
remoteAE1Originator = 'CremoteAcpAE1'
remoteAE2Originator = 'CremoteAcpAE2'

# Originators used for the ID-form tests below, expressed in SP-relative form
# as they would appear to the local CSE if they genuinely originated from an
# AE registered on the remote CSE (REMOTECSEID). Sent as-is as the "From"
# value - no actual registration on the remote CSE is required for this.
wildcardSPRelativeOriginator  = f'{REMOTECSEID}/CwildSP1'
wildcardCSERelativeOriginator = f'{REMOTECSEID}/CwildCSE1'

acpORIGINATOR = 'testOriginator'


class TestRemote_ACP(unittest.TestCase):

	ae: JSON|None = None
	acp: JSON|None = None
	originator: str|None = None
	remoteAcpRI: str|None = None
	remoteAcpRIAEAccess: str|None = None
	remoteAcp1Ri: str|None = None
	remoteAcp2Ri: str|None = None

	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestRemote_ACP')
		dct: JSON


		# Create a remote ACP resource to allow the hosting CSE to access the AE resources

		dct = 	{ 'm2m:acp' : {
					'rn': acpRN,
					'pv': {
						'acr': [ { 'acor': [ CSEID ], 'acop': Permission.ALL } ]
					},
					'pvs': {
						'acr': [ { 'acor': [ REMOTEORIGINATOR, CSEID ], 'acop': Permission.ALL } ]
					}
				}}
		r, rsc = CREATE(REMOTEcseURL, REMOTEORIGINATOR, T.ACP, dct)
		assert rsc == RC.CREATED, f'cannot create remote ACP: {r}'
		cls.remoteAcpRIAEAccess = findXPath(r, 'm2m:acp/ri')


		# Create two remote AEs that represent the originators used in the ACP rules below.

		dct = 	{ 'm2m:ae' : {
					'rn': f'{aeRN}RemoteAE1',
					'api': APPID,
					'rr': True,
					'srv': [ RELEASEVERSION ],
					'acpi': [ cls.remoteAcpRIAEAccess ]
				}}
		r, rsc = CREATE(REMOTEcseURL, remoteAE1Originator, T.AE, dct)
		assert rsc == RC.CREATED, f'cannot create remote AE 1: {r}'

		dct = 	{ 'm2m:ae' : {
					'rn': f'{aeRN}RemoteAE2',
					'api': APPID,
					'rr': True,
					'srv': [ RELEASEVERSION ],
					'acpi': [ cls.remoteAcpRIAEAccess ]
				}}
		r, rsc = CREATE(REMOTEcseURL, remoteAE2Originator, T.AE, dct)
		assert rsc == RC.CREATED, f'cannot create remote AE 2: {r}'


		# <ACP> #1 on the REMOTE CSE: 2 rules, each granting a different
		# (exact-match) originator its own single permission.
		dct = 	{ 'm2m:acp' : {
					'rn': acp1RN,
					'pv': {
						'acr': [
							{ 'acor': [ remoteAE1Originator ], 'acop': Permission.CREATE },
							{ 'acor': [ remoteAE2Originator ], 'acop': Permission.UPDATE },
						]
					},
					'pvs': {
						'acr': [ { 'acor': [ REMOTEORIGINATOR, CSEID ], 'acop': Permission.ALL } ]
					}
				}}
		r, rsc = CREATE(REMOTEcseURL, remoteAE1Originator, T.ACP, dct)
		assert rsc == RC.CREATED, f'cannot create remote ACP 1: {r}'
		cls.remoteAcp1Ri = findXPath(r, 'm2m:acp/ri')

		# <ACP> #2 on the REMOTE CSE: 2 wildcard rules, one SP-relative, one
		# CSE-relative, both intended (per TS-0003) to be scoped to the
		# *remote* CSE (the ACP's own host), not the CSE evaluating the request.
		dct =	{ 'm2m:acp' : {
					'rn': acp2RN,
					'pv': {
						'acr': [
							{ 'acor': [ f'{REMOTECSEID}/CwildSP*' ],  'acop': Permission.RETRIEVE },
							{ 'acor': [ 'CwildCSE*' ],                'acop': Permission.RETRIEVE },
						]
					},
					'pvs': {
						'acr': [ { 'acor': [ REMOTEORIGINATOR, CSEID ], 'acop': Permission.ALL } ]
					}
				}}
		r, rsc = CREATE(REMOTEcseURL, remoteAE2Originator, T.ACP, dct)
		assert rsc == RC.CREATED, f'cannot create remote ACP 2: {r}'
		cls.remoteAcp2Ri = findXPath(r, 'm2m:acp/ri')

		# Local <AE> to host the test <CNT>s
		dct = 	{ 'm2m:ae' : {
					'rn'  : ae1RN,
					'api' : APPID,
					'rr'  : True,
					'srv' : [ RELEASEVERSION ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)
		assert rsc == RC.CREATED, f'cannot create parent AE: {cls.ae}'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')

		testCaseEnd('Setup TestRemote_ACP')


	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestRemote_ACP')
		DELETE(f'{cseURL}/{ae1RN}', ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(acpURL, ORIGINATOR)	# Just delete the ACP 
		DELETE(f'{REMOTEcseURL}/{acp1RN}', REMOTEORIGINATOR)
		DELETE(f'{REMOTEcseURL}/{acp2RN}', REMOTEORIGINATOR)
		DELETE(f'{REMOTEcseURL}/{acpRN}', REMOTEORIGINATOR)
		DELETE(f'{REMOTEcseURL}/{aeRN}RemoteAE1', remoteAE1Originator)
		DELETE(f'{REMOTEcseURL}/{aeRN}RemoteAE2', remoteAE2Originator)
		testCaseEnd('TearDown TestRemote_ACP')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)


	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)

	#########################################################################
	#
	#	create an announced ACP
	#

	# Create an ACP 
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createAnnouncedACP(self) -> None:
		""" Create an announced <ACP> """
		dct = 	{ "m2m:acp": {
					"rn": acpRN,
					"pv": {
						"acr": [ { 	"acor": [ ORIGINATOR ],
									"acop": 63
								} ]
					},
					"pvs": { 
						"acr": [ {
							"acor": [ acpORIGINATOR ],
							#"acor": [ 'all' ],
							"acop": 63
						} ]
					},
				 	'at': 	[ REMOTECSEID ]
				}}
		r, rsc = CREATE(cseURL, ORIGINATOR, T.ACP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:acp/at'))
		self.assertIsInstance(findXPath(r, 'm2m:acp/at'), list)
		self.assertEqual(len(findXPath(r, 'm2m:acp/at')), 1)
		self.assertTrue(findXPath(r, 'm2m:acp/at')[0].startswith(f'{REMOTECSEID}/'))
		TestRemote_ACP.remoteAcpRI = findXPath(r, 'm2m:acp/at')[0]
		self.assertIsNotNone(self.remoteAcpRI)
		self.assertIsNone(findXPath(r, 'm2m:acp/aa'))
		TestRemote_ACP.acp = r


	# Retrieve the announced ACP
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedACPwithCSERelativeOriginatorFail(self) -> None:
		""" Retrieve remote <ACPA> w/ CSE-Relative originator -> Fail """
		if TestRemote_ACP.remoteAcpRI is None:
			self.skipTest('remote ACP.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_ACP.remoteAcpRI}', acpORIGINATOR)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	# Retrieve the announced ACP
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedACP(self) -> None:
		""" Retrieve remote <ACPA> """
		if TestRemote_ACP.remoteAcpRI is None:
			self.skipTest('remote ACP.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_ACP.remoteAcpRI}', 'other')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_ACP.remoteAcpRI}', f'{CSEID}/{acpORIGINATOR}')
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:acpA'))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/ty'))
		self.assertEqual(findXPath(r, 'm2m:acpA/ty'), T.ACPAnnc)
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/pi'))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/lnk'))
		self.assertTrue(findXPath(r, 'm2m:acpA/lnk').endswith( findXPath(TestRemote_ACP.acp, 'm2m:acp/ri') ))
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/pv'))	# MA attribute
		self.assertIsInstance(findXPath(r, 'm2m:acpA/pv'), dict)
		self.assertIsNotNone(findXPath(r, 'm2m:acpA/pvs'))	# MA attribute
		self.assertIsInstance(findXPath(r, 'm2m:acpA/pvs'), dict)


	# Retrieve the announced ACP with wrong originator
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedACPwithWrongOriginator(self) -> None:
		""" Retrieve remote <ACPA> with wrong originator """
		if TestRemote_ACP.remoteAcpRI is None:
			self.skipTest('remote ACP.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_ACP.remoteAcpRI}', 'wrong')
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE)


	# Retrieve the announced ACP with the CSE-ID
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_retrieveAnnouncedACPwithCSI(self) -> None:
		""" Retrieve remote <ACPA> with remote CSE's CSI """
		if TestRemote_ACP.remoteAcpRI is None:
			self.skipTest('remote ACP.ri not found')
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_ACP.remoteAcpRI}', CSEID)
		self.assertEqual(rsc, RC.OK)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_deleteAnnounceACP(self) -> None:
		""" Delete remote <ACPA> directly -> FAIL """
		if TestRemote_ACP.acp is None:
			self.skipTest('acp not found')
		_, rsc = DELETE(acpURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)
		# try to retrieve the announced Node. Should not be found
		r, rsc = RETRIEVE(f'{REMOTECSEURL}~{TestRemote_ACP.remoteAcpRI}', CSEID)
		self.assertEqual(rsc, RC.NOT_FOUND)
		TestRemote_ACP.acp = None
		TestRemote_ACP.remoteAcpRI = None


	#
	#	Referencing the remote <ACP>, and multiple access control rules
	#

	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createCNTwithRemoteAcpi(self) -> None:
		""" CREATE <CNT> with acpi referencing a remote <ACP> (SP-relative) """
		dct = 	{ 'm2m:cnt' : {
					'rn'   : cnt1RN,
					'acpi' : [ f'{REMOTECSEID}/{TestRemote_ACP.remoteAcp1Ri}' ]
				}}
		r, rsc = CREATE(f'{cseURL}/{ae1RN}', TestRemote_ACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertEqual(findXPath(r, 'm2m:cnt/acpi'), [ f'{REMOTECSEID}/{TestRemote_ACP.remoteAcp1Ri}' ], r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_remoteAcpFirstRuleGrantsFirstOriginator(self) -> None:
		""" CREATE child <CNT> as remote-ACP originator 1 (rule 1 grants CREATE) """
		dct = { 'm2m:cnt' : { 'rn': f'{cnt1RN}Sub' } }
		r, rsc = CREATE(f'{cseURL}/{ae1RN}/{cnt1RN}', f'{REMOTECSEID}/{remoteAE1Originator}', T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		DELETE(f'{cseURL}/{ae1RN}/{cnt1RN}/{cnt1RN}Sub', TestRemote_ACP.originator)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_remoteAcpFirstRuleDeniesDisallowedOperationFail(self) -> None:
		""" UPDATE <CNT> as remote-ACP originator 1 (rule 1 only grants CREATE) -> Fail """
		dct = { 'm2m:cnt' : { 'lbl': [ 'x' ] } }
		r, rsc = UPDATE(f'{cseURL}/{ae1RN}/{cnt1RN}', f'{REMOTECSEID}/{remoteAE1Originator}', dct)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_remoteAcpSecondRuleGrantsSecondOriginatorDespiteEarlierNonMatch(self) -> None:
		""" UPDATE <CNT> as remote-ACP originator 2 (rule 2 grants UPDATE, despite rule 1 not matching) """
		dct = { 'm2m:cnt' : { 'lbl': [ 'y' ] } }
		r, rsc = UPDATE(f'{cseURL}/{ae1RN}/{cnt1RN}', f'{REMOTECSEID}/{remoteAE2Originator}', dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:cnt/lbl'), [ 'y' ], r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_remoteAcpSecondRuleDeniesDisallowedOperationFail(self) -> None:
		""" CREATE child <CNT> as remote-ACP originator 2 (rule 2 only grants UPDATE) -> Fail """
		dct = { 'm2m:cnt' : { 'rn': f'{cnt1RN}Sub2' } }
		r, rsc = CREATE(f'{cseURL}/{ae1RN}/{cnt1RN}', f'{REMOTECSEID}/{remoteAE2Originator}', T.CNT, dct)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)


	#########################################################################
	#
	#	acpi addressing format: a bare (CSE-relative) ri is always looked up locally
	#

	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createCNTwithBareRemoteAcpiRiFail(self) -> None:
		""" CREATE <CNT> with acpi as a bare ri of a remote <ACP> (resolved as local, not found) -> Fail """
		dct = 	{ 'm2m:cnt' : {
					'rn'   : f'{cnt1RN}Bare',
					'acpi' : [ TestRemote_ACP.remoteAcp1Ri ]
				}}
		r, rsc = CREATE(f'{cseURL}/{ae1RN}', TestRemote_ACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	#########################################################################
	#
	#	Wildcard acor entries on a REMOTE <ACP>: written relative to the CSE
	#	hosting the ACP, not the CSE evaluating the "From" originator
	#

	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_createCNTwithRemoteAcpiWildcardAcp(self) -> None:
		""" CREATE a 2nd <CNT> with acpi referencing the remote wildcard <ACP> """
		dct = 	{ 'm2m:cnt' : {
					'rn'   : cnt2RN,
					'acpi' : [ f'{REMOTECSEID}/{TestRemote_ACP.remoteAcp2Ri}' ]
				}}
		r, rsc = CREATE(f'{cseURL}/{ae1RN}', TestRemote_ACP.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_remoteAcpSPRelativeWildcardGrantsAccess(self) -> None:
		""" RETRIEVE <CNT> as an SP-relative wildcard match on the remote <ACP> """
		r, rsc = RETRIEVE(f'{cseURL}/{ae1RN}/{cnt2RN}', wildcardSPRelativeOriginator)
		self.assertEqual(rsc, RC.OK, r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_remoteAcpCSERelativeWildcardGrantsAccess(self) -> None:
		""" RETRIEVE <CNT> as a CSE-relative wildcard match on the remote <ACP> """
		r, rsc = RETRIEVE(f'{cseURL}/{ae1RN}/{cnt2RN}', wildcardCSERelativeOriginator)
		self.assertEqual(rsc, RC.OK, r)


def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestRemote_ACP, [


		# create an announced ACP
		'test_createAnnouncedACP',
		'test_retrieveAnnouncedACPwithWrongOriginator',
		'test_retrieveAnnouncedACP',
		'test_retrieveAnnouncedACPwithCSERelativeOriginatorFail',
		'test_retrieveAnnouncedACPwithCSI',
		'test_deleteAnnounceACP',

		# referencing the remote ACP, multiple access control rules
		'test_createCNTwithRemoteAcpi',
		'test_remoteAcpFirstRuleGrantsFirstOriginator',
		'test_remoteAcpFirstRuleDeniesDisallowedOperationFail',
		'test_remoteAcpSecondRuleGrantsSecondOriginatorDespiteEarlierNonMatch',
		'test_remoteAcpSecondRuleDeniesDisallowedOperationFail',

		# acpi addressing format
		'test_createCNTwithBareRemoteAcpiRiFail',

		# ID form of wildcard acor entries on a remote ACP
		'test_createCNTwithRemoteAcpiWildcardAcp',
		'test_remoteAcpSPRelativeWildcardGrantsAccess',
		'test_remoteAcpCSERelativeWildcardGrantsAccess',

	])

	# Run tests
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
