#
#	DateUtils.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that deal with dates and times
#


from __future__ import annotations
from typing import Callable, Union
import datetime, time
import isodate


##############################################################################
#
#	Time, Date, Timestamp related
#

def getResourceDate(offset:int=0) -> str:
	"""	Generate an UTC-relative ISO 8601 timestamp and return it.

		`offset` adds or substracts n seconds to the generated timestamp.
	"""
	# return toISO8601Date(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=delta))
	return toISO8601Date(utcTime() + offset)


def toISO8601Date(ts:Union[float, datetime.datetime], isUTCtimestamp:bool=True) -> str:
	"""	Convert and return a UTC-relative float timestamp or datetime object to an ISO 8601 string.
	"""
	if isinstance(ts, float):
		if isUTCtimestamp:
			ts = datetime.datetime.fromtimestamp(ts)
		else:
			ts = datetime.datetime.utcfromtimestamp(ts)
	return ts.strftime('%Y%m%dT%H%M%S,%f')


def fromAbsRelTimestamp(absRelTimestamp:str, default:float=0.0, withMicroseconds:bool=True) -> float:
	"""	Parse a ISO 8601 string and return a UTC-relative timestamp as a float.
		If  `absRelTimestamp` in the string is a period (relatice) timestamp (e.g. PT2S), then this function
		tries to convert it and return an absolute timestamp as a float, based on the current UTC time.
		If the `absRelTimestamp` contains an integer then it is treated as a relative offset and a UTC-based
		timestamp is generated for this offset and returned.
	"""
	try:
		if not withMicroseconds:
			return isodate.parse_datetime(absRelTimestamp).replace(microsecond=0).timestamp()
		return isodate.parse_datetime(absRelTimestamp).timestamp()
		# return datetime.datetime.strptime(timestamp, '%Y%m%dT%H%M%S,%f').timestamp()
	except Exception as e:
		try:
			return utcTime() + fromDuration(absRelTimestamp)
		except:
			return default


def fromDuration(duration:str) -> float:
	"""	Convert a duration to a number of seconds (float). Input could be either an ISO period 
		or a number of ms.
	"""
	try:
		return isodate.parse_duration(duration).total_seconds()
	except Exception as e:
		try:
			# Last try: absRelTimestamp could be a relative offset in ms. Try to convert 
			# the string and return an absolute UTC-based duration
			return float(duration) / 1000.0
		except Exception as e:
			#if L.isWarn: L.logWarn(f'Wrong format for duration: {duration}')
			raise e
	return 0.0


def utcTime() -> float:
	"""	Return the current time's timestamp, but relative to UTC.
	"""
	return datetime.datetime.utcnow().timestamp()


def timeUntilTimestamp(ts:float) -> float:
	"""	Return the time in seconds until the UTC-based `ts` timestamp is reached.
	
		Negative values mean that the timestamp lies is the past.
	"""
	return ts - utcTime()


def timeUntilAbsRelTimestamp(absRelTimestamp:str) -> float:
	"""	Return the time in seconds until the UTC-based `absRelTimestamp` is reached.

		Negative values mean that the timestamp lies is the past.
		
		0.0 is returned in case of an error.
	"""
	if (ts := fromAbsRelTimestamp(absRelTimestamp)) == 0.0:
		return 0.0
	return timeUntilTimestamp(ts)


def waitFor(timeout:float, condition:Callable[[], bool]=None) -> bool:
	"""	Busy waiting for `timeout` seconds, or until the `condition`
		callback function returns *True*.

		The functionn returns *True* if the `condition` returns *True* 
		before the timeout is reached, and *False* otherwise.

		If `condition` is None, then only the `timeout` is used, and *False*
		is always returned.

		If `timeout` is negative then *False* is returned.
	"""
	if timeout < 0.0:
		return False
	if not condition:
		time.sleep(timeout)
		return False
	else:
		toTs = time.time() + timeout
		while not (res := condition()) and toTs > time.time():
			time.sleep(0.01)
		return res