# homework_bot

Проект телеграмм бота реализованный на Python 3.7 и python-telegram-bot 13.7.
Основная функция бота опрашивать API яндекс практикума и уточнять статус домашней работы.
В проект встроено логирование, результаты логирования выводятся в консоль. 
Опрос сервера происходит каждые 10 минут.
При опросе сервера, если возникнет ошибка, она будет продублирована и в телеграмме пользователя.

## Stack

Python 3.7, python-telegram-bot 13.7

### Установка, Как запустить проект:

Клонируйте репозиторий:

```
git clone git@github.com:Alex386386/homework_bot
```

Перейдите в клонированный репозиторий:

```
cd homework_bot
```

Cоздайте файл .env со следующим наполнением:

```
PRACTICUM_TOKEN=# токен для авторизации на сайте
TELEGRAM_TOKEN=# токен дл доступа к телеграм боту
TELEGRAM_CHAT_ID=# ID вашего чата в телеграмм 
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

* Если у вас Linux/macOS

    ```
    source venv/bin/activate
    ```

* Если у вас windows

    ```
    source venv/scripts/activate
    ```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Запустить проект:

```
python homework.py
```

Проект сделан в рамках учебного процесса по специализации Python-разработчик (back-end) Яндекс.Практикум.

Автор:

- [Александр Мамонов](https://github.com/Alex386386) 
