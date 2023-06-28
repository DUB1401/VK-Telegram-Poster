#!/usr/bin/python

from starlette.responses import HTMLResponse, Response
from starlette.requests import Request
from Source.Callback import Callback
from fastapi import FastAPI

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
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

# Версия скрипта.
Version = "0.2.1"
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

# Проверка доступности файла.
if os.path.exists("Settings.json"):

	# Открытие файла настроек.
	with open("Settings.json", encoding = "utf-8") as FileRead:
		# Чтение настроек.
		Settings = json.load(FileRead)

		# Проверка корректности заданного логина.
		if type(Settings["token"]) is not str or len(Settings["token"]) == 0:
			raise Exception("Incorrect Telegram bot's token.")

		# Проверка корректности заданного пароля.
		if type(Settings["target-id"]) != str or len(Settings["target-id"]) == 0:
			raise Exception("Incorrect group or channel ID.")

		# Установка информирующего сообщения в случае отсутствия кода подтверждения сервера.
		if type(Settings["confirmation-code"]) != str or len(Settings["confirmation-code"]) == 0:
			Settings["confirmation-code"] = "Confirmation code not found in settings file."

# Обработчик Callback-запросов.
CallbackSender = Callback(Settings)

# Обрабатывает запросы от браузера.
@App.get("/vtp/{Source}")
def CheckServer(Source: str):
	# HTML-блок источника.
	SourceHTML = None

	# Проверка соответствия источника заданному настройками.
	if Source == Settings["source"]:
		SourceHTML = f"<span style=\"color: green;\">{Source}</span>"
	else:
		SourceHTML = f"<span style=\"color: red;\">{Source}</span>"

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
			return Response(content = Settings["confirmation-code"])

		# Если тип запроса – новый пост.
		if RequestData["type"] == "wall_post_new":
			CallbackSender.AddMessageToBufer(RequestData)

	# Если нет поля типа, выбросить исключение.
	else:
		raise Exception("Unsupported POST-request.")

	return Response(content = "ok")