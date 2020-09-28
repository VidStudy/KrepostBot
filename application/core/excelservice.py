import xlrd
from . import dishservice
from application.core.models import DishCategory


def parse_excel_file(path_to_file: str):
    workbook = xlrd.open_workbook(path_to_file)
    worksheet = workbook.sheet_by_index(0)
    for rx in range(worksheet.nrows):
        if rx == 0:
            continue
        row = worksheet.row(rx)
        parent_category = row[0].value
        product_name = row[1].value
        category_1 = row[2].value
        category_2 = row[3].value
        category_3 = row[4].value
        description = row[5].value
        price = row[6].value
        image = row[7].value
        quantity = row[8].value
        category_4 = row[9].value
        _create_product(product_name, parent_category, category_1, category_2, category_3, description, price, image, quantity, category_4)


def _create_category(category4_name, category3_name, category2_name, category1_name, parent_category_name) -> DishCategory:
    parent_category = dishservice.get_category_by_name(parent_category_name, 'ru')
    if not parent_category:
        parent_category = dishservice.create_category(parent_category_name)
    category1 = _get_or_create_category(category1_name, parent_category)
    category2 = _get_or_create_category(category2_name, category1)
    category3 = _get_or_create_category(category3_name, category2)
    category4 = _get_or_create_category(category4_name, category3)
    if category4:
        return category4
    elif category3:
        return category3
    elif category2:
        return category2
    elif category1:
        return category1
    else:
        return parent_category


def _get_or_create_category(category_name, parent_category):
    if not category_name:
        return None
    category = dishservice.get_category_by_name(category_name, 'ru', parent_category)
    if not category:
        category = dishservice.create_category(category_name, parent_category.id)
    return category


def _create_product(product_name, parent_category,
                    category1, category2, category3,
                    product_description, product_price, image, quantity, category4):
    if product_price:
        product_price = float(product_price)
    else:
        product_price = 0.0

    category = _create_category(category4, category3, category2, category1, parent_category)
    _get_or_create_dish(product_name, product_description, str(image), product_price, quantity, category.id)


def _get_or_create_dish(product_name, product_description, image, product_price, quantity, category):
    if not product_name:
        return None
    product = dishservice.get_dish_by_name(product_name, 'ru')
    if not product:
        dishservice.create_dish(product_name, product_description, str(image), product_price, quantity, category)
    return product
