import os
import random
import string
from application.utils import files

from config import Config
from . import bp
from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from .forms import ContactForm, DeliveryPriceForm, CafeLocationForm, FilesForm, TimeSet
import settings as app_settings


@bp.route('/settings', methods=['GET'])
@login_required
def settings():
    delivery_cost_form = DeliveryPriceForm()
    location_form = CafeLocationForm()
    time_form = TimeSet()
    contact_form = ContactForm()
    files_form = FilesForm()
    delivery_cost_form.fill_from_settings()
    location_form.fill_from_settings()
    time_form.fill_from_settings()
    contact_form.fill_from_settings()
    return render_template('admin/settings.html', title='Настройки', area='settings',
                           cost_form=delivery_cost_form,
                           location_form=location_form,
                           time_form=time_form,
                           contact_form=contact_form,
                           files_form=files_form)


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
    else:
        flash('Ошибка в задании времени работы', category='error')
    return redirect(url_for('admin.settings'))


@bp.route('/settings/contacts', methods=['POST'])
@login_required
def set_contacts():
    contact_form = ContactForm()
    if contact_form.validate_on_submit():
        telegram = contact_form.telegram.data
        phone = contact_form.phone.data
        app_settings.set_contacts((telegram, phone))
        flash('Контакты заданы', category='success')
    else:
        flash('Ошибка в задании контактов', category='error')
    return redirect(url_for('admin.settings'))


@bp.route('/settings/location', methods=['POST'])
@login_required
def set_location():
    location_form = CafeLocationForm()
    if location_form.validate_on_submit():
        latitude = location_form.latitude.data
        longitude = location_form.longitude.data
        app_settings.set_cafe_coordinates((latitude, longitude))
        flash('Координаты изменены', category='success')
    else:
        flash('Ошибка в задании координатов', category='error')
    return redirect(url_for('admin.settings'))


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
        app_settings.set_currency_value(int(delivery_cost_form.currency_value.data))
        flash('Стоимость доставки изменена', category='success')
    else:
        flash('Ошибка в задании стоимости доставки', category='error')
    return redirect(url_for('admin.settings'))


def _save_file(file_to_save):
    if file_to_save and file_to_save.filename != '':
        filename = ''.join(random.choice(string.ascii_letters) for _ in range(16)) + '.' +  file_to_save.filename.split('.')[-1]
        file_path = os.path.join(Config.UPLOAD_DIRECTORY, filename)
        files.save_file(file_to_save, file_path, recreate=True)
        print('saving ' + file_to_save.filename + ' to ' + file_path)
        return file_path
    return None


@bp.route('/settings/set-files', methods=['POST'])
@login_required
def set_files():
    files_form = FilesForm()
    if files_form.validate_on_submit():
        tos = _save_file(files_form.tos.data)
        pricelist = _save_file(files_form.pricelist.data)
        app_settings.set_files(tos, pricelist)
        flash('Файлы изменены', category='success')
    else:
        flash('Ошибка в задании файлов', category='error')
    return redirect(url_for('admin.settings'))
