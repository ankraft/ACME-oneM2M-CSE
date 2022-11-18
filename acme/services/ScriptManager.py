#
#	ScriptManager.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Managing scripts and batch job executions.
"""


from __future__ import annotations
from typing import Callable, Dict, Union, Any, Tuple, cast, Optional

from pathlib import Path
import json, os, fnmatch, re, base64, urllib.parse
import requests

from ..helpers.KeyHandler import FunctionKey
from ..etc.Types import JSON, ACMEIntEnum, CSERequest, Operation, ResourceTypes
from ..services.Configuration import Configuration
from ..helpers.Interpreter import PContext, checkMacros, PError, PState, PFuncCallable
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..helpers import TextTools
from ..services import CSE
from ..etc import Utils, DateUtils
from ..resources import Factory
from ..services.Logging import Logging as L, LogLevel


# TODO implement request sdefaults


#
#	Meta Tags
#

_metaOnStartup = 'onstartup'
_metaOnRestart = 'onrestart'
_metaOnShutdown = 'onshutdown'
_metaPrompt = 'prompt'
_metaTimeout = 'timeout'
_metaFilename = 'filename'
_metaAt = 'at'
_metaOnNotification = 'onnotification'
_metaOnKey = 'onkey'
_metaPromptlessEvents = [ _metaOnStartup, _metaOnRestart, _metaOnShutdown, _metaAt, _metaOnNotification ]


class ACMEPContext(PContext):
	"""	Child class of the `PContext` context class that adds further commands and details.

		Attributes:
			poas: A dictionary that maps between CSE-ID's and Point-of-Access. The default is the own CSE.
			filename: Script filename.
			fileMtime: The script file's latest modified timestamp.
			maxRuntime: The maximum runtime (in seconds) for a script.
			requestParameters: Dictionary with additional request parameters.

	"""

	def __init__(self, 
				 script:Union[str, list[str]], 
				 preFunc:Optional[PFuncCallable] = None,
				 postFunc:Optional[PFuncCallable] = None, 
				 errorFunc:Optional[PFuncCallable] = None,
				 filename:Optional[str] = None) -> None:
		"""	Initializer for the context class.

			Args:
				script: A script contained in a string or a list of strings.
				preFunc: An optional callback that is called with the `PContext` object just before the script is executed. Returning *None* prevents the script execution.
				postFunc: An optional callback that is called with the `PContext` object just after the script finished execution.
				errorFunc: An optional callback that is called with the `PContext` object when encountering an error during script execution.
				filename: The script's filename.

		"""

		super().__init__(script, 

						# !!! Always use lower case when adding new macros and commands below
						 commands = {	
							 			'clear':				self.doClear,
							 			'create':				self.doCreate,
							 			'delete':				self.doDelete,
										'http':					self.doHttp,
										'importraw':			self.doImportRaw,
										'logdivider':			self.doLogDivider,
							 			'notify':				self.doNotify,
						 				'originator':			self.doOriginator,
										'printjson':			self.doPrintJSON,
						 				'poa':					self.doPoa,
										'reset':				self.doReset,
							 			'retrieve':				self.doRetrieve,
										'requestattributes':	self.doRequestAttributes,
										'run':					self.doRun,
										'setconfig':			self.doSetConfig,
										'setlogging':			self.doSetLogging,
										'storageput':			self.doStoragePut,
						 				'storageremove':		self.doStorageRemove,
							 			'update':				self.doUpdate,
									}, 
						 macros = 	{ 	# !!! macro names must be lower case

							 			'attribute':			self.doAttribute,
										'b64encode':			self.doB64Encode,
										'csestatus':			self.doCseStatus,
							 			'hasattribute':			self.doHasAttribute,
										'isipython':			self.doIsIPython,
										'jsonify':				self.doJsonify,
										'storagehas':			self.doStorageHas,
										'storageget':			self.doStorageGet,
										'urlencode':			self.doURLEncode,
						 				'__default__':			lambda c, a, l: Configuration.get(a),
						  			},
						 logFunc = self.log, 
						 logErrorFunc = self.logError,
						 printFunc = self.prnt,
						 preFunc = preFunc, 
						 postFunc = postFunc, 
						 matchFunc = lambda p, l, r : TextTools.simpleMatch(l, r),
						 errorFunc = errorFunc)

		self.poas:Dict[str, str] = { CSE.cseCsi: None }		# Default: Own CSE
		self.filename = filename
		self.fileMtime = os.stat(filename).st_mtime

		self._validate()	# May change the state to indicate an error
		self.requestParameters:dict[str, Any] = {}


	def _validate(self) -> None:
		"""	Validate the script

			If an invalid script is detected then the state is set to *invalid*.
		"""
		# Check that @prompt is not used together with conflicting events, and other checks.
		if _metaPrompt in self.meta:
			if any(key in _metaPromptlessEvents for key in self.meta.keys()):
				self.setError(PError.invalid, f'"@prompt" is not allowed together with any of: {_metaPromptlessEvents}')
				self.state = PState.terminatedWithError
		if _metaTimeout in self.meta:
			t = self.meta[_metaTimeout]
			try:
				self.maxRuntime = float(t)
			except ValueError as e:
				self.setError(PError.invalid, f'"@timeout" has an invalid value; it must be a float: {t}')
				self.state = PState.terminatedWithError
	

	def reset(self) -> None:
		# Additional things to reset
		self.requestParameters = {}
		return super().reset()


	def log(self, pcontext:PContext, msg:str) -> None:
		"""	Callback for normal log messages.

			Args:
				pcontext: Script context. Not used.
				msg: log message.
		"""
		L.isDebug and L.logDebug(msg)


	def logError(self, pcontext:PContext, msg:str, exception:Optional[Exception] = None) -> None:
		"""	Callback for error log messages.

			Args:
				pcontext: Script context. Not used.
				msg: The log message.
				exception: Optional exception to log.
		"""
		L.logErr(msg, exc = exception)


	def prnt(self, pcontext:PContext, msg:str) -> None:
		"""	Callback for *print* command messages.

			Args:
				pcontext: Script context. Not used.
				msg: The log message.
		"""
		if CSE.isHeadless:
			return
		for line in msg.split('\n'):	# handle newlines in the msg
			L.console(line, nl = not len(line))
	
	
	@property
	def errorMessage(self) -> str:
		"""	Format and return an error message.
		
			Return:
				String with the error message.
		"""
		return f'{self.error.error.name} error in {self.filename}:{self.error.line} - {self.error.message}'


	@property
	def filename(self) -> str:
		"""	Return the script's filename (from the *filename* meta information).
		
			Return:
				String with the full filename.
		"""
		return self.meta.get(_metaFilename)


	@filename.setter
	def filename(self, filename:str) -> None:
		"""	Set the script's filename (to the *filename* meta information).
		
			Args:
				filename: The full filename.
		"""
		self.meta[_metaFilename] = filename


	#########################################################################
	#
	#	Commands
	#

	def doClear(self, pcontext:PContext, arg:str) -> PContext:
		"""	Execute a CLEAR command. Clear the console.
		
			Example:
				CREATE

			Args:
				pcontext: PContext object of the running script.
				arg: remaining argument(s) of the command. Not used.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		if CSE.isHeadless:
			return pcontext
		L.consoleClear()
		return pcontext


	def doCreate(self, pcontext:PContext, arg:str) -> PContext:
		"""	Execute a CREATE request. The originator must be set before this command.
		
			Example:
				CREATE <target> <resource>

			Args:
				pcontext: `PContext` object of the running script.
				arg: remaining argument(s) of the command.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		return self._handleRequest(cast(ACMEPContext, pcontext), Operation.CREATE, arg)
	

	def doDelete(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Execute a DELETE request. The originator must be set before this command.
		
			Example:
				DELETE <target>

			Args:
				pcontext: PContext object of the running script.
				arg: remaining argument(s) of the command, only the target.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		return self._handleRequest(cast(ACMEPContext, pcontext), Operation.DELETE, arg)


	_httpMethods = {
		'get':		requests.get,
		'post':		requests.post,
		'put':		requests.put,
		'delete':	requests.delete,
		'patch':	requests.patch,
	}
	"""	Internal mapping between http methods and function callbacks.
	"""


	def doHttp(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		""" Making a http(s) request.
				
			Example:
				http post https://example.com
				aHeader: a header value
				anotherHeader: another header value

				body content
				endhttp

			Args:
				pcontext: `PContext` object of the running script.
				arg: remaining argument(s) of the command, only the target.
			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		# clear all response variables first
		for k, _ in pcontext.getVariables('response\\.*'):
			pcontext.delVariable(k)

		# Parse first command line
		op, _, url = arg.partition(' ')

		if not op:
			pcontext.setError(PError.invalid, 'Missing http method')
			return None
		if not url:
			pcontext.setError(PError.invalid, 'Missing URL')
			return None

		# Check command -> method
		if (method := self._httpMethods.get(op.lower())) is None:
			pcontext.setError(PError.invalid, f'Unsupported http method: {op}')
			return None

		# Get headers & body
		headers:dict[str, str] = {}
		lines = re.split('\n', self.remainingLinesAsString(upto = 'endhttp')) # NO macros are evaluated
		lenLines = len(lines)
		pcontext.pc += lenLines + 1 # increment pc, skip over endhttp

		# parse & construct headers
		idx = 0
		while idx < lenLines and len(l := lines[idx].strip()):
			if (l := checkMacros(pcontext, l)) is None:	# evaluate the macros here
				pcontext.state = PState.terminatedWithError
				return None
			key, found, value = l.partition(':')
			if not found:
				pcontext.setError(PError.invalid, f'Invalid header: {l}')
				return None
			headers[key] = value.strip()
			idx += 1
		
		# construct body
		bodyLines:list[str] = []
		for line in lines[idx+1:]:
			if (l := checkMacros(pcontext, line)) is None:	# evaluate the macros here
				pcontext.state = PState.terminatedWithError
				return None
			bodyLines.append(l)
		body = '\n'.join(bodyLines)
		if len(body):
			headers['Content-Length'] = str(len(body))

		# send http request
		try:
			response = method(url, 
							  data = body,
							  headers = headers, 
							  verify = CSE.security.verifyCertificateHttp,
							  timeout = CSE.httpServer.requestTimeout)		# type: ignore[operator, call-arg]
		except requests.exceptions.ConnectionError:
			pcontext.setVariable('response.status', '-1')
			return pcontext
		
		# parse response and assign to variables
		pcontext.setVariable('response.status', str(response.status_code))
		if response.text: # fill body variable
			pcontext.setVariable('response.body', response.text)
		if response.headers: # fill header variables
			for k, v in response.headers.items():
				pcontext.setVariable(f'response.{k}', v)
		
		return pcontext


	def doImportRaw(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Import a raw resource. Not much verification is done, and a full resource
			representation, including for example the parent resource ID, must be provided.
		
			Example:
				importRaw <resource>

			Args:
				pcontext: `PContext` object of the running script.
				arg: remaining argument(s) of the command, only the resource, which may start on a new line.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		#  Get and check primitive content
		if (dct := self._getResourceFromScript(pcontext, arg)) is None:
			pcontext.setError(PError.invalid, f'No or invalid content found')
			return None

		resource = Factory.resourceFromDict(dct, create = True, isImported=True).resource

		# Get the originator for the request
		if (originator := self.getVariable('request.originator')) is None:
			originator = CSE.cseOriginator

		# Check resource creation
		if not CSE.registration.checkResourceCreation(resource, originator):
			return None

		# Get a potential parent resource
		parentResource:Any = None
		if resource.pi:
			if not (pres := CSE.dispatcher.retrieveLocalResource(ri = resource.pi)).status:
				return None
			parentResource = pres.resource

		# Create the resource
		if not (res := CSE.dispatcher.createLocalResource(resource, parentResource = parentResource, originator = originator)).resource:
			L.logErr(f'Error during import: {res.dbg}', showStackTrace = False)
			return None
			
		return pcontext


	def doLogDivider(self, pcontext:PContext, arg:Optional[str] = '') -> Optional[PContext]:
		"""	Print a divider line to the log (on DEBUG level).
			
			Optionally add a message that is centered on the line.
			
			Example:
				LOGDIVIDER a message

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
			"""
		L.logDivider(LogLevel.DEBUG, arg)
		return pcontext


	def doNotify(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Execute a NOTIFY request. The originator must be set before this command.
		
			Example:
				NOTIFY <target> <resource>

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command.
			
			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		return self._handleRequest(cast(ACMEPContext, pcontext), Operation.NOTIFY, arg)


	def doOriginator(self, pcontext:PContext, arg:str) -> PContext:
		"""	Set the originator for the following requests.

			Example:
				originator [<name>]
		
			Internally, this sets the variable *request.originator* in the `PContext` object. The
			difference is that with this command the originator can be set to an empty value.

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument of the command.

			Returns:
				The script's `PContext` object.
		"""
		self.setVariable('request.originator', arg if arg else '')
		return pcontext


	def doPoa(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Assign a "poa" for an identifier.

			Example:
				poa <identifier> <uri>

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument of the command.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		orig, found, url = arg.partition(' ')
		if found:
			self.poas[orig] = url.strip()
		else:
			pcontext.setError(PError.invalid, f'Missing of invalid argument for POA: {arg}')
			return None
		return pcontext


	def doPrintJSON(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Print a beautified JSON to the console.
			
			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument of the command, the JSON structure.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		 """
		if CSE.isHeadless:
			return pcontext
		try:
			L.console(json.loads(arg))
		except Exception as e:
			pcontext.setError(PError.invalid, str(e))
			return None
		return pcontext


	def doRequestAttributes(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Add extra request attributes to a request. The argument to this
			command is a JSON structure with the attributes.
			
			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument of the command, the JSON structure.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		if (dct := self._getResourceFromScript(pcontext, arg)) is None:
			pcontext.setError(PError.invalid, f'No or invalid content found {pcontext.error.message}')
			return None
		cast(ACMEPContext, pcontext).requestParameters = dct
		return pcontext


	def doReset(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Initiate a CSE reset.

			Example:
				RESET

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument of the command.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""

		_, found, _ = arg.partition(' ')
		if found:
			pcontext.setError(PError.invalid, f'RESET command has no arguments')
			return None
		else:
			CSE.resetCSE()
		return pcontext
	

	def doRetrieve(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Execute a RETRIEVE request. The originator must be set before this command.
		
			Example:
				RETRIEVE <target>

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		return self._handleRequest(cast(ACMEPContext, pcontext), Operation.RETRIEVE, arg)
	

	def doRun(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Run another script. The *result* variable will contain the return value
			of the run sript.
		
			Example:
				RUN <script name> [<arguments>]

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command, name of a script and arguments.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		name, found, arg = arg.partition(' ')
		if name:
			if len(scripts := CSE.script.findScripts(name = name)) == 0:
				pcontext.setError(PError.undefined, f'No script "{name}" found')
				return None
			else:
				script = scripts[0]
				if not CSE.script.runScript(script, argument = arg, background = False):
					pcontext.setError(script.error.error, f'Running script error: {script.error.message}')
					return None
				pcontext.result = script.result
				return pcontext
		pcontext.setError(PError.invalid, 'Script name required')
		return None


	def doSetConfig(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Set a CSE configuration. The configuration must be an existing configuration. No
			new configurations can e created this way.
		
			Example:
				setConfig <configuration key> <value>

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command, the key and the value.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
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


	def doSetLogging(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Implementation of the *setLoggin* command. Enable/disable the console logging.

			Args:
				pcontext: Current script context.
				arg: Remaining arguments, key and value.

			Return:
				Current `PContext` object, or *None* in case of an error.
		"""
		if arg and (a := arg.lower()) in [ 'on', 'off' ]:
			L.enableScreenLogging = a == 'on'
		else:
			pcontext.setError(PError.invalid, f'Syntax error. Argument "on" or "off" missing')
			return None
		return pcontext

	
	def doStoragePut(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Implementation of the *storagePut* command. Store a value in the persistent storage.

			Args:
				pcontext: Current script context.
				arg: Remaining arguments, key and value.

			Return:
				Current `PContext` object, or *None* in case of an error.
		"""
		key, found, value = arg.partition(' ')
		if not found:
			pcontext.setError(PError.invalid, f'Invalid format for "storagePut" command: {arg}')
			return None
		CSE.script.storagePut(key, value)
		return pcontext


	def doStorageRemove(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Implementation of the *storageRemove* command. Remove a value from the persistent storage.

			Args:
				pcontext: Current script context.
				arg: Remaining arguments, key.

			Return:
				Current `PContext` object, or *None* in case of an error.
		"""
		key, found, value = arg.partition(' ')
		if found:
			pcontext.setError(PError.invalid, f'Invalid format for "storageRemove" command: {arg}')
			return None
		CSE.script.storageRemove(key)
		return pcontext


	def doUpdate(self, pcontext:PContext, arg:str) -> Optional[PContext]:
		"""	Execute an UPDATE request. The originator must be set before this command.
		
			Example:
				UPDATE <target> <resource>

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command.

			Returns:
				The script's `PContext` object, or *None* in case of an error.
		"""
		return self._handleRequest(cast(ACMEPContext, pcontext), Operation.UPDATE, arg)
	

	#########################################################################
	#
	#	Macros
	#

	def doAttribute(self, pcontext:PContext, arg:str, line:str) -> Optional[str]:
		""" Retrieve an attribute of a resource via its key path. 
		
			Example:
				[attribute <key path> <resource>]

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command.
				line: The original code line.

			Returns:
				The value of the resource attribute, or *None* in case of an error.
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


	def doB64Encode(self, pcontext:PContext, arg:str, line:str) -> str:
		"""	Base-64 encode a string.

			Example:
				[b64encode <string>]

			Args:
				pcontext: `PContext` object of the running script. Not used.
				arg: Remaining argument(s) of the command.
				line: The original code line.

			Returns:
				Base-64 encoded result.
		"""
		return base64.b64encode(arg.encode('utf-8')).decode('utf-8')


	def doCseStatus(self, pcontext:PContext, arg:str, line:str) -> str:
		""" Retrieve the CSE status.
		
			Example:
				[cseStatus]

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command.
				line: The original code line.

			Returns:
				The CSE status as a string, or *None* in case of an error.
		"""
		return str(CSE.cseStatus)


	def doHasAttribute(self, pcontext:PContext, arg:str, line:str) -> Optional[str]:
		""" Check whether an attribute exists for the given its key path . 
		
			Example:
				[hasAttribute <key path> <resource>]

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command.
				line: The original code line.

			Returns:
				*True* or *False*, depending whether the *key path* exists in the *resource*.
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


	def doIsIPython(self, pcontext:PContext, arg:str, line:str) -> Optional[str]:
		"""	Check whether the CSE currently runs in an IPython environment,
			such as Jupyter Notebooks.
		
			Example:
				[isIPython]

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command. Shall be none.
				line: The original code line.

			Returns:
				*True* or *False*, depending whether the current environment in IPython.
		"""
		if arg:
			pcontext.setError(PError.invalid, f'Invalid format: isIPython')
			return None
		return str(Utils.runsInIPython()).lower()


	def doJsonify(self, pcontext:PContext, arg:str, line:str) -> str:
		"""	Escape a string for use in a JSON structure. Newlines and quotes are escaped.

			Example:
				[jsonify <string>]

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command.
				line: The original code line.

			Returns:
				Escaped JSON string.
		"""
		return arg.replace('\n', '\\n').replace('"', '\\"')


	def doStorageHas(self, pcontext:PContext, arg:str, line:str) -> Optional[str]:
		"""	Implementation of the *storageHas* macro. Test for a key in the persistent storage.

			Args:
				pcontext: Current script context.
				arg: Remaining arguments, key only.
				line: The original code line.

			Return:
				Boolean result, or *None* in case of an error.
		"""
		# extract key
		key, found, res = arg.strip().partition(' ')	

		if found:
			pcontext.setError(PError.invalid, f'Invalid format: storageHas <key>')
			return None

		return CSE.script.storageHas(key)


	def doStorageGet(self, pcontext:PContext, arg:str, line:str) -> Optional[str]:
		"""	Implementation of the *storageGet* macro. Retrieve a value from the persistent storage.

			Args:
				pcontext: Current script context.
				arg: Remaining arguments, key only.
				line: The original code line.

			Return:
				The stored value for the key, or *None* in case of an error.
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


	def doURLEncode(self, pcontext:PContext, arg:str, line:str) -> str:
		"""	URL-Encode a string.

			Example:
				[urlencode <string>]

			Args:
				pcontext: `PContext` object of the running script.
				arg: Remaining argument(s) of the command.
				line: The original code line.

			Returns:
				URL-encoded string.
		"""
		return urllib.parse.quote_plus(arg)


	#########################################################################
	#
	#	Internals
	#

	def  _getResourceFromScript(self, pcontext:PContext, arg:str) -> Optional[JSON]:
		"""	Return a resource definition (JSON) from a script. The resource definition
			may span multiple lines.

			Args:
				pcontext: `PContext` object for the script.
				arg: The remaining args

			Returns:
				A resource as JSON object (dict), or *None* in case of an error.
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
			#L.isDebug and L.logDebug(resultLine)
			return json.loads(resultLine)
		except Exception as e:
			pcontext.setError(PError.invalid, f'{str(e)}')
			return None


	def _handleRequest(self, pcontext:ACMEPContext, operation:Operation, arg:str) -> Optional[PContext]:
		"""	Internally handle a request, either via a direct URL or through an originator.

			Return status and resources in the variables *result.status* and 
			*result.resource* respectively.

			Args:
				pcontext: `PContext` object for the script.
				operation: The operation to perform.
				arg: The remaining args.

			Returns:
				The stored value for the key, or *None* in case of an error.
		"""
		target, _, content = arg.partition(' ')

		# Get the request originator
		if (originator := self.getVariable('request.originator')) is None:
			originator = Configuration.get('cse.originator')
			# pcontext.setError(PError.undefined, f'"originator" is not set. Set before a request with "originator <id>".')
			# return None

		# Prepare request structure
		req = { 'op': operation,
				'fr': originator,
				'to': target, 
				'rvi': CSE.releaseVersion,
				'rqi': Utils.uniqueRI(), 
			}
		
		# Transform the extra request attributes set by the script
		if pcontext.requestParameters:
			rp = pcontext.requestParameters
			# requestIentifier
			if (rqi := rp.pop('rqi', None)) is not None:
				req['rqi'] = rqi
			# add remaining attributes to the filterCriteria of a request
			for key in list(rp.keys()):
				Utils.setXPath(req, key, rp.pop(key))
			pcontext.requestParameters = None

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
		

		# Replace target with POA if available
		if target in self.poas:
			target = self.poas[target]
			request.to = target
		
		L.isDebug and L.logDebug(f'Sending request from script: {res.request.originalRequest}')
		
		# Send request
		if Utils.isURL(target):
			if operation == Operation.RETRIEVE:
				res = CSE.request.sendRetrieveRequest(target, originator)
			if operation == Operation.DELETE:
				res = CSE.request.sendDeleteRequest(target, originator)
			elif operation == Operation.CREATE:
				res = CSE.request.sendCreateRequest(target, originator, ty, content = request.pc)
			elif operation == Operation.UPDATE:
				res = CSE.request.sendUpdateRequest(target, originator, content = request.pc)
			elif operation == Operation.NOTIFY:
				res = CSE.request.sendNotifyRequest(target, originator, content = request.pc)

		else:
			# Request via CSE-ID, either local, or otherwise a transit reqzest. Let the CSE handle it
			res = CSE.request.handleRequest(request)

		# Construct response
		self.setVariable('response.status', str(res.rsc.value))
		try:
			if not res.status:
				L.isDebug and L.logDebug(f'Request response: {res.dbg}')
				self.setVariable('response.resource', f'{{ "m2m:dbg:": "{str(res.dbg)}"}}')
			elif res.data:
				L.isDebug and L.logDebug(f'Request response: {res.data}')
				self.setVariable('response.resource', json.dumps(res.data) if isinstance(res.data, dict) else str(res.data))
				L.logDebug(self.getVariable('response.resource'))
			elif res.resource:
				L.isDebug and L.logDebug(f'Request response: {res.resource}')
				self.setVariable('response.resource', json.dumps(res.resource) if isinstance(res.resource, dict) else json.dumps(res.resource.asDict()))
			else:
				L.isDebug and L.logDebug(f'Request response: (unknown or none)')
				self.setVariable('response.resource', '')
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
	"""	This manager entity handles script execution in the CSE.

		Attributes:
			scripts: Dictionary of scripts and script `ACMEPContext`.
			storage: Dictionary for internal global variable storage.

			verbose: Verbosity configuration value.
			scriptMonitorInterval: Interval for monitoring scripts files.
			scriptDirectories: List of script directories to monitoe.
			scriptUpdatesMonitor: `BackgroundWorker` worker to monitor script directories.
			scriptCronWorker: `BackgroundWorker` worker to run cron-enabled scripts.
	"""

	def __init__(self) -> None:
		"""	Initializer for the ScriptManager class.
		"""

		self.scripts:Dict[str,ACMEPContext] = {}			# The managed scripts
		self.storage:Dict[str, str] = {}					# storage for global values

		self.scriptUpdatesMonitor:BackgroundWorker = None
		self.scriptCronWorker:BackgroundWorker = None

		self._assignConfig()

		# Also do some internal handling
		CSE.event.addHandler(CSE.event.cseStartup, self.cseStarted)			# type: ignore
		CSE.event.addHandler(CSE.event.cseReset, self.restart)				# type: ignore
		CSE.event.addHandler(CSE.event.cseRestarted, self.restartFinished)	# type: ignore
		CSE.event.addHandler(CSE.event.keyboard, self.onKeyboard)			# type: ignore
		CSE.event.addHandler(CSE.event.acmeNotification, self.onNotification)	# type: ignore

		# Add a handler for configuration changes
		CSE.event.addHandler(CSE.event.configUpdate, self.configUpdate)		# type: ignore

		L.isInfo and L.log('ScriptManager initialized')


	def shutdown(self) -> bool:
		"""	Shutdown the ScriptManager. 
		
			Run the *shutdown* script(s) if present.
		
			Return:
				Boolean, always *True*.
		"""

		# Look for the shutdown script(s) and run them. 
		self.runEventScripts(_metaOnShutdown)

		# Stop the monitors
		if self.scriptUpdatesMonitor:
			self.scriptUpdatesMonitor.stop()
		if self.scriptCronWorker:
			self.scriptCronWorker.stop()

		L.isInfo and L.log('ScriptManager shut down')
		return True
	
	
	def _assignConfig(self) -> None:
		"""	Store relevant configuration values in the manager.
		"""
		self.verbose = Configuration.get('cse.scripting.verbose')
		self.scriptMonitorInterval = Configuration.get('cse.scripting.fileMonitoringInterval')
		self.scriptDirectories = Configuration.get('cse.scripting.scriptDirectories')


	def configUpdate(self, key:Optional[str] = None, value:Optional[Any] = None) -> None:
		"""	Callback for the *configUpdate* event.
			
			Args:
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'cse.scripting.verbose', 
						'cse.scripting.fileMonitoringInterval', 
						'cse.scripting.scriptDirectories']:
			return

		# assign new values
		self._assignConfig()

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
		"""	Callback for the *cseStartup* event.

			Start a background worker to monitor directories for scripts.
		"""
		# Add a worker to monitor changes in the scripts
		self.scriptUpdatesMonitor = BackgroundWorkerPool.newWorker(self.scriptMonitorInterval, self.checkScriptUpdates, 'scriptUpdatesMonitor')
		if self.scriptMonitorInterval > 0.0:
			self.scriptUpdatesMonitor.start()

		# Add a worker to check scheduled script, fixed every minute
		self.scriptCronWorker = BackgroundWorkerPool.newWorker(60.0, self.cronMonitor, 'scriptCronMonitor').start()

		# Look for the startup script(s) and run them. 
		self.runEventScripts(_metaOnStartup)


	def restart(self) -> None:
		"""	Callback for the *cseReset* event.
		
			Restart the script manager service, ie. clear the scripts and storage. 
			They are reloaded during import.
		"""
		self.removeScripts()
		self.storage.clear()
		L.isDebug and L.logDebug('ScriptManager restarted')
	

	def restartFinished(self) -> None:
		"""	Callback for the *cseRestarted* event.
		
			Run the restart script(s), if any.
		"""
		# Look for the shutdown script(s) and run them. 
		self.runEventScripts(_metaOnRestart)


	def onKeyboard(self, ch:str) -> None:
		"""	Callback for the *keyboard* event.
		
			Run script(s) with configured meta tags, if any.

			Args:
				ch: The pressed key.
		"""
		# Check for function key names first
		# Look for the shutdown script(s) and run them. 
		self.runEventScripts(_metaOnKey, 
							 cast(FunctionKey, ch).name if isinstance(ch, FunctionKey) else ch)


	def onNotification(self, uri:str, originator:str, data:JSON) -> None:
		"""	Callback for the *notification* event.

			Run script(s) with configured meta tags, if any.

			Args:
				uri: The target URI.
				originator: The notification's originator.
				data: The notification's payload.
		"""
		try:
			self.runEventScripts( _metaOnNotification,	# !!! Lower case
								  uri,
								  background = False, 
								  environment = { 'notification.resource' : json.dumps(data), 
								  				  'notification.originator' : originator,
												  'notification.uri': uri })	
		except Exception as e:
			L.logErr('Error in JSON', exc = e)



	##########################################################################
	#
	#	Monitor handlers
	#

	def checkScriptUpdates(self) -> bool:
		"""	This is the callback for the monitor to look for new, updated or outdated
			scripts. 

			Return:
				Boolean. Usually *True* to continue with monitoring.
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
		if CSE.importer.resourcePath:	# from the init directory
			if self.loadScriptsFromDirectory(CSE.importer.resourcePath) == -1:
				L.isWarn and L.logWarn('Cannot import new scripts')
		if CSE.script.scriptDirectories:	# from the extra script directories
			if self.loadScriptsFromDirectory(CSE.script.scriptDirectories) == -1:
				L.isWarn and L.logWarn('Cannot import new scripts')
		return True


	def cronMonitor(self) -> bool:
		"""	This is the callback for the cron scheduler.
		
			It looks for scripts with an *@at* meta tag and takes the argument as a cron pattern.
			Scripts that are scheduled to run now will be run, one after the other.
			
			Return:
				Boolean. Usually *True* to continue with monitoring.
		"""
		#L.isDebug and L.logDebug(f'Looking for scheduled scripts')
		for each in self.findScripts(meta = _metaAt):
			try:
				if DateUtils.cronMatchesTimestamp(at := each.meta.get(_metaAt)):
					L.isDebug and L.logDebug(f'Running script: {each.scriptName} at: {at}')
					self.runScript(each)
			except ValueError as e:
				L.logErr(f'Error in script: {each.scriptName} - {str(e)}')
		return True

	##########################################################################


	def loadScriptsFromDirectory(self, directory:str|list[str]) -> int:
		"""	Load all scripts from a (monitored) directory.

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

		# If this is just a single directory then still put into a list		
		if isinstance(directory, str):
			directory = [ directory ]

		countScripts = 0
		# Look into each directory
		for each in directory:
			if not each:	# skip empty directory names
				continue
			for fn in fnmatch.filter(os.listdir(each), '*.as'):
				ffn = f'{each}{os.path.sep}{fn}'
				if _hasScriptWithFilename(ffn):	# Skip existing scripts, ie only new scripts
					continue
				# read the file and add it to the script manager

				L.isDebug and L.logDebug(f'Importing script: {os.path.relpath(ffn)}')
				if not self.loadScriptFromFile(ffn):
					return -1
				countScripts += 1

		return countScripts


	def loadScriptFromFile(self, filename:str) -> ACMEPContext:
		"""	Load and store a script from a file. 

			Args:
				filename: The filename of the file.

			Return:
				`ACMEPContext` object with the script, or *None*.
		"""
		with open(filename) as file:
			return CSE.script.loadScript(file.read(), filename)


	def loadScript(self, script:str, filename:str) -> Optional[ACMEPContext]:
		"""	Load and initialize a script. If no name is set in the script itself, then the 
			filename's stem is set as the name.

			Args:
				script: The script as a single string.
				filename: The filename of the file.

			Return:
				`ACMEPContext` object with the script, or *None*.
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
	

	def removeScripts(self) -> None:
		"""	Remove all scripts.
		"""
		self.scripts.clear()
	

	def findScripts(self, name:Optional[str] = None,
						  meta:Optional[Union[str, list[str]]] = None) -> list[PContext]:
		""" Find scripts by a filter.
		
			Filters are and-combined.

			Args:
				name: Filter by script name. The name can be a simple match.
				meta: Filter by script meta data. This can be a single string or a list of strings.

			Return:
				List of `PContext` objects with the script(s), sorted by name, or `None` in case of an error.
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


	def runScript(self, pcontext:PContext, 
						argument:Optional[str] = '', 
						background:Optional[bool] = False, 
						finished:Optional[Callable] = None,
						environment:Optional[dict[str, str]] = {}) -> bool:
		""" Run a script.

			Args:
				pcontext: The script to run.
				argument: An optional argument to the script. This is available to the script via the *argv* macro.
				background: Boolean to indicate whether to run the script in the backhround (as an Actor).

			Return:
				Boolean that indicates the successful running of the script. A background script always returns *True*.
		"""
		def runCB(pcontext:PContext, argument:str) -> None:
			pcontext.run(verbose = self.verbose, argument = argument)


		if pcontext.state == PState.running:
			L.isWarn and L.logWarn(f'Script "{pcontext.name}" is already running')
			# pcontext.setError(PError.invalid, f'Script "{pcontext.name}" is already running')
			return False
		
		# Set environemt
		pcontext.setEnvironment(environment)

		# Run in background or direct
		if background:
			BackgroundWorkerPool.newActor(runCB, name = f'AS:{pcontext.scriptName}-{Utils.uniqueID()}', finished = finished).start(pcontext = pcontext, argument = argument)
			return True	# Always return True when running in Background
		return pcontext.run(verbose = self.verbose, argument = argument).state != PState.terminatedWithError
	

	def run(self, scriptName:str, 
				  argument:Optional[str] = '',
				  metaFilter:Optional[list[str]] = []) -> Tuple[bool, str]:
		""" Run a script by its name (only in the foreground).

			Args:
				scriptName: The name of the script to run..
				argument: An optional argument to the script. This is available to the script via the *argv* macro.
				metaFilter: Extra filter to select a script.

			Return:
				The result of the script run in a tuple. Boolean indicating success, and an optional result.
		"""
		L.isDebug and L.logDebug(f'Looking for script: {scriptName}, arguments: {argument if argument else "None"}, meta: {metaFilter}')
		if len(scripts := CSE.script.findScripts(name = scriptName, meta = metaFilter)) != 1:
			L.logWarn(dbg := f'Script not found: "{scriptName}"')
			return (False, dbg)
		script = scripts[0]
		if CSE.script.runScript(script, argument = argument, background = False):
			L.isDebug and L.logDebug(f'Script: "{scriptName}" finished successfully')
			return (True, script.result if script.result else '')
			
		L.isWarn and L.logWarn(f'Script "{scriptName}" finished with error: {script.error.error.name} ({script.error.line}) : {script.error.message}')

		if script.error.error == PError.quitWithError:
			script.result = script.error.message
		return (False, script.result)


	##########################################################################
	#
	#	Storage handlers
	#

	def storageGet(self, key:str) -> Optional[str]:
		"""	Retrieve a key/value pair from the persistent storage. 
		
			Args:
				key: Key for the value to retrieve.

			Return:
				Previously stored value for the key, or *None*.
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

	def runEventScripts(self, event:str, 
							  argument:Optional[str] = None, 
							  background:Optional[bool] = True, 
							  environment:Optional[dict[str, str]] = {}) -> None:
		"""	Get and run all the scripts for specific events. 
		
			If the *argument* is given then the event's parameter must match the argument.

			This method is still called in the same thread as the console (the event is raised not in
			the background!), because otherwise the prompt input and the getch() function from the
			console are mixing up.

			Args:
				event: The event for which the script(s) are run.
				argument: The optional argument that needs to match the event's pararmater in the script.
				background: Run the script in the background
				environment: Extra variables to set in the script's environment
		"""

		def getPrompt(r:str) -> str:
			"""	Prompt the user for input if the @prompt meta tag is set.

				Return:
					The user's input.
			"""
			if (p := each.meta.get('prompt')) is not None:
				L.off()
				if (r := L.consolePrompt(p, nl = False)) is None:
					# Normally we would provide an empty string as default, but
					# this would add the ugly empty "()". So, we assign an empty
					# string afterwards.
					r = ''
				L.on()
			return r

		arg = f'{event}' if argument is None else f'{event} {argument}'
		for each in self.findScripts(meta = event):
			if argument:
				if (v := each.meta.get(event)) and v == argument:
					self.runScript(each, argument = getPrompt(arg), background = background, environment = environment)
			else:
				self.runScript(each, argument = getPrompt(''), background = background, environment = environment)
