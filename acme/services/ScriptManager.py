#
#	ScriptManager.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Managing scripts and batch job executions
#


from __future__ import annotations
from inspect import getargs
from typing import Callable, Dict, Union
from pathlib import Path
import json, os, fnmatch
from ..etc.Types import JSON, ACMEIntEnum, CSERequest, Operation, ResourceTypes
from ..services.Configuration import Configuration
from ..helpers.Interpreter import PContext, checkMacros, PError, PState, PFuncCallable
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..helpers import TextTools
from ..services.Logging import Logging as L
from ..services import CSE
from ..etc import Utils, DateUtils
from ..resources import Factory


# TODO implement defaults
# TODO Change tags (e.g. meta tags to) constants


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
							 			'clear':		self.doClear,
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
										'storageput':	self.doStoragePut,
						 				'storageremove':self.doStorageRemove,
							 			'update':		self.doUpdate,
									}, 
						 macros = 	{ 
							 			'attribute':	self.doAttribute,
										'cseStatus':	self.doCseStatus,
							 			'hasAttribute':	self.doHasAttribute,
										'isIPython':	self.doIsIPython,
										'storageHas':	self.doStorageHas,
										'storageGet':	self.doStorageGet,
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
		self._validate()	# May change the state to indicate an error



	def _validate(self) -> None:
		"""	Check that @prompt is not used together with conflicting events, and other checks.

			If an invalid script is detected then the state is set to `invalid`.
		"""
		events = ['onstartup', 'onrestart', 'onshutdown', 'at']
		if 'prompt' in self.meta:
			if any(key in events for key in self.meta.keys()):
				self.setError(PError.invalid, f'"@prompt" is not allowed together with any of: {events}')
				self.state = PState.invalid


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
		L.console(msg)
	
	
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

	def doClear(self, pcontext:PContext, arg:str) -> PContext:
		"""	Execute a CLEAR command. Clear the console.
		
			Example:
				CREATE

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command.
			
			Returns:
				The scripts "PContext" object, or None in case of an error.
		"""
		L.consoleClear()
		return pcontext


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
				RUN <script name> [<arguments>]

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command, name of a script and arguments
			
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
				# bool must be tested before int! 
				# See https://stackoverflow.com/questions/37888620/comparing-boolean-and-int-using-isinstance/37888668#37888668
				elif isinstance(v, bool):	
					r = Configuration.update(key, value.strip().lower() == 'true')
				elif isinstance(v, int):
					r = Configuration.update(key, int(value.strip()))
				elif isinstance(v, float):
					r = Configuration.update(key, float(value.strip()))
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
		""" Retrieve an attribute of a resource via its key path. 
		
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


	def doCseStatus(self, pcontext:PContext, arg:str) -> str:
		""" Retrieve the CSE status . 
		
			Example:
				${cseStatus}
			
			Returns:
				The CSE status as a string, or None in case of an error.
		"""
		return str(CSE.cseStatus)


	def doHasAttribute(self, pcontext:PContext, arg:str) -> str:
		""" Check whether an attribute exists for the given its key path . 
		
			Example:
				${hasAttribute <key path> <resource>}

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command.
			
			Returns:
				True or False, depending whether the `key path` exists in the `resource`.
		"""
		# extract key path
		key, found, res = arg.strip().partition(' ')	
		if not found:
			pcontext.setError(PError.invalid, f'Invalid format: hasAttribute <key> <resource>')
			return None
		try:
			if Utils.findXPath(json.loads(res), key) is None:
				return 'false'
		except Exception as e:
			pcontext.setError(PError.invalid, f'Error decoding resource: {e}')
			return None
		return 'true'


	def doIsIPython(self, pcontext:PContext, arg:str) -> str:
		"""	Check whether the CSE currently runs in an IPython environment,
			such as Jupyter Notebooks.
		
			Example:
				${isIPython}

			Args:
				pcontext: PContext object of the runnig script.
				arg: remaining argument(s) of the command. Shall be none.
			
			Returns:
				True or False, depending whether the current environment in IPython.
		"""
		if arg:
			pcontext.setError(PError.invalid, f'Invalid format: isIPython')
			return None
		return str(Utils.runsInIPython()).lower()
		

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

			# TODO add defaults when CREATE

			# Add type when CREATE
			if operation == Operation.CREATE:
				if (ty := ResourceTypes.fromTPE( list(dct.keys())[0] )) is None: # first is tpe
					pcontext.setError(PError.invalid, 'Cannot determine resource type')
					return None
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
		self.scripts:Dict[str,ACMEPContext] = {}			# The managed scripts
		self.storage:Dict[str, str] = {}					# storage for global values

		self.verbose = Configuration.get('cse.scripting.verbose')
		self.scriptMonitorInterval = Configuration.get('cse.scripting.fileMonitoringInterval')
		self.scriptUpdatesMonitor:BackgroundWorker = None
		self.scriptCronWorker:BackgroundWorker = None

		# Also do some internal handling
		CSE.event.addHandler(CSE.event.cseStartup, self.cseStarted)			# type: ignore
		CSE.event.addHandler(CSE.event.cseReset, self.restart)				# type: ignore
		CSE.event.addHandler(CSE.event.cseRestarted, self.restartFinished)	# type: ignore
		CSE.event.addHandler(CSE.event.keyboard, self.onKeyboard)			# type: ignore

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)		# type: ignore

		L.isInfo and L.log('ScriptManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the ScriptManager. Run the "shutdown" script(s) if present.
		
			Return:
				Boolean, always True.
		"""

		# Look for the shutdown script(s) and run them. 
		self.runEventScripts('onshutdown')

		# Stop the monitors
		if self.scriptUpdatesMonitor:
			self.scriptUpdatesMonitor.stop()
		if self.scriptCronWorker:
			self.scriptCronWorker.stop()

		L.isInfo and L.log('ScriptManager shut down')
		return True
	

	def configUpdate(self, key:str = None, value:Any = None) -> None:
		"""	Callback for the `configUpdate` event.
			
			Args:
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'cse.scripting.verbose', 'cse.scripting.fileMonitoringInterval']:
			return
		# assign new values
		self.verbose = Configuration.get('cse.scripting.verbose')
		self.scriptMonitorInterval = Configuration.get('cse.scripting.fileMonitoringInterval')

		# restart or stop monitor worker
		if self.scriptUpdatesMonitor:
			if self.scriptMonitorInterval > 0.0:
				self.scriptUpdatesMonitor.restart(interval = self.scriptMonitorInterval)
			else:
				self.scriptUpdatesMonitor.stop()


	##########################################################################
	#
	#	Event handlers
	#

	def cseStarted(self) -> None:
		"""	Callback for the `cseStartup` event.

			Start a background worker to monitor for scripts.
		"""
		# Add a worker to monitor changes in the scripts
		self.scriptUpdatesMonitor = BackgroundWorkerPool.newWorker(self.scriptMonitorInterval, self.checkScriptUpdates, 'scriptUpdatesMonitor')
		if self.scriptMonitorInterval > 0.0:
			self.scriptUpdatesMonitor.start()

		# Add a worker to check scheduled script, fixed every minute
		self.scriptCronWorker = BackgroundWorkerPool.newWorker(60.0, self.cronMonitor, 'scriptCronMonitor').start()

		# Look for the startup script(s) and run them. 
		self.runEventScripts('onstartup')


	def restart(self) -> None:
		"""	Callback for the `cseReset` event.
		
			Restart the script manager service, ie. clear the scripts and storage. 
			They are reloaded during import.
		"""
		self.scripts.clear()
		self.storage.clear()
		L.isDebug and L.logDebug('ScriptManager restarted')
	

	def restartFinished(self) -> None:
		"""	Callback for the `cseRestarted` event.
		
			Run the restart script(s), if any.
		"""
		# Look for the shutdown script(s) and run them. 
		self.runEventScripts('onrestart')


	def onKeyboard(self, ch:str) -> None:
		"""	Callback for the `keyboard` event.
		
			Run script(s) with configured meta tags, if any.
		"""
		# Look for the shutdown script(s) and run them. 
		self.runEventScripts('onkey', ch)


	##########################################################################
	#
	#	Monitor handlers
	#

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


	def cronMonitor(self) -> bool:
		"""	This is the callback for the cron scheduler. It looks for scripts with an @at meta tag
			and takes the argument as a cron pattern. Scripts that are scheduled to run now will
			be run, one after the other.
			
			Return:
				Boolean. Usually true to continue with monitoring.
		"""
		L.isDebug and L.logDebug(f'Looking for scheduled scripts')
		for each in self.findScripts(meta = 'at'):
			try:
				if DateUtils.cronMatchesTimestamp(at := each.meta.get('at')):
					L.isDebug and L.logDebug(f'Running script: {each.scriptName} at: {at}')
					self.runScript(each)
			except ValueError as e:
				L.logErr(f'Error in script: {each.scriptName} - {str(e)}')
		return True

	##########################################################################


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
		pcontext = ACMEPContext(script, filename = filename)
		if pcontext.state != PState.ready:
			L.isWarn and L.logWarn(f'Error loading script: {pcontext.errorMessage}')
			return None

		# Add to scripts
		if not (name := pcontext.scriptName):		# Add name to meta data if not set
			pcontext.scriptName = Path(filename).stem
			name = pcontext.scriptName
		if not pcontext.filename:							# Add filename to meta data
			pcontext.filename = filename
		self.scripts[name] = pcontext
		return pcontext
	

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

		result.sort(key = lambda p: p.scriptName.lower())
		return result


	def runScript(self, pcontext:PContext, argument:str = '', background:bool = False, finished:Callable = None) -> bool:
		""" Run a script.

			Args:
				pcontext: The script to run.
				argument: An optional argument to the script. This is available to the script via the `argv` macro.
				background: Boolean to indicate whether to run the script in the backhround (as an Actor).
			
			Return:
				Boolean that indicates the successful running of the script. A background script always returns True.
		"""
		def runCB(pcontext:PContext, argument:str) -> None:
			pcontext.run(verbose = self.verbose, argument = argument)

		if pcontext.state == PState.running:
			L.isWarn and L.logWarn(f'Script "{pcontext.name}" is already running')
			# pcontext.setError(PError.invalid, f'Script "{pcontext.name}" is already running')
			return False
		if background:
			BackgroundWorkerPool.newActor(runCB, name = f'AS:{pcontext.scriptName}-{Utils.uniqueID()}', finished = finished).start(pcontext = pcontext, argument = argument)
			return True	# Always return True when running in Background
		
		return pcontext.run(verbose = self.verbose, argument = argument).state != PState.terminatedWithError
	

	def run(self, scriptName:str, argument:str = '', metaFilter:list[str] = []) -> str:
		""" Run a script by its name (only in the foreground).

			Args:
				scriptName: The name of the script to run..
				argument: An optional argument to the script. This is available to the script via the `argv` macro.
				metaFiler: Extra filter to select a script.
			
			Return:
				The result of the script run, or None in case if an error.
		"""
		L.isDebug and L.logDebug(f'Looking for script: {scriptName}, arguments: {argument if argument else "None"}, meta: {metaFilter}')
		if len(scripts := CSE.script.findScripts(name = scriptName, meta = metaFilter)) != 1:
			L.isWarn and L.logWarn(f'Script not found: "{scriptName}"')
			return None
		script = scripts[0]
		if CSE.script.runScript(script, argument = argument, background = False):
			L.isDebug and L.logDebug(f'Script: "{scriptName}"" finished successfully')
			return script.result if script.result else ''
		L.isWarn and L.logWarn(f'Script: "{scriptName}"finished with error: {script.error}')
		return None


	##########################################################################
	#
	#	Storage handlers
	#

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


	##########################################################################
	#
	#	Misc
	#

	def runEventScripts(self, event:str, argument:str = None) -> None:
		"""	Get and run all the scripts for specific events. If the `argument` is given
			then the event's parameter must match the argument.

			This method is still called in the same thread as the console (the event is raised not in
			the background!), because otherwise the prompt input and the getch() function from the
			console are mixing up.

			Args:
				event: The event for which the script(s) are run.
				argument: The optional argument that needs to match the event's pararmater in the script.
		"""

		def getPrompt(r:str) -> str:
			if (p := each.meta.get('prompt')) is not None:
				L.off()
				if (r := L.consolePrompt(p, nl = False)) is None:
					# Normally we would provide an empty string as default, but
					# this would add the ugly empty "()". So, we assign an empty
					# string afterwards.
					r = ''
				L.on()
			return r

		for each in self.findScripts(meta = event):
			if argument:
				if (v := each.meta.get(event)) and v == argument:
					self.runScript(each, argument = getPrompt(argument), background = True)
			else:
				self.runScript(each, argument = getPrompt(''), background = True)
