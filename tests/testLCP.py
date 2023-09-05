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
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, TimeWindowType
from acme.etc.Types import NotificationEventType, NotificationEventType as NET
from init import *
		

pointInside = {
	'type' : 'Point',
	'coordinates' : [ 52.520817, 13.409446 ]
}

pointInsideStr = json.dumps(pointInside)

pointOutside = {
	'type' : 'Point',
	'coordinates' : [ 52.505033, 13.278189 ]
}
pointOutsideStr = json.dumps(pointOutside)

targetPoligon = {
	'type' : 'Polygon',
	'coordinates' : [
		[ [52.522423, 13.409468], [52.520634, 13.412107], [52.518362, 13.407172], [52.520086, 13.404897] ]
	]
}
targetPoligonStr = json.dumps(targetPoligon)

# TODO wrong poligon, wrong point


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
		  		'los': 2,							# device based
				'gta': targetPoligonStr	# geoTargetArea
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
				'gta': targetPoligonStr,# geoTargetArea
				'gec': 2				# geoEventCategory	= 2 (leaving). Assuming that the initial location is inside the target area


		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/lost'))
		self.assertEqual(findXPath(r, 'm2m:lcp/lost'), '')
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/loi'), '')

		# Add a location ContentInstance
		dct = { 'm2m:cin': { 
				'con': pointOutsideStr 
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Just wait a moment
		testSleep(2)

		# Retrieve the latest location ContentInstance to check the event
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:cin/con'))
		self.assertEqual(findXPath(r, 'm2m:cin/con'), '2', r)	# leaving


		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)


# TODO add test: move from inside to inside -> no notification
# TODO add test: move from inside to outside -> notification
# TODO add test: move from outside to inside -> notification
# TODO add test: move from outside to outside -> no notification

# TODO test with invalid location format



	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_testManualUpdates(self) -> None:
		"""	CREATE <LCP> with lit = 2, lou = None """

		dct = { 'm2m:lcp': {
		  		'rn': lcpRN,
		  		'los': 2,				# device based
				'lit': 2,				# locationInformationType = 2 (geo-fence)
				'lon': cntRN,			# containerName
				'gta': targetPoligonStr,# geoTargetArea
				'gec': 2				# geoEventCategory	= 2 (leaving). Assuming that the initial location is inside the target area
		}}
		r, rsc = CREATE(aeURL, self.originator, T.LCP, dct)
		self.assertEqual(rsc, RC.CREATED, r)
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/lost'))
		self.assertEqual(findXPath(r, 'm2m:lcp/lost'), '')
		self.assertIsNotNone(findXPath(r, 'm2m:lcp/loi'), '')

		# Add a location ContentInstance
		dct = { 'm2m:cin': { 
				'con': pointOutsideStr 
		}}
		r, rsc = CREATE(f'{aeURL}/{cntRN}', self.originator, T.CIN, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# Retrieve <latest> 
		r, rsc = RETRIEVE(f'{aeURL}/{cntRN}/la', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		latest = findXPath(r, 'm2m:cin/con')
		print(latest)


		# Just wait a moment
		testSleep(2)

		# TODO receive result?

		_, rsc = DELETE(lcpURL, self.originator)
		self.assertEqual(rsc, RC.DELETED)



	#########################################################################



def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()

	# basic tests
	addTest(suite, TestLCP('test_createLCPMissingLosFail'))
	addTest(suite, TestLCP('test_createMinimalLCP'))
	addTest(suite, TestLCP('test_createLCPWithSameCNTRnFail'))
	addTest(suite, TestLCP('test_createLCPWithLOS2LotFail'))
	addTest(suite, TestLCP('test_createLCPWithLOS2AidFail'))
	addTest(suite, TestLCP('test_createLCPWithLOS2LorFail'))
	addTest(suite, TestLCP('test_createLCPWithLOS2RlklFail'))
	addTest(suite, TestLCP('test_createLCPWithLOS2LuecFail'))
	addTest(suite, TestLCP('test_createLCPWithWrongGtaFail'))
	addTest(suite, TestLCP('test_createLCPWithGta'))

	# periodic tests
	addTest(suite, TestLCP('test_createLCPWithLit2Lou0'))
	addTest(suite, TestLCP('test_testPeriodicUpdates'))
	addTest(suite, TestLCP('test_testManualUpdates'))


	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)