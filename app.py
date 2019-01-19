from flask import Flask, render_template, request, redirect, url_for, \
    jsonify, session as login_session, send_from_directory, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import random
import string

app = Flask(__name__)
CLIENT_ID = json.loads(
        open('client_secrets.json', 'r').read()
)['web']['client_id']
APPLICATION_NAME = "Application"


engine = create_engine('postgresql://vagrant:123@localhost:5432/catalog')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/')
def main():
    categories = session.query(Category)
    items = session.query(
        Item, Category
    ).join(Category).order_by(Item.update_at.desc())
    return render_template('main.html',
                           categories=categories,
                           items=items,
                           login_session=login_session)


@app.route('/categories/<int:category_id>/')
def categoryItems(category_id):
    categories = session.query(Category)
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category.id)
    if 'username' not in login_session:
        return render_template(
            'category_items_without_login.html',
            login_session=login_session,
            categories=categories,
            category=category,
            items=items)
    else:
        return render_template(
            'category_items.html',
            login_session=login_session,
            categories=categories,
            category=category,
            items=items)


@app.route('/items/<int:category_id>/<int:item_id>/')
def item(item_id, category_id):
    item = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=category_id).one()
    if 'username' not in login_session:
        return render_template('item_without_login.html',
                               item=item,
                               category=category,
                               login_session=login_session)
    else:
        return render_template('item.html',
                               item=item,
                               category=category,
                               login_session=login_session)


@app.route('/item/<int:category_id>/new/', methods=['GET', 'POST'])
def newitem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
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
                               category_id=category_id,
                               login_session=login_session)


@app.route('/categories/<int:category_id>/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('categoryItems', category_id=category_id))
    else:
        return render_template('deleteconfirmation.html',
                               item=itemToDelete,
                               login_session=login_session)


@app.route('/categories/<int:category_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
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
            item=editedItem,
            login_session=login_session
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


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401
        )
        response.headers['Content-Type'] = 'application/json'
        return response
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401
        )
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;\
    border-radius: 150px;-webkit-border-radius: 150px;\
    -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'\
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect(url_for('main'))
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
