from telebot.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo
from MessageEditor import MessageEditor
from threading import Thread
from time import sleep

import requests
import logging
import telebot
import os
import re

# Обработчик запросов Callback API ВКонтакте.
class Callback:

	# Очищает сообщение от упоминаний в тегах ВКонтакте.
	def __CleanTags(self, Post: str) -> str:
		# Поиск всех совпадений.
		RegexSubstrings = re.findall("#\w+@\w+", Post)

		# Удаление каждой подстроки.
		for RegexSubstring in RegexSubstrings:
			Post = Post.replace("@" + RegexSubstring.split('@')[1], "")
		
		# Запись в лог отладочной информации: количество очищенных тегов ВКонтакте.
		logging.debug("Cleaned tags count: " + str(len(RegexSubstrings)) + ".")

		return Post

	# Экранирует символы при использовании MarkdownV2 разметки.
	def __EscapeCharacters(self, Post: str) -> str:
		# Список экранируемых символов. _ * [ ] ( ) ~ ` > # + - = | { } . !
		CharactersList = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

		# Экранировать каждый символ из списка.
		for Character in CharactersList:
			Post = Post.replace(Character, "\\" + Character)

		return Post

	# Получает URL вложения и загружает его.
	def __GetAttachements(self, PostAttachements: dict) -> list:
		# Список вложений.
		Attachements = list()
		# Список поддерживаемых вложений.
		SupportedTypes = list()

		# Формирование списка включённых вложений.
		for Type in self.__Settings["attachments"].keys():
			if self.__Settings["attachments"][Type] == True:
				SupportedTypes.append(Type)

		# Если нет папки для хранения вложений, то создать.
		if os.path.isdir("Temp") == False:
			os.makedirs("Temp")

		# Для каждого вложения проверить соответствие поддерживаемым типам.
		for Attachment in PostAttachements:
			for Type in SupportedTypes:

				# Если вложение поддерживается.
				if Attachment["type"] == Type:
					# Буфер описания вложения.
					Bufer = {
						"type": Type,
						"url": None,
						"filename": None
					}

					# Получение URL вложения и названия файла (doc).
					if Bufer["type"] == "doc":
						Bufer["url"] = Attachment[Type]["url"]
						Bufer["filename"] = Attachment[Type]["url"].split('?')[0].split('/')[-1] + "." + Attachment[Type]["ext"]
					
					# Получение URL вложения и названия файла (photo).
					if Bufer["type"] == "photo":
						Bufer["url"] = Attachment[Type]["sizes"][-1]["url"]
						Bufer["filename"] = Attachment[Type]["sizes"][-1]["url"].split('?')[0].split('/')[-1]

					# Получение URL вложения и названия файла (video).
					if Bufer["type"] == "video":
						Bufer["url"] = "https://vk.com/video" + str(Attachment[Type]["owner_id"]) + "_" + str(Attachment[Type]["id"])
						Bufer["filename"] = str(Attachment[Type]["id"]) + ".mp4"
					
					# Если вложение не было загружено раньше.
					if os.path.exists("Temp/" + Bufer["filename"]) == False:
						# Запись в лог отладочной информации: URL загружаемого вложения.
						logging.debug("Downloading attachment (\"" + Type + "\"): " + Bufer["url"])
						
						# Загрузка вложения (doc, photo).
						if Bufer["type"] in ["doc", "photo"]:
							# Запрос вложения.
							Response = requests.get(Bufer["url"])
					
							# Если удалось запросить вложение.
							if Response.status_code == 200:
								# Запись описания вложения в список вложений.
								Attachements.append(Bufer)
								
								# Сохранить вложение в файл.
								with open("Temp/" + Bufer["filename"], "wb") as FileWriter:
									FileWriter.write(Response.content)

							else:
								# Запись в лог ошибки: не удалось загрузить вложение.
								logging.error("Unable to download attachment (\"" + Type + "\"). Request code: " + str(Response.status_code) + ".")

						# Загрузка вложения (video).
						if Bufer["type"] == "video":
							# Загрузить видео с помощью кроссплатформенной версии yt-dlp.
							ExitCode = os.system("python yt-dlp -o " + Bufer["filename"] + " -P Temp " + Bufer["url"])

							# Если загрузка успешна.
							if ExitCode == 0:
								# Запись описания вложения в список вложений.
								Attachements.append(Bufer)

					else:
						# Запись описания вложения в список вложений.
						Attachements.append(Bufer)
						
		return Attachements

	# Обрабатывает очередь сообщений.
	def __SenderThread(self):
		# Запись в лог отладочной информации: поток очереди отправки запущен.
		logging.debug("Sender thread started.")

		# Пока сообщение не отправлено.
		while True:

			# Если в очереди на отправку есть сообщения.
			if len(self.__MessagesBufer) > 0:
				# Список медиа-вложений.
				MediaGroup = list()

				# Если у сообщения есть вложения.
				if len(self.__MessagesBufer[0]["attachments"]) > 0:

					# Для каждого вложения.
					for Index in range(0, len(self.__MessagesBufer[0]["attachments"])):

						# Если тип вложения – doc.
						if self.__MessagesBufer[0]["attachments"][Index]["type"] == "doc":
							# Дополнить медиа группу вложением (doc).
							MediaGroup.append(
								InputMediaDocument(
									open("Temp/" + self.__MessagesBufer[0]["attachments"][Index]["filename"], "rb"), 
									caption = self.__MessagesBufer[0]["text"] if Index == 0 else "",
									parse_mode = self.__Settings["parse-mode"] if Index == 0 else None
								)
							)

						# Если тип вложения – photo.
						if self.__MessagesBufer[0]["attachments"][Index]["type"] == "photo":
							# Дополнить медиа группу вложением (photo).
							MediaGroup.append(
								InputMediaPhoto(
									open("Temp/" + self.__MessagesBufer[0]["attachments"][Index]["filename"], "rb"), 
									caption = self.__MessagesBufer[0]["text"] if Index == 0 else "",
									parse_mode = self.__Settings["parse-mode"] if Index == 0 else None
								)
							)

						# Если тип вложения – video.
						if self.__MessagesBufer[0]["attachments"][Index]["type"] == "video":
							# Дополнить медиа группу вложением (video).
							MediaGroup.append(
								InputMediaVideo(
									open("Temp/" + self.__MessagesBufer[0]["attachments"][Index]["filename"], "rb"), 
									caption = self.__MessagesBufer[0]["text"] if Index == 0 else "",
									parse_mode = self.__Settings["parse-mode"] if Index == 0 else None
								)
							)

				try:
					
					# Если есть вложения.
					if len(MediaGroup) > 0:
						# Отправка медиа группы.
						self.__TelegramBots[self.__MessagesBufer[0]["source"]].send_media_group(
							self.__MessagesBufer[0]["target"], 
							media = MediaGroup
						)

					else:
						# Отправка текстового сообщения.
						self.__TelegramBots[self.__MessagesBufer[0]["source"]].send_message(
							self.__MessagesBufer[0]["target"], 
							self.__MessagesBufer[0]["text"], 
							parse_mode = self.__Settings["parse-mode"], 
							disable_web_page_preview = self.__Settings["disable-web-page-preview"]
						)
					
				except telebot.apihelper.ApiTelegramException as ExceptionData:
					# Описание исключения.
					Description = str(ExceptionData)

					# Если исключение вызвано частыми запросами, то выждать указанный интервал.
					if "Too Many Requests" in Description:
						sleep(int(Description.split()[-1]) + 1)

					else:
						# Запись в лог ошибки: исключение Telegram.
						logging.error("Telegram exception: \"" + Description + "\".")
						# Удаление первого сообщения в очереди отправки.
						self.__MessagesBufer.pop(0)

				else:
					# Удаление первого сообщения в очереди отправки.
					self.__MessagesBufer.pop(0)

			else:
				# Запись в лог отладочной информации: поток очереди отправки оставновлен.
				logging.debug("Sender thread stopped.")
				# Остановка потока.
				break

	# Отправляет сообщение в группу Telegram через буфер ожидания.
	def __SendMessage(self, PostObject: dict, Source: str):
		# Состояние: есть ли запрещённые слова в посте.
		HasBlacklistWords = False
		# Объект сообщения.
		MessageStruct = {
			"source": Source,
			"target": self.__Settings["targets"][Source],
			"text": None,
			"attachments": list()
		}

		# Экранировать символы при указанной разметке MarkdownV2.
		if self.__Settings["parse-mode"] == "MarkdownV2":
			PostObject["text"] = self.__EscapeCharacters(PostObject["text"])

		# Обработка текста поста пользовательским скриптом.
		PostObject["text"] = MessageEditor(PostObject["text"], Source)

		# Если сообщение не игнорируется.
		if PostObject["text"] != None and PostObject["text"] != "" and HasBlacklistWords == False:
			
			# Если включена очистка тегов, то удалить упоминания из них.
			if self.__Settings["clean-tags"] == True:
				PostObject["text"] = self.__CleanTags(PostObject["text"])

			# Для каждого запрещённого слова проверить соответствие словам поста.
			for ForbiddenWord in self.__Settings["blacklist"]:
				for Word in PostObject["text"].split():

					# Если пост содержит запрещённое слово, то игнорировать его.
					if ForbiddenWord.lower() == Word.lower():
						HasBlacklistWords = True

			# Обрезка текста поста до максимально дозволенной длинны.
			PostObject["text"] = PostObject["text"][:4096]
			# Копирование текста из поста в сообщение.
			MessageStruct["text"] = PostObject["text"]
			
			# Если есть вложения.
			if len(PostObject["attachments"]) > 0:
				MessageStruct["attachments"] = self.__GetAttachements(PostObject["attachments"])
			
			# Помещение поста в очередь на отправку.
			self.__MessagesBufer.append(MessageStruct)

		else:
			# Запись в лог отладочной информации: пост был проигнорирован.
			logging.debug("Post " + str(PostObject["id"]) + " was ignored.")

		# Активировать поток отправки, если не активен.
		if self.__Sender.is_alive() == False:
			self.__Sender = Thread(target = self.__SenderThread, name = "VK-Telegram Poster (sender)")
			self.__Sender.start()
		
	# Конструктор: задаёт глобальные настройки и тело Callback-запроса.
	def __init__(self, Settings: dict):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Экзмепляры обработчиков постов.
		self.__PostsEditorsThreads = list()
		# Очередь отложенных сообщений.
		self.__MessagesBufer = list()
		# Список экземпляров бота.
		self.__TelegramBots = dict()
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Поток отправки сообщений.
		self.__Sender = Thread(target = self.__SenderThread)

		# Запуск потока обработки буфера сообщений.
		self.__Sender.start()
		
		# Инициализация экзепляров бота.
		for Target in self.__Settings["tokens"].keys():
			self.__TelegramBots[Target] = telebot.TeleBot(self.__Settings["tokens"][Target])
		
	# Добавляет сообщение в очередь отправки.
	def AddMessageToBufer(self, CallbackRequest: dict, Source: str):

		# Проверка работы потоков.
		for Index in range(0, len(self.__PostsEditorsThreads)):

			# Если поток завершил работу, то удалить его из списка.
			if self.__PostsEditorsThreads[Index].is_alive() == False:
				self.__PostsEditorsThreads.pop(Index)

		# Добавление потока обработчика поста в список.
		self.__PostsEditorsThreads.append(Thread(target = self.__SendMessage, args = (CallbackRequest["object"], Source)))
		# Запуск потока обработчика поста в список.
		self.__PostsEditorsThreads[-1].start()