#
#	KeyHandler.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
r"""This module implements a handler for keyboard inputs.

	It should run on \*IX-alikes and Windows OS.
"""

from __future__ import annotations
from typing import Callable, Dict, Tuple, Optional

import sys, time, select
from enum import Enum

_timeout = 1
""" Timeout for getch() in seconds. """

try:
	# Posix, Linux, Mac OS
	import tty, termios

	class FunctionKey(str, Enum):
		"""	POSIX function keys. """

		# Common
		LF					= '\x0a'
		""" Line feed. """
		CR					= '\x0d'
		""" Carriage return. """
		SPACE				= '\x20'
		""" Space. """
		# ESC				= '\x1b'
		BACKSPACE			= '\x7f'
		""" Backspace. """
		TAB					= '\x09'
		""" Tab. """
		SHIFT_TAB			= '\x1b\x5b\x5a'
		""" Shift tab. """
		
		# CTRL-Keys
		CTRL_A				= '\x01'
		""" Ctrl-A. """
		CTRL_B				= '\x02'
		""" Ctrl-B. """
		CTRL_C				= '\x03'
		""" Ctrl-C. """
		CTRL_D				= '\x04'
		""" Ctrl-D. """
		CTRL_E				= '\x05'
		""" Ctrl-E. """
		CTRL_F				= '\x06'
		""" Ctrl-F. """
		CTRL_G				= '\x07'
		""" Ctrl-G. """
		CTRL_H				= '\x08'
		""" Ctrl-H. """
		CTRL_I				= TAB
		""" Ctrl-I. Mappped to TAB. """
		CTRL_J				= LF
		""" Ctrl-J. Mapped to Line Feed. """
		CTRL_K				= '\x0b'
		""" Ctrl-K. """
		CTRL_L				= '\x0c'
		""" Ctrl-L. """
		CTRL_M	 			= CR
		""" Ctrl-M. Mapped to Carriage Return. """
		CTRL_N				= '\x0e'
		""" Ctrl-N. """
		CTRL_O				= '\x0f'
		""" Ctrl-O. """
		CTRL_P				= '\x10'
		""" Ctrl-P. """
		CTRL_Q				= '\x11'
		""" Ctrl-Q. """
		CTRL_R				= '\x12'
		""" Ctrl-R. """
		CTRL_S				= '\x13'
		""" Ctrl-S. """
		CTRL_T				= '\x14'
		""" Ctrl-T. """
		CTRL_U				= '\x15'
		""" Ctrl-U. """
		CTRL_V				= '\x16'
		""" Ctrl-V. """
		CTRL_W				= '\x17'
		""" Ctrl-W. """
		CTRL_X				= '\x18'
		""" Ctrl-X. """
		CTRL_Y				= '\x19'
		""" Ctrl-Y. """
		CTRL_Z				= '\x1a'
		""" Ctrl-Z. """
		
		# Cursor keys
		UP 					= '\x1b\x5b\x41'
		""" Cursor up. """
		DOWN				= '\x1b\x5b\x42'
		""" Cursor down. """
		LEFT				= '\x1b\x5b\x44'
		""" Cursor left. """
		RIGHT				= '\x1b\x5b\x43'
		""" Cursor right. """
		SHIFT_UP			= '\x1b\x5b\x31\x3b\x32\x41'
		""" Shift cursor up. """
		SHIFT_DOWN			= '\x1b\x5b\x31\x3b\x32\x42'
		""" Shift cursor down. """
		SHIFT_RIGHT			= '\x1b\x5b\x31\x3b\x32\x43'
		""" Shift cursor right. """
		SHIFT_LEFT			= '\x1b\x5b\x31\x3b\x32\x44'
		""" Shift cursor left. """
		CTRL_UP				= '\x1b\x5b\x31\x3b\x35\x41'
		""" Ctrl cursor up. """
		CTRL_DOWN			= '\x1b\x5b\x31\x3b\x35\x42'
		""" Ctrl cursor down. """
		CTRL_RIGHT			= '\x1b\x5b\x31\x3b\x35\x43'
		""" Ctrl cursor right. """
		CTRL_LEFT			= '\x1b\x5b\x31\x3b\x35\x44'
		""" Ctrl cursor left. """
		ALT_UP				= '\x1b\x1b\x5b\x41'
		""" Alt cursor up. """
		ALT_DOWN			= '\x1b\x1b\x5b\x42'
		""" Alt cursor down. """
		ALT_RIGHT			= '\x1b\x1b\x5b\x43'
		""" Alt cursor right. """
		ALT_LEFT			= '\x1b\x1b\x5b\x44'
		""" Alt cursor left. """
		SHIFT_ALT_UP		= '\x1b\x5b\x31\x3b\x31\x30\x41'
		""" Shift Alt cursor up. """
		SHIFT_ALT_DOWN		= '\x1b\x5b\x31\x3b\x31\x30\x42'
		""" Shift Alt cursor down. """
		SHIFT_ALT_RIGHT		= '\x1b\x5b\x31\x3b\x31\x30\x43'
		""" Shift Alt cursor right. """
		SHIFT_ALT_LEFT		= '\x1b\x5b\x31\x3b\x31\x30\x44'
		""" Shift Alt cursor left. """
		SHIFT_CTRL_UP		= '\x1b\x5b\x31\x3b\x36\x41'
		""" Shift Ctrl cursor up. """
		SHIFT_CTRL_DOWN		= '\x1b\x5b\x31\x3b\x36\x42'
		""" Shift Ctrl cursor down. """
		SHIFT_CTRL_RIGHT	= '\x1b\x5b\x31\x3b\x36\x43'
		""" Shift Ctrl cursor right. """
		SHIFT_CTRL_LEFT		= '\x1b\x5b\x31\x3b\x36\x44'
		""" Shift Ctrl cursor left. """
		SHIFT_CTRL_ALT_UP	= '\x1b\x5b\x31\x3b\x31\x34\x41'
		""" Shift Ctrl Alt cursor up. """
		SHIFT_CTRL_ALT_DOWN	= '\x1b\x5b\x31\x3b\x31\x34\x42'
		""" Shift Ctrl Alt cursor down. """
		SHIFT_CTRL_ALT_RIGHT= '\x1b\x5b\x31\x3b\x31\x34\x43'
		""" Shift Ctrl Alt cursor right. """
		SHIFT_CTRL_ALT_LEFT	= '\x1b\x5b\x31\x3b\x31\x34\x44'
		""" Shift Ctrl Alt cursor left. """

		# Navigation keys
		INSERT 				= '\x1b\x5b\x32\x7e'
		""" Insert. """
		SUPR				= '\x1b\x5b\x33\x7e'
		""" Supr. """

		HOME				= '\x1b\x5b\x48'
		""" Home. """
		SHIFT_HOME			= '\x1b\x5b\x31\x3b\x32\x48'
		""" Shift Home. """
		CTRL_HOME			= '\x1b\x5b\x31\x3b\x35\x48'
		""" Ctrl Home. """
		ALT_HOME			= '\x1b\x5b\x31\x3b\x39\x48'
		""" Alt Home. """
		SHIFT_CTRL_HOME		= '\x1b\x5b\x31\x3b\x36\x48'
		""" Shift Ctrl Home. """
		SHIFT_ALT_HOME		= '\x1b\x5b\x31\x3b\x31\x30\x48'
		""" Shift Alt Home. """
		SHIFT_CTRL_ALT_HOME	= '\x1b\x5b\x31\x3b\x31\x34\x48'
		""" Shift Ctrl Alt Home. """

		END					= '\x1b\x5b\x46'
		""" End. """
		SHIFT_END			= '\x1b\x5b\x31\x3b\x32\x46'
		""" Shift End. """
		CTRL_END			= '\x1b\x5b\x31\x3b\x35\x46'
		""" Ctrl End. """
		ALT_END				= '\x1b\x5b\x31\x3b\x39\x46'
		""" Alt End. """
		SHIFT_CTRL_END		= '\x1b\x5b\x31\x3b\x36\x46'
		""" Shift Ctrl End. """
		SHIFT_ALT_END		= '\x1b\x5b\x31\x3b\x31\x30\x46'
		""" Shift Alt End. """
		SHIFT_CTRL_ALT_END	= '\x1b\x5b\x31\x3b\x31\x34\x46'
		""" Shift Ctrl Alt End. """

		PAGE_UP				= '\x1b\x5b\x35\x7e'
		""" Page up. """
		ALT_PAGE_UP			= '\x1b\x1b\x5b\x35\x7e'
		""" Alt Page up. """
		PAGE_DOWN			= '\x1b\x5b\x36\x7e'
		""" Page down. """
		ALT_PAGE_DOWN		= '\x1b\x1b\x5b\x36\x7e'
		""" Alt Page down. """


		# Funcion keys
		F1					= '\x1b\x4f\x50'
		""" F1. """
		F2					= '\x1b\x4f\x51'
		""" F2. """
		F3					= '\x1b\x4f\x52'
		""" F3. """
		F4					= '\x1b\x4f\x53'
		""" F4. """
		F5					= '\x1b\x5b\x31\x35\x7e'
		""" F5. """
		F6					= '\x1b\x5b\x31\x37\x7e'
		""" F6. """
		F7					= '\x1b\x5b\x31\x38\x7e'
		""" F7. """
		F8					= '\x1b\x5b\x31\x39\x7e'
		""" F8. """
		F9					= '\x1b\x5b\x32\x30\x7e'
		""" F9. """
		F10					= '\x1b\x5b\x32\x31\x7e'
		""" F10. """
		F11					= '\x1b\x5b\x32\x33\x7e'
		""" F11. """
		F12					= '\x1b\x5b\x32\x34\x7e'
		""" F12. """
		SHIFT_F1			= '\x1b\x5b\x31\x3b\x32\x50'
		""" Shift F1. """
		SHIFT_F2			= '\x1b\x5b\x31\x3b\x32\x51'
		""" Shift F2. """
		SHIFT_F3			= '\x1b\x5b\x31\x3b\x32\x52'
		""" Shift F3. """
		SHIFT_F4			= '\x1b\x5b\x31\x3b\x32\x53'
		""" Shift F4. """
		SHIFT_F5			= '\x1b\x5b\x31\x35\x3b\x32\x7e'
		""" Shift F5. """
		SHIFT_F6			= '\x1b\x5b\x31\x37\x3b\x32\x7e'
		""" Shift F6. """
		SHIFT_F7			= '\x1b\x5b\x31\x38\x3b\x32\x7e'
		""" Shift F7. """
		SHIFT_F8			= '\x1b\x5b\x31\x39\x3b\x32\x7e'
		""" Shift F8. """
		SHIFT_F9			= '\x1b\x5b\x32\x30\x3b\x32\x7e'
		""" Shift F9. """
		SHIFT_F10			= '\x1b\x5b\x32\x31\x3b\x32\x7e'
		""" Shift F10. """
		SHIFT_F11			= '\x1b\x5b\x32\x33\x3b\x32\x7e'
		""" Shift F11. """
		SHIFT_F12			= '\x1b\x5b\x32\x34\x3b\x32\x7e'
		""" Shift F12. """


except ImportError:
	# Probably Windows.
	try:
		import msvcrt
	except ImportError:
		# FIXME what to do on other platforms?
		# Just give up here.
		raise ImportError('getch not available')
	else:

		def getch() -> Optional[str|FunctionKey]:
			try:
				# ch = msvcrt.getch	# type: ignore
				return _getKey(lambda : msvcrt.getch()) # type: ignore
			except Exception:
				return None


		def flushInput() -> None:
			pass
			# while msvcrt.kbhit():	# type: ignore
			# 	msvcrt.getch()		# type: ignore
		

		class FunctionKey(str, Enum):	# type: ignore[no-redef]
			""" MS Windows function keys in cmd.exe. """

			# Common
			LF					= '\x0a'
			CR					= '\x0d'
			SPACE				= '\x20'
			# ESC				= '\x1b'
			BACKSPACE			= '\x08'
			CTRL_BACKSPACE		= '\x7f'
			TAB					= '\x09'
			CTRL_TAB			= '\x00\x94'

			# CTRL-Keys
			CTRL_A				= '\x01'
			CTRL_B				= '\x02'
			CTRL_C				= '\x03'
			CTRL_D				= '\x04'
			CTRL_E				= '\x05'
			CTRL_F				= '\x06'
			CTRL_G				= '\x07'
			CTRL_H				= '\x08'
			CTRL_I				= TAB
			CTRL_J				= LF
			CTRL_K				= '\x0b'
			CTRL_L				= '\x0c'
			CTRL_M	 			= CR
			CTRL_N				= '\x0e'
			CTRL_O				= '\x0f'
			CTRL_P				= '\x10'
			CTRL_Q				= '\x11'
			CTRL_R				= '\x12'
			CTRL_S				= '\x13'
			CTRL_T				= '\x14'
			CTRL_U				= '\x15'
			CTRL_V				= '\x16'
			CTRL_W				= '\x17'
			CTRL_X				= '\x18'
			CTRL_Y				= '\x19'
			CTRL_Z				= '\x1a'
		
			# Cursors keys

			UP 					= '\xe0\x48'
			CTRL_UP 			= '\xe0\x8d'
			ALT_UP 				= '\x00\x98'

			DOWN 				= '\xe0\x50'
			CTRL_DOWN 			= '\xe0\x91'
			ALT_DOWN 			= '\x00\xa0'

			LEFT 				= '\xe0\x4b'
			CTRL_LEFT 			= '\xe0\x73'
			ALT_LEFT 			= '\x00\x9b'

			RIGHT				= '\xe0\x4d'
			CTRL_RIGHT			= '\xe0\x74'
			ALT_RIGHT			= '\x00\x9d'

			# Navigation keys
			INSERT 				= '\xe0\x52'
			SUPR 				= '\xe0\x53'
			HOME 				= '\xe0\x47'
			CTRL_HOME 			= '\xe0\x77'
			ALT_HOME 			= '\x00\x97'

			END 				= '\xe0\x4f'
			CTRL_END 			= '\xe0\x75'
			ALT_END 			= '\x00\x9f'
			
			PAGE_UP 			= '\xe0\x49'
			ALT_PAGE_UP 		= '\x00\x99'

			PAGE_DOWN 			= '\xe0\x51'
			CTRL_PAGE_DOWN 		= '\xe0\x76'
			ALT_PAGE_DOWN 		= '\x00\xa1'

			# Funcion keys
			F1 					= '\x00\x3b'
			F2 					= '\x00\x3c'
			F3 					= '\x00\x3d'
			F4 					= '\x00\x3e'
			F5 					= '\x00\x3f'
			F6 					= '\x00\x40'
			F7 					= '\x00\x41'
			F8 					= '\x00\x42'
			F9 					= '\x00\x43'
			F10 				= '\x00\x44'
			F11					= '\xe0\x85'
			F12					= '\xe0\x86'
			SHIFT_F1			= '\x00\x54'
			SHIFT_F2			= '\x00\x55'
			SHIFT_F3			= '\x00\x56'
			SHIFT_F4			= '\x00\x57'
			SHIFT_F5			= '\x00\x58'
			SHIFT_F6			= '\x00\x59'
			SHIFT_F7			= '\x00\x5a'
			SHIFT_F8			= '\x00\x5b'
			SHIFT_F9			= '\x00\x5c'
			SHIFT_F10			= '\x00\x5d'
			SHIFT_F11			= '\xe0\x87'
			SHIFT_F12			= '\xe0\x88'
			CTRL_F1				= '\x00\x5e'
			CTRL_F2				= '\x00\x5f'
			CTRL_F3				= '\x00\x60'
			CTRL_F4				= '\x00\x61'
			CTRL_F5				= '\x00\x62'
			CTRL_F6				= '\x00\x63'
			CTRL_F7				= '\x00\x64'
			CTRL_F8				= '\x00\x65'
			CTRL_F9				= '\x00\x66'
			CTRL_F10			= '\x00\x67'
			CTRL_F11			= '\xe0\x89'
			CTRL_F12			= '\xe0\x8a'
			ALT_F1				= '\x00\x68'
			ALT_F2				= '\x00\x69'
			ALT_F3				= '\x00\x6a'
			ALT_F4				= '\x00\x6b'
			ALT_F5				= '\x00\x6c'
			ALT_F6				= '\x00\x6d'
			ALT_F7				= '\x00\x6e'
			ALT_F8				= '\x00\x6f'
			ALT_F9				= '\x00\x70'
			ALT_F10				= '\x00\x71'
			ALT_F11				= '\xe0\x8b'
			ALT_F12				= '\xe0\x8c'
			
else:


	_errorInGetch:bool = False
	def getch() -> Optional[str|FunctionKey]:
		"""	getch() -> key character

			Read a single keypress from stdin and return the resulting character. 
			Nothing is echoed to the console. This call will block if a keypress 
			is not already available, but will not wait for Enter to be pressed. 

			If the pressed key was a modifier key, nothing will be detected; if
			it were a special function key, it may return the first character of
			of an escape sequence, leaving additional characters in the buffer.

			Returns:
				A single character str or a FunctionKey enum value.
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
""" List of all function keys. """

Commands = Dict[str, Callable[[str], str|None]]
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
		key = chr(ord(nextKeyCB()))
		# print(hex(ord(key)))

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
			# print(fn)
			if len(fn[1]) == _escapeSequenceIdx+1:		# But only return when the whole sequence was read
				return fn[0]							# return the function key

		if _fcount == 0:
			return key	# Return the last character if nothing matched

		_escapeSequenceIdx += 1


def loop(commands:Commands, 
		 quit:Optional[str] = None, 
		 catchKeyboardInterrupt:Optional[bool] = False, 
		 headless:Optional[bool] = False, 
		 ignoreException:Optional[bool] = True,
		 catchAll:Optional[Callable] = None,
		 nextKey:Optional[str] = None,
		 postCommandHandler:Optional[Callable] = None,
		 exceptionHandler:Optional[Callable] = None) -> None:
	"""	Endless loop that reads single chars from the keyboard and then executes
		a handler function for that key (from the dictionary *commands*).

		Args:
			commands: A dictionary of `Commands` that map between input keys and callbacks.
			quit: If a single 'key' value is set in *quit* and this key is pressed, then the loop terminates.
			catchKeyboardInterrupt: If *catchKeyboardInterrupt* is *True*, then this event is handled as the "^C" key,
				otherweise a KeyboardInterrupt event is raised.
			headless: If *headless* is *True*, then operate differently. Ignore all key inputs, but handle
					a keyboard interrupt. If in this case the *quit* key is set then the loop is just interrupted.
					Otherwise tread the keyboard interrupt as the "^C" key. It must also be handled in *commands*.
			ignoreException: If *ignoreException* is *True* then exceptions raised during command execution are
				ignore, or passed on otherwise.
			catchAll: If this attribute is set to a callback function then this callback is called in case a pressed
				key was not found in *commands*.
			nextKey: A simulated key-press that is interpreted when first calling the function.
			postCommandHandler: A handler callback that is called after running a command.
			exceptionHandler: A handler callback that is called in case an exception happened during the execution of a command.
	"""
	
	# main loop
	ch:str = None
	while True:	

		if not headless:
			if nextKey is not None:
				ch = nextKey
				nextKey = None
		
		# normal console operation: Get a key. Catch a ctrl-c keyboard interrup and handle it according to configuration

			else:		
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
		if (headless and not _stopLoop) or ch is None:
			try:
				# The following sleep is necessary to avoid 100% CPU load.
				# It must be very short because the loop should react immediately to a key press.
				time.sleep(0.001)
				continue
			except KeyboardInterrupt:
				break

		# handle all other keys
		if ch in commands:
			try:
				commands[ch](ch)
				if postCommandHandler:
					nextKey = postCommandHandler(ch)
			except SystemExit:
				raise
			except KeyboardInterrupt:
				if catchKeyboardInterrupt:
					nextKey = '\x03'
			except Exception as e:
				if exceptionHandler:
					exceptionHandler(ch)
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

		Args:
			prompt: The prompt to display before the input.

		Returns:
			The input line or None.
	"""
	answer = None
	try:
		result = input(prompt)
	except KeyboardInterrupt as e:
		pass
	except Exception:
		pass
	return answer

def waitForKeypress(s:float) -> Optional[str]:
	"""	Wait for a keypress for a maximum of *s* seconds. 
		If no key was pressed then return None.

		Args:
			s: Maximum time to wait in seconds.

		Returns:
			The key that was pressed or None.
	"""
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
