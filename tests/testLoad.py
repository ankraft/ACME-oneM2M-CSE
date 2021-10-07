#
#	testLoad.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Load tests
#

from __future__ import annotations
import unittest, sys, time
if '..' not in sys.path:
	sys.path.append('..')
from typing import Tuple
import threading
from acme.etc.Types import ResponseStatusCode as RC, ResourceTypes as T
from init import *


class TestLoad(unittest.TestCase):
	aes:list[Tuple[str, str]] 	= []
	timeStart:float				= 0

	def __init__(self, methodName:str='runTest', count:int=None, parallel:int=1):
		"""	Pass a count to the test cases.
		"""
		super(TestLoad, self).__init__(methodName)
		self.count = count
		self.parallel = parallel


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def setUpClass(cls) -> None:
		pass


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def tearDownClass(cls) -> None:
		for ae in cls.aes:
			DELETE(f'{cseURL}/{ae[1]}', ORIGINATOR)


	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def startTimer(cls) -> None:
		"""	Start a timer.
		"""
		cls.timeStart = time.perf_counter()

	@classmethod
	@unittest.skipIf(noCSE, 'No CSEBase')
	def stopTimer(cls, count:int, parallel:int=1, divider:int=1) -> str:
		"""	Stop a timer and return a meaningful result string.
			The count and parallel arguments must be given bc this is a class method that has no access to these instance attributes.
		"""
		timeEnd = time.perf_counter()
		total = (timeEnd - cls.timeStart)
		return f'{total:.4f} ({total/(count*parallel)/divider:.5f})'


	def _createAEs(self, count:int) -> list[Tuple[str, str]]:
		"""	Create n AEs and return the list of (identifiers, resourceName).
		"""
		aes:list[Tuple[str, str]] = []
		for _ in range(count):
			dct = 	{ 'm2m:ae' : {
						'rn': uniqueRN(),	# Sometimes needs a set rn
						'api': 'NMyApp1Id',
						'rr': False,
						'srv': [ '3' ]
					}}
			r, rsc = CREATE(cseURL, 'C', T.AE, dct)
			self.assertEqual(rsc, RC.created, r)
			ri = findXPath(r, 'm2m:ae/ri')
			rn = findXPath(r, 'm2m:ae/rn')
			aes.append((ri, rn))
		self.assertEqual(len(aes), count)
		return aes

	
	def _retrieveAEs(self, count:int, aes:list[Tuple[str, str]]=None) -> None:
		if aes is None:
			aes = TestLoad.aes
		self.assertEqual(len(aes), count)
		for ae in list(aes):
			r, rsc = RETRIEVE(f'{cseURL}/{ae[1]}', ORIGINATOR)
			self.assertEqual(rsc, RC.OK, r)
			self.assertEqual(findXPath(r, 'm2m:ae/ri'), ae[0], r)


	def _deleteAEs(self, count:int, aes:list[Tuple[str, str]]=None) -> None:
		"""	Delete n AE's. Remove the AE's von the given list (only removed from the global list if no list was given).
		"""
		if aes is None:
			aes = TestLoad.aes
		self.assertEqual(len(aes), count)
		for ae in list(aes):
			r, rsc = DELETE(f'{cseURL}/{ae[1]}', ORIGINATOR)
			self.assertEqual(rsc, RC.deleted, r)
			aes.remove(ae)
		self.assertEqual(len(aes), 0)


	def _createCNTs(self, aern:str, originator:str, count:int, mni:int) -> list[Tuple[str, str]]:
		"""	Create n CNTs and return the list of (identifiers, resourceName).
		"""
		cnts:list[Tuple[str, str]] = []
		for _ in range(count):
			dct = 	{ 'm2m:cnt' : {
					'mni': mni
				}}
			r, rsc = CREATE(f'{cseURL}/{aern}',  originator, T.CNT, dct)
			self.assertEqual(rsc, RC.created, r)
			ri = findXPath(r, 'm2m:cnt/ri')
			rn = findXPath(r, 'm2m:cnt/rn')
			cnts.append((ri, rn))
		self.assertEqual(len(cnts), count)
		return cnts


	def _createCINs(self, aern:str, cntrn:str, originator:str, count:int) -> list[Tuple[str, str]]:
		"""	Create n CINs and return the list of (identifiers, resourceName).
		"""
		cins:list[Tuple[str, str]] = []
		for _ in range(count):
			dct = 	{ 'm2m:cin' : {
					'con': 'Hello, world'
				}}
			r, rsc = CREATE(f'{cseURL}/{aern}/{cntrn}',  originator, T.CIN, dct)
			self.assertEqual(rsc, RC.created, r)
			ri = findXPath(r, 'm2m:cnt/ri')
			rn = findXPath(r, 'm2m:cin/rn')
			cins.append((ri, rn))
		self.assertEqual(len(cins), count)
		return cins


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createAEs(self) -> None:
		"""	Create n AEs """
		TestLoad.startTimer()
		print(f'{self.count} ... ', end='', flush=True)
		TestLoad.aes.extend(self._createAEs(self.count))
		print(f'{TestLoad.stopTimer(self.count)} ... ', end='', flush=True)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_retrieveAEs(self) -> None:
		"""	Retrieve n AEs """
		TestLoad.startTimer()
		print(f'{self.count} ... ', end='', flush=True)
		self._retrieveAEs(self.count)
		print(f'{TestLoad.stopTimer(self.count)} ... ', end='', flush=True)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteAEs(self) -> None:
		"""	Delete n AEs """
		TestLoad.startTimer()
		print(f'{self.count} ... ', end='', flush=True)
		self._deleteAEs(self.count)
		print(f'{TestLoad.stopTimer(self.count)} ... ', end='', flush=True)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipIf(BINDING=='mqtt', 'No parallel execution for MQTT binding yet')
	def test_createAEsParallel(self) -> None:
		"""	Create n AEs in m threads in parallel"""
		print(f'{self.count} * {self.parallel} Threads ... ', end='', flush=True)
		threads = [threading.Thread(target=lambda: TestLoad.aes.extend(self._createAEs(self.count))) for _ in range(self.parallel)]
		TestLoad.startTimer()
		[t.start() for t in threads] 	# type: ignore [func-returns-value]
		[t.join() for t in threads]		# type: ignore [func-returns-value]
		print(f'{TestLoad.stopTimer(self.count, self.parallel)} ... ', end='', flush=True)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipIf(BINDING=='mqtt', 'No parallel execution for MQTT binding yet')
	def test_deleteAEsParallel(self) -> None:
		"""	Delete n AEs in m threads in parallel """
		print(f'{self.count} * {self.parallel} Threads ... ', end='', flush=True)
		nrPerList = int(len(TestLoad.aes)/self.parallel)
		deleteLists = [TestLoad.aes[x:x+nrPerList] for x in range(0, len(TestLoad.aes), nrPerList)]
		threads = [threading.Thread(target=lambda n: self._deleteAEs(self.count, aes=deleteLists[n]), args=(n,)) for n in range(self.parallel)]
		TestLoad.startTimer()
		[t.start() for t in threads]	# type: ignore [func-returns-value]
		[t.join() for t in threads]		# type: ignore [func-returns-value]
		print(f'{TestLoad.stopTimer(self.count, self.parallel)} ... ', end='', flush=True)
		TestLoad.aes.clear()


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_createCNTCINs(self) -> None:
		"""	Create 1 AE + n CNTs * 20 CINs"""
		self.assertEqual(len(TestLoad.aes), 0)
		print(f'{self.count} ... ', end='', flush=True)
		TestLoad.startTimer()

		# create an AE
		TestLoad.aes.extend(self._createAEs(1))
		ae = TestLoad.aes[0]

		# add self.count containers
		cnts = self._createCNTs(ae[1], ae[0], self.count, mni=10)
		self.assertEqual(len(cnts), self.count)

		# add 20 CIN to each container
		for cnt in cnts:
			self._createCINs(ae[1], cnt[1], ae[0], 20)

		print(f'{TestLoad.stopTimer(self.count, 1, divider=20)} ... ', end='', flush=True)


	@unittest.skipIf(noCSE, 'No CSEBase')
	@unittest.skipIf(BINDING=='mqtt', 'No parallel execution for MQTT binding yet')
	def test_createCNTCINsParallel(self) -> None:
		"""	Create 1 AE + n CNTs * 20 CINs in n threads"""
		self.assertEqual(len(TestLoad.aes), 0)
		print(f'{self.count} ... ', end='', flush=True)
		TestLoad.startTimer()

		# create an AE
		TestLoad.aes.extend(self._createAEs(1))
		ae = TestLoad.aes[0]

		# add self.count containers
		cnts = self._createCNTs(ae[1], ae[0], self.count, mni=10)
		self.assertEqual(len(cnts), self.count)

		threads = []			# construct and start the threads in a non-comprehensiv way bc we need the cnt variable to be assigned in the lambda
		for cnt in cnts:
			threads.append(t := threading.Thread(target=lambda: self._createCINs(ae[1], cnt[1], ae[0], 20)))
			t.start()
		[t.join() for t in threads]		# type: ignore [func-returns-value]
		print(f'{TestLoad.stopTimer(self.count, 1, divider=20)} ... ', end='', flush=True)


	@unittest.skipIf(noCSE, 'No CSEBase')
	def test_deleteCNTCINs(self) -> None:
		"""	Delete 1 AE  + n CNTs + 20 CINs"""
		self.assertEqual(len(TestLoad.aes), 1)
		print(f'{self.count} ... ', end='', flush=True)
		TestLoad.startTimer()
		self._deleteAEs(1)
		print(f'{TestLoad.stopTimer(1)} ... ', end='', flush=True)




# TODO: RETRIEVE CNT+CIN+la n times

# TODO Discover AEs
# TODO discover CIN

# TODO CNT + CIN
# TODO CNT + CIN + SUB

def run(testVerbosity:int, testFailFast:bool) -> Tuple[int, int, int]:
	suite = unittest.TestSuite()


	suite.addTest(TestLoad('test_createAEs', 10))
	suite.addTest(TestLoad('test_retrieveAEs', 10))
	suite.addTest(TestLoad('test_deleteAEs', 10))

	suite.addTest(TestLoad('test_createAEs', 100))
	suite.addTest(TestLoad('test_retrieveAEs', 100))
	suite.addTest(TestLoad('test_deleteAEs', 100))

	suite.addTest(TestLoad('test_createAEs', 1000))
	suite.addTest(TestLoad('test_retrieveAEs', 1000))
	suite.addTest(TestLoad('test_deleteAEs', 1000))

	suite.addTest(TestLoad('test_createAEsParallel', 10, 10))
	suite.addTest(TestLoad('test_deleteAEsParallel', 10, 10))
	suite.addTest(TestLoad('test_createAEsParallel', 100, 10))
	suite.addTest(TestLoad('test_deleteAEsParallel', 100, 10))
	suite.addTest(TestLoad('test_createAEsParallel', 10, 100))
	suite.addTest(TestLoad('test_deleteAEsParallel', 10, 100))

	suite.addTest(TestLoad('test_createCNTCINs', 10))
	suite.addTest(TestLoad('test_deleteCNTCINs', 10))
	suite.addTest(TestLoad('test_createCNTCINs', 100))
	suite.addTest(TestLoad('test_deleteCNTCINs', 100))

	suite.addTest(TestLoad('test_createCNTCINsParallel', 10))
	suite.addTest(TestLoad('test_deleteCNTCINs', 10))
	suite.addTest(TestLoad('test_createCNTCINsParallel', 100))
	suite.addTest(TestLoad('test_deleteCNTCINs', 100))
	
	result = unittest.TextTestRunner(verbosity=testVerbosity, failfast=testFailFast).run(suite)
	printResult(result)
	return result.testsRun, len(result.errors + result.failures), len(result.skipped)

if __name__ == '__main__':
	_, errors, _ = run(2, True)
	sys.exit(errors)
