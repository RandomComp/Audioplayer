import utils

from pathlib import Path

from json import JSONDecoder

class Translator:
	def __init__(self, file: str | Path=None, translator_dict: dict=None, verbose: bool=False) -> None:
		if not translator_dict and not file:
			raise TypeError("Translator dict or file not provided")
		
		if file:
			if isinstance(file, str):
				translator_dict = JSONDecoder().decode(Path(file).read_text())
			else:
				raise TypeError(f"Expected str or Path, got {file}")

		self.verbose = verbose

		languages = translator_dict["languages"]
		
		self.translator_dict = dict()

		self.translator_dict["languages"] = translator_dict["languages"]
		
		for lang in languages:
			self.translator_dict[lang] = dict()

			for word in translator_dict[lang]:
				self.translator_dict[lang][word.lower()] = translator_dict[lang][word].lower()
		
		self.cache = {}
	
	def __output(self, *values: object, sep: str=" ", end: str="\n") -> None:
		utils.print(*values, sep=sep, end=end)

	def translate(self, _text: str, language: str | None=None) -> str:
		if self.verbose:
			self.__output(f"Input text: \"{_text}\"")

		is_capitalized = _text[0].isupper()

		text = _text.lower().strip()

		#text = text.split(" ")

		#punctuation_marks = ".,!?:-\"()"

		#for mark in punctuation_marks:
		#	

		languages = self.list_languages()

		lang = languages[0]

		if language in languages:
			lang = language
		elif language and language != lang:
			self.__output(f"Unknown language \"{language}\".\nNative language fallback...")
		
		if lang in self.cache and \
			text in self.cache[lang]:
			result = self.cache[lang][text]

			if self.verbose:
				self.__output(f"Using cached \"{result}\" for \"{text}\"")

			return result

		words_dict = self.translator_dict[lang]

		occurences = utils.ListGenerator(word.lower() for word in words_dict if word.lower() in text.lower())

		result = text

		occurences = sorted(occurences, key=len, reverse=True)

		result_index = -1

		try:
			result_index = occurences.index(text.lower())
		except ValueError:
			result_index = -1

		if result_index != -1:
			occurence = occurences[result_index]

			result = words_dict[occurence]

		else:
			if self.verbose:
				self.__output(f"Closest occurences:", occurences)

			for occurence in occurences:
				if occurence not in result: continue

				if self.verbose:
					self.__output(f"\"{occurence}\" --> \"{words_dict[occurence]}\"")
				
				result = result.replace(occurence, words_dict[occurence])
		
		if lang not in self.cache:
			self.cache[lang] = dict()
		
		self.cache[lang][text] = result

		return result.capitalize() if is_capitalized else result
	
	def print(self, *_values: object, sep: str=" ", end: str="\n") -> None:
		values = ((self.translate(value) if isinstance(value, str) else value) for value in _values)

		string = f"{sep.join(values)}{end}"

		self.__output(string, end='')
	
	def source_language(self) -> str:
		return self.translator_dict["from"]
	
	def list_languages(self) -> list[str]:
		return self.translator_dict["languages"]
	
	def __repr__(self):
		return f"Translator(from=\'{self.source_language()}\', to={self.list_languages()})"