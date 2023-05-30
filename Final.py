import pymongo
import os
import sys
import pprint
from flask import Flask, redirect, Markup, url_for, session, request, jsonify
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
    return render_template('home.html')
    
@app.route('/order')
def render_order():
    if 'github_token' in session:
        menu = getMenu("Food")
        menu2 = getMenu("Drink")
        menu3 = getMenu("Dessert")
        return render_template('order.html', menu=menu, menu2=menu2, menu3=menu3)
    else:
        return render_template('pleaseLog.html')
        
        
def getMenu(menu):
    m=""
    for doc in collection2.find( {menu:{"$gt":""}}):
        m += Markup('<div>' + str(doc[menu]) + "<br>" + str(doc["Price"]) + "<form action=\"/ordered\" method=\"POST\"> <input type=\"checkbox\" value=\"" + str(doc["_id"]) + '" name="' + menu + '"></div>')
    return m

    
    
@app.route('/ordered', methods=['GET','POST'])
def render_ordered():
    food = "none"
    drink = "none"
    dessert = "none"
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
        newvalues = { '$push': {'Food/s': food}, '$push': {'Drink/s': drink}, '$push': {'Dessert/s': dessert}}
        collection1.update_one(filters, newvalues)
    return render_template('ordered.html')
    
@app.route('/cart')
def render_cart():
    order=getOrder()
    return render_template('cart.html', order=order)
    
def getOrder():
    items=""
    for food in collection1.find_one()["Food/s"]:
        f = collection2.find_one({"_id": ObjectId(food)})
    for drink in collection1.find_one()["Drink/s"]:
        d = collection2.find_one({"_id": ObjectId(drink)})
    for dessert in collection1.find_one()["Dessert/s"]:
        ds = collection2.find_one({"_id": ObjectId(dessert)})
    items += Markup('<div>' + "Food/s: " + f['Food'] + "<br>" + "Drink/s: " + d['Drink'] + "<br>" + "Dessert/s: " + ds['Dessert'] +"<form action=\"/delete\" method=\"post\"> <button type=\"submit\" name=\"delete\" value=\"" + str(f["Food"]) + str(d["Drink"]) + str(ds["Dessert"]) + "\">Delete</button> </form>" + "</div>")
    return items
    
@app.route("/delete", methods=['POST'])
def renderDelete():
    if 'delete' in request.form:
        ID = request.form['delete']
        collection1.delete_one({'_id': ObjectId(ID)})
    return redirect(url_for("render_cart"))

if __name__ == '__main__':
    app.run(debug=True)
