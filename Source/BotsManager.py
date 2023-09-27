import logging
import telebot

# Менеджер подключений к ботам.
class BotsManager:
	
	# Конструктор.
	def __init__(self):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Хранилище активных ботов.
		self.__Bots = dict()
		# Данные о подключениях к ботам.
		self.__ConnectionsData = dict()
	
	# Создаёт новое подключение к боту.
	def createBotConnection(self, Token: str, Source: str, Target: str):
		
		# Если бот с таким токеном ещё не инициализирован.
		if Token not in self.__Bots.keys():
			
			try:
				# Инициализация бота.
				self.__Bots[Token] = telebot.TeleBot(Token)
				
			except Exception as ExceptionData:
				# Запись в лог ошибки: не удалось инициализировать бота.
				logging.error("Incorrect bot token. Exception: " + str(ExceptionData))
			
			# Заполнение данных о подключении.
			self.__ConnectionsData[Token] = {
				"sources": list(),
				"targets": list()
			}
			
		# Дополнение информации о подключении.
		self.__ConnectionsData[Token]["sources"].append(Source)
		self.__ConnectionsData[Token]["targets"].append(Target)
		
	# Возвращает экземпляр бота по токену.
	def getBot(self, Token: str) -> telebot.TeleBot:
		return self.__Bots[Token]	