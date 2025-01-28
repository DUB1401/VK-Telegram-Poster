from .Config import Config
from ..API import Callback, Open, Types

import os

class SystemManager:
	"""Системный менеджер."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def configs(self) -> list[Config]:
		"""Список конфигураций."""

		return list(self.__Configs.values)

	@property
	def configs_names(self) -> list[str]:
		"""Список названий конфигураций."""

		return list(self.__Configs.keys())

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __LoadConfigs(self):
		"""Загружает файлы конфигураций."""

		ConfigsFiles = os.listdir("Configs")
		ConfigsFiles = list(filter(lambda File: File.endswith(".json"), ConfigsFiles))

		for Filename in ConfigsFiles:
			Filename = Filename[:-5]
			NewConfig = Config(Filename)
			self.__API[NewConfig.type]["required"] = True
			self.__Configs[Filename] = NewConfig
			self.__Workers[Filename] = self.__API[NewConfig.type]["worker"](NewConfig)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self):
		"""Системный менеджер."""
		
		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self.__Configs: dict[str, Config] = dict()

		self.__API = {
			Types.Callback: {
				"required": False,
				"worker": Callback
			},
			Types.LongPoll: {
				"required": False,
				"worker": None
			},
			Types.Open: {
				"required": False,
				"worker": None
			}
		}
		self.__Workers = dict()

		self.__LoadConfigs()

	def check_api(self, type: Types) -> bool:
		"""
		Проверяет, задействован ли тип API для текущих конфигураций.
			type – тип API.
		"""

		return self.__API[type]["required"]

	def get_config(self, name: str) -> Config:
		"""
		Возвращает конфигурацию.
			name – название конфигурации.
		"""

		return self.__Configs[name]
	
	def get_worker(self, name: str) -> Callback | Open:
		"""
		Возвращает выделенный обработчик API.
			name – название конфигурации.
		"""

		return self.__Workers[name]