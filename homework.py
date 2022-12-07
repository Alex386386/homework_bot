import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Dict, Optional

import requests
import telegram
from dotenv import load_dotenv

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
ONE_MONTH: int = 2592000

HOMEWORK_VERDICTS: Dict[str, str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
condition: str = ''


def check_tokens() -> bool:
    """Функция проверки доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message: Optional[str]) -> None:
    """Функция отправки любого сообщения(message) в чат (TELEGRAM_CHAT_ID)."""
    if message is None:
        return None
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Успешная отправка сообщения: {message}')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения!: {error}')


def get_api_answer(timestamp: int) -> Optional[Dict]:
    """
    Функция выполняющая запрос к эндпоинту и возвращающая ответ в формате JSON.
    """
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
        return
    status_code = homework_statuses.status_code
    if status_code != HTTPStatus.OK:
        raise Exception(f'Статус код {status_code} != 200')
    return homework_statuses.json()


def check_response(response: Dict) -> Dict:
    """Функция проверки ответа от эндпоинта на соответствие документации."""
    expected_keys = ['current_date', 'homeworks']
    if type(response) is not dict:
        raise TypeError(
            'Структура данных ответа API не соответствует ожидаемым')
    if type(response.get('homeworks')) != list:
        raise TypeError('В ответе API под ключом "homeworks"'
                        ' находится несоответствующий тип данных!')
    try:
        if expected_keys[0] in response and expected_keys[1] in response:
            return response.get('homeworks')[0]
    except Exception as error:
        logging.error(f'Ответ API не прошёл проверку '
                      f'на соответствие документации: {error}')


def parse_status(homework: Dict) -> Optional[str]:
    """
    Извлекает из ответа статус домашней работы и возвращает строку,
    подготовленную для данного статуса в словаре HOMEWORK_VERDICTS.
    """
    global condition
    if 'homework_name' not in homework:
        raise Exception('В ответе API домашней работы нет названия!')
    homework_name = homework.get('homework_name')
    verdict = homework.get('status')
    if verdict not in HOMEWORK_VERDICTS:
        logging.error('В API ответе обнаружен неожиданный статус')
        raise Exception(
            f'Статус домашней работы не соответствует документации{verdict}')
    if condition == '':
        condition = verdict
        logging.debug(f'Изменился статус: {verdict}')
        verdicts = HOMEWORK_VERDICTS[verdict]
        return (f'Изменился статус проверки работы "{homework_name}".'
                f' {verdicts}')
    if verdict != condition:
        condition = verdict
        logging.debug(f'Изменился статус: {verdict}')
        verdicts = HOMEWORK_VERDICTS[verdict]
        return (f'Изменился статус проверки работы "{homework_name}".'
                f' {verdicts}')
    elif verdict == condition:
        logging.debug(f'Статус работы не изменился: {verdict}')


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Отсутствует одна или несколько переменных окружения!'
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = (int(time.time())) - ONE_MONTH
    while True:
        try:
            answer = get_api_answer(timestamp)
            homework = check_response(answer)
            message = parse_status(homework)
            send_message(bot, message)
            time.sleep(RETRY_PERIOD)
            continue
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            break


if __name__ == '__main__':
    main()
