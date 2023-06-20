#!/usr/bin/python
# uvicorn vtp:App --reload --host 95.217.12.58 --port 444

from starlette.responses import Response, JSONResponse
from MessageEditor import MessageEditor
from starlette.requests import Request
from Source.Callback import Callback
from fastapi import FastAPI
from typing import Union

import telebot
import json
import sys
import os

#==========================================================================================#
# >>>>> ПРОВЕРКА ВЕРСИИ PYTHON <<<<< #
#==========================================================================================#

# Минимальная требуемая версия Python.
PythonMinimalVersion = (3, 9)
# Проверка соответствия.
if sys.version_info < PythonMinimalVersion:
	sys.exit("Python %s.%s or later is required.\n" % PythonMinimalVersion)

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

# Глобальные настройки.
Settings = {
	"token": "",
	"group-id": "",
	"source": "vk-group-wall",
	"parse-mode": "MarkdownV2",
	"confirmation-code": None
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
		if type(Settings["group-id"]) != str or len(Settings["group-id"]) == 0:
			raise Exception("Incorrect group ID.")

		# Установка информирующего сообщения в случае отсутствия кода подтверждения сервера.
		if type(Settings["confirmation-code"]) != str or len(Settings["confirmation-code"]) == 0:
			Settings["confirmation-code"] = "Confirmation code not found in settings file."

# Обработчик запросов FastAPI.
App = FastAPI()

# Проверяет доступность сервера через браузер.
@App.get("/vtp/{Source}")
def CheckServer(Source: str):
	return JSONResponse(content = {"source": Source, "status": "OK"})

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
			ObjectCallback = Callback(Settings, RequestData)

	# Если нет поля типа, выбросить исключение.
	else:
		raise Exception("Unsupported POST-request.")

	return Response(content = "ok")