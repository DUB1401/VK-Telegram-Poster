from Source.SystemManager import Manager
from Source.API import Types

from dublib.Methods.Filesystem import ReadJSON, ReadTextFile
from dublib.Methods.System import CheckPythonMinimalVersion
from dublib.Methods.Filesystem import MakeRootDirectories

from starlette.responses import HTMLResponse, Response
from starlette.requests import Request
from fastapi import FastAPI

import datetime
import logging
import sys

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ СКРИПТА <<<<< #
#==========================================================================================#

CheckPythonMinimalVersion(3, 10)
MakeRootDirectories(["Configs", "Editors", "Logs", "Temp"])

CurrentDate = datetime.datetime.now()
LogFilename = "Logs/" + str(CurrentDate)[:-7] + ".log"
LogFilename = LogFilename.replace(':', '-')
logging.basicConfig(filename = LogFilename, encoding = "utf-8", level = logging.INFO, format = "%(asctime)s %(levelname)s: %(message)s", datefmt = "%Y-%m-%d %H:%M:%S")
logging.getLogger("vk_api").setLevel(logging.CRITICAL)

Version = "2.0.0"
Copyright = ReadTextFile("README.md", split = "\n")[-1].strip("_")
Settings = ReadJSON("Settings.json")

logging.info("====== VK-Telegram Poster v" + Version + " ======")
logging.info(f"Starting with Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} on {sys.platform}.")

App = FastAPI()
Manager = Manager()
Workers = list()

logging.info("====== Working ======")

#==========================================================================================#
# >>>>> ОБРАБОТКА API <<<<< #
#==========================================================================================#

@App.get("/")
def WorkingStatus() -> HTMLResponse:
	ResponseBody = f"""
		<html>
			<head>
				<title>VK-Telegram Poster</title>
				<link rel="icon" href="https://web.telegram.org/a/favicon.svg" type="image/svg+xml">
			</head>
			<body style="background-color: #0E1010; color: #D4CDF5;">
				<span style="font-size: 200%;">VK-Telegram Poster</span><br>
				<b>Version:</b> {Version}<br>
				<b>Status:</b> <span style="color: green;">200 OK</span><br>
				<br>
				{Copyright} | <a href="https://github.com/DUB1401/VK-Telegram-Poster" style="text-decoration: none; color: #F5E3CD;">GitHub</a><br>
			</body>
		</html>
	"""

	return HTMLResponse(content = ResponseBody)

if Manager.check_api(Types.Callback):

	@App.get("/vtp/{Source}")
	def CheckServer(Source: str) -> HTMLResponse:
		SourceHTML = None

		if Source in Manager.configs_names:
			SourceHTML = f"<span style=\"color: green;\">{Source}</span>"
			logging.info(f"[Callback API] Source validation: \"{Source}\". Correct.")
		else:
			SourceHTML = f"<span style=\"color: red;\">{Source}</span>"
			logging.warning(f"[Callback API] Source validation: \"{Source}\". Uncorrect.")

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

	@App.post("/vtp/{Source}")
	async def SendMessageToGroup(CallbackRequest: Request, Source: str) -> Response:
		RequestData = dict(await CallbackRequest.json())

		if "type" in RequestData.keys():
		
			if RequestData["type"] == "confirmation":
				logging.info("[Callback API] Confirmation code requested: \"" + Settings["confirmation-code"] + "\".")

				return Response(content = Settings["confirmation_code"])

			if RequestData["type"] == "wall_post_new":
				Manager.get_worker(Source).add_post(RequestData)
				# else: logging.error(f"[Callback API] Unknown source: \"{Source}\".")

		else: logging.error("[Callback API] Unsupported POST-request.")

		return Response(content = "ok")
	
if Manager.check_api(Types.Open):

	for Config in Manager.configs:

		if Config.type == Types.Open:
			Worker = Manager.get_worker(Config.name)
			Worker.check_updates()
			Workers.append(Worker)