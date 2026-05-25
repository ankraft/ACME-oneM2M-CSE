#
#	DateUtils.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	This module contains various utilty functions that deal with dates and times.
"""

from __future__ import annotations
from typing import Callable, Union, Tuple, Optional

import time
from email.utils import formatdate
from datetime import datetime, timedelta, timezone
import isodate

##############################################################################
#
#	Time, Date, Timestamp related
#

def getResourceDate(offset:Optional[float] = 0.0) -> str:
	"""	Generate an UTC-relative ISO 8601 timestamp and return it.

		Args:
			offset: adds or substracts *offset* seconds to the generated timestamp.
		Return:
			String with UTC-relative ISO 8601 timestamp.
	"""
	# return toISO8601Date(datetime.now(timezone.utc) + timedelta(seconds=delta))
	return toISO8601Date(utcTime() + offset)


def toISO8601Date(ts:Union[float, datetime], readable:Optional[bool] = False) -> str:
	"""	Convert and return a UTC-relative float timestamp or datetime object to an ISO 8601 string.

		Args:
			ts: Timestamp. Either a POSIX float timestamp, of a *datetime* object.
			readable: Optional boolean indicating whether the output should be in the format "YYYY-MM-DDThh:mm:ss,f
		Return:
			ISO 8601 datetime string.
	"""
	if isinstance(ts, float):
		ts = datetime.fromtimestamp(ts, tz = timezone.utc)
	return ts.strftime('%Y-%m-%dT%H:%M:%S,%f' if readable else '%Y%m%dT%H%M%S,%f')


def fromISO8601Date(date:str) -> datetime:
	"""	Convert an ISO 8601 date time string to a *datetime* object.

		Args:
			date: ISO 8601 datetime string.
		Return:
			Datetime object.
	"""
	return isodate.parse_datetime(date)


def fromAbsRelTimestamp(absRelTimestamp:str, 
						default:Optional[float] = 0.0, 
						withMicroseconds:Optional[bool] = True) -> float:
	"""	Parse a ISO 8601 string and return a UTC-based POSIX timestamp as a float.

		If the *absRelTimestamp* is a period (relative) timestamp (e.g. "PT2S"), then this function
		tries to convert it and return an absolute POSIX timestamp as a float, based on the current UTC time.

		If the *absRelTimestamp* contains a stringified integer then it is treated as a relative offset in ms and
		a UTC-based POSIX timestamp is generated for this offset and returned.

		Args:
			absRelTimestamp: A string with either a stringified integer that represents a POSIX UTC-based timestamp,
				or a ISO 8601 period timestamp.
			default: The default that is returned in case a conversion fails.
			withMicroseconds: The function handles the timestamps including micro seconds.
		Return:
			A float representing a UTC-based POSIX timestamp.
	"""
	try:
		if not withMicroseconds:
			return isodate.parse_datetime(absRelTimestamp).replace(microsecond = 0, tzinfo = timezone.utc).timestamp()
		return isodate.parse_datetime(absRelTimestamp).replace(tzinfo = timezone.utc).timestamp()
		# return datetime.datetime.strptime(timestamp, '%Y%m%dT%H%M%S,%f').timestamp()
	except Exception as e:
		try:
			return utcTime() + fromDuration(absRelTimestamp)
		except:
			return default


def fromDuration(duration:str, allowMS:bool = True) -> float:
	"""	Convert a duration to a number of seconds (float). 

		Args:
			duration: String with either an ISO 8601 period or a string with a number of ms.
			allowMS: If True, the function tries to convert the string as if it contains a number of ms.
		Return:
			Float, number of seconds.
		Raise:
			Exception if wrong format is provided in *duration*.
	"""
	try:
		return isodate.parse_duration(duration).total_seconds()
	except Exception as e:
		try:
			# Last try: absRelTimestamp could be a relative offset in ms. Try to convert 
			# the string and return an absolute UTC-based duration
			if allowMS:
				return float(duration) / 1000.0
			raise
		except Exception as e:
			#if L.isWarn: L.logWarn(f'Wrong format for duration: {duration}')
			raise


def toDuration(ts:float) -> str:
	"""	Convert a POSIX timestamp to ISO 8601 duration format.

		Args:
			ts: Float with a UTC-based POSIX time stamp.
		Return:
			A string with an ISO 8601 duration.
	"""
	d = isodate.Duration()
	d.tdelta = timedelta(seconds = ts)
	return isodate.duration_isoformat(d)


def rfc1123Date(timeval:Optional[float] = None) -> str:
	"""	Return a date time string in RFC 1123 format, e.g. for use in HTTP requests.

		The timestamp is UTC-based.

		Args:
			timeval: Optional UTC-based POSIX timestamp to use, otherwise the current time is used.
		Return:
			String with the UTC-based time.
	"""
	return formatdate(timeval = timeval, localtime = False, usegmt = True)


def utcDatetime() -> datetime:
	"""	Return the current datetime, but relative to UTC.

		Returns:
			Datetime with current UTC-based time.
	"""
	return datetime.now(tz = timezone.utc)


def utcTime() -> float:
	"""	Return the current time's timestamp, but relative to UTC.

		Returns:
			Float with current UTC-based POSIX time.
	"""
	return utcDatetime().timestamp()


def timeUntilTimestamp(ts:float) -> float:
	"""	Return the time in seconds until the UTC-based POSIX timestamp is reached.

		Args:
			ts: UTC-based POSIX timestamp.

		Return:
			Number of seconds until the timestamp. A negative value means that the timestamp lies is the past.
	"""
	return ts - utcTime()


def timeUntilAbsRelTimestamp(absRelTimestamp:str) -> float:
	"""	Return the time in seconds until the UTC-based POSIX *absRelTimestamp* is reached.

		Args:
			absRelTimestamp: String with either an ISO 8601 period or a string with an 
				integer (UTC-based POSIX timestamp in seconds).
		
		Return:
			Time in seconds until the timestamp is reached. Negative values mean that the timestamp lies is the past.
			0.0 is returned in case of an error.
	"""
	if (ts := fromAbsRelTimestamp(absRelTimestamp)) == 0.0:
		return 0.0
	return timeUntilTimestamp(ts)


def isodateDelta(isoDateTime:str, now:Optional[float] = None) -> Optional[float]:
	"""	Calculate the delta between and ISO 8601 date time string and a UTC-based POSIX timestamp.
		
		Args:
			isoDateTime: ISO 8601 compatible string.
			now: Optional float with a time stamp. If *None* is given then the current time (UTC-based) will be taken.

		Return:
			A signed float value indicating the delta (negative when the given ISO date time 
			is earlier then "now"), or *None* in case of an error.
	"""
	if now is None:
		now = utcTime()
	try:
		return now - isodate.parse_datetime(isoDateTime).replace(tzinfo = timezone.utc).timestamp()
	except Exception as e:
		return None


def waitFor(timeout:float, 
			condition:Optional[Callable[[], bool]] = None,
			latency:Optional[float] = 0.01) -> bool:
	"""	Busy waiting for *timeout* seconds, or until a *condition* callback function returns *True*.

		Args:
			timeout: The time to wait at most for the event to be true. 
			condition: A callback. It it returns *True* the wait-for condition is met and the waiting stops. 
				If it is None, then only the *timeout* is used, and *False* is always returned.
			latency: The time between *condition* checks.

		Return:
			The functionn returns *True* if the *condition* returns *True* 	
			before the timeout is reached, and *False* otherwise.
			It returns *False* if *timeout* is negative.
			If *condition* is not callable then *False* is returned.
	"""
	if timeout < 0.0:
		return False
	if not condition:
		try:
			time.sleep(timeout)
		except KeyboardInterrupt:
			pass
		return False
	else:
		if not callable(condition):
			return False
		toTs = time.time() + timeout
		while not (res := condition()) and toTs > time.time():
			try:
				time.sleep(latency)
			except KeyboardInterrupt:
				return False
		return res

##############################################################################
#
#	Cron
#

def cronMatchesTimestamp(cronPattern:Union[str, list[str]], 
						 ts:Optional[datetime] = None) -> bool:
	r"""A cron parser to determine if the *cronPattern* matches for a given timestamp *ts*.

		The cronPattern must follow the usual crontab pattern of 7 fields:
	
			second minute hour dayOfMonth month dayOfWeek year

		which each must comply to the following patterns:

		- \* : any integer value
		- \*/num : step values
		- num[,num]\* : value list separator (either num, range or step)
		- num-num : range of values
	
		see also: https://crontab.guru/crontab.5.html

		Args:
			cronPattern: Either a string with the pattern or a list of strings, one for each pattern element.
			ts: Optional timestamp. If *None* then a current UTC-based timestamp is used to fill the timestamp.
		
		Return:
			Boolean, indicating whether time pattern matches the given timestamp.
		
		Raises:
			ValueError: If *cronPattern* is invalid.
	"""

	def _parseMatchCronArg(element:str, target:int) -> bool:
		"""	Parse and match a single cron element and match it against a target value.

			Args:
				element: A single cron element/pattern.
				target: Target value to match.
			
			Return:
				Indication whether the target value matches against the pattern element.

			Raises:
				ValueError: If *element* is invalid.
		"""

		# Return True if element is only a *, because this matches anything
		if element == '*':
			return True

		# Either a list of values, of a single value 
		for element in element.split(',') if ',' in element else [ element ] :
			try:
				# First, try a direct comparison
				# If this isn't a number then continue after the exception
				if int(element) == target:
					return True
				continue	# It didnt raise an exception, but didn't match either, so continue
			except ValueError:
				pass		# Exception, no number, but maybe a pattern
			
			# Value is something else, not a number, look for - or /
			# If not, then ignore wrong format of value

			if '-' in element:
				step = 1
				if '/' in element:
					# Allow divider in values
					try:
						st, tmp = ( x for x in element.split('-') )	# tmp could be another value
						start = int(st)
						end, step =( int(x) for x in tmp.split('/') )
					except ValueError:
						raise ValueError(f'Invalid cron element: {element}')	# Error in any of the values
				else:
					try:
						start, end = ( int(x) for x in element.split('-') )
					except ValueError:
						raise ValueError(f'Invalid cron element: {element}. Not a number.')	# Not a number

				# If target value is in the range, it matches
				if target in range(start, end + 1, step):
					return True
			
				# Else continue
				continue

			if '/' in element:
				v, interval = ( x for x in element.split('/') )
				if v != '*':	
					raise ValueError(f'Invalid cron element: {element}. Interval only for *.')	# Intervals only, if it is a *
				# If the remainder is zero, this matches
				try:
					if target % int(interval) == 0:
						return True
				except ValueError:
					raise ValueError(f'Invalid cron element: {element}. Not a number.')	# Not a number
				# Else continue
				continue

			raise ValueError(f'Invalid cron element: {element}.')	# Not a number

		return False

	if ts is None:
		ts = utcDatetime()
	
	cronElements = cronPattern.split() if isinstance(cronPattern, str) else cronPattern
	if len(cronElements) != 7:
		raise ValueError(f'Invalid or empty cron pattern: "{cronPattern}". Must have 7 elements.')

	weekday = ts.isoweekday()
	return  _parseMatchCronArg(cronElements[0], ts.second) \
		and _parseMatchCronArg(cronElements[1], ts.minute) \
		and _parseMatchCronArg(cronElements[2], ts.hour) \
		and _parseMatchCronArg(cronElements[3], ts.day) \
		and _parseMatchCronArg(cronElements[4], ts.month) \
		and _parseMatchCronArg(cronElements[5], 0 if weekday == 7 else weekday) \
		and _parseMatchCronArg(cronElements[6], ts.year)


def cronInPeriod(cronPattern:Union[str, 
								   list[str]], 
								   startTs:datetime, 
								   endTs:Optional[datetime] = None) -> Tuple[bool, datetime]:
	''' A parser to check whether a cron pattern has been true during a certain time period. 
	
		This is useful for applications which cannot check every minute or need to catch up during a
		restart, or want to determinethe next run at some time in the future.

		Attention:
			Be aware that this function just tries every minute between *startTs* and *endTs*, 
			so it might take some time to execute.
	
		Args:
			cronPattern: Either a string with the pattern or a list of strings, one for each pattern element.
			startTs: Start UTC-based POSIX timestamp.
			endTs: End UTC-based POSIX timestamp. If *None* then the current UTC time is used to fill the timestamp. 
				In this case *startTs* must be before *endTs*.
		
		Return:
			Tupple[bool, datetime]. The first element indicates whether the *cronPattern* matches
			any time in the given period. The second element provides the matched timestamp.
		
		Raises:
			ValueError: If *cronPattern* is invalid.
	'''

	# Fill in the default
	if endTs is None:
		endTs =  utcDatetime()

	# Check the validity of the range
	if endTs < startTs:
		raise ValueError('timestamp must be before the current datetime.')

	# Check for every minute
	td = timedelta(minutes = 1)
	while startTs <= endTs:
		if cronMatchesTimestamp(cronPattern, startTs):
			return True, startTs
		startTs += td	# Increase by 1 minute for each iteration

	return False, None

