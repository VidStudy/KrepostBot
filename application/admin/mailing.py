from werkzeug.utils import secure_filename
from config import Config
from application.admin import bp
from flask_login import login_required
from flask import render_template, redirect, url_for, flash, request
from .forms import MailForm
from application import telegram_bot
import telebot
from application.core.models import User
import os
from threading import Thread
from time import sleep


def do_mailing(image, text, preview):
    file_id = None
    if preview:
        users = [583411442, 1294618325]
    else:
        users = User.query.all()
    if image:
        for user in users:
            user_id = user.id if preview is False else user
            if file_id:
                try:
                    telegram_bot.send_photo(chat_id=user_id,
                                            photo=file_id,
                                            caption=text)
                except telebot.apihelper.ApiException:
                    continue
            else:
                try:
                    file = open(image, 'rb')
                    file_id = telegram_bot.send_photo(chat_id=user_id,
                                                      photo=file,
                                                      caption=text).photo[-1].file_id
                    file.close()
                except telebot.apihelper.ApiException:
                    continue
            # 10 message per second
            sleep(1 / 10)
    else:
        for user in users:
            user_id = user.id if preview is False else user
            try:
                telegram_bot.send_message(chat_id=user_id,
                                          text=text)
            except telebot.apihelper.ApiException:
                continue
            # 10 message per second
            sleep(1 / 10)


@bp.route('/mailing', methods=['GET', 'POST'])
@login_required
def mailing():
    mail_form = MailForm()
    if request.method == 'POST':
        file = request.files['image']
        filepath = None
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(Config.MAILING_DIRECTORY, filename))
            filepath = (Config.MAILING_DIRECTORY + filename)
        text = mail_form.mail.data
        preview = mail_form.preview.data
        thread = Thread(target = do_mailing, args = (filepath, text, preview))
        thread.start()
        flash('Рассылка запущена!', category='success')
        return redirect(url_for('admin.mailing'))

    return render_template('admin/mailing.html',
                           title='Рассылка',
                           area='mailing',
                           mail_form=mail_form)
