from . import bp
from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from .forms import DeliveryPriceForm, CafeLocationForm, TimeSet
import settings as app_settings


@bp.route('/settings', methods=['GET'])
@login_required
def settings():
    delivery_cost_form = DeliveryPriceForm()
    location_form = CafeLocationForm()
    time_form = TimeSet()
    delivery_cost_form.fill_from_settings()
    location_form.fill_from_settings()
    time_form.fill_from_settings()
    return render_template('admin/settings.html', title='Настройки', area='settings',
                           cost_form=delivery_cost_form,
                           location_form=location_form,
                           time_form=time_form)


@bp.route('/settings/time', methods=['POST'])
@login_required
def set_times():
    time_form = TimeSet()
    if time_form.validate_on_submit():
        start = time_form.start.data
        end = time_form.end.data
        notify = time_form.notification.data
        app_settings.set_timelimits((start, end))
        app_settings.set_timenotify(notify)
        flash('Задано время работы', category='success')
        return redirect(url_for('admin.settings'))
    delivery_cost_form = DeliveryPriceForm()
    location_form = CafeLocationForm()
    delivery_cost_form.fill_from_settings()
    location_form.fill_from_settings()
    return render_template('admin/settings.html', title='Настройки', area='settings',
                           cost_form=delivery_cost_form,
                           location_form=location_form,
                           time_form=time_form)


@bp.route('/settings/location', methods=['POST'])
@login_required
def set_location():
    location_form = CafeLocationForm()
    if location_form.validate_on_submit():
        latitude = location_form.latitude.data
        longitude = location_form.longitude.data
        app_settings.set_cafe_coordinates((latitude, longitude))
        flash('Координаты изменены', category='success')
        return redirect(url_for('admin.settings'))
    delivery_cost_form = DeliveryPriceForm()
    delivery_cost_form.fill_from_settings()
    time_form = TimeSet()
    time_form.fill_from_settings()
    return render_template('admin/settings.html', title='Настройки', area='settings',
                           cost_form=delivery_cost_form,
                           location_form=location_form,
                           time_form=time_form)


@bp.route('/settings/delivery-cost', methods=['POST'])
@login_required
def set_delivery_cost():
    delivery_cost_form = DeliveryPriceForm()
    if delivery_cost_form.validate_on_submit():
        first_3_km = int(delivery_cost_form.first_3_km.data)
        others_km = int(delivery_cost_form.others_km.data)
        app_settings.set_delivery_cost((first_3_km, others_km))
        limit_km = int(delivery_cost_form.limit_km.data)
        app_settings.set_limit_delivery_km(limit_km)
        limit_delivery_price = int(delivery_cost_form.limit_price.data)
        app_settings.set_limit_delivery_price(limit_delivery_price)
        app_settings.set_currency_value(int(delivery_cost_form.currency_value.data))
        flash('Стоимость доставки изменена', category='success')
        return redirect(url_for('admin.settings'))
    location_form = CafeLocationForm()
    location_form.fill_from_settings()
    time_form = TimeSet()
    time_form.fill_from_settings()
    return render_template('admin/settings.html', title='Настройки', area='settings',
                           cost_form=delivery_cost_form,
                           location_form=location_form,
                           time_form=time_form)
        
