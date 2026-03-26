import asyncio

from pathlib import Path

import ansi

import utils

from plyer import filechooser

from os import get_terminal_size

from menu import Menu

class FileChooser:
	def __init__(self, title: str="Choice a file", multiple: bool=False, gui: bool=True):
		self.gui = gui

		self.finished = asyncio.Event()

		self.dir = Path("/mnt/")

		self.objs = []

		self.menu = Menu(title=title, multiple=multiple)

		self.menu.input.subscribe(self.input_handler)

	async def input_handler(self, *args, **kwargs) -> None:
		option = args[1]

		input_key: str = args[2]

		if input_key == "q":
			self.menu.finished.set()

			self.finished.set()

		elif input_key == "↑":
			self.menu.sel_option = max(self.menu.sel_option - 1, 0)
		elif input_key == "↓":
			self.menu.sel_option = max(min(self.menu.sel_option + 1, self.menu.option_cnt - 1), 0)

		elif input_key in "\r\n":
			if option >= self.menu.option_cnt:
				print("Attempt to select option outside of the list.")

				return

			obj = Path(self.objs[option])

			print(f"obj: {obj}")

			if obj.is_file():
				if option not in self.menu.selected_options:
					self.menu.selected_options.append(option)
				else:
					self.menu.selected_options.remove(option)
			elif obj.is_dir():
				self.dir = obj
			elif obj.is_symlink():
				self.dir = obj.resolve()
			
			self.menu.finished.set()
		elif input_key in "\x08\x7F":
			self.dir = self.dir.parent

		self.menu.update.set()

	async def choice_file(self, filters: list[str] | None=None) -> list[Path | None] | None:
		result = None

		if self.gui:
			try:
				result = map(Path, filechooser.open_file(filers=filters, multiple=self.multiple, title=self.title))
			except TypeError:
				return None
		else:
			while not self.finished.is_set():
				objs = list(self.dir.iterdir())

				folders = [obj for obj in objs if obj.is_dir()]

				files = [obj for obj in objs if obj.is_file()]

				menu_list = []

				self.objs.clear()

				for folder in folders:
					self.objs.append(folder)

					menu_list.append(f"{ansi.lime_fg}{folder}/{ansi.default_fg}")
				
				for file in files:
					self.objs.append(file)

					menu_list.append(f"{ansi.default_fg}{file}")

				self.menu.reset()

				self.menu.options = list(map(str, self.objs))

				self.menu.option_cnt = len(menu_list)

				self.menu.update.set()

				await self.menu.loop(filters)

		return result

	async def loop(self, filters: list[Path | str] | None=None) -> list[Path | None] | None:
		return await self.choice_file(filters)