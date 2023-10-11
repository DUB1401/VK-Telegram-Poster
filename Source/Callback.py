from telebot.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo
from Source.Configurator import Configurator
from Source.BotsManager import BotsManager
from MessageEditor import MessageEditor
from Source.Datasets import API_Types
from Source.Functions import *
from threading import Thread
from time import sleep

import logging
import telebot

# Обработчик запросов Callback API ВКонтакте.
class Callback:

	# Обрабатывает очередь сообщений.
	def __SenderThread(self):
		# Запись в лог отладочной информации: поток очереди отправки запущен.
		logging.debug("[Callback API] Sender thread started.")
		
		# Пока сообщение не отправлено.
		while True:

			# Если в очереди на отправку есть сообщения.
			if len(self.__MessagesBufer) > 0:
				# Конфигурация источника.
				Config = self.__Configurations.getConfig(self.__MessagesBufer[0]["source"])
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
									parse_mode = Config["parse-mode"] if Index == 0 else None
								)
							)

						# Если тип вложения – photo.
						if self.__MessagesBufer[0]["attachments"][Index]["type"] == "photo":
							# Дополнить медиа группу вложением (photo).
							MediaGroup.append(
								InputMediaPhoto(
									open("Temp/" + self.__MessagesBufer[0]["attachments"][Index]["filename"], "rb"), 
									caption = self.__MessagesBufer[0]["text"] if Index == 0 else "",
									parse_mode = Config["parse-mode"] if Index == 0 else None
								)
							)

						# Если тип вложения – video.
						if self.__MessagesBufer[0]["attachments"][Index]["type"] == "video":
							# Дополнить медиа группу вложением (video).
							MediaGroup.append(
								InputMediaVideo(
									open("Temp/" + self.__MessagesBufer[0]["attachments"][Index]["filename"], "rb"), 
									caption = self.__MessagesBufer[0]["text"] if Index == 0 else "",
									parse_mode = Config["parse-mode"] if Index == 0 else None
								)
							)

				try:
					
					# Если есть вложения.
					if len(MediaGroup) > 0:
						# Отправка медиа группы.
						self.__Bots.getBot(self.__MessagesBufer[0]["token"]).send_media_group(
							self.__MessagesBufer[0]["target"], 
							media = MediaGroup
						)

					else:
						# Отправка текстового сообщения.
						self.__Bots.getBot(self.__MessagesBufer[0]["token"]).send_message(
							self.__MessagesBufer[0]["target"], 
							self.__MessagesBufer[0]["text"], 
							parse_mode = Config["parse-mode"], 
							disable_web_page_preview = Config["disable-web-page-preview"]
						)
					
				except telebot.apihelper.ApiTelegramException as ExceptionData:
					# Описание исключения.
					Description = str(ExceptionData)

					# Если исключение вызвано частыми запросами.
					if "Too Many Requests" in Description:
						# Запись в лог предупреждения: слишком много запросов.
						logging.warning("[Callback API]  Too many requests to Telegram. Waiting...")
						# Выждать указанный исключением интервал.
						sleep(int(Description.split()[-1]) + 1)

					else:
						# Запись в лог ошибки: исключение Telegram.
						logging.error("[Callback API] Telegram exception: \"" + Description + "\".")
						# Удаление первого сообщения в очереди отправки.
						self.__MessagesBufer.pop(0)
						
				except Exception as ExceptionData:
					# Запись в лог ошибки: исключение.
					logging.error("[Callback API] Exception: \"" + str(ExceptionData) + "\".")
					# Удаление первого сообщения в очереди отправки.
					self.__MessagesBufer.pop(0)

				else:
					# Удаление первого сообщения в очереди отправки.
					self.__MessagesBufer.pop(0)

			else:
				# Запись в лог отладочной информации: поток очереди отправки оставновлен.
				logging.debug("[Callback API] Sender thread stopped.")
				# Остановка потока.
				break

	# Отправляет сообщение в группу Telegram через буфер ожидания.
	def __SendMessage(self, PostObject: dict, Source: str, LaunchSenderThread: bool = True):
		# Состояние: есть ли запрещённые конструкции в посте.
		HasBlacklistRegex = False
		# Конфигурация источника.
		Config = self.__Configurations.getConfig(Source)
		# Объект сообщения.
		MessageStruct = {
			"source": Source,
			"token": Config["token"],
			"target": Config["target"],
			"text": None,
			"attachments": list()
		}

		# Экранировать символы при указанной разметке MarkdownV2.
		if Config["parse-mode"] == "MarkdownV2":
			PostObject["text"] = EscapeCharacters(PostObject["text"])

		# Обработка текста поста пользовательским скриптом.
		PostObject["text"] = MessageEditor(PostObject["text"] if PostObject["text"] != None else "", Source)
		
		# Для каждого регулярного выражения запрещённой конструкции.
		for ForbiddenRegex in Config["blacklist"]:
			
			# Если в тексте сообщения найдено совпадение с запрещённой конструкцией, игнорировать его.
			if re.search(ForbiddenRegex, PostObject["text"], re.IGNORECASE) != None:
				HasBlacklistRegex = True

		# Если сообщение не игнорируется.
		if PostObject["text"] != None and PostObject["text"] != "" and HasBlacklistRegex == False:
			
			# Если включена очистка тегов, то удалить упоминания из них.
			if Config["clean-tags"] == True:
				PostObject["text"] = CleanTags(PostObject["text"])

			# Обрезка текста поста до максимально дозволенной длинны.
			PostObject["text"] = PostObject["text"][:4096]
			# Копирование текста из поста в сообщение.
			MessageStruct["text"] = PostObject["text"]
			
			# Если есть вложения.
			if len(PostObject["attachments"]) > 0:
				# Список поддерживаемых вложений.
				SupportedTypes = list()
				
				# Формирование списка включённых вложений.
				for Type in self.__Configurations.getAttachments(Source).keys():
					if self.__Configurations.getAttachments(Source)[Type] == True:
						SupportedTypes.append(Type)
						
				# Получение вложений.
				MessageStruct["attachments"] = GetAttachments(PostObject["attachments"], Source, SupportedTypes, PostObject["id"], API_Types.Callback)
			
			# Помещение поста в очередь на отправку.
			self.__MessagesBufer.append(MessageStruct)

		else:
			# Запись в лог отладочной информации: пост был проигнорирован.
			logging.info(f"[Callback API] Source: \"{Source}\". Post with ID " + str(PostObject["id"]) + " was ignored.")

		# Если указано, активировать поток отправки сообщений.
		if LaunchSenderThread == True:
			self.__StartSenderThread()
		
	# Запускает поток отправки сообщений, если тот уже не запущен.
	def __StartSenderThread(self):
		 
		# Если поток отправки не функционирует, то запустить его.
		if self.__Sender.is_alive() == False:
			self.__Sender = Thread(target = self.__SenderThread, name = "[Open API] Sender.")
			self.__Sender.start()

	# Конструктор: задаёт глобальные настройки, обработчик конфигураций и менеджер подключений к ботам.
	def __init__(self, Settings: dict, ConfiguratorObject: Configurator, BotsManagerObject: BotsManager):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Поток отправки сообщений.
		self.__Sender = Thread(target = self.__SenderThread, name = "[Callback API] Sender.")
		# Конфигурации.
		self.__Configurations = ConfiguratorObject
		# Экзмепляры обработчиков постов.
		self.__PostsEditorsThreads = list()
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Менеджер подключений к ботам.
		self.__Bots = BotsManagerObject
		# Очередь отложенных сообщений.
		self.__MessagesBufer = list()
		
		# Инициализация экзепляров ботов.
		for ConfigName in self.__Configurations.getConfigsNames(API_Types.Callback):
			# Конфигурация источника.
			Config = self.__Configurations.getConfig(ConfigName)
			# Инициализация подключения к боту.
			self.__Bots.createBotConnection(Config["token"], ConfigName, Config["target"])
		
	# Добавляет сообщение в очередь отправки.
	def AddMessageToBufer(self, CallbackRequest: dict, Source: str):
		# Запись в лог сообщения: получен новый пост.
		logging.info(f"[Callback API] Source: \"{Source}\". New post with ID " + str(CallbackRequest["object"]["id"]) + ".")
		
		# Проверка работы потоков.
		for Index in range(0, len(self.__PostsEditorsThreads)):

			# Если поток завершил работу, то удалить его из списка.
			if self.__PostsEditorsThreads[Index].is_alive() == False:
				self.__PostsEditorsThreads.pop(Index)

		# Добавление потока обработчика поста в список.
		self.__PostsEditorsThreads.append(Thread(target = self.__SendMessage, args = (CallbackRequest["object"], Source), name = "[Callback API] Post editor."))
		# Запуск потока обработчика поста в список.
		self.__PostsEditorsThreads[-1].start()