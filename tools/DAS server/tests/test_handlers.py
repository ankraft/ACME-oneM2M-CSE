#
#	test_handlers.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Unit tests for dass.handlers.authorize() - run from the "DAS server" directory:
#		python3 -m unittest discover -s tests
#

import unittest, tempfile
from pathlib import Path
from types import SimpleNamespace

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from dass import handlers
from dass.Rules import Rules


_CSE_ORIGINATOR = '/id-in'
_AE_ORIGINATOR = 'CDASServer'

_COMMON_HEADERS = {
	'X-M2M-RI': 'req123',
	'X-M2M-RVI': '5',
	'Content-Type': 'application/json',
}


class TestAuthorize(AioHTTPTestCase):
	""" End-to-end tests for the authorize() handler, via a real aiohttp test server. """

	async def get_application(self) -> web.Application:
		self._tmpDir = tempfile.TemporaryDirectory()
		# An empty rules directory is enough here - these tests are about response
		# status/RSC correctness, not rule-matching content (covered in test_rules.py).
		rules = Rules(str(Path(self._tmpDir.name)))

		app = web.Application()
		app['config'] = SimpleNamespace(cses={ _CSE_ORIGINATOR: { 'aeOriginator': _AE_ORIGINATOR } })
		app['rules'] = rules
		handlers.installRoutes(app, '/authorize')
		return app


	async def tearDownAsync(self) -> None:
		self._tmpDir.cleanup()
		await super().tearDownAsync()


	def _dreqBody(self, **overrides) -> dict:
		dreq = { 'org': 'Ctest', 'trid': 'id-in/cnt-1', 'trt': 3, 'op': 2 }
		dreq.update(overrides)
		return { 'm2m:seci': { 'sit': 1, 'dreq': dreq } }


	@unittest_run_loop
	async def test_unknownCseOriginator(self) -> None:
		headers = { **_COMMON_HEADERS, 'X-M2M-Origin': '/unknown-cse' }
		resp = await self.client.post('/authorize', headers=headers, json=self._dreqBody())
		self.assertEqual(resp.status, 400)
		self.assertEqual(resp.headers['X-M2M-RSC'], '4103')


	@unittest_run_loop
	async def test_wrongContentType(self) -> None:
		headers = { **_COMMON_HEADERS, 'X-M2M-Origin': _CSE_ORIGINATOR, 'Content-Type': 'text/plain' }
		resp = await self.client.post('/authorize', headers=headers, data=b'not json')
		self.assertEqual(resp.status, 400)
		self.assertEqual(resp.headers['X-M2M-RSC'], '4000')


	@unittest_run_loop
	async def test_malformedJsonBody(self) -> None:
		headers = { **_COMMON_HEADERS, 'X-M2M-Origin': _CSE_ORIGINATOR }
		resp = await self.client.post('/authorize', headers=headers, data=b'{not valid json')
		self.assertEqual(resp.status, 400)
		self.assertEqual(resp.headers['X-M2M-RSC'], '4000')


	@unittest_run_loop
	async def test_missingSeci(self) -> None:
		headers = { **_COMMON_HEADERS, 'X-M2M-Origin': _CSE_ORIGINATOR }
		resp = await self.client.post('/authorize', headers=headers, json={ 'not': 'seci' })
		self.assertEqual(resp.status, 400)
		self.assertEqual(resp.headers['X-M2M-RSC'], '4000')


	@unittest_run_loop
	async def test_unsupportedSit(self) -> None:
		headers = { **_COMMON_HEADERS, 'X-M2M-Origin': _CSE_ORIGINATOR }
		resp = await self.client.post('/authorize', headers=headers, json={ 'm2m:seci': { 'sit': 99 } })
		self.assertEqual(resp.status, 400)
		self.assertEqual(resp.headers['X-M2M-RSC'], '4000')


	@unittest_run_loop
	async def test_success(self) -> None:
		headers = { **_COMMON_HEADERS, 'X-M2M-Origin': _CSE_ORIGINATOR }
		resp = await self.client.post('/authorize', headers=headers, json=self._dreqBody())
		self.assertEqual(resp.status, 200)
		self.assertEqual(resp.headers['X-M2M-RSC'], '2000')
		self.assertEqual(resp.headers['X-M2M-Origin'], _AE_ORIGINATOR)
		body = await resp.json()
		self.assertEqual(body['m2m:seci']['sit'], 2)


if __name__ == '__main__':
	unittest.main()
