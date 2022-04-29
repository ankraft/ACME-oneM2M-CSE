#
#	testMgmtObj.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for all kind of MgmtObj specialisations
#

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
		dct = 	{ 'm2m:nod' : { 
					'rn' 	: nodRN,
					'ni'	: nodeID
				}}
		cls.nod, rsc = CREATE(cseURL, ORIGINATOR, T.NOD, dct)
		assert rsc == RC.created, 'cannot create <node>'


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		DELETE(nodURL, ORIGINATOR)	# Just delete the Node and everything below it. Ignore whether it exists or not

	#
	#	FWR
	#

	fwrRN	= 'fwr'
	fwrURL	= f'{nodURL}/{fwrRN}'


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createFWR(self) -> None:
		"""	Create [Firmware] """
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
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:fwr/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveFWR(self) -> None:
		"""	Retrieve [Firmware] """
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
		"""	Delete [Firmware] """
		_, rsc = DELETE(self.fwrURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)

	#
	#	SWR
	#

	swrRN	= 'swr'
	swrURL	= f'{nodURL}/{swrRN}'


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createSWR(self) -> None:
		"""Create [Software] """
		dct =  { 'm2m:swr' : {
					'mgd' : T.SWR,
					'rn' : self.swrRN,
					'dc' : 'aSwr',
					'vr' : '1234',
					'swn': 'mySwr',
					'url': 'example.com'
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:swr/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveSWR(self) -> None:
		"""	Retrieve [Software] """
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
		"""	Delete [Software] """
		_, rsc = DELETE(self.swrURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	#
	#	MEM
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createMEM(self) -> None:
		""" Create [Memory] """
		dct =  { 'm2m:mem' : {
					'mgd' : T.MEM,
					'rn' : memRN,
					'dc' : 'aMem',
					'mma' : 1234,
					'mmt' : 4321
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:mem/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveMEM(self) -> None:
		"""	Retrieve [Memory] """
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
		""" Delete [Memory] """
		_, rsc = DELETE(memURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)

	#
	#	ANI
	#

	aniRN	= 'ANI'
	aniURL	= f'{nodURL}/{aniRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createANI(self) -> None:
		""" Create [areaNwkInfo] """
		dct =  { 'm2m:ani' : {
					'mgd' : T.ANI,
					'rn' : self.aniRN,
					'dc' : 'aAni',
					'ant' : 'aniType',
					'ldv' : [ 'dev1', 'dev2' ]
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:ani/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveANI(self) -> None:
		""" Retrieve [areaNwkInfo] """
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
		"""	Delete [areaNwkInfo] """
		_, rsc = DELETE(self.aniURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	#
	#	ANDI
	#

	andiRN	= 'ANDI'
	andiURL	= f'{nodURL}/{andiRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createANDI(self) -> None:
		""" Create [areaNwkDeviceInfo] """
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
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:andi/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveANDI(self) -> None:
		""" Retrieve [areaNwkDeviceInfo] """
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
		""" Delete [areaNwkDeviceInfo] """
		_, rsc = DELETE(self.andiURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	#
	#	BAT
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createBAT(self) -> None:
		""" Create [battery] """
		dct =  { 'm2m:bat' : {
					'mgd' : T.BAT,
					'rn'  : batRN,
					'dc'  : 'aBat',
					'btl' : 23,
					'bts' : 5
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/ri'))
		self.assertEqual(findXPath(r, 'm2m:bat/ty'), T.MGMTOBJ)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveBAT(self) -> None:
		""" Retrieve [battery] """
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
		""" Delete [battery] """
		_, rsc = DELETE(batURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	#
	#	DVI
	#

	dviRN	= 'DVI'
	dviURL	= f'{nodURL}/{dviRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDVI(self) -> None:
		"""	Create [deviceInfo] """
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
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:dvi/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveDVI(self) -> None:
		""" Retrieve [deviceInfo] """
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
		""" Delete [deviceInfo] """
		_, rsc = DELETE(self.dviURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	#
	#	DVC
	#

	dvcRN	= 'DVC'
	dvcURL	= f'{nodURL}/{dvcRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createDVC(self) -> None:
		""" Create [deviceCapability] """
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
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:dvc/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveDVC(self) -> None:
		""" Retrieve [deviceCapability] """
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
		""" Update [deviceCapability] ENA=False """
		dct =  { 'm2m:dvc' : {
					'ena' : True,
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertTrue(findXPath(r, 'm2m:dvc/ena'))
		self.assertTrue(findXPath(r, 'm2m:dvc/dis'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDVCEnaFalse(self) -> None:
		""" Update [deviceCapability] ENA=False """
		dct =  { 'm2m:dvc' : {
					'ena' : False,
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertTrue(findXPath(r, 'm2m:dvc/ena'))
		self.assertTrue(findXPath(r, 'm2m:dvc/dis'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDVCDisTrue(self) -> None:
		""" Test [deviceCapability] DIS """
		dct =  { 'm2m:dvc' : {
					'dis' : True
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertTrue(findXPath(r, 'm2m:dvc/ena'))
		self.assertTrue(findXPath(r, 'm2m:dvc/dis'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDVCDisFalse(self) -> None:
		""" Test [deviceCapability] DIS """
		dct =  { 'm2m:dvc' : {
					'dis' : False
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
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
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateDVCEnaDisFalse(self) -> None:
		"""	Update [deviceCapability] ENA=False & DIS=False -> ENA=True & DIS=True """
		dct =  { 'm2m:dvc' : {
					'ena' : False,
					'dis' : False
				}}
		r, rsc = UPDATE(self.dvcURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertTrue(findXPath(r, 'm2m:dvc/ena'))
		self.assertTrue(findXPath(r, 'm2m:dvc/dis'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteDVC(self) -> None:
		"""	Delete [deviceCapability] """
		_, rsc = DELETE(self.dvcURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	#
	#	RBO
	#

	rboRN	= 'RBO'
	rboURL	= f'{nodURL}/{rboRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createRBO(self) -> None:
		"""	Create [reboot] """
		dct =  { 'm2m:rbo' : {
					'mgd' : T.RBO,
					'rn'  : self.rboRN,
					'dc'  : 'aRbo',

					'rbo' : False,
					'far' : False
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:rbo/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveRBO(self) -> None:
		"""	Retrieve [reboot] """
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
		"""	Update [reboot] with RBO=True -> RBO=False """
		dct =  { 'm2m:rbo' : {
					'rbo' : True,
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBORboFalse(self) -> None:
		""" Update [reboot] with RBO=False -> RBO=False """
		dct =  { 'm2m:rbo' : {
					'rbo' : False,
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBOFarTrue(self) -> None:
		"""	Update [reboot] FAR=True -> FAR=False """
		dct =  { 'm2m:rbo' : {
					'far' : True
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBOFarFalse(self) -> None:
		"""	Update [reboot] FAR=False -> FAR=False """
		dct =  { 'm2m:rbo' : {
					'far' : False
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBORboFarTrue(self) -> None:
		""" Update [reboot] with RBO=True & FAR=True -> Fail """
		dct =  { 'm2m:rbo' : {
					'rbo' : True,
					'far' : True
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.badRequest)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_updateRBORboFarFalse(self) -> None:
		""" Update [reboot] with RBO=False & FAR=False  -> RBO=False & FAR=False """
		dct =  { 'm2m:rbo' : {
					'rbo' : False,
					'far' : False
				}}
		r, rsc = UPDATE(self.rboURL, ORIGINATOR, dct)
		self.assertEqual(rsc, RC.updated)
		self.assertFalse(findXPath(r, 'm2m:rbo/rbo'))
		self.assertFalse(findXPath(r, 'm2m:rbo/far'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteRBO(self) -> None:
		"""	Delete [reboot] """
		_, rsc = DELETE(self.rboURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	#
	#	NYCFC
	#

	nycfcRN		= 'nycfc'
	nycfcURL	= f'{nodURL}/{nycfcRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createNYCFC(self) -> None:
		"""	Create [myCertFileCred] """
		dct =  { 'm2m:nycfc' : {
					'mgd' : T.NYCFC,
					'rn' : self.nycfcRN,
					'dc' : 'aNycfc',
					'suids' : [ 99 ],
					'mcff' : 'application/pkcs7mime',
					'mcfc' : 'secretKey'
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveNYCFC(self) -> None:
		""" Retrieve [myCertFileCred] """
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
		self.assertEqual(findXPath(r, 'm2m:nycfc/suids/{0}'), 99)
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/mcff'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/mcff'), 'application/pkcs7mime')
		self.assertIsNotNone(findXPath(r, 'm2m:nycfc/mcfc'))
		self.assertEqual(findXPath(r, 'm2m:nycfc/mcfc'), 'secretKey')


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteNYCFC(self) -> None:
		"""	Delete [myCertFileCred] """
		_, rsc = DELETE(self.nycfcURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)


	#
	#	EVL
	#

	evlRN	= 'EVL'
	evlURL	= f'{nodURL}/{evlRN}'

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createEVL(self) -> None:
		"""	Create [EventLog] """
		dct =  { 'm2m:bat' : {
					'mgd' : T.BAT,
					'rn'  : batRN,
					'dc'  : 'aBat',
					'btl' : 23,
					'bts' : 5
				}}
		r, rsc = CREATE(nodURL, ORIGINATOR, T.MGMTOBJ, dct)
		self.assertEqual(rsc, RC.created)
		self.assertIsNotNone(findXPath(r, 'm2m:bat/ri'))


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveEVL(self) -> None:
		"""	Retrieve [eventLog] """
		r, rsc = RETRIEVE(batURL, ORIGINATOR)
		self.assertEqual(rsc, RC.OK)
		self.assertEqual(findXPath(r, 'm2m:bat/mgd'), T.BAT)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_attributesEVL(self) -> None:
		"""	Test [eventLog] attributes """
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
	def test_deleteEVL(self) -> None:
		""" Delete [eventLog] """
		_, rsc = DELETE(batURL, ORIGINATOR)
		self.assertEqual(rsc, RC.deleted)




def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
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
	suite.addTest(TestMgmtObj('test_createBAT'))
	suite.addTest(TestMgmtObj('test_retrieveBAT'))
	suite.addTest(TestMgmtObj('test_attributesBAT'))
	suite.addTest(TestMgmtObj('test_deleteBAT'))
	suite.addTest(TestMgmtObj('test_createDVI'))
	suite.addTest(TestMgmtObj('test_retrieveDVI'))
	suite.addTest(TestMgmtObj('test_attributesDVI'))
	suite.addTest(TestMgmtObj('test_deleteDVI'))
	suite.addTest(TestMgmtObj('test_createDVC'))
	suite.addTest(TestMgmtObj('test_retrieveDVC'))
	suite.addTest(TestMgmtObj('test_attributesDVC'))
	suite.addTest(TestMgmtObj('test_updateDVCEnaTrue'))
	suite.addTest(TestMgmtObj('test_updateDVCEnaFalse'))
	suite.addTest(TestMgmtObj('test_updateDVCDisTrue'))
	suite.addTest(TestMgmtObj('test_updateDVCDisFalse'))
	suite.addTest(TestMgmtObj('test_updateDVCEnaDisTrue'))
	suite.addTest(TestMgmtObj('test_updateDVCEnaDisFalse'))
	suite.addTest(TestMgmtObj('test_deleteDVC'))
	suite.addTest(TestMgmtObj('test_createRBO'))
	suite.addTest(TestMgmtObj('test_retrieveRBO'))
	suite.addTest(TestMgmtObj('test_attributesRBO'))
	suite.addTest(TestMgmtObj('test_updateRBORboTrue'))
	suite.addTest(TestMgmtObj('test_updateRBORboFalse'))
	suite.addTest(TestMgmtObj('test_updateRBOFarTrue'))
	suite.addTest(TestMgmtObj('test_updateRBOFarFalse'))
	suite.addTest(TestMgmtObj('test_updateRBORboFarTrue'))
	suite.addTest(TestMgmtObj('test_updateRBORboFarFalse'))
	suite.addTest(TestMgmtObj('test_deleteRBO'))
	suite.addTest(TestMgmtObj('test_createNYCFC'))
	suite.addTest(TestMgmtObj('test_retrieveNYCFC'))
	suite.addTest(TestMgmtObj('test_attributesNYCFC'))
	suite.addTest(TestMgmtObj('test_deleteNYCFC'))
	suite.addTest(TestMgmtObj('test_createEVL'))
	suite.addTest(TestMgmtObj('test_retrieveEVL'))
	suite.addTest(TestMgmtObj('test_attributesEVL'))
	suite.addTest(TestMgmtObj('test_deleteEVL'))
	
		
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)


if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
