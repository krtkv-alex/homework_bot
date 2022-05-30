
import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

OLD_MESSAGE = ''
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'В чат отправлено сообщение:"{message}".')
    except Exception():
        logging.error('Сообщени отправить не удалось.')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(
        ENDPOINT, headers=HEADERS, params=params
    )
    if response.status_code != HTTPStatus.OK:
        logging.error(f'Ошибка {response.status_code}!')
        raise Exception(f'Ошибка {response.status_code}!')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    homework = response['homeworks']
    if type(homework) is not list:
        raise TypeError()
    return homework


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return (
        PRACTICUM_TOKEN is not None
        and TELEGRAM_TOKEN is not None
        and TELEGRAM_CHAT_ID is not None
    )


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        format='%(asctime)s, %(levelname)s, %(message)s',
        filemode='a'
    )

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if check_tokens() is False:
        message = 'У нас проблемы с переменными в коде!'
        logging.critical(message)
        send_message(bot, message)
        raise NameError()

    while True:
        try:
            current_timestamp = int(time.time() - RETRY_TIME)
            response = get_api_answer(current_timestamp)
            homework = check_response(response)[0]
            message = parse_status(homework)
            send_message(bot, message)
            logging.info('Успешная отправка уведомления.')
            time.sleep(RETRY_TIME)
        except IndexError:
            logging.debug('Статус домашки пока не изменился.')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Сбой в работе программы: {error}')
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
