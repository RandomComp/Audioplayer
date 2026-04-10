import asyncio

from pathlib import Path

from plyer import filechooser

import ansi

from menu import Menu

from translator import Translator

class FileChooser:
	def __init__(self, title: str="Choice a file", dir: Path=Path().home(), multiple: bool=False, gui: bool=True, translator: Translator=None):
		self.title = title

		if translator:
			self.title = translator.translate(self.title)

		self.gui = gui

		self.multiple = multiple

		self.translator = translator

		self.dir = dir

		self.finished = asyncio.Event()

		self.selected_files = []

		self.find_buf = ""

		self.find = asyncio.Event()

		if not gui:
			self.objs = []

			self.info = """arrows ↑↓ -- navigate
enter -- select
f -- find objects by name (including files, folders and symlinks, double esc to exit)
backspace -- go previous location
q -- quit menu"""

			self.__supported_extension_str = "Supported extensions"

			if translator:
				self.info = translator.translate(self.info)

				self.__supported_extension_str = self.translator.translate(self.__supported_extension_str)

			self.menu = Menu(title=self.title, info=self.info, multiple=self.multiple, translator=translator)

			self.menu.on_update_subcribe(self.menu.menu_cli_frame)

			self.menu.default_input.subscribe(self.menu.menu_default_input_handler)

			self.menu.input.subscribe(self.input_handler)

	async def input_handler(self, event_name: str, menu: Menu, option: int, input_key: str) -> None:
		if input_key in "\r\n" and len(self.objs) > option:
			view_options = [obj for obj in self.objs if not self.find.is_set() or self.find_buf.lower() in obj.name.lower()]
			
			obj: Path = view_options[option]

			if obj.is_file():
				if obj not in self.selected_files:
					self.selected_files.append(obj)
				else:
					self.selected_files.remove(obj)
				
				await self.menu.menu_select(option)

				if not self.multiple:
					self.menu.close()

					self.finished.set()

			elif obj.is_dir() or obj.is_symlink():
				self.dir = obj.resolve()
			
				self.menu.close()

		elif input_key in "\x08\x7F":
			if not self.find.is_set():
				old_dir = self.dir

				self.dir = self.dir.parent

				if old_dir != self.dir:
					self.menu.close()
			else:
				self.find_buf = self.find_buf[:(len(self.find_buf) - 1)]

				self.menu.set_find(self.find_buf)

		elif self.find.is_set():
			if input_key == "\x1B":
				self.menu.stop_find()

				self.find.clear()
			else:
				self.find_buf += input_key

				self.menu.set_find(self.find_buf)

		elif input_key == "q":
			self.finished.set()

		elif input_key == "f":
			self.menu.set_find()

			self.find.set()
	
	async def choice_file_gui(self, filters: list[str] | None=None) -> list[Path | None] | None:
		try:
			return map(Path, filechooser.open_file(filers=filters, multiple=self.multiple, title=self.title))
		except TypeError:
			return None
		
		# TODO: Написать свою альтернативу plyer.filechooser используя zenity и GetOpenFileName
	
	async def choice_file_cli(self, filters: list[str] | None=None) -> list[Path | None] | None:
		while not self.finished.is_set():
			objs = []
			
			retry = True

			self.menu.title = f"{self.title}: {self.dir}"

			while retry:
				try:
					objs = list(self.dir.iterdir())
				except FileNotFoundError:
					continue

				retry = False

			folders = []

			files = []

			for obj in objs:
				if obj.name.startswith("."):
					continue

				if obj.is_dir() or obj.is_symlink():
					folders.append(str(obj))
				elif obj.is_file() and (not filters or obj.suffix.lower() in filters):
					files.append(str(obj))
				
			folders = sorted(folders)
				
			files = sorted(files)

			menu_list = []

			self.objs.clear()

			for folder in folders:
				folder = Path(folder)

				self.objs.append(folder)

				menu_list.append(f"{ansi.lime_fg}{folder.name}/")
				
			for file in files:
				file = Path(file)

				self.objs.append(file)

				menu_list.append(file.name)

			await self.menu.reset()

			self.menu.full_options = self.objs

			self.menu.options = menu_list

			self.menu.option_cnt = len(menu_list)

			extension_string = "\", \"".join(filters) if filters else "All"

			self.menu.info = f"{self.info}\n{self.__supported_extension_str}: \"{extension_string}\""

			await self.menu.update()

			await self.menu.loop(filters=filters)

		return self.selected_files

	async def choice_file(self, filters: list[str] | None=None) -> list[Path | None] | None:
		result = []

		if self.gui:
			result = await self.choice_file_gui(filters=filters)
		else:
			result = await self.choice_file_cli(filters=filters)
		
		print(ansi.clear_screen)
		
		return result if self.multiple else result[0] if result else None