#
#	KeyHandler.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	These module implements a handler for keyboard inputs.
#	It should run on *IX-alikes and Windows OS.
#

from __future__ import annotations
import sys, time, select
from typing import Callable, Dict

_timeout = 0.5

try:
	import tty, termios
except ImportError:
	# Probably Windows.
	try:
		import msvcrt
	except ImportError:
		# FIXME what to do on other platforms?
		# Just give up here.
		raise ImportError('getch not available')
	else:
		getch = msvcrt.getch	# type: ignore

		def flushInput() -> None:
			pass
			# while msvcrt.kbhit():	# type: ignore
			# 	msvcrt.getch()		# type: ignore

else:
	_errorInGetch:bool = False
	def getch() -> str:
		"""getch() -> key character

		Read a single keypress from stdin and return the resulting character. 
		Nothing is echoed to the console. This call will block if a keypress 
		is not already available, but will not wait for Enter to be pressed. 

		If the pressed key was a modifier key, nothing will be detected; if
		it were a special function key, it may return the first character of
		of an escape sequence, leaving additional characters in the buffer.
		"""
		global _errorInGetch
		if _errorInGetch:		# getch() doesnt't fully work previously, so just return
			return None

		fd = sys.stdin.fileno()
		try:
			old_settings = termios.tcgetattr(fd)

		except:
			_errorInGetch = True
			return None

		try:
			#tty.setraw(fd)
			tty.setcbreak(fd)	# Not extra lines in input
			if select.select([sys.stdin,], [], [], _timeout)[0]:
				ch = sys.stdin.read(1)
				if ch == '\x1b':
					ch2 = sys.stdin.read(1)
					if ch2 == '[':
						ch3 = sys.stdin.read(1)
						ch += ch2 + ch3
			else:
				ch = None
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		return ch
	
	def flushInput() -> None:
		sys.stdin.flush()


Commands = Dict[str, Callable[[str], None]]
""" Mapping between characters and callback functions. """

_stopLoop = False
""" Internal variable to indicate to stop the keyboard loop. """


def loop(commands:Commands, quit:str = None, catchKeyboardInterrupt:bool = False, headless:bool = False, ignoreException:bool = True, catchAll:Callable = None) -> None:
	"""	Endless loop that reads single chars from the keyboard and then executes
		a handler function for that key (from the dictionary `commands`).
		If a single 'key' value is set in `quit` and this key is pressed, then
		the loop terminates.

		If `catchKeyboardInterrupt` is True, then this key is handled as the ^C key,
		otherweise a KeyboardInterrupt event is raised.

		If `headless` is True, then operate differently. Ignore all key inputs, but handle
		a keyboard interrupt. If the `quit` key is set then the loop is just interrupted. Otherwise
		tread the keyboard interrupt as ^C key. It must be hanled in the `commands`.

		If `ignoreException` is True, then exceptions raised during command execution is ignore, or
		passed on otherwise.

		If `catchAll` is given then this callback is called in case the pressed key was not found
		in `commands`.
	"""
	
	# main loop
	ch:str = None
	while True:	

		# normal console operation: Get a key. Catch a ctrl-c keyboard interrup and handle it according to configuration
		if not headless:
			try:
				ch = getch() # this also returns the key pressed, if you want to store it
				if isinstance(ch, bytes):	# Windows getch() returns a byte-string
					ch = ch.decode('utf-8') # type: ignore [attr-defined]
			except KeyboardInterrupt as e:
				flushInput()
				if catchKeyboardInterrupt:
					ch = '\x03'
				else:
					raise e 
			except Exception:	# Exit the loop when there is any other problem
				break

			# handle "quit" key			
			if quit is not None and ch == quit:
				break
			
		# When headless then look only for keyboard interrup
		if _stopLoop:
			break
			# Just break?
			if quit is not None or not '\x03' in commands:	# shortcut: if there is a quit key OR ^C is not in the commands, then just return from the loop
				break
			ch = '\x03'										# Assign ^C

		# hande potential headless state: just sleep a moment, but only when not keyboad interrupt was received
		if headless and not _stopLoop:
			try:
				time.sleep(0.2)
				continue
			except KeyboardInterrupt:
				break

		# handle all other keys
		if ch in commands:
			try:
				commands[ch](ch)
			except SystemExit:
				raise
			except Exception as e:
				if not ignoreException:
					raise e
		elif ch and catchAll:
			catchAll(ch)


def stopLoop() -> None:
	"""	Stop the keyboard loop.
	"""
	global _stopLoop
	_stopLoop = True


def readline(prompt:str='>') -> str:
	"""	Read a line from the console. 
		Catch EOF (^D) and Keyboard Interrup (^C). I that case None is returned.
	"""
	answer = None
	try:
		result = input(prompt)
	except KeyboardInterrupt as e:
		pass
	except Exception:
		pass
	return answer

def waitForKeypress(s:float) -> str:
	for i in range(0, int(s * 1.0 / _timeout)):
		ch = None
		try:
			ch = getch()	# returns after _timeout s
		except KeyboardInterrupt as e:
			ch = '\x03'
		except Exception:
			return None
		if ch is not None:
			return ch
	return None