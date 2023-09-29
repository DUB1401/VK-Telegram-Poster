from Source.Datasets import API_Types
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
		# Список доступных API.
		API = ["Callback", "Open"]
		# Словарь конфигураций.
		Configurations = dict()
		
		# Для каждого API.
		for Name in API:
			# Название файла с примером API.
			Example = f"# {Name} API Example.json"		

			# Если обнаружен файл примера, то удалить его.
			if Example in FilesList:
				FilesList.remove(Example)
		
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
		
	# Возвращает список конфигураций. Поддерживает фильтрацию по типу API.
	def getConfigsNames(self, API_Type: API_Types | None = None) -> list[str]:
		# Список конфигурация.
		Configs = list()	
		
		# Если не указана спецификация API.
		if API_Type == None:
			Configs = self.__Configurations.keys()
		
		else:
				
			# Для каждой конфигурации.
			for ConfigName in self.__Configurations.keys():
					
				# Если конфигурация соответствует искомому API, то записать её название.
				if self.__Configurations[ConfigName]["api"].lower() == API_Type.value.lower():
					Configs.append(ConfigName)

		return Configs
	
	# Возвращает словарь с количеством модулей, требующих конкретный API.
	def getRequiredAPI(self) -> dict:
		# Список API.
		API = {
			API_Types.Callback: 0,
			API_Types.LongPoll: 0,
			API_Types.Open: 0
		}

		# Для каждого типа API.
		for API_Type in list(API_Types):
			
			# Для каждой конфигурации.
			for ConfigName in self.__Configurations.keys():
			
				# Если конфигурация соответствует API.
				if self.__Configurations[ConfigName]["api"].lower() == API_Type.value.lower():
					API[API_Type] += 1
				
		return API

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
	
	# Обновляет конфигурации с указанным типом API.
	def updateConfigs(self, API_Type: API_Types):
		# Список конфигураций с указанный API.
		SelectedConfigs = list()

		# Для каждой конфигурации.
		for ConfigName in self.__Configurations.keys():
				
			# Если конфигурация требует указанный API.
			if self.__Configurations[ConfigName]["api"].lower() == API_Type.value.lower():
				SelectedConfigs.append(ConfigName)
		
		# Для каждого файла конфигурации с указанный API.
		for Filename in SelectedConfigs:
			# Прочитать конфигурацию в словарь.
			self.__Configurations[Filename] = ReadJSON("Config/" + Filename + ".json")