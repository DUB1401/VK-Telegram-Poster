from ..API import Types

from dublib.Methods.JSON import ReadJSON, WriteJSON

import logging
import telebot

class AttachmentsStatus:
	"""Контейнер статусов вложений."""

	@property
	def doc(self) -> bool:
		"""Состояние: пересылать ли документы."""

		return self.__Data["doc"]
	
	@property
	def photo(self) -> bool:
		"""Состояние: пересылать ли фото."""

		return self.__Data["photo"]
	
	@property
	def video(self) -> bool:
		"""Состояние: пересылать ли видео."""

		return self.__Data["video"]

	def __init__(self, data: dict):
		"""
		Контейнер статусов вложений.
			data – словарь статусов вложений.
		"""
		
		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self.__Data = data

class Config:
	"""Конфигурация для обработчика API."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def app_id(self) -> int | None:
		"""Идентификатор приложения ВКонтакте."""

		return self.__Data["app_id"]

	@property
	def attachments(self) -> AttachmentsStatus:
		"""Статусы вложений."""

		return self.__Attachments

	@property
	def blacklist(self) -> list[str]:
		"""Список запрещённых выражений."""

		return self.__Data["blacklist"]

	@property
	def bot(self) -> telebot.TeleBot:
		"""Бот Telegram."""

		return self.__Bot

	@property
	def chat_id(self) -> int:
		"""ID группы или канала Telegram."""

		return self.__Data["chat_id"]
	
	@property
	def is_clean_tags(self) -> bool:
		"""Состояние: включена ли очистка тегов ВКонтакте."""

		return self.__Data["clean_tags"]
	
	@property
	def is_disable_web_page_preview(self) -> bool:
		"""Состояние: включать ли предпросмотр ссылок."""

		return self.__Data["disable_web_page_preview"]

	@property
	def last_post_id(self) -> int | None:
		"""ID последнего полученного поста."""

		return self.__Data["last_post_id"]

	@property
	def login(self) -> str | None:
		"""Логин ВКонтакте."""

		return self.__Data["login"]

	@property
	def name(self) -> str:
		"""Название конфигурации."""

		return self.__Name

	@property
	def period(self) -> int | None:
		"""Период запроса обновлений."""

		return self.__Data["period"]

	@property
	def parse_mode(self) -> str | None:
		"""Режим парсинга сообщений."""

		return self.__Data["parse_mode"]
	
	@property
	def password(self) -> str | None:
		"""Пароль ВКонтакте."""

		return self.__Data["password"]

	@property
	def type(self) -> Types:
		"""Тип API."""

		return self.__Data["api"]
	
	@property
	def vk_token(self) -> str | None:
		"""Токен ВКонтакте."""

		return self.__Data["vk_token"]
	
	@property
	def wall_id(self) -> int | None:
		"""Идентификатор стены ВКонтакте."""

		return self.__Data["wall_id"]

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __Read(self):
		"""Читает файл конфигурации и проверяет его корректность."""

		Data = ReadJSON(self.__Path)

		for Key in self.__Data.keys():

			if Key not in Data.keys():
				Data[Key] = self.__Data[Key]
				logging.warning(f"Option \"{Key}\" dropped to default in \"{self.__Name}\" config.")

		if Data["api"].lower() == "callback": Data["api"] = Types.Callback
		elif Data["api"].lower() == "longpoll": Data["api"] = Types.LongPoll
		elif Data["api"].lower() == "open": Data["api"] = Types.Open

		self.__Data = Data

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, name: str):
		"""
		Конфигурация для обработчика API.
			name – название конфигурации.
		"""
		
		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self.__Name = name

		self.__Path = f"Configs/{name}.json"
		self.__Data = {
			"api": None,
			"bot_token": None,
			"chat_id": None,

			"clean_tags": True,
			"parse_mode": None,
			"disable_web_page_preview": True,

			"blacklists": [],
			"attachments": {
				"doc": True,
				"photo": True,
				"video": True
			},

			"login": None,
			"password": None,
			"app_id": 6121396,
			"vk_token": None,
			"wall_id": None,
			"period": 60,
			"last_post_id": None
		}

		self.__Read()

		self.__Bot = telebot.TeleBot(self.__Data["bot_token"])
		self.__Attachments = AttachmentsStatus(self.__Data["attachments"])

	def check_attachments_type(self, type: str) -> bool:
		"""
		Проверяет, включена ли пересылка типа вложения.
			type – тип.
		"""

		match type:
			case "doc": return self.attachments.doc
			case "photo": return self.attachments.photo
			case "video": return self.attachments.video

		raise Exception(f"No attacnhments type: \"{type}\".")
	
	def save(self):
		"""Сохраняет файл конфигурации."""

		WriteJSON(self.__Path, self.__Data)

	def set_last_post_id(self, post_id: int, save: bool = True):
		"""
		Задаёт ID последнего полученного поста.
			post_id – идентификатор;\n
			save – указывает, нужно ли выполнить сохранение.
		"""

		self.__Data["last_post_id"] = post_id
		if save: self.save()