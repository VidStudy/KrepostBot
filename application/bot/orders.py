from application import telegram_bot as bot
from application.core import orderservice, paymeservice, userservice
from application.resources import strings, keyboards
from application.utils import geocode
from telebot.types import Message, PreCheckoutQuery
from .catalog import back_to_the_catalog
from application.core.models import Order
from .notifications import notify_new_order
from . import registration
from config import Config
import secrets
import settings
import re


@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout_order_query_handler(query: PreCheckoutQuery):
    user_id = query.from_user.id
    chat_id = user_id
    user = userservice.get_user_by_telegram_id(user_id)
    language = user.language
    total = float(query.invoice_payload)
    order = orderservice.confirm_order(user_id, user.full_user_name, total)
    bot.answer_pre_checkout_query(query.id, ok=True)
    order_success_message = strings.get_string('order.success', language)
    bot.clear_step_handler_by_chat_id(chat_id)
    back_to_the_catalog(chat_id, language, order_success_message)
    notify_new_order(order, total)


def _total_order_sum(order_items) -> int:
    summary_dishes_sum = [order_item.count * order_item.dish.price for order_item in order_items]
    total = sum(summary_dishes_sum)
    return total


def _total_cart_sum(cart) -> int:
    summary_dishes_sum = [cart_item.dish.price * cart_item.count
                          for cart_item in cart]
    total = sum(summary_dishes_sum)
    return total


def _to_the_shipping_method(chat_id, language):
    order_shipping_method_message = strings.get_string('order.shipping_method', language)
    order_shipping_method_keyboard = keyboards.get_keyboard('order.shipping_methods', language)
    bot.send_message(chat_id, order_shipping_method_message, parse_mode='HTML',
                     reply_markup=order_shipping_method_keyboard)
    bot.register_next_step_handler_by_chat_id(chat_id, shipping_method_processor)


def _to_the_payment_method(chat_id, language, user_id: int):
    current_order = orderservice.get_current_order_by_user(user_id)
    if current_order.shipping_method == Order.ShippingMethods.PICK_UP:
        payment_message = strings.get_string('order.payment_pickup', language)
    else:
        payment_message = strings.get_string('order.payment_delivery', language)
    payment_keyboard = keyboards.get_keyboard('order.payment', language)
    bot.send_message(chat_id, payment_message, reply_markup=payment_keyboard, parse_mode='HTML')
    bot.register_next_step_handler_by_chat_id(chat_id, payment_method_processor)


def _to_the_address(chat_id, language):
    cart = userservice.get_user_cart(chat_id)
    total = _total_cart_sum(cart)
    cart_contains_message = strings.from_cart_items(cart, language, total)
    address_message = strings.get_string('order.address', language).format(cart_contains_message)
    address_keyboard = keyboards.get_keyboard('order.address', language)
    bot.send_message(chat_id, address_message, parse_mode='HTML', reply_markup=address_keyboard)
    bot.register_next_step_handler_by_chat_id(chat_id, address_processor)


def _to_the_phone_number(chat_id, language, user):
    phone_number_message = strings.get_string('order.phone_number', language)
    phone_number_keyboard = keyboards.from_user_phone_number(language, user.phone_number)
    bot.send_message(chat_id, phone_number_message, reply_markup=phone_number_keyboard, parse_mode='HTML')
    bot.register_next_step_handler_by_chat_id(chat_id, phone_number_processor)


def _to_the_confirmation(chat_id, current_order, language):
    total = _total_order_sum(current_order.order_items.all())
    summary_order_message = strings.from_order(current_order, language, total)
    confirmation_keyboard = keyboards.get_keyboard('order.confirmation', language)
    if current_order.payment_method == Order.PaymentMethods.PAYME:
        confirmation_keyboard = keyboards.get_keyboard('order.confirmation', language)
        bot.send_message(chat_id, summary_order_message, parse_mode='HTML', reply_markup=confirmation_keyboard)
        bot.register_next_step_handler_by_chat_id(chat_id, confirmation_processor, total=total, payme=True)
        return
    elif current_order.payment_method == Order.PaymentMethods.CLICK:
        title = strings.get_string('order.payment.title', language).format(current_order.id)
        description = strings.get_string('order.payment.description', language)
        payload = str(total)
        start_parameter = secrets.token_hex(20)
        currency = 'UZS'
        prices = strings.from_order_items_to_labeled_prices(current_order, language)
        confirmation_keyboard = keyboards.get_keyboard('order.payment_confirmation', language)
        bot.send_message(chat_id, summary_order_message, parse_mode='HTML', reply_markup=confirmation_keyboard)
        invoice = bot.send_invoice(chat_id, title, description, payload, Config.PAYMENT_PROVIDER_TOKEN_CLICK, currency, prices,
                         start_parameter)
        bot.register_next_step_handler_by_chat_id(chat_id, confirmation_processor, total=total, message_id=invoice.message_id)
        return
    else:
        bot.send_message(chat_id, summary_order_message, parse_mode='HTML', reply_markup=confirmation_keyboard)
    bot.register_next_step_handler_by_chat_id(chat_id, confirmation_processor, total=total)


def order_processor(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    cart = userservice.get_user_cart(user_id)
    if len(cart) == 0:
        cart_empty_message = strings.get_string('cart.empty', language)
        back_to_the_catalog(chat_id, language, cart_empty_message)
        return
    _to_the_address(chat_id, language)


def shipping_method_processor(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        if message.text == '/start':
            registration.welcome(message)
            return
        error_msg = strings.get_string('order.shipping_method_error', language)
        bot.send_message(chat_id, error_msg)
        bot.register_next_step_handler_by_chat_id(chat_id, shipping_method_processor)

    if not message.text:
        error()
        return
    orderservice.make_an_order(user_id)
    if strings.get_string('go_to_menu', language) in message.text:
        back_to_the_catalog(chat_id, language)
    elif strings.from_order_shipping_method(Order.ShippingMethods.PICK_UP, language) in message.text:
        orderservice.set_shipping_method(user_id, Order.ShippingMethods.PICK_UP)
        _to_the_payment_method(chat_id, language, user_id)
    elif strings.from_order_shipping_method(Order.ShippingMethods.DELIVERY, language) in message.text:
        orderservice.set_shipping_method(user_id, Order.ShippingMethods.DELIVERY)
        _to_the_address(chat_id, language)
    else:
        error()
        return


def payment_method_processor(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)
    current_order = orderservice.get_current_order_by_user(user_id)

    def error():
        if message.text == '/start':
            registration.welcome(message)
            return
        error_msg = strings.get_string('order.payment_error', language)
        bot.send_message(chat_id, error_msg)
        bot.register_next_step_handler_by_chat_id(chat_id, payment_method_processor)

    def phone_number():
        _to_the_phone_number(chat_id, language, current_order.customer)

    if not message.text:
        error()
        return
    if strings.get_string('go_to_menu', language) in message.text:
        back_to_the_catalog(chat_id, language)
    elif strings.get_string('go_back', language) in message.text:
        if current_order.shipping_method == Order.ShippingMethods.PICK_UP:
            _to_the_shipping_method(chat_id, language)
        elif current_order.shipping_method == Order.ShippingMethods.DELIVERY:
            _to_the_address(chat_id, language)
    elif strings.from_order_payment_method(Order.PaymentMethods.CASH, language) in message.text:
        orderservice.set_payment_method(user_id, Order.PaymentMethods.CASH)
        phone_number()
    elif strings.from_order_payment_method(Order.PaymentMethods.PAYME, language) in message.text:
        orderservice.set_payment_method(user_id, Order.PaymentMethods.PAYME)
        phone_number()
    elif strings.from_order_payment_method(Order.PaymentMethods.CLICK, language) in message.text:
        orderservice.set_payment_method(user_id, Order.PaymentMethods.CLICK)
        phone_number()
    else:
        error()


def phone_number_processor(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        if message.text == '/start':
            registration.welcome(message)
            return
        error_msg = strings.get_string('order.phone_number', language)
        bot.send_message(chat_id, error_msg, parse_mode='HTML')
        bot.register_next_step_handler_by_chat_id(chat_id, phone_number_processor)

    if message.contact is not None:
        current_order = orderservice.set_phone_number(user_id, message.contact.phone_number)
    else:
        if message.text is None:
            error()
            return
        else:
            if strings.get_string('go_back', language) in message.text:
                _to_the_payment_method(chat_id, language, user_id)
                return
            match = re.match(r'\+*998\s*\d{2}\s*\d{3}\s*\d{2}\s*\d{2}', message.text)
            if match is None:
                error()
                return
            phone_number = match.group()
            current_order = orderservice.set_phone_number(user_id, phone_number)
    _to_the_confirmation(chat_id, current_order, language)


def address_processor(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        if message.text == '/start':
            registration.welcome(message)
            return
        error_msg = strings.get_string('order.address_error')
        bot.send_message(chat_id, error_msg, parse_mode='HTML')
        bot.register_next_step_handler_by_chat_id(chat_id, address_processor)

    orderservice.make_an_order(user_id)
    orderservice.set_shipping_method(user_id, Order.ShippingMethods.DELIVERY)

    if message.text:
        if strings.get_string('go_back', language) in message.text:
            back_to_the_catalog(chat_id, language)
            return
        error()
        return
        #orderservice.set_address_by_string(user_id, message.text)
        #_to_the_payment_method(chat_id, language, user_id)
    elif message.location:
        location = message.location
        distance = geocode.distance_between_two_points((location.latitude, location.longitude), settings.get_cafe_coordinates())
        if (distance[0] > settings.get_limit_delivery_km()):
            bot.send_message(chat_id, strings.get_string('order.too_far'))
            back_to_the_catalog(chat_id, language)
            return

        result = orderservice.set_address_by_map_location(user_id, (location.latitude, location.longitude))
        if result:
            _to_the_payment_method(chat_id, language, user_id)
        else:
            error()
    else:
        error()


def confirmation_processor(message: Message, **kwargs):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        if message.text == '/start':
            registration.welcome(message)
            return
        error_msg = strings.get_string('order.confirmation_error', language)
        bot.send_message(chat_id, error_msg)
        bot.register_next_step_handler_by_chat_id(chat_id, confirmation_processor)

    if not message.text:
        error()
        return
    if strings.get_string('order.confirm', language) in message.text:
        total = kwargs.get('total')
        user = userservice.get_user_by_telegram_id(user_id)
        if 'payme' in kwargs:
            order = orderservice.get_current_order_by_user(user_id)
            if order.delivery_price:
                order.total_amount = order.delivery_price + total
            else:
                order.total_amount = total
            paymeservice.create_check(order)
        else:
            order = orderservice.confirm_order(user_id, user.full_user_name, total)
            notify_new_order(order, total)
        order_success_message = strings.get_string('order.success', language)
        back_to_the_catalog(chat_id, language, order_success_message)
    elif strings.get_string('order.cancel', language) in message.text:
        order_canceled_message = strings.get_string('order.canceled', language)
        if 'message_id' in kwargs:
            invoice_message_id = kwargs.get('message_id')
            bot.delete_message(chat_id, invoice_message_id)
        back_to_the_catalog(chat_id, language, order_canceled_message)
    else:
        error()
