#
#	Logging.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Wrapper for the logging sub-system. It provides simpler access as well
#	some more usefull output rendering.
#

"""	Wrapper class for the logging subsystem. """

import traceback
import logging, logging.handlers, os, inspect, re, sys, datetime, time, threading, queue
from typing import List, Any, Union
from logging import StreamHandler, LogRecord
from pathlib import Path
from Configuration import Configuration
from Types import JSON
from rich.logging import RichHandler
from rich.highlighter import ReprHighlighter
from rich.style import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
from rich.default_styles import DEFAULT_STYLES
from rich.theme import Theme
from rich.tree import Tree
from rich.table import Table


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

class	Logging:
	""" Wrapper class for the logging subsystem. This class wraps the 
		initialization of the logging subsystem and provides convenience 
		methods for printing log, error and warning messages to a 
		logfile and to the console.
	"""
	INFO 	= logging.INFO
	DEBUG 	= logging.DEBUG
	ERROR 	= logging.ERROR
	WARNING = logging.WARNING

	logLevelNames = {
		INFO    : 'INFO',
		DEBUG   : 'DEBUG',
		ERROR   : 'ERROR',
		WARNING : 'WARNING',
	}

	logger  			= None
	loggerConsole		= None
	logLevel 			= logging.INFO
	loggingEnabled		= True
	enableFileLogging	= True
	enableScreenLogging	= True
	stackTraceOnError	= True
	worker 				= None
	queue 				= None

	checkInterval:float	= 0.2		# wait (in s) between checks of the logging queue
	queueMaxsize:int	= 1000		# max number of items in the logging queue. Might otherwise grow forever on large load

	_console			= None
	_handlers:List[Any] = None

	@staticmethod
	def init() -> None:
		"""Init the logging system.
		"""

		if Logging.logger is not None:
			return
		Logging.enableFileLogging 	= Configuration.get('logging.enableFileLogging')
		Logging.enableScreenLogging	= Configuration.get('logging.enableScreenLogging')
		Logging.logLevel 			= Configuration.get('logging.level')
		Logging.loggingEnabled		= Configuration.get('logging.enable')
		Logging.stackTraceOnError	= Configuration.get('logging.stackTraceOnError')

		Logging.logger				= logging.getLogger('logging')			# general logger
		Logging.loggerConsole		= logging.getLogger('rich')				# Rich Console logger
		Logging._console			= Console()								# Console object

		# Add logging queue
		Logging.queue = queue.Queue(maxsize=Logging.queueMaxsize)

		# List of log handlers
		Logging._handlers = [ ACMERichLogHandler() ]

		# Log to file only when file logging is enabled
		if Logging.enableFileLogging:
			import Utils, CSE

			logpath = Configuration.get('logging.path')
			os.makedirs(logpath, exist_ok=True)# create log directory if necessary
			logfile = f'{logpath}/cse-{CSE.cseType.name}.log'
			logfp = logging.handlers.RotatingFileHandler(logfile,
														 maxBytes=Configuration.get('logging.size'),
														 backupCount=Configuration.get('logging.count'))
			logfp.setLevel(Logging.logLevel)
			logfp.setFormatter(logging.Formatter('%(levelname)s %(asctime)s %(message)s'))
			Logging.logger.addHandler(logfp) 
			Logging._handlers.append(logfp)

		# config the logging system
		logging.basicConfig(level=Logging.logLevel, format='%(message)s', datefmt='[%X]', handlers=Logging._handlers)

		# Start worker to handle logs in the background
		from helpers.BackgroundWorker import BackgroundWorkerPool
		BackgroundWorkerPool.newWorker(Logging.checkInterval, Logging.loggingWorker, 'loggingWorker').start()
	
	
	@staticmethod
	def finit() -> None:
		if Logging.queue is not None:
			while not Logging.queue.empty():
				time.sleep(0.5)
		from helpers.BackgroundWorker import BackgroundWorkerPool
		BackgroundWorkerPool.stopWorkers('loggingWorker')


	@staticmethod
	def loggingWorker() -> bool:
		while Logging.queue is not None and not Logging.queue.empty():
			level, msg, caller, thread = Logging.queue.get()
			Logging.loggerConsole.log(level, '%s*%d*%-10.10s*%s', os.path.basename(caller.filename), caller.lineno, thread.name, msg)
		return True


	@staticmethod
	def log(msg:str) -> None:
		"""Print a log message with level INFO. """
		Logging._log(logging.INFO, msg)


	@staticmethod
	def logDebug(msg:str) -> None:
		"""Print a log message with level DEBUG. """
		Logging._log(logging.DEBUG, msg)


	@staticmethod
	def logErr(msg:str) -> None:
		"""Print a log message with level ERROR. """
		import CSE
		# raise logError event
		(not CSE.event or CSE.event.logError())	# type: ignore
		if Logging.stackTraceOnError:
			strace = ''.join(map(str, traceback.format_stack()[:-1]))
			Logging._log(logging.ERROR, f'{msg}\n\n{strace}')
		else:
			Logging._log(logging.ERROR, msg)


	@staticmethod
	def logWarn(msg:str) -> None:
		"""Print a log message with level WARNING. """
		import CSE
		# raise logWarning event
		(not CSE.event or CSE.event.logWarning()) 	# type: ignore
		Logging._log(logging.WARNING, msg)


	@staticmethod
	def _log(level:int, msg:str) -> None:
		if Logging.loggingEnabled and Logging.logLevel <= level and Logging.queue is not None:
			# Queue a log message : (level, message, caller from stackframe, current thread)
			try:
				Logging.queue.put((level, str(msg), inspect.getframeinfo(inspect.stack()[2][0]), threading.current_thread()))
			except Exception as e:
				# sometimes this raises an exception. Just ignore it.
				pass
	

	@staticmethod
	def console(msg:Union[str, Tree, Table, JSON]='&nbsp;', extranl:bool=False, end:str='\n', plain:bool=False, isError:bool=False) -> None:
		style = Style(color='spring_green2') if not isError else Style(color='red')
		if extranl:
			Logging._console.print()
		if isinstance(msg, str):
			Logging._console.print(msg if plain else Markdown(msg), style=style, end=end)
		elif isinstance(msg, dict):
			Logging._console.print(msg, style=style, end=end)
		elif isinstance(msg, (Tree, Table)):
			Logging._console.print(msg, style=style, end=end)

		if extranl:
			Logging._console.print()
	

	@staticmethod
	def consoleClear() -> None:
		"""	Clear the console screen.
		"""
		Logging._console.clear()


#
#	Redirect handler to support Rich formatting
#

class ACMERichLogHandler(RichHandler):

	def __init__(self, level: int = logging.NOTSET, console: Console = None) -> None:

		# Add own styles to the default styles and create a new theme for the console
		ACMEStyles = { 
			'repr.dim' 				: Style(color='grey70', dim=True),
			'repr.request'			: Style(color='spring_green2'),
			'repr.response'			: Style(color='magenta2'),
			'repr.id'				: Style(color='light_sky_blue1'),
			'repr.url'				: Style(color='sandy_brown', underline=True),
			'repr.start'			: Style(color='orange1'),
			'logging.level.debug'	: Style(color='grey50'),
			'logging.level.warning'	: Style(color='orange3'),
			'logging.level.error'	: Style(color='red', reverse=True),
			'logging.console'		: Style(color='spring_green2'),
		}
		_styles = DEFAULT_STYLES.copy()
		_styles.update(ACMEStyles)

		super().__init__(level=level, console=Console(theme=Theme(_styles)))


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
			r"(?P<request>Request ==>:)",					# Outgoing request or response
			r"(?P<response><== [^ :]+[ :]+)",				# outgoing response or request
			r"(?P<response>Response <== [^ :]+[ :]+)",		# Incoming response or request
			r"(?P<number>\(RSC: [0-9]+\.?[0-9]\))",			# Result code
			#r"(?P<id> [\w/\-_]*/[\w/\-_]+)",				# ID
			r"(?P<number>\nHeaders: )",
			r"(?P<number> \- Headers: )",
			r"(?P<number>\nBody: )",
			r"(?P<number> \- Body: )",
			# r"(?P<request>CSE started$)",					# CSE startup message
			# r"(?P<request>CSE shutdown$)",					# CSE shutdown message
			# r"(?P<start>CSE shutting down$)",				# CSE shutdown message
			# r"(?P<start>Starting CSE$)",				# CSE shutdown message

			#r"(?P<id>(acp|ae|bat|cin|cnt|csest|dvi|grp|la|mem|nod|ol|sub)[0-9]+\.?[0-9])",		# ID

		]
		
	def emit(self, record:LogRecord) -> None:
		"""Invoked by logging."""
		if not Logging.enableScreenLogging or not Logging.loggingEnabled or record.levelno < Logging.logLevel:
			return
		#path = Path(record.pathname).name
		log_style = f"logging.level.{record.levelname.lower()}"
		message = self.format(record)
		path  = ''
		lineno = 0
		threadID = ''
		if len(messageElements := message.split('*', 3)) == 4:
			path = messageElements[0]
			lineno = int(messageElements[1])
			threadID = messageElements[2]
			message = messageElements[3]
		time_format = None if self.formatter is None else self.formatter.datefmt
		log_time = datetime.datetime.fromtimestamp(record.created)

		level = Text()
		level.append(f'{record.levelname:<7}', log_style)	# add trainling spaces to level name for a bit nicer formatting
		message_text = Text(f'{threadID} - {message}')
		message_text = self.highlighter(message_text)

		# # find caller on the stack
		# caller = inspect.getframeinfo(inspect.stack()[8][0])

		self.console.print(
			self._log_render(
				self.console,
				[message_text],
				log_time=log_time,
				time_format=time_format,
				level=level,
				path=path,
				line_no=lineno,
			)
			# self._log_render(
			# 	self.console,
			# 	[message_text],
			# 	log_time=log_time,
			# 	time_format=time_format,
			# 	level=level,
			# 	path=os.path.basename(caller.filename),
			# 	line_no=caller.lineno,
			# )
		)


