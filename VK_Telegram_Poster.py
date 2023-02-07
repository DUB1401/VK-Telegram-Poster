#!/usr/bin/env python3.9

from time import sleep
from telebot.types import InputMediaPhoto

import configparser
import telebot
import vk_api
import sys
import os

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

ConfigPath = os.path.join(sys.path[0], "Settings.ini")
Config = configparser.ConfigParser()
Config.read(ConfigPath)
LOGIN = Config.get("VK", "LOGIN")
PASSWORD = Config.get("VK", "PASSWORD")
DOMAIN = Config.get("VK", "DOMAIN")
COUNT = Config.get("VK", "COUNT")
VK_TOKEN = Config.get("VK", "TOKEN", fallback = None)
BOT_TOKEN = Config.get("Telegram", "BOT_TOKEN")
CHANNEL = Config.get("Telegram", "CHANNEL")
INCLUDE_LINK = Config.getboolean("Settings", "INCLUDE_LINK")
PREVIEW_LINK = Config.getboolean("Settings", "PREVIEW_LINK")

# Символы, по которым можно разбить сообщение.
MessageBreakers = [':', ' ', '\n']
# Максимальная длина сообщения (ограничена Telegram).
MaxMessageLength = 4091
# Инициализация бота.
Bot = telebot.TeleBot(BOT_TOKEN)

# Получаем данные из vk.com
def get_data(domain_vk, count_vk):
	global LOGIN
	global PASSWORD
	global VK_TOKEN
	global Config
	global ConfigPath

	if VK_TOKEN is not None:
		vk_session = vk_api.VkApi(LOGIN, PASSWORD, VK_TOKEN)
		vk_session.auth(token_only=True)
	else:
		vk_session = vk_api.VkApi(LOGIN, PASSWORD)
		vk_session.auth()

	new_token = vk_session.token['access_token']
	if VK_TOKEN != new_token:
		VK_TOKEN = new_token
		Config.set('VK', 'TOKEN', new_token)
		with open(ConfigPath, "w") as config_file:
			Config.write(config_file)

	vk = vk_session.get_api()
	# Используем метод wall.get из документации по API vk.com
	response = vk.wall.get(domain=domain_vk, count=count_vk)
	return response


# Проверяем данные по условиям перед отправкой
def check_posts_vk():
	global DOMAIN
	global COUNT
	global INCLUDE_LINK
	global Bot
	global Config
	global ConfigPath

	response = get_data(DOMAIN, COUNT)
	response = reversed(response['items'])

	for post in response:

		# Читаем последний извесный id из файла
		id = Config.get('Settings', 'LAST_ID')

		# Сравниваем id, пропускаем уже опубликованные
		if int(post['id']) <= int(id):
			continue

		#print('------------------------------------------------------------------------------------------------\n\n')
		#print(post)

		# Текст
		text = post['text'].replace("@ranoberf", "")

		# Проверяем есть ли что то прикрепленное к посту
		images = []
		links = []
		attachments = []
		if 'attachments' in post:
			attach = post['attachments']
			for add in attach:
				if add['type'] == 'photo':
					img = add['photo']
					images.append(img)
				elif add['type'] == 'audio':
					# Все аудиозаписи заблокированы везде, кроме оффицальных приложений
					continue
				elif add['type'] == 'video':
					video = add['video']
					if 'player' in video:
						links.append(video['player'])
				else:
					for (key, value) in add.items():
						if key != 'type' and 'url' in value:
							attachments.append(value['url'])

		if INCLUDE_LINK:
			post_url = "https://vk.com/" + DOMAIN + "?w=wall" + \
				str(post['owner_id']) + '_' + str(post['id'])
			links.insert(0, post_url)
		text = '\n'.join([text] + links)
		#send_posts_text(text)

		text = text.replace("#", "\#")
		text = text.replace("!", "\!")
		text = text.replace(".", "\.")
		text = text.replace("-", "\-")
		text = text.replace("👉", "\👉🏻")

		MessageParagraphs = text.split('\n')
		ReadHere = ""
		RemovePart = ""

		for index in range(0, len(MessageParagraphs)):
			if "Читать:" in MessageParagraphs[index]:
				RemovePart = MessageParagraphs[index]
				ReadHere = "\n👉🏻 Читать [здесь](" + MessageParagraphs[index][len("👉🏻 Читать: "):] + ")\."

		if RemovePart in MessageParagraphs:
			MessageParagraphs.remove(RemovePart)

		text = '\n'.join(MessageParagraphs)

		if len(images) > 0:
			image_urls = list(map(lambda img: max(
				img["sizes"], key=lambda size: size["type"])["url"], images))
			#print(image_urls)

			# Альбом с постом.
			MediaGroup = []

			print(text[:1023])

			for i in range(0, len(image_urls)):
				# Для первого элемента добавить описание (фикс отображения текста под альбомом).
				if i == 0 and len(text) >= 1024:
					MediaGroup.append(InputMediaPhoto(image_urls[i], caption = text[:1006] + '…\n' + ReadHere, parse_mode = "MarkdownV2"))
				elif i == 0:
					MediaGroup.append(InputMediaPhoto(image_urls[i], caption = text[:1008] + ReadHere, parse_mode = "MarkdownV2"))
				else:
					MediaGroup.append(InputMediaPhoto(image_urls[i]))
			print(text)
			Bot.send_media_group(CHANNEL, MediaGroup)
			sleep(5)


		# Проверяем есть ли репост другой записи
		if 'copy_history' in post:
			copy_history = post['copy_history']
			copy_history = copy_history[0]
			print('--copy_history--')
			print(copy_history)
			text = copy_history['text']
			send_posts_text(text)

			# Проверяем есть ли у репоста прикрепленное сообщение
			if 'attachments' in copy_history:
				copy_add = copy_history['attachments']
				copy_add = copy_add[0]

				# Если это ссылка
				if copy_add['type'] == 'link':
					link = copy_add['link']
					text = link['title']
					send_posts_text(text)
					img = link['photo']
					send_posts_img(img)
					url = link['url']
					send_posts_text(url)

				# Если это картинки
				if copy_add['type'] == 'photo':
					attach = copy_history['attachments']
					for img in attach:
						image = img['photo']
						send_posts_img(image)

		# Записываем id в файл
		Config.set('Settings', 'LAST_ID', str(post['id']))
		with open(ConfigPath, "w") as config_file:
			Config.write(config_file)


# Отправляем посты в телеграмм


# Текст
def send_posts_text(text):
	global CHANNEL
	global PREVIEW_LINK
	global Bot

	if text == '':
		print('no text')
	else:
		# В телеграмме есть ограничения на длину одного сообщения в 4091 символ, разбиваем длинные сообщения на части
		for msg in split(text):
			Bot.send_message(CHANNEL, msg, disable_web_page_preview=not PREVIEW_LINK)


def split(text):
	global message_breakers
	global MaxMessageLength

	if len(text) >= MaxMessageLength:
		last_index = max(
			map(lambda separator: text.rfind(separator, 0, MaxMessageLength), message_breakers))
		good_part = text[:last_index]
		bad_part = text[last_index + 1:]
		return [good_part] + split(bad_part)
	else:
		return [text]


# Изображения
def send_posts_img(img):
	global Bot
	
	# Находим картинку с максимальным качеством
	url = max(img["sizes"], key=lambda size: size["type"])["url"]
	Bot.send_photo(CHANNEL, url)

# Отправка поста.
def SendPost(Text, Image):
	global Bot
	
	# Находим картинку с максимальным качеством
	url = max(Image["sizes"], key=lambda size: size["type"])["url"]
	Bot.send_photo(CHANNEL, url, caption = Text)


if __name__ == "__main__":
	check_posts_vk()
