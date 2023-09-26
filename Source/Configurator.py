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
	def getConfigsNames(self, API_Type: str | None = None) -> list[str]:
		# Список конфигурация.
		Configs = list()	
		
		# Если не указана спецификация API.
		if API_Type == None:
			Configs = self.__Configurations.keys()
			
		# Если запрошен список конфигураций для Callback API.
		elif API_Type.lower() == "callback":
			
			# Для каждой конфигурации проверить соответствие типу API.
			for Name in self.__Configurations.keys():
				if self.__Configurations[Name]["api"].lower() == "callback":
					Configs.append(Name)
					
		# Если запрошен список конфигураций для Open API.
		elif API_Type.lower() == "open":
			
			# Для каждой конфигурации проверить соответствие типу API.
			for Name in self.__Configurations.keys():
				if self.__Configurations[Name]["api"].lower() == "open":
					Configs.append(Name)

		return Configs
	
	# Возвращает словарь с количеством модулей, требующих конкретный API.
	def getRequiredAPI(self) -> dict:
		# Список API.
		API = {
			"Callback": 0,
			"Open": 0
		}
		
		# Для каждой конфигурации.
		for ConfigName in self.__Configurations.keys():
			
			# Если конфигурация требует Callback API.
			if self.__Configurations[ConfigName]["api"].lower() == "callback":
				API["Callback"] += 1
				
			# Если конфигурация требует Open API.
			if self.__Configurations[ConfigName]["api"].lower() == "open":
				API["Open"] += 1
				
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
	def updateConfigs(self, API_Type: str):
		# Список конфигураций с Open API.
		OpenConfigs = list()

		# Для каждой конфигурации.
		for ConfigName in self.__Configurations.keys():
				
			# Если конфигурация требует Open API.
			if self.__Configurations[ConfigName]["api"].lower() == API_Type:
				OpenConfigs.append(ConfigName)
		
		# Для каждого файла конфигурации с Open API.
		for Filename in OpenConfigs:
			# Прочитать конфигурацию в словарь.
			self.__Configurations[Filename] = ReadJSON("Config/" + Filename + ".json")