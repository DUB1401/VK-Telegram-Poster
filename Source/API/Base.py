from Source.BaseEditor import BaseEditor
from Source.Config import Config

from threading import Thread
from time import sleep
import logging
import os
import re

from telebot.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo
import requests
import telebot

class Base:
	"""Основание обработчиков API."""

	#==========================================================================================#
	# >>>>> НАСЛЕДУЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _CleanTags(self, post: str) -> str:
		"""Очищает теги в посту от упоминаний ВКонтакте."""
		
		RegexSubstrings = re.findall(r"#\w+@\w+", post)

		for RegexSubstring in RegexSubstrings:
			post = post.replace("@" + RegexSubstring.split('@')[1], "")
			
		return post
	
	def _ClearEditors(self):
		"""Удаляет объекты завершивших работу обработчиков постов."""

		for Index in range(len(self._PostsEditorsThreads)):
			if not self._PostsEditorsThreads[Index].is_alive(): self._PostsEditorsThreads.remove(self._PostsEditorsThreads[Index])

	def _ConvertAliases(self, text: str) -> str:
		"""
		Извлекает алиасы из текста ВКонтакте.
			text – текст сообщения.
		"""

		Pattern = r'\[#alias\|([^|]+)\|(https?://[^\]]+)\]'
		Replacement = r'<a href="\2">\1</a>'

		return re.sub(Pattern, Replacement, text)

	def _DownloadAttachments(self, post_id: int, data: dict) -> list:
		"""
		Скачивает вложения во временный каталог и возвращает список данных только доступных для отправки вложений.
			data – данные вложений.
		"""

		Attachements = list()

		for Attachment in data:
			Type = Attachment["type"]

			if self._Config.check_attachment_type_available(Type):
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

						else: logging.error(f"Unable to download attachment \"{Type}\". Request code: {Response.status_code}.")

					elif Buffer["type"] == "video":
						ExitCode = os.system("python yt-dlp -o " + Buffer["filename"] + " -P Temp " + Buffer["url"])
						if ExitCode == 0: Attachements.append(Buffer)

				else: Attachements.append(Buffer)
						
		logging.info(f"[{self._Name} API] Source: \"{self._Config.name}\". Post {post_id} contains " + str(len(Attachements)) + " supported attachments.")						

		return Attachements

	def _NormalizeMentions(self, text: str) -> str:
		"""
		Форматирует упоминания ВКонтакте в HTML-ссылки.
			text – текст сообщения.
		"""

		Pattern = r'\[id(\d+)\|([^\]]+)\]'
		Replacement = r'<a href="https://vk.com/id\1">\2</a>'
	
		return re.sub(Pattern, Replacement, text)

	def _ParseAttachments(self, attachments: list, caption: str) -> list[InputMediaDocument | InputMediaPhoto | InputMediaVideo]:
		"""
		Преобразует данные вложений в объекты Telegram.
			attachments – список данных вложений;\n
			caption – текст.
		"""

		MediaGroup = list()
		DocumentsGroup = list()
		caption = caption[:1023]
		
		for Index in range(len(attachments)):
			Input = None
			if Index > 0: caption = None

			Filename = attachments[Index]["filename"]
			Path = f"Temp/{Filename}"
			Filesize = int(os.path.getsize(Path) / (1024 * 1024))

			Types = {
				"doc": InputMediaDocument,
				"photo": InputMediaPhoto,
				"video": InputMediaVideo
			}

			for Type in Types.keys():
				
				if Type == attachments[Index]["type"]:
					if Filesize < 20: Input = Types[Type](open(Path, "rb"), caption = caption, parse_mode = "HTML")
					else: logging.warning(f"Attachment \"{Filename}\" is too large ({Filesize} MB).")
					break

			if type(Input) == InputMediaDocument: DocumentsGroup.append(Input)
			else: MediaGroup.append(Input)

		return MediaGroup, DocumentsGroup

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

		PostID = post["id"]
		logging.info(f"[{self._Name} API] Source: \"{self._Config.name}\". New post {PostID}.")

		HasBlacklistRegex = False
		AllowedTypes = ["post", "reply"]
		MessageStruct = {
			"text": None,
			"attachments": []
		}

		if post["text"]:
			for ForbiddenRegex in self._Config.blacklist:
				if re.search(ForbiddenRegex, post["text"], re.IGNORECASE):
					HasBlacklistRegex = True
					break

		post["text"] = self._ConvertAliases(post["text"])
		post["text"] = self._NormalizeMentions(post["text"])

		if not self._Config.donut_posts and post["donut"]["is_donut"]:
			logging.info(f"[{self._Name} API] Source: \"{self._Config.name}\". Donut post {PostID} was ignored.")
			return
		
		if self._Editor: 
			try: post["text"] = self._Editor.edit(post["text"])
			except Exception as ExceptionData:
				Type = type(ExceptionData).__qualname__
				logging.error(f"[{self._Name} API] Source: \"{self._Config.name}\". {Type}: {ExceptionData}.")

		if not post["text"] or HasBlacklistRegex or post["post_type"] not in AllowedTypes:
			logging.info(f"[{self._Name} API] Source: \"{self._Config.name}\". Post {PostID} was ignored.")
			return

		if self._Config.is_clean_tags: post["text"] = self._CleanTags(post["text"])
		MessageStruct["text"] = post["text"][:4096]
		if post["attachments"]: MessageStruct["attachments"] = self._DownloadAttachments(PostID, post["attachments"])
		self._MessagesBuffer.append(MessageStruct)

		self._StartSenderThread()

	def _Sender(self):
		"""Обработчик очереди постов."""

		logging.debug(f"[{self._Name} API] Sender thread started.")
		
		while self._MessagesBuffer:
			MediaGroups = tuple()
			if self._MessagesBuffer[0]["attachments"]: MediaGroups = self._ParseAttachments(self._MessagesBuffer[0]["attachments"], self._MessagesBuffer[0]["text"])
						
			try:
				
				if MediaGroups:
					for Group in MediaGroups:
						if Group: self._Config.bot.send_media_group(chat_id = self._Config.chat_id, media = Group)

				else: 
					self._Config.bot.send_message(
						chat_id = self._Config.chat_id,
						text = self._MessagesBuffer[0]["text"][:2047],
						parse_mode = "HTML", 
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

	def __init__(self, config: Config, editor: BaseEditor):
		"""
		Основание обработчиков API.
			editor – редактор постов;\n
			config – конфигурация источника.
		"""

		#---> Генерация динамических атриубтов.
		#==========================================================================================#
		self._Config = config
		self._Editor: BaseEditor = editor

		self._Name = self._Config.type.value
		self._MessagesBuffer = list()
		self._PostsEditorsThreads = list()

		self._SenderThread = Thread(target = self._Sender)

		self._PostInitMethod()