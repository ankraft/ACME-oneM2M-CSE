#
#	Management.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""Management module for accessing and managing CSE internal functions.
"""

from typing import Generator, Optional, Tuple, TextIO
import json, time, socket, platform, os, sys, datetime, threading, csv, io
from urllib.parse import urlparse

from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.style import Style
from rich.pretty import Pretty
from rich.tree import Tree
from rich import box


from ..etc.Constants import RuntimeConstants as RC, Constants as C
from ..etc.Types import CSEStatus, JSON, ResourceTypes, LogLevel, CSEType, Operation, TreeMode, RequestOptionality
from ..etc.DateUtils import fromISO8601Date, utcTime, utcDatetime, toISO8601Date, getResourceDate
from ..etc.IDUtils import isAbsolute, getSPFromID
from ..etc.ResponseStatusCodes import ResponseException
from ..helpers.TextTools import simpleMatch
from ..helpers.OrderedSet import OrderedSet
from ..helpers.NetworkTools import getIPAddress
from ..helpers.BackgroundWorker import BackgroundWorkerPool
from ..resources.CSEBase import getCSE
from ..resources.Resource import Resource


from ..runtime import CSE
from ..runtime.Configuration import Configuration
from ..runtime.Logging import Logging as L


# Used in many "rich" functions
_markupText = Text.from_markup


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
	if (d := getCSEStatusAsDict()) is None:
		d = { 'debug': 'Statistics not available' }
	return json.dumps(d, indent=4)


def getCSEStatusAsDict() -> JSON:
	"""	Get the status, statistics, and runtime information of the CSE.

		Return:
			Status as JSON object.
	"""
	try:
		csebase = getCSE()
		try:
			status:JSON = CSE.pluginManager.statistics.statsAsDict() # type: ignore [attr-defined]
		except AttributeError as e:
			status = {
				'resources': {},
				'logging': {},
			}
			# For example if statistics plugin is not loaded 
			# return None

		status.update({
			'cse': {
				'Type': RC.cseType.name,
				'CSE-ID': RC.cseCsi,
				'CSE-RN': RC.cseRn,
				'SP-ID': csebase.spid if csebase and csebase.spid else RC.cseSPid,
				'IN-CSE-ID': csebase.ici if csebase and csebase.ici else '',
			},
			'network': {
				'hostname': socket.gethostname(),
				'ipaddress': getIPAddress(),
				'POA': RC.csePOA,
			},
		})

		status['resources'].update({
			'AE': (_cAE := CSE.dispatcher.countResources(ResourceTypes.AE)),
			'ACP':(_cACP := CSE.dispatcher.countResources(ResourceTypes.ACP)),
			'ACTR': (_cACTR := CSE.dispatcher.countResources(ResourceTypes.ACTR)),
			'ALST': (_cALST := CSE.dispatcher.countResources(ResourceTypes.ALST)),
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
			'total': _cAE + _cACP + _cACTR + _cALST + _cCB + _cCIN + _cCNT + _cCRS + _cCSR + _cDEPR + _cFCNT + _cFCI + _cGRP + _cLCP + _cMGMTOBJ + _cNOD + _cNTP + _cNTPR + _cPCH + _cPDR + _cREQ + _cSCH + _cSMD + _cSUB + _cTS + _cTSB + _cTSI
		})

		status['runtime'] = {
			'version': C.version,
			'startTime': str(datetime.datetime.fromtimestamp(int(RC.startupTime), tz=None)),
			'currentTime': str(utcDatetime()).split('.')[0],
			'uptime': str(datetime.timedelta(seconds=int(utcTime() - int(RC.startupTime)))),
			'localTime': str(datetime.datetime.now()).split('.')[0],
			'platform': platform.platform(terse=True) + ' (' + platform.machine() + ')',
			'pythonVersion': f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
			'cwd': os.getcwd(),
			'baseDirectory': str(Configuration.baseDirectory),
			'configFile': str(Configuration.configfile) if Configuration.configfile else 'Zookeeper (' + Configuration._args_zkHost + ' - ' + Configuration._args_zkRoot + ')' if Configuration._args_zkHost else 'Unknown',
			'database': {
				'type': Configuration.database_type,
			},
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
			'plugins': [ {
							'module': p.name,
							'filename': p.fileName,
							'instanceClass': p.instance.__class__.__name__,
							'priority': p.priority,
							'state': p.state.name,
							'doc': p.doc,
						}
						for p in CSE.pluginManager.plugins.values()
			]
		}
		status['logging'].update({
				'level': L.logLevel.name,
		})
		
		# Add the database type and configuration
		match Configuration.database_type:
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

	except AttributeError as e:
		L.logErr(f'Error getting CSE status: {e}')
		return None


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




#########################################################################
#
#	Export functions
#


def doExportResource(ri: str, withChildResources: Optional[bool] = False) -> Tuple[int, str]:
	"""	Export a resource and its children to the tmp directory as a shell script with curl commands.

		Args:
			ri: Resource ID of the resource to export.
			withChildResources: If *True*, also export child resources.

		Return:
			Tuple with the number of resources exported, and the filename of the exported file.
	"""
	try:

		if withChildResources:
			resdis = CSE.dispatcher.discoverResources(ri, originator=RC.cseOriginator)
			# insert the parent resource at the beginning of the list
			resdis.insert(0, CSE.dispatcher.retrieveResource(ri))
		else:
			resdis = [CSE.dispatcher.retrieveResource(ri)]

		# Counter for the number of resources exported
		count = 0

		# Create a temporary directory for the export
		outdir = f'{CSE.Configuration.baseDirectory}/tmp'
		os.makedirs(outdir, exist_ok = True)

		filename = f'export-{getResourceDate().rsplit(",", 1)[0]}.sh'
		path = f'{outdir}/{filename}'
		cseUrl = Configuration.http_address
		with open(path, 'w') as f:

			# Write shell file header
			f.write(f'''\
#!/bin/bash
# Exported {ri} from {RC.cseRi} at {getResourceDate()}

cseURL={cseUrl}

function uniqueNumber() {{
	unique_number=""
	for i in {{1..10}}
	do
		unique_number+=$RANDOM
	done
	unique_number=${{unique_number:0:10}}
	echo "$unique_number"
}}

function createResource() {{
	printf '\\nCreating child resource under %s\\n' $cseURL/$4
	printf 'Result: '		  
	curl -X POST -H "X-M2M-Origin: $1" -H "X-M2M-RVI: {RC.releaseVersion}" -H "X-M2M-RI: $(uniqueNumber)" -H "Content-Type: application/json;ty=$2" -d "$3" $cseURL/$4
	printf '\\n'
}}
			
''')

			# Write createResource commands for all resources
			for r in resdis:
				typeShortname = r.typeShortname
				attributes = {}
				for attr in r.getAttributes():
					policy = CSE.validator.getAttributePolicy(r.ty, attr)
					if policy.optionalCreate != RequestOptionality.NP:
						attributes[attr] = r[attr]
				
				# Special handling for some attributes
				if 'et' in attributes:
					del attributes['et']

				attributes = { typeShortname : attributes }
				parentSrn = r.getSrn().rsplit('/', 1)[0]
				# f.write(f'createResource {r.getOriginator()} {r.ty} \'{json.dumps(attributes).replace("\'", "\\\'")}\' \'{parentSrn}\'\n')
				f.write('createResource ' + r.getOriginator() + ' ' + str(r.ty) +' \'' + json.dumps(attributes).replace("\'", "\\\'") + '\' \'' + parentSrn + '\'\n')
				count += 1
		L.console(f'Exported {count} resource(s) to {path}')

	except ResponseException as e:
		L.console(e.dbg, isError = True)
		return 0, e.dbg
	
	return count, f'tmp/{filename}'



def doExportInstances(ri: str, asString: Optional[bool] = False) -> Tuple[int, str]:
	"""	Export instances of a container resource to a CSV file in the tmp directory, or return as a string.

		Args:
			ri: Resource ID of the container resource.
			asString: Return the CSV string instead of writing to a file.

		Return:
			Tuple with the number of instances exported, and the filename of the exported file or the CSV string.

	"""
	_instanceMapping = {
		ResourceTypes.CNT: ResourceTypes.CIN,
		ResourceTypes.CNTAnnc: ResourceTypes.CINAnnc,
		ResourceTypes.FCNT: ResourceTypes.FCI,
		ResourceTypes.TS: ResourceTypes.TSI,
		ResourceTypes.TSAnnc: ResourceTypes.TSIAnnc
	}

	count:int = 0

	def _writeTo(f: TextIO, instances: list[Resource]) -> None:
		nonlocal count

		writer = csv.writer(f)
		# Write CIN and TSI instances
		writer.writerow(['ri', 'st', 'ct', 'con', 'cnf', 'structured_resource_identifier'])
		for instance in instances:
			writer.writerow([instance.ri, instance.st, instance.ct, instance.con, instance.cnf, instance.getSrn()])
			count += 1


	try:
		L.console('Export Instance Resources', isHeader=True)
		container = CSE.dispatcher.retrieveResource(ri)
		if container.ty in [ResourceTypes.FCNT, ResourceTypes.FCNTAnnc]:
			# TODO FCNT export not supported at the moment
			return 0, L.console(f'Export of FCNT {ri} not supported', isError=True)

		if not ResourceTypes.isContainerResource(container.ty):
			return 0, L.console(f'{ri} is not a container resource', isError=True)
		if not (instances := CSE.dispatcher.retrieveDirectChildResources(ri, _instanceMapping[container.ty])):
			L.console(f'No instances found under {ri}', isError=True)
			return 0, f'No instances found under {ri}'

		else:
			if not asString:
				# Create a temporary directory for the export
				outdir = f'{CSE.Configuration.baseDirectory}/tmp'
				os.makedirs(outdir, exist_ok=True)

				# get the filename and open the file for writing
				filename = f'instances-{getResourceDate().rsplit(",", 1)[0]}.csv'
				path = f'{outdir}/{filename}'
				with open(path, 'w') as f:
					_writeTo(f, instances)
				L.console(f'Exported {count} instances to {filename}')
				return count, f'tmp/{filename}'
			
			# return the CSV string
			else:
				with io.StringIO() as csvString:
					_writeTo(csvString, instances)
					return count, csvString.getvalue()
	except Exception as e:
		if hasattr(e, 'dbg'):
			L.console(e.dbg, isError=True)
			return 0, e.dbg
		else:
			L.console(str(e), isError=True)
			return 0, str(e)
	


#########################################################################
#
#	CSE Structure ouutput
#

def getStructurePuml(maxLevel: Optional[int] = 0) -> str:
	"""	This function will generate a PlanUML graph of a CSE's structure, including:
			- The CSE, Type, http, port
			- The CSE's resource tree
			- The Registrar CSE (if any)
			- A list of descendant CSE's (if any)
		
		This function calls itself recursively to generate the tree structure.
		
		Args:
			maxLevel:	The maximum level of the tree to print. 0 means all levels.
		
		Return:
			The PlanUML graph as a string.
	"""

	def getChildren(res:Resource, level:int) -> str:
		""" Find and print the children in the tree structure. """
		result = ''
		if maxLevel > 0 and level == maxLevel:
			return result
		chs = CSE.dispatcher.retrieveDirectChildResources(res.ri)
		for ch in chs:
			result += ' ' * 2 * level + f'|_ {ch.rn} <color:grey>< {ResourceTypes(ch.ty).typeShortname()} ></color>\n'
			result += getChildren(ch, level+1)
		return result

	result = """@startuml
!define lightgrey eeeeee
skinparam defaultTextAlignment center
skinparam note {
BorderColor grey
backgroundColor lightgrey
RoundCorner 25
TextAlignment left
FontSize 10
}
skinparam rectangle {
Shadowing<< CSE >> false
bordercolor<< CSE >> #cccccc
}
skinparam linetype ortho
"""

	# Own CSE node & http interface
	result += 'rectangle << CSE >> {\n'
	address = urlparse(Configuration.http_address)
	(ip, _) = tuple(address.netloc.split(':'))
	result += f'node CSE as "<color:green>{RC.cseCsi[1:]}</color> ({RC.cseType.name})\\n{ip}" #white\n'

	# Own http interface
	http = 'https' if Configuration.http_security_useTLS else 'http'
	result += f'interface "{http}\\n{Configuration.http_port}" as http_own #white\n'

	# MQTT broker connection
	if Configuration.mqtt_enable:
		mqtt = 'mqtts' if Configuration.mqtt_security_useTLS else 'mqtt'
		result += f'interface "{mqtt}\\n{mqtt}://{Configuration.mqtt_address}:{Configuration.mqtt_port}" as mqtt_own #white\n'
	
	# Own CoAP interface
	if Configuration.coap_enable:
		result += f'interface "coap\\n{Configuration.coap_port}" as coap_own #white\n'

	# Own WS interface
	if Configuration.websocket_enable:
		ws = 'wss' if Configuration.websocket_security_useTLS else 'ws'
		result += f'interface "{ws}\\n{Configuration.websocket_port}" as ws_own #white\n'

	# Build Resource Tree
	result += 'note left of CSE\n'
	result += '**Resource Tree**\n\n'
	cse = getCSE()
	result += f'{cse.rn}\n'
	result += getChildren(cse, 0)
	result += 'end note\n'

	# Build Own
	result += 'http_own -[norank]- [CSE] #lightblue\n'
	if Configuration.mqtt_enable:
		result += 'mqtt_own -[norank]- [CSE] #lightblue\n'
	if Configuration.coap_enable:
		result += 'coap_own -[norank]- [CSE] #lightblue\n'
	if Configuration.websocket_enable:
		result += 'ws_own -[norank]- [CSE] #lightblue\n'
	result += '}\n' # rectangle

	# Has parent Registrar CSE?
	if len(Configuration.cse_registrars) > 0:
		for index, registrar in enumerate(Configuration.cse_registrars.values()):
			registrarCSE = registrar._registrarCSEBaseResource
			bg = 'white' if registrarCSE else 'lightgrey'
			color = 'green' if registrarCSE else 'black'
			address = urlparse(registrar.address)
			(ip, port) = tuple(address.netloc.split(':'))
			registrarType = CSEType(registrarCSE.cst).name if registrarCSE else '???'
			result += f'cloud PARENT_{index} as "<color:{color}>{registrar.cseID[1:] if registrar.spID != RC.cseSPid else registrar.spID + registrar.cseID}</color> ({registrarType})\\n{registrar.address}" #{bg}\n'
			result += f'CSE -UP- PARENT_{index}\n'

	
	# Has CSE descendants?
	if RC.cseType != CSEType.ASN:
		cnt = 0
		connections = {}
		for desc in CSE.remote.descendantCSR.keys():
			csi = desc[1:]
			(csr, atCsi) = CSE.remote.descendantCSR[desc]
			poa = f'\\n{csr.poa}' if csr else ''
			typeShortname = f' ({CSEType(csr.cst).name})' if csr and csr.cst else ''
			shape = 'node' if csr else 'rectangle'
			result += f'{shape} d{cnt} as "<color:green>{csi}</color>{typeShortname}{poa}" #white\n'
			connections[desc] = (cnt, atCsi)
			cnt += 1
		
		for key in connections.keys():
			connection = connections[key]
			nodeNr = connection[0]
			atCsi = connection[1]
			if atCsi == RC.cseCsi:
				result += f'd{nodeNr} -UP- CSE\n'
			else:
				if atCsi in connections:
					subcon = connections[atCsi]
					result += f'd{connection[0]} -UP- d{subcon[0]}\n'

	# end
	result += '@enduml'
	return result


# TODO events transit requests
# TODO notifications
def getStatusRich(style:Optional[Style] = Style(), 
				  withProgress:Optional[bool] = True,
				  textStyle:Optional[Style] = None) -> Table:
	"""	Generate an overview about various resources, event counts, and more.

		Args:
			style: Rich style.
			withProgress: Display with progress indicator.
			textStyle: Rich text style. If this is not set then the style is used for the text as well.
		
		Return:
			Rich Table object.
	"""

	if (status := getCSEStatusAsDict()) is None:
		L.console('Statistics not available', isError=True)
		return Table()

	def _stats() -> Table:
		#
		#	Right columns
		#

		#
		#	Misc
		#

		# Calculate some values upfront
		try:
			_ipAddress = status['network']['ipaddress']
		except Exception as e:
			_ipAddress = 'N/A'

		_poas = status['network']['POA']
		_poa = _poas[0] if _poas[0] else 'N/A'
		if len(_poas) > 1:
			_poa += '\n' + '\n'.join([f'                    {poa}' for poa in _poas[1: ]])
		
		_load = 'N/A | N/A | N/A'
		if len((_loadValues := status['runtime']['load'])) == 3:
			_load = f'{_loadValues[0]:.2f} | {_loadValues[1]:.2f} | {_loadValues[2]:.2f}'

		miscLeft  = Text(style = textStyle) + \
f'''
CSE-ID | CSE-Name : {status['cse']['CSE-ID']}  |  {status['cse']['CSE-RN']}
Type              : {status['cse']['Type']}
SP-ID             : {status['cse']['SP-ID']}
IN-CSE-ID         : {status['cse']['IN-CSE-ID']}
Hostname          : {status['network']['hostname']}
IP-Address        : {_ipAddress}
PoA               : {_poa}

CWD               : {status['runtime']['cwd']}
Runtime Directory : {status['runtime']['baseDirectory']}
Config Source     : {status['runtime']['configFile']}

StartTime         : {status['runtime']['startTime']} (UTC)
Uptime            : {status['runtime']['uptime']}

Load              : {_load}

Platform          : {status['runtime']['platform']}
Python Version    : {status['runtime']['pythonVersion']}
ACME CSE Version  : {status['runtime']['version']}'''

		miscHeight = len(miscLeft.split('\n'))
		panelMiscLeft = Panel(miscLeft, 
								box=box.ROUNDED, 
								title=_markupText('[b]Misc[/b]'), 
								title_align='left', 
								padding=(1, 1, 0, 1),
								expand=True,
								style=style)

		#
		#	Request stats
		#
		if Configuration.cse_statistics_enable:
			_st = status['operations']
			resourceOps = _markupText('[u]Operations[/u]', style=textStyle) + \
f'''
				
Created  : {_st["created"]}
Retrieved: {_st["retrieved"]}
Updated  : {_st["updated"]}
Deleted  : {_st["deleted"]}
Notified : {_st["notified"]}
Expired  : {_st["expired"]}

''' 
			resourceOps += _markupText(f'[dim]Includes virtual\nresources[/dim]')
			opsHeight = len(resourceOps.split('\n'))

			# Construct the protocol stats columns for all the protocols and request types
			protColumns = []
			for _prot, _title in [('coap', 'CoAP'), ('http', 'HTTP'), ('mqtt', 'MQTT'), ('ws', 'WS')]:
				for _type, _h in [('received', 'R'), ('sent', 'S')]:
					_st = status['requests'][_prot][_type]
					protColumns.append(_markupText(f'[u]{_title}:{_h}[/u]\n', style=textStyle) + \
f'''
C: {_st["create"]}
R: {_st["retrieve"]}
U: {_st["update"]}
D: {_st["delete"]}
N: {_st["notify"]}
''')


			#
			#	Logs
			#

			miscLogs  = Text(style=textStyle) + \
f'''
LogLevel : {status["logging"]["level"]}
Errors   : {status["logging"]["errors"]}
Warnings : {status["logging"]["warnings"]}\
'''

		else:
			# Statistics are disabled
			resourceOps  = _markupText('[dim]Statistics are disabled[/dim]\n', style=textStyle)
			protColumns = [ _markupText('', style=textStyle) for _ in range(8)]
			miscLogs = _markupText('\n[dim]Statistics are disabled[/dim]\n\n\n', style=textStyle)
			opsHeight = 2


		#
		#	Database
		#

		_dbType = status["runtime"]["database"]["type"]
		miscDB = Text(style=textStyle)
		match _dbType:
			case 'postgresql':
				_db = status["runtime"]["database"]["postgresql"]
				miscDB += \
f'''
Type     : {_dbType}
Host     : {_db["host"]}
Role     : {_db["role"]}
Database : {_db["database"]}
Schema   : {_db["schema"]}'''
				
			case 'tinydb':
				_db = status["runtime"]["database"]["tinydb"]						
				miscDB += \
f'''
Type     : {_dbType}
Path     : {_db["path"]}


'''
				
			case 'memory':
				miscDB += \
f'''
Type     : {_dbType}



'''				


		#
		#	Construct the panels for the right column
		#
		panelMiscLogs = Panel(miscLogs, 
								box=box.ROUNDED, 
								title=_markupText('[b]Logs[/b]'), 
								title_align='left', 
								padding=(0, 1, 0, 1),
								expand=True,
								style=style)
		logsHeight = 4

		tableWorkers = Table(expand=True, row_styles=[ '', L.tableRowStyle], box=None, padding=(0, 0, 0, 1))
		tableWorkers.add_column(_markupText('[u]Name[/u]\n', style=textStyle), no_wrap=True)
		tableWorkers.add_column(_markupText('[u]Type[/u]\n', style=textStyle), no_wrap=True)
		tableWorkers.add_column(_markupText('[u]Intvl (s)[/u]\n', style=textStyle), no_wrap=True, justify='right')
		tableWorkers.add_column(_markupText('[u]#Runs[/u]\n', style=textStyle), no_wrap=True, justify='right')
		for w in status['runtime']['workers']:
			tableWorkers.add_row(w['name'], 
									w['type'], 
									str(w['interval']) if w['interval'] is not None else '', 
									str(w['runs']) if w['runs'] is not None else '', 
									style = textStyle)

		# for w in sorted(BackgroundWorkerPool.backgroundWorkers.values(), key = lambda w: w.name.lower()):
		# 	a = 'Actor' if w.maxCount == 1 else 'Worker'
		# 	tableWorkers.add_row(w.name, a, str(float(w.interval)) if w.interval > 0.0 else '', str(w.numberOfRuns) if w.interval > 0.0 else '', style = textStyle)
		
		panelWorkers = Panel(tableWorkers, 
								box=box.ROUNDED, 
								title=_markupText('[b]Workers[/b]'), 
								title_align='left', 
								padding=(1, 1, 0, 1),
								expand=True,
								style=style)
		workersHeight = len(tableWorkers.rows) + 3	# table rows + header

		tableThreads = Text(style=textStyle) + \
f'''
Running  : {status['runtime']["threads"]["running"]}
Paused   : {status['runtime']["threads"]["paused"]}
Native   : {status['runtime']["threads"]["native"]}'''
			
		panelThreads = Panel(tableThreads, 
						box=box.ROUNDED, 
						title=_markupText('[b]Threads[/b]'), 
						title_align='left', 
						padding=(0, 1, workersHeight-4, 1),
						expand=True,
						style=style)
		threadsHeight = 6

		# Last Panel that needs to be adapted in height 
		panelMiscDB = Panel(miscDB, 
							box=box.ROUNDED, 
							title=_markupText('[b]Database[/b]'), 
							title_align='left', 
							padding=(0, 1, miscHeight + workersHeight - threadsHeight - logsHeight - 12, 1),	# adapt height accoring to misc panel height
							expand=True,
							style=style)

		#
		#	Construct the requests panel with all the protocol stats
		#
		requestsGrid = Table.grid(expand=True)
		requestsGrid.add_column(ratio=28)
		requestsGrid.add_column(ratio=12)
		requestsGrid.add_column(ratio=12)
		requestsGrid.add_column(ratio=12)
		requestsGrid.add_column(ratio=12)
		requestsGrid.add_column(ratio=12)
		requestsGrid.add_column(ratio=12)
		requestsGrid.add_column(ratio=12)
		requestsGrid.add_column(ratio=12)
		requestsGrid.add_row(resourceOps, *protColumns)

		panelRequests = Panel(requestsGrid, 
								box=box.ROUNDED, 
								title=_markupText('[b]Requests[/b]'), 
								title_align='left', 
								padding=(1, 0, 0, 1),
								expand=True,
								style=style)

		panelMiscRight = Table.grid(expand=True,)
		panelMiscRight.add_column()
		panelMiscRight.add_row(panelMiscLogs)
		panelMiscRight.add_row(panelMiscDB)

		infoGrid = Table.grid(expand=True, padding=(0, 1, 0, 0))
		infoGrid.add_column(ratio=70, no_wrap=True)
		infoGrid.add_column(ratio=30)
		infoGrid.add_row(panelMiscLeft, panelMiscRight)

		workerGrid = Table.grid(expand=True, padding=(0, 1, 0, 0))
		workerGrid.add_column(ratio=70)
		workerGrid.add_column(ratio=30)
		workerGrid.add_row(panelWorkers, panelThreads)

		rightGrid = Table.grid(expand=True)
		rightGrid.add_column()
		rightGrid.add_row(panelRequests)
		rightGrid.add_row(workerGrid)
		rightGrid.add_row(infoGrid)

		#
		#	Left column
		#

		_cts = status["resources"]
		resourceTypes = Text(style=textStyle) + \
f'''
AE      : {_cts['AE']}
ACP     : {_cts['ACP']}
ACTR    : {_cts['ACTR']}
ALST    : {_cts['ALST']}
CB      : {_cts['CB']}
CIN     : {_cts['CIN']}
CNT     : {_cts['CNT']}
CRS     : {_cts['CRS']}
CSR     : {_cts['CSR']}
DEPR    : {_cts['DEPR']}
FCNT    : {_cts['FCNT']}
FCI     : {_cts['FCI']}
GRP     : {_cts['GRP']}
LCP     : {_cts['LCP']}
MgmtObj : {_cts['MGMTOBJ']}
NOD     : {_cts['NOD']}
NTP     : {_cts['NTP']}
NTPR    : {_cts['NTPR']}
PCH     : {_cts['PCH']}
PDR     : {_cts['PDR']}
REQ     : {_cts['REQ']}
SCH     : {_cts['SCH']}
SMD     : {_cts['SMD']}
SUB     : {_cts['SUB']}
TS      : {_cts['TS']}
TSB     : {_cts['TSB']}
TSI     : {_cts['TSI']}

'''
		resourceTypes += _markupText(f'[b]Total   : {_cts["total"]}[/b]')

		# Not sure why rich does not use 1 per line for padding. For some unknown reasons
		# we need to multiply the number of lines with 2 to get the correct padding.
		# _padding = 9 + (miscHeight - 15) * 2
		_padding = opsHeight + workersHeight + miscHeight + 6 - len(resourceTypes.split('\n'))
		
		panelResources = Panel(resourceTypes, 
								box=box.ROUNDED, 
								title=_markupText('[b]Resources[/b]'), 
								title_align='left', 
								padding=(0, 0, _padding, 1),
								expand=True,
								style=style)

		result = Table.grid(expand=True, padding=(0, 1, 0, 0))
		result.add_column(width=15)
		result.add_column()
		result.add_row(panelResources, rightGrid )

		return result

	# Assign the text style if not None.
	if textStyle is None:
		textStyle = style
	if withProgress:
		with L.consoleStatusWait('Collecting...'):
			return _stats()
	else:
		return _stats()


def getRegistrationsRich(style: Optional[Style] = Style(), 
						 textStyle: Optional[Style] = None) -> Table:
	"""	Create and return an overview about the registrar, registrees, and
		descendant CSE's.

		Args:
			style: Style for the general output.
			textStyle: Style for the text.

		Return:
			Rich formatted string.
	"""

	# Assign the text style if not None.
	if textStyle is None:
		textStyle = style

	def _addCSERow(table: Table, 
					style: Style, 
					cse: Resource, 
					registrarCSE: Resource, 
					registrees: list[str]) -> None:
		table.add_row(cse.csi, 
						CSEType(cse.cst.value if isinstance(cse.cst, CSEType) else cse.cst).name, 
						cse.ri, 
						'' if not cse.srv else ', '.join(cse.srv),
						str(cse.rr) if cse.rr is not None else '', 
						'' if cse.poa is None else ', '.join(cse.poa),
						'' if not registrarCSE else registrarCSE.csi,
						'' if not registrees else ', '.join(registrees),
						style = style)

	cse = getCSE()

	tableCSE = Table(row_styles=[ '', L.tableRowStyle], box=None, expand=True)
	tableCSE.add_column(_markupText('[u]CSE-ID[/u]\n', style=textStyle), no_wrap=True)
	tableCSE.add_column(_markupText('[u]Type[/u]\n', style=textStyle), no_wrap=True)
	tableCSE.add_column(_markupText('[u]Resource ID[/u]\n', style=textStyle), width=12, no_wrap=True)
	tableCSE.add_column(_markupText('[u]Release[/u]\n', style=textStyle), no_wrap=False)
	tableCSE.add_column(_markupText('[u]Reachable[/u]\n', style=textStyle), no_wrap=True)
	tableCSE.add_column(_markupText('[u]POA[/u]\n', style=textStyle), no_wrap=False)
	tableCSE.add_column(_markupText('[u]Registrar[/u]\n', style=textStyle), no_wrap=True)
	tableCSE.add_column(_markupText('[u]Registrees[/u]\n', style=textStyle), no_wrap=False)

	# one row for the CSE itself
	_addCSERow(tableCSE, 
				Style.combine((Style(italic=True, bold=True), textStyle)), 
				cse, 
				CSE.remote.registrarConfig._registrarCSEBaseResource if CSE.remote.registrarConfig else None, 
				CSE.remote.descendantCSR.keys()) #type:ignore[arg-type]

	spCsr:list[Resource] = []
	for csr in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.CSR):
		if isAbsolute(csr.csi) and getSPFromID(csr.csi) != RC.cseSPIDSlashLess:	# store the CSR for other SP for later
			spCsr.append(csr)
			continue
		if CSE.remote.registrarConfig and CSE.remote.registrarConfig._registrarCSEBaseResource and csr.csi == CSE.remote.registrarConfig._registrarCSEBaseResource.csi:
			_addCSERow(tableCSE, textStyle, csr, None, [cse.csi] + csr.dcse)
		else:
			_addCSERow(tableCSE, textStyle, csr, cse, csr.dcse)

	panelCSE = Panel(tableCSE, 
						box=box.ROUNDED, 
						title=_markupText('[b]CSE – Common Services Entities[/b]'), 
						title_align='left', 
						padding = (1, 0, 0, 0),
						expand=True,
						style=style)

	if spCsr:

		tableSPCSE = Table(row_styles=[ '', L.tableRowStyle], box=None, expand=True)
		tableSPCSE.add_column(_markupText('[u]SP-ID[/u]\n', style=textStyle), no_wrap=True)
		tableSPCSE.add_column(_markupText('[u]CSE-ID[/u]\n', style=textStyle), no_wrap=True)
		tableSPCSE.add_column(_markupText('[u]Resource ID[/u]\n', style=textStyle), no_wrap=True)
		tableSPCSE.add_column(_markupText('[u]Release[/u]\n', style=textStyle), no_wrap=False)
		tableSPCSE.add_column(_markupText('[u]POA[/u]\n', style=textStyle), no_wrap=False)

		for csr in spCsr:
			tableSPCSE.add_row(f'//{getSPFromID(csr.csi)}',
							csr.csi,
							csr.ri, 
							'' if not csr.srv else ', '.join(csr.srv),
							'' if csr.poa is None else ', '.join(csr.poa),
							style=textStyle)
		
		panelSPCSE = Panel(tableSPCSE, 
						box=box.ROUNDED, 
						title=_markupText("[b]SP CSE – Services Providers via Mcc'[/b]"), 
						title_align='left', 
						padding=(1, 0, 0, 0),
						expand=True,
						style=style)
	

	tableAE = Table(row_styles=[ '', L.tableRowStyle], box=None, expand=True)
	tableAE.add_column(_markupText('[u]AE-ID[/u]\n', style=textStyle), width=10, no_wrap=True)
	tableAE.add_column(_markupText('[u]Name[/u]\n', style=textStyle), width=10, no_wrap=True)
	tableAE.add_column(_markupText('[u]Resource ID[/u]\n', style=textStyle), width=10, no_wrap=True)
	tableAE.add_column(_markupText('[u]APP-ID[/u]\n', style=textStyle), width=10, no_wrap=True)
	tableAE.add_column(_markupText('[u]Reachable[/u]\n', style=textStyle), width=5, no_wrap=True)
	tableAE.add_column(_markupText('[u]POA[/u]\n', style=textStyle), width=15, no_wrap=False)

	for ae in CSE.dispatcher.retrieveResourcesByType(ResourceTypes.AE):
		tableAE.add_row(ae.aei, 
						ae.rn, 
						ae.ri, 
						ae.api, 
						str(ae.rr), 
						'' if ae.poa is None else ', '.join(ae.poa),
						style=textStyle)

	panelAE = Panel(tableAE, 
					box=box.ROUNDED, 
					title=_markupText('[b]AE – Application Entities[/b]'), 
					title_align='left', 
					padding=(1, 0, 0, 0),
					expand=True,
					style=style)

	result = Table.grid(expand=True)
	result.add_column()
	result.add_row(panelCSE)
	if spCsr:
		result.add_row(panelSPCSE)
	result.add_row(panelAE)

	return result


def getResourceTreeText(maxLevel: int = 0) -> str:
	"""	This function will generate a Text tree of a CSE's resource structure.

		Args: 
			maxLevel: Maximum tree level to render. Currently not supported.
		
		Return:
			Pure text rendering of the resource tree.

		Todo:
			Support the *maxLevel* parameter.
	"""
	from rich.console import Console as RichConsole

	console = RichConsole(color_system=None)
	console.begin_capture()
	console.print(getResourceTreeRich(withProgress=False))
	return '\n'.join([item.rstrip() for item in console.end_capture().splitlines()])



def getResourceTreeRich(maxLevel: int = 0, 
						parent: Optional[str] = None, 
						style: Optional[Style] = Style(),
						withProgress: Optional[bool] = True,
						treeMode: Optional[TreeMode] = TreeMode.NORMAL) -> Tree:
	"""	This function will generate a Rich tree structure of a CSE's resource structure.

		Args:
			maxLevel: The maximum level for the result tree.
			parent: The resource ID from where to start the tree. The default is the CSEBase.
			style: The Rich Style to use.
			withProgress: Display a progress indicator while gathering the tree.
		Return:
			Return a Rich Tree object.
	"""

	def info(res: Resource) -> str:
		"""	Retrieve further information about the current resource.
		
			This depends on the current `treeMode` mode.
			
			Args:
				res: The resource to handle.
		"""

		# Determine extra infos
		extraInfo = ''
		if treeMode not in [ TreeMode.COMPACT, TreeMode.CONTENTONLY ]: 
			# if res.ty in [ T.FCNT, T.FCI] :
			# 	extraInfo = f' (cnd={res.cnd})'
			match res.ty:
				case ResourceTypes.FCNT | ResourceTypes.FCI:
					extraInfo = f' ({res.cnf})' if res.cnf else ''
				case ResourceTypes.CSEBase | ResourceTypes.CSEBaseAnnc | ResourceTypes.CSR:
					extraInfo = f' (csi={res.csi})'

		# Determine content
		contentInfo = ''
		if treeMode in [ TreeMode.CONTENT, TreeMode.CONTENTONLY ]:
			match res.ty:
				case ResourceTypes.CIN | ResourceTypes.TSI:
					contentInfo = f'{res.con}' if res.con else ''
				case ResourceTypes.FCNT | ResourceTypes.FCI:
					contentInfo = ', '.join([ f'{attr}={str(res[attr])}' for attr in res.dict if CSE.validator.isExtraResourceAttribute(attr, res) ])

		# construct the info
		info = ''
		match treeMode:
			case TreeMode.COMPACT:
				info = f'-> {res[C.attrRtype]}'
			case TreeMode.CONTENT:
				if len(contentInfo) > 0:
					info = f'-> {res[C.attrRtype]}{extraInfo} | {contentInfo}'
				else:
					info = f'-> {res[C.attrRtype]}{extraInfo}'
			case TreeMode.CONTENTONLY:
				if len(contentInfo) > 0:
					info = f'-> {contentInfo}'
			case _: # treeMode == NORMAL
				if res.isVirtual():
					info = f'-> {res[C.attrRtype]}{extraInfo} (virtual)'
				else:
					info = f'-> {res[C.attrRtype]}{extraInfo} | ri={res.ri}'

		return f'{res.rn} [dim]{info}[/dim]'


	def getChildren(res:Resource, tree:Tree, level:int) -> None:
		""" Recursively find and print the children in the tree structure. 

			Args:
				res: Current resource to handle.
				tree: The current Rich Tree node.
				level: The current resource tree level.
		"""
		if maxLevel > 0 and level == maxLevel:
			return
		chs = CSE.dispatcher.retrieveDirectChildResources(res.ri)
		for ch in chs:
			if ch.isVirtual() and not Configuration.console_treeIncludeVirtualResource:	# Ignore virual resources
				continue
			# Ignore resources/resource patterns 
			ri = ch.ri
			if len([ p for p in Configuration.console_hideResources if simpleMatch(p, ri) ]) > 0:
				continue
			branch = tree.add(info(ch))
			getChildren(ch, branch, level+1)
	

	def getTree() -> Optional[Tree]:
		"""	Build and return the resource tree.

			Return:
				A Rich Tree object, or *None*.
		"""
		if parent:
			if not (res := CSE.dispatcher.retrieveResource(parent)):
				return None
		else:
			res = getCSE()
		if not res:
			return None
		tree = Tree(info(res), style=style, guide_style=style)
		getChildren(res, tree, 0)
		return tree

	if withProgress:
		with L.consoleStatusWait('Collecting...'):
			tree = getTree()
	else:
		tree = getTree()

	return tree



def getRequestsRich(id: Optional[str] = None) -> Tuple[Table, str]:
	"""	Generate a Rich table with all requests and a PlantUML sequence diagram.

		Args:
			id: If set, then only the requests for this resource ID are returned.
		
		Return:
			A tuple with a Rich Table object and a PlantUML sequence diagram string.
	"""

	table = Table(row_styles=[ '', L.tableRowStyle],  expand=True)
	table.add_column(_markupText('[u]Timestamp[/u]\n'), no_wrap=True)
	table.add_column(_markupText('[u]Originator[/u]\n'), no_wrap=True)
	table.add_column(_markupText('[u]Operation[/u]\n'), no_wrap=True)
	if not id:
		table.add_column(_markupText('[u]Resource ID[/u]\n'), no_wrap=True)
	table.add_column(_markupText('[u]Request[/u]\n'))
	table.add_column(_markupText('[u]Response[/u]\n'))

	uml = """\
@startuml
hide footbox
!theme plain
skinparam backgroundcolor transparent
skinparam BoxPadding 60

"""

	participants = OrderedSet()
	targets = OrderedSet()
	seqs = ''
	origPrefix = '<originator>\\n'

	for r in CSE.storage.getRequests(id, sortedByOt=True):
		req = r['req']
		op = req['op']
		to = None

		ri = r.get('ri', '(unknown)')
		to = req.get('to', '(unknown)')
		if op == Operation.NOTIFY:
			if '/' in ri:	
				ri = ri.rsplit('/', 1)[-1]
			ri = f'"{origPrefix}{ri}"'
		else:
			ri = f'"{ri}"'

		org = r['org']
		if org == RC.cseCsi or org == f'{RC.cseSPid}/{RC.cseCsi}':
			participants.add(orig := f'"{org[1:]}"')	# CSI without the leading /
		else:
			participants.add(orig := f'"{origPrefix}{org}"')
		

		ty = req.get('ty') if op == 1 else None

		if id:
			table.add_row(toISO8601Date(r['ts']), 
						org,
						Operation(op).name, 
						Pretty(req, indent_size=2),
						Pretty(r['rsp'], indent_size=2))
		else:
			table.add_row(toISO8601Date(r['ts']), 
						org,
						Operation(op).name, 
						ri,
						Pretty(req, indent_size=2),
						Pretty(r['rsp'], indent_size=2))

		if ri not in participants:
			targets.add(ri)
		
		tyn = ResourceTypes(ty).name if ResourceTypes.has(ty) else f'UNKNOWN_TYPE_{ty}'
		rsc = r['rsp']['rsc']
		color = 'green' if rsc < 3000 else 'red'
		seqs += f'{orig} -> {ri}: <b>{Operation(op).name} {"<" + tyn + ">" if ty else ""}</b>\\n<i>{to}</i>\n'
		seqs += f'{orig} <-[#{color}] {ri}: RSC: {rsc} \n'
	

	uml += '\n'.join([f'participant {p}' for p in participants]) + '\n'
	uml += f'box "CSE {RC.cseCsi}" #f8f8f8\n'
	uml += '\n'.join([f'participant {p}' for p in targets]) + '\n'
	uml += 'end box\n'
	uml += seqs
	uml += '@enduml\n'

	return (table, uml)
