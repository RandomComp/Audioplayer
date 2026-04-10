import numpy as np

import asyncio

from pyaudio import PyAudio, paFloat32, paInt32, paInt24, paInt16, paInt8, paUInt8

from utils import print

from translator import Translator

class AudioStream:
	def __init__(self, sample_rate: int=44100, channels: int=2, dtype=paFloat32, input: bool=False, chunked: bool=True, chunk_seconds: float=0.5, translator: Translator=None) -> None:
		self.port = None

		self.stream = None

		self.translator = translator

		self.sample_rate = sample_rate

		self.channels = channels

		self.dtype = dtype

		self.input = input # False means output, and True means input

		self.chunk_size = int(chunk_seconds * self.sample_rate * self.channels)

		self.chunked = chunked

		self.async_loop = asyncio.get_running_loop()

		self.ready_to_finish = asyncio.Event()

		self.finished = asyncio.Event()

		self.is_playing = asyncio.Event()

		self.is_playing.set()

		self.write_proc = None
	
	def __translated_output(self, *values: object, sep: str=" ", end: str="\n") -> None:
		print(self.__translated(*values, sep=sep), end=end)
	
	def __translated(self, *values: object, sep: str=" ") -> None:
		values_str = []

		for value in values:
			value_str = str(value)

			if isinstance(value, str):
				if self.translator:
					value_str = self.translator.translate(value_str)

			values_str.append(value_str)
		
		return sep.join(values_str)

	def open(self) -> None:
		if self.port == None:
			self.port = PyAudio()
		
		self.close_stream()
		
		self.stream = self.port.open(self.sample_rate, self.channels, self.dtype, input=self.input, output=not self.input)

	def start(self) -> None:
		self.is_playing.set()

		#if self.stream == None:
		#	self.open()

		#self.stream.start_stream()

	async def write_wrapper(self, frames: np.ndarray, frames_size: int, bytes_per_frame: int=4) -> None:
		frames = bytes(frames)

		frames_len = len(frames)

		if frames_len == 0 or frames_size <= 0 or self.finished.is_set():
			#print(frames_size, self.finished.is_set())

			return

		self.ready_to_finish.clear()

		frames_size = min(frames_len, frames_size) // bytes_per_frame

		await self.async_loop.run_in_executor(None, self.stream.write, frames, frames_size)

		self.ready_to_finish.set()
	
	async def write_chunk(self, frames: np.ndarray, bytes_per_frame: int=4) -> None:
		if not self.stream:
			raise IOError(self.__translated("Stream is invalid."))
		
		frames_len = len(frames)

		frames_size = self.chunk_size

		if frames_size == -1: frames_size = frames_len

		else:
			frames_size = min(frames_size, self.chunk_size)

		await self.write_wrapper(frames, frames_size, bytes_per_frame)
	
	def next_chunk(self, _frames: np.ndarray, frames_size: int=-1):
		frames = _frames.copy()

		frames_len = len(frames)
		
		if frames_size == 0: return

		if frames_size == -1: frames_size = frames_len

		st_i = 0

		while st_i <= frames_size:
			chunk = frames[st_i:(st_i + self.chunk_size)]

			frames_size = min(frames_len, frames_size)

			yield chunk

			st_i += self.chunk_size

	async def write(self, frames: np.ndarray, frames_size: int=-1, bytes_per_frame: int=4) -> None:
		if not self.stream:
			raise IOError(self.__translated("Stream is invalid."))
		
		await self.is_playing.wait()

		frames = np.clip(frames, -1.0, 1.0)
		
		frames_len = len(frames)
		
		if frames_size == 0: return

		if frames_size == -1: frames_size = frames_len

		if self.chunked:
			for chunk in self.next_chunk(frames, frames_size):
				await self.write_chunk(chunk, bytes_per_frame)
		else:
			frames_size = min(frames_len, frames_size)
			
			await self.write_wrapper(frames, frames_size, bytes_per_frame)
	
	async def read(self) -> None:
		raise NotImplementedError()

	def stop(self) -> None:
		self.is_playing.clear()

		#if self.stream == None:
		#	return

		#self.stream.stop_stream()

	def close_stream(self) -> None:
		if self.stream != None:
			self.stream.stop_stream()

			self.stream.close()

			self.stream = None

	async def close(self) -> None:
		self.__translated_output("AudioStream cleaning...")

		ready_to_quit_wait_task = asyncio.create_task(self.ready_to_finish.wait())

		try:
			await asyncio.wait_for(ready_to_quit_wait_task, timeout=5)
		except asyncio.exceptions.TimeoutError:
			self.__translated_output("Timeouted.")

			ready_to_quit_wait_task.cancel()

			self.ready_to_finish.set()
		finally:
			self.is_playing.clear()

			self.close_stream()
			
			if self.port != None:
				self.port.terminate()

				self.stream = None
			
			self.finished.set()
		
		self.__translated_output("AudioStream cleaning done.")

	async def __aenter__(self):
		await self.start()
		
		return self

	async def __aexit__(self, exc_type, exc_value, traceback) -> bool:
		await self.close()

		return False