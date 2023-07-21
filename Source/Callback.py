from MessageEditor import MessageEditor
from threading import Thread
from time import sleep

import logging
import telebot
import re

class Callback:
    
    #==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Очередь отложенных сообщений.
	__MessagesBufer = list()
	# Экземпляр бота.
	__TelegramBot = None
	# Глобальные настройки.
	__Settings = dict()
	# Поток отправки сообщений.
	__Sender = None

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

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

	# Обрабатывает очередь сообщений.
	def __SenderThread(self):
		# Запись в лог отладочной информации: поток очереди отправки запущен.
		logging.debug("Sender thread started.")

		# Пока сообщение не отправлено.
		while True:

			# Если в очереди на отправку есть сообщения.
			if len(self.__MessagesBufer) > 0:

				try:
					# Попытка отправить сообщение.
					self.__TelegramBot.send_message(self.__Settings["target-id"], self.__MessagesBufer[0]["text"], parse_mode = self.__Settings["parse-mode"], disable_web_page_preview = self.__Settings["disable-web-page-preview"])

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
	def __SendMessage(self, PostObject: dict):
		# Состояние: есть ли запрещённые слова в посте.
		HasBlacklistWords = False
		# Объект сообщения.
		MessageStruct = {
			"text": None,
			"attachments": list()
		}

		# Экранировать символы при указанной разметке MarkdownV2.
		if self.__Settings["parse-mode"] == "MarkdownV2":
			PostObject["text"] = self.__EscapeCharacters(PostObject["text"])

		# Обработка текста поста пользовательским скриптом.
		PostObject["text"] = MessageEditor(PostObject["text"])

		# Если включена очистка тегов, то удалить упоминания из них.
		if self.__Settings["clean-tags"] == True:
			PostObject["text"] = self.__CleanTags(PostObject["text"])

		# Для каждого запрещённого слова проверить соответствие словам поста.
		for ForbiddenWord in self.__Settings["blacklist"]:
			for Word in PostObject["text"].split():

				# Если пост содержит запрещённое слово, то игнорировать его.
				if ForbiddenWord.lower() == Word.lower():
					HasBlacklistWords = True

		# Если сообщение не игнорируется.
		if PostObject["text"] != None and PostObject["text"] != "" and HasBlacklistWords == False:
			# Обрезка текста поста до максимально дозволенной длинны.
			PostObject["text"] = PostObject["text"][:4096]
			# Копирование текста из поста в сообщение.
			MessageStruct["text"] = PostObject["text"]

			# Помещение поста в очередь на отправку.
			self.__MessagesBufer.append(MessageStruct)

		else:
			# Запись в лог отладочной информации: пост был проигнорирован.
			logging.debug("Post was ignored.")
		
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
		# Сохранение тела запроса.
		self.__CallbackRequest = CallbackRequest
		# Отправка сообщения в группу Telegram через буфер ожидания.
		self.__SendMessage(CallbackRequest["object"])

		# Активировать поток, если не активен.
		if self.__Sender.is_alive() == False:
			self.__Sender = Thread(target = self.__SenderThread)
			self.__Sender.start()