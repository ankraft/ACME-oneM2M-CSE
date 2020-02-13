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

import logging, logging.handlers, os, inspect, re, sys, datetime#
from logging import StreamHandler
from Configuration import Configuration

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

		# Log to file only when file logging is enabled
		if Logging.enableFileLogging:
			logfile = Configuration.get('logging.file')
			os.makedirs(os.path.dirname(logfile), exist_ok=True)# create log directory if necessary
			logfp				= logging.handlers.RotatingFileHandler( logfile,
																		maxBytes=Configuration.get('logging.size'),
																		backupCount=Configuration.get('logging.count'))
			logfp.setLevel(Logging.logLevel)
			logfp.setFormatter(logging.Formatter('%(levelname)s %(asctime)s %(message)s'))
			Logging.logger.addHandler(logfp) 

		Logging.logger.setLevel(Logging.logLevel)

	

	@staticmethod
	def log(msg, withPath=True):
		"""Print a log message with level INFO.
		"""
		Logging._log(logging.INFO, msg, withPath)


	@staticmethod
	def logDebug(msg, withPath=True):
		"""Print a log message with level DEBUG.
		"""
		Logging._log(logging.DEBUG, msg, withPath)


	@staticmethod
	def logErr(msg, withPath=True):
		"""Print a log message with level ERROR.
		"""
		import CSE
		CSE.event.logError()	# raise logError event
		Logging._log(logging.ERROR, msg, withPath)


	@staticmethod
	def logWarn(msg, withPath=True):
		"""Print a log message with level WARNING.
		"""
		import CSE
		CSE.event.logWarning()	# raise logWarning event
		Logging._log(logging.WARNING, msg, withPath)


	@staticmethod
	def _log(level, msg, withPath):
		try:
			if Logging.loggingEnabled and Logging.logLevel <= level:
				caller = inspect.getframeinfo(inspect.stack()[2][0])
				if withPath:
					msg = '(%s:%d) %s' % (os.path.basename(caller.filename), caller.lineno, msg)
				#print( "(" + time.ctime(time.time()) + ") " + msg)
				print('%s %s %s' % (levelName[level], datetime.datetime.now().isoformat(sep=' ', timespec='milliseconds'), msg))
				Logging.logger.log(level, msg)
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
		if record.levelno == logging.DEBUG:
			Logging.logDebug(msg, False)
		elif record.levelno == logging.INFO:
			Logging.log(msg, False)
		elif record.levelno == logging.WARNING:
			Logging.logWarn(msg, False)
		elif record.levelName == logging.ERROR:
			Logging.logErr(msg, False)
