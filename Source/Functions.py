from Source.Datasets import API_Types

import requests
import logging
import os
import re

# Очищает сообщение от упоминаний в тегах ВКонтакте.
def CleanTags(Post: str) -> str:
	# Поиск всех совпадений.
	RegexSubstrings = re.findall("#\w+@\w+", Post)

	# Удаление каждой подстроки.
	for RegexSubstring in RegexSubstrings:
		Post = Post.replace("@" + RegexSubstring.split('@')[1], "")
		
	# Запись в лог отладочной информации: количество очищенных тегов ВКонтакте.
	logging.debug("Cleaned tags count: " + str(len(RegexSubstrings)) + ".")

	return Post

# Экранирует символы при использовании MarkdownV2 разметки.
def EscapeCharacters(Post: str) -> str:
	# Список экранируемых символов. _ * [ ] ( ) ~ ` > # + - = | { } . !
	CharactersList = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

	# Экранировать каждый символ из списка.
	for Character in CharactersList:
		Post = Post.replace(Character, "\\" + Character)

	return Post

# Получает URL вложения и загружает его.
def GetAttachments(PostAttachements: dict, Source: str, SupportedTypes: list[str], PostID: int, API_Type: API_Types) -> list:
	# Список вложений.
	Attachements = list()

	# Для каждого вложения проверить соответствие поддерживаемым типам.
	for Attachment in PostAttachements:
		for Type in SupportedTypes:

			# Если вложение поддерживается.
			if Attachment["type"] == Type:
				# Буфер описания вложения.
				Bufer = {
					"type": Type,
					"url": None,
					"filename": None
				}

				# Получение URL вложения и названия файла (doc).
				if Bufer["type"] == "doc":
					Bufer["url"] = Attachment[Type]["url"]
					Bufer["filename"] = Attachment[Type]["url"].split('?')[0].split('/')[-1] + "." + Attachment[Type]["ext"]
					
				# Получение URL вложения и названия файла (photo).
				if Bufer["type"] == "photo":
					
					# Для каждого размера изображения.
					for Size in Attachment[Type]["sizes"]:
						
						# Если обнаружен максимальный размер фотографии.
						if Size["type"] == "w":
							# Записать URL фотографии.
							Bufer["url"] = Size["url"]
							# Запись названия файла изображения.
							Bufer["filename"] = Bufer["url"].split('?')[0].split('/')[-1]

				# Получение URL вложения и названия файла (video).
				if Bufer["type"] == "video":
					Bufer["url"] = "https://vk.com/video" + str(Attachment[Type]["owner_id"]) + "_" + str(Attachment[Type]["id"])
					Bufer["filename"] = str(Attachment[Type]["id"]) + ".mp4"
					
				# Если вложение не было загружено раньше.
				if os.path.exists("Temp/" + Bufer["filename"]) == False:
					# Запись в лог отладочной информации: URL загружаемого вложения.
					logging.debug("Downloading attachment (\"" + Type + "\"): " + Bufer["url"])
						
					# Загрузка вложения (doc, photo).
					if Bufer["type"] in ["doc", "photo"]:
						# Запрос вложения.
						Response = requests.get(Bufer["url"])
					
						# Если удалось запросить вложение.
						if Response.status_code == 200:
							# Запись описания вложения в список вложений.
							Attachements.append(Bufer)
								
							# Сохранить вложение в файл.
							with open("Temp/" + Bufer["filename"], "wb") as FileWriter:
								FileWriter.write(Response.content)

						else:
							# Запись в лог ошибки: не удалось загрузить вложение.
							logging.error("Unable to download attachment (\"" + Type + "\"). Request code: " + str(Response.status_code) + ".")

					# Загрузка вложения (video).
					if Bufer["type"] == "video":
						# Загрузить видео с помощью кроссплатформенной версии yt-dlp.
						ExitCode = os.system("python yt-dlp -o " + Bufer["filename"] + " -P Temp " + Bufer["url"])

						# Если загрузка успешна.
						if ExitCode == 0:
							# Запись описания вложения в список вложений.
							Attachements.append(Bufer)

				else:
					# Запись описания вложения в список вложений.
					Attachements.append(Bufer)
					
	# Запись в лог сообщения: количество.
	logging.info(f"[{API_Type.value} API] Source: \"{Source}\". Post with ID {PostID} contains " + str(len(Attachements)) + " supported attachments.")						

	return Attachements