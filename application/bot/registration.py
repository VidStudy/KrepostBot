import io
from application import telegram_bot
from application.core import userservice
from application.resources import strings, keyboards
from application.utils import bot as botutils
from telebot.types import Message
from telebot import types
import re
import settings


@telegram_bot.message_handler(commands=['start'], func=lambda m: m.chat.type == 'private')
def request_age(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    current_user = userservice.get_user_by_telegram_id(user_id)
    if current_user:
        botutils.to_main_menu(chat_id, current_user.language)
        return
    else:
        accept_age = types.ReplyKeyboardMarkup(resize_keyboard = True)
        accept_age.add(types.KeyboardButton('Исполнилось'))
        accept_age.add(types.KeyboardButton('Не исполнилось'))
        error_msg = ('Для дальнейшего использования бота подтвердите, что вам исполнился 21 год.')
        telegram_bot.send_message(chat_id, error_msg, reply_markup=accept_age, parse_mode='HTML')
        telegram_bot.register_next_step_handler_by_chat_id(chat_id, process_age)


def process_age(message):
    chat_id = message.chat.id
    if message.text.startswith('Исполнилось'):
        request_accept_policy(message)
    else:
        telegram_bot.send_message(chat_id, 'Использование бота не предоставляется возможным', parse_mode='HTML')
        telegram_bot.register_next_step_handler_by_chat_id(chat_id, process_age)
        return


def request_accept_policy(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    accept_text = """
    Подтвердите своё согласие с публичной оффертой. \n
Publik offerta bilan tanishib chiqqaningizni tasdiqlang!\n
    """
    accept_policy = types.ReplyKeyboardMarkup(resize_keyboard = True)
    item1 = types.KeyboardButton('🤝 Я согласен(сна) / Rozilik beraman')
    accept_policy.add(item1)

    with open(settings.get_files()['tos'], 'rb') as doc:
        document = io.BytesIO(doc.read())
        extension = settings.get_files()['tos'].split('.')[-1]
        document.name = 'offerta.' + extension
        telegram_bot.send_document(chat_id, document, caption=accept_text, reply_markup=accept_policy, parse_mode='HTML')
    telegram_bot.register_next_step_handler_by_chat_id(chat_id, welcome)


def welcome(message):
    chat_id = message.chat.id

    def error():
        if message.text == '/start':
            request_age(message)
            return
        accept_policy = types.ReplyKeyboardMarkup(resize_keyboard = True)
        item1 = types.KeyboardButton('🤝 Я согласен(сна) / Rozilik beraman')
        accept_policy.add(item1)
        error_msg = ('Примите пользовательское соглашение!  \n\nFoydalanuvchi shartnomasini qabul qiling!')
        telegram_bot.send_message(chat_id, error_msg, reply_markup=accept_policy, parse_mode='HTML')
        telegram_bot.register_next_step_handler_by_chat_id(chat_id, welcome)

    if message.text.startswith('🤝'):
        accept_policy = True
        welcome_message = strings.get_string('welcome')
        language_keyboard = keyboards.get_keyboard('welcome.language')
        telegram_bot.send_message(chat_id, welcome_message, reply_markup=language_keyboard, parse_mode='HTML')
        telegram_bot.register_next_step_handler_by_chat_id(chat_id, process_user_language, accept_policy=accept_policy)
    else:
        error()
        return


def process_user_language(message: Message, **kwargs):
    chat_id = message.chat.id
    accept_policy = kwargs.get('accept_policy')

    def error():
        if message.text == '/start':
            request_age(message)
            return
        error_msg = strings.get_string('welcome.say_me_language')
        telegram_bot.send_message(chat_id, error_msg)
        telegram_bot.register_next_step_handler_by_chat_id(chat_id, process_user_language)

    if not message.text:
        error()
        return
    if message.text.startswith('/'):
        error()
        return
    if strings.get_string('language.russian') in message.text:
        language = 'ru'
    elif strings.get_string('language.uzbek') in message.text:
        language = 'uz'
    else:
        error()
        return
    request_registration_handler(message, language, accept_policy=accept_policy)


def request_registration_handler(message: Message, language: str, accept_policy: bool):
    chat_id = message.chat.id

    welcome_message = strings.get_string('registration.request.welcome', language)
    remove_keyboard = keyboards.get_keyboard('remove')
    telegram_bot.send_message(chat_id, welcome_message, reply_markup=remove_keyboard)
    telegram_bot.register_next_step_handler_by_chat_id(chat_id, request_registration_name_handler, language=language, accept_policy=accept_policy)


def request_registration_name_handler(message: Message, **kwargs):
    chat_id = message.chat.id
    language = kwargs.get('language')
    accept_policy = kwargs.get('accept_policy')

    def error():
        if message.text == '/start':
            request_age(message)
            return
        error_msg = strings.get_string('registration.request.welcome', language)
        telegram_bot.send_message(chat_id, error_msg)
        telegram_bot.register_next_step_handler_by_chat_id(chat_id, request_registration_name_handler,
                                                           language=language)

    if not message.text:
        error()
        return
    if message.text == '/start':
        error()
        return
    name = message.text
    phone_number_message = strings.get_string('registration.request.phone_number', language)
    phone_number_keyboard = keyboards.from_user_phone_number(language, go_back=False)
    telegram_bot.send_message(chat_id, phone_number_message, parse_mode='HTML', reply_markup=phone_number_keyboard)
    telegram_bot.register_next_step_handler_by_chat_id(chat_id, request_registration_phone_number_handler, name=name,
                                                       language=language, accept_policy=accept_policy)


def request_registration_phone_number_handler(message: Message, **kwargs):
    chat_id = message.chat.id
    user_id = message.from_user.id
    name = kwargs.get('name')
    language = kwargs.get('language')
    accept_policy = kwargs.get('accept_policy')

    def error():
        if message.text == '/start':
            request_age(message)
            return
        error_msg = strings.get_string('registration.request.phone_number', language)
        telegram_bot.send_message(chat_id, error_msg, parse_mode='HTML')
        telegram_bot.register_next_step_handler_by_chat_id(chat_id, request_registration_phone_number_handler, name=name, language=language)

    if message.contact is not None:
        phone_number = message.contact.phone_number
    else:
        if message.text is None:
            error()
            return
        else:
            match = re.match(r'\+*998\s*\d{2}\s*\d{3}\s*\d{2}\s*\d{2}', message.text)
            if match is None:
                error()
                return
            phone_number = match.group()
    userservice.register_user(user_id, message.from_user.username, name, phone_number, language, accept_policy)
    success_message = strings.get_string("welcome.registration_successfully", language)
    botutils.to_main_menu(chat_id, language, success_message)
