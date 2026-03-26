from menu import Menu

from filechooser import FileChooser

import asyncio

import utils

import ansi

from time import time

async def main():
	# menu = Menu(
	# 	["Hello", 
	# 	"World!", 
	# 	"Grok", 
	# 	"ChatGPT", 
	# 	"DeepSeek", 
	# 	"Alice", 
	# 	"Mom", 
	# 	"I", 
	# 	"you", 
	# 	"Do", 
	# 	"know", 
	# 	"wanna", 
	# 	"to", 
	# 	"love", 
	# 	"too", 
	# 	"so", 
	# 	"much", 
	# 	"and", 
	# 	"fuck", 
	# 	"you", 
	# 	"10", 
	# 	"11", 
	# 	"12", 
	# 	"13", 
	# 	"14", 
	# 	"15", 
	# 	"16", 
	# 	"17", 
	# 	"18", 
	# 	"19", 
	# 	"20", 
	# 	"21", 
	# 	"22", 
	# 	"23", 
	# 	"24", 
	# 	"25", 
	# 	"26", 
	# 	"27", 
	# 	"28", 
	# 	"29"], 
	# 	title="Hello!"
	# )

	# menu.input.subscribe(menu.default_input_handler)

	# selected = await menu.loop()

	# print(f"Selected: {selected}")
	start = time()

	columns, _ = utils.get_terminal_size()

	while True:
		dur = time() - start
		
		string = utils.text_scroller("Мама, знаешь что? ТЫ У МЕНЯ САМАЯ ЛУЧШАЯ НА СВЕТЕ МАМА! Я тебя люблю!", 20, dur)
		
		utils.print(f"\r{string}", end='')

		await asyncio.sleep(0.01)

	#chooser = FileChooser(gui=False)

	#await chooser.loop()

if __name__ == "__main__":
	#default_settings = utils.switch_to_raw()

	print(ansi.invisible_cursor, end='')

	try:
		asyncio.run(main())
	finally:
		utils.print()
		print(ansi.visible_cursor, end='')

	#	utils.switch_to_default(default_settings)