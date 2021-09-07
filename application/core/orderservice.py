from application import db
from application.core.models import Order, User, Location, Dish
from application.utils import geocode, date
from . import userservice
from datetime import datetime, timedelta
import settings
from math import floor
from typing import List
from telebot.types import Message


def get_current_order_by_user(user_id: int) -> Order:
    user = userservice.get_user_by_telegram_id(user_id)
    return user.orders.filter(Order.confirmed != True, Order.created_at == None).first()


def get_order_yesterday_today_statistic():
    all_orders = Order.query.filter(Order.confirmed == True).all()
    yesterday = date.convert_utc_to_asia_tz(datetime.utcnow() - timedelta(days=1))
    yesterday_start = datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=yesterday.tzinfo)
    yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, tzinfo=yesterday.tzinfo)
    today = date.convert_utc_to_asia_tz(datetime.utcnow())
    today_start = datetime(today.year, today.month, today.day, tzinfo=today.tzinfo)
    yesterday_orders_count = len([o for o in all_orders if yesterday_start <= date.convert_utc_to_asia_tz(o.confirmation_date) <= yesterday_end])
    today_orders_count = len([o for o in all_orders if today_start <= date.convert_utc_to_asia_tz(o.confirmation_date) <= today])
    return yesterday_orders_count, today_orders_count


def get_yesterday_orders():
    all_orders = get_all_confirmed_orders()
    yesterday = date.convert_utc_to_asia_tz(datetime.utcnow() - timedelta(days=1))
    yesterday_start = datetime(yesterday.year, yesterday.month, yesterday.day, tzinfo=yesterday.tzinfo)
    yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59, tzinfo=yesterday.tzinfo)
    yesterday_orders = [o for o in all_orders if yesterday_start <= date.convert_utc_to_asia_tz(o.confirmation_date) <= yesterday_end]
    return yesterday_orders


def get_all_confirmed_orders() -> List[Order]:
    return Order.query.filter(Order.confirmed == True).order_by(Order.confirmation_date.desc()).all()


def get_order_by_id(order_id) -> Order:
    return Order.query.get_or_404(order_id)


def get_all_order_locations() -> List[Location]:
    orders = get_all_confirmed_orders()
    return [order.location for order in orders if order.location]


def make_an_order(user_id: int):
    """
    Make a new empty order if doesn't exist in user's orders
    :param user_id: User's Telegram-ID
    :return: void
    """
    user = userservice.get_user_by_telegram_id(user_id)
    current_order = get_current_order_by_user(user_id)
    if not current_order:
        new_order = Order()
        new_order.fill_from_user_cart(user.cart.all())
        user.orders.append(new_order)
        db.session.add(new_order)
    else:
        current_order.fill_from_user_cart(user.cart.all())
        current_order.payment_method = None
        current_order.address_txt = None
        if current_order.location:
            db.session.delete(current_order.location)
        current_order.shipping_method = None
        current_order.delivery_price = None
    db.session.commit()


def set_shipping_method(user_id: int, shipping_method: str):
    """
    Set shipping method to user's current order
    :param user_id: User's Telegram-ID
    :param shipping_method: String value of shipping method (Order.ShippingMethods is recommended to use)
    :return: void
    """
    current_order = get_current_order_by_user(user_id)
    current_order.shipping_method = shipping_method
    db.session.commit()


def set_payment_method(user_id: int, payment_method: str):
    """
    Set payment method to user's current order
    :param user_id: User's Telegram-ID
    :param payment_method: String value of payment method (Order.PaymentMethods is recommended to use)
    :return: void
    """
    current_order = get_current_order_by_user(user_id)
    current_order.payment_method = payment_method
    db.session.commit()


def set_address_by_string(user_id: int, address: str):
    """
    Set address by user's address string
    :param user_id: Telegram-ID
    :param address: String value of address
    :return: void
    """
    current_order = get_current_order_by_user(user_id)
    current_order.address_txt = address
    db.session.commit()


def get_delivery_price_by_distance(distance):
    dis = distance[0]
    delivery_price = settings.get_delivery_cost()
    delivery_price_limit = settings.get_limit_delivery_price()
    delivery_price_km = settings.get_limit_delivery_km()
    if dis <= 3.0:
        delivery_cost = delivery_price[0]
        return round(delivery_cost, 1)

    elif dis > 3.0 and dis <= delivery_price_km:
        delivery_cost = (dis - 3) * delivery_price[1] + delivery_price[0]
        return round(delivery_cost, 1)

    else:
        delivery_cost = (dis * delivery_price[1]) + ((dis - delivery_price_km) * delivery_price_limit)
        return round(delivery_cost, 1)


def set_address_by_map_location(user_id: int, map_location: tuple) -> bool:
    """
    Set address by location sent by user
    :param user_id: User's Telegram-ID
    :param map_location: tuple of latitude and longitude
    :return: void
    """
    latitude = map_location[0]
    longitude = map_location[1]
    address = geocode.get_address_by_coordinates(map_location)
    if not address:
        return False
    current_order = get_current_order_by_user(user_id)
    order_location = Location(latitude=latitude, longitude=longitude, address=address)
    distance = geocode.distance_between_two_points(map_location, settings.get_cafe_coordinates())
    current_order.location = order_location
    current_order.distance = str(distance[0]) + str(distance[1])
    current_order.delivery_price = get_delivery_price_by_distance(distance)
    db.session.commit()
    return True


def set_phone_number(user_id: int, phone_number: str) -> Order:
    current_order = get_current_order_by_user(user_id)
    current_order.phone_number = phone_number
    userservice.set_user_phone_number(user_id, phone_number)
    db.session.commit()
    return current_order


def confirm_order(user_id: int, user_name, total_amount: float):
    """
    Confirm order and let him show on admin panel
    :param user_id: User's Telegram-ID
    :return: void
    """
    current_order = get_current_order_by_user(user_id)
    current_order.created_at = datetime.utcnow()
    current_order.confirmed = True
    current_order.confirmation_date = datetime.utcnow()
    current_order.user_name = user_name
    if current_order.delivery_price:
        current_order.total_amount = current_order.delivery_price + total_amount 
    else:
        current_order.total_amount = total_amount 
    reduce_dish_count(user_id)
    userservice.clear_user_cart(user_id)
    db.session.commit()
    return current_order


def reduce_dish_count(user_id):
    cart = userservice.get_user_cart(user_id)
    for cart_item in cart:
        dish_in_cart = Dish.query.get(cart_item.dish.id)
        dish_in_cart.quantity = dish_in_cart.quantity - cart_item.count
    db.session.commit()


def get_user_orders(user_id: int):
    user = userservice.get_user_by_telegram_id(user_id)
    return user.orders.filter(Order.confirmed == True).order_by(
        Order.confirmation_date.desc()).limit(10).all()

