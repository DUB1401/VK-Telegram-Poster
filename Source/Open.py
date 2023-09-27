from telebot.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo
from dublib.Methods import ReadJSON, WriteJSON
from Source.Configurator import Configurator
from MessageEditor import MessageEditor
from vk_captcha import VkCaptchaSolver
from threading import Thread, Timer
from Source.Functions import *
from vk_api import VkApi
from time import sleep

import telebot

# Обработчик запросов Open API ВКонтакте.
class Open:
	
	# Выполняет авторизацию.
	def __Authorizate(self):
		# Менеджер обработки каптчи.
		CaptchaSolver = VkCaptchaSolver(logging = False)
		# Состояние: решена ли каптча.
		IsUncaptched = False
		
		# Пока не будет решена каптча.
		while IsUncaptched == False:
			
			try:
				# Установка логина, пароля и обработчика каптчи.
				self.__Session = VkApi(
					self.__Settings["login"], 
					self.__Settings["password"], 
					app_id = self.__Settings["app-id"], 
					token = self.__Settings["vk-access-token"],
					captcha_handler = CaptchaSolver.vk_api_captcha_handler
				)
				
				# Если токен не используется, то авторизоваться.
				if self.__Settings["vk-access-token"] == None:
					self.__Session.auth(token_only = True)
				
			except VkApi.exceptions.AuthError as ExceptionData:	
				# Запись в лог ошибки: исключение авторизации.
				logging.error("[Open API] Authorization exception: " + str(ExceptionData).split(" Please")[0])
				# Выжидание интервала.
				sleep(5)
				
			else:
				# Переключение состояния решения каптчи.
				IsUncaptched = True
				
		# Получение экземпляра API.
		self.__API = self.__Session.get_api()

	# Возвращает список постов.
	def __GetPosts(self, WallID: str, PostsCount: int = 20, Offset: int = 0) -> list[dict]:
		# Добавление минуса к ID стены.
		WallID = "-" + str(WallID).strip("-")
		# Список полученных постов.
		WallPosts = list()
		
		try:
			# Попытка получить список постов.
			WallPosts = self.__API.wall.get(owner_id = WallID, count = PostsCount, offset = Offset)["items"]
			
		except VkApi.exceptions.ApiError as ExceptionData:
			# Запись в лог ошибки: исключение API.
			logging.error("[Open API] Exception: " + str(ExceptionData))
		
		return WallPosts
	
	# Возвращает список постов, опубликованных с момента последней проверки.
	def __GetUpdates(self, ConfigName: str) -> list[dict]:
		# Состояние: найден ли ранее опубликованный пост.
		IsUpdated = False
		# Список вышедших постов.
		Posts = list()
		# Получение конфигурации.
		Config = self.__Configurations.getConfig(ConfigName)
		# Индекс запроса.
		RequestIndex = 0
		
		# Пока не будет найдено обновление.
		while IsUpdated == False:
			# Получение последних 20 постов.
			Bufer = self.__GetPosts(Config["wall-id"], Offset = 20 * RequestIndex)

			# Если ID последнего отправленного поста записан.
			if Config["last-post-id"] != None:

				# Для каждого полученного поста.
				for Post in Bufer:
				
					# Если ID обрабатываемого поста меньше или равен ID последнего отправленного поста.
					if Post["id"] <= Config["last-post-id"]:
						# Переключить состояние обновления.
						IsUpdated = True
				
					else:
						# Записать пост.
						Posts.append(Post)
						
			else:
				# Записать последний пост.
				Posts.append(Bufer[0])
				# Переключить состояние обновления.
				IsUpdated = True
					
			# Инкремент индекса запроса.
			RequestIndex += 1
			
			# Если ожидается ещё один запрос, выждать время.
			if IsUpdated == False:
				sleep(5)

		return Posts	
	
	# Обрабатывает очередь сообщений.
	def __SenderThread(self):
		# Запись в лог отладочной информации: поток очереди отправки запущен.
		logging.debug("Open API sender thread started.")

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
									parse_mode = self.__Configurations.getConfig(self.__MessagesBufer[0]["source"])["parse-mode"] if Index == 0 else None
								)
							)

						# Если тип вложения – photo.
						if self.__MessagesBufer[0]["attachments"][Index]["type"] == "photo":
							# Дополнить медиа группу вложением (photo).
							MediaGroup.append(
								InputMediaPhoto(
									open("Temp/" + self.__MessagesBufer[0]["attachments"][Index]["filename"], "rb"), 
									caption = self.__MessagesBufer[0]["text"] if Index == 0 else "",
									parse_mode = self.__Configurations.getConfig(self.__MessagesBufer[0]["source"])["parse-mode"] if Index == 0 else None
								)
							)

						# Если тип вложения – video.
						if self.__MessagesBufer[0]["attachments"][Index]["type"] == "video":
							# Дополнить медиа группу вложением (video).
							MediaGroup.append(
								InputMediaVideo(
									open("Temp/" + self.__MessagesBufer[0]["attachments"][Index]["filename"], "rb"), 
									caption = self.__MessagesBufer[0]["text"] if Index == 0 else "",
									parse_mode = self.__Configurations.getConfig(self.__MessagesBufer[0]["source"])["parse-mode"] if Index == 0 else None
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
							parse_mode = self.__Configurations.getConfig(self.__MessagesBufer[0]["source"])["parse-mode"], 
							disable_web_page_preview = self.__Configurations.getConfig(self.__MessagesBufer[0]["source"])["disable-web-page-preview"]
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
						
				except Exception as ExceptionData:
					# Запись в лог ошибки: исключение.
					logging.error("Exception: \"" + str(ExceptionData) + "\".")
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
			"target": self.__Configurations.getConfig(Source)["target"],
			"text": None,
			"attachments": list()
		}

		# Экранировать символы при указанной разметке MarkdownV2.
		if self.__Configurations.getConfig(Source)["parse-mode"] == "MarkdownV2":
			PostObject["text"] = EscapeCharacters(PostObject["text"])

		# Обработка текста поста пользовательским скриптом.
		PostObject["text"] = MessageEditor(PostObject["text"] if PostObject["text"] != None else "", Source)
		
		# Для каждого запрещённого слова проверить соответствие словам поста.
		for ForbiddenWord in self.__Configurations.getConfig(Source)["blacklist"]:
			for Word in PostObject["text"].split():

				# Если пост содержит запрещённое слово, то игнорировать его.
				if ForbiddenWord.lower() == Word.lower():
					HasBlacklistWords = True

		# Если сообщение не игнорируется.
		if PostObject["text"] != None and PostObject["text"] != "" and HasBlacklistWords == False:
			
			# Если включена очистка тегов, то удалить упоминания из них.
			if self.__Configurations.getConfig(Source)["clean-tags"] == True:
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
				MessageStruct["attachments"] = GetAttachments(PostObject["attachments"], Source, SupportedTypes, PostObject["id"])
			
			# Помещение поста в очередь на отправку.
			self.__MessagesBufer.append(MessageStruct)

		else:
			# Запись в лог отладочной информации: пост был проигнорирован.
			logging.info(f"Source: \"{Source}\". Post with ID " + str(PostObject["id"]) + " was ignored.")

		# Активировать поток отправки, если не активен.
		if self.__Sender.is_alive() == False:
			self.__Sender = Thread(target = self.__SenderThread, name = "VK-Telegram Poster (Open API sender)")
			self.__Sender.start()
			
	# Записывает ID последнего отправленного поста.
	def __WriteLastPostID(self, Source: str, ID: int):
		# Чтение конфигурации.
		Config = ReadJSON(f"Config/{Source}.json")
		# Обновление ID.
		Config["last-post-id"] = ID
		# Запись обновлённой конфигурации.
		WriteJSON(f"Config/{Source}.json", Config)

	# Конструктор: задаёт глобальные настройки и обработчик конфигураций.
	def __init__(self, Settings: dict, ConfiguratorObject: Configurator):
	
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Поток отправки сообщений.
		self.__Sender = Thread(target = self.__SenderThread)
		# Конфигурации.
		self.__Configurations = ConfiguratorObject
		# Экзмепляры обработчиков постов.
		self.__PostsEditorsThreads = list()
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Очередь отложенных сообщений.
		self.__MessagesBufer = list()
		# Список экземпляров бота.
		self.__TelegramBots = dict()
		# Сессия ВКонтакте.
		self.__Session = None  
		# Обработчик повторов.
		self.__Repiter = None
		# Экземпляр API.
		self.__API = None
		
		# Авторизация и получение API.
		self.__Authorizate()
		# Запуск потока обработки буфера сообщений.
		self.__Sender.start()
		
		# Инициализация экзепляров бота.
		for Target in self.__Configurations.getConfigsNames("Open"):
			self.__TelegramBots[Target] = telebot.TeleBot(self.__Configurations.getToken(Target))
			
		# Немедленная проверка новых постов и активация таймера.
		self.CheckUpdates()
			
	# Интервально проверяет обновления и добавляет сообщения в очередь отправки.
	def CheckUpdates(self):
		# Обновление конфигураций с Open API.
		self.__Configurations.updateOpenConfigs()
		# Получение списка конфигураций, использующих Open API.
		Configs = self.__Configurations.getConfigsNames("Open")
		# Количество новых постов.
		NewPostsCount = 0
		# Список постов.
		Posts = list()
		
		# Проверка работы потоков.
		for Index in range(0, len(self.__PostsEditorsThreads)):

			# Если поток завершил работу, то удалить его из списка.
			if self.__PostsEditorsThreads[Index].is_alive() == False:
				self.__PostsEditorsThreads.pop(Index)
		
		# Для каждой конфигурации.
		for Source in Configs:
			# Получение списка новых постов (инверитрование порядка для обработки в порядке возрастания даты публикации).
			Posts = list(reversed(self.__GetUpdates(Source)))
			# Подсчёт количества новых постов.
			NewPostsCount += len(Posts)
			
			# Для каждого поста.
			for Post in Posts:
				# Запись в лог сообщения: получен новый пост.
				logging.info(f"Source: \"{Source}\". New post with ID " + str(Post["id"]) + ".")
				# Добавление потока обработчика поста в список.
				self.__PostsEditorsThreads.append(Thread(target = self.__SendMessage, args = (Post, Source)))
				# Запуск потока обработчика поста в список.
				self.__PostsEditorsThreads[-1].start()
				
		
		# Запись ID последнего отправленного поста в конфигурацию.
		if len(Posts) > 0:
			self.__WriteLastPostID(Source, Posts[-1]["id"])
		
		# Запись в лог сообщения: количество обновлённых постов.
		logging.info(f"[Open API] Updates checked. New posts count: {NewPostsCount}.")
		# Активация таймера.
		self.__Repiter = Timer(float(self.__Settings["openapi-period"] * 60), self.CheckUpdates)
		self.__Repiter.start()