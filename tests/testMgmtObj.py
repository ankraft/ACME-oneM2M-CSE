#
#	testMgmtObj.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for all kind of MgmtObj specialisations
#

import unittest, sys
import requests
sys.path.append('../acme')
from Constants import Constants as C
from Types import ResourceTypes as T
from init import *

nodeID  = 'urn:sn:1234'
nod2RN 	= 'test2NOD'
nod2URL = '%s/%s' % (cseURL, nod2RN)


class TestMgmtObj(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.cse, rsc = RETRIEVE(cseURL, ORIGINATOR)
		jsn = 	{ 'm2m:nod' : { 
					'rn' 	: nodRN,
					'ni'	: nodeID
				}}
		cls.nod, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, jsn)
		assert rsc == C.rcCreated, 'cannot create <node>'


	@classmethod
	def tearDownClass(cls):
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not

	#
	#	FWR
	#

	fwrRN	= 'fwr'
	fwrURL	= '%s/%s' % (nodURL, fwrRN)


	def test_createFWR(self):
		self.assertIsNotNone(TestMgmtObj.cse)
		jsn =  { 'm2m:fwr' : {
					'mgd' : T.FWR,
					'rn' : self.fwrRN,
					'dc' : 'aFwr',
					'vr' : '1234',
					'fwn': 'myFwr',
					'url': 'example.com',
					'ud' : False
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/ri'))


	def test_retrieveFWR(self):
		r, rsc = RETRIEVE(self.fwrURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:fwr/mgd'), T.FWR)


	def test_attributesFWR(self):
		r, rsc = RETRIEVE(self.fwrURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:fwr/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:fwr/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:fwr/rn'), self.fwrRN)
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/dc'))
		self.assertEqual(findXPath(r, 'm2m:fwr/dc'), 'aFwr')
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/vr'))
		self.assertEqual(findXPath(r, 'm2m:fwr/vr'), '1234')
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/fwn'))
		self.assertEqual(findXPath(r, 'm2m:fwr/fwn'), 'myFwr')
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/url'))
		self.assertEqual(findXPath(r, 'm2m:fwr/url'), 'example.com')
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/ud'))
		self.assertEqual(findXPath(r, 'm2m:fwr/ud'), False)
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/uds'))
		self.assertIsInstance(findXPath(r, 'm2m:fwr/uds'), dict)


	def test_deleteFWR(self):
		_, rsc = DELETE(self.fwrURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)

	#
	#	SWR
	#

	swrRN	= 'swr'
	swrURL	= '%s/%s' % (nodURL, swrRN)


	def test_createSWR(self):
		self.assertIsNotNone(TestMgmtObj.cse)
		jsn =  { 'm2m:swr' : {
					'mgd' : T.SWR,
					'rn' : self.swrRN,
					'dc' : 'aSwr',
					'vr' : '1234',
					'swn': 'mySwr',
					'url': 'example.com'
				}}


		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:swr/ri'))


	def test_retrieveSWR(self):
		r, rsc = RETRIEVE(self.swrURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:swr/mgd'), T.SWR)


	def test_attributesSWR(self):
		r, rsc = RETRIEVE(self.swrURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:swr/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:swr/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:swr/rn'), self.swrRN)
		self.assertIsNotNone(findXPath(r, 'm2m:swr/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:swr/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:swr/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:swr/dc'))
		self.assertEqual(findXPath(r, 'm2m:swr/dc'), 'aSwr')
		self.assertIsNotNone(findXPath(r, 'm2m:swr/vr'))
		self.assertEqual(findXPath(r, 'm2m:swr/vr'), '1234')
		self.assertIsNotNone(findXPath(r, 'm2m:swr/swn'))
		self.assertEqual(findXPath(r, 'm2m:swr/swn'), 'mySwr')
		self.assertIsNotNone(findXPath(r, 'm2m:swr/url'))
		self.assertEqual(findXPath(r, 'm2m:swr/url'), 'example.com')
		self.assertIsNotNone(findXPath(r, 'm2m:swr/in'))
		self.assertIsNotNone(findXPath(r, 'm2m:swr/un'))
		self.assertIsNotNone(findXPath(r, 'm2m:swr/ins'))


	def test_deleteSWR(self):
		_, rsc = DELETE(self.swrURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)


	#
	#	MEM
	#

	memRN	= 'mem'
	memURL	= '%s/%s' % (nodURL, memRN)


	def test_createMEM(self):
		self.assertIsNotNone(TestMgmtObj.cse)
		jsn =  { 'm2m:mem' : {
					'mgd' : T.MEM,
					'rn' : self.memRN,
					'dc' : 'aMem',
					'mma' : 1234,
					'mmt' : 4321
				}}

		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:mem/ri'))


	def test_retrieveMEM(self):
		r, rsc = RETRIEVE(self.memURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:mem/mgd'), T.MEM)


	def test_attributesMEM(self):
		r, rsc = RETRIEVE(self.memURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:mem/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:mem/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:mem/rn'), self.memRN)
		self.assertIsNotNone(findXPath(r, 'm2m:mem/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:mem/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:mem/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:mem/dc'))
		self.assertEqual(findXPath(r, 'm2m:mem/dc'), 'aMem')
		self.assertIsNotNone(findXPath(r, 'm2m:mem/mma'))
		self.assertEqual(findXPath(r, 'm2m:mem/mma'), 1234)
		self.assertIsNotNone(findXPath(r, 'm2m:mem/mmt'))
		self.assertEqual(findXPath(r, 'm2m:mem/mmt'), 4321)


	def test_deleteMEM(self):
		_, rsc = DELETE(self.memURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)

	#
	#	ANI
	#

	aniRN	= 'ANI'
	aniURL	= '%s/%s' % (nodURL, aniRN)


	def test_createANI(self):
		self.assertIsNotNone(TestMgmtObj.cse)
		jsn =  { 'm2m:ani' : {
					'mgd' : T.ANI,
					'rn' : self.aniRN,
					'dc' : 'aAni',
					'ant' : 'aniType',
					'ldv' : [ 'dev1', 'dev2' ]
				}}

		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:ani/ri'))


	def test_retrieveANI(self):
		r, rsc = RETRIEVE(self.aniURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:ani/mgd'), T.ANI)


	def test_attributesANI(self):
		r, rsc = RETRIEVE(self.aniURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:ani/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:ani/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:ani/rn'), self.aniRN)
		self.assertIsNotNone(findXPath(r, 'm2m:ani/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:ani/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:ani/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:ani/dc'))
		self.assertEqual(findXPath(r, 'm2m:ani/dc'), 'aAni')
		self.assertIsNotNone(findXPath(r, 'm2m:ani/ant'))
		self.assertEqual(findXPath(r, 'm2m:ani/ant'), 'aniType')
		self.assertIsNotNone(findXPath(r, 'm2m:ani/ldv'))
		self.assertIsInstance(findXPath(r, 'm2m:ani/ldv'), list)
		self.assertEqual(len(findXPath(r, 'm2m:ani/ldv')), 2)
		self.assertIn('dev1', findXPath(r, 'm2m:ani/ldv'))
		self.assertIn('dev2', findXPath(r, 'm2m:ani/ldv'))


	def test_deleteANI(self):
		_, rsc = DELETE(self.aniURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)


	#
	#	ANDI
	#

	andiRN	= 'ANDI'
	andiURL	= '%s/%s' % (nodURL, andiRN)


	def test_createANDI(self):
		self.assertIsNotNone(TestMgmtObj.cse)
		jsn =  { 'm2m:andi' : {
					'mgd' : T.ANDI,
					'rn' : self.andiRN,
					'dc' : 'aAndi',
					'dvd' : 'aDeviceID',
					'dvt' : 'aDeviceType',
					'awi' : 'aNetworkID',
					'sli' : 5,
					'sld' : 23,
					'lnh' : [ 'dev1', 'dev2']
				}}

		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:andi/ri'))


	def test_retrieveANDI(self):
		r, rsc = RETRIEVE(self.andiURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:andi/mgd'), T.ANDI)


	def test_attributesANDI(self):
		r, rsc = RETRIEVE(self.andiURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:andi/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:andi/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:andi/rn'), self.andiRN)
		self.assertIsNotNone(findXPath(r, 'm2m:andi/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:andi/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:andi/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:andi/dc'))
		self.assertEqual(findXPath(r, 'm2m:andi/dc'), 'aAndi')
		self.assertIsNotNone(findXPath(r, 'm2m:andi/dvd'))
		self.assertEqual(findXPath(r, 'm2m:andi/dvd'), 'aDeviceID')
		self.assertIsNotNone(findXPath(r, 'm2m:andi/dvt'))
		self.assertEqual(findXPath(r, 'm2m:andi/dvt'), 'aDeviceType')
		self.assertIsNotNone(findXPath(r, 'm2m:andi/awi'))
		self.assertEqual(findXPath(r, 'm2m:andi/awi'), 'aNetworkID')
		self.assertIsNotNone(findXPath(r, 'm2m:andi/sli'))
		self.assertEqual(findXPath(r, 'm2m:andi/sli'), 5)
		self.assertIsNotNone(findXPath(r, 'm2m:andi/sld'))
		self.assertEqual(findXPath(r, 'm2m:andi/sld'), 23)
		self.assertIsNotNone(findXPath(r, 'm2m:andi/lnh'))
		self.assertIsInstance(findXPath(r, 'm2m:andi/lnh'), list)
		self.assertEqual(len(findXPath(r, 'm2m:andi/lnh')), 2)
		self.assertIn('dev1', findXPath(r, 'm2m:andi/lnh'))
		self.assertIn('dev2', findXPath(r, 'm2m:andi/lnh'))


	def test_deleteANDI(self):
		_, rsc = DELETE(self.andiURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)



	#
	#	NYCFC
	#

	nycfcRN		= 'nycfc'
	nycfcURL	= '%s/%s' % (nodURL, nycfcRN)


	def test_createNYCFC(self):
		self.assertIsNotNone(TestMgmtObj.cse)
		jsn =  { 'm2m:nycfc' : {
					'mgd' : T.NYCFC,
					'rn' : self.nycfcRN,
					'dc' : 'aNycfc',
					'suids' : [ 99 ],
					'mcff' : 'application/pkcs7mime',
					'mcfc' : 'secretKey'
				}}

		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, jsn)
		self.assertEqual(rsc, C.rcCreated)
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/ri'))


	def test_retrieveNYCFC(self):
		r, rsc = RETRIEVE(self.nycfcURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:nycfc/mgd'), T.NYCFC)


	def test_attributesNYCFC(self):
		r, rsc = RETRIEVE(self.nycfcURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcOK)
		self.assertEqual(findXPath(r, 'm2m:nycfc/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:nycfc/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/rn'), self.nycfcRN)
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/dc'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/dc'), 'aNycfc')
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/suids'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/suids/{0}'), 99)
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/mcff'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/mcff'), 'application/pkcs7mime')
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/mcfc'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/mcfc'), 'secretKey')


	def test_deleteNYCFC(self):
		_, rsc = DELETE(self.nycfcURL, ORIGINATOR)
		self.assertEqual(rsc, C.rcDeleted)

	# BAT			= 1006
	# DVI 		= 1007
	# DVC 		= 1008
	# RBO 		= 1009
	# EVL 		= 1010



def run():
	suite = unittest.TestSuite()
	suite.addTest(TestMgmtObj('test_createFWR'))
	suite.addTest(TestMgmtObj('test_retrieveFWR'))
	suite.addTest(TestMgmtObj('test_attributesFWR'))
	suite.addTest(TestMgmtObj('test_deleteFWR'))
	suite.addTest(TestMgmtObj('test_createSWR'))
	suite.addTest(TestMgmtObj('test_retrieveSWR'))
	suite.addTest(TestMgmtObj('test_attributesSWR'))
	suite.addTest(TestMgmtObj('test_deleteSWR'))
	suite.addTest(TestMgmtObj('test_createMEM'))
	suite.addTest(TestMgmtObj('test_retrieveMEM'))
	suite.addTest(TestMgmtObj('test_attributesMEM'))
	suite.addTest(TestMgmtObj('test_deleteMEM'))
	suite.addTest(TestMgmtObj('test_createANI'))
	suite.addTest(TestMgmtObj('test_retrieveANI'))
	suite.addTest(TestMgmtObj('test_attributesANI'))
	suite.addTest(TestMgmtObj('test_deleteANI'))
	suite.addTest(TestMgmtObj('test_createANDI'))
	suite.addTest(TestMgmtObj('test_retrieveANDI'))
	suite.addTest(TestMgmtObj('test_attributesANDI'))
	suite.addTest(TestMgmtObj('test_deleteANDI'))
	suite.addTest(TestMgmtObj('test_createNYCFC'))
	suite.addTest(TestMgmtObj('test_retrieveNYCFC'))
	suite.addTest(TestMgmtObj('test_attributesNYCFC'))
	suite.addTest(TestMgmtObj('test_deleteNYCFC'))
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=True).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run()
	sys.exit(errors)
