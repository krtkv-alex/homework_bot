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
    params = {'from_date': current_timestamp}
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
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        format='%(asctime)s, %(levelname)s, %(message)s',
        filemode='a'
    )
    checked_homework_status = ''
    current_timestamp = 0

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if check_tokens() is False:
        message = 'У нас проблемы с переменными в коде!'
        logging.critical(message)
        raise NameError()

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date') - RETRY_TIME
            homework = check_response(response)[0]
# На мой взгляд в этой проверке нет смысла. Потому что в 'current_timestamp'
# я вычисляю время от последней проверки до нынешней. За этот период я же
# никак не могу получить 'homework', если не изменился статус домашки.
# Список будет пустой и я словлю IndexError, после чего следующая проверка
# будет только через 10 минут.
            if checked_homework_status != homework.get('homework_name'):
                checked_homework_status = homework.get('homework_name')
                message = parse_status(homework)
                send_message(bot, message)
                logging.info('Успешная отправка уведомления.')
        except IndexError:
            logging.debug('Статус домашки пока не изменился.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Сбой в работе программы: {error}')
            send_message(bot, message)
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
