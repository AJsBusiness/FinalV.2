import pymongo
import os
import sys
import pprint
from flask import Flask, redirect, Markup, url_for, session, request, jsonify, flash
from flask_oauthlib.client import OAuth
from flask import render_template
from bson.objectid import ObjectId


app = Flask(__name__)

app.debug = False #Change this to False for production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Remove once done debugging

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

connection_string = os.environ["MONGO_CONNECTION_STRING"]
db_name1 = os.environ["MONGO_DBNAME1"]
db_name2 = os.environ["MONGO_DBNAME2"]
client = pymongo.MongoClient(connection_string)
db1 = client[db_name1]
db2 = client[db_name2]
collection1 = db1['Items']
collection2 = db2['Prices']


    
#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)


#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}


#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL


@app.route('/logout')
def logout():
    session.clear()
    return render_template('homeMessage.html', message='Logged out successfully!')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        flash('Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args))      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            #pprint.pprint(vars(github['/email']))
            #pprint.pprint(vars(github['api/2/accounts/profile/']))
            flash('You were successfully logged in as ' + session['user_data']['login'] + '.')
        except Exception as inst:
            session.clear()
            print(inst)
            flash('Unable to login, please try again.')
    return redirect('/')
    #Change the render
    
@app.route('/googleb4c3aeedcc2dd103.html')
def render_google_verification():
    return render_template('googleb4c3aeedcc2dd103.html')

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']
    
    
@app.route('/')
def home():
    return render_template('home.html', bckgrnd = "hmepge")
    
@app.route('/order')
def render_order():
    if 'github_token' in session:
        menu = getMenu("Food")
        menu2 = getMenu("Drink")
        menu3 = getMenu("Dessert")
        return render_template('order.html', menu=menu, menu2=menu2, menu3=menu3, bckgrnd = "ordr")
    else:
        return render_template('pleaseLog.html')
        
        
def getMenu(menu):
    m=""
    for doc in collection2.find( {menu:{"$gt":""}}):
        m += Markup('<div>' + str(doc[menu]) + "<br>" + str(doc["Price"]) + "<form action=\"/ordered\" method=\"POST\"> <input class=\"chckbx\" type=\"checkbox\" value=\"" + str(doc["_id"]) + '" name="' + menu + '"></div>')
    return m

    
    
@app.route('/ordered', methods=['GET','POST'])
def render_ordered():
    food = []
    drink = []
    dessert = []
    filters = {"ID": session['user_data']['id']}
    order = collection1.find_one(filters)
    if order == None:
        if 'Food' in request.form:
            food=request.form.getlist('Food')
        if 'Drink' in request.form:
            drink=request.form.getlist('Drink')
        if 'Dessert' in request.form:
            dessert=request.form.getlist('Dessert')
        doc = {"Food/s":food, "Drink/s":drink, "Dessert/s":dessert, "ID": session['user_data']['id']}
        collection1.insert_one(doc)
    else:
        if 'Food' in request.form:
            food=request.form.getlist('Food')
        if 'Drink' in request.form:
            drink=request.form.getlist('Drink')
        if 'Dessert' in request.form:
            dessert=request.form.getlist('Dessert')
        newvalues = {'$push': {'Food/s': {'$each': food}, 'Drink/s': {'$each': drink}, 'Dessert/s': {'$each': dessert}}}
        collection1.update_one(filters, newvalues)
    return render_template('ordered.html')
    
@app.route('/cart')
def render_cart():
    if 'github_token' in session:
        order=getOrder()
        total = getTotal()
        return render_template('cart.html', order=order, total=total, bckgrnd = "ordr")
    else:
        return render_template('pleaseLog.html')
    
def getOrder():
    items=""
    filters = {"ID": session['user_data']['id']}
    menu = collection1.find_one(filters)
    if 'Food/s' in menu:
        for food in menu["Food/s"]:
            f = collection2.find_one({"_id": ObjectId(food)})
            items += Markup('<div>' + "Food/s: " + f['Food'] + "<br>" + "<form action=\"/delete\" method=\"post\"> <button type=\"submit\" name=\"Food/s\" value=\"" + str(f["Food"]) + "\">Delete</button> </form>" + "</div>")
    if 'Drink/s' in menu:            
        for drink in menu["Drink/s"]:
            d = collection2.find_one({"_id": ObjectId(drink)})
            items += Markup('<div>' + "Drink/s: " + d['Drink'] + "<br>" + "<form action=\"/delete\" method=\"post\"> <button type=\"submit\" name=\"Drink/s\" value=\"" + str(d["Drink"]) + "\">Delete</button> </form>" + "</div>")
    if 'Dessert/s' in menu:
        for dessert in menu["Dessert/s"]:
            ds = collection2.find_one({"_id": ObjectId(dessert)})
            items += Markup('<div>' + "Dessert/s: " + ds['Dessert'] +"<form action=\"/delete\" method=\"post\"> <button type=\"submit\" name=\"Dessert/s\" value=\"" + str(ds["Dessert"]) + "\">Delete</button> </form>" + "</div>")
    if items == "":
        items="You must first add things to your cart in  order to view it."
    return items
    
def getTotal():
    total=0
    filters = {"ID": session['user_data']['id']}
    menu = collection1.find_one(filters)
    for food in menu["Food/s"]:
        pf = collection2.find_one({"_id": ObjectId(food)})
        total += pf["Price"]
    for drink in menu["Drink/s"]:
        pd = collection2.find_one({"_id": ObjectId(drink)})
        total += pd["Price"]
    for dessert in menu["Dessert/s"]:
        pde = collection2.find_one({"_id": ObjectId(dessert)})
        total += pde["Price"]
    return total
    
@app.route("/delete", methods=['POST'])
def renderDelete():
    filters = {"ID": session['user_data']['id']}
    menu = collection1.find_one(filters)
    item_type = list(request.form.keys())[0][:-2]
    item_filter = {item_type: list(request.form.values())[0]}
    dis = collection2.find_one(item_filter)
    var = list(request.form.keys())[0]
    deletevalues = {'$pull': {var: str(dis['_id'])}}
    collection1.update_one(filters, deletevalues)
    return redirect(url_for("render_cart"))

if __name__ == '__main__':
    app.run(debug=True)