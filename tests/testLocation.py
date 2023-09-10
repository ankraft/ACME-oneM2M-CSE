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
from typing import Tuple
from acme.etc.Types import ResourceTypes as T, ResponseStatusCode as RC, TimeWindowType
from acme.etc.Types import NotificationEventType, NotificationEventType as NET
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







	#########################################################################


def run(testFailFast:bool) -> Tuple[int, int, int, float]:
	suite = unittest.TestSuite()

	# basic tests
	suite.addTest(TestLocation('test_createContainerWrongLocFail'))

	# Point
	suite.addTest(TestLocation('test_createContainerLocWrongAttributesFail'))
	suite.addTest(TestLocation('test_createContainerLocPointIntCoordinatesFail'))
	suite.addTest(TestLocation('test_createContainerLocPointWrongCountFail'))
	suite.addTest(TestLocation('test_createContainerLocPoint'))

	# LineString
	suite.addTest(TestLocation('test_createContainerLocLineStringWrongCountFail'))
	suite.addTest(TestLocation('test_createContainerLocLineString'))

	# Polygon
	suite.addTest(TestLocation('test_createContainerLocPolygonWrongCountFail'))
	suite.addTest(TestLocation('test_createContainerLocPolygonWrongFirstLastCoordinateFail'))
	suite.addTest(TestLocation('test_createContainerLocPolygon'))

	# MultiPoint
	suite.addTest(TestLocation('test_createContainerLocMultiPointWrongFail'))
	suite.addTest(TestLocation('test_createContainerLocMultiPointWrongCountFail'))
	suite.addTest(TestLocation('test_createContainerLocMultiPoint'))

	# MultiLineString
	suite.addTest(TestLocation('test_createContainerLocMultiLineStringWrongFail'))
	suite.addTest(TestLocation('test_createContainerLocMultiLineString2WrongFail'))
	suite.addTest(TestLocation('test_createContainerLocMultiLineString'))

	# MultiPolygon
	suite.addTest(TestLocation('test_createContainerLocMultiPolygonWrongFail'))
	suite.addTest(TestLocation('test_createContainerLocMultiPolygonWrongFirstLastCoordinateFail'))
	suite.addTest(TestLocation('test_createContainerLocMultiPolygon'))

	result = unittest.TextTestRunner(verbosity = testVerbosity, failfast = testFailFast).run(suite)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped), getSleepTimeCount()


if __name__ == '__main__':
	r, errors, s, t = run(True)
	sys.exit(errors)