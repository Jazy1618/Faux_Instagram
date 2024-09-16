from flask import Flask, render_template, request, session, redirect, url_for, send_file
import pymysql.cursors 
import hashlib
import os
from random import randint
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'test'

conn = pymysql.connect(host='localhost',user='root',password='root',db='finsta2',charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor, port=8889)

SALT = 'cs3083'
IMAGES_DIR = os.path.join(os.getcwd(), "static")

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/login', methods=["GET"])
def login():
    return render_template('login.html')

@app.route('/register', methods=["GET"])
def register():
    return render_template('register.html')


@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query,(username,hashed_password))
    data = cursor.fetchone()
    cursor.close()
    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or username'
        return render_template('login.html', error = error)

@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    username = request.form['username']
    password = request.form['password'] + SALT
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    first_name = request.form['firstName']
    last_name = request.form['lastName']
    bio = request.form['bio']
    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query,(username,hashed_password))
    data = cursor.fetchone()
    if(data):
        error = "A user already exists with that name"
        cursor.close()
        return render_template('login.html',error=error)
    else:
        ins ='INSERT INTO Person VALUES(%s, %s, %s, %s, %s)'
        cursor.execute(ins,(username,hashed_password,first_name,last_name,bio))
        conn.commit()
        cursor.close()
        return render_template('home.html',username = username)

#Nathan
@app.route("/post", methods=["POST"])
def post():
        user = session['username']
        today = date.today()
        cursor = conn.cursor()
        photoID = randint(0000000000, 2147483647)
        curr_ids = 'SELECT photoID FROM Photo'
        cursor.execute(curr_ids)
        ids = cursor.fetchall()
        while photoID in ids:
            photoID = randint(0000000000, 2147483647)
        cursor.close()
        imageFile = request.files.get("file", "")
        imageName = imageFile.filename
        filepath = os.path.join(IMAGES_DIR, imageName)
        imageFile.save(filepath)
        caption = request.form['caption']
        try:
            allFollowers = request.form['allFollowers']
        except:
            allFollowers = 0
        photoPoster = request.form['username']
        query = "INSERT INTO Photo (postingdate,filePath,photoID,caption,allFollowers,photoPoster) VALUES (%s, %s,%s,%s,%s,%s)"
        cursor = conn.cursor()
        cursor.execute(query,(today.strftime('%Y-%m-%d'),imageName,photoID,caption,allFollowers,photoPoster))
        conn.commit()
        message = "Image has been successfully uploaded."
        cursor.close()
        username = session['username']
        cursor = conn.cursor();
        query = 'SELECT groupName FROM Friendgroup WHERE groupOwner=%s'
        cursor.execute(query,(username))
        data = cursor.fetchall()
        cursor.close()
        return render_template('home.html', username=username, groups=data)

#1 - visible photos
@app.route("/view", methods=["GET"])
def view():
        username = session['username']
        cursor = conn.cursor()
        query = "SELECT DISTINCT photoID, photoPoster,filepath, postingdate FROM Photo WHERE (photoPoster= %s) OR (photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s AND followstatus=1) AND allFollowers=1) OR (photoID IN (SELECT photoID FROM BelongTo JOIN SharedWith USING(groupName) WHERE %s = member_username OR %s = owner_username))"
        cursor.execute(query,(username, username, username, username))
        data = cursor.fetchall()
        for d in data:
            d['filepath']=url_for('static',filename=d['filepath'])
            cursorName = conn.cursor()
            posterName = "SELECT firstName, lastName FROM `photo` INNER JOIN `person` ON photo.photoPoster = person.username WHERE photoID = %s"
            cursorName.execute(posterName, (d['photoID']))
            myName = cursorName.fetchone()
            d['name'] = myName['firstName'] + ' ' + myName['lastName']
            print("Name: ", d['name'])
            print(username, d['photoID'], d['photoPoster'])
            cursorName.close()
            cursorDate = conn.cursor()
            print("Post time: ", d['postingdate'])
            cursorTags = conn.cursor()
            postTaggee = "SELECT person.username AS 'username', firstName, lastName FROM `person` JOIN `tagged` ON person.username = tagged.username WHERE tagged.tagstatus = 1 AND tagged.photoID = %s"
            cursorTags.execute(postTaggee, (d['photoID']))
            d['tags'] = cursorTags.fetchall()
            print("Tags: ", d['tags'])
            cursorTags.close()
            #username of people who liked photo and the given rating
            cursorLikes = conn.cursor()
            ratings = "SELECT username, rating FROM `likes` WHERE photoID = %s"
            cursorLikes.execute(ratings, (d['photoID']))
            d['likes'] = cursorLikes.fetchall()
            print("Likes: ", d['likes'])
            cursorLikes.close()
        conn.commit()
        cursor.close()


        #return render_template('view.html', username=username, images=data, name=name, date=date, tags=tags, likes=likes)
        return render_template('view.html', images=data)

#Raina Kim
@app.route('/search_bar_tag', methods=["GET"])
def search_bar_tag():
    return render_template('search_bar_tag.html')

#Raina Kim
@app.route("/search_tag", methods=['GET','POST'])
def search_tag():
    username = session['username']
    tagged = request.form['search']
    cursor = conn.cursor()
    error = False
    if tagged is ' ':
        error = True
        return render_template('search_tag.html', err=error)
    query = "SELECT * FROM(SELECT * FROM (SELECT DISTINCT * FROM Photo WHERE (photoPoster= %s) OR (photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s AND followstatus=1) AND allFollowers=1) OR (photoID IN (SELECT photoID FROM BelongTo JOIN SharedWith USING(groupName) WHERE %s = member_username OR %s = owner_username)) AND allFollowers=0) AS t1 JOIN Tagged AS t2 USING(photoID)) AS t3 HAVING username=%s AND tagstatus=1"
    cursor.execute(query,(username,username,username,username,tagged))
    data = cursor.fetchall()
    if data == ():
        error = True
        return render_template('search_tag.html', err=error)
    for d in data:
        d['filepath'] = url_for('static', filename=d['filepath'])
    conn.commit()
    cursor.close()
    return render_template('search_tag.html', username=username, images=data, err=error)


#Raina Kim
@app.route('/search_bar_poster', methods=["GET"])
def search_bar_poster():
    return render_template('search_bar_poster.html')

#Raina Kim
@app.route("/search_poster", methods=['GET','POST'])
def search_poster():
    username = session['username']
    poster = request.form['search']
    cursor = conn.cursor()
    error = False
    if poster is ' ':
        error = True
        return render_template('search_poster.html', err=error)
    query = "SELECT * FROM (SELECT DISTINCT * FROM Photo WHERE (photoPoster= %s) OR (photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s AND followstatus=1) AND allFollowers=1) OR (photoID IN (SELECT photoID FROM BelongTo JOIN SharedWith USING(groupName) WHERE %s = member_username OR %s = owner_username)) AND allFollowers=0) AS t1 HAVING photoPoster=%s"
    cursor.execute(query,(username,username,username,username,poster))
    data = cursor.fetchall()
    if data == ():
        error = True
        return render_template('search_poster.html', err=error)
    for d in data:
        d['filepath'] = url_for('static', filename=d['filepath'])
    conn.commit()
    cursor.close()
    return render_template('search_poster.html', username=username, images=data)

#Nathan
@app.route("/addFriendGroup", methods=["POST","GET"])
def addFriendGroup():
    groupOwner = session['username']
    groupName = request.form['groupName']
    query = 'SELECT groupName FROM Friendgroup WHERE groupOwner=%s'
    cursor = conn.cursor()
    cursor.execute(query,(groupOwner))
    data = cursor.fetchall()
    err = False
    for d in data:
        if d['groupName'] == groupName:
            err = True
    if(not err):
        groupOwner = session['username']
        groupName = request.form['groupName']
        description = request.form['description']
        query = 'INSERT INTO Friendgroup (groupOwner,groupName,description) VALUES(%s,%s,%s)'
        cursor = conn.cursor()
        cursor.execute(query,(groupOwner,groupName,description))
        conn.commit()
        cursor.close()
        cursor = conn.cursor();
        username = session['username']
        query = 'SELECT groupName FROM Friendgroup WHERE groupOwner=%s'
        cursor.execute(query,(username))
        data = cursor.fetchall()
        cursor.close()
        return render_template('home.html', username=username, groups=data,groupErr = err  )
    else:
        cursor = conn.cursor();
        username = session['username']
        query = 'SELECT groupName FROM Friendgroup WHERE groupOwner=%s'
        cursor.execute(query,(username))
        data = cursor.fetchall()
        cursor.close()
        return render_template('home.html', username=username, groups=data,groupErr= err )

#Nathan
@app.route("/removeFriendGroup", methods=["POST","GET"])
def removeFriendGroup():
    groupOwner = session['username']
    groupName = request.form['groupname']
    query = 'SELECT groupName FROM Friendgroup WHERE groupOwner=%s'
    cursor = conn.cursor()
    cursor.execute(query,(groupOwner))
    data = cursor.fetchall()
    err = True
    for d in data:
        if d['groupName'] == groupName:
            err = False
    if(not err):
        groupOwner = session['username']
        groupName = request.form['groupname']
        query = 'DELETE FROM `Friendgroup` WHERE groupOwner = %s AND groupName = %s;'
        cursor = conn.cursor()
        cursor.execute(query,(groupOwner,groupName))
        conn.commit()
        cursor.close()
        groupOwner = session['username']
        groupName = request.form['groupname']
        query = 'DELETE FROM `BelongTo` WHERE owner_username = %s AND groupName = %s;'
        cursor = conn.cursor()
        cursor.execute(query,(groupOwner,groupName))
        conn.commit()
        cursor.close()
        cursor = conn.cursor();
        username = session['username']
        query = 'SELECT groupName FROM Friendgroup WHERE groupOwner=%s'
        cursor.execute(query,(username))
        data = cursor.fetchall()
        cursor.close()
        return render_template('home.html', username=username, groups=data, removeErr = err)
    else:
        cursor = conn.cursor();
        username = session['username']
        query = 'SELECT groupName FROM Friendgroup WHERE groupOwner=%s'
        cursor.execute(query,(username))
        data = cursor.fetchall()
        cursor.close()
        return render_template('home.html', username=username, groups=data,removeErr= err )

#4 - Manage Follows
#Jasmine Amani Murphy
@app.route("/following", methods=["GET"])
def following():
    #4a.i - Find requested user if username exists
    cursor = conn.cursor()
    user =  request.args.get('search')
    validQuery = 'SELECT username, firstName, lastName FROM `person` WHERE username = %s'
    searchResults = []
    if (user):
        cursor.execute(validQuery, (user))
        searchResults = cursor.fetchall()
    length1 = len(searchResults)
    cursor.close()
    #4b.i - Load requests to follow signed in user
    cursor = conn.cursor()
    followRequests = "SELECT username_follower AS 'username', firstName, lastName FROM `follow` JOIN `person` ON follow.username_follower = person.username WHERE followstatus = 0 AND username_followed = %s"
    cursor.execute(followRequests, (session['username']))
    pendingFollowers = cursor.fetchall()
    length2 = len(pendingFollowers)
    cursor.close()
    #4c - Load current followers
    cursor = conn.cursor()
    print("Cursor is ready")
    followedBy = "SELECT username_follower AS 'username' FROM `follow` WHERE followstatus = 1 AND username_followed = %s"
    print("Query is ready")
    cursor.execute(followedBy, (session['username']))
    print("Query executed")
    currentFollowers = cursor.fetchall()
    print("Current Followers: ", currentFollowers)
    length3 = len(currentFollowers)
    cursor.close()
    #4d - Load who you currently follow
    cursor = conn.cursor()
    print("Cursor is ready")
    followedBy = "SELECT username_followed AS 'username' FROM `follow` WHERE followstatus = 1 AND username_follower = %s"
    print("Query is ready")
    cursor.execute(followedBy, (session['username']))
    print("Query executed")
    iFollow = cursor.fetchall()
    print("I follow: ", iFollow)
    length4 = len(iFollow)
    cursor.close()
    return render_template('following.html', searchResults=searchResults, pendingFollowers=pendingFollowers, currentFollowers=currentFollowers, iFollow=iFollow, length1=length1, length2=length2, length3=length3, length4=length4) #, results=results), length=len(results)

#4a.ii - Send new follow request to Follow table
@app.route("/requestsent", methods=["POST"])
def requestToFollow():
    username = session['username']
    cursor = conn.cursor()
    followee = request.form['followMe']
    #check that user is not trying to follow themself
    if (username == followee):
        #error message for user trying to follow themselves
        error = "You can not follow yourself"
        cursor.close()
        return redirect(url_for('following', error=error))
    else:
        #check that request does not conflict with an existing table entry
        checkDuplicate = 'SELECT username_followed, username_follower FROM `follow` WHERE username_followed = %s AND username_follower = %s'
        cursor.execute(checkDuplicate, (followee, session['username']))
        duplicate = cursor.fetchall()
        if (duplicate):
            #error message for duplicate request
            error = "You have already requested to follow this user"
            cursor.close()
            return redirect(url_for('following', error=error))
        else:
            #confirmation of request being sent
            followRequest = "INSERT INTO `follow` VALUES (%s, %s, 0)"
            cursor.execute(followRequest, (followee, session['username']))
            success = "Follow request has been successfully sent"
            conn.commit()
            cursor.close()
            return redirect(url_for('following', success=success))

#4b.ii - Accept/Decline follow request
@app.route("/acceptDecline", methods=["POST"])
def acceptDecline():
    username = session['username']
    cursor = conn.cursor()
    requestAction = request.form['requestAction']
    followName = request.form['followName']
    if (requestAction == "1"):
        #request accepted, followstatus is updated to 1
        query = "UPDATE `follow` SET followstatus = 1 WHERE username_followed = %s AND username_follower = %s"
        cursor.execute(query, (username, followName))
        conn.commit()
        accept = 'User ' + followName + ' is now following you'
        cursor.close()
        return redirect(url_for('following', accept=accept))
    else:
        #request declined, tuple deleted from table
        query = "DELETE FROM `follow` WHERE username_followed = %s AND username_follower = %s"
        cursor.execute(query, (username, followName))
        conn.commit()
        decline = 'User ' + followName + ' is not following you'
        cursor.close()
        return redirect(url_for('following', decline=decline))

#8 - Like a photo
#Jasmine Amani Murphy
@app.route("/like", methods=["POST"])
def likePhoto():
    cursor = conn.cursor()
    likeTime = datetime.now()
    user = session['username']
    rating = request.form['rating']
    likedID = request.form['likedID']
    #make sure user entered a rating
    if (rating):
        #check that request does not conflict with an existing table entry
        checkDuplicate = 'SELECT * FROM `likes` WHERE username = %s AND photoID = %s'
        cursor.execute(checkDuplicate, (session['username'], likedID))
        duplicate = cursor.fetchall()
        if (duplicate):
            #error message if they already liked/rated the photo
            error = "You have already liked and rated this photo"
            cursor.close()
            return redirect(url_for('view', error=error))
        else:
            #enter tuple in Likes table
            query = "INSERT INTO `likes` VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (user, likedID, likeTime, rating))
            conn.commit()
            cursor.close()
            return redirect(url_for('view'))
    else:
        error = "Please enter a rating to like a photo"
        cursor.close()
        return redirect(url_for('view', error=error))


@app.route('/home')
def home():
   username = session['username']
   cursor = conn.cursor();
   query = 'SELECT groupName FROM Friendgroup WHERE groupOwner=%s'
   cursor.execute(query,(username))
   data = cursor.fetchall()
   cursor.close()
   return render_template('home.html', username=username, groups=data)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')
