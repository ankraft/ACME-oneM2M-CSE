#
#	Management.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""Management module for accessing and managing CSE internal functions.
"""

from typing import cast, Generator
import json, socket, platform, threading, sys, os, datetime, time

from ..etc.Constants import RuntimeConstants as RC, Constants as C
from ..etc.Types import CSEStatus, JSON, ResourceTypes, LogLevel, CSEType
from ..etc.DateUtils import utcDatetime, fromAbsRelTimestamp, fromISO8601Date
from ..etc.IDUtils import isAbsolute, getSPFromID
from ..helpers.NetworkTools import getIPAddress
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..runtime import CSE
from ..runtime.Configuration import Configuration
from ..runtime.Logging import Logging as L
from ..runtime import Statistics


def getConfig() -> str:
	"""Get the current configuration of the CSE as a JSON string.

		Returns:
			The configuration of the CSE in JSON format.
	"""
	return json.dumps(Configuration.all(), indent=4)


def getLogGenerator() -> Generator[str, None, None]:

	def generate() -> Generator[str, None, None]:
		_rb = L.ringBufferHandler
		index = _rb.head	# get the current index of the ring buffer
		try:
			while True:
				if index != _rb.head:
					index = _rb.nextIndex(index)	# increment the index in a circular manner
					yield _rb.getLogEntryAsString(index) + '\n'
				else:
					time.sleep(0.0001)
		except GeneratorExit:
			# This exception happens after the next yield and the connection to the client is closed
			pass
	return generate()



def getLoglevel() -> str:
	"""Get the current log level of the CSE.

		Returns:
			The current log level of the CSE.
	"""
	return L.logLevel.name


def refreshRegistrations() -> str:
	""" Force the CSE to immediately check the registrations with the remote registrar(s).

		This is useful for testing purposes, e.g. when the CSE is started and the registration is not done automatically.
		
		Returns:
			A message indicating the result of the registration.
	"""
	CSE.remote.checkConnectionsNow()
	return "Registration(s) refresh triggered."


def getRegistrations() -> str:
	"""Get the current registration status of the CSE as a JSON string.

		Returns:
			The registration status of the CSE in JSON format.
	"""
	return json.dumps(getRegistrationStatus(), indent=4)



def getRequests() -> Generator[str, None, None]:
	"""Get the current requests of the CSE as a generator of JSON strings.

		Returns:
			A generator that yields JSON strings of the request."""

	def generate() -> Generator[str, None, None]:
		_rb = CSE.request.requestRingBuffer
		index = _rb.head	# Ensure the ring buffer is initialized
		try:
			while True:
				if index != _rb.head:
					index = _rb.nextIndex(index)	# increment the index in a circular manner
					yield json.dumps(_rb[index], indent=4) + '\n'
				else:
					time.sleep(0.0001)
		except GeneratorExit:
			# This exception happens after the next yield and the connection to the client is closed
			pass

	return generate()


def getCSEStatus() -> str:
	"""Get the current status of the CSE.

		Returns:
			The status of the CSE in JSON format.
	"""
	return json.dumps(getCSEStatusJSON(), indent=4)


def getCSEStatusJSON() -> JSON:
	"""	Get the status, statistics, and runtime information of the CSE.

		Return:
			Status as JSON object.
	"""
	stats = CSE.statistics.getStats()

	status:JSON = {
		'cse': {
			'Type': RC.cseType.name,
			'CSE-ID': RC.cseCsi,
			'CSE-RN': RC.cseRn,
			'SP-ID': RC.cseSPid,
		},
		'network': {
			'hostname': socket.gethostname(),
			'ipaddress': getIPAddress(),
			'POA': RC.csePOA,
		},
		'runtime': {
			'version': C.version,
			'platform': platform.platform(terse=True) + ' (' + platform.machine() + ')',
			'pythonVersion': f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
			'cwd': os.getcwd(),
			'baseDirectory': str(Configuration.baseDirectory),
			'configFile': str(Configuration.configfile) if Configuration.configfile else 'Zookeeper (' + Configuration._args_zkHost + ' - ' + Configuration._args_zkRoot + ')' if Configuration._args_zkHost else 'Unknown',
			'database': {
				'type': Configuration.database_type,
			},
			'currentTime': str(utcDatetime()),
			'startTime': str(datetime.datetime.fromtimestamp(fromAbsRelTimestamp(cast(str, stats[Statistics.cseStartUpTime]), withMicroseconds=False), tz = datetime.timezone.utc)),
			'uptime': stats[Statistics.cseUpTime],
			'load': os.getloadavg() if hasattr(os, 'getloadavg') else [],
			'threads': {
				'running': BackgroundWorkerPool.countJobs()[0],
				'paused': BackgroundWorkerPool.countJobs()[1],
				'native': threading.active_count(),
			},
			'workers': [ {
							'name': w.name,
							'type': 'Actor' if w.maxCount == 1 else 'Worker',
							'interval': float(w.interval) if w.interval > 0.0 else None,
							'runs': w.numberOfRuns if w.interval > 0.0 else None,
						}
						for w in sorted(BackgroundWorkerPool.backgroundWorkers.values(), key = lambda w: w.name.lower()) 
			],
		},
		'logging': {
			'level': L.logLevel.name,
			'errors': stats.get(Statistics.logErrors, 0),
			'warnings': stats.get(Statistics.logWarnings, 0),
		},
		'requests': {
			'http': {
				'received': {
					'create': stats[Statistics.httpCreates],
					'retrieve': stats[Statistics.httpRetrieves],
					'update': stats[Statistics.httpUpdates],
					'delete': stats[Statistics.httpDeletes],
					'notify': stats[Statistics.httpNotifies],
				},
				'sent': {
					'create': stats[Statistics.httpSendCreates],
					'retrieve': stats[Statistics.httpSendRetrieves],
					'update': stats[Statistics.httpSendUpdates],
					'delete': stats[Statistics.httpSendDeletes],
					'notify': stats[Statistics.httpSendNotifies],
				}
			},
			'mqtt': {
				'received': {
					'create': stats[Statistics.mqttCreates],
					'retrieve': stats[Statistics.mqttRetrieves],
					'update': stats[Statistics.mqttUpdates],
					'delete': stats[Statistics.mqttDeletes],
					'notify': stats[Statistics.mqttNotifies],
				},
				'sent': {
					'create': stats[Statistics.mqttSendCreates],
					'retrieve': stats[Statistics.mqttSendRetrieves],
					'update': stats[Statistics.mqttSendUpdates],
					'delete': stats[Statistics.mqttSendDeletes],
					'notify': stats[Statistics.mqttSendNotifies],
				}
			},
			'ws': {
				'received': {
					'create': stats[Statistics.wsCreates],
					'retrieve': stats[Statistics.wsRetrieves],
					'update': stats[Statistics.wsUpdates],
					'delete': stats[Statistics.wsDeletes],
					'notify': stats[Statistics.wsNotifies],
				},
				'sent': {
					'create': stats[Statistics.wsSendCreates],
					'retrieve': stats[Statistics.wsSendRetrieves],
					'update': stats[Statistics.wsSendUpdates],
					'delete': stats[Statistics.wsSendDeletes],
					'notify': stats[Statistics.wsSendNotifies],
				}
			},
			'coap': {
				'received': {
					'create': stats[Statistics.coCreates],
					'retrieve': stats[Statistics.coRetrieves],
					'update': stats[Statistics.coUpdates],
					'delete': stats[Statistics.coDeletes],
					'notify': stats[Statistics.coNotifies],
				},
				'sent': {
					'create': stats[Statistics.coSendCreates],
					'retrieve': stats[Statistics.coSendRetrieves],
					'update': stats[Statistics.coSendUpdates],
					'delete': stats[Statistics.coSendDeletes],
					'notify': stats[Statistics.coSendNotifies],
				}
			},
		},
		'resources': {
			'operations': {
				'created': stats[Statistics.createdResources],
				'retrieved': stats[Statistics.retrievedResources], 
				'updated': stats[Statistics.updatedResources], 
				'deleted': stats[Statistics.deletedResources], 
				'notified': stats[Statistics.notifications], 
				'expired': stats[Statistics.expiredResources],
			},
			'counts': {
				'AE': (_cAE := CSE.dispatcher.countResources(ResourceTypes.AE)),
				'ACP':(_cACP := CSE.dispatcher.countResources(ResourceTypes.ACP)),
				'ACTR': (_cACTR := CSE.dispatcher.countResources(ResourceTypes.ACTR)),
				'CB': (_cCB := CSE.dispatcher.countResources(ResourceTypes.CSEBase)),
				'CIN': (_cCIN := CSE.dispatcher.countResources(ResourceTypes.CIN)),
				'CNT': (_cCNT := CSE.dispatcher.countResources(ResourceTypes.CNT)),
				'CRS': (_cCRS := CSE.dispatcher.countResources(ResourceTypes.CRS)),
				'CSR': (_cCSR := CSE.dispatcher.countResources(ResourceTypes.CSR)),
				'DEPR': (_cDEPR := CSE.dispatcher.countResources(ResourceTypes.DEPR)),
				'FCNT': (_cFCNT := CSE.dispatcher.countResources(ResourceTypes.FCNT)),
				'FCI': (_cFCI := CSE.dispatcher.countResources(ResourceTypes.FCI)),
				'GRP': (_cGRP := CSE.dispatcher.countResources(ResourceTypes.GRP)),
				'LCP': (_cLCP := CSE.dispatcher.countResources(ResourceTypes.LCP)),
				'MGMTOBJ': (_cMGMTOBJ := CSE.dispatcher.countResources(ResourceTypes.MGMTOBJ)),
				'NOD': (_cNOD := CSE.dispatcher.countResources(ResourceTypes.NOD)),
				'NTP': (_cNTP := CSE.dispatcher.countResources(ResourceTypes.NTP)),
				'NTPR': (_cNTPR := CSE.dispatcher.countResources(ResourceTypes.NTPR)),
				'PCH': (_cPCH := CSE.dispatcher.countResources(ResourceTypes.PCH)),
				'PDR': (_cPDR := CSE.dispatcher.countResources(ResourceTypes.PDR)),
				'REQ': (_cREQ := CSE.dispatcher.countResources(ResourceTypes.REQ)),
				'SCH': (_cSCH := CSE.dispatcher.countResources(ResourceTypes.SCH)),
				'SMD': (_cSMD := CSE.dispatcher.countResources(ResourceTypes.SMD)),
				'SUB': (_cSUB := CSE.dispatcher.countResources(ResourceTypes.SUB)),
				'TS': (_cTS := CSE.dispatcher.countResources(ResourceTypes.TS)),
				'TSB': (_cTSB := CSE.dispatcher.countResources(ResourceTypes.TSB)),
				'TSI': (_cTSI := CSE.dispatcher.countResources(ResourceTypes.TSI)),
				'total': _cAE + _cACP + _cACTR + _cCB + _cCIN + _cCNT + _cCRS + _cCSR + _cDEPR + _cFCNT + _cFCI + _cGRP + _cLCP + _cMGMTOBJ + _cNOD + _cNTP + _cNTPR + _cPCH + _cPDR + _cREQ + _cSCH + _cSMD + _cSUB + _cTS + _cTSB + _cTSI
			},
		},
	}

	# Add the database type and configuration
	match status['runtime']['database']['type']:
		case 'tinydb':
			status['runtime']['database']['tinydb'] = {
				'path': f'./{os.path.relpath(Configuration.database_tinydb_path, Configuration.baseDirectory)}',
			} 
		case 'postgresql':
			status['runtime']['database']['postgresql'] = {
				'host': f'{Configuration.database_postgresql_host}:{Configuration.database_postgresql_port}',
				'role': Configuration.database_postgresql_role,
				'database': Configuration.database_postgresql_database,
				'schema': Configuration.database_postgresql_schema,
			}

	return status


def resetCSE() -> None:
	"""Reset the CSE to its initial state.
	"""
	CSE.resetCSE()


def restartCSE() -> None:
	"""Restart the CSE.

		This is done by setting the CSE status to SHUTTINGDOWNRESTART and calling the forceShutdown method.
	"""
	RC.cseStatus = CSEStatus.SHUTTINGDOWNRESTART
	CSE.forceShutdown()	# This might not return (e.g. under Windows)


def setLogLevel(level:str) -> str:
	"""Set the log level of the CSE.

		Args:
			level: The log level to set. Should be one of the Logging levels.

		Returns:
			A response indicating the result 
	"""
	try:
		newLevel = LogLevel[level.upper()]
		L.setLogLevel(newLevel)
		return newLevel.name
	except KeyError:
		return None


def setRequestRecording(param:str) -> str:
	"""Enable or disable request recording.

		Args:
			param: The parameter to set. Should be 'enable' or 'disable'.
		
		Returns:
			The new status of the request recording.
	"""
	match param.lower():
		case 'enable' | 'on':
			L.isInfo and L.log('Enabling request recording')
			Configuration.cse_operation_requests_enable = True
			CSE.request.enableRequestRecording = True
			return 'Request recording enabled'
		case 'disable' | 'off':
			L.isInfo and L.log('Disabling request recording')
			Configuration.cse_operation_requests_enable = False
			CSE.request.enableRequestRecording = False
			return 'Request recording disabled'
		case 'status':
			return 'Request recording is ' + ('enabled' if Configuration.cse_operation_requests_enable else 'disabled')
		case _:
			return 'Invalid parameter. Use "enable", "disable", "status".'


def shutdownCSE() -> None:
	"""Shutdown the CSE.
	"""
	CSE.forceShutdown()	# This might not return (e.g. under Windows)



def getRegistrationStatus() -> JSON:
	"""	Return the registration status of the CSE, and registrations of CSEs and AEs.

		Return:
			A JSON object with the registration status of the CSE, and registrations of CSEs and AEs.
	"""
	status:JSON = {
		'registrar': [],
		'spRegistrations': [],
		'registrees': [],
		'ae': []
	}

	# CSE registrations
	for csr in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.CSR):
		_e = {
			'CSE-ID': csr.csi,
			'SP-ID': f'//{getSPFromID(csr.csi)}' if isAbsolute(csr.csi) else RC.cseSPid,
			'cseType': CSEType(csr.cst.value if isinstance(csr.cst, CSEType) else csr.cst).name,
			'resourceID': csr.ri,
			'resourceName': csr.rn,
			'supportedReleaseVersions': [] if not csr.srv else csr.srv,
			'requestReachable': csr.rr if csr.rr is not None else '',
			'pointsOfAccess': [] if csr.poa is None else csr.poa,
			'descendantCSEs': [] if csr.dcse is None else csr.dcse,
			'registeredSince': str(fromISO8601Date(csr.ct)),

		}
		if isAbsolute(csr.csi) and getSPFromID(csr.csi) != RC.cseSPIDSlashLess:
			status['spRegistrations'].append(_e)
		elif CSE.remote.registrarConfig and CSE.remote.registrarConfig._registrarCSEBaseResource and csr.csi == CSE.remote.registrarConfig._registrarCSEBaseResource.csi:
			status['registrar'].append(_e)
		else:
			status['registrees'].append(_e)

	# AE registrations

	for ae in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.AE):
		status['ae'].append({
			'AE-ID': ae.aei,
			'resourceID': ae.ri,
			'resourceName': ae.rn,
			'App-ID': ae.api,
			'requestReachable': ae.rr,
			'pointsOfAccess': [] if ae.poa is None else ae.poa,
			'registeredSince': str(fromISO8601Date(ae.ct)),
		})

	for n in ('registrar', 'spRegistrations', 'registrees', 'ae'):
		if len(status[n]) == 0:
			del status[n]
	
	return status


