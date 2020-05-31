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

import logging, logging.handlers, os, inspect, re, sys, datetime
from logging import StreamHandler, LogRecord
from pathlib import Path
from Configuration import Configuration
from rich.logging import RichHandler
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

	@staticmethod
	def init():
		"""Init the logging system.
		"""

		if Logging.logger is not None:
			return
		Logging.enableFileLogging 	= Configuration.get('logging.enableFileLogging')
		Logging.logLevel 			= Configuration.get('logging.level')
		Logging.loggingEnabled		= Configuration.get('logging.enable')
		Logging.logger				= logging.getLogger('logging')
		Logging.loggerConsole		= logging.getLogger("rich")

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

		logging.basicConfig(level=Logging.logLevel, format='%(message)s', datefmt='[%X]', handlers=[ACMERichHandler(), logfp])

	

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
		try:
			if Logging.loggingEnabled and Logging.logLevel <= level:
				Logging.loggerConsole.log(level, msg)
		except:
			pass


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

class ACMERichHandler(RichHandler):

	def __init__(self, level: int = logging.NOTSET, console: Console = None) -> None:
		super().__init__(level=level)


	def emit(self, record: LogRecord) -> None:
		"""Invoked by logging."""
		path = Path(record.pathname).name
		log_style = f"logging.level.{record.levelname.lower()}"
		message = self.format(record)
		time_format = None if self.formatter is None else self.formatter.datefmt
		log_time = datetime.datetime.fromtimestamp(record.created)

		level = Text()
		level.append(record.levelname, log_style)
		message_text = Text(message)
		message_text.highlight_words(self.KEYWORDS, "logging.keyword")
		message_text = self.highlighter(message_text)

		# find caller on the stack
		caller = inspect.getframeinfo(inspect.stack()[8][0])

		self.console.print(
			self._log_render(
				self.console,
				[message_text],
				log_time=log_time,
				time_format=time_format,
				level=level,
				path=os.path.basename(caller.filename),
				line_no=caller.lineno,
			)
		)