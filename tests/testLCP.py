#
#	testLCP.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for LocationPolicy functionality
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acmecse.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *
		

pointInside = {
	'type' : 'Point',
	'coordinates' : [ 52.520817, 13.409446 ]
}

pointInside2 = {
	'type' : 'Point',
	'coordinates' : [ 52.520957, 13.411500 ]
}

pointOutside = {
	'type' : 'Point',
	'coordinates' : [ 52.505033, 13.278189 ]
}

pointOutside2 = {
	'type' : 'Point',
	'coordinates' : [ 52.506500, 13.283000 ]
}


targetPoligon = {
	'type' : 'Polygon',
	'coordinates' : [
		[ [52.522423, 13.409468], [52.520634, 13.412107], [52.518362, 13.407172], [52.520086, 13.404897] ]
	]
}


class TestLCP(unittest.TestCase):

	ae 			= None
	aeRI		= None
	ae2 		= None
	nod 		= None
	nodRI		= None
	crs			= None
	crsRI		= None


	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestLCP')

		# Start notification server
		startNotificationServer()

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

		testCaseEnd('Setup TestLCP')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		if not isTearDownEnabled():
			stopNotificationServer()
			return
		testCaseStart('TearDown TestLCP')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestLCP')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)

	#########################################################################

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createLCPMissingLosFail(self) -> None:
		"""	CREATE invalid <LCP> with missing los -> Fail"""

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'lou': [ 'PT5S' ],
				'lon': 'myLocationContainer'
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createMinimalLCP(self) -> None:
		"""	CREATE minimal <LCP> with missing lou"""

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,	# device based
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/lost'))
		self.assertEqual(findXPath(r, 'm2m:lcp/lost'), '')

		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createLCPWithSameCNTRnFail(self) -> None:
		"""	CREATE <LCP> with assigned container RN as self -> Fail """

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,	# device based
				'lon': lcpRN
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createLCPWithLOS2LotFail(self) -> None:
		"""	CREATE <LCP> with los=2 (device based) and set lot -> Fail """

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,		# device based
				'lot': '1234'	# locationTargetID
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createLCPWithLOS2AidFail(self) -> None:
		"""	CREATE <LCP> with los=2 (device based) and set aid -> Fail """

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,		# device based
				'aid': '1234'	# authID
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createLCPWithLOS2LorFail(self) -> None:
		"""	CREATE <LCP> with los=2 (device based) and set lor -> Fail """

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,		# device based
				'lor': '1234'	# locationServer
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createLCPWithLOS2RlklFail(self) -> None:
		"""	CREATE <LCP> with los=2 (device based) and set rlkl -> Fail """

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,		# device based
				'rlkl': True	# retrieveLastKnownLocation
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createLCPWithLOS2LuecFail(self) -> None:
		"""	CREATE <LCP> with los=2 (device based) and set luec -> Fail """

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,		# device based
				'luec': 0	# locationUpdateEventCriteria
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createLCPWithWrongGtaFail(self) -> None:
		"""	CREATE <LCP> with wrong gta -> Fail"""

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,		# device based
				'gta': 'wrong'	# geoTargetArea
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createLCPWithGta(self) -> None:
		"""	CREATE <LCP> with gta """

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,				# device based
				'gta': targetPoligon	# geoTargetArea
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/gta'))

		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)


	#
	#	Periodic tests
	#

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createLCPWithLit2Lou0(self) -> None:
		"""	CREATE <LCP> with lit = 2, lou = 0s"""

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,	# device based
				'lit': 2,	# locationInformationType = 2 (geo-fence)
				'lou': [ 'PT0S' ]	# locationUpdatePeriod = 0s,
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/lost'))
		self.assertEqual(findXPath(r, 'm2m:lcp/lost'), '')

		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testPeriodicUpdates(self) -> None:
		"""	CREATE <LCP> with lit = 2, lou = 1s"""

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,				# device based
				'lit': 2,				# locationInformationType = 2 (geo-fence)
				'lou': [ 'PT1S' ],		# locationUpdatePeriod = 1s
				'lon': cntRN,			# containerName
				'gta': targetPoligon,	# geoTargetArea
				'gec': 2				# geoEventCategory	= 2 (leaving). Assuming that the initial location is inside the target area


		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/lost'))
		self.assertEqual(findXPath(r, 'm2m:lcp/lost'), '')
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/loi'), '')

		# Add a location ContentInstance
		dct = { 'm2m:cin': { 
				'con': pointOutside
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Just wait a moment
		testSleep(2)

		# Retrieve the latest location ContentInstance to check the event
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 2, r)	# leaving


		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testManualUpdates(self) -> None:
		"""	CREATE <LCP> with lit = 2, lou = None """

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,				# device based
				'lit': 2,				# locationInformationType = 2 (geo-fence)
				'lon': cntRN,			# containerName
				'gta': targetPoligon,	# geoTargetArea
				'gec': 2				# geoEventCategory	= 2 (leaving). Assuming that the initial location is inside the target area
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/lost'))
		self.assertEqual(findXPath(r, 'm2m:lcp/lost'), '')
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/loi'), '')

		# Add a location ContentInstance
		dct = { 'm2m:cin': { 
				'con': pointOutside 
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual( findXPath(r, 'm2m:cin/con'), 2, r)	# leaving

		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testManualInsideEvent(self) -> None:
		"""	CREATE <LCP> gec = 3 (inside) and expect inside event"""

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,				# device based
				'lit': 2,				# locationInformationType = 2 (geo-fence)
				'lon': cntRN,			# containerName
				'gta': targetPoligon,	# geoTargetArea
				'gec': 3				# geoEventCategory	= 3 (inside). Assuming that the initial location is inside the target area
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/lost'))
		self.assertEqual(findXPath(r, 'm2m:lcp/lost'), '')
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/loi'), '')

		# Add a location ContentInstance
		dct = { 'm2m:cin': { 
				'con': pointInside 
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 3, r)	# inside event expected

		#
		# Add a second location inside ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointInside2
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 3, r)	# inside event expected
		
		#
		# Add an outside location ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointOutside
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 2, r)	# leaving NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)
		
		#
		# Add a second outside location ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointOutside2
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 4, r)	# outside NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)

		#
		# Add an inside location ContentInstance again
		#
		dct = { 'm2m:cin': { 
				'con': pointInside
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 1, r)	# entering NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)

		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testManualOutsideEvent(self) -> None:
		"""	CREATE <LCP> gec = 4 (outside) and expect outside event"""

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,				# device based
				'lit': 2,				# locationInformationType = 2 (geo-fence)
				'lon': cntRN,			# containerName
				'gta': targetPoligon,	# geoTargetArea
				'gec': 4				# geoEventCategory	= 4 (outside). Assuming that the initial location is insode the target area
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/lost'))
		self.assertEqual(findXPath(r, 'm2m:lcp/lost'), '')
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/loi'), '')

		# Add a location ContentInstance
		dct = { 'm2m:cin': { 
				'con': pointInside 
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 3, r)	# inside event NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)

		#
		# Add a second location inside ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointInside2
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 3, r)	# inside event NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)
		
		#
		# Add an outside location ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointOutside
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 2, r)	# leaving NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)
		
		#
		# Add a second outside location ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointOutside2
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 4, r)	# outside expected

		#
		# Add an inside location ContentInstance again
		#
		dct = { 'm2m:cin': { 
				'con': pointInside
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 1, r)	# entering NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)

		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testManualLeavingEvent(self) -> None:
		"""	CREATE <LCP> gec = 1 (leaving) and expect leaving event"""

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,				# device based
				'lit': 2,				# locationInformationType = 2 (geo-fence)
				'lon': cntRN,			# containerName
				'gta': targetPoligon,	# geoTargetArea
				'gec': 2				# geoEventCategory	= 2 (leaving). Assuming that the initial location is inside the target area
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/lost'))
		self.assertEqual(findXPath(r, 'm2m:lcp/lost'), '')
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/loi'), '')

		# Add a location ContentInstance
		dct = { 'm2m:cin': { 
				'con': pointInside 
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 3, r)	# inside event NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)

		#
		# Add a second location inside ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointInside2
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 3, r)	# inside event NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)
		
		#
		# Add an outside location ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointOutside
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 2, r)	# leaving expected
		
		#
		# Add a second outside location ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointOutside2
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 4, r)	# outside NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)

		#
		# Add an inside location ContentInstance again
		#
		dct = { 'm2m:cin': { 
				'con': pointInside
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 1, r)	# entering NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)

		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testManualEnteringEvent(self) -> None:
		"""	CREATE <LCP> gec = 2 (entering) and expect entering event"""

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,				# device based
				'lit': 2,				# locationInformationType = 2 (geo-fence)
				'lon': cntRN,			# containerName
				'gta': targetPoligon,	# geoTargetArea
				'gec': 1				# geoEventCategory	= 2 (entering). Assuming that the initial location is inside the target area
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/lost'))
		self.assertEqual(findXPath(r, 'm2m:lcp/lost'), '')
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/loi'), '')

		# Add a location ContentInstance
		dct = { 'm2m:cin': { 
				'con': pointInside 
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 3, r)	# inside event NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)

		#
		# Add a second location inside ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointInside2
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 3, r)	# inside event NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)
		
		#
		# Add an outside location ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointOutside
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 2, r)	# leaving NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)
		
		#
		# Add a second outside location ContentInstance
		#
		dct = { 'm2m:cin': { 
				'con': pointOutside2
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertNotEqual(findXPath(r, 'm2m:cin/con'), 4, r)	# outside NOT expected
		self.assertIsInstance(findXPath(r, 'm2m:cin/con'), dict, r)

		#
		# Add an inside location ContentInstance again
		#
		dct = { 'm2m:cin': { 
				'con': pointInside
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), 1, r)	# entering expected

		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)


	#########################################################################

# TODO test with invalid location format
# TODO wrong poligon, wrong point


def run(testFailFast:bool) -> TestResult:

	# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestLCP, [

		# basic tests
		'test_createLCPMissingLosFail',
		'test_createMinimalLCP',
		'test_createLCPWithSameCNTRnFail',
		'test_createLCPWithLOS2LotFail',
		'test_createLCPWithLOS2AidFail',
		'test_createLCPWithLOS2LorFail',
		'test_createLCPWithLOS2RlklFail',
		'test_createLCPWithLOS2LuecFail',
		'test_createLCPWithWrongGtaFail',
		'test_createLCPWithGta',

		# periodic tests
		'test_createLCPWithLit2Lou0',
		'test_testPeriodicUpdates',
		'test_testManualUpdates',

		# Moving inside and outside
		'test_testManualInsideEvent',
		'test_testManualOutsideEvent',
		'test_testManualLeavingEvent',
		'test_testManualEnteringEvent',
	])

	# Run tests
	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)