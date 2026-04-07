import audiostream

import numpy as np

import pydub

from pathlib import Path

from matplotlib import pyplot

import asyncio

import os

from platform import system

import ansi

import utils

import math

system_name = system().lower()

python_print = print

columns, rows = os.get_terminal_size()

async def show_graph(snippet: bytes | list | np.ndarray, samples: int=-1):
	snippet_len = len(snippet)
	
	if not snippet_len or samples == 0: return

	if samples == -1: samples = snippet_len

	pyplot.plot(snippet)

	loop = asyncio.get_running_loop()

	return await loop.run_in_executor(None, pyplot.show)

def show_device_info(device: dict):
	print(f"Device name: {ansi.green}\"{device['name']}\"{ansi.default}")

	print(f"    Device index: {ansi.cyan}{device['index']}{ansi.default}")

	print(f"    Device max output channels: {ansi.cyan}{device['maxOutputChannels']}{ansi.default}")

	print(f"    Device default output latency: {ansi.cyan}{device['defaultHighOutputLatency']:.4}{ansi.default} - {ansi.cyan}{device['defaultLowOutputLatency']:.4}{ansi.default} ms")

	print(f"    Device default sample rate: {ansi.cyan}{device['defaultSampleRate']}{ansi.default}")
	
class AudioPlayer:
	supported_extensions = (".mp4", ".mp3", ".wav", ".ogg", ".aac")

	def __init__(self, file: Path | str="", silent: bool=False, extra_volume: bool=False, mock: bool=False):
		# non for edit members:

		self.is_playing = asyncio.Event()

		self.seek = asyncio.Event()

		self.playback_ended = asyncio.Event()

		self.playback_error = asyncio.Event()

		self.ready_to_quit = asyncio.Event()

		self.closed = asyncio.Event()

		self.update_processing = asyncio.Event()

		self.update_display = utils.EventEmitter("update_display")

		self.__lines_outputed = 0
		
		self.progress_bar_c = "━"

		self.stream = None

		self.write_proc = None

		self.sound = None

		# for user members:

		self.file = Path(file)

		self.silent = silent

		self.second = 0

		self.seconds = 0

		self.volume = 0.5

		self.frame_rate = 44100

		self.channels = 2

		self.play_speed = 1

		self.chunk_seconds = 0.3

		self.mock = mock
		
		self.extra_volume = extra_volume
		
	async def open(self) -> None:
		if not self.silent:
			print("AudioPlayer initializing...")

			# print("Available sound devices for playback:\n")

			# for i in range(self.audio.get_device_count()):
			# 	device = self.audio.get_device_info_by_index(i)

			# 	if (device['maxOutputChannels'] == 0): continue

			# 	show_device_info(device)

			# 	print()

			print("Using default sound device for playback...")

		self.write_proc = None

		self.sound = None

		self.update_display.subscribe(self.display_update)

		await self.open_stream()

		show_device_info(self.stream.port.get_default_output_device_info())
	
	async def open_stream(self):
		if self.stream:
			if not self.silent:
				utils.print("Stream reopening... ", end='')

			await self.stream.close()

			self.stream = None
		elif not self.silent:
			utils.print("Stream opening... ", end='')

		self.stream = audiostream.AudioStream(self.frame_rate, self.channels, dtype=audiostream.paFloat32, input=False, chunked=False)

		self.stream.open()

		utils.print("done")
	
	def __output(self, *values: object, sep: str=" ", end: str="\n") -> None:
		string = f"{sep.join(map(str, values))}{end}"

		self.__lines_outputed += len(string.splitlines())

		utils.print(string, end='')
	
	def update(self) -> None:
		#columns, rows = utils.get_terminal_size()

		#for _ in range(self.__lines_outputed, rows):
		#	utils.print("\r".ljust(columns))

		#self.lines_outputed = 0

		utils.set_cursor_pos(0, 0)
	
	def display_volume(self, volume: float, columns: int) -> None:
		volume_max_width = columns

		volume_width = int(volume * volume_max_width)

		volume_mess = f"{ansi.cyan}{self.progress_bar_c * volume_width}{ansi.default}{self.progress_bar_c * (volume_max_width - volume_width)}"
					
		self.__output(f"\r{ansi.clear}{volume_mess}")

		volume_status_mess = f"volume {int(volume * 100)}%"
					
		self.__output(f"\r{ansi.clear}{utils.center(volume_status_mess, columns)}")
	
	def display_progress(self, second: float, seconds: float, columns: int) -> None:
		seconds_str = utils.format_time(seconds)

		seconds_str_len = len(seconds_str)

		progress_max_width = columns - seconds_str_len * 2 - 1

		second_str = utils.format_time(second)

		width = int((second / seconds if seconds > 0 else 1) * progress_max_width)

		progress_bar = f"{ansi.default}{ansi.lime_fg}{self.progress_bar_c * width}{ansi.default}{self.progress_bar_c * (progress_max_width - width)}"

		mess = f"{utils.ljust(second_str, seconds_str_len)}{progress_bar} {seconds_str}"
					
		self.__output(f"\r{ansi.clear}{mess}")

	def display_update(self, event_name: str) -> None:
		if self.update_processing.is_set():
			return

		self.update_processing.set()

		columns, rows = utils.get_terminal_size()

		self.__output(f"Press {ansi.bold}space{ansi.default} to play/stop")

		self.__output(f"Press {ansi.lime_fg}s{ansi.default} to seek")

		self.__output(f"Use {ansi.lime_fg}←→{ansi.default} to seek the audio")

		self.__output(f"Use {ansi.lime_fg}↑↓{ansi.default} to control the audio volume")

		self.__output(f"Press {ansi.lime_fg}q{ansi.default} to quit")

		self.display_volume(self.volume, columns)

		utils.set_cursor_pos(0, rows - 1)

		self.display_progress(self.second, self.seconds, columns)

		self.update()

		self.update_processing.clear()

	async def load(self) -> None:
		if not self.silent:
			self.__output(f"Playback file: \"{self.file}\"")

			self.__output(f"Loading... ", end="")

		try:
			self.sound = pydub.AudioSegment.from_file(self.file)
		except pydub.exceptions.CouldntDecodeError:
			if not self.silent:
				self.__output("error")

				raise RuntimeError(f"\"{self.file}\" is not valid audio file")

			self.playback_error.set()

			return

		if not self.silent:
			self.__output("done")

		self.seconds = self.sound.duration_seconds

	async def play_loop(self):
		if not self.stream:
			raise RuntimeError(f"Cannot play the audio: self.stream (aka {self.stream}) invalid")
		
		if not self.sound:
			raise RuntimeError(f"Cannot start the playing loop: no audio to play")

		if self.sound.frame_rate != self.frame_rate:
			self.__output(f"Frame rate mismatch between the sound ({self.sound.frame_rate}) and the speaker ({self.frame_rate}), reconfiguration...")

			self.frame_rate = self.sound.frame_rate

			self.channels = self.sound.channels

			await self.open_stream()

		if not self.silent:
			self.__output(f"Sound duration: {ansi.cyan}{utils.format_time(self.seconds)}{ansi.default}")
			self.__output(f"Sound dBFS: {ansi.cyan}{self.sound.dBFS:.2} dB{ansi.default}")
			self.__output(f"Sound channels: {ansi.cyan}{self.sound.channels}{ansi.default}")
			self.__output(f"Sound frame rate: {ansi.cyan}{self.sound.frame_rate}{ansi.default}")
			self.__output(f"Sound frame width: {ansi.cyan}{self.sound.frame_width}{ansi.default}")
			self.__output(f"Sound max sample: {ansi.cyan}{self.sound.max}{ansi.default}")
			self.__output(f"Sound max dBFS: {ansi.cyan}{self.sound.max_dBFS}{ansi.default}")
			self.__output(f"Sound max possible amplitude: {ansi.cyan}{self.sound.max_possible_amplitude}{ansi.default}")
			self.__output(f"Sound volume (rms): {ansi.cyan}{self.sound.rms}{ansi.default}")
			self.__output(f"Sound sample width: {ansi.cyan}{self.sound.sample_width}{ansi.default}")

			self.__output()
		
		self.__output(ansi.clear_screen, end='')

		self.stream.start()

		sample_chunks = int(self.chunk_seconds * self.sound.frame_rate)

		samples = self.sound.get_array_of_samples().tolist()

		samples = np.asarray(samples, dtype=np.float32) / (self.sound.max - 1)

		try:
			while self.second <= self.seconds and not self.playback_ended.is_set():
				await self.is_playing.wait()

				if not self.stream.is_playing.is_set():
					raise RuntimeError("Playing loop is back, but audio output stream is stopped.")

				pos = int(self.second * self.sound.frame_rate * 2)
				
				self.snippet = np.clip(samples[pos:(pos + sample_chunks)] * math.pow(self.volume, 2), -1.0, 1.0)

				if self.write_proc and not self.write_proc.done():
					await self.write_proc

					self.write_proc = None
						
				if self.mock:
					self.write_proc = asyncio.create_task(asyncio.sleep(self.chunk_seconds))
				else:
					self.write_proc = asyncio.create_task(self.stream.write(self.snippet, sample_chunks, self.sound.sample_width))

				self.second += self.chunk_seconds / 2
		finally:
			if self.write_proc and not self.write_proc.done():
				try:
					await asyncio.wait_for(self.write_proc, self.chunk_seconds)
				except TimeoutError:
					pass

				self.write_proc = None
			
			self.ready_to_quit.set()

			await self.close()
		
		self.__output()
	
	def play(self) -> None:
		self.is_playing.set()
	
	def pause(self) -> None:
		self.is_playing.clear()
	
	def volume_up(self, percent: float) -> None:
		self.volume_set(self.volume_get() + percent)
	
	def volume_down(self, percent: float) -> None:
		self.volume_set(self.volume_get() - percent)
	
	def volume_set(self, percent: float) -> None:
		if percent < 0:
			if not self.silent:
				print("Volume lower the 0% isn't supported. Forced using 0%.")

			percent = 0

		if percent > 100 and not self.extra_volume:
			if not self.silent:
				self.__output("Extra volume disabled, please enable it to set volume under 100%")

			percent = 100

		self.volume = percent / 100

	def volume_get(self) -> float:
		return self.volume * 100

	def seek_second(self, second: float) -> None:
		if second < 0:
			second %= self.seconds

		self.second = min(second, self.seconds)

	def get_cur_second(self) -> float:
		return self.second

	async def key_handler(self) -> None:
		loop = asyncio.get_running_loop()

		while not self.playback_ended.is_set():
			#get_input_byte_task = asyncio.create_task(utils.get_input_byte(loop))

			#tasks = [
			#	get_input_byte_task,
			#	asyncio.create_task(self.playback_ended.wait())
			#]
			
			#done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

			#for task in pending:
			#	task.cancel()

			#	try:
			#		await task
			#	except asyncio.CancelledError:
			#		pass
			
			#input_key = ""

			#if get_input_byte_task in done:
			#	try:
			#		input_key = get_input_byte_task.result()
			#	except asyncio.InvalidStateError:
			#		continue

			input_key = await utils.get_input_byte(loop)

			handled = False

			if input_key == "\x1B":
				try:
					next_byte = await asyncio.wait_for(utils.get_input_byte(loop), 0.3)

					if next_byte == "[":
						next_byte = await asyncio.wait_for(utils.get_input_byte(loop), 0.3)

						input_arrows = "↑↓→←"

						input_key = input_arrows[ord(next_byte) - ord('A')]
				except asyncio.exceptions.TimeoutError:
					pass

			seek_seconds = 1

			if input_key == "q":
				await self.close()

			elif input_key == " ":
				if self.is_playing.is_set():
					self.stream.stop()

					self.pause()
				else:
					self.stream.start()

					self.play()
				
				handled = True

			elif input_key == "s":
				if self.seek.is_set():
					self.seek.clear()
				else:
					self.seek.set()
				
				handled = True

			elif input_key == "↑":
				self.volume_up(1)
				
				handled = True

			elif input_key == "↓":
				self.volume_down(1)
				
				handled = True
			
			elif input_key == "←":
				self.seek_second(self.second - seek_seconds)
				
				handled = True
			
			elif input_key == "→":
				self.seek_second(self.second + seek_seconds)
				
				handled = True
			
			if handled:
				await self.update_display.invoke()
	
	async def timer(self, dur: float=1.0) -> None:
		while not self.playback_ended.is_set():
			await self.is_playing.wait()

			await self.update_display.invoke()

			await asyncio.sleep(dur)
	
	async def loop(self) -> None:
		await asyncio.gather(
			self.play_loop(),
			self.key_handler(),
			self.timer(1)
		)
	
	async def reset(self) -> None:
		self.__output("AudioPlayer reseting...")

		self.second = 0

		self.playback_error.clear()

		self.playback_ended.clear()

		self.ready_to_quit.clear()

		self.is_playing.set()

		self.seek.clear()

		self.update_display.subscribe(self.display_update)

		if not self.stream:
			await self.open_stream()
	
	async def close(self) -> None:
		self.playback_ended.set()

		self.seek.clear()

		self.is_playing.clear()

		if self.closed.is_set():
			return

		await self.ready_to_quit.wait()

		if self.stream:
			self.__output("AudioPlayer cleaning... ")

			await self.stream.close()

			self.stream = None

			self.__output("AudioPlayer cleaning done.")

		self.closed.set()
	
	async def __aenter__(self):
		await self.open()

		return self
	
	async def __aexit__(self, exc_type, exc, tb):
		await self.close()

	def __del__(self):
		pass