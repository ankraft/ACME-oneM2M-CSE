#
#	AE.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	AE base class for DAS server
#
"""	AE base class for DAS server. """

import asyncio, json, uuid, logging
from enum import Enum
import aiohttp
from .Configuration import Configuration

log = logging.getLogger(__name__)

RSC_CONFLICT = 4105

DEREGISTRATION_TIMEOUT = 10
"""	Timeout (in seconds) for the deregistration request, so that shutdown does not hang on an unreachable CSE. """


class RegistrationResult(Enum):
	"""	Outcome of an AE registration attempt. """

	OK = 'ok'
	"""	The AE is registered with the CSE. """

	FAILED = 'failed'
	"""	The CSE was reached but rejected the registration. """

	UNREACHABLE = 'unreachable'
	"""	The CSE could not be reached (e.g. it is not running). The registration may be retried later. """


class DASAE():
	"""	AE base class for DAS server. """

	def __init__(self, config: dict, session: aiohttp.ClientSession) -> None:
		self.config = config
		self.session = session
		self.originator: str = None
		"""	The AE-ID assigned by the CSE after a successful registration. """


	async def register(self) -> RegistrationResult:
		"""	Register the AE with the CSE.

			Return:
				RegistrationResult.OK if the AE is registered, RegistrationResult.FAILED if the CSE
				rejected the registration, or RegistrationResult.UNREACHABLE if the CSE could not be reached.
		"""

		rvi = self.config.get('releaseVersion', '4')

		# Try to retrieve the AE first to check whether it is already registered
		retrieveUrl = f'{self.config["httpAddress"]}/-/{self.config["aeResourceName"]}'
		retrieveHeaders = {
			'X-M2M-Origin': self.config['aeOriginator'],
			'X-M2M-RI': str(uuid.uuid4()),
			'X-M2M-RVI': rvi,
			'Accept': 'application/json',
		}

		try:
			async with self.session.get(retrieveUrl, headers=retrieveHeaders) as retrieveResponse:
				match retrieveResponse.status:
					case 200:
						j = await retrieveResponse.json()
						self.originator = j.get('m2m:ae', {}).get('aei')
						log.info(f'AE "{self.config["aeResourceName"]}" is already registered with AE-ID "{self.originator}".')
						return RegistrationResult.OK
					case 403:
						log.error(f'AE "{self.config["aeResourceName"]}" seems to be already registered, but originator "{self.config["aeOriginator"]}" is not allowed to access it.')
						return RegistrationResult.FAILED
		except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
			log.warning(f'Cannot connect to CSE at {self.config["httpAddress"]}: {e or type(e).__name__}')
			return RegistrationResult.UNREACHABLE
		except aiohttp.ClientError as e:
			log.warning(f'Error retrieving AE, will attempt to register it: {e}')

		url = f'{self.config["httpAddress"]}/{self.config["cseId"]}'
		body = {
			'm2m:ae': {
				'rn': self.config['aeResourceName'],
				'api': self.config.get('aeAppId', f'N{self.config["aeAppId"]}'),
				'rr': True,
				'srv': [ rvi ],
				'poa': [ self.config['aeHttpPOA']]
			}
		}
		headers = {
			'X-M2M-Origin': self.config['aeOriginator'],
			'X-M2M-RI': str(uuid.uuid4()),
			'X-M2M-RVI': rvi,
			'Content-Type': 'application/json;ty=2',
			'Accept': 'application/json',
		}

		try:
			async with self.session.post(url, headers=headers, data=json.dumps(body)) as response:
				if response.status not in (200, 201):
					rsc = int(response.headers.get('X-M2M-RSC', response.status))
					text = await response.text()
					log.error(f'Failed to register AE: {response.status}/{rsc} {text}')
					return RegistrationResult.FAILED

				j = await response.json()
				self.originator = j.get('m2m:ae', {}).get('aei')
				return RegistrationResult.OK
		except (aiohttp.ClientConnectionError, asyncio.TimeoutError) as e:
			log.warning(f'Cannot connect to CSE at {self.config["httpAddress"]}: {e or type(e).__name__}')
			return RegistrationResult.UNREACHABLE
		except aiohttp.ClientError as e:
			log.error(f'Error registering AE: {e}')
			return RegistrationResult.FAILED


	async def deregister(self) -> bool:
		"""	Deregister the AE from the CSE. """

		if not self.originator:
			log.warning(f'No AE-ID available, skipping deregistration of AE "{self.config["aeResourceName"]}"')
			return True

		url = f'{self.config["httpAddress"]}/-/{self.config["aeResourceName"]}'
		headers = {
			'X-M2M-Origin': self.originator,
			'X-M2M-RI': str(uuid.uuid4()),
			'X-M2M-RVI': self.config.get('releaseVersion', '4'),
			'Accept': 'application/json',
		}

		try:
			async with self.session.delete(url, headers=headers, timeout=aiohttp.ClientTimeout(total=DEREGISTRATION_TIMEOUT)) as response:
				if response.status not in (200, 202, 204):
					text = await response.text()
					log.error(f'Failed to deregister AE: {response.status} {text}')
					return False
		except asyncio.TimeoutError:
			log.error(f'Error deregistering AE: CSE at {self.config["httpAddress"]} did not respond within {DEREGISTRATION_TIMEOUT} seconds')
			return False
		except aiohttp.ClientError as e:
			log.error(f'Error deregistering AE: {e}')
			return False

		self.originator = None
		return True
