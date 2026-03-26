import asyncio

import sys

from utils import *

import ansi

import numpy as np

class Menu:
	def __init__(self, options: list[str]=[], title: str="Menu", multiple: bool=False) -> None:
		self.options = options

		self.option_cnt = len(options)

		self.title = title
		
		self.multiple = multiple

		self.input = EventEmitter("input", max_handlers=1)

		self.update = asyncio.Event()

		self.finished = asyncio.Event()

		self.sel_option = 0

		self.old_sel_item = 0

		self.selected_options: list[bool] = []
	
	async def default_input_handler(self, *args, **kwargs) -> None:
		option = args[1]

		input_key: str = args[2]

		if option >= self.option_cnt:
			print("Attempt to select option outside of the list.")

			return

		if input_key == "q":
			self.finished.set()

		elif input_key == "↑":
			self.sel_option = max(self.sel_option - 1, 0)
		elif input_key == "↓":
			self.sel_option = min(self.sel_option + 1, self.option_cnt - 1)

		elif input_key in "\r\n":
			if option not in self.selected_options:
				self.selected_options.append(option)
			else:
				self.selected_options.remove(option)

		self.update.set()
	
	async def menu_key_handler(self) -> None:
		loop = asyncio.get_running_loop()

		while not self.finished.is_set():
			input_key = await get_input_byte(loop)

			if input_key == "\x1B":
				try:
					next_byte = await asyncio.wait_for(get_input_byte(loop), 0.3)

					if next_byte == "[":
						next_byte = await asyncio.wait_for(get_input_byte(loop), 0.3)

						input_arrows = "↑↓→←"

						input_key = input_arrows[ord(next_byte) - ord('A')]
				except asyncio.exceptions.TimeoutError:
					pass

			await self.input.invoke(self.sel_option, input_key)
	
	async def menu_cli(self, filters: list[str]) -> list[str | None]:
		self.old_sel_item = self.sel_option

		while not self.finished.is_set():
			set_cursor_pos(0, 0)

			columns, rows = get_terminal_size()

			print(self.title.center(columns))

			options_display_cnt = min(self.option_cnt, rows - 3 - 1 - 1)

			options_display_start = 0

			if self.sel_option >= options_display_cnt:
				options_display_start = self.sel_option - options_display_cnt + 1

			for i in range(options_display_start, options_display_start + options_display_cnt):
				selected = self.sel_option == i

				color = ansi.default_fg

				selected_color = ansi.black_fg

				option = self.options[i]

				if selected:
					print(f"{ansi.white_bg}{selected_color}{option.ljust(columns)}{ansi.default}")
				else:
					print(f"{color}{ansi.default_bg}{option.ljust(columns)}{ansi.default}")
				
			print(f"selected item: {self.sel_option}".ljust(columns))

			options_string = '\", \"'.join([self.options[option] for option in self.selected_options])
				
			print(f"selected: \"{options_string}\"".ljust(columns))

			await self.update.wait()

			self.update.clear()
		
		return self.selected_options
	
	async def menu_gui(self) -> list[str | None]:
		raise NotImplementedError()
		
		return self.selected_options

	def reset(self) -> None:
		self.finished.clear()
		self.update.clear()
		self.selected_options.clear()
		self.sel_option = 0
		self.options.clear()
		self.option_cnt = 0

	async def loop(self, filters: list[str] | None=None) -> list[str | None]:
		return (await asyncio.gather(self.menu_cli(filters), self.menu_key_handler()))[0]
	