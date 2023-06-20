from MessageEditor import MessageEditor
from time import sleep

import telebot

class Callback:
    
    #==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Callback-запрос.
	__CallbackRequest = None
	# Экземпляр бота.
	__TelegramBot = None
	# Глобальные настройки.
	__Settings = dict()

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Экранирует символы при использовании MarkdownV2 разметки.
	def __EscapeCharacters(self, Post: str) -> str:
		Post = Post.replace('.', "\.")
		Post = Post.replace('#', "\#")
		Post = Post.replace('!', "\!")
		Post = Post.replace('.', "\.")
		Post = Post.replace('-', "\-")

		return Post

	# Отправляет сообщение в группу Telegram.
	def __SendMessage(self, Post: str):
		# Декодирование из UTF-8.
		Post = Post.encode().decode("UTF-8", "ignore")
		# Обработка текста поста пользовательским скриптом.
		Post = MessageEditor(Post)
		# Обрезка текста поста до максимально дозволенной длинны.
		Post = Post[:4096]

		# Экранировать символы при указанной разметке MarkdownV2.
		if self.__Settings["parse-mode"] == "MarkdownV2":
			Post = self.__EscapeCharacters(Post)

		# Отправка сообщения в группу Telegram.
		self.__TelegramBot.send_message(self.__Settings["group-id"], Post, parse_mode = self.__Settings["parse-mode"])
		# Выжидание интервала для предотвращения блокировки по частоте запросов.
		sleep(5)
		
	# Конструктор: задаёт глобальные настройки и тело Callback-запроса.
	def __init__(self, Settings: dict, CallbackRequest: dict):

		#---> Генерация свойств.
		#==========================================================================================#
		self.__Settings = Settings
		self.__CallbackRequest = CallbackRequest
		self.__TelegramBot = telebot.TeleBot(Settings["token"])

		# Отправка сообщения в группу Telegram.
		self.__SendMessage(CallbackRequest["object"]["text"])