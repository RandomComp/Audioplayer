from librosa import load, get_duration, get_samplerate

from pathlib import Path

from mp3tag import id3tag

import numpy as np

class AudioLoader:
	def __init__(self, file: Path | str, segment_dur: int=30):
		file = Path(file).resolve()

		if not file.is_file():
			raise FileNotFoundError(f"No file specified \"{str(file)}\"")

		self.file = file

		self.segment_part = 0

		self.seconds = 0

		self.sample_rate = 0

		self.channels = 0

		self.segment_dur = segment_dur

		self.id3tag = id3tag.id3tag()
	
	def load(self) -> None:
		self.seconds = get_duration(path=self.file)

		self.sample_rate = get_samplerate(self.file)

		self.metadata = self.id3tag.get_tag(str(self.file))

		self.segment_samples = self.sample_rate * self.segment_dur

		self.segment = np.zeros(self.segment_samples)

	def next_segment(self, segment_begin: float=0) -> None:
		self.segment, self.segment_sample_rate = load(self.file, mono=False, offset=segment_begin, duration=self.segment_dur, dtype=np.float32)
	
	def load_segment(self, segment_num: float=0) -> None:
		return load(self.file, mono=False, sr=None, offset=segment_num * self.segment_dur, duration=self.segment_dur, dtype=np.float32)
	
	def __getitem__(self, key: int):
		if not isinstance(key, int):
			raise RuntimeError(f"\"{key}\" is not instance of int")
		
		#self.segment 