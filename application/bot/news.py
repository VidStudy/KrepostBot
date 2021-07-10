from telebot import types
from application import telegram_bot as bot
from application.core import userservice
from application.resources import strings, keyboards
from application.utils import bot as botutils
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMedia, Message
from application.core.models import News


def check_news(message: Message):
    if not message.text:
        return False
    user_id = message.from_user.id
    user = userservice.get_user_by_telegram_id(user_id)
    if not user:
        return False
    language = user.language
    return strings.get_string('main_menu.news', language) in message.text and 'private' in message.chat.type


def get_news_keyboard(all_news, current: int, language='ru'):
    keyboard = InlineKeyboardMarkup()
    if current > 0:
        keyboard.add(InlineKeyboardButton(strings.get_string('news.prev', language), callback_data='news:' + str(current-1)))
    if current < len(all_news) - 1:
        keyboard.add(InlineKeyboardButton(strings.get_string('news.next', language), callback_data='news:' + str(current+1)))
    return keyboard


@bot.callback_query_handler(func=lambda call: str(call.data).startswith('news:'))
def news_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    language = userservice.get_user_language(user_id)
    bot.answer_callback_query(call.id)

    all_news = News.query.all()
    segments = str(call.data).split(':')
    news_id = int(segments[1])
    news = all_news[news_id]
    image = open(news.image_path, 'rb')

    keyboard = get_news_keyboard(all_news, news_id, language)
    bot.edit_message_media(media=InputMedia(type='photo', media=image, caption=news.content), chat_id=chat_id, message_id=call.message.message_id, reply_markup=keyboard)


@bot.message_handler(commands=['/news'])
@bot.message_handler(content_types='text', func=lambda m: botutils.check_auth(m) and check_news(m))
def news(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    all_news = News.query.all()
    news = all_news[0]
    if news:
        keyboard = get_news_keyboard(all_news, 0, language)
        image = open(news.image_path, 'rb')
        bot.send_photo(chat_id=chat_id, photo=image, caption=news.content, reply_markup=keyboard)
    else:
        bot.send_message(chat_id=chat_id, message=strings.get_string('news.empty'))

