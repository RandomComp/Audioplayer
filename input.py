import utils

import asyncio

class Input:
	def __init__(self) -> None:
		self.input = utils.EventEmitter("input", max_handlers=1)

		self.key_pool: list[str] = []

		self.key_index = 0

		self.finished = asyncio.Event()
	
	async def bytes(self):
		loop = asyncio.get_running_loop()

		while not self.finished.is_set():
			key = await utils.get_input_byte(loop)

			self.key_pool.append(key)
	
	def next_byte(self, bytes: int=1) -> list[str]:
		key_pool_len = len(self.key_pool)
		
		if bytes == 1:
			if self.key_index >= key_pool_len:
				return "\0"
		
			result = self.key_pool.pop(self.key_index) if len(self.key_pool) > 0 else "\0"

			self.key_index += 1

			return result
		
		result = []
		
		for _ in range(bytes):
			key = self.key_pool.pop(self.key_index) if self.key_index < key_pool_len else "\0"
		
			self.key_index += 1

			result.append(key)

		return result
	
	def peek(self, peek_index: int=0) -> str:
		key_pool_len = len(self.key_pool)

		index = self.key_index + peek_index
		
		if index >= key_pool_len:
			return '\0'

		return self.key_pool[self.key_index]
	
	async def handler(self) -> None:
		while not self.finished.is_set():
			input_key = await self.next_byte()

			if input_key == "\x1B" and self.peek(1) == "[":
				byte = self.peek(2)

				if byte in "ABCD":
					input_arrows = "↑↓→←"

					input_key = input_arrows[ord(byte) - ord('A')]
			
			#utils.print(input_key, end='')

			await self.input.invoke(self, input_key)
	
	async def loop(self) -> None:
		return await asyncio.gather(self.handler(), self.bytes())