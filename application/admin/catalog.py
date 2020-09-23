from application.admin import bp
from flask_login import login_required
from flask import render_template, redirect, url_for, flash, request
from application.core import dishservice
from application.core.models import DishCategory, Dish
from application.admin.forms import CategoryForm, DishForm


@bp.route('/catalog', methods=['GET'])
@login_required
def catalog():
    categories = dishservice.get_parent_categories(sort_by_number=True)
    return render_template('admin/catalog.html', title='Каталог', area='catalog', categories=categories)


@login_required
@bp.route('/catalog/<int:category_id>', methods=['GET', 'POST'])
def show_category(category_id: int):
    category = dishservice.get_category_by_id(category_id)
    categories = category.get_children().order_by(DishCategory.number.asc()).all()

    return render_template('admin/category.html', title='{}'.format(category.name),
                           area='catalog', category=category, categories=categories)


@bp.route('/catalog/<int:category_id>/dishes', methods=['GET', 'POST'])
@login_required
def category_dishes(category_id: int):
    category = dishservice.get_category_by_id(category_id)
    dishes = category.dishes.order_by(Dish.number.asc()).all()

    return render_template('admin/category_dishes.html', title='{}'.format(category.name),
                           area='catalog', category=category, dishes=dishes)


@bp.route('/catalog/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id: int):
    form = CategoryForm()
    all_categories = dishservice.get_all_categories()
    form.parent.choices = [(c.id, 'RU: {}'.format(c.get_nested_names())) for c in all_categories]
    form.parent.choices.insert(0, (0, 'Нет'))
    if form.validate_on_submit():
        name_ru = form.name_ru.data
        image = form.image.data
        parent_id = form.parent.data
        dishservice.update_category(category_id, name_ru, parent_id, image)
        flash('Категория {} изменена'.format(name_ru), category='success')
        return redirect(url_for('admin.catalog'))
    category = dishservice.get_category_by_id(category_id)
    form.fill_from_object(category)
    return render_template('admin/edit_category.html',
                           title='{}'.format(category.name),
                           area='catalog', form=form, category=category)


@login_required
@bp.route('/catalog/create', methods=['GET', 'POST'])
def create_category():
    form = CategoryForm()
    all_categories = dishservice.get_all_categories()
    form.parent.choices = [(c.id, 'RU: {}'.format(c.get_nested_names())) for c in all_categories]
    form.parent.choices.insert(0, (0, 'Нет'))
    if form.validate_on_submit():
        name_ru = form.name_ru.data
        image = form.image.data
        parent_id = form.parent.data
        dishservice.create_category(name_ru, parent_id, image)
        flash('Категория {} добавлена'.format(name_ru), category='success')
        return redirect(url_for('admin.catalog'))
    form.parent.data = 0
    return render_template('admin/new_category.html', title='Добавить категорию', area='catalog', form=form)


@login_required
@bp.route('/catalog/<int:category_id>/remove', methods=['GET'])
def remove_category(category_id: int):
    dishservice.remove_category(category_id)
    flash('Категория удалена', category='success')
    return redirect(url_for('admin.catalog'))


@login_required
@bp.route('/catalog/dish/create', methods=['GET', 'POST'])
def create_dish():
    form = DishForm()
    all_categories = dishservice.get_all_categories()
    form.category.choices = [(c.id, 'RU: {}'.format(c.get_nested_names())) for c in all_categories]
    if form.validate_on_submit():
        name = form.name_ru.data
        description = form.description_ru.data
        show_usd = form.show_usd.data
        quantity = form.quantity.data
        image = form.image.data
        price = form.price.data
        category_id = form.category.data
        new_dish = dishservice.create_dish(name=name, description=description, image=image,
                                           price=price, category_id=category_id, quantity=quantity, show_usd=show_usd)
        print(new_dish)
        flash('Блюдо {} успешно добавлено в категорию {}'.format(
            name, new_dish.category.name
        ), category='success')
        return redirect(url_for('admin.catalog'))
    return render_template('admin/new_dish.html', title="Добавить блюдо", area='catalog', form=form)


@login_required
@bp.route('/catalog/dish/<int:dish_id>', methods=['GET', 'POST'])
def dish(dish_id: int):
    form = DishForm()
    all_categories = dishservice.get_all_categories()
    form.category.choices = [(c.id, 'RU: {}'.format(c.get_nested_names())) for c in all_categories]
    if form.validate_on_submit():
        name_ru = form.name_ru.data
        description_ru = form.description_ru.data
        image = form.image.data
        price = form.price.data
        quantity = form.quantity.data
        category_id = form.category.data
        delete_image = form.delete_image.data
        show_usd = form.show_usd.data
        dishservice.update_dish(dish_id, name_ru, description_ru, image, price,
                                category_id, delete_image, show_usd, quantity)
        flash('Блюдо {} изменено'.format(name_ru, category='success'))
        return redirect(url_for('admin.catalog'))
    dish = dishservice.get_dish_by_id(dish_id)
    form.fill_from_object(dish)
    return render_template('admin/dish.html', title='{}'.format(dish.name),
                           area='catalog', form=form, dish=dish)


@login_required
@bp.route('/catalog/dish/<int:dish_id>/remove', methods=['GET'])
def remove_dish(dish_id: int):
    dishservice.remove_dish(dish_id)
    flash('Блюдо удалено', category='success')
    return redirect(url_for('admin.catalog'))


@login_required
@bp.route('/catalog/dish/<int:dish_id>/number', methods=['POST'])
def set_dish_number(dish_id: int):
    number = request.get_json()['number']
    dishservice.set_dish_number(dish_id, number)
    return '', 201


@login_required
@bp.route('/catalog/<int:category_id>/number', methods=['POST'])
def set_category_number(category_id: int):
    number = request.get_json()['number']
    dishservice.set_category_number(category_id, number)
    return '', 201


@bp.route('/catalog/dish/<int:dish_id>/toggle-hide', methods=['GET'])
@login_required
def toggle_hide_dish(dish_id: int):
    result = dishservice.toggle_hidden_dish(dish_id)
    if not result:
        message = 'Блюдо теперь будет показано в меню Telegram-бота'
    else:
        message = 'Блюдо скрыто из меню Telegram-бота!'
    flash(message, category='success')
    return redirect(url_for('admin.catalog'))
