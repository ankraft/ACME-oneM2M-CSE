#
#	KeyHandler.py
#
#	(c) 2021 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	These module implements a handler for keyboard inputs.
#	It should run on *IX-alikes and Windows OS.
#

import sys
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
else:
	def getch() -> str:
		"""getch() -> key character

		Read a single keypress from stdin and return the resulting character. 
		Nothing is echoed to the console. This call will block if a keypress 
		is not already available, but will not wait for Enter to be pressed. 

		If the pressed key was a modifier key, nothing will be detected; if
		it were a special function key, it may return the first character of
		of an escape sequence, leaving additional characters in the buffer.
		"""
		fd = sys.stdin.fileno()
		old_settings = termios.tcgetattr(fd)
		try:
			#tty.setraw(fd)
			tty.setcbreak(fd)	# Not extra lines in input
			ch = sys.stdin.read(1)
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		return ch


def loop(commands:dict, quit:str=None, catchKeyboardInterrupt:bool=False) -> None:
	"""	Endless loop that reads single chars from the keyboard and then executes
		a handler function for that key (from the dictionary 'commands').
		If a single 'key' value is set in 'quit' and this key is pressed, then
		the loop terminates.
		If 'catchKeyboardInterrupt' is True, then this key is handled as the ^C key,
		otherweise a KeyboardInterrup event is raised.
	"""
	while True:	
		# Get a key. Catch a ctrl-c keyboard interrup and handle it according to configuration
		try:
			ch = getch() # this also returns the key pressed, if you want to store it
			if isinstance(ch, bytes):	# Windows getch() returns a byte-string
				ch = ch.decode('utf-8') 
		except KeyboardInterrupt as e:
			if catchKeyboardInterrupt:
				ch = '\x03'
			else:
				raise e 
		
		# handle "quit" key			
		if quit is not None and ch == quit:
			break
		
		# handle all other keys
		if ch in commands:
			commands[ch](ch)


def readline(prompt:str='>') -> str:
	"""	Read a line from the console. 
		Catch EOF (^D) and Keyboard Interrup (^C). I that case None is returned.
	"""
	result = None
	try:
		result = input(prompt)
	except KeyboardInterrupt as e:
		pass
	except Exception:
		pass
	return result