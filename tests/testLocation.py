#
#	testLocation.py
#
#	(c) 2023 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for geo-query functionality and queries
#

import unittest, sys
if '..' not in sys.path:
	sys.path.append('..')
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC
from init import *
		

class TestLocation(unittest.TestCase):

	ae 			= None
	aeRI		= None

	originator 	= None

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		testCaseStart('Setup TestLocation')

		# Start notification server
		#startNotificationServer()

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

		dct = 	{ 'm2m:cnt' : {
					'rn'  : f'{cntRN}2'
				}}
		cls.ae, rsc = CREATE(aeURL, cls.originator, T.CNT, dct)	# Extra CNT. Acts as a non-location enabled resource
		assert rsc == RC.CREATED, 'cannot create CNT'

		testCaseEnd('Setup TestLocation')


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		# if not isTearDownEnabled():
		# 	stopNotificationServer()
		# 	return
		testCaseStart('TearDown TestLocation')
		DELETE(aeURL, ORIGINATOR)	# Just delete the AE and everything below it. Ignore whether it exists or not
		testCaseEnd('TearDown TestLocation')


	def setUp(self) -> None:
		testCaseStart(self._testMethodName)
	

	def tearDown(self) -> None:
		testCaseEnd(self._testMethodName)

	#########################################################################

	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createContainerWrongLocFail(self) -> None:
		"""	CREATE <CNT> with invalid location  -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': 'wrong',
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	#
	#	Point
	#

	def test_createContainerLocWrongAttributesFail(self) -> None:
		"""	CREATE <CNT> with location & wrong attributes  -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[ 1.0, 2.0 ]',
					  'wrong': 'wrong'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocPointIntCoordinatesFail(self) -> None:
		"""	CREATE <CNT> with location type Point & and integer values  -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[ 1, 2 ]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocPointWrongCountFail(self) -> None:
		"""	CREATE <CNT> with location type Point & multiple coordinates  -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[[ 1.0, 2.0 ], [ 3.0, 4.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocPoint(self) -> None:
		"""	CREATE <CNT> with location type Point """

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[ 1.0, 2.0 ]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		self.assertEqual(findXPath(r, 'm2m:cnt/loc/typ'), 1, r)
		self.assertEqual(findXPath(r, 'm2m:cnt/loc/crd'), '[ 1.0, 2.0 ]', r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	# LineString
	#

	def test_createContainerLocLineStringWrongCountFail(self) -> None:
		"""	CREATE <CNT> with location type LineString & 1 coordinate -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 2,
					  'crd': '[[ 1.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocLineString(self) -> None:
		"""	CREATE <CNT> with location type LineString & 2 coordinates"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 2,
					  'crd': '[[ 1.0, 2.0 ], [ 3.0, 4.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		self.assertEqual(findXPath(r, 'm2m:cnt/loc/typ'), 2, r)
		self.assertEqual(findXPath(r, 'm2m:cnt/loc/crd'), '[[ 1.0, 2.0 ], [ 3.0, 4.0 ]]', r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)

	#
	# Polygon
	#

	def test_createContainerLocPolygonWrongCountFail(self) -> None:
		"""	CREATE <CNT> with location type Polygon & 1 coordinate -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 1.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocPolygonWrongFirstLastCoordinateFail(self) -> None:
		"""	CREATE <CNT> with location type Polygon & not matching first and last coordinate -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 1.0, 2.0 ], [ 3.0, 4.0 ], [ 5.0, 6.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocPolygon(self) -> None:
		"""	CREATE <CNT> with location type Polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 1.0, 2.0 ], [ 3.0, 4.0 ], [ 5.0, 6.0 ], [ 1.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		self.assertEqual(findXPath(r, 'm2m:cnt/loc/typ'), 3, r)
		self.assertEqual(findXPath(r, 'm2m:cnt/loc/crd'), '[[ 1.0, 2.0 ], [ 3.0, 4.0 ], [ 5.0, 6.0 ], [ 1.0, 2.0 ]]', r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	# Multipoint
	#

	def test_createContainerLocMultiPointWrongFail(self) -> None:
		"""	CREATE <CNT> with location type MultiPoint & wrong coordinate -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 4,
					  'crd': '[1.0, 2.0 ]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocMultiPointWrongCountFail(self) -> None:
		"""	CREATE <CNT> with location type MultiPoint & wrong count  -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 4,
					  'crd': '[ [ [1.0, 2.0 ], [ 3.0, 4.0 ] ] ]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocMultiPoint(self) -> None:
		"""	CREATE <CNT> with location type MultiPoint"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 4,
					  'crd': '[[ 1.0, 2.0 ], [ 3.0, 4.0 ], [ 5.0, 6.0 ], [ 1.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		self.assertEqual(findXPath(r, 'm2m:cnt/loc/typ'), 4, r)
		self.assertEqual(findXPath(r, 'm2m:cnt/loc/crd'), '[[ 1.0, 2.0 ], [ 3.0, 4.0 ], [ 5.0, 6.0 ], [ 1.0, 2.0 ]]', r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)



	#
	# MultiLineString
	#

	def test_createContainerLocMultiLineStringWrongFail(self) -> None:
		"""	CREATE <CNT> with location type MultiLineString & wrong coordinate -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[1.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocMultiLineString2WrongFail(self) -> None:
		"""	CREATE <CNT> with location type MultiLineString & wrong coordinate -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[[1.0, 2.0 ]]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocMultiLineString(self) -> None:
		"""	CREATE <CNT> with location type MultiLineString"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[[ 1.0, 2.0 ], [ 3.0, 4.0 ]], [[ 5.0, 6.0 ], [ 7.0, 8.0 ]]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		self.assertEqual(findXPath(r, 'm2m:cnt/loc/typ'), 5, r)
		self.assertEqual(findXPath(r, 'm2m:cnt/loc/crd'), '[[[ 1.0, 2.0 ], [ 3.0, 4.0 ]], [[ 5.0, 6.0 ], [ 7.0, 8.0 ]]]', r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	#
	# MultiPolygon
	#

	def test_createContainerLocMultiPolygonWrongFail(self) -> None:
		"""	CREATE <CNT> with location type MultiPolygon & wrong coordinate -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 6,
					  'crd': '[[1.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocMultiPolygonWrongFirstLastCoordinateFail(self) -> None:
		"""	CREATE <CNT> with location type MultiPolygon & not matching first and last coordinate -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 6,
					  'crd': '[[[ 1.0, 2.0 ], [ 3.0, 4.0 ], [ 5.0, 6.0 ]]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_createContainerLocMultiPolygon(self) -> None:
		"""	CREATE <CNT> with location type MultiPolygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 6,
					  'crd': '[[[ 1.0, 2.0 ], [ 3.0, 4.0 ], [ 5.0, 6.0 ], [ 1.0, 2.0 ]]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		self.assertEqual(findXPath(r, 'm2m:cnt/loc/typ'), 6, r)
		self.assertEqual(findXPath(r, 'm2m:cnt/loc/crd'), '[[[ 1.0, 2.0 ], [ 3.0, 4.0 ], [ 5.0, 6.0 ], [ 1.0, 2.0 ]]]', r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)

	#
	# geo-query
	#

	def test_geoQueryGmtyOnlyFail(self) -> None:
		"""	RETRIEVE <AE> with rcn=4, gmty only -> Fail"""

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1', self.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_geoQueryGeomOnlyFail(self) -> None:
		"""	RETRIEVE <AE> with rcn=4, geom only -> Fail"""

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&geom=[1.0,2.0]', self.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_geoQueryGsfOnlyFail(self) -> None:
		"""	RETRIEVE <AE> with rcn=4, gsf only -> Fail"""

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gsf=1', self.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)


	def test_geoQueryGeomWrongFail(self) -> None:
		"""	RETRIEVE <AE> with rcn=4, geometry wrong format -> Fail"""

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=1&geom=1.0', self.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

	# Point

	def test_geoQueryPointWithinPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point is within polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=1&geom=[0.5,0.5]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointOutsidePolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point outside polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=1&geom=[2.0,2.0]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointWithinPoint(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point is within point"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[ 1.0, 1.0 ]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=1&geom=[1.0,1.0]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointContainsPoint(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point contains point"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[ 1.0, 1.0 ]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=2&geom=[1.0,1.0]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointContainsPolygonFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point contains polygon -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=2&geom=[0.5,0.5]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsPoint(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects point"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[ 1.0, 1.0 ]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=3&geom=[1.0,1.0]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsPointFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects point -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[ 1.0, 1.0 ]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=3&geom=[2.0,2.0]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=3&geom=[0.0,0.5]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsPolygonFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects polygon -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=2&geom=[0.5,0.5]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)



	# LineString

	def test_geoQueryLineStringWithinPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry line strinng is within polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=2&gsf=1&geom=[[0.5,0.5],[0.6,0.6]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryLineStringOutsidePolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry line string outside polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=2&gsf=1&geom=[[2.0,2.0],[3.0,3.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointWithinLineString1(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point is within LineString start point"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 2,
					  'crd': '[[ 1.0, 1.0 ], [ 2.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=1&geom=[1.0,1.0]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointWithinLineString2(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point is within LineString middle"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 2,
					  'crd': '[[ 1.0, 1.0 ], [ 2.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=1&geom=[1.5,1.5]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryLineStringContainsLineString(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry line string contains line string"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 2,
					  'crd': '[[ 1.0, 1.0 ], [ 2.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=2&gsf=2&geom=[[1.0,1.0],[2.0,2.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryLineStringContainsPolygonFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point contains polygon -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=2&gsf=2&geom=[[0.5,0.5],[0.6,0.6]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsLineString(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects line string"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 2,
					  'crd': '[[ 1.0, 1.0 ], [ 2.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=3&geom=[1.5,1.5]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryLineStringIntersectsLineString(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry line string intersects line string"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 2,
					  'crd': '[[ 1.0, 1.0 ], [ 2.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=2&gsf=3&geom=[[2.0,1.0],[1.0,2.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryLineStringIntersectsLineStringFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry line string intersects line string -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 2,
					  'crd': '[[ 1.0, 1.0 ], [ 2.0, 2.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=2&gsf=3&geom=[[3.0,3.0],[4.0,4.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	# Polygon

	def test_geoQueryPolygonWithinPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry polygon is within polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=3&gsf=1&geom=[[0.5,0.5],[0.6,0.5],[0.6,0.6],[0.5,0.6],[0.5,0.5]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPolygonOutsidePolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry polygon outside polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=3&gsf=1&geom=[[2.0,2.0],[3.0,2.0],[3.0,3.0],[2.0,3.0],[2.0,2.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPolygonPartlyWithinPolygonFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry polygon partly is within polygon -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=3&gsf=1&geom=[[0.5,0.5],[1.5,0.5],[1.5,1.5],[0.5,1.5],[0.5,0.5]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPolygonContainsPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry polygon contains polygon """

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=3&gsf=2&geom=[[0.0,0.0],[2.0,0.0],[2.0,2.0],[0.0,2.0],[0.0,0.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPolygonContainsPolygonFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry polygon contains polygon -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 3.0, 0.0 ], [ 3.0, 3.0 ], [ 0.0, 3.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=3&gsf=2&geom=[[0.0,0.0],[2.0,0.0],[2.0,2.0],[0.0,2.0],[0.0,0.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPolygonIntersectsPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry polygon intersects polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=3&gsf=3&geom=[[0.5,0.5],[2.0,0.5],[2.0,2.0],[0.5,2.0],[0.5,0.5]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPolygonIntersectsPolygonFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry polygon intersects polygon -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=3&gsf=3&geom=[[1.5,1.5],[2.0,1.5],[2.0,2.0],[1.5,2.0],[1.5,1.5]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)



	# MultiPoint

	def test_geoQueryMultiPointWithinPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi point is within polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=4&gsf=1&geom=[[0.5,0.5],[0.6,0.6]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiPointOutsidePolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi point outside polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=4&gsf=1&geom=[[2.0,2.0],[3.0,3.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiPointOutsidePolygonWrongGmtyFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry type invalid for geometry -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		# request with invalid geometry
		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=3&gsf=1&geom=[[2.0,2.0],[3.0,3.0]]', self.originator)
		self.assertEqual(rsc, RC.BAD_REQUEST, r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiPointContainsPoint(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi point contains Point"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[0.5, 0.5]',
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=4&gsf=2&geom=[[0.5,0.5],[0.6,0.6]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiPointContainsPointFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi point contains Point -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[0.5, 0.5]',
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=4&gsf=2&geom=[[0.4,0.4],[0.6,0.6]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsMultiPoint(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects multi point"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 4,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=3&geom=[0.0,0.0]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsMultiPointFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects multi point -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 4,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=3&geom=[2.0,2.0]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiPointIntersectsMultiPoint(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi point intersects multi point"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 4,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=4&gsf=3&geom=[[0.0,0.0],[2.0,2.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiPointIntersectsMultiPointFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi point intersects multi point -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 4,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=4&gsf=3&geom=[[3.0,3.0],[2.0,2.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)



	# MultiLinestring

	def test_geoQueryMultiLinestringWithinPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi line string within polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=5&gsf=1&geom=[[[0.5,0.5],[0.6,0.6]],[[0.7,0.7],[0.8,0.8]]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiLinestringOutsidePolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi line string outside polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=5&gsf=1&geom=[[[1.5,1.5],[1.6,1.6]],[[1.7,1.7],[1.8,1.8]]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiLineContainsPoint(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi line contains Point"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[1.55, 1.55]',
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=5&gsf=2&geom=[[[1.5,1.5],[1.6,1.6]],[[1.7,1.7],[1.8,1.8]]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiLineContainsPointFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi line contains Point -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[0.5, 0.5]',
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=5&gsf=2&geom=[[[1.5,1.5],[1.6,1.6]],[[1.7,1.7],[1.8,1.8]]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsMultiLine(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects multi line"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[[1.0,1.0],[2.0,2.0]],[[3.0,3.0],[4.0,4.0]]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=3&geom=[1.5,1.5]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsMultiLineFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects multi line -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[[1.0,1.0],[2.0,2.0]],[[3.0,3.0],[4.0,4.0]]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=3&geom=[5.0,5.0]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryLineStringIntersectsMultiLine(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry line string intersects multi line"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[[1.0,1.0],[2.0,2.0]],[[3.0,3.0],[4.0,4.0]]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=2&gsf=3&geom=[[2.0,1.0],[1.0,2.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryLineStringIntersectsMultiLineFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry line string intersects multi line -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[[1.0,1.0],[2.0,2.0]],[[3.0,3.0],[4.0,4.0]]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=2&gsf=3&geom=[[5.0,5.0],[6.0,6.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)



	# MultiPolygon

	def test_geoQueryMultiPolygonWithinPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi polygon is within polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=6&gsf=1&geom=[[[0.5,0.5],[0.6,0.5],[0.6,0.6],[0.5,0.6],[0.5,0.5]],[[0.7,0.7],[0.8,0.7],[0.8,0.8],[0.7,0.8],[0.7,0.7]]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiPolygonOutsidePolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi polygon outside polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 3,
					  'crd': '[[ 0.0, 0.0 ], [ 1.0, 0.0 ], [ 1.0, 1.0 ], [ 0.0, 1.0 ], [ 0.0, 0.0 ]]'
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=6&gsf=1&geom=[[[1.5,1.5],[1.6,1.5],[1.6,1.6],[1.5,1.6],[1.5,1.5]],[[1.7,1.7],[1.8,1.7],[1.8,1.8],[1.7,1.8],[1.7,1.7]]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiPolygonContainsPoint(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi polygon contains Point"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[1.55, 1.55]',
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=6&gsf=2&geom=[[[1.5,1.5],[1.6,1.5],[1.6,1.6],[1.5,1.6],[1.5,1.5]],[[1.7,1.7],[1.8,1.7],[1.8,1.8],[1.7,1.8],[1.7,1.7]]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryMultiPolygonContainsPointFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry multi line contains Point -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 1,
					  'crd': '[0.5, 0.5]',
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=6&gsf=2&geom=[[[1.5,1.5],[1.6,1.5],[1.6,1.6],[1.5,1.6],[1.5,1.5]],[[1.7,1.7],[1.8,1.7],[1.8,1.8],[1.7,1.8],[1.7,1.7]]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsMultiPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects multi polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[[1.5,1.5],[1.6,1.5],[1.6,1.6],[1.5,1.6],[1.5,1.5]],[[1.7,1.7],[1.8,1.7],[1.8,1.8],[1.7,1.8],[1.7,1.7]]]',
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=3&geom=[1.55,1.5]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPointIntersectsMultiPolygonFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry point intersects multi polygon -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[[1.5,1.5],[1.6,1.5],[1.6,1.6],[1.5,1.6],[1.5,1.5]],[[1.7,1.7],[1.8,1.7],[1.8,1.8],[1.7,1.8],[1.7,1.7]]]',
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=1&gsf=3&geom=[2.0,2.0]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPolygonIntersectsMultiPolygon(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry polygon intersects multi polygon"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[[1.5,1.5],[1.6,1.5],[1.6,1.6],[1.5,1.6],[1.5,1.5]],[[1.7,1.7],[1.8,1.7],[1.8,1.8],[1.7,1.8],[1.7,1.7]]]',
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=3&gsf=3&geom=[[0.0,0.0],[2.0,0.0],[2.0,2.0],[0.0,2.0],[0.0,0.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNotNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)


	def test_geoQueryPolygonIntersectsMultiPolygonFail(self) -> None:
		"""	CREATE <CNT>, RETRIEVE <AE>, geometry polygon intersects multi polygon -> Fail"""

		dct = { 'm2m:cnt': {
		  		'rn': cntRN,
		  		'loc': {
					  'typ': 5,
					  'crd': '[[[1.5,1.5],[1.6,1.5],[1.6,1.6],[1.5,1.6],[1.5,1.5]],[[1.7,1.7],[1.8,1.7],[1.8,1.8],[1.7,1.8],[1.7,1.7]]]',
				 },
		}}
		r, rsc = CREATE(aeURL, self.originator, T.CNT, dct)
		self.assertEqual(rsc, RC.CREATED, r)

		r, rsc = RETRIEVE(f'{aeURL}?rcn=4&gmty=3&gsf=3&geom=[[2.0,2.0],[4.0,2.0],[4.0,4.0],[2.0,4.0],[2.0,2.0]]', self.originator)
		self.assertEqual(rsc, RC.OK, r)
		self.assertIsNone(findXPath(r, 'm2m:ae/m2m:cnt'), r)

		r, rsc = DELETE(cntURL, self.originator)
		self.assertEqual(rsc, RC.DELETED, r)

	#########################################################################


def run(testFailFast:bool) -> TestResult:
	suite = unittest.TestSuite()

		# Assign tests
	suite = unittest.TestSuite()
	addTests(suite, TestLocation, [

		# basic tests
		'test_createContainerWrongLocFail',

		# Point
		'test_createContainerLocWrongAttributesFail',
		'test_createContainerLocPointIntCoordinatesFail',
		'test_createContainerLocPointWrongCountFail',
		'test_createContainerLocPoint',

		# LineString
		'test_createContainerLocLineStringWrongCountFail',
		'test_createContainerLocLineString',

		# Polygon
		'test_createContainerLocPolygonWrongCountFail',
		'test_createContainerLocPolygonWrongFirstLastCoordinateFail',
		'test_createContainerLocPolygon',

		# MultiPoint
		'test_createContainerLocMultiPointWrongFail',
		'test_createContainerLocMultiPointWrongCountFail',
		'test_createContainerLocMultiPoint',

		# MultiLineString
		'test_createContainerLocMultiLineStringWrongFail',
		'test_createContainerLocMultiLineString2WrongFail',
		'test_createContainerLocMultiLineString',

		# MultiPolygon
		'test_createContainerLocMultiPolygonWrongFail',
		'test_createContainerLocMultiPolygonWrongFirstLastCoordinateFail',
		'test_createContainerLocMultiPolygon',

		# geo-query
		'test_geoQueryGmtyOnlyFail',
		'test_geoQueryGeomOnlyFail',
		'test_geoQueryGsfOnlyFail',
		'test_geoQueryGeomWrongFail',

		'test_geoQueryPointWithinPolygon',
		'test_geoQueryPointOutsidePolygon',
		'test_geoQueryPointWithinPoint',
		'test_geoQueryPointContainsPoint',
		'test_geoQueryPointContainsPolygonFail',
		'test_geoQueryPointIntersectsPoint',
		'test_geoQueryPointIntersectsPointFail',
		'test_geoQueryPointIntersectsPolygon',
		'test_geoQueryPointIntersectsPolygonFail',
	
		'test_geoQueryLineStringWithinPolygon',
		'test_geoQueryLineStringOutsidePolygon',
		'test_geoQueryPointWithinLineString1',
		'test_geoQueryPointWithinLineString2',
		'test_geoQueryLineStringContainsLineString',
		'test_geoQueryLineStringContainsPolygonFail',
		'test_geoQueryLineStringIntersectsLineString',
		'test_geoQueryLineStringIntersectsLineStringFail',
	
		'test_geoQueryPolygonWithinPolygon',
		'test_geoQueryPolygonOutsidePolygon',
		'test_geoQueryPolygonPartlyWithinPolygonFail',
		'test_geoQueryPointContainsPolygonFail',
		'test_geoQueryPolygonContainsPolygon',
		'test_geoQueryPolygonContainsPolygonFail',
		'test_geoQueryPolygonIntersectsPolygon',
		'test_geoQueryPolygonIntersectsPolygonFail',

		'test_geoQueryMultiPointWithinPolygon',
		'test_geoQueryMultiPointOutsidePolygon',
		'test_geoQueryMultiPointOutsidePolygonWrongGmtyFail',
		'test_geoQueryMultiPointContainsPoint',
		'test_geoQueryMultiPointContainsPointFail',
		'test_geoQueryPointIntersectsMultiPoint',
		'test_geoQueryPointIntersectsMultiPointFail',
		'test_geoQueryMultiPointIntersectsMultiPoint',
		'test_geoQueryMultiPointIntersectsMultiPointFail',
	
		'test_geoQueryMultiLinestringWithinPolygon',
		'test_geoQueryMultiLinestringOutsidePolygon',
		'test_geoQueryMultiLineContainsPoint',
		'test_geoQueryMultiLineContainsPointFail',
		'test_geoQueryPointIntersectsMultiLine',
		'test_geoQueryPointIntersectsMultiLineFail',
		'test_geoQueryLineStringIntersectsMultiLine',
		'test_geoQueryLineStringIntersectsMultiLineFail',

		'test_geoQueryMultiPolygonWithinPolygon',
		'test_geoQueryMultiPolygonOutsidePolygon',
		'test_geoQueryMultiPolygonContainsPoint',
		'test_geoQueryMultiPolygonContainsPointFail',
		'test_geoQueryPointIntersectsMultiPolygon',
		'test_geoQueryPointIntersectsMultiPolygonFail',
		'test_geoQueryPolygonIntersectsMultiPolygon',
		'test_geoQueryPolygonIntersectsMultiPolygonFail',

	])

	# Run tests
	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)