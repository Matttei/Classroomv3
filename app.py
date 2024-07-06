import os
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from cs50 import SQL
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = 'supersecretkey'
Session(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQL("sqlite:///users.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        cofimation = request.form.get("verification")
        if not username or not password:
            flash("Username and password cannot be empty")
            return redirect("/register")
        elif password != cofimation:
            flash("Passwords don't match")
            return redirect("/register")
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) > 0:
            flash("Username already exists")
            return redirect("/register")
        hash = generate_password_hash(password)
        time = datetime.now()
        db.execute("INSERT INTO users (username, hash, timestamp) VALUES (?, ?, ?)", username, hash, time)
        user_id = db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]
        session["user_id"] = user_id
        session["username"] = username
        flash(f"Registered! Welcome, {session.get('username')}")  
        return redirect("/")
    return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Provide the info!")
            return redirect("/login")
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            flash("Invalid username or password")
            return redirect("/login")
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]
        flash(f"Logged in! Welcome back, {session.get('username')}")  
        return redirect("/")
    return render_template("login.html")


@app.route("/todo", methods=["POST", "GET"])
def todo():
    if "user_id" not in session:
        flash("You must be registered to access this feature!")
        return redirect("/")

    if request.method == "POST":
        info = request.form.get("todo")
        if not info:
            flash("Task field is empty :/")
        elif info.isdigit():
            flash("Provide letters not numbers :/")
        else:
            time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_id = session["user_id"]
            
            db.execute("INSERT INTO todolist (user_id, info, timestamp) VALUES (?, ?, ?)", user_id, info, time)

    tasks = db.execute("SELECT * FROM todolist WHERE user_id = ?", session["user_id"])

    return render_template("todo.html", tasks=tasks)


@app.route("/remove_task", methods=["POST"])
def remove_task():
    if "user_id" not in session:
        flash("You must be logged in to access this feature!")
        return redirect("/login")
    task_id = request.form.get("info")
    if not task_id:
        flash("Invalid Request. Please try again ;)")
        return redirect("/todo")
    db.execute("DELETE FROM todolist WHERE id = ?", task_id)

    flash("Task removed succesfully!")
    return redirect("/todo")

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    feedback = request.form.get('feedback')
    if not feedback:
        flash("Please provide the feedback")
        return redirect("/")
    db.execute("INSERT INTO feedback (user_id, feedback) VALUES (?, ?)", 
               session["user_id"], feedback)
    flash("Feedback sent succesfully, thank you")
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out succesfully")
    return redirect("/")


@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    if request.method == "POST":

        subjects = {
            'romana': 0, 'engleza': 0, 'franceza': 0, 'mate': 0, 'fizica': 0,
            'chimie': 0, 'biologie': 0, 'istorie': 0, 'geografie': 0,
            'psihologie': 0, 'religie': 0, 'muzica': 0, 'desen': 0, 'sport': 0,
            'info': 0, 'tic': 0, 'antreprenoriala': 0, 'purtare': 0
        }

        for subject in subjects:
            try:
                value = float(request.form.get(subject, 0))
                if 1 <= value <= 10 and value.is_integer():
                    subjects[subject] = int(value)
            except ValueError:
                subjects[subject] = 0

        suma = sum(subjects.values())
        media = suma / len(subjects)
        media = "{:.3f}".format(media).rstrip('0').rstrip('.')
        media_float = float(media)
        if media_float == 10:
            flash("Felicitari pentru aceasta medie excelenta")
        elif media_float >= 9 and media_float < 10:
            flash("Ai obtinut o medie foarte buna")
        elif media_float >= 6 and media_float < 9:
            flash("Ai obtinut o medie destul de buna")
        elif media_float >= 5 and media_float < 6:
            flash("La limita")
        else:
            flash("Ai ramas repetent")

        return render_template("calculator.html", rezultat=media)

    return render_template("calculator.html")


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)