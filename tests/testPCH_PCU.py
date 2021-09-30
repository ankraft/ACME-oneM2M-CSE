#
#	testPCH_PCU.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for PollingChannelURI functionality
#

import unittest, sys, time
import requests
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, NotificationEventType as NET, ResourceTypes as T, NotificationContentType, ResponseCode as RC, Permission
from init import *

aeRN2 = f'{aeRN}2'

class TestPCH_PCU(unittest.TestCase):

	ae 			= None
	cnt			= None
	ae2			= None
	acp2		= None
	originator 	= None
	originator2	= None
	aeRI		= None
	aeRI2		= None
	cntRI		= None
	acpRI2		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:

		# Add first AE
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyAppId',
				 	'rr'  : False,		# Explicitly not request reachable
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		cls.aeRI = findXPath(cls.ae, 'm2m:ae/ri')

		# Add second AE that will receive notifications
		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN2, 
					'api' : 'NMyAppId',
				 	'rr'  : False,		# Explicitly not request reachable
				 	'srv' : [ '3' ]
				}}
		cls.ae2, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator2 = findXPath(cls.ae2, 'm2m:ae/aei')
		cls.aeRI2 = findXPath(cls.ae2, 'm2m:ae/ri')

		# Add permissions for second AE
		dct = 	{ "m2m:acp": {
			"rn": acpRN,
			"pv": {
				"acr": [ { 	
					"acor": [ cls.originator ],
					"acop": Permission.ALL
				} ]
			},
			"pvs": { 
				"acr": [ {
					"acor": [ cls.originator2 ],
					"acop": Permission.ALL
				} ]
			},
		}}
		cls.acp2, rsc = CREATE(f'{aeURL}2', cls.originator2, T.ACP, dct)
		assert rsc == RC.created, 'cannot create ACP'
		cls.acpRI2 = findXPath(cls.acp2, 'm2m:acp/ri')

		# Add acpi to second AE 
		dct = 	{ 'm2m:ae' : {
					'acpi' : [ cls.acpRI2 ]
				}}
		cls.ae, rsc = UPDATE(f'{aeURL}2', cls.originator2, dct)
		assert rsc == RC.updated, 'cannot update AE'
		
		# Add container to first AE
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		cls.cntRI = findXPath(cls.cnt, 'm2m:cnt/ri')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		DELETE(f'{aeURL}2', ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSUB(self) -> None:
		"""	CREATE <SUB> under <CNT>. No <PCH> yet -> FAIL"""
		clearLastNotification()	# clear the notification first
		self.assertIsNotNone(TestPCH_PCU.ae)
		self.assertIsNotNone(TestPCH_PCU.cnt)
		dct = 	{ 'm2m:sub' : { 
					'rn' : subRN,
			        'enc': {
			            'net': [ NET.resourceUpdate, NET.createDirectChild ]
					},
					'nu': [ TestPCH_PCU.aeRI2 ],
					'su': TestPCH_PCU.aeRI2
				}}
		r, rsc = CREATE(cntURL, TestPCH_PCU.originator, T.SUB, dct)
		self.assertEqual(rsc, RC.subscriptionVerificationInitiationFailed, r)



# TODO Non-Blocking async request, then retrieve notification via pcu
# TODO multiple non-blocking async requests, then retrieve notification via pcu

# TODO retrieve via PCU *after* delete

def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()

	# basic tests
	suite.addTest(TestPCH_PCU('test_createSUB'))


	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)

