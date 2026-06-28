import asyncio
from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method, dbus_property, PropertyAccess
from dbus_next import Variant

class MprisRootInterface(ServiceInterface):
	def __init__(self):
		super().__init__('org.mpris.MediaPlayer2')

	@dbus_property(access=PropertyAccess.READ)
	def CanQuit(self) -> 'b': return False

	@dbus_property(access=PropertyAccess.READ)
	def CanRaise(self) -> 'b': return False

	@dbus_property(access=PropertyAccess.READ)
	def HasTrackList(self) -> 'b': return False

	@dbus_property(access=PropertyAccess.READ)
	def Identity(self) -> 's': return "r-audio"

	@dbus_property(access=PropertyAccess.READ)
	def SupportedUriSchemes(self) -> 'as': return ['file']

	@dbus_property(access=PropertyAccess.READ)
	def SupportedMimeTypes(self) -> 'as': return ['audio/mpeg', 'audio/ogg']

	@dbus_property(access=PropertyAccess.READ)
	def DesktopEntry(self) -> 's': return ''


class MprisPlayerInterface(ServiceInterface):
	def __init__(self):
		super().__init__('org.mpris.MediaPlayer2.Player')
		self._status = 'Stopped'
		self.vol = 1.0
		self.second = 12

	@dbus_property(access=PropertyAccess.READ)
	def CanControl(self) -> 'b': return True

	# --- Существующие свойства ---
	@dbus_property(access=PropertyAccess.READ)
	def PlaybackStatus(self) -> 's':
		return self._status

	@dbus_property(access=PropertyAccess.READ)
	def Metadata(self) -> 'a{sv}':
		return {
			'mpris:trackid': Variant('o', '/com/my_player/track/1'),
			'xesam:title': Variant('s', 'Мой Асинхронный Трек'),
		}

	@dbus_property(access=PropertyAccess.READ)
	def CanPause(self) -> 'b': return True

	@dbus_property(access=PropertyAccess.READ)
	def CanPlay(self) -> 'b': return True

	@dbus_property(access=PropertyAccess.READ)
	def CanGoNext(self) -> 'b': return True

	@dbus_property(access=PropertyAccess.READ)
	def CanGoPrevious(self) -> 'b': return True

	@dbus_property(access=PropertyAccess.READ)
	def CanSeek(self) -> 'b': return True

	@dbus_property(access=PropertyAccess.READ)
	def CanSetPosition(self) -> 'b': return True

	@dbus_property(access=PropertyAccess.READ)
	def LoopStatus(self) -> 's': return 'None'

	@dbus_property(access=PropertyAccess.READ)
	def Shuffle(self) -> 'b': return False

	@dbus_property(access=PropertyAccess.READWRITE)
	def Volume(self) -> 'd': return self.vol  # Громкость от 0.0 до 1.0

	@Volume.setter
	def Volume(self, val: 'd'):
		self.vol = val

		print(f"[D-Bus] Команда: ГРОМКОСТЬ НА {val}")

		self.emit_properties_changed({'Volume': val})

	@dbus_property(access=PropertyAccess.READ)
	def Position(self) -> 'x': return int(self.second * 1000 * 1000)

	@method()
	def Seek(self, val: 'x'):
		self.second = val / (1000 * 1000)

		print(f"[D-Bus] Команда: ПЕРЕМОТКА НА {val}")

		self.Seeked(val)
	
	@method(name='Seeked')
	def Seeked(self, Position: 'x'):
		pass

	# --- Методы управления ---
	@method()
	async def Play(self):
		self._status = 'Playing'
		print("[D-Bus] Команда: ИГРАТЬ")
		self.emit_properties_changed({'PlaybackStatus': self._status})

	@method()
	async def Pause(self):
		self._status = 'Paused'
		print("[D-Bus] Команда: ПАУЗА")
		self.emit_properties_changed({'PlaybackStatus': self._status})

	@method()
	async def Stop(self):
		self._status = 'Stopped'
		print("[D-Bus] Команда: СТОП")
		self.emit_properties_changed({'PlaybackStatus': self._status})

	@method()
	async def PlayPause(self):
		# Переключаем статус туда-обратно
		if self._status == 'Playing':
			self._status = 'Paused'
			print("[D-Bus] Команда: ПАУЗА")
			self.emit_properties_changed({'PlaybackStatus': self._status})
		else:
			self._status = 'Playing'
			print("[D-Bus] Команда: ИГРАТЬ")
			self.emit_properties_changed({'PlaybackStatus': self._status})
			
	@method()
	async def Previous(self):
		print("[D-Bus] Команда: ПРЕДЫДУЩИЙ ТРЕК")


	@method()
	async def Next(self):
		print("[D-Bus] Команда: СЛЕДУЮЩИЙ ТРЕК")


# =====================================================================
# 3. ТОЧКА ВХОДА И РЕГИСТРАЦИЯ
# =====================================================================
async def main():
	bus = await MessageBus().connect()
	
	root_interface = MprisRootInterface()
	player_interface = MprisPlayerInterface()
	
	# Экспортируем ОБА интерфейса на один и тот же системный путь
	bus.export('/org/mpris/MediaPlayer2', root_interface)
	bus.export('/org/mpris/MediaPlayer2', player_interface)
	
	# Запрашиваем уникальное имя для нашего плеера в системе
	await bus.request_name("org.mpris.MediaPlayer2.r_audio_player")
	
	print("Чисто асинхронный MPRIS2 плеер запущен и настроен...")
	await asyncio.get_running_loop().create_future()

	await bus.release_name("org.mpris.MediaPlayer2.r_audio_player")

try:
	asyncio.run(main())
except KeyboardInterrupt:
	print("\nОстановлено.")
