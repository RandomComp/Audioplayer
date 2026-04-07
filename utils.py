import sys

from termios import tcsetattr, tcgetattr, TCSADRAIN

from tty import setraw

from os import get_terminal_size

from types import FunctionType, CoroutineType

from typing import Any, Generator

import ansi

import asyncio

from enum import Enum

import builtins

def ansi_len(ansi_str: str) -> int:
	ch_len = builtins.len(ansi_str)

	index = ansi_str.find("\x1B[")

	result = 0
	
	while index != -1:
		temp_result = 2 # [

		c = get_ch(ansi_str, index + temp_result, ch_len)

		commands = "mhlsuHJK"

		while c not in commands and c != "\0":
			inc = 1

			if c.isdigit():
				inc = num_len(ansi_str, index + temp_result, ch_len)

			temp_result += inc

			c = get_ch(ansi_str, index + temp_result, ch_len)
		
		if c in commands:
			temp_result += 1

		index = ansi_str.find("\x1B[", index + temp_result)

		result += temp_result

	return result

def len(text: str) -> int:
	return builtins.len(text) - ansi_len(text)

def text_start(text: str) -> int | tuple[int]:
	result = 0

	i = text.find("\x1B[")

	while i != -1 and text[i] == "\x1B":
		i += 2

		i = text.find("\x1B[")

	return result

def text_scroller(text: str, max_length: int, time: float, speed: float=10) -> str:
	text_len = len(text)

	if text_len <= max_length:
		return text

	result = text

	pos = int(((time * speed) % (text_len + max_length + 1)) - max_length)

	end = pos + max_length
	
	result = result[max(0, pos):end]

	if pos >= 0:
		result = result.ljust(max_length)
	else:
		result = result.rjust(max_length)

	return result

async def get_input_byte(loop: asyncio.AbstractEventLoop, bytes: int=1):
	return await loop.run_in_executor(None, sys.stdin.read, bytes)

python_print = print

class PrintPadding(Enum):
	none = 		0
	up = 		1
	down = 		2
	right = 	4
	left = 		8
	center_x = 	12
	center_y = 	3
	center = 	15

def print(*values: object, sep: str=" ", end: str="\n", padding_val: int=0, padding: PrintPadding=PrintPadding.none) -> None:
	string = f"{sep.join(map(str, values))}{end}".replace("\n", "\n\r").expandtabs(4)

	#up = padding 

	#if padding & PrintPadding.center_x

	python_print(string, end='', flush=True)

def clear_screen() -> None:
	ansi.set_cursor_pos(0, 0)

	columns, rows = get_terminal_size()

	print(" " * columns * rows, end='')

	ansi.set_cursor_pos(0, 0)

def get_ch(txt: str, i: int, c_len: int) -> str:
	return "\0" if i >= c_len else txt[i]

def num_len(txt: str, i: int, c_len: int) -> int:
	result = 0

	while get_ch(txt, i + result, c_len).isdigit():
		result += 1
	
	return result

def __ljust(string: str, length: int, fill_char: str=" ") -> str:
	str_len = len(string)

	if str_len >= length:
		return string
	
	spaces = length - str_len
	
	return f"{string}{fill_char * spaces}"

def ljust(block: str, length: int, fill_char: str=" ") -> str:
	result = ""

	strings = block.splitlines()

	for string in strings:
		result += f"{__ljust(string, length)}"
	
	return result

def __rjust(string: str, length: int, fill_char: str=" ") -> str:
	str_len = len(string)

	if str_len >= length:
		return string
	
	spaces = length - str_len
	
	return f"{fill_char * spaces}{string}"

def rjust(block: str, length: int, fill_char: str=" ") -> str:
	result = ""

	strings = block.splitlines()

	strings_cnt = builtins.len(strings)

	for i, string in enumerate(strings):
		end = "\n" if i != (strings_cnt - 1) else ""

		result += f"{__rjust(string, length)}{end}"
	
	return result

def __center(string: str, length: int, fill_char: str=" ") -> str:
	str_len = len(string)

	if str_len == 0 or str_len >= length:
		return string
	
	spaces = (length - str_len) // 2
	
	return f"{fill_char * spaces}{string}{fill_char * spaces}"

def center(block: str, length: int, fill_char: str=" ") -> str:
	result = ""

	strings = block.splitlines()

	strings_cnt = builtins.len(strings)

	for i, string in enumerate(strings):
		end = "\n" if i != (strings_cnt - 1) else ""

		result += f"{__center(string, length)}{end}"
	
	return result

def set_cursor_pos(x: int, y: int):
	sys.stdout.write(f"\x1B[{y};{x}H")

# obsolete
async def get_cursor_pos() -> tuple[int, int]:
	sys.stdout.flush()

	sys.stdout.write("\x1B[6n")

	sys.stdout.flush()

	async def next() -> str:
		return await get_input_byte(asyncio.get_running_loop())

	while await next() != "\x1B" or await next() != "[":
		sys.stdout.write("\x1B[6n")

		sys.stdout.flush()

		await asyncio.sleep(0.1)

	buffer = c = ""

	while c != "R":
		buffer += c

		c = await next()

	row, column = buffer.split(";")

	return (int(column), int(row))

class EventEmitter:
	def __init__(self, name: str='', max_handlers: int = -1):
		if max_handlers == 0:
			raise RuntimeError("Maximum handlers cannot be 0.")

		self.name = name

		self.handlers: list[FunctionType] = []

		self.max_handlers = max_handlers
	
	def subscribe(self, handler: FunctionType) -> None:
		handler_cnt = builtins.len(self.handlers)
		
		if handler_cnt >= self.max_handlers and not self.max_handlers < 0:
			print(f"Maximum handlers count exceeded ({handler_cnt} >= {self.max_handlers})")

			return

		if handler not in self.handlers:
			self.handlers.append(handler)

	def unsubscribe(self, handler: FunctionType=None) -> None:
		handler_cnt = builtins.len(self.handlers)
		
		if handler == None or handler_cnt == 1:
			if self.handlers: self.handlers.pop()

		elif handler in self.handlers:
			self.handlers.remove(handler)
	
	async def invoke(self, *args, **kwargs) -> list[Any]:
		if not self.handlers:
			raise RuntimeWarning(f"No any handler subscribed for event \"{self.name}\".")

		corous_or_results: list[CoroutineType | Any] = \
			(handler(self.name, *args, **kwargs) for handler in self.handlers)
		
		results = []

		for cor_or_result in corous_or_results:
			result = None

			if isinstance(cor_or_result, CoroutineType):
				result = await cor_or_result
			else:
				result = cor_or_result

			results.append(result)

		return results
	
class VirtualConsole:
	def __init__(self, columns=-1, rows=-1):
		self.column = self.row = 0

		term_columns, term_rows = get_terminal_size()

		self.columns = columns if columns > 0 else term_columns
		
		self.rows = rows if rows > 0 else term_rows

		self.text_buf = ""
	
	def clear(self) -> None:
		self.text_buf = ""

		self.update()

	def print(self, *values: object, sep: str=" ", end: str="\n") -> None:
		string = f"{sep.join(map(str, values))}{end}".expandtabs(4)

		self.text_buf += string

		line_cnt = builtins.len(string.splitlines())
		
		self.column += builtins.len(string) - line_cnt

		self.row += line_cnt

	def get_cursor_pos(self) -> tuple[int, int]:
		cursor = (self.row * self.columns) + self.column

		self.column, self.row = (cursor % self.columns, cursor / self.columns)

		return self.column, self.row
	
	def update(self) -> None:
		columns, rows = self.columns, self.rows

		term_columns, term_rows = get_terminal_size()

		if columns == -1:
			columns = term_columns
		
		if rows == -1:
			rows = term_rows

		temp = self.text_buf.replace("\n", " " * columns)

		#string = '\", \"'.join(c for c in temp)

		#print(f"\"{string}\"")

		for i in range(rows):
			st = columns * i

			string = temp[st:(st + columns)]

			if builtins.len(string) > 0:
				python_print(f"{string}|")

def switch_to_raw() -> list:
	fileno = sys.stdin.fileno()
	
	default_settings = tcgetattr(fileno)

	setraw(fileno)

	return default_settings

def switch_to_default(default_settings) -> None:
	fileno = sys.stdin.fileno()

	tcsetattr(fileno, TCSADRAIN, default_settings)

def format_time(time: int):
	hours = int((time / (60 * 60)) % 24)
	minutes = int((time / 60) % 60)
	seconds = int(time % 60)

	result = ""

	if hours != 0:
		result += f"{hours:02} h "

	if minutes != 0:
		result += f"{minutes:02} m "

	result += f"{seconds:02} s "

	return result

def get_system_name() -> str:
	from platform import system

	return system().lower()

def is_input_bytes() -> bool:
	if get_system_name() == "windows":
		from msvcrt import kbhit
		
		return kbhit()
	else:
		raise NotImplementedError()