from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from application.resources.strings import get_string, from_order_shipping_method, from_order_payment_method
from application.core.models import Order
from application.utils.bot import to_main_menu

_keyboards_ru = {
    'remove': ReplyKeyboardRemove()
}
_keyboards_uz = {
    'remove': ReplyKeyboardRemove()
}

_default_value = ReplyKeyboardMarkup(resize_keyboard=True)
_default_value.add('no_keyboard')

# Initialization russian keyboards
_welcome_language = ReplyKeyboardMarkup(resize_keyboard=True)
_welcome_language.add(get_string('language.russian'), get_string('language.uzbek'))
_keyboards_ru['welcome.language'] = _welcome_language

_main_menu_ru = ReplyKeyboardMarkup(resize_keyboard=True)
_main_menu_ru.add(get_string('main_menu.make_order'), get_string('main_menu.my_orders'))
_main_menu_ru.add(get_string('main_menu.send_comment'), get_string('main_menu.news'))
_main_menu_ru.add(get_string('main_menu.language'), get_string('main_menu.contacts'))
_keyboards_ru['main_menu'] = _main_menu_ru

_my_orders_menu_ru = ReplyKeyboardMarkup(resize_keyboard=True)
_my_orders_menu_ru.add(get_string('my_orders.repeat'))
_my_orders_menu_ru.add(get_string('go_back'))
_keyboards_ru['my_orders_menu'] = _my_orders_menu_ru

_go_back_ru = ReplyKeyboardMarkup(resize_keyboard=True)
_go_back_ru.add(get_string('go_back'))
_keyboards_ru['go_back'] = _go_back_ru

_dish_keyboard_ru = InlineKeyboardMarkup(row_width=3)
_count_keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '15', '20', '25', '30', '35']
_count_keys_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35]
_dish_keyboard_ru.add(*[InlineKeyboardButton(_count_keys[i], callback_data='count:' + str(_count_keys_values[i])) for i in list(range(len(_count_keys)))])
_keyboards_ru['catalog.dish_keyboard'] = _dish_keyboard_ru

_shipping_methods_keyboard_ru = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
_shipping_methods_keyboard_ru.add(from_order_shipping_method(Order.ShippingMethods.DELIVERY, 'ru'),
                                  from_order_shipping_method(Order.ShippingMethods.PICK_UP, 'ru'),
                                  get_string('go_to_menu'))
_keyboards_ru['order.shipping_methods'] = _shipping_methods_keyboard_ru

_order_location_keyboard_ru = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
location_button = KeyboardButton(get_string('my_location'), request_location=True)
_order_location_keyboard_ru.add(location_button)
_order_location_keyboard_ru.add(get_string('go_back'))
_keyboards_ru['order.address'] = _order_location_keyboard_ru

_order_payment_keyboard_ru = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
_order_payment_keyboard_ru.add(from_order_payment_method(Order.PaymentMethods.PAYME, 'ru'),
                               from_order_payment_method(Order.PaymentMethods.CLICK, 'ru'),
                               from_order_payment_method(Order.PaymentMethods.CASH, 'ru'))
_order_payment_keyboard_ru.add(get_string('go_back'), get_string('go_to_menu'))
_keyboards_ru['order.payment'] = _order_payment_keyboard_ru

_order_confirmation_keyboard_ru = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
_order_confirmation_keyboard_ru.add(get_string('order.confirm'), get_string('order.cancel'))
_keyboards_ru['order.confirmation'] = _order_confirmation_keyboard_ru
_order_confirmation_payment_keyboard_ru = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
_order_confirmation_payment_keyboard_ru.add(get_string('order.cancel', 'ru'))
_keyboards_ru['order.payment_confirmation'] = _order_confirmation_payment_keyboard_ru

_comments_keyboard_ru = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
_comments_keyboard_ru.add(*[get_string('comments.point_' + str(x)) for x in list(reversed(range(1, 6)))])
_comments_keyboard_ru.add(get_string('go_to_menu'))
_keyboards_ru['comments.send_comment'] = _comments_keyboard_ru

# Initialization uzbek keyboards
_main_menu_uz = ReplyKeyboardMarkup(resize_keyboard=True)
_main_menu_uz.add(get_string('main_menu.make_order', 'uz'), get_string('main_menu.my_orders', 'uz'))
_main_menu_uz.add(get_string('main_menu.send_comment', 'uz'), get_string('main_menu.news', 'uz'))
_main_menu_uz.add(get_string('main_menu.language', 'uz'), get_string('main_menu.contacts', 'uz'))
_keyboards_uz['main_menu'] = _main_menu_uz

_go_back_uz = ReplyKeyboardMarkup(resize_keyboard=True)
_go_back_uz.add(get_string('go_back', 'uz'))
_keyboards_uz['go_back'] = _go_back_uz

_my_orders_menu_uz = ReplyKeyboardMarkup(resize_keyboard=True)
_my_orders_menu_uz.add(get_string('my_orders.repeat', 'uz'))
_my_orders_menu_uz.add(get_string('go_back', 'uz'))
_keyboards_uz['my_orders_menu'] = _my_orders_menu_uz

_keyboards_uz['catalog.dish_keyboard'] = _dish_keyboard_ru

_shipping_methods_keyboard_uz = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
_shipping_methods_keyboard_uz.add(from_order_shipping_method(Order.ShippingMethods.DELIVERY, 'uz'),
                                  from_order_shipping_method(Order.ShippingMethods.PICK_UP, 'uz'),
                                  get_string('go_to_menu', 'uz'))
_keyboards_uz['order.shipping_methods'] = _shipping_methods_keyboard_uz
_order_location_keyboard_uz = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
location_button_uz = KeyboardButton(get_string('my_location', 'uz'), request_location=True)
_order_location_keyboard_uz.add(location_button_uz)
_order_location_keyboard_uz.add(get_string('go_back', 'uz'))
_keyboards_uz['order.address'] = _order_location_keyboard_uz
_order_payment_keyboard_uz = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
_order_payment_keyboard_uz.add(from_order_payment_method(Order.PaymentMethods.PAYME, 'uz'),
                               from_order_payment_method(Order.PaymentMethods.CLICK, 'uz'),
                               from_order_payment_method(Order.PaymentMethods.CASH, 'uz'))
_order_payment_keyboard_uz.add(get_string('go_back', 'uz'), get_string('go_to_menu', 'uz'))
_keyboards_uz['order.payment'] = _order_payment_keyboard_uz
_order_confirmation_keyboard_uz = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
_order_confirmation_keyboard_uz.add(get_string('order.confirm', 'uz'), get_string('order.cancel', 'uz'))
_keyboards_uz['order.confirmation'] = _order_confirmation_keyboard_uz
_order_confirmation_payment_keyboard_uz = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
_order_confirmation_payment_keyboard_uz.add(get_string('order.cancel', 'uz'))
_keyboards_uz['order.payment_confirmation'] = _order_confirmation_payment_keyboard_uz
_comments_keyboard_uz = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
_comments_keyboard_uz.add(*[get_string('comments.point_' + str(x), 'uz') for x in list(reversed(range(1, 6)))])
_comments_keyboard_uz.add(get_string('go_to_menu', 'uz'))
_keyboards_uz['comments.send_comment'] = _comments_keyboard_uz


def get_keyboard(key, language='ru'):
    if language == 'ru':
        return _keyboards_ru.get(key, _default_value)
    elif language == 'uz':
        return _keyboards_uz.get(key, _default_value)
    else:
        raise Exception('Invalid language')


def from_dish_categories(dish_categories, language: str) -> ReplyKeyboardMarkup:
    categories_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    categories_keyboard.add(get_string('catalog.cart', language), get_string('catalog.make_order', language))
    if language == 'uz':
        names = [category.name_uz for category in dish_categories]
    else:
        names = [category.name for category in dish_categories]
    categories_keyboard.add(*names)
    categories_keyboard.add(get_string('go_back', language))
    return categories_keyboard


def from_dishes(dishes, language: str) -> ReplyKeyboardMarkup:
    dishes_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    dishes_keyboard.add(get_string('catalog.cart', language), get_string('go_back', language))
    if language == 'uz':
        names = [dish.name_uz for dish in dishes]
    else:
        names = [dish.name for dish in dishes]
    dishes_keyboard.add(*names)
    dishes_keyboard.add(get_string('go_to_menu', language))
    return dishes_keyboard


def from_my_orders(orders, language) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    for order in orders:
        button = get_string('my_orders.order', language).format(order.id,
                        order.confirmation_date.strftime('%d.%m.%Y'))
        keyboard.add(button)
    keyboard.add(get_string('go_to_menu', language))
    return keyboard


def from_cart(cart_items, language):
    ret = InlineKeyboardMarkup()
    cart_dict = {}
    for cart_item in cart_items:
        if cart_item in cart_dict:
            cart_dict[cart_item] += 1
        else:
            cart_dict[cart_item] = 1
    for item in cart_dict:
        ret.add(InlineKeyboardButton(item.dish.name, callback_data='none'))
        ret.add(InlineKeyboardButton('➖', callback_data='cart_sub:' + str(item.id)),
            InlineKeyboardButton('✖️', callback_data='cart_remove:' + str(item.id)),
            InlineKeyboardButton('➕', callback_data='cart_add:' + str(item.id)))
    return ret


def from_cart_items(cart_items, language) -> ReplyKeyboardMarkup:
    cart_items_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    cart_dict = {}
    counter = 0
    for cart_item in cart_items:
        counter += 1
        cart_dict[counter] = cart_item
    names = list(cart_dict.keys())
    names = ['❌ ' + str(name) for name in names]
    cart_items_keyboard.add(*names)
    cart_items_keyboard.add(get_string('go_back', language), get_string('cart.clear', language))
    cart_items_keyboard.add(get_string('catalog.make_order', language))
    return cart_items_keyboard


def from_change_language(current_language: str) -> ReplyKeyboardMarkup:
    change_language_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    if current_language == 'uz':
        change_language_keyboard.add(get_string('language.russian'))
    else:
        change_language_keyboard.add(get_string('language.uzbek'))
    change_language_keyboard.add(get_string('go_back', current_language))
    return change_language_keyboard


def from_user_phone_number(language, phone_number: str = None, go_back: bool = True) -> ReplyKeyboardMarkup:
    phone_number_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    if phone_number and phone_number != '':
        phone_number_keyboard.add(phone_number)
    phone_button = KeyboardButton(get_string('my_number', language), request_contact=True)
    phone_number_keyboard.add(phone_button)
    if go_back:
        phone_number_keyboard.add(get_string('go_back', language))
    return phone_number_keyboard
