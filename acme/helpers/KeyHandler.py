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
from ast import Call
import sys, time, select
from enum import Enum
from typing import Callable, Dict, Tuple, Union

_timeout = 0.5

try:
	# Posix, Linux, Mac OS
	import tty, termios

	class FunctionKey(str, Enum):
		
		# Cursor keys
		UP 					= '\x1b\x5b\x41'
		DOWN				= '\x1b\x5b\x42'
		LEFT				= '\x1b\x5b\x44'
		RIGHT				= '\x1b\x5b\x43'
		SHIFT_UP			= '\x1b\x5b\x31\x3b\x32\x41'
		SHIFT_DOWN			= '\x1b\x5b\x31\x3b\x32\x42'
		SHIFT_RIGHT			= '\x1b\x5b\x31\x3b\x32\x43'
		SHIFT_LEFT			= '\x1b\x5b\x31\x3b\x32\x44'
		CTRL_UP				= '\x1b\x5b\x31\x3b\x35\x41'
		CTRL_DOWN			= '\x1b\x5b\x31\x3b\x35\x42'
		CTRL_RIGHT			= '\x1b\x5b\x31\x3b\x35\x43'
		CTRL_LEFT			= '\x1b\x5b\x31\x3b\x35\x44'
		ALT_UP				= '\x1b\x1b\x5b\x41'
		ALT_DOWN			= '\x1b\x1b\x5b\x42'
		ALT_RIGHT			= '\x1b\x1b\x5b\x43'
		ALT_LEFT			= '\x1b\x1b\x5b\x44'
		SHIFT_ALT_UP		= '\x1b\x5b\x31\x3b\x31\x30\x41'
		SHIFT_ALT_DOWN		= '\x1b\x5b\x31\x3b\x31\x30\x42'
		SHIFT_ALT_RIGHT		= '\x1b\x5b\x31\x3b\x31\x30\x43'
		SHIFT_ALT_LEFT		= '\x1b\x5b\x31\x3b\x31\x30\x44'
		SHIFT_CTRL_UP		= '\x1b\x5b\x31\x3b\x36\x41'
		SHIFT_CTRL_DOWN		= '\x1b\x5b\x31\x3b\x36\x42'
		SHIFT_CTRL_RIGHT	= '\x1b\x5b\x31\x3b\x36\x43'
		SHIFT_CTRL_LEFT		= '\x1b\x5b\x31\x3b\x36\x44'
		SHIFT_CTRL_ALT_UP	= '\x1b\x5b\x31\x3b\x31\x34\x41'
		SHIFT_CTRL_ALT_DOWN	= '\x1b\x5b\x31\x3b\x31\x34\x42'
		SHIFT_CTRL_ALT_RIGHT= '\x1b\x5b\x31\x3b\x31\x34\x43'
		SHIFT_CTRL_ALT_LEFT	= '\x1b\x5b\x31\x3b\x31\x34\x44'


		# navigation keys
		INSERT 				= '\x1b\x5b\x32\x7e'
		SUPR				= '\x1b\x5b\x33\x7e'

		HOME				= '\x1b\x5b\x48'
		SHIFT_HOME			= '\x1b\x5b\x31\x3b\x32\x48'
		CTRL_HOME			= '\x1b\x5b\x31\x3b\x35\x48'
		ALT_HOME			= '\x1b\x5b\x31\x3b\x39\x48'
		SHIFT_CTRL_HOME		= '\x1b\x5b\x31\x3b\x36\x48'
		SHIFT_ALT_HOME		= '\x1b\x5b\x31\x3b\x31\x30\x48'
		SHIFT_CTRL_ALT_HOME	= '\x1b\x5b\x31\x3b\x31\x34\x48'

		END					= '\x1b\x5b\x46'
		SHIFT_END			= '\x1b\x5b\x31\x3b\x32\x46'
		CTRL_END			= '\x1b\x5b\x31\x3b\x35\x46'
		ALT_END				= '\x1b\x5b\x31\x3b\x39\x46'
		SHIFT_CTRL_END		= '\x1b\x5b\x31\x3b\x36\x46'
		SHIFT_ALT_END		= '\x1b\x5b\x31\x3b\x31\x30\x46'
		SHIFT_CTRL_ALT_END	= '\x1b\x5b\x31\x3b\x31\x34\x46'

		PAGE_UP				= '\x1b\x5b\x35\x7e'
		ALT_PAGE_UP			= '\x1b\x1b\x5b\x35\x7e'
		PAGE_DOWN			= '\x1b\x5b\x36\x7e'
		ALT_PAGE_DOWN		= '\x1b\x1b\x5b\x36\x7e'


		# funcion keys
		F1					= '\x1b\x4f\x50'
		F2					= '\x1b\x4f\x51'
		F3					= '\x1b\x4f\x52'
		F4					= '\x1b\x4f\x53'
		F5					= '\x1b\x5b\x31\x35\x7e'
		F6					= '\x1b\x5b\x31\x37\x7e'
		F7					= '\x1b\x5b\x31\x38\x7e'
		F8					= '\x1b\x5b\x31\x39\x7e'
		F9					= '\x1b\x5b\x32\x30\x7e'
		F10					= '\x1b\x5b\x32\x31\x7e'
		F11					= '\x1b\x5b\x32\x33\x7e'
		F12					= '\x1b\x5b\x32\x34\x7e'
		SHIFT_F1			= '\x1b\x5b\x31\x3b\x32\x50'
		SHIFT_F2			= '\x1b\x5b\x31\x3b\x32\x51'
		SHIFT_F3			= '\x1b\x5b\x31\x3b\x32\x52'
		SHIFT_F4			= '\x1b\x5b\x31\x3b\x32\x53'
		SHIFT_F5			= '\x1b\x5b\x31\x35\x3b\x32\x7e'
		SHIFT_F6			= '\x1b\x5b\x31\x37\x3b\x32\x7e'
		SHIFT_F7			= '\x1b\x5b\x31\x38\x3b\x32\x7e'
		SHIFT_F8			= '\x1b\x5b\x31\x39\x3b\x32\x7e'
		SHIFT_F9			= '\x1b\x5b\x32\x30\x3b\x32\x7e'
		SHIFT_F10			= '\x1b\x5b\x32\x31\x3b\x32\x7e'
		SHIFT_F11			= '\x1b\x5b\x32\x33\x3b\x32\x7e'
		SHIFT_F12			= '\x1b\x5b\x32\x34\x3b\x32\x7e'

		# Common
		BACKSPACE			= '\x7f'
		SHIFT_TAB			= '\x1b\x5b\x5a'


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
		
		class FunctionKey(str, Enum):	# type: ignore[no-redef]
			# TODO
			pass
		
else:


	_errorInGetch:bool = False
	def getch() -> str|FunctionKey:
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
				ch = _getKey(lambda : sys.stdin.read(1))
			else:
				ch = None
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		return ch
	
	def flushInput() -> None:
		sys.stdin.flush()

_functionKeys:Tuple[FunctionKey, str] = [(e, e.value) for e in FunctionKey] # type:ignore
# TODO

Commands = Dict[str, Callable[[str], None]]
""" Mapping between characters and callback functions. """

_stopLoop = False
""" Internal variable to indicate to stop the keyboard loop. """


def _getKey(nextKeyCB:Callable) -> str|FunctionKey:
	"""	Read and process a keypress. If the key is a start of a sequence then process all further
		keys until a single sequence has been identified and full read. Then return the key as a
		function key enum.
		
		Args:
			nextKeyCB: A function the provides the next key from a keypress.
		Return:
			Either a string with a single non-function key, or a function key enum value.
	"""

	_fkmatches = [ True ] * len(_functionKeys) # init list with True, one for each function key
	_escapeSequenceIdx = 0

	while True:
		key = nextKeyCB()
		#print(hex(ord(key)))

		for i, f in enumerate(_functionKeys):
			_escapeSequence = f[1]
			# Check if the function key sequence-to-be-tested is still long enough,
			# and char at the current index position in the sequence matches the key, 
			# and the function key row was not eliminates from the search (ie False)
			if len(_escapeSequence) > _escapeSequenceIdx and key == _escapeSequence[_escapeSequenceIdx] and _fkmatches[i] :	
				pass	# Don't do anything with a found entry. Leave the old value in the array
			else:
				_fkmatches[i] = False	# eliminate the sequence if no match
		
		# Check after each new key and sequence processing
		if (_fcount := _fkmatches.count(True)) == 1:	# break out of the search as soon there is only one full match left
			fn = _functionKeys[_fkmatches.index(True)]
			if len(fn[1]) == _escapeSequenceIdx+1:		# But only return when the whole sequence was read
				return fn[0]							# return the function key

		if _fcount == 0:
			return key	# Return the last character if nothing matched

		_escapeSequenceIdx += 1


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