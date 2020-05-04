#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import dbBlob
import os 

SALT = '0123password' 
#Initialize the app from Flask
app = Flask(__name__, static_folder="images")
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

@app.route('/home', methods=['GET'])
def home():
    if 'username' in session:
        user = session['username']
    else:
        error = 'Please login first'
        return render_template('login.html', error=error)
    
    cursor = conn.cursor(); 
    query = 'SELECT firstName, lastName FROM Person WHERE username = %s'
    cursor.execute(query, (user))
    name = cursor.fetchall()
    
    query = '(SELECT DISTINCT Person.firstName, Person.lastName, Photo.postingDate, Photo.pID FROM Photo '\
    'NATURAL JOIN Person NATURAL JOIN Follow WHERE (AllFollowers = 1 AND follower = %s AND '\
    'followee = poster AND followStatus = 1 AND Person.username = Photo.poster) OR '\
    '(Person.username = Photo.poster AND Photo.pID IN (SELECT DISTINCT SharedWith.pID '\
    'FROM FriendGroup NATURAL JOIN SharedWith NATURAL JOIN BelongTo '\
    'WHERE BelongTo.username = %s AND SharedWith.groupName = BelongTo.groupName '\
    'AND SharedWith.groupCreator = BelongTo.groupCreator))) '\
    'UNION '\
    '(SELECT DISTINCT Person.firstName, Person.lastName, Photo.postingDate, Photo.pID '\
    'FROM Person JOIN Photo ON (poster = username) '\
    'WHERE Person.username = %s) '\
    'ORDER BY postingDate DESC'
    cursor.execute(query, (user, user, user))
    photo = cursor.fetchall() 
    
    #query = 'SELECT DISTINCT groupName, groupCreator FROM BelongTo WHERE username = %s'
    #cursor.execute(query, (user))
    #group = cursor.fetchall()

    query = 'SELECT DISTINCT firstName, lastName, follower FROM Follow JOIN Person ON (username=follower) WHERE followee = %s AND followStatus = 0'
    cursor.execute(query, (user))
    follow = cursor.fetchall()
    
    cursor.close()
    return render_template('home.html', user=name, photo=photo, follow=follow)

@app.route('/photo_info', methods=['GET'])
def photo_info():
    if 'username' in session:
        user = session['username']
    else:
        error = 'Please login first'
        return render_template('login.html', error=error)
    
    pID = request.args.get('pID')
    cursor = conn.cursor();
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

@app.route('/share', methods=['GET', 'POST'])
def share():
    if 'username' in session:
        user = session['username']
    else:
        error = 'Please login first'
        return render_template('login.html', error=error)
    
    photo = request.form['photo']
    allFollowers = request.form['allFollowers']
    caption = request.form['caption']
    #groupName = request.form['groupName']
    #groupCreator = request.form['groupCreator']
    pID = dbBlob.insertBLOB(user, photo, allFollowers, caption)
    if(allFollowers == '0'):
        cursor = conn.cursor(); 
        query = 'SELECT DISTINCT groupName, groupCreator FROM BelongTo WHERE username = %s'
        cursor.execute(query, (user))
        group = cursor.fetchall()
        return render_template('friend_group.html', group=group, pID=pID)
    else:
        return redirect(url_for('home'))


@app.route('/follow', methods=['POST'])
def follow():
    if 'username' in session:
        user = session['username']
    else:
        error = 'Please login first'
        return render_template('login.html', error=error)
    
    followee = request.form['followee']
    cursor = conn.cursor();
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (followee))
    data = cursor.fetchone()
    if(data):
        query = 'INSERT INTO Follow (follower, followee, followStatus) VALUES(%s, %s, %s)'
        cursor.execute(query, (user, followee, 0))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))
    else:
        error = 'Incorrect username, go back and try again'
        return render_template('error.html', error=error)

@app.route('/setFollowTrue', methods=['POST'])
def setFollowTrue():
    if 'username' in session:
        user = session['username']
    else:
        error = 'Please login first'
        return render_template('login.html', error=error)
    
    follower = request.form['follower']
    cursor = conn.cursor();
    query = 'UPDATE Follow SET followStatus = 1 WHERE followee = %s AND follower = %s'
    cursor.execute(query, (user, follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/setFollowFalse', methods=['POST'])
def setFollowFalse():
    if 'username' in session:
        user = session['username']
    else:
        error = 'Please login first'  
        return render_template('login.html', error=error)
    
    follower = request.form['follower']
    cursor = conn.cursor();
    query = 'DELETE FROM Follow WHERE followee = %s AND follower = %s'
    cursor.execute(query, (user, follower))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

@app.route('/friendGroup', methods=['POST'])
def friendGroup():
    if 'username' in session:
        user = session['username']
    else:
        error = 'Please login first'
        return render_template('login.html', error=error)
    
    groupName = request.form['groupName']
    cursor = conn.cursor();
    query = 'SELECT * FROM FriendGroup WHERE groupName = %s'
    cursor.execute(query, (groupName))
    data = cursor.fetchone() 
    if(data):
        error = 'You already have a group with this name, go back and try another name.'
        return render_template('error.html', error=error)
    else:
        description = request.form['description']
        query = 'INSERT INTO FriendGroup (groupName, groupCreator, description) VALUES(%s, %s, %s)'
        cursor.execute(query, (groupName, user, description))
        conn.commit()
        query = 'INSERT INTO BelongTo (username, groupName, groupCreator) VALUES(%s, %s, %s)'
        cursor.execute(query, (user, groupName, user))
        conn.commit()
        cursor.close()
        return redirect(url_for('home'))

@app.route('/photo', methods=['GET'])
def photo():
    if 'username' in session:
        user = session['username']
    else:
        error = 'Please login first'
        return render_template('login.html', error=error)
    
    pID = request.args.get('pID') 
    dbBlob.readBLOB(pID, "images/{}.png".format(pID))
    return render_template('photo.html', pID=pID)

@app.route('/friend_group', methods=['POST'])
def friend_group():
    if 'username' in session:
        user = session['username']
    else:
        error = 'Please login first'  
        return render_template('login.html', error=error)
    
    pID = request.form['pID']
    groupCreator = request.form['groupCreator']
    groupName = request.form['groupName']
    cursor = conn.cursor();
    query = 'INSERT INTO SharedWith (pID, groupName, groupCreator) VALUES(%s, %s, %s)'
    cursor.execute(query, (pID, groupName, groupCreator))
    conn.commit() 
    cursor.close() 
    return redirect(url_for('home'))

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
