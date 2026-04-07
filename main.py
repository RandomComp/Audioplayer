from filechooser import FileChooser

from audioplayer import AudioPlayer

import ansi

import asyncio

import utils

#import input

from pathlib import Path

#from mp3tag import id3tag

async def main():
	choicer = FileChooser(dir=Path().home(), gui=False, multiple=True)

	files = await choicer.choice_file(filters=AudioPlayer.supported_extensions)

	# files = [Path("/mnt/SSD/Downloads/Песни/Любимые песни/Queen_-_Bohemian_Rhapsody_Remastered_2011_75941904.mp3")]

	if not files:
		print("No any file choiced")

		return

	player = None

	#id3 = id3tag.id3tag()

	player = AudioPlayer(mock=False)
			
	await player.open()

	for file in files:
		utils.print(f"Choiced file: {ansi.cyan}\"{file.name}\"{ansi.default}")

		if file.suffix.lower() not in AudioPlayer.supported_extensions:
			utils.print(f"File {ansi.cyan}\"{file.name}\"{ansi.default} with extension {ansi.cyan}\"{file.suffix.lower()}\"{ansi.default} unsupported")
			
			supported_extensions_str = f"\"{ansi.default}, {ansi.cyan}\"".join(AudioPlayer.supported_extensions)

			supported_extensions_str = f"{ansi.cyan}\"{supported_extensions_str}\"{ansi.default}"

			utils.print(f"Supported extensions: {supported_extensions_str}")

			return

		await player.reset()
	
		player.file = file

		await player.load()

		player.play()

		await player.loop()
		
		utils.print()

	#input_obj = input.Input()

	#await input_obj.loop()

if __name__ == "__main__":
	default_settings = utils.switch_to_raw()

	print(ansi.invisible_cursor, end='')

	try:
		asyncio.run(main())
	finally:
		print(ansi.visible_cursor, end='')

		utils.switch_to_default(default_settings)
