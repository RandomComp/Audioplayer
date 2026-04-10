import asyncio

from time import time

from types import FunctionType

import utils

import ansi

import event

from translator import Translator

class Menu:
	def __init__(self, full_options: list[str]=None, options: list[str]=[], title: str="Menu", info: str="""arrows ↑↓→← -- navigate
f -- find objects by name (double esc to exit)
backspace -- go previous location
enter -- select
q -- quit menu""", multiple: bool=False, translator: Translator=None) -> None:
		self.options = options

		if not full_options:
			full_options = options

		self.full_options = full_options

		self.view_options = options

		self.option_cnt = len(options)

		self.title = title

		self.info = info
		
		self.multiple = multiple

		self.input = event.EventEmitter("input", max_handlers=1)

		self.default_input = event.EventEmitter("default_input", max_handlers=1)

		self.__menu_update = event.EventEmitter("menu_update")

		self.finished = asyncio.Event()

		self.find_buf = ""

		self.state_string = ""

		self.find = asyncio.Event()

		self.selected_option = 0

		self.old_sel_item = 0

		self.options_display_start = 0

		self.selected_options: list[str] = []

		self.filters: list[str] | None = []

		self.__lines_outputed = 0

		self.__selected_str = "selected"

		self.__selected_item_str = "selected item"

		if translator:
			self.__selected_str = translator.translate(self.__selected_str)

			self.__selected_item_str = translator.translate(self.__selected_item_str)

		#self.console = utils.VirtualConsole()
	
	def __output(self, *values: object, sep: str=" ", end: str="\n") -> None:
		string = f"{sep.join(map(str, values))}{end}"

		self.__lines_outputed += len(string.splitlines())

		string = string.replace("\n", "\n\r").expandtabs(4)

		print(string, end='', flush=True)
	
	def __output_update(self) -> None:
		columns, rows = utils.get_terminal_size()

		for _ in range(self.__lines_outputed, rows):
			utils.print("\r".ljust(columns))

		self.__lines_outputed = 0

		utils.set_cursor_pos(0, 0)
	
	async def menu_default_input_handler(self, *args, **kwargs) -> None:
		option = args[1]

		input_key: str = args[2]
		
		if input_key == "↑":
			self.selected_option -= 1
		elif input_key == "↓":
			self.selected_option += 1
		else:
			await self.input.invoke(self, option, input_key)
		
		view_options_cnt = len(self.view_options)

		self.selected_option = 0 if view_options_cnt <= 0 else self.selected_option % view_options_cnt

		if input_key == "q" and not self.find.is_set():
			self.finished.set()
	
	async def menu_key_handler(self) -> None:
		loop = asyncio.get_running_loop()

		while not self.finished.is_set():
			input_key = await utils.get_input_byte(loop)

			if input_key == "\x1B":
				try:
					next_byte = await asyncio.wait_for(utils.get_input_byte(loop), 0.3)

					if next_byte == "[":
						next_byte = await asyncio.wait_for(utils.get_input_byte(loop), 0.3)

						input_arrows = "↑↓→←"

						input_key = input_arrows[ord(next_byte) - ord('A')]
				except asyncio.exceptions.TimeoutError:
					pass

			await self.default_input.invoke(self.selected_option, input_key)
				
			await self.update()
	
	async def menu_select(self, option: int) -> None:
		self.view_options = [option for option in self.full_options if not self.find.is_set() or self.find_buf.lower() in str(option).lower()]
			
		option_name = self.view_options[option]

		if option_name not in self.selected_options:
			self.selected_options.append(option_name)
		else:
			self.selected_options.remove(option_name)
	
	async def menu_cli_frame(self, event_name: str, filters: list[str]) -> None:
		columns, rows = utils.get_terminal_size()

		dur = time()
			
		self.view_options = [i for i, option in enumerate(self.options) if not self.find.is_set() or self.find_buf.lower() in option.lower()]
			
		view_options_cnt = len(self.view_options)

		self.selected_option = 0 if view_options_cnt <= 0 else self.selected_option % view_options_cnt

		options_string = '\", \"'.join(str(option) for option in self.selected_options)
		selected_mess = f"{len(self.selected_options)} {self.__selected_str}: "
		selected_string = utils.text_scroller(f"\"{options_string}\"", columns - len(selected_mess) - 1, dur)

		self.state_string = utils.ljust(f"{self.__selected_item_str}: {self.selected_option + 1}/{len(self.view_options)}", columns)

		self.state_string += "\n"

		self.state_string += utils.ljust(f"{selected_mess}{selected_string}", columns)

		if self.find.is_set():
			mess = "Type: "

			mess_len = len(mess)

			inputed = utils.ljust(utils.text_scroller(self.find_buf, columns - mess_len, dur), columns - mess_len)

			self.state_string += "\n"

			self.state_string += utils.ljust(f"{mess}{inputed}", columns)

		head = 2 + len(self.title.splitlines())

		tail = 1 + len(self.info.splitlines()) + len(self.state_string.splitlines())

		options_display_cnt = min(view_options_cnt, rows - head - tail)

		options_display_end = self.options_display_start + options_display_cnt

		if self.selected_option >= options_display_end:
			self.options_display_start = self.selected_option - options_display_cnt + 1

		elif self.selected_option < self.options_display_start:
			self.options_display_start = self.selected_option

		option_width = columns - 3 - (3 if self.multiple else 0)

		self.__output(utils.center(utils.text_scroller(self.title, columns, time=dur), columns))
				
		screen_width = columns - 2

		self.__output(f"┌{'─' * screen_width}┐")

		for i in range(options_display_cnt):
			i += self.options_display_start

			if i >= view_options_cnt:
				break

			option_index = self.view_options[i]
				
			full_option = self.full_options[option_index]

			selected_marker = ""

			if self.multiple:
				selected_marker = "[X]" if full_option in self.selected_options else "[ ]"
				
			option = self.options[option_index]

			if self.selected_option == i:
				option = utils.text_scroller(option, option_width, dur)
			else:
				option = option[:option_width]

			option = utils.ljust(option, option_width)

			if self.selected_option == i:
				self.__output(f"│{selected_marker} {ansi.inverse}{option}{ansi.default}│")
			else:
				self.__output(f"│{selected_marker} {ansi.default_fg}{ansi.default_bg}{option}{ansi.default}│")

		self.__output(f"└{'─' * screen_width}┘")

		self.__output(self.state_string)

		info_lines = self.info.splitlines()

		for line in info_lines:
			self.__output(utils.center(utils.text_scroller(line, columns, dur), columns), end='')
		
		self.__output()

		self.__output_update()
	
	async def timer(self) -> None:
		while not self.finished.is_set():
			await asyncio.sleep(0.1)

			await self.update()
	
	async def menu_gui(self) -> list[str | None]:
		raise NotImplementedError()
		
		return self.selected_options

	async def loop(self, filters: list[str] | None=None) -> list[str]:
		self.filters = filters

		await asyncio.gather(self.timer(), self.menu_key_handler())

		return self.selected_options

	def set_find(self, find: str="") -> None:
		self.find_buf = find

		self.find.set()

	def stop_find(self) -> None:
		self.find_buf = ""

		self.find.clear()

	async def reset(self) -> None:
		self.finished.clear()
		self.selected_option = 0
		self.options.clear()
		self.option_cnt = 0

	def on_update_subcribe(self, update_handler: FunctionType) -> None:
		self.__menu_update.subscribe(update_handler)

	def on_update_unsubcribe(self, update_handler: FunctionType) -> None:
		self.__menu_update.unsubscribe(update_handler)

	async def update(self) -> None:
		await self.__menu_update.invoke(self.filters)

	def close(self) -> None:
		self.finished.set()