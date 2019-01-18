from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

app = Flask(__name__)


engine = create_engine('postgresql://vagrant:123@localhost:5432/catalog')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
def HelloWorld():
    categories = session.query(Category)
    items = session.query(
        Item, Category
    ).join(Category).order_by(Item.update_at.desc())
    return render_template('main.html', categories=categories, items=items)


@app.route('/categories/<int:category_id>/')
def categoryItems(category_id):
    categories = session.query(Category)
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category.id)
    return render_template(
        'category_items.html',
        categories=categories,
        category=category,
        items=items)


@app.route('/items/<int:category_id>/<int:item_id>/')
def item(item_id, category_id):
    item = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    return render_template('item.html', item=item, category=category)


@app.route('/item/<int:category_id>/new/', methods=['GET', 'POST'])
def newitem(category_id):
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=category_id
        )
        session.add(newItem)
        session.commit()
        return redirect(url_for('categoryItems', category_id=category_id))
    else:
        categories = session.query(Category).all()
        return render_template('newitem.html',
                               categories=categories,
                               category_id=category_id)


@app.route('/categories/<int:category_id>/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('categoryItems', category_id=category_id))
    else:
        return render_template('deleteconfirmation.html', item=itemToDelete)


@app.route('/categories/<int:category_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name'] or request.form['description']:
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            session.add(editedItem)
            session.commit()
            return redirect(url_for('categoryItems', category_id=category_id))
    else:
        return render_template(
            'edititem.html',
            category_id=category_id,
            item_id=item_id,
            item=editedItem
        )


@app.route('/catalog.json')
def categoryItemsJSON():
    categories_dic = {"Category": []}
    categories = session.query(Category).all()
    for category in categories:
        items = session.query(Item).filter_by(
            category_id=category.id
        ).all()
        category_dic = category.serialize
        category_dic['itmes'] = [i.serialize for i in items]
        categories_dic["Category"].append(category_dic)

    return jsonify(categories_dic)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
