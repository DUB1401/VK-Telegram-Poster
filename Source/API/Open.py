from Source.API.Base import Base

from threading import Thread
from time import sleep
import logging

from vk_api.exceptions import AuthError, ApiError
from vk_captcha import VkCaptchaSolver
from vk_api import VkApi

class Open(Base):
	"""Обработчик Open API."""

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __Authorizate(self):
		"""Выполняет авторизацию во ВКонтакте."""

		CaptchaSolver = VkCaptchaSolver(logging = False)
		IsUncaptched = False
		
		while IsUncaptched == False:
			
			try:
				self.__Session = VkApi(
					login = self._Config.login,
					password = self._Config.password,
					app_id = self._Config.app_id,
					token = self._Config.vk_token,
					captcha_handler = CaptchaSolver.vk_api_captcha_handler
				)
				
				if not self._Config.vk_token: self.__Session.auth(token_only = True)
				
			except AuthError as ExceptionData:	
				logging.error(f"[{self._Name} API] Authorization exception: " + str(ExceptionData).split(" Please")[0])
				sleep(5)
				
			else: IsUncaptched = True
				
		self.__API = self.__Session.get_api()

	def __GetPosts(self, wall_id: str, posts_count: int = 20, offset: int = 0) -> list[dict]:
		"""
		Получает список постов.
			wall_id – идентификатор стены ВКонтакте;\n
			posts_count – количество постов на странице;\n
			offset – сдвиг от последнего поста.
		"""

		wall_id = "-" + str(wall_id).strip("-")
		WallPosts = list()
		
		try: WallPosts = self.__API.wall.get(owner_id = wall_id, count = posts_count, offset = offset)["items"]
		except ApiError as ExceptionData: logging.error(f"[{self._Name} API] Exception: " + str(ExceptionData))
		
		return WallPosts

	def __GetUpdates(self) -> list[dict]:
		"""Получает список обновлённых с момента последней проверки постов постов."""

		IsUpdated = False
		Posts = list()
		RequestIndex = 0
		
		while IsUpdated == False:
			Bufer = self.__GetPosts(self._Config.wall_id, offset = 20 * RequestIndex)

			if self._Config.last_post_id != None:

				for Post in Bufer:
				
					if Post["id"] > self._Config.last_post_id:
						Posts.append(Post)
						
					else:
						IsUpdated = True
						
			else:
				Posts.append(Bufer[0])
				IsUpdated = True
					
			RequestIndex += 1
			
			if IsUpdated == False:
				sleep(5)

		return Posts	

	def __UpdaterThread(self, immediately: bool = False):
		"""
		Запускает проверку обновлений.
			immediately – включает немедленную проверку.
		"""
		
		try:
			
			if immediately == True:
				self.check_updates()
		
			while True:
				sleep(self._Config.period * 60)
				self.check_updates()
				
		except Exception as ExceptionData:
			ExceptionData = str(ExceptionData).split('\n')[0].rstrip(".:")
			logging.error(f"[{self._Name} API] Updater exception: \"" + ExceptionData + "\".")

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _PostInitMethod(self):
		"""Метод, выполняемый после инициализации объекта."""

		self.__Repeater = Thread(target = self.__UpdaterThread, args = [True])
		self.__IsUpdating = False
		self.__Session = None  
		self.__API = None

		self.__Authorizate()
		self.__Repeater.start()

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def check_updates(self):
		
		if not self.__IsUpdating:
			self.__IsUpdating = True

			Posts = tuple(reversed(self.__GetUpdates()))
			if Posts: self._Config.set_last_post_id(Posts[-1]["id"])
			logging.info(f"[{self._Name} API] Source: \"{self._Config.name}\". Updates checked. New posts count: " + str(len(Posts)) + ".")
			for Post in Posts: self._PushMessage(Post)

			self._StartSenderThread()
			self.__IsUpdating = False
			
		else: logging.warning(f"[{self._Name} API] Update already in progress. Skipped.")