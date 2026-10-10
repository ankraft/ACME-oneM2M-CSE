#
#	testRemote_ACP.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for referencing an <ACP> resource hosted on a remote CSE via "acpi"
#

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


class TestRemote_ACP(unittest.TestCase):

	ae				= None
	originator		= None
	remoteAcp1Ri	= None
	remoteAcp2Ri	= None

	@classmethod
	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestRemote_ACP')
		dct: JSON

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
		r, rsc = CREATE(REMOTEcseURL, REMOTEORIGINATOR, T.ACP, dct)
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
		r, rsc = CREATE(REMOTEcseURL, REMOTEORIGINATOR, T.ACP, dct)
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
		DELETE(f'{REMOTEcseURL}/{acp1RN}', REMOTEORIGINATOR)
		DELETE(f'{REMOTEcseURL}/{acp2RN}', REMOTEORIGINATOR)
		testCaseEnd('TearDown TestRemote_ACP')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)


	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################
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
		r, rsc = CREATE(f'{cseURL}/{ae1RN}/{cnt1RN}', remoteAE1Originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		DELETE(f'{cseURL}/{ae1RN}/{cnt1RN}/{cnt1RN}Sub', TestRemote_ACP.originator)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_remoteAcpFirstRuleDeniesDisallowedOperationFail(self) -> None:
		""" UPDATE <CNT> as remote-ACP originator 1 (rule 1 only grants CREATE) -> Fail """
		dct = { 'm2m:cnt' : { 'lbl': [ 'x' ] } }
		r, rsc = UPDATE(f'{cseURL}/{ae1RN}/{cnt1RN}', remoteAE1Originator, dct)
		self.assertEqual(rsc, RC.ORIGINATOR_HAS_NO_PRIVILEGE, r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_remoteAcpSecondRuleGrantsSecondOriginatorDespiteEarlierNonMatch(self) -> None:
		""" UPDATE <CNT> as remote-ACP originator 2 (rule 2 grants UPDATE, despite rule 1 not matching) """
		dct = { 'm2m:cnt' : { 'lbl': [ 'y' ] } }
		r, rsc = UPDATE(f'{cseURL}/{ae1RN}/{cnt1RN}', remoteAE2Originator, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertEqual(findXPath(r, 'm2m:cnt/lbl'), [ 'y' ], r)


	@unittest.skipIf(noRemote or noCSE, 'No CSEBase or remote CSEBase')
	def test_remoteAcpSecondRuleDeniesDisallowedOperationFail(self) -> None:
		""" CREATE child <CNT> as remote-ACP originator 2 (rule 2 only grants UPDATE) -> Fail """
		dct = { 'm2m:cnt' : { 'rn': f'{cnt1RN}Sub2' } }
		r, rsc = CREATE(f'{cseURL}/{ae1RN}/{cnt1RN}', remoteAE2Originator, T.CNT, dct)
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
