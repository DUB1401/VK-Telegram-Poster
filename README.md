# VK-Telegram-Poster
**VK-Telegram Poster** – это инструмент автопостинга записей из сообщества ВКонтакте в группу Telegram с возможностью настройки пользовательского скрипта обработки постов. Использует [Callback API](https://dev.vk.com/api/callback/getting-started).

## Порядок установки и использования
1. Установить Python версии не старше 3.9. Рекомендуется добавить в PATH.
2. В среду исполнения установить следующие пакеты вручную или при помощи файла _requirements.txt_: [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI), [fastapi](https://github.com/tiangolo/fastapi), [uvicorn](https://github.com/encode/uvicorn).
```
pip install pyTelegramBotAPI
pip install fastapi
pip install uvicorn
```
3. Настроить скрипт путём редактирования _Settings.json_. Для добавления пользовательского скрипта обработки постов можно внести изменения в файл _MessageEditor.py_.
4. При необходимости, например в случае использования скрипта на хостинге активного сайта, настроить переадресацию [Nginx](https://nginx.org/) на свободный порт.
5. Провести валидацию сервера согласно данному [руководству](https://dev.vk.com/api/callback/getting-started#%D0%9F%D0%BE%D0%B4%D0%BA%D0%BB%D1%8E%D1%87%D0%B5%D0%BD%D0%B8%D0%B5%20Callback%20API). Код подтверждения перед верификацией занести в файл настроек _Settings.json_. По умолчанию скрипт слушает `{HOST}/vtp/vk-group-wall`.
6. Открыть директорию со скриптом в терминале. Можно использовать метод `cd` и прописать путь к папке, либо запустить терминал из проводника. Активировать автопостер командой `uvicorn vtp:App --host {IP} --port {PORT}`.
7. Для автоматического запуска службы рекомендуется провести инициализацию скрипта через [systemd](https://github.com/systemd/systemd) (пример [здесь](https://github.com/DUB1401/VK-Telegram-Poster/tree/main/systemd)) на Linux или путём добавления его в автозагрузку на Windows.

# Settings.json
```JSON
"token": ""
```
Сюда необходимо занести токен бота Telegram (можно узнать у [@BotFather](https://t.me/BotFather)).
___
```JSON
"group-id": ""
```
Сюда необходимо занести  ID группы Telegram (можно получить, переслав сообщение из группы боту [Chat ID Bot](https://t.me/chat_id_echo_bot)).
___
```JSON
"source": "vk-group-wall"
```
Указывает конечную часть URI, использующегося для прослушивания Callback-запросов. По умолчанию скрипт слушает `{HOST}/vtp/vk-group-wall`.
___
```JSON
"parse-mode": null
```
Указывает способ форматирования сообщения, отправляемого в группу Telegram. 

Поддерживаются: _MarkdownV2_, _HTML_.
___
```JSON
"confirmation-code": ""
```
Указывает код подтверждения, необходимый для валидации прослушивающего сервера.

> **Warning**
> Код подтверждения периодически меняется. Убедитесь, что вы используете верную комбинацию.

_Copyright © DUB1401. 2022-2023._
