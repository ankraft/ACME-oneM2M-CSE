#
#	PushoverClient.py
#
#	(c) 2026 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Minimal helper for sending notifications via the Pushover API.

	Documentation:
		https://pushover.net/api

	Example:

		::

			from PushoverClient import PushoverClient, sendNotification

			sendNotification(
				token="YOUR_APP_TOKEN",
				user="YOUR_USER_KEY",
				message="a message",
				title="a title",
			)

			# Reusable client (avoids passing token/user each time)
			client = PushoverClient(token='YOUR_APP_TOKEN', user='YOUR_USER_KEY')
			client.sendNotification('Disk usage above 90%', title='Alert', priority=1, sound='siren')
"""

from __future__ import annotations

from typing import Optional
from dataclasses import dataclass
import requests

PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"
""" URL for the Pushover API endpoint to send messages. """


class PushoverError(Exception):
	"""Raised when the Pushover API rejects a request or returns an error."""


@dataclass
class PushoverClient:
	token: str          
	"""Application/API token"""
	user: str
	"""User or group key"""
	device: Optional[str] = None
	"""Restrict to a single device name, if set"""
	timeout: float = 10.0
	""" Timeout for HTTP requests in seconds (default 10.0)"""

	def sendNotification(self, message: str,
							   title: Optional[str] = None,
							   priority: int = 0,
							   sound: Optional[str] = None,
							   url: Optional[str] = None,
							   urlTitle: Optional[str] = None,
							   html: bool = False,
							   retry: Optional[int] = None,
							   expire: Optional[int] = None
		) -> dict:
		"""	Send a single notification. Returns the parsed JSON response.

			Args:
				message: The message to send (max 1024 characters).
				title: Optional title for the message (max 250 characters).
				priority: Message priority (-2 to 2). Default is 0 (normal).
				sound: Optional sound name. Default is "pushover".
				url: Optional supplementary URL to show with the message.
				urlTitle: Optional title for the supplementary URL.
				html: Whether to interpret the message as HTML (default: False).
				retry: Required if priority=2 (emergency). The retry interval in seconds (minimum 30).
				expire: Required if priority=2 (emergency). The total time in seconds Pushover will keep retrying (maximum 10800).

			Return:
				Parsed JSON response from the Pushover API.

			Raises:
				PushoverError - If the API returns an error or a non-200 status code
		"""

		# Build the payload for the Pushover API request
		payload = {
			'token': self.token,
			'user': self.user,
			'message': message,
		}
		if self.device:
			payload['device'] = self.device
		if title:
			payload['title'] = title
		if priority:
			payload['priority'] = priority
		if sound:
			payload['sound'] = sound
		if url:
			payload['url'] = url
		if urlTitle:
			payload['url_title'] = urlTitle
		if html:
			payload['html'] = 1
		if priority == 2:
			if retry is None or expire is None:
				raise ValueError('priority=2 (emergency) requires retry and expire')
			payload['retry'] = retry
			payload['expire'] = expire

		# Send the POST request to the Pushover API
		response = requests.post(PUSHOVER_API_URL, data=payload, timeout=self.timeout)
		try:
			result = response.json()
		except ValueError:
			raise PushoverError(f'Non-JSON response ({response.status_code}): {response.text}')

		if response.status_code != 200 or result.get('status') != 1:
			errors = result.get('errors')
			raise PushoverError(f'Pushover API error (status {response.status_code}): {errors or result}')

		return result


def sendNotification(token: str, user: str, message: str, **kwargs) -> dict:
	"""	Convenience one-off call - builds a client and sends immediately.

		Args:
			token: Application/API token.
			user: User or group key.
			message: The message to send (max 1024 characters).
			**kwargs: Additional keyword arguments for PushoverClient.sendNotification().

		Return:
			Parsed JSON response from the Pushover API.

		Raises:
			PushoverError: If the API returns an error or a non-200 status code
	"""
	return PushoverClient(token=token, user=user).sendNotification(message, **kwargs)
