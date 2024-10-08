#
#	Logging.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	
#

"""	Wrapper for the logging sub-system. 

	It provides simpler access as well some nicer output rendering.
"""

from __future__ import annotations
from typing import List, Any, Union, Optional, cast

import traceback
import logging, logging.handlers, os, inspect, datetime, time, threading
from queue import Queue
from logging import LogRecord


from rich import inspect as richInspect
from rich.logging import RichHandler
from rich.style import Style
from rich.console import Console
from rich.status import Status
from rich.markdown import Markdown
from rich.text import Text
from rich.default_styles import DEFAULT_STYLES
from rich.theme import Theme
from rich.tree import Tree
from rich.table import Table
from rich.prompt import Prompt
from rich.syntax import Syntax

from ..etc.Types import JSON, LogLevel, Result, ContentSerializationType
from ..etc.Constants import RuntimeConstants as RC
from ..helpers import TextTools
from ..helpers.BackgroundWorker import BackgroundWorker
from ..runtime.Configuration import Configuration

levelName = {
	logging.INFO :    'ℹ️  I',
	logging.DEBUG :   '🐞 D',
	logging.ERROR :   '🔥 E',
	logging.WARNING : '⚠️  W'
	# logging.INFO :    'INFO   ',
	# logging.DEBUG :   'DEBUG  ',
	# logging.ERROR :   'ERROR  ',
	# logging.WARNING : 'WARNING'
}

# Color Schemes for the terminal
terminalColorDark		= '#2DFE54' 
terminalColorErrorDark	= '#FF073A'
tableRowColorDark		= 'grey15'
fontDark				= '#E4E4E4'

terminalColorLight		= '#137E6D'
terminalColorErrorLight	= '#FF073A'
tableRowColorLight		= 'grey89'
fontLight				= '#1C1C1C'


class LogFilter(logging.Filter):
	"""	Filter for the logging system. It removes all log messages that
		originate from the given sources.
	"""

	def __init__(self, sources:tuple[str, ...]) -> None:
		"""	Initialize the filter with the given sources. If the sources
			are empty, no filtering is done.
			
			Args:
				sources: A tuple of sources to filter out.
		"""
		super().__init__()
		self.sources = sources if sources else ()


	def filter(self, record:LogRecord) -> bool:
		# filter out unwanted debug messages's loggings
		return not record.name.startswith(self.sources)


class Logging:
	""" Wrapper class for the logging subsystem. This class wraps the 
		initialization of the logging subsystem and provides convenience 
		methods for printing log, error and warning messages to a 
		logfile and to the console.
	"""

	logger  						= None
	loggerConsole					= None
	logLevel:LogLevel				= LogLevel.INFO
	isInfo 							= False
	isWarn 							= False
	isDebug 						= False
	lastLogLevel:LogLevel			= None
	enableFileLogging				= True
	enableScreenLogging				= True
	stackTraceOnError				= True
	enableBindingsLogging			= True
	worker 							= None
	queue:Queue						= None
	enableQueue						= False		# Can be used to enable/disable the logging queue 
	queueSize:int					= 0			# max number of items in the logging queue. Might otherwise grow forever on large load
	filterSources:tuple[str, ...]	= ()		# List of log sources that will be removed while processing the log messages
	maxLogMessageLength:int			= 0			# Max length of a log message. Longer messages will be truncated
	utcTime							= False		# Use UTC time for logging

	_console:Console				= None
	_richHandler:ACMERichLogHandler	= None
	_handlers:List[Any] 			= None
	_logWorker:BackgroundWorker		= None
	_basenames:dict[str, str]		= {}

	_eventLogError					= None
	_eventLogWarning				= None

	terminalStyle:Style				= Style(color = terminalColorDark)
	terminalStyleRGBTupple			= (0,0,0)
	terminalStyleError:Style		= Style(color = terminalColorErrorDark)
	tableRowStyle:Style				= Style(bgcolor = tableRowColorDark)


	@staticmethod
	def init() -> None:
		"""Init the logging system.
		"""

		if Logging.logger:
			return

		Logging.enableFileLogging 		= Configuration.logging_enableFileLogging
		Logging.enableScreenLogging		= Configuration.logging_enableScreenLogging
		Logging.stackTraceOnError		= Configuration.logging_stackTraceOnError
		Logging.enableBindingsLogging	= Configuration.logging_enableBindingsLogging
		Logging.queueSize				= Configuration.logging_queueSize
		Logging.filterSources			= tuple(Configuration.logging_filter)
		Logging.maxLogMessageLength		= Configuration.logging_maxLogMessageLength
		Logging.utcTime					= Configuration.logging_enableUTCTimezone

		Logging._configureColors(Configuration.console_theme)

		Logging.logger					= logging.getLogger('logging')			# general logger
		Logging.loggerConsole			= logging.getLogger('rich')				# Rich Console logger
		Logging._console				= Console()								# Console object
		Logging._richHandler			= ACMERichLogHandler()

		# Add logging filter
		Logging._richHandler.addFilter(LogFilter(Logging.filterSources))

		Logging.setLogLevel(cast(LogLevel, Configuration.logging_level))					# Assign the initial log level

		# Add logging queue
		Logging.queue = Queue(maxsize = Logging.queueSize)
		Logging.queueOn()

		# List of log handlers
		Logging._handlers = [ Logging._richHandler ]

		# Configurable: Set the timezone converter for file logging to UTC
		if Logging.utcTime:
			logging.Formatter.converter = time.gmtime

		# Log to file only when file logging is enabled
		if Logging.enableFileLogging:
			from ..runtime import CSE as CSE

			logpath = Configuration.logging_path
			os.makedirs(logpath, exist_ok = True)# create log directory if necessary
			logfile = f'{logpath}/cse-{RC.cseType.name}.log'
			logfp = logging.handlers.RotatingFileHandler(logfile,
														 maxBytes = Configuration.logging_size,
														 backupCount = Configuration.logging_count)
			logfp.setLevel(Logging.logLevel)
			logfp.setFormatter(logging.Formatter('%(levelname)s %(asctime)s %(message)s'))
			logfp.addFilter(LogFilter(Logging.filterSources))
			Logging.logger.addHandler(logfp) 
			Logging._handlers.append(logfp)

		# config the logging system
		logging.basicConfig(level = Logging.logLevel, format = '%(message)s', datefmt = '[%X]', handlers = Logging._handlers)

		# Start worker to handle logs in the background
		from ..helpers.BackgroundWorker import BackgroundWorkerPool
		Logging._logWorker = BackgroundWorkerPool.newActor(Logging.loggingActor, name = 'loggingWorker', ignoreException = True)
		Logging._logWorker.start()	# Yes, this could be in one line but the _logworker attribute may not be assigned yet before the 
									# actor callback is executed, and this might result in a None exception

		# React on config update. Only assig if it hasn't assigned before
		from ..runtime import CSE
		if not CSE.event.hasHandler(CSE.event.configUpdate, Logging.configUpdate):		# type: ignore [attr-defined]
			CSE.event.addHandler(CSE.event.configUpdate, Logging.configUpdate)			# type: ignore

		# Optimized eventing
		Logging._eventLogError = CSE.event.logError	# type: ignore
		Logging._eventLogWarning = CSE.event.logWarning 	# type: ignore


	@staticmethod
	def _configureColors(theme:str) -> None:
		Logging.terminalStyle 		= Style(color = terminalColorDark if theme == 'dark' else terminalColorLight)
		Logging.tableRowStyle		= Style(bgcolor = tableRowColorDark if theme == 'dark' else tableRowColorLight)
		Logging.terminalStyleError	= Style(color = terminalColorErrorDark if theme == 'dark' else terminalColorErrorLight)
		Logging.terminalStyleRGBTupple = ( Logging.terminalStyle.color.triplet.red, Logging.terminalStyle.color.triplet.green, Logging.terminalStyle.color.triplet.blue )


	@staticmethod
	def configUpdate(name:str, 
					 key:Optional[str] = None, 
					 value:Optional[Any] = None) -> None:
		"""	Handle configuration update.
		"""
		restartNeeded = False
		if key.startswith('logging.'):
			# No special action needed
			if key in [ 'logging.enableScreenLogging', 
			  			'logging.stackTraceOnError',
						'logging.enableBindingsLogging' ]:
				return
			
			# Use the log level function to perform extra actions
			if key == 'logging.level':
				Logging.setLogLevel(cast(LogLevel, Configuration.logging_level))
				return 

			restartNeeded = True

		# Check console theme color		
		restartNeeded = True if key == 'cse.logging.theme' else restartNeeded
			
		if restartNeeded:
			# Otherwise a restart of the log system is needed
			Logging.logDebug('Restarting Logging')
			Logging.finit()
			Logging.init()
		
	
	@staticmethod
	def finit() -> None:
		"""	End logging.
		"""
		from ..etc.DateUtils import waitFor
		if Logging.queue:
			waitFor(5.0, Logging.queue.empty)
		if Logging._logWorker:
			Logging._logWorker.stop()
		Logging.log('')
		if Logging.logger:
			Logging.logger.handlers.clear()
		if Logging._handlers:
			Logging._handlers.clear()
		Logging.logger = None


	@staticmethod
	def _logMessageToLoggerConsole(level:int, msg:str, caller:inspect.Traceback, threadName:str) -> None:
		if isinstance(msg, str):
			
			# optimize determining the source file's basename
			if not (basename := Logging._basenames.get(caller.filename)):
				basename = os.path.basename(caller.filename)
				Logging._basenames[caller.filename] = basename

			Logging.loggerConsole.log(level, f'{basename}\x04{caller.lineno}\x04{threadName:<10.10}\x04{msg}')
		else:
			try:
				richInspect(msg, private = True, docs = False, dunder = False)
			except:
				pass
			
	@staticmethod
	def loggingActor() -> bool:
		while Logging._logWorker.running:
			# Check queue and give up the CPU
			if Logging.queue.empty():
				time.sleep(0.1)
				continue
			level, msg, caller, threadName = Logging.queue.get(block = True)
			# if msg is None or (isinstance(msg, str) and not len(msg)):
			if msg is None:
				continue
			Logging._logMessageToLoggerConsole(level, msg, caller, threadName)

		return True


	@staticmethod
	def log(msg:Any, stackOffset:Optional[int] = 0) -> str:
		"""Print a log message with log-level **INFO**. 

			Args:
				msg: The log message.
				stackOffset: Optional offset for printing stacktraces.
			Return:
				Return the log *msg* again. 
		"""
		return Logging._log(logging.INFO, msg, stackOffset = stackOffset)


	@staticmethod
	def logDebug(msg:Any, stackOffset:Optional[int] = 0) -> str:
		"""Print a log message with log-level **DEBUG**. 

			Args:
				msg: The log message.
				stackOffset: Optional offset for printing stacktraces.
			Return:
				Return the log *msg* again. 
		"""
		return Logging._log(logging.DEBUG, msg, stackOffset = stackOffset)


	@staticmethod
	def logErr(msg:Any, 
			   showStackTrace:Optional[bool] = True, 
			   exc:Optional[Exception] = None, 
			   stackOffset:Optional[int] = 0) -> str:
		"""	Print a log message with log-level **ERROR**. 

			Args:
				msg: The log message.
				showStackTrace: Optional indicates whether a stacktrace shall be logged 
					together with the error	as well.
				exc: Optional exception to log.
				stackOffset: Optional offset for printing stacktraces.
			Return:
				Return the log *msg* again. 
		"""
		from ..runtime import CSE
		# raise logError event
		Logging._eventLogError()

		if exc:
			fmtexc = ''.join(traceback.TracebackException.from_exception(exc).format())
			return Logging._log(logging.ERROR, f'{msg}\n\n{fmtexc}', stackOffset = stackOffset)
		elif showStackTrace and Logging.stackTraceOnError:
			strace = ''.join(map(str, traceback.format_stack()[:-1]))
			return Logging._log(logging.ERROR, f'{msg}\n\n{strace}', stackOffset = stackOffset)
		else:
			return Logging._log(logging.ERROR, msg, stackOffset = stackOffset)


	@staticmethod
	def logWarn(msg:Any, stackOffset:Optional[int] = 0) -> str:
		"""	Print a log message with log-level **WARNING**. 

			Args:
				msg: The log message.
				stackOffset: Optional offset for printing stacktraces.
			Return:
				Return the log *msg* again. 
		"""
		from ..runtime import CSE as CSE
		# raise logWarning event
		Logging._eventLogWarning()
		return Logging._log(logging.WARNING, msg, stackOffset = stackOffset)


	@staticmethod
	def logWithLevel(level:int, msg:Any, 
								showStackTrace:Optional[bool] = False, 
								stackOffset:Optional[int] = 0) -> str:
		"""	Fallback log method when the *level* is a directly given  argument.
		# TODO
		"""
		# TODO add a parameter frame substractor to correct the line number, here and in In _log()
		# TODO change to match in Python10
		match level:
			case logging.DEBUG:
				return Logging.logDebug(msg, stackOffset = stackOffset)
			case logging.INFO:
				return Logging.log(msg, stackOffset = stackOffset)
			case logging.WARNING:
				return Logging.logWarn(msg, stackOffset = stackOffset)
			case logging.ERROR:
				return Logging.logErr(msg, showStackTrace = showStackTrace, stackOffset = stackOffset)
			case _:
				return msg


	@staticmethod
	def logDivider(level:Optional[int] = None, message:Optional[str] = '') -> None:
		"""	Add a divider line to the log.
		
			Args:
				level: Loglevel for the message. If None, the the current log level is taken
				message: Optional message that is centered on the line.
		"""
		message = f'[ {message} ]' if message else ''	# add spaces if there is a message
		ln  = '=' * int((Logging.consoleWidth() - 50 - len(message)) / 2)
		Logging.logWithLevel(level if level is not None else Logging.logLevel, 
							 f'{ln}{message}{ln}')


	@staticmethod
	def logRequest(result:Result, data:bytes|JSON) -> None:
		"""	Log request.

			Args:
				result: The result of the request.
				data: The request data. Either bytes or JSON dictionary.
		"""

		if result.request.originalRequest:
			Logging.isDebug and Logging.logDebug(f'Operation: {result.request.originalRequest.get("op")}')
		# data = data if isinstance(data, bytes) else json.dumps(data, indent = 2).encode()
		if result.request.ct == ContentSerializationType.JSON:
			# Logging.isDebug and Logging.logDebug(f'Body: \n{cast(str, data.decode())}')
			Logging.isDebug and Logging.logDebug(f'Body: \n{cast(str, data)}')
		else:
			Logging.isDebug and Logging.logDebug(f'Body: \n{TextTools.toHex(cast(bytes, data))}')
			if result.request.originalRequest:
				Logging.isDebug and Logging.logDebug(f'=>\n{result.request.originalRequest}')
			# Logging.isDebug and Logging.logDebug(f'Body: \n{TextTools.toHex(cast(bytes, data))}\n=>\n{result.request.originalRequest}')


	@staticmethod
	def _log(level:int, msg:Any, stackOffset:Optional[int] = 0, immediate:Optional[bool] = False) -> str:
		"""	Internally adding various information to the log output. 
		
			The *stackOffset* is used to determine the correct caller. 
			It is set by a calling method in case the log information are re-routed.

			Args:
				level: The log level.
				msg: The log message.
				stackOffset: Optional offset in the stack frame.
				immediate: Immediately log the message, don't put it into the log queue.
			
			Return:
				The log *msg*.
		"""
		if Logging.logLevel <= level:
			try:
				# Queue a log message : (level, message, caller from stackframe, current thread)
				caller = inspect.getframeinfo(inspect.stack()[stackOffset + 2][0])
				thread = threading.current_thread()
				if isinstance(msg, str) and Logging.maxLogMessageLength:
					msg = msg[:Logging.maxLogMessageLength]	# truncate message if necessary
				if Logging.enableQueue and not immediate:
					Logging.queue.put((level, msg, caller, thread.name))
				else:
					Logging._logMessageToLoggerConsole(level, msg, caller, thread.name)
			except Exception as e:
				print(e)
				# sometimes this raises an exception. Just ignore it.
				pass
		return msg


	@staticmethod
	def console(msg:Union[str, Text, Tree, Table, JSON] = '&nbsp;', 
				nl:Optional[bool] = False, 
				nlb:Optional[bool] = False, 
				end:Optional[str] = '\n', 
				plain:Optional[bool] = False, 
				isError:Optional[bool] = False, 
				isHeader:Optional[bool] = False) -> str:
		"""	Print a message or object to the console.
		"""
		# if this is a header then call the method again with different parameters
		if isHeader:
			return Logging.console(f'**{msg}**', nlb = True, nl = True)

		style = Logging.terminalStyle if not isError else Logging.terminalStyleError
		if nlb:	# Empty line before
			Logging._console.print()
		
		match msg:
			case str():
				_msg = msg if plain else Markdown(msg)
				Logging._console.print(_msg, style = style, end = end, highlight = False)
				result = str(_msg)
			case dict() | Tree() | Table() | Text():
				Logging._console.print(msg, style = style, end = end)
				result = str(msg)
			case _:
				_msg = str(msg)
				Logging._console.print(_msg, style = style, end = end)
				result = _msg
		if nl:	# Empty line after
			Logging._console.print()
		
		return result


	@staticmethod
	def consoleSyntax(code:str, language:str) -> None:
		"""	Print a piece of code or data with syntax highlighting to the console.
			This function does not format the code.

			Args:
				code: A string with formatted code or data.
				language: The language or type of data.
		"""
		Logging._console.print(Syntax(code, language))
	

	@staticmethod
	def consoleClear() -> None:
		"""	Clear the console screen.
		"""
		Logging._console.clear()


	@staticmethod
	def consoleStatusWait(msg:str) -> Status:
		"""	Return and show a progress spinner and message while waiting for a block to complete.
		
			Example:
				
				with consoleStatusWait('waiting...'):
					. . .
			
			Args:
				msg: Message to display
			Return:
				Status object.
				
		"""
		return Logging._console.status(f'[{Logging.terminalStyle}]{msg}', spinner_style = terminalColorDark)
	

	@staticmethod
	def consolePrompt(prompt:str, 
					  nl:Optional[bool] = True, 
					  default:Optional[str] = None) -> str:
		"""	Read a line from the console. 
			Catch EOF (^D) and Keyboard Interrup (^C). In that case None is returned.
		"""
		answer = None
		try:
			answer = Prompt.ask(f'[{Logging.terminalStyle}]{prompt}', console = Logging._console, default = default)
			if nl:
				Logging.console()
		except KeyboardInterrupt as e:
			pass
		except Exception:
			pass
		return answer
	

	@staticmethod
	def consoleWidth() -> int:
		"""	Return the current console width.
		"""
		return Logging._console.width

	
	@staticmethod
	def inspect(obj:Any, immediate:bool = False) -> None:
		"""	Output a very comprehensive description of an object.
		
			Args:
				obj: The object to inspect.
				immediate: Immediately log the message, don't put it into the log queue.
		"""
		if Logging.logLevel != LogLevel.OFF:
			Logging._log(Logging.logLevel, obj, immediate = immediate)
	

	@staticmethod
	def stacktrace(startFrame:Optional[int] = -10, 
				   skipEndFrames:Optional[int] = 1) -> None:
		"""	Output the current stacktrace to the log.
		
			Args:
				startFrame: Skip over a number of uninteresting frames at the beginning of the stack trace. The default is -10, meaning only log the last 10 stack frames.
				skipEndFrames: Number of stack frames to skip at the end of the stack trace. The default of 1 means to ignore the call to this logging function.
		"""
		if Logging.logLevel != LogLevel.OFF:
			Logging._log(Logging.logLevel, ''.join(map(str, traceback.format_stack()[startFrame:-skipEndFrames])), immediate = False)


	@staticmethod
	def off() -> None:
		"""	Switch logging off. Remember the last logLevel
		"""
		if Logging.logLevel != LogLevel.OFF:
			Logging.lastLogLevel = Logging.logLevel
			Logging.setLogLevel(LogLevel.OFF)


	@staticmethod
	def on() -> None:
		"""	Switch logging on. Enable the last logLevel.
		"""
		if Logging.logLevel == LogLevel.OFF and Logging.lastLogLevel:
			Logging.setLogLevel(Logging.lastLogLevel)
			Logging.lastLogLevel = None
	

	@staticmethod
	def setEnableScreenLogging(value:bool) -> None:
		"""	Set the `enableScreenLogging` attribute via a method call.
		
			Args:
				value: New value for `enableScreenLogging`.
		"""
		Logging.enableScreenLogging = value


	@staticmethod
	def setLogLevel(logLevel:LogLevel) -> None:
		"""	Set a new log level to the logging system.

			Args:
				logLevel: New log level
		"""
		Logging.logLevel = logLevel
		Logging.loggerConsole.setLevel(logLevel)

		# Set the is... indicators for optimizing the log output
		Logging.isDebug = Logging.logLevel <= LogLevel.DEBUG
		Logging.isInfo 	= Logging.logLevel <= LogLevel.INFO
		Logging.isWarn	= Logging.logLevel <= LogLevel.WARNING


	@staticmethod
	def queueOff() -> None:
		"""	Disable the logging queue. This can be used to get immediate
			feedback, e.g during startup.
		"""
		Logging.enableQueue = False
	

	@staticmethod
	def queueOn() -> None:
		"""	Enable the logging queue. Whether the usage of the queue really happens
			depends on the configured queue size.
		"""
		Logging.enableQueue = Logging.queueSize > 0


#
#	Redirect handler to support Rich formatting
#

class ACMERichLogHandler(RichHandler):

	__slots__ = (
		'_fromtimestamp',
	)


	_levels = {
		'DEBUG': Text(f'{"DEBUG":<7}', style='DEBUG'),
		'INFO': Text(f'{"INFO":<7}', style='INFO'),
		'WARNING': Text(f'{"WARNING":<7}', style='WARNING'),
		'ERROR': Text(f'{"ERROR":<7}', style='ERROR'),
	}

	def __init__(self, level: int = logging.NOTSET) -> None:

		# Add own styles to the default styles and create a new theme for the console
		ACMEStyles = { 
			'repr.dim' 				: Style(color = 'grey70', dim = True),
			'repr.request'			: Style(color = 'spring_green2'),
			'repr.response'			: Style(color = 'magenta2'),
			'repr.id'				: Style(color = 'light_sky_blue1'),
			'repr.url'				: Style(color = 'sandy_brown', underline = True),
			'repr.start'			: Style(color = 'orange1'),
			'DEBUG'					: Style(color = 'grey50'),
			'WARNING'				: Style(color = 'orange3'),
			'ERROR'					: Style(color = 'red', reverse = True),
			'INFO'					: Style(color = 'blue'),
			'logging.console'		: Style(color = 'spring_green2'),
		}
		_styles = DEFAULT_STYLES.copy()
		_styles.update(ACMEStyles)

		super().__init__(level = level, console = Console(theme = Theme(_styles)))


		# Set own highlights 
		self.highlighter.highlights = [	# type: ignore
			# r"(?P<brace>[\{\[\(\)\]\}])",
			#r"(?P<tag_start>\<)(?P<tag_name>\w*)(?P<tag_contents>.*?)(?P<tag_end>\>)",
			#r"(?P<attrib_name>\w+?)=(?P<attrib_value>\"?\w+\"?)",
			#r"(?P<bool_true>True)|(?P<bool_false>False)|(?P<none>None)",
			r"(?P<none>None)",
			#r"(?P<id>(?<!\w)\-?[0-9]+\.?[0-9]*\b)",
			# r"(?P<number>\-?[0-9a-f])",
			r"(?P<number>\-?0x[0-9a-f]+)",
			#r"(?P<filename>\/\w*\.\w{3,4})\s",
			r"(?<!\\)(?P<str>b?\'\'\'.*?(?<!\\)\'\'\'|b?\'.*?(?<!\\)\'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
			#r"(?P<id>[\w\-_.]+[0-9]+\.?[0-9])",		# ID
			r"(?P<url>https?:\/\/[0-9a-zA-Z\$\-\_\~\+\!`\(\)\,\.\?\/\;\:\&\=\%]*)",
			#r"(?P<uuid>[a-fA-F0-9]{8}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{12})",

			# r"(?P<dim>^[0-9]+\.?[0-9]*\b - )",			# thread ident at front
			r"(?P<dim>^[^ ]*[ ]*- )",						# thread ident at front
			r"(?P<request>==>.*:)",							# Incoming request or response
			r"(?P<request>[^-]+Request ==>:)",				# Outgoing request or response
			r"(?P<response><== [^:]+[(:]+)",				# outgoing response or request
			r"(?P<response>[^-]+Response <== [^ :]+[ :]+)",		# Incoming response or request
			r"(?P<number>\(RSC: [0-9]+\.?[0-9]\))",			# Result code
			#r"(?P<id> [\w/\-_]*/[\w/\-_]+)",				# ID
			r"(?P<number>\n(?:Headers|Options|Body|Operation|Payload): )",
			r"(?P<number> \- (?:Operation|Headers|Body|Payload|Source): )",
			# r"(?P<number>\nBody: )",
			# r"(?P<number> \- Body: )",
			# r"(?P<number> \- Operation: )",
			r"(?P<start>=+[^=]*=+$)",

			# r"(?P<request>CSE started$)",					# CSE startup message
			# r"(?P<request>CSE shutdown$)",					# CSE shutdown message
			# r"(?P<start>CSE shutting down$)",				# CSE shutdown message
			# r"(?P<start>Starting CSE$)",				# CSE shutdown message

			#r"(?P<id>(acp|ae|bat|cin|cnt|csest|dvi|grp|la|mem|nod|ol|sub)[0-9]+\.?[0-9])",		# ID

		]

		# Set the time conversion function, depending on the setting of UTC time
		if Logging.utcTime:
			self._fromtimestamp = lambda t : datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc)
		else:
			self._fromtimestamp = datetime.datetime.fromtimestamp


		
	def emit(self, record:LogRecord) -> None:
		"""	Invoked by logging. """
		if not Logging.enableScreenLogging:
			return
		
		message	= self.format(record)
		if len(messageElements := message.split('\x04', 3)) == 4:
			path 	= messageElements[0]
			lineno 	= int(messageElements[1])
			threadID= messageElements[2]
			message = messageElements[3]
		else:
			path	= record.filename
			lineno	= record.lineno
			threadID= f'{record.threadName:<10.10}'

		self.console.print(
			self._log_render(
				self.console,
				[ self.highlighter(Text(f'{threadID} - {message}')) ],
				log_time	= self._fromtimestamp(record.created),	# type: ignore[no-untyped-call]
				# time_format	= None if self.formatter is None else self.formatter.datefmt,
				time_format	= self.formatter.datefmt,
				# level		= Text(f'{record.levelname:<7}', style=record.levelname),
				level		= self._levels[record.levelname],
				path		= path,
				line_no		= lineno,
			)
		)
