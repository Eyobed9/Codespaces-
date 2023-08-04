import os
import sqlite3
import cv2

from datetime import datetime
from flask import flash, Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.serving import run_simple
from werkzeug.utils import secure_filename

from helpers import login_required, registration_required


# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Connect to database
conn = sqlite3.connect('hospital.db', check_same_thread=False)
db = conn.cursor()
db.execute("CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY, room_type TEXT, price INTEGER, status TEXT);")
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT, hash TEXT);")
db.execute("CREATE TABLE IF NOT EXISTS info (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, first_name TEXT, last_name TEXT, email TEXT, phone TEXT, age INTEGER, question TEXT, answer TEXT, user_id INTEGER, FOREIGN KEY (user_id) REFERENCES users(id));")
db.execute("CREATE INDEX IF NOT EXISTS username ON users (username);")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Home page"""
    return render_template("homepage.html")


@app.route("/about")
def about():
    """ Return the page that contains the about info """
    return render_template("about.html")


@app.route("/appointment")
@login_required
def appointment():
    """Schedule an appointment"""
    if request.method == "POST":
        return "This is the appointment page"
        # price and payment options
    # else
        # price and payment options
    else:
        return render_template("appointment.html")


@app.route("/card")
@registration_required
def card():
    """ Create a medical card for the user """
    
    # Get the user info from the database
    id = session["user_id"]
    info = db.execute("SELECT first_name, last_name, email, phone, age FROM info WHERE user_id = ?;", (id,)).fetchall()
    
    return render_template("card.html", info=info)

@app.route("/cancer")
def cancer():
    """ Return the page that contains the cancer treatment info """
    return render_template("cancer.html")


@app.route("/devices")
def devices():
    """ Return the page that contains the Medical devices info """
    return render_template("devices.html")


@app.route("/double")
def double():
    """ Return the page that contains the double room info """
    availability = "available"
    cost = 1000
    
    # The following code can be used to insert/update the data into the database if needed
    '''db.execute("INSERT INTO rooms(room_type, price, status) VALUES(?, ?, ?);", ("double", 1000, "available"))
    db.execute("UPDATE rooms SET status = ? WHERE room_type = 'double';", (availability,))
    db.execute("UPDATE rooms SET price = ? WHERE room_type = 'double';", (cost,))
    conn.commit()'''
    
    result = db.execute("SELECT price, status FROM rooms WHERE room_type = 'double';").fetchall()
    price = result[0][0]
    beds = result[0][1]
    return render_template("double.html", beds=beds, price=price)


@app.route("/forgot", methods=["GET", "POST"])
def reset():
    """ Change the password if the user forgot it """
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username")
            return render_template("forgot.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("forgot.html")
        
        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            flash("Must confirm password")
            return render_template("forgot.html")
        
        # Ensure password and confirmation match
        elif request.form.get("password") != request.form.get("confirmation"):
            flash("Passwords must match")
            return render_template("forgot.html")
        
        # Query database for username
        username = request.form.get("username")
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?;", (username,)
        ).fetchall()
        
        # Query database for email, security question, and security answer
        rows = db.execute("SELECT * FROM info WHERE user_id = ?;", (rows[0][0],)).fetchall()
        
        # Ensure username exists and password is correct
        if len(rows) != 1:
            flash("Invalid username")
            return render_template("forgot.html")
        
        # Ensure the security question is correct
        elif request.form.get("question1") != rows[0][6]:
            flash("Invalid question")
            return render_template("forgot.html")
        
        # Ensure the security answer is correct
        elif request.form.get("answer1").capitalize() != rows[0][7]:
            flash("Invalid answer")
            return render_template("forgot.html")
        
        # Ensure the email is correct
        elif request.form.get("email") != rows[0][3]:
            flash("Invalid email")
            return render_template("forgot.html")
        
        # Update the password
        db.execute("UPDATE users SET hash = ? WHERE username = ?;", (generate_password_hash(request.form.get("password")), username,))
        conn.commit()
        
        # Redirect user to login page
        return redirect("/login")
    else:
        return render_template("forgot.html")
        
    
@app.route("/multiple")
def multiple():
    """ Return the page that contains the multiple room info """
    availability = "available"
    cost = 500
    
    # The following code can be used to insert/update the data into the database if needed
    '''db.execute("INSERT INTO rooms(room_type, price, status) VALUES(?, ?, ?);", ("multiple", 500, "available"))
    db.execute("UPDATE rooms SET status = ? WHERE room_type = 'multiple';", (availability,))
    db.execute("UPDATE rooms SET price = ? WHERE room_type = 'multiple';", (cost,))
    conn.commit()'''
    
    result = db.execute("SELECT price, status FROM rooms WHERE room_type = 'multiple';").fetchall()
    price = result[0][0]
    beds = result[0][1]
    return render_template("multiple.html", beds=beds, price=price)
    

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password")
            return render_template("login.html")

        # Query database for username
        username = request.form.get("username")
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?;", (username,)
        ).fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            flash("Invalid username and/or password")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET 
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/physicians")
def physicians():
    """ Return the page that contains the physicians info """
    name = request.args.get('name')
    if name:
        return render_template(name + '.html')
    return render_template("physicians.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    
    # If submitted via Post
    if request.method == "POST":     
        # Get the username from the form
        username = request.form.get("username")
        usernames = db.execute("SELECT username FROM users;").fetchall()
        usernames = [dict(username=row[0]) for row in usernames]

        # Check if the username exists and is not repeated 
        if any(username in d.values() for d in usernames):
            flash("Username already exists")
            return redirect("/register")
        elif not username:
            flash("Must provide a username")
            return redirect("/register")

        # Get password from the form
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check if the passwords match and exist
        if password != confirmation:
            flash("Password doesn't match")
            return redirect("/register")
        elif not password or not confirmation:
            flash("Must provide a password")
            return redirect("/register")
        
        '''# Handle profile picture upload
        profile_picture = request.files.get("profile_picture")
        if profile_picture:
            # Save the uploaded file to a secure location
            filename = secure_filename(profile_picture.filename)
            profile_picture.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            # Store the file path in the database or perform any other necessary operations'''

       
        # Insert the user into users table
        hashed_password = generate_password_hash(password)
        db.execute("BEGIN TRANSACTION;")
        db.execute(
            "INSERT INTO users(username, hash) VALUES(?, ?);", (username, hashed_password)
        )
        db.execute("COMMIT;")
        conn.commit()   
        
        rows = db.execute("SELECT id FROM users WHERE username = ?;", (username,)).fetchall() 
        session["user_id"] = rows[0][0]
        ID = session["user_id"]
    
        # Get the user info from the form
        first_name = request.form.get("first_name").capitalize()
        last_name = request.form.get("last_name").capitalize()
        age = request.form.get("age")
        phone = request.form.get("phone_number")
        email = request.form.get("email")
        question = request.form.get("question1")
        answer = request.form.get("answer1").capitalize()

        # Insert the user info into info table
        db.execute("INSERT INTO info(first_name, last_name, age, phone, email, user_id, question, answer) VALUES(?, ?, ?, ?, ?, ?, ?, ?);", (first_name, last_name, age, phone, email, ID, question, answer))
        db.execute("COMMIT;")
        conn.commit()
        
        # Login the user
        return redirect("/card")

    # If submitted via Get
    else:
        return render_template("register.html")


@app.route("/rooms")
def rooms():
    """ Return the page that contains the rooms info """
    return render_template("rooms.html")


@app.route("/single")
def single():
    """ Return the page that contains the single room info """
    availability = "available"
    cost = 2000
    
    # The following code can be used to insert/update the data into the database if needed
    '''db.execute("INSERT INTO rooms(room_type, price, status) VALUES(?, ?, ?);", ("single", 2000, "available"))
    db.execute("UPDATE rooms SET status = ? WHERE room_type = 'single';", (availability,))
    db.execute("UPDATE rooms SET price = ? WHERE room_type = 'single';", cost)
    conn.commit()'''
    
    result = db.execute("SELECT price, status FROM rooms WHERE room_type = 'single';").fetchall()
    price = result[0][0]
    beds = result[0][1]
    return render_template("single.html", beds=beds, price=price)


@app.route("/services")
def services():
    """ Return the page that contains the services info """
    return render_template("services.html")


@app.route('/capture', methods=['POST'])
def capture():
    # Access the camera
    camera = cv2.VideoCapture(0)
    _, frame = camera.read()

    # Get the username from the database
    rows
    # Save the captured image
    image_path = 'captured_image.jpg'
    cv2.imwrite(image_path, frame)

    # Release the camera
    camera.release()

    return render_template('capture.html', image_path=image_path)


if __name__ == '__main__':
    app.run(debug=True)

conn.commit()
conn.close()