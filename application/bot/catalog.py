from application import telegram_bot as bot
from application.core import userservice, dishservice
from application.resources import strings, keyboards
from application.utils import bot as botutils
from telebot.types import Message
from application.core import exceptions
from application.core.models import Dish, DishCategory
from . import userservice
from datetime import datetime, timezone, timedelta, time
import settings


def check_catalog(message: Message):
    if not message.text:
        return False
    user_id = message.from_user.id
    user = userservice.get_user_by_telegram_id(user_id)
    if not user:
        return False
    language = user.language
    return strings.get_string('main_menu.make_order', language) in message.text and 'private' in message.chat.type


def back_to_the_catalog(chat_id, language, message_text=None, parent_category_id=None):
    parent_category = dishservice.get_category_by_id(parent_category_id)
    bot.send_chat_action(chat_id, 'typing')
    if not message_text:
        catalog_message = strings.get_string('catalog.start', language)
    else:
        catalog_message = message_text
    if parent_category:
        catalog_message = strings.from_category_name(parent_category, language)
        categories = parent_category.get_siblings(include_self=True).order_by(DishCategory.name.asc()).all()
        category_keyboard = keyboards.from_dish_categories(categories, language)
        bot.send_message(chat_id, catalog_message, reply_markup=category_keyboard)
        if parent_category.parent:
            bot.register_next_step_handler_by_chat_id(chat_id, catalog_processor, parent_category_id=parent_category.parent.id)
        else:
            bot.register_next_step_handler_by_chat_id(chat_id, catalog_processor)
        return
    categories = dishservice.get_parent_categories(sort_by_number=True)
    category_keyboard = keyboards.from_dish_categories(categories, language)
    bot.send_message(chat_id, catalog_message, reply_markup=category_keyboard, parse_mode='HTML')
    bot.register_next_step_handler_by_chat_id(chat_id, catalog_processor)


def dish_action_processor(message: Message, **kwargs):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)
    message_id = kwargs.get('message_id')
    current_dish = userservice.get_current_user_dish(user_id)
    if strings.get_string('go_back', language) in message.text:
        back_to_the_catalog(chat_id, language, parent_category_id=current_dish.category.id)

    elif strings.get_string('go_to_menu', language) in message.text:
        botutils.to_main_menu(chat_id, language)##MENU

    elif strings.get_string('catalog.cart', language) in message.text:
        user_cart.cart_processor(message, dish_action_processor)

    else:
        choose_dish_processor(message, category_id=current_dish.category.id)

    if message_id:
        bot.delete_message(chat_id, message_id)

@bot.callback_query_handler(func=lambda call: str(call.data).startswith('count:'))
def count_callback_query(call):
    def _total_cart_sum(cart) -> int:
        summary_dishes_sum = [cart_item.dish.price * cart_item.count
                              for cart_item in cart]
        total = sum(summary_dishes_sum)
        return total
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    language = userservice.get_user_language(user_id)
    bot.answer_callback_query(call.id)
    bot.clear_step_handler_by_chat_id(chat_id)
    selected_number = int(call.data[6:])
    current_dish = userservice.get_current_user_dish(user_id)
    dish_to_check = Dish.query.get(current_dish.id)
    if selected_number > dish_to_check.quantity:
        not_enough_count = strings.get_string('not_enough_count', language).format(dish_to_check.quantity)
        msg = bot.send_message(chat_id, text=not_enough_count)
        bot.register_next_step_handler(msg, dish_action_processor)
    else:
        userservice.add_dish_to_cart(user_id, current_dish, selected_number)
        cart = userservice.get_user_cart(user_id)
        total = _total_cart_sum(cart)
        bot.delete_message(chat_id, call.message.message_id)
        cart_contains_message = strings.from_cart_items(cart, language, total)
        continue_message = strings.get_string('catalog.continue', language).format(cart_contains_message)
        back_to_the_catalog(chat_id, language, continue_message)
        catalog_message = strings.get_string('catalog.start', language)
        bot.send_message(chat_id, catalog_message, parse_mode='HTML')

def choose_dish_processor(message: Message, **kwargs):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        if message.text == '/start':
            registration.welcome(message)
            return
        error_message = strings.get_string('catalog.dish_error', language)
        bot.send_message(chat_id, error_message)
        bot.register_next_step_handler_by_chat_id(chat_id, choose_dish_processor)

    if not message.text:
        error()
        return
    if strings.get_string('go_back', language) in message.text:
        if 'category_id' in kwargs:
            category_id = kwargs.get('category_id')
            back_to_the_catalog(chat_id, language, parent_category_id=category_id)
            return
        back_to_the_catalog(chat_id, language)

    elif strings.get_string('go_to_menu', language) in message.text:
        botutils.to_main_menu(chat_id, language)##MENU

    elif strings.get_string('catalog.cart', language) in message.text:
        user_cart.cart_processor(message, choose_dish_processor)
    else:
        dish_name = message.text
        dish = dishservice.get_dish_by_name(dish_name, language, dishservice.get_category_by_id(kwargs.get('category_id')))
        if not dish:
            error()
            return
        userservice.set_current_user_dish(user_id, dish.id)
        dish_info = strings.from_dish(dish, language)
        dish_keyboard = keyboards.get_keyboard('catalog.dish_keyboard', language)
        msg_id = None
        if dish.image_id or dish.image_path:
            if dish.image_path and not dish.image_id:
                try:
                    image = open(dish.image_path, 'rb')
                except FileNotFoundError:
                    bot.send_message(chat_id, dish_info, reply_markup=dish_keyboard, parse_mode='HTML')
                else:
                    sent_message = bot.send_photo(chat_id, image, caption=dish_info, reply_markup=dish_keyboard, parse_mode='HTML')
                    dishservice.set_dish_image_id(dish, sent_message.photo[-1].file_id)
                    msg_id = sent_message.message_id
            elif dish.image_id:
                msg_id = bot.send_photo(chat_id, dish.image_id, caption=dish_info, reply_markup=dish_keyboard, parse_mode='HTML').message_id
        else:
            msg_id = bot.send_message(chat_id, dish_info, reply_markup=dish_keyboard, parse_mode='HTML').message_id
        bot.register_next_step_handler_by_chat_id(chat_id, dish_action_processor, message_id=msg_id)


def catalog_processor(message: Message, **kwargs):

    def send_category(category, message, keyboard):
        if category.image_path or category.image_id:
            if category.image_path and not category.image_id:
                try:
                    image = open(category.image_path, 'rb')
                except FileNotFoundError:
                    bot.send_message(chat_id=chat_id, text=message, reply_markup=keyboard)
                else:
                    sent_message = bot.send_photo(chat_id=chat_id, photo=image, caption=message,
                                                  reply_markup=keyboard)
                    dishservice.set_category_image_id(category, sent_message.photo[-1].file_id)
            elif category.image_id:
                bot.send_photo(chat_id=chat_id, photo=category.image_id, caption=message, reply_markup=keyboard)
        else:
            bot.send_message(chat_id=chat_id, text=message, reply_markup=keyboard)

    chat_id = message.chat.id
    if message.successful_payment:
        bot.register_next_step_handler_by_chat_id(chat_id, catalog_processor)
        return
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)

    def error():
        if message.text == '/start':
            registration.welcome(message)
            return
        error_message = strings.get_string('catalog.error', language)
        bot.send_message(chat_id, error_message)
        bot.register_next_step_handler_by_chat_id(chat_id, catalog_processor)

    if not message.text:
        error()
        return
    if strings.get_string('go_back', language) in message.text:
        parent_category_id = kwargs.get('parent_category_id', None)
        if not parent_category_id:
            botutils.to_main_menu(chat_id, language)
            return
        back_to_the_catalog(chat_id, language, parent_category_id=parent_category_id)

    elif strings.get_string('go_to_menu', language) in message.text:
        botutils.to_main_menu(chat_id, language)##MENU


    elif strings.get_string('catalog.cart', language) in message.text:
        user_cart.cart_processor(message)
    elif strings.get_string('catalog.make_order', language) in message.text:
        orders.order_processor(message)
    else:
        category_name = message.text
        parent_category = dishservice.get_category_by_id(kwargs.get('parent_category_id', None))
        category = dishservice.get_category_by_name(category_name, language, parent_category)
        if not category:
            error()
            return
        if category.get_children().count() > 0:
            categories = category.get_children().order_by(DishCategory.name.asc()).all()
            catalog_message = strings.from_category_name(category, language)
            category_keyboard = keyboards.from_dish_categories(categories, language)
            send_category(category, catalog_message, category_keyboard)
            bot.register_next_step_handler_by_chat_id(chat_id, catalog_processor, parent_category_id=category.id)
        elif category.dishes.count() > 0:
            dishes = category.dishes.filter(Dish.is_hidden == False).order_by(Dish.number.asc())
            dish_message = strings.get_string('catalog.choose_dish', language)
            dishes_keyboard = keyboards.from_dishes(dishes, language)
            send_category(category, dish_message, dishes_keyboard)
            bot.register_next_step_handler_by_chat_id(chat_id, choose_dish_processor, category_id=category.id)
        else:
            empty_message = strings.get_string('catalog.empty', language)
            bot.send_message(chat_id, empty_message)
            if category.parent:
                bot.register_next_step_handler_by_chat_id(chat_id, catalog_processor, parent_category_id=category.parent.id)
            else:
                bot.register_next_step_handler_by_chat_id(chat_id, catalog_processor)


@bot.message_handler(commands=['order'], func=botutils.check_auth)
@bot.message_handler(content_types=['text'], func=lambda m: botutils.check_auth(m) and check_catalog(m))
def work_hours(message: Message):
    get = settings.get_timelimits()
    now = datetime.time(datetime.now(timezone(timedelta(hours=5))))
    morning = time(int(get[0].split(':')[0]), int(get[0].split(':')[1]))
    night = time(int(get[1].split(':')[0]), int(get[1].split(':')[1]))
    notify = settings.get_timenotify()
    if morning <= now <= night:
        catalog(message)
    else:
        bot.send_message(message.chat.id, notify)


def catalog(message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    language = userservice.get_user_language(user_id)
    bot.send_chat_action(chat_id, 'typing')
    catalog_message = strings.get_string('catalog.start', language)
    categories = dishservice.get_parent_categories(sort_by_number=True)
    if len(categories) == 0:
        empty_message = strings.get_string('catalog.empty', language)
        bot.send_message(chat_id, empty_message)
        return
    category_keyboard = keyboards.from_dish_categories(categories, language)
    bot.send_message(chat_id, catalog_message, reply_markup=category_keyboard)
    bot.register_next_step_handler_by_chat_id(chat_id, catalog_processor)


from . import registration
from . import orders
from . import cart as user_cart
