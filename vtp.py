#!/usr/bin/python

from dublib.Methods import CheckPythonMinimalVersion, MakeRootDirectories, ReadJSON
from starlette.responses import HTMLResponse, Response
from Source.Configurator import Configurator
from starlette.requests import Request
from Source.Callback import Callback
from fastapi import FastAPI

import datetime
import logging
import sys
import os

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ СКРИПТА <<<<< #
#==========================================================================================#

# Проверка поддержки используемой версии Python.
CheckPythonMinimalVersion(3, 10)
# Создание папок в корневой директории.
MakeRootDirectories(["Logs"])

#==========================================================================================#
# >>>>> НАСТРОЙКА ЛОГГИРОВАНИЯ <<<<< #
#==========================================================================================#

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
Version = "1.1.0"
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
	"attachments": {
		"audio": True,
		"doc": True,
		"photo": True,
		"video": True
	},
	"confirmation-code": "",
	"logging": False,
	"debug": False
}
# Запись в лог сообщения: версия скрипта.
logging.info("====== VK-Telegram Poster v" + Version + " ======")
# Запись в лог сообщения: используемая версия Python и платформа.
logging.info("Starting with Python " + str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro) + " on " + str(sys.platform) + ".")
# Чтение настроек.
Settings = ReadJSON("Settings.json")

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

#==========================================================================================#
# >>>>> ОБРАБОТКА ЗАПРОСОВ <<<<< #
#==========================================================================================#

# Запись в лог сообщения: заголовок раздела прослушивания запросов.
logging.info("====== Listen ======")
# Инициализация менеджера конфигураций.
ConfiguratorObject = Configurator()
# Обработчик Callback-запросов.
CallbackSender = Callback(Settings, ConfiguratorObject)

# Обрабатывает запросы от браузера.
@App.get("/vtp/{Source}")
def CheckServer(Source: str) -> HTMLResponse:
	# HTML-блок источника.
	SourceHTML = None
	
	# Проверка соответствия источника заданному настройками.
	if Source in ConfiguratorObject.getConfigsNames():
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
@App.post("/vtp/{Source}")
async def SendMessageToGroup(CallbackRequest: Request, Source: str) -> Response:
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
			
			# Если задана цель для источника.
			if Source in ConfiguratorObject.getConfigsNames():
				# Запись в лог сообщения: получен новый пост.
				logging.info("New post with ID " + str(RequestData["object"]["id"]) + " from source \"" + Source + "\". Attachments count: " + str(len(RequestData["object"]["attachments"])) + ".")
				# Добавление поста в буфер отложенной отправки.
				CallbackSender.AddMessageToBufer(RequestData, Source)
			
			else:
				# Запись в лог ошибки: неизвестный источник.
				logging.error(f"Unknown source: \"{Source}\".")

	else:
		# Запись в лог ошибки: неподдерживаемый POST-запрос.
		logging.error("Unsupported POST-request.")
		# Выброс исключения.
		raise Exception("Unsupported POST-request.")

	return Response(content = "ok")