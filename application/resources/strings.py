import os
import json
from application.core.models import Dish, Order, Comment, OrderItem
from telebot.types import LabeledPrice
from typing import List
import settings

_basedir = os.path.abspath(os.path.dirname(__file__))

# Load strings from json
# Russian language
_strings_ru = json.loads(open(os.path.join(_basedir, 'strings_ru.json'), 'r', encoding='utf8').read())

# Uzbek language
_strings_uz = json.loads(open(os.path.join(_basedir, 'strings_uz.json'), 'r', encoding='utf8').read())


def _format_number(number: int):
    return '{0:,}'.format(number).replace(',', ' ')


def get_string(key, language='ru'):
    if language == 'ru':
        return _strings_ru.get(key, 'no_string')
    elif language == 'uz':
        return _strings_uz.get(key, 'no_string')
    else:
        raise Exception('Invalid language')


def from_cart_items(cart_items, language, total) -> str:
    cart_contains = ''
    cart_contains += '<b>{}</b>:'.format(get_string('catalog.cart', language))
    cart_contains += '\n\n'
    cart_str_item = "<b>{counter}. {name}</b>\n{count} x {price} = {sum}"
    currency_value = settings.get_currency_value()
    counter = 0
    for cart_item in cart_items:
        counter += 1
        if language == 'uz':
            dish_item = cart_str_item.format(counter=counter,
                                             name=cart_item.dish.description_uz,
                                             count=cart_item.count,
                                             price=_format_number(cart_item.dish.price * currency_value),
                                             sum=_format_number(cart_item.count * cart_item.dish.price * currency_value))
        else:
            dish_item = cart_str_item.format(counter=counter,
                                             name=cart_item.dish.description,
                                             count=cart_item.count,
                                             price=_format_number(cart_item.dish.price * currency_value),
                                             sum=_format_number(cart_item.count * cart_item.dish.price * currency_value))
        dish_item += " {}\n\n".format(get_string('sum', language))
        cart_contains += dish_item
    cart_contains += "\n<b>{}</b> {} {}".format(get_string('cart.summary', language),
                                                 _format_number(total * currency_value),
                                                 get_string('sum', language))

    return cart_contains


def from_contacts(contacts: tuple, language: str) -> str:
    if language == 'uz':
        return 'Ёрдам учун куйидаги контактлар оркали мурожаат килишингиз мумкин.\n\nТелеграм: {}\nТелефон раками: {}'.format(contacts[0], contacts[1])
    return "Вы можете обратиться к нам за помощью по следующим контактам:\n\nНаписать в телеграм: {}\nНомер телефона: {}".format(contacts[0], contacts[1])


def from_dish(dish: Dish, language: str) -> str:
    dish_content = ""
    if language == 'uz':
        if dish.description_uz:
            dish_content += dish.description_uz
            dish_content += '\n\n'
    else:
        if dish.description:
            dish_content += dish.description
            dish_content += '\n\n'
    price = dish.price * settings.get_currency_value()
    price_currency = 'sum'
    if dish.show_usd:
        price = dish.price
        price_currency = 'usd'
    dish_content += "{}: {} {}".format(get_string('dish.price', language),
                                       _format_number(price), get_string(price_currency, language))
    return dish_content


def from_order_shipping_method(value: str, language: str) -> str:
    return get_string('order.' + value, language)


def from_order_payment_method(value: str, language: str) -> str:
    return get_string('order.' + value, language)


def from_order(order: Order, language: str, total: int) -> str:
    currency_value = settings.get_currency_value()
    order_content = "<b>{}:</b>".format(get_string('your_order', language))
    order_content += '\n\n'
    order_content += '<b>{phone}:</b> {phone_value}\n'.format(phone=get_string('phone', language),
                                                              phone_value=order.phone_number)
    order_content += '<b>{payment_type}:</b> {payment_type_value}\n' \
        .format(payment_type=get_string('payment', language),
                payment_type_value=from_order_payment_method(order.payment_method, language))
    order_content += '<b>{shipping_method}:</b> {shipping_method_value}\n'.format(
        shipping_method=get_string('shipping_method', language),
        shipping_method_value=from_order_shipping_method(order.shipping_method, language)
    )
    if order.address_txt:
        order_content += '<b>{address}:</b> {address_value}\n'.format(address=get_string('address', language),
                                                                    address_value=order.address_txt)
    elif order.location:
        order_content += '<b>{address}:</b> {address_value}\n'.format(address=get_string('address', language),
                                                                    address_value=order.location.address)
        order_content += '<b>Дистанция:</b> {}\n'.format(order.distance)
    order_content += '\n\n'
    order_item_tmpl = '<b>{counter}. {name}</b>\n{count} x {price} = {sum} {sum_str}\n'
    counter = 0
    for order_item in order.order_items.all():
        counter += 1
        dish = order_item.dish
        if language == 'uz':
            dish_name = dish.get_full_name_uz()
        else:
            dish_name = dish.get_full_name()
        order_item_str = order_item_tmpl.format(counter=counter,
                                                name=dish_name,
                                                count=order_item.count,
                                                price=_format_number(dish.price * currency_value),
                                                sum=_format_number(order_item.count * dish.price * currency_value),
                                                sum_str=get_string('sum', language))
        order_content += order_item_str + '\n'
    if order.delivery_price:
        order_content += "<b>{}</b> {} {}".format(get_string('cart.summary', language),
                                                  _format_number(total * currency_value + order.delivery_price),
                                                  get_string('sum', language))
    else:
        order_content += "<b>{}</b> {} {}".format(get_string('cart.summary', language),
                                                  _format_number(total * currency_value),
                                                  get_string('sum', language))
    if not order.delivery_price and order.address_txt:
        order_content += '\n\n'
        order_content += '<i>{}</i>'.format(get_string('delivery_price_without_location', language))
    if order.delivery_price:
        order_content += '\n\n'
        order_content += '<i>{}</i>: {} {}'.format(get_string('delivery_price', language),
                                                   _format_number(order.delivery_price),
                                                   get_string('sum', language))
        #order_content += '\n\n'
        #order_content += '<i>{}</i>'.format(get_string('order.delivery_price_helper', language))
    #order_content += '\n\n'
    #order_content += get_string('order.delivery_time', language)
    return order_content


def from_order_notification(order: Order, total_sum):
    order_content = "<b>Новый заказ! #{}</b>".format(order.id)
    order_content += '\n\n'
    order_content += '<b>Номер телефона:</b> {}\n'.format(order.phone_number)
    order_content += '<b>Имя покупателя:</b> {}\n'.format(order.user_name)
    order_content += '<b>Способ оплаты:</b> {}\n'.format(from_order_payment_method(order.payment_method, 'ru'))
    if order.address_txt:
        order_content += '<b>Адрес:</b> {}\n'.format(order.address_txt)
    elif order.location:
        order_content += '<b>Адрес:</b> {}\n'.format(order.location.address)
        order_content += '<b>Дистанция: </b> {}\n'.format(order.distance)
    order_content += '\n\n\U0001F6D2 Корзина:\n'
    order_item_tmpl = '<b>{counter}. {name}</b>\n    {count} x {price} = {sum} сум\n'
    order_items = order.order_items.all()
    grouped_order_items = {}
    categories_list = [oi.dish.category for oi in order_items]
    categories_list = list(set(categories_list))
    for category in categories_list:
        order_items_by_category = list(filter(lambda oi: oi.dish.category_id == category.id, order_items))
        grouped_order_items[category.name] = order_items_by_category
    counter = 0
    for oi in order_items:
        counter += 1
        group_content = '\n'
        group_content += order_item_tmpl.format(counter=counter,
                                               name=oi.dish.description,
                                               count=oi.count,
                                               price=_format_number(oi.dish.price),
                                               sum=_format_number(oi.dish.price * oi.count))
        order_content += group_content
    order_content += "\n<b>Итого: </b>: {} сум".format(_format_number(order.total_amount))
    if order.delivery_price:
        order_content += '\n\n'
        order_content += '<b>Стоимость доставки</b>: {} сум'.format(_format_number(order.delivery_price))
    return order_content


def from_comment_notification(comment: Comment):
    comment_content = "<b>У вас новый отзыв!</b>\n\n"
    comment_content += "<b>От кого:</b> {}".format(comment.username)
    if comment.author.username:
        comment_content += " <i>{}</i>".format(comment.author.username)
    comment_content += "\n"
    if comment.author.phone_number:
        comment_content += "<b>Номер телефона:</b> {}".format(comment.author.phone_number)
        comment_content += '\n'
    comment_content += comment.text
    return comment_content


def from_category_name(category, language):
    if language == 'uz':
        return category.name_uz
    else:
        return category.name


def from_dish_name(dish: Dish, language):
    if language == 'uz':
        return dish.name_uz
    else:
        return dish.name


def from_order_items_to_labeled_prices(order_items: List[OrderItem], language) -> List[LabeledPrice]:
    currency_value = settings.get_currency_value()
    return [LabeledPrice(from_dish_name(oi.dish, language) + ' x ' + str(oi.count), int(oi.count * oi.dish.price * currency_value * 100)) for oi in order_items]
