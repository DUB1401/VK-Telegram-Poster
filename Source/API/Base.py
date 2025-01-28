from Source.Manager import Config

from telebot.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo
from dublib.Polyglot import Markdown
from threading import Thread
from time import sleep

import requests
import logging
import telebot
import os
import re

class Base:
	"""Основание обработчиков API."""

	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _CleanTags(self, post: str) -> str:
		"""Очищает теги в посту от упоминаний ВКонтакте."""
		
		RegexSubstrings = re.findall("#\w+@\w+", post)

		for RegexSubstring in RegexSubstrings:
			post = post.replace("@" + RegexSubstring.split('@')[1], "")
			
		return post
	
	def _ClearEditors(self):
		"""Удаляет объекты завершивших работу обработчиков постов."""

		for Index in range(len(self._PostsEditorsThreads)):
			if not self._PostsEditorsThreads[Index].is_alive(): self._PostsEditorsThreads.remove(self._PostsEditorsThreads[Index])

	def _DownloadAttachments(self, data: dict) -> list:
		"""
		Скачивает вложения во временный каталог и возвращает список данных только доступных для отправки вложений.
			data – данные вложений.
		"""

		Attachements = list()

		for Attachment in data:
			Type = Attachment["type"]

			if self._Config.check_attachments_type(Type):
				Buffer = {
					"type": Type,
					"url": None,
					"filename": None
				}

				#---> Получение ссылок для вложения.
				#==========================================================================================#

				if Type == "doc":
					Buffer["url"] = Attachment[Type]["url"]
					Buffer["filename"] = Attachment[Type]["url"].split('?')[0].split('/')[-1] + "." + Attachment[Type]["ext"]
					
				elif Type == "photo":
					
					for Size in Attachment[Type]["sizes"]:
						if Size["type"] == "w": Buffer["url"] = Size["url"]
							
					if Buffer["url"] == None: Buffer["url"] = Attachment[Type]["sizes"][-1]["url"]	
					Buffer["filename"] = Buffer["url"].split('?')[0].split('/')[-1]

				elif Type == "video":
					Buffer["url"] = "https://vk.com/video" + str(Attachment[Type]["owner_id"]) + "_" + str(Attachment[Type]["id"])
					Buffer["filename"] = str(Attachment[Type]["id"]) + ".mp4"
					
				#---> Скачивание вложения.
				#==========================================================================================#
				Path = "Temp/" + Buffer["filename"]

				if not os.path.exists(Path):
					logging.debug("Downloading attachment (\"" + Type + "\"): " + Buffer["url"])
						
					if Buffer["type"] in ["doc", "photo"]:
						Response = requests.get(Buffer["url"])
					
						if Response.status_code == 200:
							Attachements.append(Buffer)
							with open("Temp/" + Buffer["filename"], "wb") as FileWriter: FileWriter.write(Response.content)

						else: logging.error("Unable to download attachment (\"" + Type + "\"). Request code: " + str(Response.status_code) + ".")

					elif Buffer["type"] == "video":
						ExitCode = os.system("python yt-dlp -o " + Buffer["filename"] + " -P Temp " + Buffer["url"])
						if ExitCode == 0: Attachements.append(Buffer)

				else: Attachements.append(Buffer)
						
		# logging.info(f"[{API_Type.value} API] Source: \"{Source}\". Post with ID {PostID} contains " + str(len(Attachements)) + " supported attachments.")						

		return Attachements

	def _ParseAttachments(self, attachments: list) -> list[InputMediaDocument | InputMediaPhoto | InputMediaVideo]:
		"""
		Преобразует данные вложений в объекты Telegram.
			attachments – список данных вложений.
		"""

		MediaGroup = list()
		
		for Index in range(len(attachments)):
			Input = None
			Caption = None
			ParseMode = None

			if Index == 0:
				Caption = attachments[0]["text"]
				ParseMode = self._Config.parse_mode

			match attachments[Index]["type"]:

				case "doc": Input = InputMediaDocument(open("Temp/" + attachments[Index]["filename"], "rb"), Caption, ParseMode)
				case "photo": Input = InputMediaPhoto(open("Temp/" + attachments[Index]["filename"], "rb"), Caption, ParseMode)
				case "video": Input = InputMediaVideo(open("Temp/" + attachments[Index]["filename"], "rb"), Caption, ParseMode)

			if Input: MediaGroup.append(Input)

		return MediaGroup

	def _PopMessage(self):
		"""Удаляет первое сообщение из буфера ожидания и очищает его вложения."""

		for Index in range(0, len(self._MessagesBuffer[0]["attachments"])):		
			Path = "Temp/" + self._MessagesBuffer[0]["attachments"][Index]["filename"]
			
			if os.path.exists(Path):
				os.remove(Path)
				logging.info(f"[{self._Name} API] File \"" + self._MessagesBuffer[0]["attachments"][Index]["filename"] + "\" removed.")

		self._MessagesBuffer.pop(0)

	def _PushMessage(self, post: dict):
		"""
		Парсит основные данные поста и добавляет их в буфер отправки.
			post – данные поста.
		"""

		# logging.info(f"[{self._Name} API] Source: \"{source}\". New post with ID " + str(data["object"]["id"]) + ".")

		HasBlacklistRegex = False
		AllowedTypes = ["post", "reply"]
		MessageStruct = {
			"text": None,
			"attachments": []
		}

		if self._Config.parse_mode == "MarkdownV2": post["text"] = Markdown(post["text"]).escaped_text

		# PostObject["text"] = MessageEditor(PostObject["text"] if PostObject["text"] != None else "", Source)
		
		for ForbiddenRegex in self._Config.blacklist:
			if re.search(ForbiddenRegex, post["text"] if post["text"] != None else "", re.IGNORECASE) != None: HasBlacklistRegex = True

		if post["text"] and HasBlacklistRegex == False and post["post_type"] in AllowedTypes:
			if self._Config.is_clean_tags: post["text"] = self._CleanTags(post["text"])
			MessageStruct["text"] = post["text"][:4096]
			if len(post["attachments"]): MessageStruct["attachments"] = self._DownloadAttachments(post["attachments"])
			self._MessagesBuffer.append(MessageStruct)

		else:
			# logging.info(f"[{self._Name} API] Source: \"{Source}\". Post with ID " + str(post["id"]) + " was ignored.")
			pass

		self._StartSenderThread()

	def _Sender(self):
		"""Обработчик очереди постов."""

		logging.debug(f"[{self._Name} API] Sender thread started.")
		
		while len(self._MessagesBuffer):
			MediaGroup = list()
						
			try:
				
				if len(MediaGroup):
					self._Config.bot.send_media_group(self._Config.chat_id, media = MediaGroup)

				else: 
					self._Config.bot.send_message(
						self._Config.chat_id,
						self._MessagesBuffer[0]["text"],
						self._Config.parse_mode, 
						disable_web_page_preview = self._Config.is_disable_web_page_preview
					)
				
			except telebot.apihelper.ApiTelegramException as ExceptionData:
				Description = str(ExceptionData)

				if "Too Many Requests" in Description:
					logging.warning(f"[{self._Name} API]  Too many requests to Telegram. Waiting...")
					sleep(int(Description.split()[-1]) + 1)

				else:
					logging.error(f"[{self._Name} API] Telegram exception: \"" + Description + "\".")
					self._PopMessage()
					
			except Exception as ExceptionData:
				logging.error(f"[{self._Name} API] Exception: \"" + str(ExceptionData) + "\".")
				self._PopMessage()

			else: self._PopMessage()

	def _StartSenderThread(self):
		"""Запускает поток обработки очереди."""
		 
		if not self._SenderThread.is_alive():
			self._SenderThread = Thread(target = self._Sender, name = f"[{self._Name} API] Sender.")
			self._SenderThread.start()

	#==========================================================================================#
	# >>>>> ПЕРЕГРУЖАЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _PostInitMethod(self):
		"""Метод, выполняемый после инициализации объекта."""

		pass

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, config: Config):
		"""
		Основание обработчиков API.
			config – конфигурация.
		"""

		#---> Генерация динамических атриубтов.
		#==========================================================================================#
		self._Config = config

		self._Name = self._Config.type.value
		self._MessagesBuffer = list()
		self._PostsEditorsThreads = list()

		self._SenderThread = Thread(target = self._Sender)

		self._PostInitMethod()