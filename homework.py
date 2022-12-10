import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Dict, Optional, List

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler('program.log'),
        logging.StreamHandler(sys.stdout)
    ],
)

RETRY_PERIOD: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: Dict[str, str] = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
ONE_WEEK: int = 604800

HOMEWORK_VERDICTS: Dict[str, str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """Функция проверки доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message: Optional[str]) -> None:
    """Функция отправки любого сообщения(message) в чат (TELEGRAM_CHAT_ID)."""
    try:
        logging.debug('Попытка отправить сообщение в телеграмм.')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Успешная отправка сообщения: {message}')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения!: {error}')


def get_api_answer(timestamp: int) -> Optional[Dict]:
    """Функция выполняющая запрос и возвращающая ответ в формате JSON."""
    params = {'from_date': timestamp}
    try:
        logging.debug('Попытка сделать запрос к API.')
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params)
        logging.debug('Попытка сделать запрос к API прошла успешно.')
    except RequestException:
        raise Exception('Попытка сделать запрос к API прошла неуспешно.')
    status_code = homework_statuses.status_code
    if status_code != HTTPStatus.OK:
        raise Exception(f'Статус код {status_code} != 200')
    return homework_statuses.json()


def check_response(response: Dict) -> List:
    """Функция проверки ответа от эндпоинта на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(
            'Структура данных ответа API не соответствует ожидаемым')
    homeworks = response.get('homeworks')
    if 'homeworks' not in response:
        raise KeyError('В словаре response нет ключа "homeworks"')
    if 'current_date' not in response:
        raise KeyError('В словаре response нет ключа "current_date"')
    if not isinstance(homeworks, list):
        raise TypeError('В ответе API под ключом "homeworks"'
                        ' находится несоответствующий тип данных!')
    return homeworks


def parse_status(homework: Dict) -> Optional[str]:
    """Извлекает из ответа статус домашней работы.
    Возвращает строку, подготовленную для данного статуса
    в словаре HOMEWORK_VERDICTS.
    """
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        raise KeyError('В API ответе не обнаружен ключ homework_name')
    if 'status' not in homework:
        raise KeyError('В API ответе не обнаружен ключ homework_status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError(
            f'Статус домашней работы'
            f' не соответствует документации: {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Отсутствует одна или несколько переменных окружения!'
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = (int(time.time())) - ONE_WEEK
    error = None
    previous_message = None
    while True:
        try:
            answer = get_api_answer(timestamp)
            homework = check_response(answer)
            if homework:
                message = parse_status(homework[0])
                if message != previous_message:
                    send_message(bot, message)
                    previous_message = message
            else:
                logging.error('Переменная homework - пуста.')
        except Exception as err:
            message = f'Сбой в работе программы: {err}'
            logging.error(message, exc_info=True)
            if err != error:
                send_message(bot, message)
                error = err
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
