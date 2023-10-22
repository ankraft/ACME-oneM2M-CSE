#
#	testMgmtObj.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for all kind of MgmtObj specialisations
#

from audioop import getsample
import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *

nodeID  = 'urn:sn:1234'
nod2RN 	= 'test2NOD'
nod2URL = f'{cseURL}/{nod2RN}'


class TestMgmtObj(unittest.TestCase):

	nod 		= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestMgmtObj')
		dct = 	{ 'm2m:nod' : { 
					'rn' 	: nodRN,
					'ni'	: nodeID
				}}
		cls.nod, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, dct)
		assert rsc == RC.CREATED, 'cannot create <node>'
		testCaseEnd('Setup TestMgmtObj')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			return
		testCaseStart('TearDown TestMgmtObj')
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestMgmtObj')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)


	#########################################################################

	#
	#	FWR
	#

	fwrRN	= 'fwr'
	fwrURL	= f'{nodURL}/{fwrRN}'


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFWR(self) -> None:
		"""	CREATE [Firmware] """
		dct =  { 'm2m:fwr' : {
					'mgd' : T.FWR,
					'rn' : self.fwrRN,
					'dc' : 'aFwr',
					'vr' : '1234',
					'fwn': 'myFwr',
					'url': 'example.com',
					'ud' : False
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFWR(self) -> None:
		"""	RETRIEVE [Firmware] """
		r, rsc = RETRIEVE(self.fwrURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:fwr/mgd'), T.FWR)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesFWR(self) -> None:
		"""	Test [Firmware] attributes """
		r, rsc = RETRIEVE(self.fwrURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
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


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteFWR(self) -> None:
		"""	DELETE [Firmware] """
		_, rsc = DELETE(self.fwrURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)

	#
	#	SWR
	#

	swrRN	= 'swr'
	swrURL	= f'{nodURL}/{swrRN}'


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSWR(self) -> None:
		"""CREATE [Software] """
		dct =  { 'm2m:swr' : {
					'mgd' : T.SWR,
					'rn' : self.swrRN,
					'dc' : 'aSwr',
					'vr' : '1234',
					'swn': 'mySwr',
					'url': 'example.com'
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:swr/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveSWR(self) -> None:
		"""	RETRIEVE [Software] """
		r, rsc = RETRIEVE(self.swrURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:swr/mgd'), T.SWR)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesSWR(self) -> None:
		""" Test [Software] attributes """
		r, rsc = RETRIEVE(self.swrURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
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


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteSWR(self) -> None:
		"""	DELETE [Software] """
		_, rsc = DELETE(self.swrURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	MEM
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createMEM(self) -> None:
		""" CREATE [Memory] """
		dct =  { 'm2m:mem' : {
					'mgd' : T.MEM,
					'rn' : memRN,
					'dc' : 'aMem',
					'mma' : 1234,
					'mmt' : 4321
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:mem/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveMEM(self) -> None:
		"""	RETRIEVE [Memory] """
		r, rsc = RETRIEVE(memURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:mem/mgd'), T.MEM)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesMEM(self) -> None:
		""" Test [Memory] attributes """
		r, rsc = RETRIEVE(memURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:mem/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:mem/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:mem/rn'), memRN)
		self.assertIsNotNone(findXPath(r, 'm2m:mem/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:mem/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:mem/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:mem/dc'))
		self.assertEqual(findXPath(r, 'm2m:mem/dc'), 'aMem')
		self.assertIsNotNone(findXPath(r, 'm2m:mem/mma'))
		self.assertEqual(findXPath(r, 'm2m:mem/mma'), 1234)
		self.assertIsNotNone(findXPath(r, 'm2m:mem/mmt'))
		self.assertEqual(findXPath(r, 'm2m:mem/mmt'), 4321)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteMEM(self) -> None:
		""" DELETE [Memory] """
		_, rsc = DELETE(memURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)

	#
	#	ANI
	#

	aniRN	= 'ANI'
	aniURL	= f'{nodURL}/{aniRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createANI(self) -> None:
		""" CREATE [areaNwkInfo] """
		dct =  { 'm2m:ani' : {
					'mgd' : T.ANI,
					'rn' : self.aniRN,
					'dc' : 'aAni',
					'ant' : 'aniType',
					'ldv' : [ 'dev1', 'dev2' ]
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:ani/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveANI(self) -> None:
		""" RETRIEVE [areaNwkInfo] """
		r, rsc = RETRIEVE(self.aniURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:ani/mgd'), T.ANI)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesANI(self) -> None:
		"""	Test [areaNwkInfo] attributes """
		r, rsc = RETRIEVE(self.aniURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
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


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteANI(self) -> None:
		"""	DELETE [areaNwkInfo] """
		_, rsc = DELETE(self.aniURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	ANDI
	#

	andiRN	= 'ANDI'
	andiURL	= f'{nodURL}/{andiRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createANDI(self) -> None:
		""" CREATE [areaNwkDeviceInfo] """
		dct =  { 'm2m:andi' : {
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
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:andi/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveANDI(self) -> None:
		""" RETRIEVE [areaNwkDeviceInfo] """
		r, rsc = RETRIEVE(self.andiURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:andi/mgd'), T.ANDI)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesANDI(self) -> None:
		""" Test [areaNwkDeviceInfo] attributes """
		r, rsc = RETRIEVE(self.andiURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
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


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteANDI(self) -> None:
		""" DELETE [areaNwkDeviceInfo] """
		_, rsc = DELETE(self.andiURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	BAT
	#


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createBATWrong(self) -> None:
		""" CREATE [battery] w/ wrong batteryStatus -> Fail"""
		dct =  { 'm2m:bat' : {
					'mgd' : T.BAT,
					'rn'  : batRN,
					'dc'  : 'aBat',
					'btl' : 23,
					'bts' : 99
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createBAT(self) -> None:
		""" CREATE [battery] """
		dct =  { 'm2m:bat' : {
					'mgd' : T.BAT,
					'rn'  : batRN,
					'dc'  : 'aBat',
					'btl' : 23,
					'bts' : 5
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/ri'))
		self.assertEqual(findXPath(r, 'm2m:bat/ty'), T.MGMTOBJ)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveBAT(self) -> None:
		""" RETRIEVE [battery] """
		r, rsc = RETRIEVE(batURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:bat/mgd'), T.BAT)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesBAT(self) -> None:
		""" Test [battery] attributes """
		r, rsc = RETRIEVE(batURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:bat/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:bat/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:bat/rn'), batRN)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:bat/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:bat/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:bat/dc'))
		self.assertEqual(findXPath(r, 'm2m:bat/dc'), 'aBat')
		self.assertIsNotNone(findXPath(r, 'm2m:bat/btl'))
		self.assertEqual(findXPath(r, 'm2m:bat/btl'), 23)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/bts'))
		self.assertEqual(findXPath(r, 'm2m:bat/bts'), 5)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteBAT(self) -> None:
		""" DELETE [battery] """
		_, rsc = DELETE(batURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	DVI
	#

	dviRN	= 'DVI'
	dviURL	= f'{nodURL}/{dviRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDVI(self) -> None:
		"""	CREATE [deviceInfo] """
		dct =  { 'm2m:dvi' : {
					'mgd' : T.DVI,
					'rn' : self.dviRN,
					'dc' : 'aDvi',

					'dlb' : '|label:value anotherLabel:value',
					'man' : 'a Manufacturer',
					'mfdl': 'https://link.to.manufacturer.com/details',
					'mfd' : '20010511T214200',
					'mod' : 'Heart of Gold',
					'smod': 'No.1',
					'dty' : 'Starship',
					'dvnm': 'a Device Name',
					'fwv' : '1.0',
					'swv' : '1.1',
					'hwv' : '1.2',
					'osv' : '1.3',
					'cnty': 'Earth',
					'loc' : 'Sol',
					'syst': '20010511T214200',
					'spur': 'http://example.com',
					'purl': 'http://example.com/ui',
					'ptl' : [ 'http' ]
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveDVI(self) -> None:
		""" RETRIEVE [deviceInfo] """
		r, rsc = RETRIEVE(self.dviURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:dvi/mgd'), T.DVI)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesDVI(self) -> None:
		""" Test [deviceInfo] attributes """
		r, rsc = RETRIEVE(self.dviURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:dvi/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:dvi/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:dvi/rn'), self.dviRN)
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/dc'))
		self.assertEqual(findXPath(r, 'm2m:dvi/dc'), 'aDvi')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/dlb'))
		self.assertEqual(findXPath(r, 'm2m:dvi/dlb'), '|label:value anotherLabel:value')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/man'))
		self.assertEqual(findXPath(r, 'm2m:dvi/man'), 'a Manufacturer')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/mfdl'))
		self.assertEqual(findXPath(r, 'm2m:dvi/mfdl'), 'https://link.to.manufacturer.com/details')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/man'))
		self.assertEqual(findXPath(r, 'm2m:dvi/man'), 'a Manufacturer')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/mfd'))
		self.assertEqual(findXPath(r, 'm2m:dvi/mfd'), '20010511T214200')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/mod'))
		self.assertEqual(findXPath(r, 'm2m:dvi/mod'), 'Heart of Gold')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/smod'))
		self.assertEqual(findXPath(r, 'm2m:dvi/smod'), 'No.1')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/dty'))
		self.assertEqual(findXPath(r, 'm2m:dvi/dty'), 'Starship')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/dvnm'))
		self.assertEqual(findXPath(r, 'm2m:dvi/dvnm'), 'a Device Name')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/fwv'))
		self.assertEqual(findXPath(r, 'm2m:dvi/fwv'), '1.0')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/swv'))
		self.assertEqual(findXPath(r, 'm2m:dvi/swv'), '1.1')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/hwv'))
		self.assertEqual(findXPath(r, 'm2m:dvi/hwv'), '1.2')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/osv'))
		self.assertEqual(findXPath(r, 'm2m:dvi/osv'), '1.3')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/cnty'))
		self.assertEqual(findXPath(r, 'm2m:dvi/cnty'), 'Earth')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/loc'))
		self.assertEqual(findXPath(r, 'm2m:dvi/loc'), 'Sol')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/syst'))
		self.assertEqual(findXPath(r, 'm2m:dvi/syst'), '20010511T214200')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/spur'))
		self.assertEqual(findXPath(r, 'm2m:dvi/spur'), 'http://example.com')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/purl'))
		self.assertEqual(findXPath(r, 'm2m:dvi/purl'), 'http://example.com/ui')
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/ptl'))
		self.assertEqual(findXPath(r, 'm2m:dvi/ptl'), [ 'http' ])


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteDVI(self) -> None:
		""" DELETE [deviceInfo] """
		_, rsc = DELETE(self.dviURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	DVC
	#

	dvcRN	= 'DVC'
	dvcURL	= f'{nodURL}/{dvcRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDVC(self) -> None:
		""" CREATE [deviceCapability] """
		dct =  { 'm2m:dvc' : {
					'mgd' : T.DVC,
					'rn' : self.dvcRN,
					'dc' : 'aDvc',

					'can': 'aCapabilityName',
					'att': True,
					'cas': { 
						'acn' : 'anAction',
						'sus' : 1
			   		},
					'cus': True

				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveDVC(self) -> None:
		""" RETRIEVE [deviceCapability] """
		r, rsc = RETRIEVE(self.dvcURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:dvc/mgd'), T.DVC)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesDVC(self) -> None:
		""" Test [deviceCapability] attributes """
		r, rsc = RETRIEVE(self.dvcURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:dvc/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:dvc/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:dvc/rn'), self.dvcRN)
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/dc'))
		self.assertEqual(findXPath(r, 'm2m:dvc/dc'), 'aDvc')
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/can'))
		self.assertEqual(findXPath(r, 'm2m:dvc/can'), 'aCapabilityName')
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/att'))
		self.assertTrue(findXPath(r, 'm2m:dvc/att'))
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/cas/acn'))
		self.assertEqual(findXPath(r, 'm2m:dvc/cas/acn'), 'anAction')
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/cas/sus'))
		self.assertEqual(findXPath(r, 'm2m:dvc/cas/sus'), 1)
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/cus'))
		self.assertTrue(findXPath(r, 'm2m:dvc/cus'))
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/ena'))
		self.assertTrue(findXPath(r, 'm2m:dvc/ena'))
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/dis'))
		self.assertTrue(findXPath(r, 'm2m:dvc/dis'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDVCEnaTrue(self) -> None:
		""" UPDATE [deviceCapability] ENA=False """
		dct =  { 'm2m:dvc' : {
					'ena' : True,
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertTrue(findXPath(r, 'm2m:dvc/ena'))
		self.assertTrue(findXPath(r, 'm2m:dvc/dis'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDVCEnaFalse(self) -> None:
		""" UPDATE [deviceCapability] ENA=False """
		dct =  { 'm2m:dvc' : {
					'ena' : False,
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertTrue(findXPath(r, 'm2m:dvc/ena'))
		self.assertTrue(findXPath(r, 'm2m:dvc/dis'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDVCDisTrue(self) -> None:
		""" Test [deviceCapability] DIS """
		dct =  { 'm2m:dvc' : {
					'dis' : True
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertTrue(findXPath(r, 'm2m:dvc/ena'))
		self.assertTrue(findXPath(r, 'm2m:dvc/dis'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDVCDisFalse(self) -> None:
		""" Test [deviceCapability] DIS """
		dct =  { 'm2m:dvc' : {
					'dis' : False
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertTrue(findXPath(r, 'm2m:dvc/ena'))
		self.assertTrue(findXPath(r, 'm2m:dvc/dis'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDVCEnaDisTrue(self) -> None:
		""" Test [deviceCapability] ENA=True & DIS = True -> Fail """
		dct =  { 'm2m:dvc' : {
					'ena' : True,
					'dis' : True
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDVCEnaDisFalse(self) -> None:
		"""	Update [deviceCapability] ENA=False & DIS=False -> ENA=True & DIS=True """
		dct =  { 'm2m:dvc' : {
					'ena' : False,
					'dis' : False
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertTrue(findXPath(r, 'm2m:dvc/ena'))
		self.assertTrue(findXPath(r, 'm2m:dvc/dis'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteDVC(self) -> None:
		"""	DELETE [deviceCapability] """
		_, rsc = DELETE(self.dvcURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	RBO
	#

	rboRN	= 'RBO'
	rboURL	= f'{nodURL}/{rboRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createRBO(self) -> None:
		"""	CREATE [reboot] """
		dct =  { 'm2m:rbo' : {
					'mgd' : T.RBO,
					'rn'  : self.rboRN,
					'dc'  : 'aRbo',

					'rbo' : False,
					'far' : False
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:rbo/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveRBO(self) -> None:
		"""	RETRIEVE [reboot] """
		r, rsc = RETRIEVE(self.rboURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:rbo/mgd'), T.RBO)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesRBO(self) -> None:
		""" Test [reboot] attributes """
		r, rsc = RETRIEVE(self.rboURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:rbo/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:rbo/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:rbo/rn'), self.rboRN)
		self.assertIsNotNone(findXPath(r, 'm2m:rbo/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:rbo/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:rbo/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:rbo/dc'))
		self.assertEqual(findXPath(r, 'm2m:rbo/dc'), 'aRbo')
		self.assertIsNotNone(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertIsNotNone(findXPath(r, 'm2m:rbo/far'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBORboTrue(self) -> None:
		"""	UPDATE [reboot] with RBO=True -> RBO=False """
		dct =  { 'm2m:rbo' : {
					'rbo' : True,
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBORboFalse(self) -> None:
		""" UPDATE [reboot] with RBO=False -> RBO=False """
		dct =  { 'm2m:rbo' : {
					'rbo' : False,
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBOFarTrue(self) -> None:
		"""	UPDATE [reboot] FAR=True -> FAR=False """
		dct =  { 'm2m:rbo' : {
					'far' : True
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBOFarFalse(self) -> None:
		"""	UPDATE [reboot] FAR=False -> FAR=False """
		dct =  { 'm2m:rbo' : {
					'far' : False
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBORboFarTrue(self) -> None:
		""" UPDATE [reboot] with RBO=True & FAR=True -> Fail """
		dct =  { 'm2m:rbo' : {
					'rbo' : True,
					'far' : True
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBORboFarFalse(self) -> None:
		""" UPDATE [reboot] with RBO=False & FAR=False  -> RBO=False & FAR=False """
		dct =  { 'm2m:rbo' : {
					'rbo' : False,
					'far' : False
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED)
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteRBO(self) -> None:
		"""	DELETE [reboot] """
		_, rsc = DELETE(self.rboURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	NYCFC
	#

	nycfcRN		= 'nycfc'
	nycfcURL	= f'{nodURL}/{nycfcRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNYCFCwrongSUID(self) -> None:
		"""	CREATE [myCertFileCred] with wrong SUID -> Fail"""
		dct =  { 'm2m:nycfc' : {
					'mgd' : T.NYCFC,
					'rn' : self.nycfcRN,
					'dc' : 'aNycfc',
					'suids' : [ 99 ],
					'mcff' : 'application/pkcs7mime',
					'mcfc' : 'secretKey'
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNYCFC(self) -> None:
		"""	CREATE [myCertFileCred] """
		dct =  { 'm2m:nycfc' : {
					'mgd' : T.NYCFC,
					'rn' : self.nycfcRN,
					'dc' : 'aNycfc',
					'suids' : [ 42 ],
					'mcff' : 'application/pkcs7mime',
					'mcfc' : 'secretKey'
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/ri'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveNYCFC(self) -> None:
		""" RETRIEVE [myCertFileCred] """
		r, rsc = RETRIEVE(self.nycfcURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:nycfc/mgd'), T.NYCFC)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesNYCFC(self) -> None:
		""" Test [myCertFileCred] attributes """
		r, rsc = RETRIEVE(self.nycfcURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:nycfc/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:nycfc/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/rn'), self.nycfcRN)
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/dc'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/dc'), 'aNycfc')
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/suids'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/suids/{0}'), 42)
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/mcff'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/mcff'), 'application/pkcs7mime')
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/mcfc'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/mcfc'), 'secretKey')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteNYCFC(self) -> None:
		"""	DELETE [myCertFileCred] """
		_, rsc = DELETE(self.nycfcURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	EVL
	#

	evlRN	= 'EVL'
	evlURL	= f'{nodURL}/{evlRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createEVL(self) -> None:
		"""	CREATE [EventLog] """
		dct =  { 'm2m:evl' : {
					'mgd' : T.EVL,
					'rn'  : self.evlRN,
					'dc'  : 'aEvl',
					'lgt' : 1,
					'lgd' : 'log',
					'lgst': 2
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED)
		self.assertIsNotNone(findXPath(r, 'm2m:evl/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveEVL(self) -> None:
		"""	RETRIEVE [eventLog] """
		r, rsc = RETRIEVE(self.evlURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:evl/mgd'), T.EVL)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesEVL(self) -> None:
		"""	Test [eventLog] attributes """
		r, rsc = RETRIEVE(self.evlURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:evl/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'm2m:evl/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'm2m:evl/rn'), self.evlRN)
		self.assertIsNotNone(findXPath(r, 'm2m:evl/ct'))
		self.assertIsNotNone(findXPath(r, 'm2m:evl/lt'))
		self.assertIsNotNone(findXPath(r, 'm2m:evl/et'))
		self.assertIsNotNone(findXPath(r, 'm2m:evl/dc'))
		self.assertEqual(findXPath(r, 'm2m:evl/dc'), 'aEvl')
		self.assertIsNotNone(findXPath(r, 'm2m:evl/lgt'))
		self.assertEqual(findXPath(r, 'm2m:evl/lgt'), 1)
		self.assertIsNotNone(findXPath(r, 'm2m:evl/lgd'))
		self.assertEqual(findXPath(r, 'm2m:evl/lgd'), 'log')
		self.assertIsNotNone(findXPath(r, 'm2m:evl/lgst'))
		self.assertEqual(findXPath(r, 'm2m:evl/lgst'), 2)
		self.assertIsNotNone(findXPath(r, 'm2m:evl/lga'), r)
		self.assertTrue(findXPath(r, 'm2m:evl/lga'), r)
		self.assertIsNotNone(findXPath(r, 'm2m:evl/lgo'), r)
		self.assertTrue(findXPath(r, 'm2m:evl/lgo'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteEVL(self) -> None:
		""" DELETE [eventLog] """
		_, rsc = DELETE(self.evlURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	WifiClient
	#

	wificRN		= 'WIFIC'
	wificURL	= f'{nodURL}/{wificRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createWIFIC(self) -> None:
		"""	CREATE [wificlient] """
		dct =  { 'dcfg:wific' : {
					'mgd' : T.WIFIC,
					'rn'  : self.wificRN,
					'dc'  : 'aWificlient',
					'ssid':	'aSSID',
					'wcrds': {
						'enct': 8,
						'unm': 'user',
						'pwd': 'pwd',

					}
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/ri'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveWIFIC(self) -> None:
		"""	RETRIEVE [wificlient] """
		r, rsc = RETRIEVE(self.wificURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK, r)
		self.assertEqual(findXPath(r, 'dcfg:wific/mgd'), T.WIFIC, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesWIFIC(self) -> None:
		"""	Test [wificlient] attributes """
		r, rsc = RETRIEVE(self.wificURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'dcfg:wific/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'dcfg:wific/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'dcfg:wific/rn'), self.wificRN)
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/ssid'))
		self.assertEqual(findXPath(r, 'dcfg:wific/ssid'), 'aSSID')
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/wcrds'))
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/wcrds/enct'))
		self.assertEqual(findXPath(r, 'dcfg:wific/wcrds/enct'), 8)
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/wcrds/unm'))
		self.assertEqual(findXPath(r, 'dcfg:wific/wcrds/unm'), 'user')
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/wcrds/pwd'))
		self.assertEqual(findXPath(r, 'dcfg:wific/wcrds/pwd'), 'pwd')
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/scan'))
		self.assertEqual(findXPath(r, 'dcfg:wific/scan'), False)
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/scanr'))
		self.assertEqual(findXPath(r, 'dcfg:wific/scanr'), [])
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/ud'))
		self.assertEqual(findXPath(r, 'dcfg:wific/ud'), False)
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/trdst'))
		self.assertEqual(findXPath(r, 'dcfg:wific/trdst'), False)
		self.assertIsNotNone(findXPath(r, 'dcfg:wific/rdst'))
		self.assertEqual(findXPath(r, 'dcfg:wific/rdst'), False)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteWIFIC(self) -> None:
		""" DELETE [wificlient] """
		_, rsc = DELETE(self.wificURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createWIFICCred1Fail(self) -> None:
		"""	CREATE [wificlient] with wrong creds 1 -> Fails"""
		dct =  { 'dcfg:wific' : {
					'mgd' : T.WIFIC,
					'rn'  : self.wificRN,
					'dc'  : 'aWificlient',
					'ssid':	'aSSID',
					'wcrds': {
						'enct': 2,
						'unm': 'user',
						'pwd': 'pwd',
					}
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createWIFICCred2Fail(self) -> None:
		"""	CREATE [wificlient] with wrong creds 2 -> Fails"""
		dct =  { 'dcfg:wific' : {
					'mgd' : T.WIFIC,
					'rn'  : self.wificRN,
					'dc'  : 'aWificlient',
					'ssid':	'aSSID',
					'wcrds': {
						'enct': 4,
						'wepk': 'user',
					}
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createWIFICCred3Fail(self) -> None:
		"""	CREATE [wificlient] with wrong creds 3 -> Fails"""
		dct =  { 'dcfg:wific' : {
					'mgd' : T.WIFIC,
					'rn'  : self.wificRN,
					'dc'  : 'aWificlient',
					'ssid':	'aSSID',
					'wcrds': {
						'enct': 8,
						'wpap': 'wpa',
					}
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	#
	#	DataCollection
	#

	datcRN		= 'DATC'
	datcURL		= f'{nodURL}/{datcRN}'
	cntPath		= f'{CSERN}/{aeRN}/{cntRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDATC(self) -> None:
		"""	CREATE [dataCollection] """
		dct =  { 'dcfg:datc' : {
					'mgd' : T.DATC,
					'rn'  : self.datcRN,
					'dc'  : 'aDataCollection',
					'cntp': self.cntPath,
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'dcfg:datc/ri'), r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCrpscIntegerFail(self) -> None:
		"""	UPDATE [dataCollection] rpsc with integer value -> FAIL"""
		dct =  { 'dcfg:datc' : {
					'rpsc':	10000,
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCmescIntegerFail(self) -> None:
		"""	UPDATE [dataCollection] mesc with integer value -> FAIL"""
		dct =  { 'dcfg:datc' : {
					'mesc':	10000,
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCrpscInvalidSchedule1Fail(self) -> None:
		"""	UPDATE [dataCollection] rpsc with an invalid schedule -> FAIL"""
		dct =  { 'dcfg:datc' : {
					'rpsc':	[ 10 ],	# must be [ scheduleEntries ]
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCrpscInvalidSchedule2Fail(self) -> None:
		"""	UPDATE [dataCollection] rpsc with an invalid schedule -> FAIL"""
		dct =  { 'dcfg:datc' : {
					'rpsc':	[ { 'sce': [ '10 * * * *' ] } ],	# invalid format, must be 7
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCrpscValidSchedule(self) -> None:
		"""	UPDATE [dataCollection] rpsc with a valid schedule"""
		dct =  { 'dcfg:datc' : {
					'rpsc':	[ { 'sce': [ '10 * * * * * *' ] } ],
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'dcfg:datc/rpsc'), r)
		self.assertIsInstance(findXPath(r, 'dcfg:datc/rpsc'), list, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCrpilWhileRpscFail(self) -> None:
		"""	UPDATE [dataCollection] rpil while rpsc is alread set -> FAIL"""
		dct =  { 'dcfg:datc' : {
					'rpil':	10000,
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCrpscRpilFail(self) -> None:
		"""	UPDATE [dataCollection] rpsc and rpil together -> FAIL"""
		dct =  { 'dcfg:datc' : {
					'rpsc':	[ { 'sce': '10 * * * * * *' } ],
					'rpil': 10000,
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCmescInvalidSchedule1Fail(self) -> None:
		"""	UPDATE [dataCollection] mesc with an invalid schedule -> FAIL"""
		dct =  { 'dcfg:datc' : {
					'mesc':	[ 10 ],	# must be [ scheduleEntries ]
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCmescInvalidSchedule2Fail(self) -> None:
		"""	UPDATE [dataCollection] mesc with an invalid schedule -> FAIL"""
		dct =  { 'dcfg:datc' : {
					'mesc':	[ { 'sce': [ '10 * * * *' ] } ],	# invalid format, must be 7
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCmescValidSchedule(self) -> None:
		"""	UPDATE [dataCollection] mesc with a valid schedule"""
		dct =  { 'dcfg:datc' : {
					'mesc':	[ { 'sce': [ '10 * * * * * *' ] } ],
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNotNone(findXPath(r, 'dcfg:datc/mesc'), r)
		self.assertIsInstance(findXPath(r, 'dcfg:datc/mesc'), list, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCmeilWhileMescFail(self) -> None:
		"""	UPDATE [dataCollection] meil while mesc is alread set -> FAIL"""
		dct =  { 'dcfg:datc' : {
					'meil':	10000,
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCmescMeilFail(self) -> None:
		"""	UPDATE [dataCollection] mesc and meil together -> FAIL"""
		dct =  { 'dcfg:datc' : {
					'mesc':	[ { 'sce': '10 * * * * * *' } ],
					'meil': 10000,
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDATCremoveMescAddMeil(self) -> None:
		"""	UPDATE [dataCollection] remove mesc and and meil"""
		dct =  { 'dcfg:datc' : {
					'mesc':	None,
					'meil': 10000,
				}}
		r, rsc = UPDATE(self.datcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.UPDATED, r)
		self.assertIsNone(findXPath(r, 'dcfg:datc/mesc'), r)
		self.assertIsNotNone(findXPath(r, 'dcfg:datc/meil'), r)
		self.assertEqual(findXPath(r, 'dcfg:datc/meil'), 10000, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesDATC(self) -> None:
		"""	Test [dataCollection] attributes """
		r, rsc = RETRIEVE(self.datcURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'dcfg:datc/ty'), T.MGMTOBJ)
		self.assertEqual(findXPath(r, 'dcfg:datc/pi'), findXPath(TestMgmtObj.nod,'m2m:nod/ri'))
		self.assertEqual(findXPath(r, 'dcfg:datc/rn'), self.datcRN)
		self.assertIsNotNone(findXPath(r, 'dcfg:datc/cntp'))
		self.assertEqual(findXPath(r, 'dcfg:datc/cntp'), self.cntPath, r)
		self.assertIsNone(findXPath(r, 'dcfg:datc/mesc'), r)
		self.assertIsNotNone(findXPath(r, 'dcfg:datc/meil'), r)
		self.assertEqual(findXPath(r, 'dcfg:datc/meil'), 10000, r)
		self.assertIsNotNone(findXPath(r, 'dcfg:datc/rpsc'), r)
		self.assertIsInstance((rpsc := findXPath(r, 'dcfg:datc/rpsc')), list, r)
		self.assertEqual(len(rpsc), 1, r)
		self.assertIsInstance((rpsce := rpsc[0]), dict, r)
		self.assertIsNotNone((sce := rpsce.get('sce')), r)
		self.assertEqual(sce, [ '10 * * * * * *' ], r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteDATC(self) -> None:
		""" DELETE [dataCollection] """
		_, rsc = DELETE(self.datcURL, ORIGINATOR)
		self.assertEqual(rsc, RC.DELETED)




def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()
		
	addTest(suite, TestMgmtObj('test_createFWR'))
	addTest(suite, TestMgmtObj('test_retrieveFWR'))
	addTest(suite, TestMgmtObj('test_attributesFWR'))
	addTest(suite, TestMgmtObj('test_deleteFWR'))
	
	addTest(suite, TestMgmtObj('test_createSWR'))
	addTest(suite, TestMgmtObj('test_retrieveSWR'))
	addTest(suite, TestMgmtObj('test_attributesSWR'))
	addTest(suite, TestMgmtObj('test_deleteSWR'))
	
	addTest(suite, TestMgmtObj('test_createMEM'))
	addTest(suite, TestMgmtObj('test_retrieveMEM'))
	addTest(suite, TestMgmtObj('test_attributesMEM'))
	addTest(suite, TestMgmtObj('test_deleteMEM'))
	
	addTest(suite, TestMgmtObj('test_createANI'))
	addTest(suite, TestMgmtObj('test_retrieveANI'))
	addTest(suite, TestMgmtObj('test_attributesANI'))
	addTest(suite, TestMgmtObj('test_deleteANI'))
	
	addTest(suite, TestMgmtObj('test_createANDI'))
	addTest(suite, TestMgmtObj('test_retrieveANDI'))
	addTest(suite, TestMgmtObj('test_attributesANDI'))
	addTest(suite, TestMgmtObj('test_deleteANDI'))
	
	addTest(suite, TestMgmtObj('test_createBATWrong'))
	addTest(suite, TestMgmtObj('test_createBAT'))
	addTest(suite, TestMgmtObj('test_retrieveBAT'))
	addTest(suite, TestMgmtObj('test_attributesBAT'))
	addTest(suite, TestMgmtObj('test_deleteBAT'))
	
	addTest(suite, TestMgmtObj('test_createDVI'))
	addTest(suite, TestMgmtObj('test_retrieveDVI'))
	addTest(suite, TestMgmtObj('test_attributesDVI'))
	addTest(suite, TestMgmtObj('test_deleteDVI'))
	
	addTest(suite, TestMgmtObj('test_createDVC'))
	addTest(suite, TestMgmtObj('test_retrieveDVC'))
	addTest(suite, TestMgmtObj('test_attributesDVC'))
	addTest(suite, TestMgmtObj('test_updateDVCEnaTrue'))
	addTest(suite, TestMgmtObj('test_updateDVCEnaFalse'))
	addTest(suite, TestMgmtObj('test_updateDVCDisTrue'))
	addTest(suite, TestMgmtObj('test_updateDVCDisFalse'))
	addTest(suite, TestMgmtObj('test_updateDVCEnaDisTrue'))
	addTest(suite, TestMgmtObj('test_updateDVCEnaDisFalse'))
	addTest(suite, TestMgmtObj('test_deleteDVC'))
	
	addTest(suite, TestMgmtObj('test_createRBO'))
	addTest(suite, TestMgmtObj('test_retrieveRBO'))
	addTest(suite, TestMgmtObj('test_attributesRBO'))
	addTest(suite, TestMgmtObj('test_updateRBORboTrue'))
	addTest(suite, TestMgmtObj('test_updateRBORboFalse'))
	addTest(suite, TestMgmtObj('test_updateRBOFarTrue'))
	addTest(suite, TestMgmtObj('test_updateRBOFarFalse'))
	addTest(suite, TestMgmtObj('test_updateRBORboFarTrue'))
	addTest(suite, TestMgmtObj('test_updateRBORboFarFalse'))
	addTest(suite, TestMgmtObj('test_deleteRBO'))
	
	addTest(suite, TestMgmtObj('test_createNYCFCwrongSUID'))
	addTest(suite, TestMgmtObj('test_createNYCFC'))
	addTest(suite, TestMgmtObj('test_retrieveNYCFC'))
	addTest(suite, TestMgmtObj('test_attributesNYCFC'))
	addTest(suite, TestMgmtObj('test_deleteNYCFC'))

	addTest(suite, TestMgmtObj('test_createEVL'))
	addTest(suite, TestMgmtObj('test_retrieveEVL'))
	addTest(suite, TestMgmtObj('test_attributesEVL'))
	addTest(suite, TestMgmtObj('test_deleteEVL'))

	addTest(suite, TestMgmtObj('test_createWIFIC'))
	addTest(suite, TestMgmtObj('test_retrieveWIFIC'))
	addTest(suite, TestMgmtObj('test_attributesWIFIC'))
	addTest(suite, TestMgmtObj('test_deleteWIFIC'))
	addTest(suite, TestMgmtObj('test_createWIFICCred1Fail'))
	addTest(suite, TestMgmtObj('test_createWIFICCred2Fail'))
	addTest(suite, TestMgmtObj('test_createWIFICCred3Fail'))

	addTest(suite, TestMgmtObj('test_createDATC'))
	addTest(suite, TestMgmtObj('test_updateDATCrpscIntegerFail'))
	addTest(suite, TestMgmtObj('test_updateDATCmescIntegerFail'))
	addTest(suite, TestMgmtObj('test_updateDATCrpscInvalidSchedule1Fail'))
	addTest(suite, TestMgmtObj('test_updateDATCrpscInvalidSchedule2Fail'))
	addTest(suite, TestMgmtObj('test_updateDATCrpscValidSchedule'))
	addTest(suite, TestMgmtObj('test_updateDATCrpilWhileRpscFail'))
	addTest(suite, TestMgmtObj('test_updateDATCrpscRpilFail'))
	addTest(suite, TestMgmtObj('test_updateDATCmescInvalidSchedule1Fail'))
	addTest(suite, TestMgmtObj('test_updateDATCmescInvalidSchedule2Fail'))
	addTest(suite, TestMgmtObj('test_updateDATCmescValidSchedule'))
	addTest(suite, TestMgmtObj('test_updateDATCmeilWhileMescFail'))
	addTest(suite, TestMgmtObj('test_updateDATCmescMeilFail'))
	addTest(suite, TestMgmtObj('test_updateDATCremoveMescAddMeil'))
	addTest(suite, TestMgmtObj('test_attributesDATC'))
	addTest(suite, TestMgmtObj('test_deleteDATC'))

	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)
