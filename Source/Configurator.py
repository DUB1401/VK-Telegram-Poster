from dublib.Methods import ReadJSON

import os

# Менеджер конфигураций.
class Configurator:
	
	# Читает конфигурации.
	def __ReadConfigs(self) -> dict:
		# Список файлов в директории конфигурации.
		FilesList = os.listdir("Config")
		# Фильтрация только файлов формата JSON.
		FilesList = list(filter(lambda x: x.endswith(".json"), FilesList))
		# Словарь конфигураций.
		Configurations = dict()
		
		# Удаление примера.
		if "Example.json" in FilesList:
			FilesList.remove("Example.json")
		
		# Для каждого файла конфигурации.
		for Filename in FilesList:
			# Прочитать конфигурацию в словарь.
			Configurations[Filename.replace(".json", "")] = ReadJSON("Config/" + Filename)
			
		return Configurations
	
	# Конструктор.
	def __init__(self):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Словарь конфигураций.
		self.__Configurations = self.__ReadConfigs()
		
	# Возвращает настройки вложений.
	def getAttachments(self, ConfigName: str) -> dict:
		return self.__Configurations[ConfigName]["attachments"]
		
	# Возвращает настройки в конфигурации.
	def getConfig(self, ConfigName: str) -> dict:
		return self.__Configurations[ConfigName]
		
	# Возвращает список конфигураций.
	def getConfigsNames(self) -> list[str]:
		return list(self.__Configurations.keys())
	
	# Возвращает токен для указанной конфигурации.
	def getToken(self, ConfigName: str) -> str:
		return self.__Configurations[ConfigName]["token"]

	# Возвращает список токенов ботов.
	def getTokens(self):
		# Список токенов.
		TokensList = list()
		
		# Для каждого элемента записать токен.
		for Config in self.__Configurations.values:
			TokensList.append(Config["token"])
			
		return TokensList