from application import telegram_bot as bot
from application.core import orderservice, userservice
from application.resources import strings, keyboards
from application.utils import bot as botutils
from telebot.types import Message
from . import cart as user_cart


def check_my_orders(message: Message):
    if not message.text:
        return False
    user_id = message.from_user.id
    user = userservice.get_user_by_telegram_id(user_id)
    if not user:
        return False
    language = user.language
    return strings.get_string('main_menu.my_orders', language) in message.text and 'private' in message.chat.type


@bot.message_handler(commands=['/myorders'])
@bot.message_handler(content_types='text', func=lambda m: botutils.check_auth(m) and check_my_orders(m))
def my_orders(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    orders = orderservice.get_user_orders(user_id)
    if len(orders) == 0:
        message = strings.get_string('my_orders.empty', language)
    else:
        message = strings.get_string('my_orders.orders', language) + '\n\n'
        for order in orders:
            message += strings.get_string('my_orders.order', language).format(
                order.id, order.confirmation_date.strftime('%d.%m.%Y')) + '\n'

    keyboard = keyboards.from_my_orders(orders, language)
    bot.send_message(chat_id, message, reply_markup=keyboard)
    bot.register_next_step_handler_by_chat_id(chat_id, my_orders_processor)


def my_orders_processor(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        message = strings.get_string('my_orders.error', language)
        bot.send_message(chat_id, message)
        bot.register_next_step_handler_by_chat_id(chat_id, my_orders_processor)

    if not message.text:
        error()
        return

    if strings.get_string('go_to_menu', language) in message.text:
        botutils.to_main_menu(chat_id, language)
        return

    # split keyboard, get second word, discard #
    if len(message.text.split()) < 2:
        error()
        return
    order_id = message.text.split()[1][1:]
    order = orderservice.get_order_by_id(order_id)
    if not order:
        error()
        return

    message = strings.from_order(order, language, order.total_amount)
    keyboard = keyboards.get_keyboard('my_orders_menu', language)
    bot.send_message(chat_id, message, reply_markup=keyboard, parse_mode='HTML')
    bot.register_next_step_handler_by_chat_id(chat_id, my_order_repeat_processor, order_id=order_id)


def my_order_repeat_processor(message: Message, **kwargs):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        message = strings.get_string('main_menu.choose_option', language)
        bot.send_message(chat_id, message)
        bot.register_next_step_handler_by_chat_id(chat_id, my_order_repeat_processor)

    if strings.get_string('go_back', language) in message.text:
        my_orders(message)
        return

    if strings.get_string('my_orders.repeat', language) in message.text:
        order_id = kwargs.get('order_id')
        order = orderservice.get_order_by_id(order_id)
        userservice.clear_user_cart(user_id)
        for item in order.order_items:
            userservice.add_dish_to_cart(user_id, item.dish, item.count)
        user_cart.cart_processor(message)

    error()