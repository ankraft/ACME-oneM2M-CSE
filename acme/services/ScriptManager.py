#
#	ScriptManager.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing scripts and batch job executions
#


from __future__ import annotations
from typing import Dict, Union
from pathlib import Path
import json, os, fnmatch
from ..etc.Types import JSON, ACMEIntEnum, CSERequest, Operation, ResourceTypes
from ..services.Configuration import Configuration
from ..helpers.Interpreter import PContext, checkMacros, PError, PState, PFuncCallable
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..helpers import TextTools
from ..services.Logging import Logging as L
from ..services import CSE
from ..etc import Utils
from ..resources import Factory


# TODO implement defaults
# TODO on event (better than shutdown, etc?)
# TODO script check interval configurable
# TODO script debug loggng configurable

# TODO add debugging to commands


class ACMEPContext(PContext):
	"""	Child class of the `PContext` context class that adds further commands and details.
	"""

	def __init__(self, 
				 script:Union[str, list[str]], 
				 preFunc:PFuncCallable = None,
				 postFunc:PFuncCallable = None, 
				 errorFunc:PFuncCallable = None,
				 filename:str = None) -> None:
		super().__init__(script, 
						 commands = {	
							 			'create':		self.doCreate,
							 			'delete':		self.doDelete,
										'importraw':	self.doImportRaw,
							 			'notify':		self.doNotify,
						 				'originator':	self.doOriginator,
						 				'poa':			self.doPoa,
										'reset':		self.doReset,
							 			'retrieve':		self.doRetrieve,
										'run':			self.doRun,
										'setconfig':	self.doSetConfig,
						 				'storageremove':self.doStorageRemove,
										'storageput':	self.doStoragePut,
							 			'update':		self.doUpdate,
									}, 
						 macros = 	{ 
							 			'attribute':	lambda c, m: self.doAttribute(c, m),
										'storageHas':	lambda c, m: self.doStorageHas(c, m),
										'storageGet':	lambda c, m: self.doStorageGet(c, m),
						 				'__default__':	lambda c, m: Configuration.get(m),
						  			},
						 logFunc = self.log, 
						 logErrorFunc = self.logError,
						 printFunc = self.prnt,
						 preFunc = preFunc, 
						 postFunc = postFunc, 
						 errorFunc = errorFunc)

		self.poas:Dict[str, str] = { CSE.cseCsi: None }		# Default: Own CSE
		self.filename = filename
		self.fileMtime = os.stat(filename).st_mtime



	def log(self, pcontext:PContext, msg:str) -> None:
		"""	Callback for normal log messages.

			Args:
				pcontext: Script context.
				msg: log message.
		"""
		L.isDebug and L.logDebug(msg)


	def logError(self, pcontext:PContext, msg:str) -> None:
		"""	Callback for error log messages.

			Args:
				pcontext: Script context.
				msg: log message.
		"""
		L.logErr(msg)


	def prnt(self, pcontext:PContext, msg:str) -> None:
		"""	Callback for `print` command messages.

			Args:
				pcontext: Script context.
				msg: log message.
		"""
		L.isInfo and L.log(msg)
	

	def isStartup(self) -> bool:
		"""	Check whether a script is marked as to be run during startup of the CSE. 
			This is done by adding the "@startup" meta data line in a script.

			Example:
				@startup
			
			Returns:
				boolean
		"""
		return 'startup' in self.meta
	

	def isShutdown(self) -> bool:
		"""	Check whether a script is marked as to be run during shutdown of the CSE. 
			This is done by adding the "@shutdown" meta data line in a script.

			Example:
				@shutdoown
			
			Returns:
				boolean
		"""
		return 'shutdown' in self.meta


	def isRestart(self) -> bool:
		"""	Check whether a script is marked as to be run during restart of the CSE. 
			This is done by adding the "@restart" meta data line in a script.

			Example:
				@restart
			
			Returns:
				boolean
		"""
		return 'restart' in self.meta

	
	@property
	def errorMessage(self) -> str:
		"""	Format and return an error message.
		
			Return:
				String with the error message.
		"""
		return f'{self.error[0].name} error in {self.filename}:{self.error[1]} - {self.error[2]}'


	@property
	def filename(self) -> str:
		"""	Return the script's filename (from the `filename` meta information).
		
			Return:
				String with the full filename.
		"""
		return self.meta.get('filename')


	@filename.setter
	def filename(self, filename:str) -> None:
		"""	Set the script's filename (to the `filename` meta information).
		
			Args:
				filename: The full filename.
		"""
		self.meta['filename'] = filename


	#########################################################################
	#
	#	Commands
	#


	def doCreate(self, pcontext:PContext, arg:str) -> PContext:
		"""	Execute a CREATE request. The originator must be set before this command.
		
			Example:
				CREATE <target> <resource>

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command.
			
			Returns:
				The scripts "PContext" object, or None in case of an error.
		"""
		return self._handleRequest(pcontext, Operation.CREATE, arg)
	

	def doDelete(self, pcontext:PContext, arg:str) -> PContext:
		"""	Execute a DELETE request. The originator must be set before this command.
		
			Example:
				DELETE <target>

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command, only the target.
			
			Returns:
				The scripts "PContext" object, or None in case of an error.
		"""
		return self._handleRequest(pcontext, Operation.DELETE, arg)


	def doImportRaw(self, pcontext:PContext, arg:str) -> PContext:
		"""	Import a raw resource. Not much verification is is done, and a full resource
			representation, including for example the parent resource ID, must be provided.
		
			Example:
				importRaw <resource>

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command, only the resource, which may start on a new line.
			
			Returns:
				The scripts "PContext" object, or None in case of an error.
		"""
		#  Get and check primitive content
		if (dct := self._getResourceFromScript(pcontext, arg)) is None:
			pcontext.setError(PError.invalid, f'No or invalid content found')
			return None

		resource = Factory.resourceFromDict(dct, create=True, isImported=True).resource

		# Check resource creation
		if not CSE.registration.checkResourceCreation(resource, CSE.cseOriginator):
			return None
		if not (res := CSE.dispatcher.createResource(resource)).resource:
			L.logErr(f'Error during import: {res.dbg}', showStackTrace = False)
			return None
			
		return pcontext


	def doNotify(self, pcontext:PContext, arg:str) -> PContext:
		"""	Execute a NOTIFY request. The originator must be set before this command.
		
			Example:
				NOTIFY <target> <resource>

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command.
			
			Returns:
				The scripts "PContext" object, or None in case of an error.
		"""
		return self._handleRequest(pcontext, Operation.NOTIFY, arg)


	def doOriginator(self, pcontext:PContext, arg:str) -> PContext:
		"""	Set the originator for the following requests.

			Example:
				originator [<name>]
		
			Internally, this sets the variable `request.originator`. The difference is that 
			with this command the originator can be set to an empty value.

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument of the command.
			
			Returns:
				The scripts "PContext" object, or None in case of an error.
		"""
		self.variables['request.originator'] = arg if arg else ''
		return pcontext


	def doPoa(self, pcontext:PContext, arg:str) -> PContext:
		"""	Assign a poa for an identifier.

		Example:
			poa <identifier> <url>
		
		Args:
			pcontext: PContext object of the runnig script.
			arg: remaining argument of the command.
			
		Returns:
			The scripts "PContext" object, or None in case of an error.
		"""
		orig, found, url = arg.partition(' ')
		if found:
			self.poas[orig] = url.strip()
		else:
			pcontext.setError(PError.invalid, f'Missing of invalid argument for POA: {arg}')
			return None
		return pcontext
	

	def doReset(self, pcontext:PContext, arg:str) -> PContext:
		"""	Initiate a CSE reset.

		Example:
			reset
		
		Args:
			pcontext: PContext object of the runnig script.
			arg: remaining argument of the command.
			
		Returns:
			The scripts "PContext" object, or None in case of an error.
		"""

		orig, found, url = arg.partition(' ')
		if found:
			pcontext.setError(PError.invalid, f'RESET command has no arguments')
			return None
		else:
			CSE.resetCSE()
		return pcontext
	

	def doRetrieve(self, pcontext:PContext, arg:str) -> PContext:
		"""	Execute a RETRIEVE request. The originator must be set before this command.
		
			Example:
				RETRIEVE <target>

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command.
			
			Returns:
				The scripts "PContext" object, or None in case of an error.
		"""
		return self._handleRequest(pcontext, Operation.RETRIEVE, arg)
	

	def doRun(self, pcontext:PContext, arg:str) -> PContext:
		"""	Run another script. The 'result' variable will contain the return value
			of the run sript.
		
			Example:
				RUN <script name>

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command, only the name of a script
			
			Returns:
				The scripts "PContext" object, or None in case of an error.

		"""
		name, found, arg = arg.partition(' ')
		if name:
			if len(scripts := CSE.script.findScripts(name = name)) == 0:
				pcontext.setError(PError.undefined, f'No script "{name}" found')
				return None
			else:
				script = scripts[0]
				if not CSE.script.runScript(script, argument = arg, background = False):
					pcontext.setError(script.error[0], f'Running script error: {script.error[2]}')
					return None
				pcontext.result = script.result
				return pcontext
		pcontext.setError(PError.invalid, 'Script name required')
		return None


	def doSetConfig(self, pcontext:PContext, arg:str) -> PContext:
		"""	Set a CSE configuration. The configuration must be an existing configuration. No
			new configurations can e created this way.
		
			Example:
				setConfig <configuration key> <value>

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command, the key and the value
			
			Returns:
				The scripts "PContext" object, or None in case of an error.

		"""
		key, found, value = arg.partition(' ')
		if found:
			if Configuration.has(key):
				# Do some conversions first
				v = Configuration.get(key)
				if isinstance(v, ACMEIntEnum):
					r = Configuration.update(key, v.__class__.to(value, insensitive = True))
				elif isinstance(v, str):
					r = Configuration.update(key, value.strip())
				elif isinstance(v, int):
					r = Configuration.update(key, int(value.strip()))
				elif isinstance(v, float):
					r = Configuration.update(key, float(value.strip()))
				elif isinstance(v, bool):
					r = Configuration.update(key, value.strip().lower() == 'true')
				elif isinstance(v, list):
					r = Configuration.update(key, value.split(','))
				else:
					pcontext.setError(PError.invalid, f'Unsupported type: {type(v)}')
					return None
				
				# Check whether something went wrong while setting the config
				if r:
					pcontext.setError(PError.invalid, r)
					return None

			else:
				pcontext.setError(PError.undefined, f'Undefined configuration: {key}')
				return None
		else:
			pcontext.setError(PError.invalid, f'Syntax error')
			return None
		return pcontext

	
	def doStoragePut(self, pcontext:PContext, arg:str) -> PContext:
		"""	Implementation of the `storagePut` command. Store a value in the persistent storage.

			Args:
				pcontext: Current script context.
				arg: Remaining arguments, key and value
		
			Return:
				Current PContext object, or None in case of an error.
		"""
		key, found, value = arg.partition(' ')
		if not found:
			pcontext.setError(PError.invalid, f'Invalid format for "storagePut" command: {arg}')
			return None
		CSE.script.storagePut(key, value)
		return pcontext


	def doStorageRemove(self, pcontext:PContext, arg:str) -> PContext:
		"""	Implementation of the `storageRemove` command. Remove a value from the persistent storage.

			Args:
				pcontext: Current script context.
				arg: Remaining arguments, key.
		
			Return:
				Current PContext object, or None in case of an error.
		"""
		key, found, value = arg.partition(' ')
		if found:
			pcontext.setError(PError.invalid, f'Invalid format for "storageRemove" command: {arg}')
			return None
		CSE.script.storageRemove(key)
		return pcontext


	def doUpdate(self, pcontext:PContext, arg:str) -> PContext:
		"""	Execute an UPDATE request. The originator must be set before this command.
		
			Example:
				UPDATE <target> <resource>

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command.
			
			Returns:
				The scripts "PContext" object, or "None" in case of an error.
		"""
		return self._handleRequest(pcontext, Operation.UPDATE, arg)
	


	#########################################################################
	#
	#	Macros
	#

	def doAttribute(self, pcontext:PContext, arg:str) -> str:
		""" Retrieve an attribute of a resource via its key path . 
		
			Example:
				${attribute <key path> <resource>}

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command.
			
			Returns:
				The value of the resource attribute, or None in case of an error.
		"""
		# extract key path
		key, found, res = arg.strip().partition(' ')	
		if not found:
			pcontext.setError(PError.invalid, f'Invalid format: attribute <key> <resource>')
			return None
		try:
			if (value := Utils.findXPath(json.loads(res), key)) is None:
				pcontext.setError(PError.undefined, f'Key "{key}" not found in resource')
				return None
		except Exception as e:
			pcontext.setError(PError.invalid, f'Error decoding resource: {e}')
			return None
		return value
		

	def doStorageHas(self, pcontext:PContext, arg:str) -> str:
		"""	Implementation of the `storageHas` macro. Test for a key in the persistent storage.

			Args:
				pcontext: Current script context.
				arg: Remaining arguments, key only
		
			Return:
				Boolean result, or None in case of an error.
		"""
		# extract key
		key, found, res = arg.strip().partition(' ')	

		if found:
			pcontext.setError(PError.invalid, f'Invalid format: storageHas <key>')
			return None

		return CSE.script.storageHas(key)


	def doStorageGet(self, pcontext:PContext, arg:str) -> str:
		"""	Implementation of the `storageGet` macro. Retrieve a value from the persistent storage.

			Args:
				pcontext: Current script context.
				arg: Remaining arguments, key only
		
			Return:
				The stored value for the key, or None in case of an error.
		"""
		# extract key
		key, found, res = arg.strip().partition(' ')	

		if found:
			pcontext.setError(PError.invalid, f'Invalid format: storageGet <key>')
			return None

		if (res := CSE.script.storageGet(key)) is None:
			pcontext.setError(PError.invalid, f'Undefined key in storage: {key}')
			return None
		return res


	#########################################################################
	#
	#	Internals
	#

	def  _getResourceFromScript(self, pcontext:PContext, arg:str) -> JSON:
		"""	Return a resource definition (JSON) from a script. The resource definition
			may span multiple lines.

			Args:
				pcontext: PContext object for the script.
				arg: The remaining args

			Returns:
				A resource as JSON object (dict), or None in case of an error.
		"""

		# Get all in one line and resolve macros and variables
		line = pcontext.remainingLinesAsString(prefix = arg)

		# Look for the resource beginnig.
		# Return an error if it doesn't startwith a {
		i = 0
		while i < len(line):
			c = line[i]
			if c.isspace():
				i += 1
				continue
			if c == '{':
				break
			pcontext.setError(PError.invalid, f'Invalid content')
			return None
		
		# Get content
		# Ignore counting brackets [...] for now
		openCurlies = 0
		inQuote = False
		while i < len(line):
			c = line[i]
			i += 1
			if c == '"':	# found a quote
				inQuote = not inQuote
				continue
			# TODO escape quotes
			if inQuote:			# skip everything in a quote
				continue
			if c == '{':	# count opening {
				openCurlies += 1
				continue
			if c == '}':	# count closing }
				openCurlies -= 1
				if openCurlies == 0:	# end search if this is the last closing }
					break
				continue
		
		if inQuote:
			pcontext.setError(PError.invalid, f'Unmatched "')
			return None
		if openCurlies > 0:
			pcontext.setError(PError.invalid, f'Unmatched }}')
			return None

		resultLine = line[:i]
		if (resultLine := checkMacros(pcontext, resultLine)) is None:
			pcontext.state = PState.terminatedWithError
			return None

		pcontext.pc += resultLine.count('\n')
		try:
			return json.loads(resultLine)
		except:
			return None


	def _handleRequest(self, pcontext:PContext, operation:Operation, arg:str) -> PContext:
		"""	Internally handle a request, either via a direct URL or through an originator.
			Return status and resources in the variables `result.status` and 
			`result.resource` respectively.

			Args:
				pcontext: PContext object for the script.
				operation: The operation to perform.
				arg: The remaining args.

			Returns:
				The stored value for the key, or None in case of an error.
		"""
		target, _, content = arg.partition(' ')

		# Get the request originator
		if (originator := self.variables.get('request.originator')) is None:
			pcontext.setError(PError.undefined, f'"originator" is not set')
			return None

		# Prepare request structure
		req = { 'op': operation,
				'fr': originator,
				'to': target, 
				'rvi': CSE.releaseVersion,
				'rqi': Utils.uniqueRI(), 
			}

		# Get the resource for some operations
		dct:JSON = None
		if operation in [ Operation.CREATE, Operation.UPDATE, Operation.NOTIFY ]:
			#  Get and check primitive content
			if (dct := self._getResourceFromScript(pcontext, content)) is None:
				pcontext.setError(PError.invalid, f'No or invalid content found')
				return None
			if (ty := ResourceTypes.fromTPE( list(dct.keys())[0] )) is None: # first is tpe # TODO remove?
				pcontext.setError(PError.invalid, 'Cannot determine resource type')
				return None

			# TODO add defaults when CREATE

			# Add type when CREATE
			if operation == Operation.CREATE:
				req['ty'] = ty

			# Add primitive content when content is available
			req['pc'] = dct

		elif content:	# operation in [ Operation.RETRIEVE, Operation.DELETE ]
			pcontext.setError(PError.invalid, f'{operation.name} request shall have no content')
			return None

		# Prepare request
		request 					= CSERequest()
		request.originalRequest 	= req
		request.pc 					= dct

		if not (res := CSE.request.fillAndValidateCSERequest(request)).status:
			pcontext.setError(PError.invalid, f'Invalid resource: {res.dbg}')
			#L.log(res)
			return None

		# Replase target with POA if available
		if target in self.poas:
			target = self.poas[target]
			request.to = target
		
		# Send request
		if Utils.isURL(target):
			if operation == Operation.RETRIEVE:
				res = CSE.request.sendRetrieveRequest(target, originator)
			if operation == Operation.DELETE:
				res = CSE.request.sendDeleteRequest(target, originator)
			elif operation == Operation.CREATE:
				res = CSE.request.sendCreateRequest(target, originator, ty, data = request.pc)
			elif operation == Operation.UPDATE:
				res = CSE.request.sendUpdateRequest(target, originator, data = request.pc)
			elif operation == Operation.NOTIFY:
				res = CSE.request.sendNotifyRequest(target, originator, data = request.pc)

		else:
			# Request via CSE-ID, either local, or otherwise a transit reqzest. Let the CSE handle it
			res = CSE.request.handleRequest(request)

		# Construct response
		self.variables['response.status'] = str(res.rsc.value)
		try:
			if not res.status:
				self.variables['response.resource'] = res.dbg
			elif res.data:
				self.variables['response.resource'] = json.dumps(res.data) if isinstance(res.data, dict) else str(res.data)
			elif res.resource:
				self.variables['response.resource'] = json.dumps(res.resource.asDict())
			else:
				self.variables['response.resource'] = ''
		except Exception as e:
			pcontext.setError(PError.invalid, f'Invalid resource or data: {res.data if res.data else res.resource}')
			L.logErr(f'Error while decoding result: {str(e)}', exc = e)
			return None
			
		return pcontext


#########################################################################
#
#	Script Manager
#

class ScriptManager(object):

	def __init__(self) -> None:
		self.scripts:Dict[str,ACMEPContext] = {}
		self.storage:Dict[str, str] = {}					# storage for global values

		self.doLogging = True	# TODO configurable
		self.scriptMonitorInterval = 2 # TODO configurale
		self.scriptUpdatesMonitor:BackgroundWorker = None

		# Also do some internal handling
		CSE.event.addHandler(CSE.event.cseStartup, self.cseStarted)			# type: ignore
		CSE.event.addHandler(CSE.event.cseReset, self.restart)				# type: ignore
		CSE.event.addHandler(CSE.event.cseRestarted, self.restartFinished)	# type: ignore
		L.isInfo and L.log('ScriptManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the ScriptManager. Run the "shutdown" script(s) if present.
		
			Return:
				Boolean, always True.
		"""

		# Look for the shutdown script(s) and run them. 
		for each in self.scripts.values():
			if each.isShutdown():
				self.runScript(each)

		# Stop the monitor
		if self.scriptUpdatesMonitor:
			self.scriptUpdatesMonitor.stop()

		L.isInfo and L.log('ScriptManager shut down')
		return True
	

	def cseStarted(self) -> None:
		"""	Callback for the `cseStartup` event.

			Start a background worker to monitor for scripts.
		"""
		# Add a worker to monitor changes in the scripts
		self.scriptUpdatesMonitor = BackgroundWorkerPool.newWorker(self.scriptMonitorInterval, self.checkScriptUpdates, 'scriptUpdatesMonitor').start()


	def restart(self) -> None:
		"""	Callback for the `cseReset` event.
		
			Restart the script manager service.
		"""
		self.scripts.clear()
		self.storage.clear()
		L.isDebug and L.logDebug('ScriptManager restarted')
	

	def restartFinished(self) -> None:
		"""	Callback for the `cseRestarted` event.
		
			Run the restart script(s), if any.
		"""
		# Look for the shutdown script(s) and run them. 
		for each in self.scripts.values():
			if each.isRestart():
				self.runScript(each)


	def checkScriptUpdates(self) -> bool:
		"""	This is the callback for the monitor to look for new, updated or outdated
			scripts. 

			Return:
				Boolean. Usually true to continue with monitoring.
		"""
		for eachName, eachScript in list(self.scripts.items()):
			try:
				if eachScript.fileMtime < os.stat(eachScript.filename).st_mtime:
					L.isDebug and L.logDebug(f'Reloading script: {eachScript.filename}')
					if eachScript.state != PState.running:
						del self.scripts[eachName]
						self.loadScriptFromFile(eachScript.filename)
			except FileNotFoundError as e:
				# Remove deleted scripts from the internal list
				L.isDebug and L.logDebug(f'Removing script {eachScript.filename}')
				del self.scripts[eachName]

		# Read new scripts
		if CSE.importer.resourcePath:
			if self.loadScriptsFromDirectory(CSE.importer.resourcePath) == -1:
				L.isWarn and L.logWarn('Cannot import new scripts')
		return True


	def loadScriptsFromDirectory(self, directory:str) -> int:
		"""	Load all scripts from a directory.

			Args:
				directory: The directory from which to load the scripts.

			Return:
				Number scripts loaded, or -1 in case of an error.
		"""

		def _hasScriptWithFilename(filename:str) -> bool:
			"""	Test whether a script with the filename exists.

				Args:
					filename: The filename to look for.
				
				Return:
					Boolean, indicating whether a script with the filename exists.
			"""
			for each in self.scripts.values():
				if each.filename == filename:
					return True
			return False

		countScripts = 0
		for fn in fnmatch.filter(os.listdir(directory), '*.as'):
			ffn = f'{directory}{os.path.sep}{fn}'
			if _hasScriptWithFilename(ffn):	# Skip existing scripts, ie only new scripts
				continue
			# read the file and add it to the script manager
			L.isDebug and L.logDebug(f'Importing script: {ffn}')
			if not self.loadScriptFromFile(ffn):
				return -1
			countScripts += 1

		return countScripts


	def loadScriptFromFile(self, filename:str) -> ACMEPContext:
		"""	Load and store a script from a file. 

			Args:
				filename: The filename of the file.

			Return:
				ACMEPContext object with the script, or None.
		"""
		with open(filename) as file:
			return CSE.script.loadScript(file.read(), filename)


	def loadScript(self, script:str, filename:str) -> ACMEPContext:
		"""	Load and initialize a script. If no name is set in the script itself, then the filename's stem
			is set as the name.

			Args:
				script: The script as a single string.
				filename: The filename of the file.
			
			Return:
				ACMEPContext object with the script, or None.
		"""
		p = ACMEPContext(script, filename = filename)
		if p.state != PState.ready:
			L.isWarn and L.logWarn(f'Error importing script: {p.errorMessage}')
			return None
		
		# Add to scripts
		if not (name := p.scriptName):		# Add name to meta data if not set
			p.scriptName = Path(filename).stem
			name = p.scriptName
		if not p.filename:							# Add filename to meta data
			p.filename = filename
		self.scripts[name] = p
		return p
	

	def findScripts(self, name:str = None, meta:Union[str, list[str]] = None) -> list[PContext]:
		""" Find scripts by a filter: `name` is the name of the script. `meta` filters the meta data. 
			Filters are and-combined.

			Args:
				name: Filter by script name. The name can be a simple match.
				meta: Filter by script meta data. This can be a single string or a list of strings.
			
			Return:
				List of PContext objects with the script(s), sorted by name, or None in case of an error.
		"""

		result:list[PContext] = []

		# Find all the scripts by with simple match
		if name:
			result = [ script for script in self.scripts.values() if (n := script.scriptName) is not None and TextTools.simpleMatch(n, name) ]
		else:
			result = list(self.scripts.values())

		# filter the results by meta tags
		if meta:
			meta = [ meta ]	if isinstance(meta, str) else meta
			_result:list[PContext] = []
			for s in result:
				if all([ m in s.meta for m in meta ]):	# Test whether all entries in meta are also in the script.meta
					_result.append(s)
			result = _result

		result.sort(key = lambda p: p.scriptName)
		return result


	def runScript(self, pcontext:PContext, argument:str = '', background:bool = False) -> bool:
		""" Run a script.

			Args:
				pcontext: The script to run.
				argument: An optional argument to the script. This is available to the script via the `argv` macro.
				background: Boolean to indicate whether to run the script in the backhround (as an Actor).
			
			Return:
				Boolean that indicates the successful running of the script. A background script always returns True.
		"""
		def runCB(argument:str) -> None:
			pcontext.run(doLogging = self.doLogging, argument = argument)

		if pcontext.state == PState.running:
			pcontext.setError(PError.invalid, f'Script "{pcontext.name}" is already running')
			return False
		if background:
			BackgroundWorkerPool.newActor(runCB, name = f'AS:{pcontext.scriptName}-{Utils.uniqueID()}').start(argument = argument)
			return True	# Always return True when running in Background

		return pcontext.run(doLogging = self.doLogging, argument = argument).state != PState.terminatedWithError
	

	def run(self, scriptName:str, argument:str = '', metaFilter:list[str] = []) -> str:
		""" Run a script by its name (only in the foreground).

			Args:
				scriptName: The name of the script to run..
				argument: An optional argument to the script. This is available to the script via the `argv` macro.
				metaFiler: Extra filter to select a script.
			
			Return:
				The result of the script run, or None in case if an error.
		"""
		L.isDebug and L.logDebug(f'Looking for script: {scriptName}, arguments: {argument}, meta: {metaFilter}')
		if len(scripts := CSE.script.findScripts(name = scriptName, meta = metaFilter)) != 1:
			L.isWarn and L.logWarn(f'Script not found: "{scriptName}"')
			return None
		script = scripts[0]
		if CSE.script.runScript(script, argument = argument, background = False):
			L.isDebug and L.logDebug(f'Script: "{scriptName}"" finished successfully')
			return script.result if script.result else ''
		L.isWarn and L.logWarn(f'Script: "{scriptName}"finished with error: {script.error}')
		return None


	def storageGet(self, key:str) -> str:
		"""	Retrieve a key/value pair from the persistent storage. 
		
			Args:
				key: Key for the value to retrieve.
			
			Return:
				Previously stored value for the key, or None.
		"""
		if key in self.storage:
			return self.storage[key]
		return None


	def storageHas(self, key:str) -> str:
		"""	Test whether a key exists in the persistent storage. 
		
			Args:
				key: Key to check.
			
			Return:
				Boolean result.
		"""
		return str(key in self.storage)


	def storagePut(self, key:str, value:str) -> None:
		"""	Store a key/value pair in the persistent storage. Existing values will be overwritten.
		
			Args:
				key: Key where to store the value.
				value: Value to store.
		"""
		self.storage[key] = value


	def storageRemove(self, key:str) -> None:
		"""	Remove a key/value pair from the persistent storage.
		
			Args:
				key: Key where to store the value.
		"""
		if key in self.storage:
			del self.storage[key]

