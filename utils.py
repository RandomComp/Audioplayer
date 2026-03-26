import sys

from termios import tcsetattr, tcgetattr, TCSADRAIN

from tty import setraw

from os import get_terminal_size

from types import FunctionType

from asyncio import AbstractEventLoop

def text_scroller(text: str, max_length: int, time: int, speed: float=10) -> str:
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

async def get_input_byte(loop: AbstractEventLoop):
	return await loop.run_in_executor(None, sys.stdin.read, 1)

class EventEmitter:
	def __init__(self, name: str='', max_handlers: int = -1):
		if max_handlers == 0:
			raise RuntimeError("Maximum handlers cannot be 0.")

		self.name = name

		self.handlers: list[FunctionType] = []

		self.max_handlers = max_handlers
	
	def subscribe(self, handler: FunctionType) -> None:
		handler_cnt = len(self.handlers)
		
		if handler_cnt >= self.max_handlers and not self.max_handlers < 0:
			print(f"Maximum handlers count exceeded ({handler_cnt} >= {self.max_handlers})")

			return

		if handler not in self.handlers:
			self.handlers.append(handler)

	def unsubscribe(self, handler: FunctionType=None) -> None:
		handler_cnt = len(self.handlers)
		
		if handler == None or handler_cnt == 1:
			self.handlers.pop()

		elif handler in self.handlers:
			self.handlers.remove(handler)
	
	async def invoke(self, *args, **kwargs) -> None:
		if not self.handlers:
			print(f"No any handler subscribed for event \"{self.name}\".")

			return

		for handler in self.handlers:
			if handler:
				await handler(self.name, *args, **kwargs)

python_print = print

def print(*values: object, sep: str=" ", end: str="\n") -> None:
	string = f"{sep.join(map(str, values))}{end}".replace("\n", "\n\r").expandtabs(4)

	python_print(string, end='')

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

def set_cursor_pos(x: int, y: int):
	sys.stdout.write(f"\033[{x};{y}H")

def get_system_name() -> str:
	from platform import system

	return system().lower()

def is_input_bytes() -> bool:
	if get_system_name() == "windows":
		from msvcrt import kbhit
		
		return kbhit()
	else:
		raise NotImplementedError()