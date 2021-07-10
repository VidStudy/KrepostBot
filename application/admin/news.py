from application.admin import bp
from flask_login import login_required
from flask import render_template, redirect, url_for, flash, send_from_directory
from .forms import NewsForm
from application.core.models import News
from application import db

import os
from config import Config
from application.utils import files
import random
import string


@bp.route('/news')
@login_required
def news():
    all_news = News.query.all()
    return render_template('admin/news.html', title='Новости', news=all_news, area='news')


@bp.route('/news/image/<path:path>')
def send_news_image(path):
    return send_from_directory(Config.UPLOAD_DIRECTORY, path)


@bp.route('/news/create', methods=['GET', 'POST'])
@login_required
def create_news():
    form = NewsForm()
    if form.validate_on_submit():
        content = form.content.data
        image = form.image.data
        news = News(content=content)

        if image and image.filename != '':
            filename = ''.join(random.choice(string.ascii_letters) for _ in range(16)) + '.' +  image.filename.split('.')[-1]
            file_path = os.path.join(Config.UPLOAD_DIRECTORY, filename)
            files.save_file(image, file_path, recreate=True)
            news.image_path = file_path
        
        db.session.add(news)
        db.session.commit()

        flash('Новость создана', category='success')
        return redirect(url_for('admin.news'))
    return render_template('admin/new_news.html', title='Добавить новость', form=form, area='news')


@bp.route('/news/<int:news_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_news(news_id: int):
    form = NewsForm()
    if form.validate_on_submit():
        content = form.content.data
        image = form.image.data
        news = News.query.get_or_404(news_id)
        news.content = content
        if image and image.filename != '':
            if news.image_path:
                files.remove_file(news.image_path)
            filename = ''.join(random.choice(string.ascii_letters) for _ in range(16)) + '.' +  image.filename.split('.')[-1]
            file_path = os.path.join(Config.UPLOAD_DIRECTORY, filename)
            files.save_file(image, file_path)
            news.image_path = file_path

        db.session.add(news)
        db.session.commit()

        flash('Новость отредактирована', category='success')
        return redirect(url_for('admin.news'))
    news = News.query.get_or_404(news_id)
    form.fill_from_object(news)
    return render_template('admin/edit_news.html', title='Новость ' + str(news.id), form=form, news=news, area='news')


@bp.route('/news/<int:news_id>/remove', methods=['GET'])
@login_required
def remove_news(news_id: int):
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    flash('Новость удалена', category='success')
    return redirect(url_for('admin.news'))

