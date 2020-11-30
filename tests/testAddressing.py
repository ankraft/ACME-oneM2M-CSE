#
#	testAddressing.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for addressing methods
#

import unittest, sys
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T, ResponseCode as RC
from init import *

# The following code must be executed before anything else because it influences
# the collection of skipped tests.
# It checks whether there actually is a CSE running.
noCSE = not connectionPossible(cseURL)

class TestAddressing(unittest.TestCase):

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		assert rsc == RC.OK, f'Cannot retrieve CSEBase:{cseURL}'

		dct = 	{ 'm2m:ae' : {
					'rn'  : aeRN, 
					'api' : 'NMyApp1Id',
				 	'rr'  : False,
				 	'srv' : [ '3' ]
				}}
		cls.ae, rsc = CREATE(cseURL, 'C', T.AE, dct)	# AE to work under
		assert rsc == RC.created, 'cannot create parent AE'
		cls.originator = findXPath(cls.ae, 'm2m:ae/aei')
		dct = 	{ 'm2m:cnt' : { 
					'rn'  : cntRN
				}}
		cls.cnt, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)
		assert rsc == RC.created, 'cannot create container'
		cls.cntRI = findXPath(cls.cnt, 'm2m:cnt/ri')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls):
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_cseRelativeStructured(self):
		url = f'{URL}{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		url = f'{URL}-/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_cseRelativeUnstructured(self):
		url = f'{URL}{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_spRelativeStructured(self):
		url = f'{URL}~{CSEID}/{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		url = f'{URL}~{CSEID}/-/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_spRelativeUnstructured(self):
		url = f'{URL}~{CSEID}/{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteStructured(self):
		url = f'{URL}_/{SPID}{CSEID}/{CSERN}/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)
		url = f'{URL}_/{SPID}{CSEID}/-/{aeRN}/{cntRN}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_absoluteUnstructured(self):
		url = f'{URL}_/{SPID}{CSEID}/{TestAddressing.cntRI}'
		r, rsc = RETRIEVE(url, TestAddressing.originator)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:cnt/rn'), cntRN)

def run():
	suite = unittest.TestSuite()
	suite.addTest(TestAddressing('test_cseRelativeStructured'))
	suite.addTest(TestAddressing('test_cseRelativeUnstructured'))
	suite.addTest(TestAddressing('test_spRelativeStructured'))
	suite.addTest(TestAddressing('test_spRelativeUnstructured'))
	suite.addTest(TestAddressing('test_absoluteStructured'))
	suite.addTest(TestAddressing('test_absoluteUnstructured'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)

