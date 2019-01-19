from flask import Flask, render_template, request, redirect, jsonify
from flask import url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup1 import MakeUp, Base, MakeUpItem, User
from flask import session as login_session
import random
import string
from functools import wraps
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "MakeUp Catalog Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///makeupcatalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# create connection with google account
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
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
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
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
    try:
        login_session['username'] = data['name']
    except Exception as e:
        login_session['username'] = 'null name'
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# this function return user information
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# return the user id
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Dog Information

# show all dogs groups
@app.route('/catalog/JSON')
def catalogJSON():
    groupslist = session.query(MakeUp).all()
    return jsonify(groupslist=[r.serialize for r in groupslist])


# show dogs in a specific dogs group
@app.route('/catalog/<int:group_id>/JSON')
def groupsJSON(group_id):
    makeup_groups = session.query(MakeUp).filter_by(id=group_id).one()
    makeup_items = session.query(MakeUpItem).filter_by(makeup_id=group_id)
    return jsonify(MakeUpItem=[i.serialize for i in makeup_items])


# show a specific dog information
@app.route('/catalog/<int:group_id>/<int:mkup_id>/JSON')
def dogJSON(group_id, mkup_id):
    makeup_groups = session.query(MakeUp).filter_by(id=group_id).one()
    makeup_items = session.query(MakeUpItem).filter_by(id=mkup_id).one()
    return jsonify(ItemDetails=[makeup_items.serialize])


# Login Required function, to a void accessing throw direct URL
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function


# Main page
@app.route('/')
@app.route('/catalog')
def showMakeUpCatalog():
    makeup_groups = session.query(MakeUp).order_by(asc(MakeUp.name))
    group_items = session.query(MakeUpItem).order_by(
        MakeUpItem.id.desc()).limit(7)

    if 'username' not in login_session:  # make sure user has logined
        return render_template(
            'publiccatalog.html',
            makeup_groups=makeup_groups,
            group_items=group_items
            )
    else:  # if user logined, able to access create a new item
        return render_template(
            'catalog.html',
            makeup_groups=makeup_groups,
            group_items=group_items
            )


# Create new dog
@app.route('/catalog/new', methods=['GET', 'POST'])
@login_required
def newMakeUp():
    if request.method == 'POST':  # get data from the form
        newMakeUp = MakeUpItem(
            name=request.form['name'],
            description=request.form['description'],
            makeup_id=request.form['group_id'],
            user_id=login_session['user_id'],
            price=request.form['price'])

        session.add(newMakeUp)
        session.commit()
        flash("new makeup Added!")
        return redirect(url_for('showMakeUpCatalog'))
    else:
        return render_template('newMakeUp.html')


# Show dogs for a specific group
@app.route('/catalog/<int:group_id>')
def showCategories(group_id):
    all_groups = session.query(MakeUp).all()
    makeup_group = session.query(MakeUp).filter_by(id=group_id).one()
    makeup_item = session.query(MakeUpItem).filter_by(makeup_id=makeup_group.id)
    return render_template(
        'makeupgroups.html',
        makeup_group=makeup_group,
        makeup_item=makeup_item,
        all_groups=all_groups
        )


# Show the specific dog and its information
@app.route('/catalog/<int:group_id>/<int:mkup_id>')
def showItem(group_id, mkup_id):
    makeup_group = session.query(MakeUp).filter_by(id=group_id).one()
    makeup_item = session.query(MakeUpItem).filter_by(id=mkup_id).one()
    if 'username' not in login_session or \
            makeup_item.user_id != login_session['user_id']:
        # make sure user logined and user is the creator
        return render_template(
            'publicmakeupitem.html', makeup_group=makeup_group, makeup_item=makeup_item)
    else:  # if user is the creator, able to access update and delete the item
        return render_template(
            'makeupitem.html',
            makeup_group=makeup_group,
            makeup_item=makeup_item
            )


# Edit the specific dog information
@app.route('/catalog/<int:group_id>/<int:mkup_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editItem(group_id, mkup_id):
    editedMakeup = session.query(MakeUpItem).filter_by(id=mkup_id).one()
    # make sure user is the creator
    if editedMakeup.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized"\
         "to edit this item. Please create your own item in order to edit.');"\
         "window.location = '/';}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name'] == "":  # if name is empty it will be unchange
            editedMakeup.name = editedMakeup.name
        else:
            editedMakeup.name = request.form['name']
        # if temperament is empty it will be unchange
        if request.form['price'] == "":
            editedMakeup.price = editedMakeup.price
        else:
            editedMakeup.price = request.form['price']

        # if description is empty it will return unchange
        if request.form['description'] == "":
            editedMakeup.description = editedMakeup.description
        else:
            editedMakeup.description = request.form['description']

        # if category is empty it will return unchange
        if request.form['group_id'] == "":
            editedMakeup.makeup_id = editedMakeup.makeup_id
        else:
            editedMakeup.makeup_id = request.form['group_id']

        session.add(editedMakeup)
        session.commit()
        flash("item edited successfully!")
        return redirect(url_for('showItem', group_id=group_id, mkup_id=mkup_id))
    else:
        return render_template(
            'edititem.html',
            group_id=group_id,
            mkup_id=mkup_id,
            editedMakeup=editedMakeup
            )


# Delete a specific dog
@app.route('/catalog/<int:group_id>/<int:mkup_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteItem(group_id, mkup_id):
    if 'username' not in login_session:
        return redirect('/login')
    makeup_group = session.query(MakeUp).filter_by(id=group_id).one()
    itemToDelete = session.query(MakeUpItem).filter_by(id=mkup_id).one()
    # make sure user is the creator
    if itemToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized "\
         "to delete this item. Please create your own item in order to delete"\
         " .');window.location = '/';}</script><body onload='myFunction()''>"

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Item Successfully Deleted!")
        return redirect(url_for('showMakeUpCatalog', group_id=group_id))
    else:
        return render_template(
            'deleteitem.html',
            group_id=group_id,
            mkup_id=mkup_id,
            item=itemToDelete
            )


# Disconnect from login session
@app.route('/disconnect')
def disconnect():
    if 'username' in login_session:
        gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showMakeUpCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showMakeUpCatalog'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
