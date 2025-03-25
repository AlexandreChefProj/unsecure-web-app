from flask import Flask, request, render_template, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Weak hardcoded key (vulnerability)

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Create the users table with an is_admin field (SQL injection risk)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        is_admin BOOLEAN DEFAULT 0
    )
    """)

    # Insert the default admin user (admin's is_admin is set to 1)
    cursor.execute("""
    INSERT OR IGNORE INTO users (id, username, password, is_admin) 
    VALUES (1, 'admin', 'password123', 1)
    """)

    cursor.execute("CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT)")
    cursor.execute("INSERT OR IGNORE INTO courses (id, name, description) VALUES (1, 'Cybersecurity 101', 'Introduction to security basics')")
    cursor.execute("INSERT OR IGNORE INTO courses (id, name, description) VALUES (2, 'Ethical Hacking', 'Learn penetration testing techniques')")
    
    cursor.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, task TEXT)")
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        print(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # Vulnerable SQL Query (allows injection)
        string=f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        print("here is what is passed to cursor.execute: ",string)
        cursor.execute(string)
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["is_admin"] = user[3]  # Assuming is_admin is the 4th column (index 3)
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Login Failed! Try Again.")

    return render_template("login.html", error=None)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check if username already exists
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # Debugging: Print the query to see what we're executing
        print(f"SELECT * FROM users WHERE username='{username}'")
        
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return render_template("register.html", error="Username already exists.")
        
        # Check if passwords match
        if password != confirm_password:
            conn.close()
            return render_template("register.html", error="Passwords do not match.")

        # Debugging: Print the query before inserting the new user
        print(f"INSERT INTO users (username, password, is_admin) VALUES ('{username}', '{password}', 0)")

        # Insert the new user into the database
        cursor.execute(f"INSERT INTO users (username, password, is_admin) VALUES ('{username}', '{password}', 0) -- can this work?")
        conn.commit()
        conn.close()

        # Automatically log in the user after registration
        print(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        # Vulnerable SQL Query (allows injection)
        string=f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        print("here is what is passed to cursor.execute: ",string)
        cursor.execute(string)
        user = cursor.fetchone()
        session["user"] = username
        session["is_admin"] = user[3]
        return redirect("/dashboard")
    
    return render_template("register.html", error=None)


@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", username=session['user'])
    return redirect("/")

@app.route("/calendar", methods=["GET", "POST"])
def calendar():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    if request.method == "POST" and session.get("is_admin") == 1:
        # Handle adding new course (admin-only functionality)
        course_name = request.form["course_name"]
        course_description = request.form["course_description"]
        
        cursor.execute(f"INSERT INTO courses (name, description) VALUES ('{course_name}', '{course_description}')")  # SQL Injection risk
        conn.commit()

    # Fetch existing courses from database
    cursor.execute("SELECT name, description FROM courses")
    courses = cursor.fetchall()
    conn.close()
    
    return render_template("calendar.html", courses=courses)

@app.route("/delete_course/<course_name>", methods=["POST"])
def delete_course(course_name):
    if "user" not in session or session["user"] != "admin":  # Only allow admin to delete courses
        return redirect("/dashboard")
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM courses WHERE name='{course_name}'")  # SQL Injection risk
    conn.commit()
    conn.close()
    
    return redirect("/calendar")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
