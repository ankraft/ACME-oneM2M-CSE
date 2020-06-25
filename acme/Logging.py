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

import logging, logging.handlers, os, inspect, re, sys, datetime, time, threading, queue
from logging import StreamHandler, LogRecord
from pathlib import Path
from Configuration import Configuration
from rich.logging import RichHandler
from rich.highlighter import ReprHighlighter
from rich.style import Style
from rich.console import Console
from rich.text import Text


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

	logger  			= None
	loggerConsole		= None
	logLevel 			= logging.INFO
	loggingEnabled		= True
	enableFileLogging	= True
	worker 				= None
	queue 				= None

	checkInterval 		= 0.2		# wait (in s) between checks of the logging queue
	queueMaxsize 		= 1000		# max number of items in the logging queue. Might otherwise grow forever on large load

	@staticmethod
	def init():
		"""Init the logging system.
		"""

		if Logging.logger is not None:
			return
		Logging.enableFileLogging 	= Configuration.get('logging.enableFileLogging')
		Logging.logLevel 			= Configuration.get('logging.level')
		Logging.loggingEnabled		= Configuration.get('logging.enable')
		Logging.logger				= logging.getLogger('logging')			# general logger
		Logging.loggerConsole		= logging.getLogger('rich')				# Rich Console logger
		Logging.checkInterval

		# Add logging queue
		Logging.queue = queue.Queue(maxsize=Logging.queueMaxsize)

		# List of log handlers
		handlers = [ ACMERichLogHandler() ]

		# Log to file only when file logging is enabled
		if Logging.enableFileLogging:
			logfile = Configuration.get('logging.file')
			os.makedirs(os.path.dirname(logfile), exist_ok=True)# create log directory if necessary
			logfp = logging.handlers.RotatingFileHandler(logfile,
														 maxBytes=Configuration.get('logging.size'),
														 backupCount=Configuration.get('logging.count'))
			logfp.setLevel(Logging.logLevel)
			logfp.setFormatter(logging.Formatter('%(levelname)s %(asctime)s %(message)s'))
			Logging.logger.addHandler(logfp) 
			handlers.append(logfp)

		# config the logging system
		logging.basicConfig(level=Logging.logLevel, format='%(message)s', datefmt='[%X]', handlers=handlers)

		# Start worker to handle logs in the background
		from helpers import BackgroundWorker
		Logging.worker = BackgroundWorker.BackgroundWorker(Logging.checkInterval, Logging.loggingWorker, 'loggingWorker')
		Logging.worker.start()
	


	@staticmethod
	def finit():
		if Logging.worker is not None:
			while not Logging.queue.empty():
				time.sleep(0.5)
			Logging.worker.stop()


	@staticmethod
	def loggingWorker():
		while not Logging.queue.empty():
			level, msg, caller, thread = Logging.queue.get()
			Logging.loggerConsole.log(level, '%s*%d*%d*%s', os.path.basename(caller.filename), caller.lineno, thread.native_id, msg)
		return True


	@staticmethod
	def log(msg: str):
		"""Print a log message with level INFO. """
		Logging._log(logging.INFO, msg)


	@staticmethod
	def logDebug(msg : str):
		"""Print a log message with level DEBUG. """
		Logging._log(logging.DEBUG, msg)


	@staticmethod
	def logErr(msg : str):
		"""Print a log message with level ERROR. """
		import CSE
		(not CSE.event or CSE.event.logError())	# raise logError event
		Logging._log(logging.ERROR, msg)


	@staticmethod
	def logWarn(msg : str):
		"""Print a log message with level WARNING. """
		import CSE
		(not CSE.event or CSE.event.logWarning())	# raise logWarning event
		Logging._log(logging.WARNING, msg)


	@staticmethod
	def _log(level : int, msg : str):
		if Logging.loggingEnabled and Logging.logLevel <= level:
			# Queue a log message : (level, message, caller from stackframe, current thread)
			Logging.queue.put((level, msg, inspect.getframeinfo(inspect.stack()[2][0]), threading.current_thread()))


#
#	Redirect handler to redirect other log output to our log
#

class RedirectHandler(StreamHandler):

	def __init__(self, topic):
		StreamHandler.__init__(self)
		self.topic = topic

	def emit(self, record):
		msg = '(%s) %s' % (self.topic, record.getMessage())
		msg = re.sub(r'\[.+?\] ', '', msg) # clean up (remove superflous date and time)

		(record.levelno == logging.DEBUG 	and Logging.logDebug(msg, False))
		(record.levelno == logging.INFO 	and Logging.log(msg, False))
		(record.levelno == logging.WARNING 	and Logging.logWarn(msg, False))
		(record.levelno == logging.ERROR 	and Logging.logErr(msg, False))



#
#	Redirect handler to support Rich formatting
#

class ACMERichLogHandler(RichHandler):

	def __init__(self, level: int = logging.NOTSET, console: Console = None) -> None:
		super().__init__(level=level)

		# Add own styles to the current console object's styles
		self.console._styles['repr.dim'] = Style(color='grey70', dim=True)
		self.console._styles['repr.request'] = Style(color='spring_green2')
		self.console._styles['repr.response'] = Style(color='magenta2')
		self.console._styles['repr.id'] = Style(color='light_sky_blue1')
		self.console._styles['repr.url'] = Style(color='sandy_brown', underline=True)
		self.console._styles['logging.level.debug'] = Style(color='grey50')
		self.console._styles['logging.level.warning'] = Style(color='orange3')
		self.console._styles['logging.level.error'] = Style(color='red', reverse=True)


		# Set own highlights 
		self.highlighter.highlights = [
			r"(?P<brace>[\{\[\(\)\]\}])",
			#r"(?P<tag_start>\<)(?P<tag_name>\w*)(?P<tag_contents>.*?)(?P<tag_end>\>)",
			#r"(?P<attrib_name>\w+?)=(?P<attrib_value>\"?\w+\"?)",
			r"(?P<bool_true>True)|(?P<bool_false>False)|(?P<none>None)",
			r"(?P<id>(?<!\w)\-?[0-9]+\.?[0-9]*\b)",
			r"(?P<number>0x[0-9a-f]*)",
			#r"(?P<filename>\/\w*\.\w{3,4})\s",
			r"(?<!\\)(?P<str>b?\'\'\'.*?(?<!\\)\'\'\'|b?\'.*?(?<!\\)\'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
			r"(?P<id>[\w\-_.]+[0-9]+\.?[0-9])",		# ID
			r"(?P<url>https?:\/\/[0-9a-zA-Z\$\-\_\~\+\!`\(\)\,\.\?\/\;\:\&\=\%]*)",
			#r"(?P<uuid>[a-fA-F0-9]{8}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{4}\-[a-fA-F0-9]{12})",

			r"(?P<dim>^[0-9]+\.?[0-9]*\b - )",		# thread ident at front
			r"(?P<request>==>.*:)",					# Incoming request 
			r"(?P<response><== [^ ]+ )",			# outgoing response
			r"(?P<number>\(RSC: [0-9]+\.?[0-9]\))",	# Result code
			r"(?P<id> [\w/\-_]*/[\w/\-_]+)",		# ID
			#r"(?P<id>(acp|ae|bat|cin|cnt|csest|dvi|grp|la|mem|nod|ol|sub)[0-9]+\.?[0-9])",		# ID

		]
		

	def emit(self, record: LogRecord) -> None:
		"""Invoked by logging."""
		#path = Path(record.pathname).name
		log_style = f"logging.level.{record.levelname.lower()}"
		message = self.format(record)
		path = ''
		lineno = 0
		threadID = 0
		if len(messageElements := message.split('*', 3)) == 4:
			path = messageElements[0]
			lineno = messageElements[1]
			threadID = messageElements[2]
			message = messageElements[3]
		time_format = None if self.formatter is None else self.formatter.datefmt
		log_time = datetime.datetime.fromtimestamp(record.created)

		level = Text()
		level.append(record.levelname, log_style)
		# message_text = Text("%d - %s" %(threading.current_thread().native_id, message))
		message_text = Text("%s - %s" %(threadID, message))
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