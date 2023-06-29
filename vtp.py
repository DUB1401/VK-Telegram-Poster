#!/usr/bin/python

from starlette.responses import HTMLResponse, Response
from starlette.requests import Request
from Source.Callback import Callback
from fastapi import FastAPI

import datetime
import logging
import json
import sys
import os

#==========================================================================================#
# >>>>> ПРОВЕРКА ВЕРСИИ PYTHON <<<<< #
#==========================================================================================#

# Минимальная требуемая версия Python.
PythonMinimalVersion = (3, 10)
# Проверка соответствия.
if sys.version_info < PythonMinimalVersion:
	sys.exit("Python %s.%s or later is required.\n" % PythonMinimalVersion)

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ ЛОГГИРОВАНИЯ <<<<< #
#==========================================================================================#

# Если нет папки для логов, то создать.
if os.path.isdir("Logs") == False:
	os.makedirs("Logs")

# Получение текущей даты.
CurrentDate = datetime.datetime.now()
# Формирование пути к файлу лога.
LogFilename = "Logs/" + str(CurrentDate)[:-7] + ".log"
LogFilename = LogFilename.replace(':', '-')
# Установка конфигнурации и формата.
logging.basicConfig(filename = LogFilename, encoding = "utf-8", level = logging.INFO, format = "%(asctime)s %(levelname)s: %(message)s", datefmt = "%Y-%m-%d %H:%M:%S")

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

# Версия скрипта.
Version = "0.2.2"
# Текст копирайта.
Copyright = "Copyright © DUB1401. 2022-2023."
# Обработчик запросов FastAPI.
App = FastAPI()
# Глобальные настройки.
Settings = {
	"token": "",
	"target-id": "",
	"source": "vk-group-wall",
	"clean-tags": True,
	"parse-mode": None,
	"disable-web-page-preview": True,
	"blacklist": list(),
	"confirmation-code": ""
}
# Запись в лог сообщения: версия скрипта.
logging.info("====== VK-Telegram Poster v" + Version + " ======")
# Запись в лог сообщения: используемая версия Python и платформа.
logging.info("Starting with Python " + str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro) + " on " + str(sys.platform) + ".")

# Проверка доступности файла настроек.
if os.path.exists("Settings.json"):

	# Открытие файла настроек.
	with open("Settings.json", encoding = "utf-8") as FileRead:
		# Чтение настроек.
		Settings = json.load(FileRead)

		# Проверка корректности заданного логина.
		if type(Settings["token"]) is not str or len(Settings["token"]) == 0:
			# Запись в лог ошибки: некорректный токен бота.
			logging.error("Incorrect Telegram bot's token.")
			# Выброс исключения.
			raise Exception("Incorrect Telegram bot's token.")

		# Проверка корректности заданного пароля.
		if type(Settings["target-id"]) != str or len(Settings["target-id"]) == 0:
			# Запись в лог ошибки: некоррентный ID группы или канала.
			logging.error("Incorrect group or channel ID.")
			# Выброс исключения.
			raise Exception("Incorrect group or channel ID.")

		# Если отсутствует кода подтверждения сервера.
		if type(Settings["confirmation-code"]) != str or len(Settings["confirmation-code"]) == 0:
			# Установка информирующего сообщения.
			Settings["confirmation-code"] = "Confirmation code not found in settings file."
			# Запись в лог отладочной информации: отсутствует код подтверждения сервера.
			logging.debug("Confirmation code not found in settings file.")

		# Запись в лог сообщения: статус очистки тегов ВКонтакте.
		if Settings["clean-tags"] == True:
			logging.info("Tags cleaning: ON.")
		else:
			logging.info("Tags cleaning: OFF.")

		# Запись в лог сообщения: статус предпросмотра WEB-содержимого.
		if Settings["disable-web-page-preview"] == True:
			logging.info("WEB page preview: OFF.")
		else:
			logging.info("WEB page preview: ON.")

		# Запись в лог сообщения: режим разметки поста.
		if Settings["parse-mode"] != None:
			logging.info("Parse mode: \"" + str(Settings["parse-mode"]) + "\".")

		# Если включён отладочный режим.
		if Settings["debug"] == True:
			# Запись в лог сообщения: включён отладочный режим.
			logging.info("Debug mode enabled.")
			# Установка уровня логгирования на DEBUG.
			logging.getLogger().setLevel(logging.DEBUG)

		# Если логгирование отключено.
		if Settings["logging"] == False:
			# Отключение текущего логгирования.
			logging.shutdown()
			# Удаление лога.
			os.remove(LogFilename)
			# Отключение будущего логгирования.
			logging.disable(logging.CRITICAL)

else:
	# Запись в лог ошибки: не найден файл настроек.
	logging.error("Settings.json file not found.")
	# Выбро исключения.
	raise Exception("Settings.json file not found.")

#==========================================================================================#
# >>>>> ОБРАБОТКА ЗАПРОСОВ <<<<< #
#==========================================================================================#

# Запись в лог сообщения: заголовок раздела прослушивания запросов.
logging.info("====== Listen ======")
# Обработчик Callback-запросов.
CallbackSender = Callback(Settings)

# Обрабатывает запросы от браузера.
@App.get("/vtp/{Source}")
def CheckServer(Source: str):
	# HTML-блок источника.
	SourceHTML = None
	
	# Проверка соответствия источника заданному настройками.
	if Source == Settings["source"]:
		# Формирование HTML-контейнера для верного источника.
		SourceHTML = f"<span style=\"color: green;\">{Source}</span>"
		# Запись в лог сообщения: выполнена проверка состояния через браузер.
		logging.info(f"Source validation: \"{Source}\". Correct.")
	else:
		# Формирование HTML-контейнера для неверного источника.
		SourceHTML = f"<span style=\"color: red;\">{Source}</span>"
		# Запись в лог предупреждения: при проверке состояния указан неверный источник.
		logging.warning(f"Source validation: \"{Source}\". Uncorrect.")

	

	# HTML-тело ответа для браузера.
	ResponseBody = f"""
		<html>
			<head>
				<title>VK-Telegram Poster</title>
				<link rel="icon" href="https://web.telegram.org/a/favicon.svg" type="image/svg+xml">
			</head>
			<body style="background-color: #0E1010; color: #D4CDF5;">
				<span style="font-size: 200%;">VK-Telegram Poster</span><br>
				<b>Source:</b> {SourceHTML}<br>
				<b>Version:</b> {Version}<br>
				<b>Status:</b> <span style="color: green;">200 OK</span><br>
				<br>
				{Copyright} | <a href="https://github.com/DUB1401/VK-Telegram-Poster" style="text-decoration: none; color: #F5E3CD;">GitHub</a><br>
			</body>
		</html>
	"""

	return HTMLResponse(content = ResponseBody)

# Обрабатывает запросы от серверов ВКонтакте по Callback API. 
@App.post("/vtp/" + Settings["source"])
async def SendMessageToGroup(CallbackRequest: Request):
	# Парсинг данных запроса в JSON.
	RequestData = dict(await CallbackRequest.json())

	# Проверка наличия в запросе поля типа.
	if "type" in RequestData.keys():
		
		# Если тип запроса – подтверждение сервера.
		if RequestData["type"] == "confirmation":
			# Запись в лог сообщения: запрос кода подтверждения сервера.
			logging.info("Confirmation code requested: \"" + Settings["confirmation-code"] + "\".")

			return Response(content = Settings["confirmation-code"])

		# Если тип запроса – новый пост.
		if RequestData["type"] == "wall_post_new":
			# Запись в лог сообщения: .
			logging.info("New post with ID: " + str(RequestData["object"]["id"]) + ".")
			# Добавление поста в буфер отложенной отправки.
			CallbackSender.AddMessageToBufer(RequestData)

	else:
		# Запись в лог ошибки: неподдерживаемый POST-запрос.
		logging.error("Unsupported POST-request.")
		# Выброс исключения.
		raise Exception("Unsupported POST-request.")

	return Response(content = "ok")