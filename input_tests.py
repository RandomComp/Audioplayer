from input import Input

import asyncio

import utils

async def input_handler(_: str, self: Input, input_key: str) -> None:
	if input_key != "\0":
		print(input_key)
	
	if input_key == "q":
		self.finished.set()

async def main() -> None:
	input_obj = Input()

	input_obj.input.subscribe(input_handler)

	await input_obj.loop()

if __name__ == "__main__":
	default_settings = utils.switch_to_raw()

	try:
		asyncio.run(main())
	finally:
		utils.switch_to_default(default_settings)