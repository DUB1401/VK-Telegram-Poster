from telebot.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo
from vk_api.exceptions import AuthError, ApiError
from dublib.Methods import ReadJSON, WriteJSON
from Source.Configurator import Configurator
from Source.BotsManager import BotsManager
from MessageEditor import MessageEditor
from vk_captcha import VkCaptchaSolver
from Source.Datasets import API_Types
from Source.Functions import *
from threading import Thread
from vk_api import VkApi
from time import sleep

import telebot

# Название API.
API_NAME = "Open"

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
				
			except AuthError as ExceptionData:	
				# Запись в лог ошибки: исключение авторизации.
				logging.error(f"[{API_NAME} API] Authorization exception: " + str(ExceptionData).split(" Please")[0])
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
			
		except ApiError as ExceptionData:
			# Запись в лог ошибки: исключение API.
			logging.error(f"[{API_NAME} API] Exception: " + str(ExceptionData))
		
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
				
					# Если ID обрабатываемого поста больше ID последнего отправленного поста.
					if Post["id"] > Config["last-post-id"]:
						# Записать пост.
						Posts.append(Post)
						
					else:
						# Переключить состояние обновления.
						IsUpdated = True
						
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
	
	# Удаляет из очереди первое сообщение.
	def __PopMessage(self):

		# Если включен режим очистки вложений.
		if self.__Settings["autoclean"]:

			# Для каждого вложения.
			for Index in range(0, len(self.__MessagesBufer[0]["attachments"])):		
				# Путь к файлу.
				FilePath = 	"Temp/" + self.__MessagesBufer[0]["attachments"][Index]["filename"]
				
				# Если файл существует.
				if os.path.exists(FilePath):
					# Удаление файла.
					os.remove(FilePath)
					# Запись в лог сообщения: файл удалён.
					logging.info(f"[{API_NAME} API] File \"" + self.__MessagesBufer[0]["attachments"][Index]["filename"] + "\" removed.")

		# Удаление из очереди первого сообщения.
		self.__MessagesBufer.pop(0)

	# Обрабатывает очередь сообщений.
	def __SenderThread(self):
		# Запись в лог отладочной информации: поток очереди отправки запущен.
		logging.debug(f"[{API_NAME} API] Sender thread started.")
		
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
						logging.warning(f"[{API_NAME} API] Too many requests to Telegram. Waiting...")
						# Выждать указанный исключением интервал.
						sleep(int(Description.split()[-1]) + 1)

					else:
						# Запись в лог ошибки: исключение Telegram.
						logging.error(f"[{API_NAME} API] Telegram exception: \"" + Description + "\"." + self.__MessagesBufer[0]["text"])
						# Удаление первого сообщения в очереди отправки.
						self.__PopMessage()
						
				except Exception as ExceptionData:
					# Запись в лог ошибки: исключение.
					logging.error(f"[{API_NAME} API] Exception: \"" + str(ExceptionData) + "\".")
					# Удаление первого сообщения в очереди отправки.
					self.__PopMessage()

				else:
					# Удаление первого сообщения в очереди отправки.
					self.__PopMessage()

			else:
				# Запись в лог отладочной информации: поток очереди отправки оставновлен.
				logging.debug(f"[{API_NAME} API] Sender thread stopped.")
				# Остановка потока.
				break

	# Отправляет сообщение в группу Telegram через буфер ожидания.
	def __SendMessage(self, PostObject: dict, Source: str, LaunchSenderThread: bool = True):
		# Состояние: есть ли запрещённые конструкции в посте.
		HasBlacklistRegex = False
		# Список разрешённых типов постов.
		AllowedTypes = ["post", "reply"]
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
			if re.search(ForbiddenRegex, PostObject["text"] if PostObject["text"] != None else "", re.IGNORECASE) != None:
				HasBlacklistRegex = True

		# Если сообщение не игнорируется.
		if PostObject["text"] != None and PostObject["text"] != "" and HasBlacklistRegex == False and PostObject["post_type"] in AllowedTypes:
			
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
				MessageStruct["attachments"] = GetAttachments(PostObject["attachments"], Source, SupportedTypes, PostObject["id"], API_Types.Open)
			
			# Помещение поста в очередь на отправку.
			self.__MessagesBufer.append(MessageStruct)

		else:
			# Запись в лог отладочной информации: пост был проигнорирован.
			logging.info(f"[{API_NAME} API] Source: \"{Source}\". Post with ID " + str(PostObject["id"]) + " was ignored.")

		# Если указано, активировать поток отправки сообщений.
		if LaunchSenderThread == True:
			self.__StartSenderThread()
			
	# Запускает поток отправки сообщений, если тот уже не запущен.
	def __StartSenderThread(self):
		 
		# Если поток отправки не функционирует, то запустить его.
		if self.__Sender.is_alive() == False:
			self.__Sender = Thread(target = self.__SenderThread, name = f"[{API_NAME} API] Sender.")
			self.__Sender.start()
			
	# Поток-надзиратель.
	def __SupervisorThread(self):
		# Запись в лог отладочной информации: запущен поток-надзиратель.
		logging.debug(f"[{API_NAME} API] Repeater supervisor thread started.")
		
		# Запуск цикла проверки.
		while True:
			# Выжидание минуты.
			sleep(60)
			
			# Если поток получения обновлений внезапно остановился.
			if self.__Repeater.is_alive() == False:
				# Переключение состояния обновления.
				self.__IsUpdating = False
				# Экземпляр повторителя.
				self.__Repeater = Thread(target = self.__UpdaterThread, name = f"[{API_NAME} API] Requests repeater.")
				# Запуск повторителя проверок.
				self.__Repeater.start()
				# Запись в лог предупреждения: поток проверки сообщений перещапущен.
				logging.warning(f"[{API_NAME} API] Requests repeater thread restarted.")
			
	# Поток отправки запросов к ВКонтакте.
	def __UpdaterThread(self, ImmediatelyUpdate: bool = False):
		
		try:
			
			# Немедленная проверка новых постов.
			if ImmediatelyUpdate == True:
				self.CheckUpdates()
		
			# Запуск цикла ожидания.
			while True:
				# Выжидание одной секунды.
				sleep(self.__Settings["openapi-period"] * 60)
				# Проверка новых постов.
				self.CheckUpdates()
				
		except Exception as ExceptionData:
			# Переформатирование сообщения исключения.
			ExceptionData = str(ExceptionData).split('\n')[0].rstrip(".:")
			# Запись в лог ошибки: исключение во время проверки обновлений.
			logging.error(f"[{API_NAME} API] Updater exception: \"" + ExceptionData + "\".")
				
	# Записывает ID последнего отправленного поста.
	def __WriteLastPostID(self, Source: str, ID: int):
		# Чтение конфигурации.
		Config = ReadJSON(f"Config/{Source}.json")
		# Обновление ID.
		Config["last-post-id"] = ID
		# Запись обновлённой конфигурации.
		WriteJSON(f"Config/{Source}.json", Config)

	# Конструктор: задаёт глобальные настройки, обработчик конфигураций и менеджер подключений к ботам.
	def __init__(self, Settings: dict, ConfiguratorObject: Configurator, BotsManagerObject: BotsManager):
	
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Поток-надзиратель.
		self.__Supervisor = Thread(target = self.__SupervisorThread, name = f"[{API_NAME} API] Repeater thread supervisor.")
		# Поток проверки обновлений.
		self.__Repeater = Thread(target = self.__UpdaterThread, args = [True], name = f"[{API_NAME} API] Requests repeater.")
		# Поток отправки сообщений.
		self.__Sender = Thread(target = self.__SenderThread, name = f"[{API_NAME} API] Sender.")
		# Конфигурации.
		self.__Configurations = ConfiguratorObject
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Менеджер подключений к ботам.
		self.__Bots = BotsManagerObject
		# Очередь отложенных сообщений.
		self.__MessagesBufer = list()
		# Состояние: идёт ли обновление.
		self.__IsUpdating = False
		# Сессия ВКонтакте.
		self.__Session = None  
		# Экземпляр API.
		self.__API = None

		# Авторизация и получение API.
		self.__Authorizate()
		
		# Инициализация экзепляров ботов.
		for ConfigName in self.__Configurations.getConfigsNames(API_Types.Open):
			# Конфигурация источника.
			Config = self.__Configurations.getConfig(ConfigName)
			# Инициализация подключения к боту.
			self.__Bots.createBotConnection(Config["token"], ConfigName, Config["target"])
			
		# Запуск повторителя проверок.
		self.__Repeater.start()
		
		# Если указано настройками, запустить поток-надзиратель.
		if Settings["use-supervisor"] == True:
			self.__Supervisor.start()
			
	# Интервально проверяет обновления и добавляет сообщения в очередь отправки.
	def CheckUpdates(self):
		
		# Если обновление не выполняется.
		if self.__IsUpdating == False:
			# Переключение статуса обновления.
			self.__IsUpdating = True
			# Обновление конфигураций с Open API.
			self.__Configurations.updateConfigs(API_Types.Open)
			# Получение списка конфигураций, использующих Open API.
			Configs = self.__Configurations.getConfigsNames(API_Types.Open)
			# Список постов.
			Posts = list()
		
			# Для каждой конфигурации.
			for Source in Configs:	
				# Получение списка новых постов (инверитрование порядка для обработки в порядке возрастания даты публикации).
				Posts = list(reversed(self.__GetUpdates(Source)))
				
				# Запись ID последнего отправленного поста в конфигурацию.
				if len(Posts) > 0:
					self.__WriteLastPostID(Source, Posts[-1]["id"])		

				# Запись в лог сообщения: количество обновлённых постов.
				logging.info(f"[{API_NAME} API] Source: \"{Source}\". Updates checked. New posts count: " + str(len(Posts)) + ".")
				
				# Для каждого поста.
				for Post in Posts:
					# Запись в лог сообщения: получен новый пост.
					logging.info(f"[{API_NAME} API] Source: \"{Source}\". New post with ID " + str(Post["id"]) + ".")
					# Отправка сообщения в буфер ожидания.
					self.__SendMessage(Post, Source, LaunchSenderThread = False)
					
			# Запуск потока отправки сообщений.
			self.__StartSenderThread()
			# Переключение статуса обновления.
			self.__IsUpdating = False
			
		else:
			# Запись в лог предупреждения: обновление уже выполняется.
			logging.warning(f"[{API_NAME} API] Update already in progress. Skipped.")