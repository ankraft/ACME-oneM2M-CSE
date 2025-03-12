#
#	ScriptManager.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
"""	Managing scripts and batch job executions.
"""

from __future__ import annotations
from typing import Callable, Dict, Union, Any, Tuple, cast, Optional, List

from pathlib import Path
import json, os, fnmatch, traceback
import requests, webbrowser
from decimal import Decimal
from rich.text import Text


from ..helpers.KeyHandler import FunctionKey
from ..etc.Types import JSON, ACMEIntEnum, CSERequest, Operation, ResourceTypes, Result, BasicType, AttributePolicy, LogLevel
from ..etc.ResponseStatusCodes import ResponseException
from ..etc.DateUtils import cronMatchesTimestamp, getResourceDate, utcDatetime
from ..etc.IDUtils import uniqueRI, uniqueID
from ..etc.ACMEUtils import pureResource
from ..etc.Utils import runsInIPython, isURL
from ..etc.Constants import RuntimeConstants as RC
from ..runtime.Configuration import Configuration
from ..helpers.Interpreter import PContext, PFuncCallable, PUndefinedError, PError, PState, SSymbol, SType, PSymbolCallable
from ..helpers.Interpreter import PInvalidArgumentError,PInvalidTypeError, PRuntimeError, PUnsupportedError, PPermissionError
from ..helpers.BackgroundWorker import BackgroundWorker, BackgroundWorkerPool
from ..helpers.TextTools import setXPath, simpleMatch
from ..helpers.TextTools import setXPath
from ..helpers.NetworkTools import pingTCPServer, isValidPort
from ..resources.Factory import resourceFromDict
from ..resources.Resource import Resource
from ..runtime import CSE
from ..runtime.Logging import Logging as L

#
#	Meta Tags
#

_metaInit = 'init'
"""	Name of the meta tag "init". """
_metaOnStartup = 'onStartup'
"""	Name of the meta tag "onStartup". """
_metaOnRestart = 'onRestart'
"""	Name of the meta tag "onRestart". """
_metaOnShutdown = 'onShutdown'
"""	Name of the meta tag "onShutdown". """
_metaPrompt = 'prompt'
""" Name of the meta tag "prompt". """
_metaTimeout = 'timeout'
""" Name of the meta tag "timeout". """
_metaFilename = 'filename'
""" Name of the meta tag "filename". """
_metaAt = 'at'
"""	Name of the meta tag "at". """
_metaOnNotification = 'onNotification'
""" Name of the meta tag "onNotification". """
_metaOnKey = 'onKey'
""" Name of the meta tag "onKey". """
_metaPromptlessEvents = [ _metaInit, _metaOnStartup, _metaOnRestart, _metaOnShutdown, _metaAt, _metaOnNotification ]
""" Events for which the "prompt" meta tag is to be ignored. """

_storageTypes = (SType.tString, SType.tNumber, SType.tBool, SType.tJson, SType.tLambda, SType.tList,
				 SType.tListQuote, SType.tNIL, SType.tSymbol, SType.tSymbolQuote)
""" Allowed types to put into storage. """

_httpMethods = {
	'get':		requests.get,
	'post':		requests.post,
	'put':		requests.put,
	'delete':	requests.delete,
	'patch':	requests.patch,
}
"""	Internal mapping between http methods and function callbacks. """



class ACMEPContext(PContext):
	"""	Child class of the `PContext` context class that adds further functions and details.
	"""

	__slots__ = (
		'scriptFilename',
		'fileMtime',
		'nextScript',
	)
	""" Slots of class attributes. """


	def __init__(self, 
				 script:str, 
				 preFunc:Optional[PFuncCallable] = None,
				 postFunc:Optional[PFuncCallable] = None, 
				 errorFunc:Optional[PFuncCallable] = None,
				 filename:Optional[str] = None,
				 fallbackFunc:PSymbolCallable = None,
				 monitorFunc:PSymbolCallable = None,
				 allowBrackets:bool = False) -> None:
		"""	Initializer for the context class.

			Args:
				script: A script contained in a string or a list of strings.
				preFunc: An optional callback that is called with the `PContext` object just before the script is executed. Returning *None* prevents the script execution.
				postFunc: An optional callback that is called with the `PContext` object just after the script finished execution.
				errorFunc: An optional callback that is called with the `PContext` object when encountering an error during script execution.
				filename: The script's filename.
				allowBrackets: Allow "[" and "]" for opening and closing lists as well.
		"""
		super().__init__(script, 

						# !!! Always use lower case when adding new macros and commands below
						 symbols = {	
							'clear-console':			self.doClearConsole,
							'create-resource':			self.doCreateResource,
							'cse-attribute-infos':		self.doCseAttributeInfos,
							'cse-status':				self.doCseStatus,
							'delete-resource':			self.doDeleteResource,
							'get-config':				self.doGetConfiguration,
							'get-loglevel':				self.doGetLogLevel,
							'get-storage':				self.doGetStorage,
							'has-config':				self.doHasConfiguration,
							'has-storage':				self.doHasStorage,
							'http':						self.doHttp,
							'import-raw':				self.doImportRaw,
							'include-script':			lambda p, a: self.doRunScript(p, a, isInclude = True),
							'log-divider':				self.doLogDivider,
							'open-web-browser':			self.doOpenWebBrowser,
							'ping-tcp-service':			self.doPingTcpService,
							'print-json':				self.doPrintJSON,
							'put-storage':				self.doPutStorage,
							'query-resource':			self.doQueryResource,
							'remove-storage':			self.doRemoveStorage,
							'reset-cse':				self.doReset,
							'retrieve-resource':		self.doRetrieveResource,
							'run-script':				self.doRunScript,
							'runs-in-ipython':			self.doRunsInIPython,
							'runs-in-tui':				self.doRunsInTUI,
							'send-notification':		self.doNotify,
							'set-category-description':	self.doSetCategoryDescription,
							'set-config':				self.doSetConfig,
							'set-console-logging':		self.doSetLogging,
							'schedule-next-script':		self.doScheduleNextScript,
							'tui-notify':				self.doTuiNotify,
							'tui-refresh-resources':	self.doTuiRefreshResources,
							'tui-visual-bell':			self.doTuiVisualBell,
							'update-resource':			self.doUpdateResource,
						},
						 logFunc = self.log, 
						 logErrorFunc = self.logError,
						 printFunc = self.prnt,
						 preFunc = preFunc, 
						 postFunc = postFunc, 
						 matchFunc = lambda p, l, r : simpleMatch(l, r),
						 errorFunc = errorFunc,
						 fallbackFunc = fallbackFunc,
						 monitorFunc = monitorFunc,
						 allowBrackets = allowBrackets,
						 verbose = Configuration.scripting_verbose
					)

		self.scriptFilename = filename if filename else None
		""" The script filename. """

		self.meta[_metaFilename] = filename if filename else None

		self.fileMtime = os.stat(filename).st_mtime if filename else None
		""" The script file's latest modified timestamp. """

		self.nextScript:Tuple[PContext, List[str]] = None	# Script to be started after another script ended
		""" The next script to be executed. Used for chaining scripts. """

		self._validate()	# May change the state to indicate an error


	def _validate(self) -> None:
		"""	Validate the script

			If an invalid script is detected then the state is set to *invalid*.
		"""
		# Check that @prompt is not used together with conflicting events, and other checks.
		if _metaPrompt in self.meta:
			if any(key in _metaPromptlessEvents for key in self.meta.keys()):
				self.setError(PError.invalid, f'"@prompt" is not allowed together with any of: {_metaPromptlessEvents}')
		if _metaTimeout in self.meta:
			t = self.meta[_metaTimeout]
			try:
				self.maxRuntime = float(t)
			except ValueError as e:
				self.setError(PError.invalid, f'"@timeout" has an invalid value; it must be a float: {t}')
	

	def log(self, pcontext:PContext, msg:str) -> None:
		"""	Callback for normal log messages.

			Args:
				pcontext: Script context. Not used.
				msg: log message.
		"""
		if RC.isHeadless:
			return
		for line in msg.split('\n'):	# handle newlines in the msg
			CSE.textUI.scriptLog(pcontext.scriptName, line)	# Additionally print to the text UI script console
			L.isDebug and L.logDebug(line, stackOffset=1)


	def logError(self, pcontext:PContext, msg:str, exception:Optional[Exception] = None) -> None:
		"""	Callback for error log messages.

			Args:
				pcontext: Script context. Not used.
				msg: The log message.
				exception: Optional exception to log.
		"""
		if RC.isHeadless:
			return
		for line in msg.split('\n'):	# handle newlines in the msg
			CSE.textUI.scriptLogError(pcontext.scriptName, line)	# Additionally print to the text UI script console
			L.isWarn and L.logWarn(line, stackOffset=1)


	def prnt(self, pcontext:PContext, msg:str) -> None:
		"""	Callback for *print* function messages.

			Args:
				pcontext: Script context. Not used.
				msg: The log message.
		"""
		if RC.isHeadless:
			return
		for line in msg.split('\n'):	# handle newlines in the msg
			if CSE.textUI.tuiApp:
				CSE.textUI.scriptPrint(pcontext.scriptName, line)	# Additionally print to the text UI script console
			else:
				# L.console(line, nl = not len(line))
				L.console(Text.from_markup(line))
	
	
	@property
	def errorMessage(self) -> str:
		"""	Format and return an error message.
		
			Return:
				String with the error message.
		"""
		return f'"{self.error.error.name}" error in {self.scriptFilename} - {self.error.message}'


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
	#	Symbols
	#


	def doClearConsole(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Clear the console.
		
			Example:
				::

					(clear-console)

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, 1)
		if not RC.isHeadless:
			CSE.textUI.scriptClearConsole(pcontext.scriptName) # Additionally clear the text UI script console
			L.consoleClear()
		return pcontext.setResult(SSymbol())


	def doCreateResource(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Execute a "create-resource" request to create a resource on a CSE.

			The function has the following arguments:

				- originator of the request
				- target resource ID
				- JSON resource
				- Optional: JSON with additional request arguments
			
			The function returns a quoted list as a result with the following symbols:
				
				- Response status
				- Response resource
				
			Example:
				::

					(create-resource "originator" "cse-in"  { "m2m:cnt": { "rn": "myCnt" }} [<request arguments>]) -> ( <status> <resource> )

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, minLength = 4, maxLength = 5)
		return self._handleRequest(cast(ACMEPContext, pcontext), symbol, Operation.CREATE)
	

	def doCseAttributeInfos(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Return a list of CSE attribute infos for the given attribute name. 
			The search is done over the short and long names of the attributes using
			a fuzzy search when searching the long names.

			The function has the following arguments:

				- attribute name. This could be a short name or a long name.
			
			The function returns a quoted list where each entry is another quoted list
			with the following symbols:
				
				- attribute short name
				- attribute long name
				- attribute type
				
			Example:
				::

					(cse-attribute-info "acop") -> ( ( "acop" "accessControlOperations" "nonNegInteger" ) )

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""

		def _getType(t:BasicType, policy:AttributePolicy) -> str:	# type:ignore [return]
			match t:
				case BasicType.list | BasicType.listNE if policy.lTypeName != 'enum':
					return f'{policy.typeName} of {policy.lTypeName}'
				case BasicType.list | BasicType.listNE if policy.lTypeName == 'enum':
					return f'{policy.typeName} of {_getType(BasicType.enum, policy)}'
				case BasicType.complex:
					return policy.typeName
				case BasicType.enum:
					return f'enum ({policy.etype})'
				case _:
					return policy.typeName


		pcontext.assertSymbol(symbol, 2)

		# get attribute name
		pcontext, _name = pcontext.valueFromArgument(symbol, 1, SType.tString)

		result = CSE.validator.getAttributePoliciesByName(_name)
		resultSymbolList = []
		if result is not None:
			for policy in result:
				# Determine exact type
				_t = _getType(policy.type, policy)
				# match policy.type:
				# 	case BasicType.list | BasicType.listNE:
				# 		_t = f'{policy.typeName} of {policy.lTypeName}'
				# 	case BasicType.complex:
				# 		_t = policy.typeName
				# 	case BasicType.enum:
				# 		_t = f'enum ({policy.etype})'
				# 	case _:
				# 		_t = policy.typeName
				
				resultSymbolList.append(SSymbol(lstQuote = [ SSymbol(string = policy.sname), 
					   										 SSymbol(string = policy.lname), 
															 SSymbol(string = _t) ]))

		return pcontext.setResult(SSymbol(lstQuote = resultSymbolList))


	def doCseStatus(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		""" Retrieve the CSE status.
		
			Example:
				::

					(cse-status)

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result, ie. the CSE status as a string.
		"""
		pcontext.assertSymbol(symbol, 1)
		return pcontext.setResult(SSymbol(string = RC.cseStatus.name))


	def doDeleteResource(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Execute a "delete-resource" request on the CSE.
		
			The function has the following arguments:

				- originator of the request
				- target resource ID
				- Optional: JSON with additional request arguments
			
			The function returns a quoted list as a result with the following symbols:
				
				- Response status
				- Response resource
		
			Example:
				::

					(delete-resource "originator "cse-in/myCnt" [<request arguments>]) -> ( <status> <resource> )

			Args:
				pcontext: PContext object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, minLength = 3, maxLength = 4)
		return self._handleRequest(cast(ACMEPContext, pcontext), symbol, Operation.DELETE)


	def doGetConfiguration(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Get a setting from the CSE's configuration.
		
			Example:
				::

					(get-configuration "cse.cseID") -> "id-in

			Args:
				pcontext: PContext object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
			
			Raises:
				`PUndefinedError`: In case the configuration key is undefined
		"""
		pcontext.assertSymbol(symbol, 2)

		# key path
		pcontext, _key = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# config value
		if (_v := Configuration.get(_key)) is None:
			raise PUndefinedError(pcontext.setError(PError.undefined, f'undefined configuration key: {_key}'))
		
		return pcontext.setResult(SSymbol(value = _v))


	def doGetLogLevel(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Get the log level of the CSE. This will be one of the following strings:

				- "DEBUG"
				- "INFO"
				- "WARNING"
				- "ERROR"
				- "OFF"

		
			Example:
				::

					(get-loglevel) -> "INFO"

			Args:
				pcontext: PContext object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, 1)
		return pcontext.setResult(SSymbol(string  = str(L.logLevel)))


	def doGetStorage(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Retrieve a value for *key* from the persistent storage *storage*.

			Example:
				::

					(get-storage "aStorageID" "aKey") -> value

			Args:
				pcontext: PContext object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
			
			Raises:
				`PUndefinedError`: If the key is undefined in the persistent storage.
		"""
		pcontext.assertSymbol(symbol, 3)

		# get storage
		pcontext, _storage = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# get key
		pcontext, _key = pcontext.valueFromArgument(symbol, 2, SType.tString)

		if (_val := CSE.script.storageGet(_storage, _key)) is None:
			raise PUndefinedError(pcontext.setError(PError.undefined, f'Undefined storage key: {_key}'))
		
		return pcontext.setResult(_val)


	def doHasConfiguration(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Test for the existence of a key in the CSE's configuration.

			Example:
				::

					(has-config "aKey")

			Args:
				pcontext: PContext object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result, ie. a boolean value.
		"""
		pcontext.assertSymbol(symbol, 2)

		# extract key
		pcontext, _key = pcontext.valueFromArgument(symbol, 1, SType.tString)

		return pcontext.setResult(SSymbol(boolean = Configuration.has(_key)))


	def doHasStorage(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Test for the existence of a key in the persistent storage.

			Example:
				::

					(has-storage "aStorageID" "aKey")

			Args:
				pcontext: PContext object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result, ie. a boolean value.
		"""
		pcontext.assertSymbol(symbol, 3)

		# extract storage
		pcontext, _storage = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# extract key
		pcontext, _key = pcontext.valueFromArgument(symbol, 2, SType.tString)

		return pcontext.setResult(SSymbol(boolean = CSE.script.storageHas(_storage, _key)))


	def doHttp(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		""" Making a http(s) request.
				
			Example:
				::

					(http post "https://example.com"
						('("aHeader" "a header value")
						 '("anotherHeader" "another header value"))
						"body content")

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.

			Raises:
				`PInvalidArgumentError`: In case the operation is undefined or an invalid header definion is encountered.
		"""
		# clear all response variables first
		for k, _ in pcontext.getVariables('response\\.*'):
			pcontext.delVariable(k)

		pcontext.assertSymbol(symbol, minLength = 3, maxLength = 5)

		# Get operation
		pcontext, _op = pcontext.valueFromArgument(symbol, 1, (SType.tSymbol, SType.tSymbolQuote))
		_op = _op.lower()
		if (_method := _httpMethods.get(_op)) is None:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'unknown or unsupported http method: {_op}'))

		# Get URL
		pcontext, _url = pcontext.valueFromArgument(symbol, 2, SType.tString)

		# Get optional headers
		_headers:JSON = {}
		if symbol.length > 3:
			pcontext, result = pcontext.resultFromArgument(symbol, 3, (SType.tJson, SType.tListQuote, SType.tNIL))
			match result.type:
				case SType.tJson:
					_headers = cast(JSON, result.value)
				case SType.tListQuote:
					for item in result.value:	# type: ignore[union-attr]
						item = cast(SSymbol, item)
						try:
							pcontext.assertSymbol(item, 2)
						except:
							raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid header definition: {item}'))
						pcontext, _key = pcontext.resultFromArgument(item, 0)
						pcontext, _value = pcontext.resultFromArgument(item, 1)
						if _key.type not in [SType.tSymbol, SType.tSymbolQuote, SType.tString]:
							raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid header key: {_key}'))
						if _value.type not in [SType.tString, SType.tNumber]:
							raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'invalid header value: {_value}'))
						_headers[str(_key.value)] = str(_value.value)
				case SType.tNIL:
					pass


		# get body, if present
		_body:str|JSON = None
		if symbol.length == 5:
			pcontext, result = pcontext.resultFromArgument(symbol, 4, (SType.tString, SType.tJson, SType.tNIL))
			match result.type:
				case SType.tString | SType.tJson:
					_body = str(result)
					if len(_body):
						_headers['Content-Length'] = str(len(_body))
				case SType.tNIL:
					pass

		# send http request
		try:
			response = _method(_url, 
							  data = _body,
							  headers = _headers, 
							  verify = Configuration.http_security_verifyCertificate,
							  timeout = Configuration.http_timeout)		# type: ignore[operator, call-arg]
		except requests.exceptions.ConnectionError:
			pcontext.variables['response.status'] = SSymbol()	# nil
			return pcontext.setResult(SSymbol())

		# parse response and assign to variables

		pcontext.variables['response.status'] = SSymbol(number = Decimal(response.status_code))
		pcontext.variables['response.body'] =  SSymbol(string = response.text) if response.text else SSymbol()
		if response.headers: # fill header variables
			for k, v in response.headers.items():
				pcontext.variables[f'response.{k}'] = SSymbol(string = v)

		pcontext.result = SSymbol(lstQuote = [	SSymbol(number = Decimal(response.status_code)),
												SSymbol(string = response.text),
												SSymbol(jsn = dict(response.headers)) ])
		return pcontext


	def doImportRaw(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Import a raw resource. Not much verification is done, and a full resource
			representation, including, for example, the parent resource ID, must be provided.
		
			Example:
				::

					(import-raw <originator> <resource JSON> )

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
			
			Raises:
				`PRuntimeError`: In case an error during the import and create is encountered.
		"""
		pcontext.assertSymbol(symbol, 3)
		
		# originator
		pcontext, _originator = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# resource object
		pcontext, _resource = pcontext.valueFromArgument(symbol, 2, SType.tJson)
		_resource = resourceFromDict(cast(dict, _resource),
							   		 create = True, 
									 isImported = True,
									 originator = _originator)

		# Get a potential parent resource
		parentResource:Any = None
		if _resource.pi:
			try:
				parentResource = CSE.dispatcher.retrieveLocalResource(ri = _resource.pi)
			except ResponseException as e:
				raise PRuntimeError(self.setError(PError.runtime, e.dbg))

		# Check resource registration
		try:
			CSE.registration.checkResourceCreation(_resource, _originator, parentResource)
		except ResponseException as e:
			raise PRuntimeError(self.setError(PError.runtime, e.dbg))

		# Create the resource
		try:
			resource = CSE.dispatcher.createLocalResource(_resource, parentResource, originator = _originator)
		except ResponseException as e:
			raise PRuntimeError(self.setError(PError.runtime, L.logErr(f'Error during import: {e.dbg}', showStackTrace = False)))
		# return self._pcontextFromRequestResult(pcontext, result)
		return pcontext.setResult(SSymbol(jsn = resource.asDict()))


	def doLogDivider(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Print a divider line to the log (on DEBUG level).
			
			Optionally add a message that is centered on the line.
			
			Example:
				::

					(log-divider "Hello, World")

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, minLength = 1, maxLength = 2)
	
		# Message
		msg = ''
		if symbol.length == 2:
			pcontext, msg = pcontext.valueFromArgument(symbol, 1, SType.tString)

		L.logDivider(LogLevel.DEBUG, msg)
		return pcontext


	def doNotify(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Execute a NOTIFY request. The originator must be set before this function.
		
			The function has the following arguments:

				- originator of the request
				- target resource ID
				- JSON resource
				- Optional: JSON with additional request arguments
			
			The function returns a quoted list as a result with the following symbols:
				
				- Response status
				- Response resource

			Example:
				::

					(send-notification <originator> <target> <resource JSON> [<headers JSON>]) -> ( <status> <resource> )

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.
			
			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, minLength = 4, maxLength = 5)
		return self._handleRequest(cast(ACMEPContext, pcontext), symbol, Operation.NOTIFY)


	def doOpenWebBrowser(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Open a web browser with the given URL.
		
			The function has the following arguments:

				- URL to open in the browser.
			
			The function returns a boolean as a result, indicating if the 
			browser could be opened.

			Example:
				::

					(open-web-browser <url>) -> boolean

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.
			
			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, 2)

		# URL
		pcontext, _url = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# Open the browser
		try:
			webbrowser.open(_url)
			return pcontext.setResult(SSymbol(boolean = True))
		except Exception as e:
			return pcontext.setResult(SSymbol(boolean = False))
		

	def doPingTcpService(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Ping a TCP service (server) to check if it is available and reachable.
		
			The function has the following arguments:

				- server name or IP address.
				- port number.
				- Optional: timeout in seconds (default: 10).
			
			The function returns a boolean as a result, indicating if the 
			service is reachable.

			Example:
				::

					(ping-service <server> <port> [<timeout>]) -> boolean

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.
			
			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, minLength = 3, maxLength = 4)

		# server
		pcontext, _server = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# port
		pcontext, _port = pcontext.valueFromArgument(symbol, 2, SType.tNumber)
		if not isValidPort(_port):
			raise PInvalidArgumentError(self.setError(PError.invalid, f'Invalid port number: {_port}'))

		# timeout
		_timeout = 10
		if symbol.length == 4:
			pcontext, _timeout = pcontext.valueFromArgument(symbol, 3, SType.tNumber)
			if _timeout <= 0.0:
				raise PInvalidArgumentError(self.setError(PError.invalid, f'Invalid timeout: {_timeout}. Must be greater than 0.0'))

		return pcontext.setResult(SSymbol(boolean = pingTCPServer(_server, int(_port), float(_timeout))))


	def doPrintJSON(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Print a beautified JSON to the console.

			Nothing will be printed if the CSE is running in *headless* mode.
			
			Example:
				::

					(print-json { "a" : "b" })

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, 2)

		if RC.isHeadless:
			return pcontext
		
		# json
		pcontext, _json = pcontext.valueFromArgument(symbol, 1, SType.tJson)

		L.console(cast(dict, _json))
		return pcontext


	def doPutStorage(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		""" Store a value in the persistent storage.

			Example:
				::

					(put-storage "storageID" "aKey" "Hello, World")

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, 4)


		# get storage
		pcontext, _storage = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# get key
		pcontext, _key = pcontext.valueFromArgument(symbol, 2, SType.tString)

		# get value
		pcontext, _value = pcontext.resultFromArgument(symbol, 3, _storageTypes)

		CSE.script.storagePut(_storage, _key, _value)
		return pcontext


	def doQueryResource(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Run a comparison query against a JSON structure. This compares to the oneM2M advanced
			query filtering in RETRIEVE/DISCOVERY requests.

			The first argument is an s-expression that only contains comparisons.

			Example:
				::

					(query-resource '(== rn "cnt1234")) { "rn": "cnt1234", "x": 123 })

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, 3)

		# get query
		pcontext = pcontext.getArgument(symbol, 1, (SType.tList, SType.tListQuote))
		_query = pcontext.result.toString(quoteStrings = True)

		# get JSON
		pcontext, _json = pcontext.valueFromArgument(symbol, 2, SType.tJson)

		return pcontext.setResult(SSymbol(boolean = CSE.script.runComparisonQuery(_query, _json)))


	def doRemoveStorage(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Either remove a value from the persistent storage, or remove all values from the storage with 
			a given storage ID.

			Example:
				::

					(storage-remove "aStorageID" "aKey")
					(storage-remove "aStorageID")

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, minLength = 2, maxLength = 3)

		if symbol.length == 2:

			# get storage
			pcontext, _storage = pcontext.valueFromArgument(symbol, 1, SType.tString)
			CSE.script.storageRemoveStorage(_storage)
			return pcontext
		
		# get storage
		pcontext, _storage = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# get key
		pcontext, _key = pcontext.valueFromArgument(symbol, 2, SType.tString)

		CSE.script.storageRemove(_storage, _key)
		return pcontext


	def doReset(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Reset the CSE.

			Example:
				::

					(reset)

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, 1)
		CSE.resetCSE()
		return pcontext.setResult(SSymbol())
	

	def doRetrieveResource(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Execute a RETRIEVE request. 

			The function has the following arguments:

				- originator of the request
				- target resource ID
				- Optional: JSON with additional request arguments
			
			The function returns a quoted list as a result with the following symbols:
				
				- Response status
				- Response resource

			Example:
				::

					(retrieve-resource "originator" "cse-in" [(<headers JSON>)] -> ( <status> <resource> )

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		return self._handleRequest(cast(ACMEPContext, pcontext), symbol, Operation.RETRIEVE)
	

	def doRunsInIPython(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Determine whether the CSE currently runs in an IPython environment, such as Jupyter Notebooks.
		
			Example:
				::

					(runs-in-ipython)

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result, ie. a boolean value.
		"""
		pcontext.assertSymbol(symbol, 1)
		return pcontext.setResult(SSymbol(boolean = runsInIPython()))


	def doRunsInTUI(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Determine whether the CSE currently runs in Text UI mode.
		
			Example:
				::

					(runs-in-tui)

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result, ie. a boolean value.
		"""
		pcontext.assertSymbol(symbol, 1)
		return pcontext.setResult(SSymbol(boolean = CSE.textUI.tuiApp is not None))


	def doScheduleNextScript(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Schedule the next script to run after the current script has finished.

			Example:
				::

					(schedule-next-script "scriptName" "arg1" "arg2" ...)
					(schedule-next-script "scriptName")

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object.
		"""
		pcontext.assertSymbol(symbol, minLength = 2)

		# script name
		pcontext, name = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# arguments
		arguments:list[str] = []
		if symbol.length > 2:
			for idx in range(2, symbol.length):
				pcontext, value = pcontext.valueFromArgument(symbol, idx)
				arguments.append(str(value))

		# find script
		if len(scripts := CSE.script.findScripts(name = name)) == 0:
			raise PUndefinedError(pcontext.setError(PError.undefined, f'script: "{name}" not found'))
		
		# Set the next-running script and its arguments
		cast(ACMEPContext, pcontext).nextScript = (scripts[0], arguments)
		return pcontext


	def doRunScript(self, pcontext:PContext, symbol:SSymbol, isInclude:bool = False) -> PContext:
		"""	Run another script. 
		
			The result of the script is passed as the result of this function.
		
			Example:
				::

					(run-script <script name> [<arguments>]* ) -> ( <status> <resource> )

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.
				isInclude: Boolean indicator whether the script result (functions, variables) shall be added to the currently running script.

			Return:
				The updated `PContext` object with the operation result.
			
			Raises:
				`PUndefinedError`: In case there is no script with that name.
				`PRuntimeError`:  In case the script exits with an error.
		"""
		pcontext.assertSymbol(symbol, minLength = 2)

		# script name
		pcontext, name = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# arguments
		arguments:list[str] = []
		if symbol.length > 2:
			for idx in range(2, symbol.length):
				pcontext, value = pcontext.valueFromArgument(symbol, idx)
				arguments.append(value.toString())

		# find script
		if len(scripts := CSE.script.findScripts(name = name)) == 0:
			raise PUndefinedError(pcontext.setError(PError.undefined, f'script: "{name}" not found'))

		# run script
		script = scripts[0]
		if not CSE.script.runScript(script, arguments = arguments, background = False):
			raise PRuntimeError(pcontext.setError(PError.runtime, f'Error in running script: {script.scriptName}: {script.error.message}'))
		
		if isInclude:
			# Copy newly defined functions
			pcontext.functions.update(script.functions)
			# Copy variables, except a few special ones
			pcontext.variables.update( { k:v 
										 for k,v in script.variables.items() 
										 if k not in ['argc'] } )

		return pcontext.setResult(script.result)


	def doSetCategoryDescription(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Set the description of a category.
		
			Example:
				::

					(set-category-description "myCategory" "My category description")

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated PContext object with the operation result.
		"""
		pcontext.assertSymbol(symbol, 3)

		# category
		pcontext, _category = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# description
		pcontext, _description = pcontext.valueFromArgument(symbol, 2, SType.tString)

		# Set the description
		CSE.script.categoryDescriptions[_category] = _description
		return pcontext
	


	def doSetConfig(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Set a CSE configuration. The configuration must be an existing configuration. No
			new configurations can be created this way.
		
			Example:
				::

					(set-config <configuration key> <value>)

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
			
			Raises:
				`PInvalidTypeError`: In case the data types of the configuration setting and the new value are different from each other.
				`PUnsupportedError`: In case the data type is not supported.
				`PInvalidArgumentError`: In case the setting could not be updated.
				`PUndefinedError`: In case the key references an undefined configuration setting.
		"""
		pcontext.assertSymbol(symbol, 3)

		# key
		pcontext, _key = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# value
		pcontext, result = pcontext.resultFromArgument(symbol, 2)

		if Configuration.has(_key):	# could be None, False, 0, empty string etc
			# Do some conversions first
			
			match (v := Configuration.get(_key)):
				case ACMEIntEnum():
					if result.type == SType.tString:
						r = Configuration.update(_key, v.__class__.to(cast(str, result.value), insensitive = True))
					else:
						raise PInvalidTypeError(pcontext.setError(PError.invalid, 'configuration value must be a string'))
				case str():
					if result.type == SType.tString:
						r = Configuration.update(_key, cast(str, result.value).strip())
					else:
						raise PInvalidTypeError(pcontext.setError(PError.invalid, 'configuration value must be a string'))
				# bool must be tested before int! 
				# See https://stackoverflow.com/questions/37888620/comparing-boolean-and-int-using-isinstance/37888668#37888668
				case bool():
					if result.type == SType.tBool:
						r = Configuration.update(_key, result.value)
					else:
						raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'configuration value must be a boolean'))

				case int():
					if result.type == SType.tNumber:
						r = Configuration.update(_key, int(cast(Decimal, result.value)))
					else:
						raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'configuration value must be an integer'))

				case float():
					if result.type == SType.tNumber:
						r = Configuration.update(_key, float(cast(Decimal, result.value)))
					else:
						raise PInvalidTypeError(pcontext.setError(PError.invalidType, f'configuration value must be a float, is: {result.type}'))

				case _:
					raise PUnsupportedError(pcontext.setError(PError.invalidType, f'unsupported type: {type(v)}'))
						
			# Check whether something went wrong while setting the config
			if r:
				raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'Error setting configuration: {r}'))

		else:
			raise PUndefinedError(pcontext.setError(PError.undefined, f'Undefined configuration: {_key}'))

		return pcontext


	def doSetLogging(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Enable/disable the console logging.

			Example:
				::

					(set-console-logging true)

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, 2)

		# Value
		pcontext, value = pcontext.valueFromArgument(symbol, 1, SType.tBool)
		L.enableScreenLogging = cast(bool, value)
		return pcontext.setResult(SSymbol())


	def doTuiNotify(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Show a TUI notification.

			This function is only available in TUI mode. It has the following arguments.

				- message: The message to show.
				- title: (Optional) The title of the notification.
				- severity: (Optional) The severity of the notification. Can be
				  one of the following values: *information*, *warning*, *error*.
				- timeout: (Optional) The timeout in seconds after which the
				  notification will disappear. If not specified, the notification
				  will disappear after 3 seconds.
			
			The function returns NIL.

			Example:
				::

					(tui-notify "This is a notification")

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object.
		"""
		pcontext.assertSymbol(symbol, minLength = 2, maxLength = 5)

		# Value
		pcontext, value = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# Title
		pcontext, title = pcontext.valueFromArgument(symbol, 2, SType.tString, optional = True)

		# Severity
		pcontext, severity = pcontext.valueFromArgument(symbol, 3, SType.tString, optional = True)

		# Timeout
		pcontext, timeout = pcontext.valueFromArgument(symbol, 4, SType.tNumber, optional = True)

		# show the notification
		CSE.textUI.scriptShowNotification(value, title, severity, float(timeout) if timeout is not None else None)

		return pcontext.setResult(SSymbol())


	def doTuiRefreshResources(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Refresh the TUI resources. This will update the resource Tree and the resource
			details.

			Example:
				::

					(tui-refresh-resources)
			
			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object.
		"""
		pcontext.assertSymbol(symbol, 1)
		CSE.textUI.refreshResources()
		return pcontext


	def doTuiVisualBell(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Execute a TUI visual bell. This shortly flashes the script's menu entry.

			Example:
				::

					(tui-visual-bell)

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.
			
			Return:
				The updated `PContext` object.
		"""
		pcontext.assertSymbol(symbol, 1)
		CSE.textUI.scriptVisualBell(pcontext.scriptName)
		return pcontext


	def doUpdateResource(self, pcontext:PContext, symbol:SSymbol) -> PContext:
		"""	Execute an UPDATE request. 

			The function has the following arguments:

				- originator of the request
				- target resource ID
				- JSON resource
				- Optional: JSON with additional request arguments
			
			The function returns a quoted list as a result with the following symbols:
				
				- Response status
				- Response resource

			Example:
				::

					(update-resource "originator" "cse-in/myCnt" { "m2m:cnt" { "lbl": ["aLabel"] }} [<request arguments>]) -> ( <status> <resource> )

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.

			Return:
				The updated `PContext` object with the operation result.
		"""
		pcontext.assertSymbol(symbol, minLength = 4, maxLength = 5)
		return self._handleRequest(cast(ACMEPContext, pcontext), symbol, Operation.UPDATE)

	#########################################################################
	#
	#	Internals
	#


	def _pcontextFromRequestResult(self, pcontext:PContext, res:Result) -> PContext:
		"""	Update a `PContext` instance from a CSE `Result`.

			Args:
				pcontext: `PContext` object of the running script.
				res: `Result` object.

			Return:
				The updated `PContext` object with the operation result.
		"""
		# Construct response
		responseStatus = SSymbol(number = Decimal(res.rsc.value))
		try:
			if res.dbg:
				# L.isDebug and L.logDebug(f'Request response: {res.dbg}')
				responseResource = SSymbol(jsn = { 'm2m:dbg:': f'{str(res.dbg)}'})
			elif res.resource:
				# L.isDebug and L.logDebug(f'Request response: {res.resource}')
				responseResource = SSymbol(jsn = cast(Resource, res.resource).asDict())
			elif res.data:
				# L.isDebug and L.logDebug(f'Request response: {res.data}')
				responseResource = SSymbol(jsnString = json.dumps(res.data)) if isinstance(res.data, dict) else SSymbol(string = str(res.data))
				# L.logDebug(self.getVariable('response.resource'))
			else:
				# L.isDebug and L.logDebug('Request response: (unknown or none)')
				responseResource = SSymbol()
		except Exception as e:
			L.logErr(f'Error while decoding result: {str(e)}', exc = e)
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'Invalid resource or data: {res.data if res.data else res.resource}'))
		
		return pcontext.setResult(SSymbol(lstQuote = [ responseStatus, responseResource ]))


	def _handleRequest(self, pcontext:PContext, symbol:SSymbol, operation:Operation) -> PContext:
		"""	Internally handle a request, either via a direct URL or through an originator.

			Return status and resources in the variables *result.status* and 
			*result.resource* respectively.

			Args:
				pcontext: `PContext` object of the running script.
				symbol: The symbol to execute.
				operation: The operation to perform.

			Return:
				The updated `PContext` object with the operation result.

			Raises:
				`PInvalidArgumentError`: In case the input, e.g. the resource, is incorrect.
		"""

		# Get originator
		pcontext, originator = pcontext.valueFromArgument(symbol, 1, SType.tString)

		# Get target
		pcontext, target = pcontext.valueFromArgument(symbol, 2, SType.tString)

		# Get Content
		content:JSON = None
		if operation in [Operation.CREATE, Operation.UPDATE, Operation.NOTIFY]:
			pcontext, content = pcontext.valueFromArgument(symbol, 3, SType.tJson)
			idx = 4
		else:
			idx = 3

		# Get extra request attributes
		attributes:JSON = {}
		if symbol.length > idx:
			pcontext, attributes = pcontext.valueFromArgument(symbol, idx, SType.tJson)

		# Prepare request structure
		req = { 'op': operation,
				'fr': originator,
				'to': target, 
				'rvi': RC.releaseVersion,
				'rqi': uniqueRI(), 
				'ot': getResourceDate(),
			}
		
		# Transform the extra request attributes set by the script
		if attributes:
			# add remaining attributes 
			for key in list(attributes.keys()):
				setXPath(req, key, attributes[key])

		# Get the resource for some operations
		if operation in [ Operation.CREATE, Operation.UPDATE, Operation.NOTIFY ]:
			# Add type when CREATE
			if operation == Operation.CREATE:
				if (ty := ResourceTypes.fromTypeShortname( list(content.keys())[0] )) is None: # first is typeShortname
					raise PInvalidArgumentError(pcontext.setError(PError.invalid, 'Cannot determine resource type'))
				req['ty'] = ty.value

			# Add primitive content when content is available
			req['pc'] = content

		elif content:	# operation in [ Operation.RETRIEVE, Operation.DELETE ]
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'{operation.name} request shall have no content'))

		# Prepare request
		try:
			request = CSE.request.fillAndValidateCSERequest(req)
		except ResponseException as e:
			raise PInvalidArgumentError(pcontext.setError(PError.invalid, f'Invalid resource: {e.dbg}', exception = e))
		
		# Send request
		L.isDebug and L.logDebug(f'Sending request from script: {request.originalRequest} to: {target}')
		if isURL(target):
			match operation:
				case Operation.RETRIEVE:
					res = CSE.request.handleSendRequest(CSERequest(op = Operation.RETRIEVE,
																ot = getResourceDate(),
																to = target, 
																originator = originator)
													)[0].result	# there should be at least one result
				case Operation.DELETE:
					res = CSE.request.handleSendRequest(CSERequest(op = Operation.DELETE,
																ot = getResourceDate(),
																to = target, 
																originator = originator)
													)[0].result	# there should be at least one result
				case Operation.CREATE:
					res = CSE.request.handleSendRequest(CSERequest(op = Operation.CREATE,
												ot = getResourceDate(),
												to = target, 
												originator = originator, 
												ty = ty,
												pc = request.pc)
									)[0].result	# there should be at least one result
				case Operation.UPDATE:
					res = CSE.request.handleSendRequest(CSERequest(op = Operation.UPDATE,
																ot = getResourceDate(),
																to = target, 
																originator = originator, 
																pc = request.pc)
													)[0].result	# there should be at least one result
				case Operation.NOTIFY:
					res = CSE.request.handleSendRequest(CSERequest(op = Operation.NOTIFY,
												ot = getResourceDate(),
												to = target, 
												originator = originator, 
												pc = request.pc)
									)[0].result	# there should be at least one result

		else:
			# Request via CSE-ID, either local, or otherwise a transit request. Let the CSE handle it
			res = CSE.request.handleRequest(request)

		return self._pcontextFromRequestResult(pcontext, res)


#########################################################################
#
#	Script Manager
#

class ScriptManager(object):
	"""	This manager entity handles script execution in the CSE.
	"""

	__slots__ = (
		'scripts',
		'storage',
		'scriptUpdatesMonitor',
		'scriptCronWorker',

		'categoryDescriptions',
	)
	""" Slots of class attributes. """

	def __init__(self) -> None:
		"""	Initializer for the ScriptManager class.
		"""

		self.scripts:Dict[str,ACMEPContext] = {}				# The managed scripts
		""" Dictionary of scripts and script `ACMEPContext`. The key is the script name. """

		self.categoryDescriptions:Dict[str,str] = {}			# The category descriptions
		""" Dictionary of category descriptions. """

		self.storage:Dict[str, Dict[str, SSymbol]] = {}			# storage for global values
		""" Dictionary for internal global variable storage. """

		self.scriptUpdatesMonitor:BackgroundWorker = None
		""" `BackgroundWorker` worker to monitor script directories. """

		self.scriptCronWorker:BackgroundWorker = None
		""" `BackgroundWorker` worker to run cron-enabled scripts. """

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
	
	
	def configUpdate(self, name:str, 
						   key:Optional[str] = None, 
						   value:Optional[Any] = None) -> None:
		"""	Callback for the *configUpdate* event.
			
			Args:
				name: Event name.
				key: Name of the updated configuration setting.
				value: New value for the config setting.
		"""
		if key not in [ 'scripting.verbose', 
						'scripting.fileMonitoringInterval', 
						'scripting.scriptDirectories',
						'scripting.maxRuntime'
					  ]:
			return

		# restart or stop monitor worker
		if self.scriptUpdatesMonitor:
			if Configuration.scripting_fileMonitoringInterval > 0.0:
				self.scriptUpdatesMonitor.restart(interval = Configuration.scripting_fileMonitoringInterval)
			else:
				self.scriptUpdatesMonitor.stop()


	##########################################################################
	#
	#	Event handlers
	#

	def cseStarted(self, name:str) -> None:
		"""	Callback for the *cseStartup* event.

			Start a background worker to monitor directories for scripts.
		"""
		# Add a worker to monitor changes in the scripts
		self.scriptUpdatesMonitor = BackgroundWorkerPool.newWorker(Configuration.scripting_fileMonitoringInterval,
							     								   self.checkScriptUpdates, 
																   'scriptUpdatesMonitor')
		if Configuration.scripting_fileMonitoringInterval > 0.0:
			self.scriptUpdatesMonitor.start()

		# Add a worker to check scheduled script, fixed interval of 1 second
		self.scriptCronWorker = BackgroundWorkerPool.newWorker(1, 
							 								   self.cronMonitor, 
															   'scriptCronMonitor').start()

		# Look for the startup script(s) and run them. 
		self.runEventScripts(_metaOnStartup)


	def restart(self, name:str) -> None:
		"""	Callback for the *cseReset* event.
		
			Restart the script manager service, ie. clear the scripts and storage. 
			They are reloaded during import.
		"""
		self.removeScripts()
		self.storage.clear()
		L.isDebug and L.logDebug('ScriptManager restarted')
	

	def restartFinished(self, name:str) -> None:
		"""	Callback for the *cseRestarted* event.
		
			Run the restart script(s), if any.
		"""
		# Look for the shutdown script(s) and run them. 
		self.runEventScripts(_metaOnRestart)


	def onKeyboard(self, name:str, ch:str) -> None:
		"""	Callback for the *keyboard* event.
		
			Run script(s) with configured meta tags, if any.

			Args:
				name:Event name.
				ch: The pressed key.
		"""
		# Check for function key names first
		# Look for the shutdown script(s) and run them. 
		self.runEventScripts(_metaOnKey, 
							 cast(FunctionKey, ch).name if isinstance(ch, FunctionKey) else ch)


	def onNotification(self, name:str, uri:str, request:CSERequest) -> None:
		"""	Callback for the *notification* event.

			Run script(s) with configured meta tags, if any.

			Args:
				name:Event name.
				uri: The target URI.
				request: The notifiction request.
		"""
		try:
			self.runEventScripts( _metaOnNotification,	# !!! Lower case
								  uri,
								  background = False, 
								  environment = { 'notification.resource' : SSymbol(jsn = request.pc), 
								  				  'notification.originator' : SSymbol(string = request.originator),
												  'notification.uri': SSymbol(string = uri) })	
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
		for eachName, eachScript in list(self.scripts.items()):	# don't remove the `list(...). The dict is modified in the loop
			try:
				if eachScript.fileMtime < os.stat(eachScript.scriptFilename).st_mtime:
					L.isDebug and L.logDebug(f'Reloading script: {eachScript.scriptFilename}')
					if eachScript.state != PState.running:
						del self.scripts[eachName]
						self.loadScriptFromFile(eachScript.scriptFilename)
			except FileNotFoundError as e:
				# Remove deleted scripts from the internal list
				L.isDebug and L.logDebug(f'Removing script {eachScript.scriptFilename}')
				del self.scripts[eachName]

		# Read new scripts
		if CSE.importer.extendedScriptPaths:	# from the init directory
			if self.loadScriptsFromDirectory(CSE.importer.extendedScriptPaths) == -1:
				L.isWarn and L.logWarn('Cannot import script(s)')
		if Configuration.scripting_scriptDirectories:	# from the extra script directories
			if self.loadScriptsFromDirectory(Configuration.scripting_scriptDirectories) == -1:
				L.isWarn and L.logWarn('Cannot import script(s)')
		return True


	def cronMonitor(self) -> bool:
		"""	This is the callback for the cron scheduler.
		
			It looks for scripts with an *@at* meta tag and takes the argument as a cron pattern.
			Scripts that are scheduled to run now will be run, one after the other.
			
			Return:
				Boolean. Usually *True* to continue with monitoring.
		"""
		#L.isDebug and L.logDebug(f'Looking for scheduled scripts')
		_ts = utcDatetime()
		for each in self.findScripts(meta = _metaAt):
			try:
				if cronMatchesTimestamp(at := each.meta.get(_metaAt), _ts):
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
				if each.scriptFilename == filename:
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

				L.isDebug and L.logDebug(f'Importing script: {ffn}')
				if not self.loadScriptFromFile(ffn):
					return -1
				countScripts += 1

		return countScripts


	def loadScriptFromFile(self, filename:str) -> Optional[ACMEPContext]:
		"""	Load and store a script from a file. 

			Args:
				filename: The filename of the file.

			Return:
				`ACMEPContext` object with the script, or *None*.
		"""
		with open(filename) as file:
			return self.loadScript(file.read(), filename)


	def loadScript(self, script:str, filename:str) -> Optional[ACMEPContext]:
		"""	Load and initialize a script. If no name is set in the script itself, then the 
			filename's stem is set as the name.

			The script is stored in the `scripts` dictionary.

			Args:
				script: The script as a single string.
				filename: The filename of the file.

			Return:
				`ACMEPContext` object with the script, or *None*.
		"""
		try:
			pcontext = ACMEPContext(script, filename = filename)
			if pcontext.state != PState.ready:
				L.isWarn and L.logWarn(f'Error loading script: {pcontext.errorMessage}')
				return None
		except PInvalidArgumentError as e:
			L.logErr(f'Error loading script: {filename} : {e.pcontext.error.message}')
			return None
		except Exception as e:
			L.logErr(str(e), exc = e)
			return None


		# Add to scripts
		if not (name := pcontext.scriptName):		# Add name to meta data if not set
			pcontext.scriptName = Path(filename).stem
			name = pcontext.scriptName
			if name in self.scripts:
				L.isWarn and L.logWarn(f'Script with name or filename "{name}" already loaded')
				return None
		if not pcontext.scriptFilename:							# Add filename to meta data
			pcontext.scriptFilename = filename
		self.scripts[name] = pcontext
		return pcontext
	

	def removeScripts(self) -> None:
		"""	Remove all scripts.
		"""
		self.scripts.clear()
	

	def findScripts(self, name:Optional[str] = None,
						  meta:Optional[Union[str, list[str]]] = None,
						  ignoreCase:bool = False) -> list[PContext]:
		""" Find scripts by a filter.
		
			Filters are and-combined.

			Args:
				name: Filter by script name. The name can be a simple match.
				meta: Filter by script meta data. This can be a single string or a list of strings.

			Return:
				List of `PContext` objects with the script(s), sorted by name, or *None* in case of an error.
		"""

		result:list[PContext] = []

		# Find all the scripts by with simple match
		if name:
			result = [ script for script in self.scripts.values() if (n := script.scriptName) is not None and simpleMatch(n, name, ignoreCase = ignoreCase) ]
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
						arguments:Optional[list[str]|str] = '', 
						background:Optional[bool] = False, 
						finished:Optional[Callable] = None,
						environment:Optional[dict[str, SSymbol]] = {}) -> bool:
		""" Run a script.

			Args:
				pcontext: The script context to run.
				arguments: Optional arguments to the script. These are available to the script via the *argv* macro.
				background: Boolean to indicate whether to run the script in the backhround (as an Actor).
				finished: An optional function that will be called after the script finished.
				environment: An optional set of variables that are passed to script.

			Return:
				Boolean that indicates the successful running of the script. A background script always returns *True*.
		"""

		def runCB(pcontext:PContext, arguments:list[str]) -> None:
			"""	Actually run the script.

				Args:
					pcontext: The script context to run.
					arguments: Arguments to the script. These are available to the script via the *argv* macro.
			"""
			while True:
				result = pcontext.run(arguments = arguments)
				if pcontext.state == PState.terminatedWithResult:
					L.logDebug(f'Script terminated with result: {pcontext.result}')
				if pcontext.state == PState.terminatedWithError:
					L.logWarn(f'Script terminated with error: {pcontext.error.message}')
					if pcontext.error.exception:
						L.logWarn(''.join(traceback.format_exception(pcontext.error.exception)))

				if not result or not cast(ACMEPContext, pcontext).nextScript:	
					return
			
				# Run next script, also in the background
				_p = pcontext
				pcontext, arguments = cast(ACMEPContext, pcontext).nextScript
				cast(ACMEPContext, _p).nextScript = None	# Clear next script
				L.isDebug and L.logDebug(f'Running next script: {pcontext.scriptName}')



		while True:
			L.isDebug and L.logDebug(f'Running script: {pcontext.scriptName}, Background: {background}')
			if pcontext.state == PState.running:
				L.isWarn and L.logWarn(f'Script "{pcontext.scriptName}" is already running')
				# pcontext.setError(PError.invalid, f'Script "{pcontext.name}" is already running')
				return False
			
			# Set script timeout
			pcontext.setMaxRuntime(Configuration.scripting_maxRuntime)

			# Set environemt
			environment['tui.theme'] = SSymbol(string = Configuration.textui_theme)
			pcontext.setEnvironment(environment)

			# Handle arguments
			_arguments:Optional[list[str]] = []
			if arguments:
				_arguments = cast(str, arguments).split() if isinstance(arguments, str) else arguments
			_arguments.insert(0, pcontext.scriptName)

			# Run in background or direct
			if background:
				BackgroundWorkerPool.newActor(runCB, name = f'AS:{pcontext.scriptName}-{uniqueID()}', 
													finished = finished).start(pcontext = pcontext, arguments = _arguments)
				return True	# Always return True when running in Background
		
			result = pcontext.run(arguments = cast(list, _arguments)).state != PState.terminatedWithError

			if not result or not cast(ACMEPContext, pcontext).nextScript:
				return result
			
			# Run next script
			_p = pcontext
			pcontext, arguments = cast(ACMEPContext, pcontext).nextScript
			cast(ACMEPContext, _p).nextScript = None	# Clear next script
			L.isDebug and L.logDebug(f'Running next script: {pcontext.scriptName}')
	


		# return pcontext.run(arguments = cast(list, _arguments)).state != PState.terminatedWithError
	

	def run(self, scriptName:str, 
				  arguments:Optional[list[str]|str] = '',
				  metaFilter:Optional[list[str]] = [],
				  ignoreCase:Optional[bool] = False) -> Tuple[bool, SSymbol]:
		""" Run a script by its name (only in the foreground).

			Args:
				scriptName: The name of the script to run..
				arguments: Optional arguments to the script. These are available to the script via the *argv* macro.
				metaFilter: Extra filter to select a script.

			Return:
				The result of the script run in a tuple. Boolean indicating success, and an optional result.
		"""
		L.isDebug and L.logDebug(f'Looking for script: {scriptName}, arguments: {arguments if arguments else "None"}, meta: {metaFilter}')
		if len(scripts := self.findScripts(name = scriptName, meta = metaFilter, ignoreCase = ignoreCase)) != 1:
			return (False, SSymbol(string = L.logWarn(f'Script not found: "{scriptName}"')))
		script = scripts[0]
		if self.runScript(script, arguments = arguments, background = False):
			L.isDebug and L.logDebug(f'Script: "{scriptName}" finished successfully')
			return (True, script.result if script.result else SSymbol())
			
		L.isWarn and L.logWarn(f'Script "{scriptName}" finished with error: {script.error.error.name} : {script.error.message}')

		if script.error.error == PError.quitWithError:
			script.result = script.error.message
		return (False, script.result)


	_allowedQuerySymbols = ( '==', '!=', '<', '<=', '>', '>=', '&', '&&', '|', '||', '!', 'not', 'in')
	""" Allowed symbols for comparison queries. """

	def runComparisonQuery(self, query:str, resource:JSON|Resource) -> bool:
		"""	Run a comparison query against a JSON strcture or a resource.

			The *query* consists of logical or comparison operations, and only those
			are allowed. It can contain attributes, which values are taken from the JSON
			structure or resource.
		
			Args:
				query: String with a valid s-expression.
				resource: JSON dictionary or resource for the attributes.				

			Return:
				Boolean value indicating the success of the query.
		"""
		jsn = pureResource(resource.asDict() if isinstance(resource, Resource) else cast(JSON, resource) )[0]  

		L.isDebug and L.logDebug(f'Running query: {query} against: {jsn}')

		def getAttribute(pcontext:PContext, symbol:SSymbol) -> PContext:
			_attr = symbol.value
			if not isinstance(_attr, str):
				raise ValueError(f'attribute: {_attr} must be a string')
			if (_value := jsn.get(_attr)) is not None:
				L.isDebug and L.logDebug(f'Attribute: {_attr} = {_value}')
				return pcontext.setResult(SSymbol(value = _value))
			L.isDebug and L.logDebug(f'Attribute: {_attr} not found')
			return pcontext.setResult(SSymbol()) # nil
	

		def monitorExecution(pcontext:PContext, symbol:SSymbol) -> PContext:
			"""	Check whether the executed symbol is an allowed function for a comparison query.

				Args:
					pcontext: `PContext` object of the running script.
					symbol: The symbol to test.
				
				Return:
					The `PContext` object.
				
				Raises:
					`PPermissionError` in case the symbol is not allowed.

			"""
			if not symbol.value in self._allowedQuerySymbols:
				raise PPermissionError(pcontext.setError(PError.permissionDenied, f'Not allowed to use function: {str(symbol)} in expression'))
			return pcontext

	
		pcontext = ACMEPContext(query, fallbackFunc = getAttribute, monitorFunc = monitorExecution, allowBrackets = True)
		pcontext = cast(ACMEPContext, pcontext.run())
		if pcontext.result.type != SType.tBool:
			L.logWarn(f'Expected boolean for comparison, received: {pcontext.result.value}')
			return False
		return cast(bool, pcontext.result.value)

	##########################################################################
	#
	#	Storage handlers
	#

	def storageGet(self, storage:str, key:str) -> Optional[SSymbol]:
		"""	Retrieve a key/value pair from the persistent storage *storage*. 
		
			Args:
				storage: Name or ID of the storage.
				key: Key for the value to retrieve.

			Return:
				Previously stored value for the key, or *None*.
		"""
		_storage:Dict[str, SSymbol] = self.storage.get(storage, {})
		return _storage.get(key, None)


	def storageHas(self, storage:str, key:str) -> bool:
		"""	Test whether a key exists in the persistent storage *storageID*. 
		
			Args:
				storage: Name or ID of the storage.
				key: Key to check.

			Return:
				Boolean result.
		"""
		return key in self.storage.get(storage, {})


	def storagePut(self, storage: str, key:str, value:SSymbol) -> None:
		"""	Store a key/value pair in the persistent storage identified by *storage*.
		Existing values will be overwritten.
		
			Args:
				storage: Name or ID of the storage.
				key: Key where to store the value.
				value: Value to store.
		"""
		_storage:Dict[str, SSymbol] = self.storage.get(storage, {})
		_storage[key] = value
		self.storage[storage] = _storage


	def storageRemove(self, storage:str, key:str) -> None:
		"""	Remove a key/value pair from the persistent storage.
		
			Args:
				storage: Name or ID of the storage.
				key: Key where to store the value.
		"""
		_storage:Dict[str, SSymbol] = self.storage.get(storage, {})
		if key in _storage:
			del _storage[key]
			self.storage[storage] = _storage


	def storageRemoveStorage(self, storage:str) -> None:
		"""	Remove all key/value pairs from the persistent *storage*.
		
			Args:
				storage: Name or ID of the storage.
		"""
		if storage in self.storage:
			del self.storage[storage]


	##########################################################################
	#
	#	Misc
	#

	def runEventScripts(self, event:str, 
							  eventData:Optional[str] = None, 
							  background:Optional[bool] = True, 
							  environment:Optional[dict[str, SSymbol]] = {}) -> None:
		"""	Get and run all the scripts for specific events. 
		
			If the *argument* is given then the event's parameter must match the argument.

			This method is still called in the same thread as the console (the event is raised not in
			the background!), because otherwise the prompt input and the getch() function from the
			console are mixing up.

			Args:
				event: The event for which the script(s) are run.
				eventData: The optional event data that needs to match the event's pararmeter of the script.
				background: Run the script in the background
				environment: Extra variables to set in the script's environment
		"""

		def getPrompt(r:str = '') -> str:
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

		environment['event.type'] = SSymbol(string = _metaOnKey)
		
		if eventData:
			environment['event.data'] = SSymbol(string = cast(FunctionKey, eventData).name if isinstance(eventData, FunctionKey) else eventData)

		for each in self.findScripts(meta = event):
			if eventData:
				if (v := each.meta.get(event)) and v == eventData:
					self.runScript(each, arguments = getPrompt(), background = background, environment = environment)
			else:
				self.runScript(each, arguments = getPrompt(), background = background, environment = environment)
