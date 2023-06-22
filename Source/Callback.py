from Source.DUBLIB import RemoveRegexSubstring
from MessageEditor import MessageEditor
from threading import Thread
from time import sleep

import telebot

class Callback:
    
    #==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Очередь отложенных сообщений.
	__MessagesBufer = list()
	# Callback-запрос.
	__CallbackRequest = None
	# Экземпляр бота.
	__TelegramBot = None
	# Глобальные настройки.
	__Settings = dict()
	# Поток отправки сообщений.
	__Sender = None

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Экранирует символы при использовании MarkdownV2 разметки.
	def __EscapeCharacters(self, Post: str) -> str:
		Post = Post.replace('.', "\.")
		Post = Post.replace('#', "\#")
		Post = Post.replace('!', "\!")
		Post = Post.replace('-', "\-")

		return Post

	# Обрабатывает очередь сообщений.
	def __SenderThread(self):
		print("Start thread")
		# Пока сообщение не отправлено.
		while True:

			# Если в очереди на отправку есть сообщения.
			if len(self.__MessagesBufer) > 0:

				try:
					# Попытка отправить сообщение.
					self.__TelegramBot.send_message(self.__Settings["group-id"], self.__MessagesBufer[0], parse_mode = self.__Settings["parse-mode"], disable_web_page_preview = self.__Settings["disable-web-page-preview"])

				except telebot.apihelper.ApiTelegramException as ExceptionData:
					# Описание исключения.
					Description = str(ExceptionData)

					# Если исключение вызвано частыми запросами, то выждать указанный интервал.
					if "Too Many Requests" in Description:
						sleep(int(Description.split()[-1]) + 1)

				else:
					# Удаление первого сообщения в очереди отправки.
					self.__MessagesBufer.pop(0)

			else:
				# Остановка потока.
				break

	# Отправляет сообщение в группу Telegram через буфер ожидания.
	def __SendMessage(self, Post: str):
		# Обработка текста поста пользовательским скриптом.
		Post = MessageEditor(Post)
		# Состояние: есть ли запрещённые слова в посте.
		HasBlacklistWords = False

		# Если включена очистка тегов.
		if self.__Settings["clean-tags"] == True:
			Post = RemoveRegexSubstring("@\w+", Post)

		# Для каждого запрещённого слова проверить соответствие словам поста.
		for ForbiddenWord in self.__Settings["blacklist"]:
			for Word in Post.split():

				# Если пост содержит запрещённое слово, то игнорировать его.
				if ForbiddenWord.lower() == Word.lower():
					HasBlacklistWords = True

		# Если сообщение не игнорируется.
		if Post != None and Post != "" and HasBlacklistWords == False:
			# Обрезка текста поста до максимально дозволенной длинны.
			Post = Post[:4096]

			# Экранировать символы при указанной разметке MarkdownV2.
			if self.__Settings["parse-mode"] == "MarkdownV2":
				Post = self.__EscapeCharacters(Post)

			# Помещение поста в очередь на отправку.
			self.__MessagesBufer.append(Post)
		
	# Конструктор: задаёт глобальные настройки и тело Callback-запроса.
	def __init__(self, Settings: dict):

		#---> Генерация свойств.
		#==========================================================================================#
		self.__Settings = Settings
		self.__TelegramBot = telebot.TeleBot(Settings["token"])
		self.__Sender = Thread(target = self.__SenderThread)

		# Запуск потока обработки буфера сообщений.
		self.__Sender.start()
		
	# Добавляет сообщение в очередь отправки.
	def AddMessageToBufer(self, CallbackRequest: dict):

		#---> Генерация свойств.
		#==========================================================================================#
		self.__CallbackRequest = CallbackRequest

		# Активировать поток, если не активен.
		if self.__Sender.is_alive() == False:
			self.__Sender = Thread(target = self.__SenderThread)
			self.__Sender.start()

		# Отправка сообщения в группу Telegram через буфер ожидания.
		self.__SendMessage(CallbackRequest["object"]["text"])