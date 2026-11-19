#
#	App.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Application orchestrator for the DAS server
#
"""	Application orchestrator for the DAS server. """

from __future__ import annotations
from typing import cast

import asyncio, logging, signal
import aiohttp
from aiohttp import web
from .AE import DASAE, RegistrationResult
from .Configuration import Configuration
from .Rules import Rules
from . import handlers

log = logging.getLogger(__name__)


class App:
	"""	Owns the HTTP client session and web server, registers/deregisters
		the AEs with all configured CSEs, and runs until asked to shut down.
	"""

	def __init__(self, config: Configuration, ignoreRegistrationError: bool = False, noDeregister: bool = False) -> None:
		self.config = config
		self.ignoreRegistrationError = ignoreRegistrationError
		self.noDeregister = noDeregister
		self.aes: dict[str, DASAE] = {}
		self.session: aiohttp.ClientSession = None
		self.runner: web.AppRunner = None
		self.rules: Rules = None
		self._rulesReloadTask: asyncio.Task = None
		self._registrationRetryTasks: list[asyncio.Task] = []
		self._pendingRegistrations: list[str] = []
		"""	CSEs that could not be reached during startup and whose registration is retried in the background. """
		self.shutdownEvent = asyncio.Event()


	async def run(self) -> None:
		"""	Register the AEs, start the HTTP server, and wait for shutdown. """

		self.session = aiohttp.ClientSession()
		self.rules = Rules(cast(str, self.config.rules.get('path', 'rules')))

		try:
			if not await self._registerAll() and not self.ignoreRegistrationError:
				log.error('Aborting startup due to AE registration errors')
				return

			await self._startServer()
			self._installSignalHandlers()
			self._startRulesReloading()
			self._startRegistrationRetries()

			log.info('DAS server running. Press Ctrl+C to stop.')
			await self.shutdownEvent.wait()

		finally:
			await self._shutdown()


	async def _registerAll(self) -> bool:
		"""	Register the AE with all configured CSEs concurrently.

			CSEs that cannot be reached (e.g. because they are not running yet) are not
			treated as an error; their registration is retried in the background later.

			Return:
				False if any CSE rejected the registration, True otherwise.
		"""

		self.aes = { cse: DASAE(cseConfig, self.session) for cse, cseConfig in self.config.cses.items() }
		results = await asyncio.gather(*(ae.register() for ae in self.aes.values()))

		allOk = True
		self._pendingRegistrations = []
		for cse, result in zip(self.aes, results):
			match result:
				case RegistrationResult.OK:
					log.info(f'DAS AE registered successfully with CSE "{cse}"')
				case RegistrationResult.UNREACHABLE:
					log.warning(f'CSE "{cse}" is not reachable, will retry the registration in the background')
					self._pendingRegistrations.append(cse)
				case _:
					log.error(f'DAS AE registration failed with CSE "{cse}"')
					allOk = False

		return allOk


	def _startRegistrationRetries(self) -> None:
		"""	Start a background task for each CSE that could not be reached during startup.
			Each task periodically retries the registration until it succeeds or the CSE
			rejects it.
		"""

		async def _retryLoop(cse: str, ae: DASAE, interval: int) -> None:
			while True:
				await asyncio.sleep(interval)
				match await ae.register():
					case RegistrationResult.OK:
						log.info(f'DAS AE registered successfully with CSE "{cse}"')
						return
					case RegistrationResult.FAILED:
						log.error(f'DAS AE registration failed with CSE "{cse}", giving up')
						return
					case RegistrationResult.UNREACHABLE:
						log.debug(f'CSE "{cse}" still not reachable, retrying in {interval} second(s)')

		for cse in self._pendingRegistrations:
			interval = max(1, int(self.config.cses[cse].get('registrationRetryInterval', 10)))
			log.info(f'Retrying registration with CSE "{cse}" every {interval} second(s)')
			self._registrationRetryTasks.append(asyncio.create_task(_retryLoop(cse, self.aes[cse], interval)))


	async def _startServer(self) -> None:
		"""	Start the aiohttp web server that receives DAS and notification requests. """

		# create a web application and install the request handlers
		# Store the configuration in the app so that it can be accessed by the request handlers
		app = web.Application()
		app['config'] = self.config
		app['rules'] = self.rules

		authorizeEndpoint = cast(str, self.config.notifications.get('endpoint', '/authorize'))
		handlers.installRoutes(app, authorizeEndpoint)

		self.runner = web.AppRunner(app)
		await self.runner.setup()
		interface = cast(str, self.config.notifications.get('interface', '0.0.0.0'))
		port = cast(int, self.config.notifications.get('port', 9999))
		await web.TCPSite(self.runner, interface, port).start()
		log.info(f'Listening for DAS/notification requests on {interface}:{port}')


	def _installSignalHandlers(self) -> None:
		"""	Trigger a graceful shutdown on SIGINT/SIGTERM. """

		loop = asyncio.get_running_loop()
		for sig in (signal.SIGINT, signal.SIGTERM):
			loop.add_signal_handler(sig, self.shutdownEvent.set)


	def _startRulesReloading(self) -> None:
		"""	Start a background task that periodically reloads the access control
			rule files if they changed. Does nothing if reloading is disabled
			(a reloadInterval of 0 or less).
		"""

		interval = cast(int, self.config.rules.get('reloadInterval', 10))
		if interval <= 0:
			log.info('Rule file reloading is disabled')
			return

		async def _reloadLoop() -> None:
			while True:
				await asyncio.sleep(interval)
				try:
					self.rules.reloadIfChanged()
				except Exception as e:
					log.error(f'Error reloading rule files: {e}')

		self._rulesReloadTask = asyncio.create_task(_reloadLoop())
		log.info(f'Reloading rule files every {interval} second(s)')


	async def _shutdown(self) -> None:
		"""	Deregister all AEs and tear down the HTTP server and client session. """

		if self._rulesReloadTask:
			self._rulesReloadTask.cancel()
		for task in self._registrationRetryTasks:
			task.cancel()

		if not self.noDeregister and self.aes:
			results = await asyncio.gather(*[ae.deregister() for ae in self.aes.values()], return_exceptions=True)
			for cse, result in zip(self.aes, results):
				if result is True:
					log.info(f'DAS AE deregistered successfully from CSE "{cse}"')
				else:
					log.error(f'DAS AE deregistration failed from CSE "{cse}"' + (f': {result}' if isinstance(result, Exception) else ''))

		if self.runner:
			await self.runner.cleanup()
		if self.session:
			await self.session.close()
