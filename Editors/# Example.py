from Source.BaseEditor import BaseEditor

class Editor(BaseEditor):
	"""Редактор постов."""

	def edit(self, text: str) -> str | None:
		"""
		Обрабатывает текст поста и возвращает отредактированную версию или ничего для игнорирования.
			text – текст поста.
		"""

		# Название источника.
		self.source
		# Доступ к конфигурации источника.
		self.config

		return text