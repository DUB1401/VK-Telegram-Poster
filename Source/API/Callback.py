from Source.API.Base import Base

from threading import Thread

class Callback(Base):
	"""Обработчик Callback API."""

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def add_post(self, post: str):
		"""
		Обрабатывает новый пост и добавляет его в очередь для отправки.
			post – данные поста.
		"""

		self._ClearEditors()
		self._PostsEditorsThreads.append(Thread(target = self._PushMessage, args = [post["object"]]))
		self._PostsEditorsThreads[-1].start()