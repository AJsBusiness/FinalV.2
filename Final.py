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
db_name = os.environ["MONGO_DBNAME"]
client = pymongo.MongoClient(connection_string)
db = client[db_name]
collection = db['Items']


    
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

@app.route('/')
def home():
    return render_template('home.html')
    

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
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            #pprint.pprint(vars(github['/email']))
            #pprint.pprint(vars(github['api/2/accounts/profile/']))
            message='You were successfully logged in as ' + session['user_data']['login'] + '.'
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('homeMessage.html', message=message)
    #Change the render
    
@app.route('/googleb4c3aeedcc2dd103.html')
def render_google_verification():
    return render_template('googleb4c3aeedcc2dd103.html')

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']
    
@app.route('/order')
def render_order():
    if 'github_token' in session:
        return render_template('order.html')
    else:
        return render_template('pleaseLog.html')
    
@app.route('/ordered', methods=['get','post'])
def render_ordered():
    food = "none"
    drink = []
    dessert = "none"
    if 'food' in request.form:
        food=request.form.getlist('food')
    if 'drink' in request.form:
        drink=request.form.getlist('drink')
    if 'dessert' in request.form:
        dessert=request.form.getlist('dessert')
    doc = {"Food Iteam/s":food, "Drink/s":drink, "Dessert/s":dessert}
    collection.insert_one(doc)
    return render_template('ordered.html')
    
@app.route('/cart')
def render_cart():
    order=getOrder()
    return render_template('cart.html', order=order)
    
def getOrder():
    docs=""
    for doc in collection.find():
        docs += Markup("<div>" + "Food Iteam/s: " + str(doc["Food Iteam/s"]) + "<br>" + "Drink/s: " + str(doc["Drink/s"]) + "<br>" + "Dessert/s: " + str(doc["Dessert/s"]) + "<form action=\"/delete\" method=\"post\"> <button type=\"submit\" name=\"delete\" value=\""+ str(doc["_id"]) + "\">Delete</button> </form>" + "</div>")
    return docs
    
@app.route("/delete", methods=['post'])
def renderDelete():
    if 'delete' in request.form:
        ID = request.form['delete']
        collection.delete_one({'_id': ObjectId(ID)})
    return redirect(url_for("render_cart"))

if __name__ == '__main__':
    app.run(debug=True)
