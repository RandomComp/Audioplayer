import sys

from os import get_terminal_size

import asyncio

from enum import Enum

import builtins

from typing import Iterable

from sys import platform

import ansi

if platform == "win32":
	from msvcrt import getch
else:
	from termios import tcsetattr, tcgetattr, TCSADRAIN

	from tty import setraw

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

def len(text: Iterable) -> int:
	if not isinstance(text, str):
		return builtins.len(text)

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

class PrintPadding(Enum):
	none = 		0
	up = 		1
	down = 		2
	right = 	4
	left = 		8
	center_x = 	12
	center_y = 	3
	center = 	15

from typing import Generator

class ListGenerator:
	def __init__(self, gen: Iterable):
		self.gen = gen

		self.results = []

		self.index = 0

		is_iterable = True

		try:
			self.next()
		except TypeError:
			is_iterable = False
		except StopIteration:
			pass

		if not is_iterable:
			raise TypeError(f"Cannot initialize ListGenerator using non-iterable type {gen}")
	
	def next(self):
		result = next(self.gen)

		self.results.append(result)

		return result

	def __next__(self):
		out_of_range = False

		try:
			result = self[self.index]
		except IndexError:
			out_of_range = True
		
		if out_of_range:
			raise StopIteration()

		self.index += 1

		return result

	def __iter__(self):
		self.index = 0

		return self

	def __getitem__(self, key: None | int | slice):
		if key == None or not isinstance(key, (int, slice)):
			raise TypeError(f"Cannot get item from {self.__repr__()} using with unsupported type object {key}")

		end = key

		is_slice = isinstance(key, slice)
		
		if is_slice:
			end = key.stop if not key.step or key.step > 0 else key.start
		
		out_of_range = False

		while not end or end >= len(self.results):
			try:
				self.next()
			except StopIteration:
				if end:
					out_of_range = True

				break

		if out_of_range:
			raise IndexError("ListGenerator index out of range")

		return self.results[key] if not is_slice else \
				self.results[key.start:key.stop:key.step]
	
	def __contains__(self, item):
		result = item in self.results

		while not result:
			try:
				cur_item = self.next()

				result = cur_item == item
			except StopIteration:
				break
			
		return result

	def __len__(self):
		while True:
			try:
				self.next()
			except StopIteration:
				break
		
		return len(self.results)

	def __str__(self):
		return self.__repr__()
	
	def __repr__(self):
		return f"ListGenerator(results={self.results}, gen={str(self.gen)})"
	
def split(text: str, sep: str | list[str]=" ") -> list[str]:
	sep_list = sep if isinstance(sep, list) else [sep] if sep else None

	sep_list = ListGenerator(map(str, sep_list))

	print(sep_list)

def print(*values: object, sep: str=" ", end: str="\n", padding_val: int=0, padding: PrintPadding=PrintPadding.none) -> None:
	string = f"{sep.join(map(str, values))}{end}".replace("\n", "\n\r").expandtabs(4)

	#up = padding

	#if padding & PrintPadding.center_x

	sys.stdout.write(string)

	sys.stdout.flush()

def clear_screen() -> None:
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

async def get_input_byte(loop: asyncio.AbstractEventLoop, bytes: int=1):
	if platform == "win32":
		return await loop.run_in_executor(None, getch)
	
	return await loop.run_in_executor(None, sys.stdin.read, bytes)

def set_cursor_pos(x: int, y: int):
	sys.stdout.write(f"\x1B[{y};{x}H")

# unstable
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

def switch_to_raw() -> list:
	if platform == "win32":
		print(f"Terminal mode switching default/raw is unsupported on your OS ({platform}).")

		return
	
	fileno = sys.stdin.fileno()
	
	default_settings = tcgetattr(fileno)

	setraw(fileno)

	return default_settings

def switch_to_default(default_settings) -> None:
	if platform == "win32":
		print(f"Terminal mode switching default/raw is unsupported on your OS ({platform}).")

		return
	
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

def format_size(size: int, base: int=1024, 
				unit_names: list[str]=["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB", "RB", "QB"]) -> str:
	if base <= 1:
		raise RuntimeError(f"Base ({base}) cannot be <= 1")

	index = 0

	result = []
	
	while size > 1 and index < len(unit_names) - 1:
		number = size % base

		if number >= 1:
			result.append(f"{number} {unit_names[index]}")

		size //= base

		index += 1

	if size >= 1:
		result.append(f"{size} {unit_names[index]}")

	return ' '.join(result[::-1]) if result else f"0 {unit_names[0]}"

def progress(progress: float, dest: float, max_width: int, c: str="━") -> None:
	width = int((progress / dest if dest > 0 else 1) * max_width)

	passed_progress = c * (width - 1)

	remaining_progress = c * (max_width - width)
					
	return f"{ansi.default}{ansi.lime_fg}{passed_progress}{ansi.default}|{remaining_progress}"

def time_progress(second: float, seconds: float, max_width: int, c: str="━") -> None:
	seconds_str = format_time(seconds)

	second_str = format_time(second)

	width = max_width - 1 - len(seconds_str) * 2

	bar = progress(second, seconds, width, c=c)
					
	return f"{second_str.ljust(len(seconds_str))}{bar} {seconds_str}"

def is_input_bytes() -> bool:
	if platform == "win32":
		from msvcrt import kbhit
		
		return kbhit()
	else:
		raise NotImplementedError()