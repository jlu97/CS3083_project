#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib

SALT = '0123password' 
#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='127.0.0.1',
                       port = 8889,
                       user='root',
                       password='root',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, hashed_password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    email = request.form['email']
    
    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO Person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins, (username, hashed_password, firstName, lastName, email))
        conn.commit()
        cursor.close()
        return render_template('index.html')

@app.route('/home')
def home():
    user = session['username']
    cursor = conn.cursor();
    query = 'SELECT DISTINCT Person.firstName, Person.lastName, Photo.postingDate, Photo.pID FROM Photo '\
    'NATURAL JOIN Person NATURAL JOIN Follow WHERE (AllFollowers = 1 AND follower = %s AND '\
    'followee = poster AND followStatus = 1 AND Person.username = Photo.poster) OR '\
    '(Person.username = Photo.poster AND Photo.pID IN (SELECT DISTINCT SharedWith.pID '\
    'FROM FriendGroup NATURAL JOIN SharedWith NATURAL JOIN BelongTo '\
    'WHERE BelongTo.username = %s AND SharedWith.groupName = BelongTo.groupName '\
    'AND SharedWith.groupCreator = BelongTo.groupCreator)) ORDER BY postingDate DESC'
    cursor.execute(query, (user, user))
    data = cursor.fetchall()
    #query = 'SELECT poster FROM Photo WHERE pID = %s'
    #cursor.execute(query, (data['pID']))
    #data2 = cursor.fetchall()
    cursor.close()
    return render_template('home.html', User=user, photo=data)

@app.route('/photo_info')
def photo_info():
    #user = session['username']
    pID = request.args.get('pID', None)
    cursor = conn.cursor();
    #query = 'CREATE VIEW PhotoView AS (SELECT DISTINCT Person.firstName, Person.lastName, Photo.postingDate, Photo.pID FROM Photo '\
     #   'NATURAL JOIN Person NATURAL JOIN Follow WHERE (AllFollowers = 1 AND follower = %s AND '\
     #   'followee = poster AND followStatus = 1 AND Person.username = Photo.poster) OR '\
     #   '(Person.username = Photo.poster AND Photo.pID IN (SELECT DISTINCT SharedWith.pID '\
     #   'FROM FriendGroup NATURAL JOIN SharedWith NATURAL JOIN BelongTo '\
     #   'WHERE BelongTo.username = %s AND SharedWith.groupName = BelongTo.groupName '\
     #   'AND SharedWith.groupCreator = BelongTo.groupCreator)) ORDER BY postingDate DESC)'
    #cursor.execute(query, (user, user))
    query = 'SELECT Person.username, Person.firstName, Person.lastName '\
            'FROM Person NATURAL JOIN TAG '\
            'WHERE Tag.pID = %s AND Tag.tagStatus = 1'
    cursor.execute(query, pID)
    tagData = cursor.fetchall()
    query = 'SELECT ReactTo.reactionTime, ReactTo.comment, ReactTo.emoji '\
            'FROM ReactTo '\
            'WHERE ReactTo.pID = %s'\
            'ORDER BY reactionTime DESC'
    cursor.execute(query, pID)
    reactionData = cursor.fetchall()
    cursor.close()
    return render_template('photo_info.html', photoID=pID, tag=tagData, reaction=reactionData)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
        
app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
