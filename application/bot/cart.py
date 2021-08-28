from application import telegram_bot as bot, db
from application.core import userservice
from application.core.models import CartItem
from application.resources import strings, keyboards
from telebot.types import CallbackQuery, Message
from .catalog import back_to_the_catalog, catalog_processor
from .orders import order_processor
from . import registration


def _total_cart_sum(cart) -> int:
    summary_dishes_sum = [cart_item.dish.price * cart_item.count
                          for cart_item in cart]
    total = sum(summary_dishes_sum)
    return total


def cart_processor(message: Message, callback=None):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    cart = userservice.get_user_cart(user_id)
    total = _total_cart_sum(cart)
    cart_contains_message = strings.from_cart_items(cart, language, total)
    cart_items_keyboard = keyboards.from_cart(cart, language)
    bot.send_message(chat_id, cart_contains_message, parse_mode='HTML', reply_markup=cart_items_keyboard)
    bot.register_next_step_handler_by_chat_id(chat_id, catalog_processor)


@bot.callback_query_handler(func=lambda call: str(call.data).startswith('cart_sub:'))
def cart_sub_query(call: CallbackQuery):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    language = userservice.get_user_language(user_id)

    cart_item_id = int(call.data[len('cart_sub:'):])
    cart_item = CartItem.query.get(cart_item_id)
    if cart_item.count == 1:
        db.session.delete(cart_item)
    else:
        cart_item.count -= 1

    if cart_item.count > cart_item.dish.quantity:
        not_enough_count = strings.get_string('not_enough_count', language).format(cart_item.dish.quantity)
        bot.answer_callback_query(call.id, text=not_enough_count, show_alert=True)
    else:
        bot.answer_callback_query(call.id)

    db.session.commit()

    cart = userservice.get_user_cart(user_id)
    total = _total_cart_sum(cart)
    msg = strings.from_cart_items(cart, language, total)
    kbd = keyboards.from_cart(cart, language)
    bot.edit_message_text(msg, chat_id=chat_id, message_id=call.message.message_id, reply_markup=kbd, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: str(call.data).startswith('cart_add:'))
def cart_add_query(call: CallbackQuery):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    language = userservice.get_user_language(user_id)

    cart_item_id = int(call.data[len('cart_add:'):])
    cart_item = CartItem.query.get(cart_item_id)
    cart_item.count += 1

    if cart_item.count > cart_item.dish.quantity:
        not_enough_count = strings.get_string('not_enough_count', language).format(cart_item.dish.quantity)
        bot.answer_callback_query(call.id, text=not_enough_count, show_alert=True)
        cart_item.count -= 1
    else:
        bot.answer_callback_query(call.id)

    db.session.commit()

    cart = userservice.get_user_cart(user_id)
    total = _total_cart_sum(cart)
    msg = strings.from_cart_items(cart, language, total)
    kbd = keyboards.from_cart(cart, language)
    bot.edit_message_text(msg, chat_id=chat_id, message_id=call.message.message_id, reply_markup=kbd, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: str(call.data).startswith('cart_remove:'))
def cart_remove_query(call: CallbackQuery):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    language = userservice.get_user_language(user_id)

    cart_item_id = int(call.data[len('cart_remove:'):])
    cart_item = CartItem.query.get(cart_item_id)
    db.session.delete(cart_item)
    db.session.commit()

    cart = userservice.get_user_cart(user_id)
    total = _total_cart_sum(cart)
    msg = strings.from_cart_items(cart, language, total)
    kbd = keyboards.from_cart(cart, language)
    bot.edit_message_text(msg, chat_id=chat_id, message_id=call.message.message_id, reply_markup=kbd, parse_mode='HTML')
