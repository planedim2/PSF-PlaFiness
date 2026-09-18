from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "psf-plafitness-secret-key"


# =========================
# DATABASE
# =========================

def get_db():
    conn = sqlite3.connect("plafitness.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            session TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            UNIQUE(date, time)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# SIGN UP
# =========================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            return render_template(
                "signup.html",
                error="Please fill in all fields."
            )

        if len(password) < 6:
            return render_template(
                "signup.html",
                error="Password must be at least 6 characters."
            )

        if password != confirm_password:
            return render_template(
                "signup.html",
                error="Passwords do not match."
            )

        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:
            conn.execute(
                """
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()

            return render_template(
                "signup.html",
                error="An account with that email already exists."
            )

        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()

        if user is None or not check_password_hash(
            user["password"],
            password
        ):
            return render_template(
                "login.html",
                error="Incorrect email or password."
            )

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        if email == "suzzansamaha@gmail.com":
            session["admin"] = True
        else:
            session["admin"] = False

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    name = session.get("user_name")

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    upcoming_booking = conn.execute(
        """
        SELECT *
        FROM bookings
        WHERE email = ?
        AND date >= ?
        ORDER BY date ASC, time ASC
        LIMIT 1
        """,
        (user["email"], date.today().isoformat())
    ).fetchone()

    conn.close()

    return render_template(
        "dashboard.html",
        name=name,
        user=user,
        upcoming_booking=upcoming_booking
    )


# =========================
# BOOKING
# =========================

@app.route("/book", methods=["POST"])
def book():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    booking_session = request.form.get("session", "").strip()
    booking_date = request.form.get("date", "").strip()
    booking_time = request.form.get("time", "").strip()

    if not name or not email or not booking_session:
        return jsonify({
            "success": False,
            "message": "Please fill in all booking fields."
        })

    if not booking_date or not booking_time:
        return jsonify({
            "success": False,
            "message": "Please select a date and time."
        })

    try:
        selected_date = date.fromisoformat(booking_date)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid booking date."
        })

    if selected_date < date.today():
        return jsonify({
            "success": False,
            "message": "You cannot book a date in the past."
        })

    conn = get_db()

    existing_booking = conn.execute(
        """
        SELECT *
        FROM bookings
        WHERE date = ?
        AND time = ?
        """,
        (booking_date, booking_time)
    ).fetchone()

    if existing_booking:
        conn.close()

        return jsonify({
            "success": False,
            "message": "That time is already booked. Please choose another time."
        })

    conn.execute(
        """
        INSERT INTO bookings
        (name, email, session, date, time)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            name,
            email,
            booking_session,
            booking_date,
            booking_time
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Your session has been booked successfully!"
    })

# =========================
# BOOKED TIMES
# =========================

@app.route("/booked-times")
def booked_times():

    booking_date = request.args.get("date", "").strip()

    conn = get_db()

    bookings = conn.execute(
        """
        SELECT time
        FROM bookings
        WHERE date = ?
        """,
        (booking_date,)
    ).fetchall()

    conn.close()

    booked = [
        booking["time"]
        for booking in bookings
    ]

    return jsonify(booked)


# =========================
# MY BOOKINGS
# =========================

@app.route("/my-bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect(url_for("login"))

    email = session.get("user_email")

    conn = get_db()

    bookings = conn.execute(
        """
        SELECT *
        FROM bookings
        WHERE email = ?
        ORDER BY date ASC, time ASC
        """,
        (email,)
    ).fetchall()

    conn.close()

    return render_template(
        "my-bookings.html",
        bookings=bookings
    )


# =========================
# CANCEL BOOKING
# =========================

@app.route("/cancel-booking/<int:booking_id>", methods=["POST"])
def cancel_booking(booking_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please log in."
        })

    email = session.get("user_email")

    conn = get_db()

    booking = conn.execute(
        """
        SELECT *
        FROM bookings
        WHERE id = ?
        AND email = ?
        """,
        (booking_id, email)
    ).fetchone()

    if booking is None:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Booking not found."
        })

    try:
        booking_date = date.fromisoformat(
            booking["date"]
        )
    except ValueError:
        conn.close()

        return jsonify({
            "success": False,
            "message": "Invalid booking date."
        })

    if booking_date < date.today():
        conn.close()

        return jsonify({
            "success": False,
            "message": "Past bookings cannot be cancelled."
        })

    conn.execute(
        """
        DELETE FROM bookings
        WHERE id = ?
        """,
        (booking_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Booking cancelled successfully."
    })


# =========================
# CONTACT
# =========================

@app.route("/contact", methods=["POST"])
def contact():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        })

    conn = get_db()

    conn.execute(
        """
        INSERT INTO messages
        (name, email, message)
        VALUES (?, ?, ?)
        """,
        (name, email, message)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Your message has been sent!"
    })


# =========================
# ADMIN
# =========================

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect(url_for("dashboard"))

    conn = get_db()

    users = conn.execute(
        """
        SELECT *
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()

    bookings = conn.execute(
        """
        SELECT *
        FROM bookings
        ORDER BY date ASC, time ASC
        """
    ).fetchall()

    messages = conn.execute(
        """
        SELECT *
        FROM messages
        ORDER BY id DESC
        """
    ).fetchall()

    total_members = conn.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    total_bookings = conn.execute(
        "SELECT COUNT(*) FROM bookings"
    ).fetchone()[0]

    total_messages = conn.execute(
        "SELECT COUNT(*) FROM messages"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        bookings=bookings,
        messages=messages,
        total_members=total_members,
        total_bookings=total_bookings,
        total_messages=total_messages
    )


# =========================
# DELETE USER
# =========================

@app.route("/delete-user/<int:user_id>")
def delete_user(user_id):

    if not session.get("admin"):
        return redirect(url_for("dashboard"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# =========================
# DELETE BOOKING
# =========================

@app.route("/delete-booking/<int:booking_id>")
def delete_booking(booking_id):

    if not session.get("admin"):
        return redirect(url_for("dashboard"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM bookings
        WHERE id = ?
        """,
        (booking_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# =========================
# DELETE MESSAGE
# =========================

@app.route("/delete-message/<int:message_id>")
def delete_message(message_id):

    if not session.get("admin"):
        return redirect(url_for("dashboard"))

    conn = get_db()

    conn.execute(
        """
        DELETE FROM messages
        WHERE id = ?
        """,
        (message_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin"))


# =========================
# WORKOUT LIBRARY
# =========================

@app.route("/workouts")
def workouts():
    return render_template("workouts.html")


# =========================
# WORKOUT DATA
# =========================

workout_data = {

    "squats": {
        "name": "Squats",
        "category": "Lower Body",
        "description": "A basic lower-body exercise that works the legs and glutes.",
        "difficulty": "Beginner",
        "duration": "10 minutes",
        "exercises": [
            "Bodyweight Squats",
            "Pause Squats",
            "Slow Squats"
        ],
        "image": "squats.jpg",
        "video": "https://www.youtube.com/embed/kI_sf3YBXYg"
    },

    "push-ups": {
        "name": "Push-Ups",
        "category": "Upper Body",
        "description": "A bodyweight exercise that works the chest, shoulders, arms, and core.",
        "difficulty": "Beginner",
        "duration": "10 minutes",
        "exercises": [
            "Standard Push-Ups",
            "Knee Push-Ups",
            "Incline Push-Ups"
        ],
        "image": "push-ups.jpg",
        "video": "https://www.youtube.com/embed/ABbVpmubIGQ"
    },

    "lunges": {
        "name": "Lunges",
        "category": "Lower Body",
        "description": "A lower-body movement that works the legs while practicing balance and control.",
        "difficulty": "Beginner",
        "duration": "10 minutes",
        "exercises": [
            "Forward Lunges",
            "Reverse Lunges",
            "Alternating Lunges"
        ],
        "image": "lunges.jpg"
    },

    "plank": {
        "name": "Plank",
        "category": "Core",
        "description": "A core exercise that focuses on maintaining a stable body position.",
        "difficulty": "Beginner",
        "duration": "5 minutes",
        "exercises": [
            "Forearm Plank",
            "Knee Plank",
            "Plank Hold"
        ],
        "image": "plank.jpg",
        "video": "https://www.youtube.com/embed/BQu26ABuVS0"
    },

    "jumping-jacks": {
        "name": "Jumping Jacks",
        "category": "Cardio",
        "description": "A simple cardio movement that gets the whole body moving.",
        "difficulty": "Beginner",
        "duration": "5 minutes",
        "exercises": [
            "Basic Jumping Jacks",
            "Low-Impact Jacks",
            "Steady-Pace Jacks"
        ],
        "image": "jumping-jacks.jpg"
    },

    "burpees": {
        "name": "Burpees",
        "category": "Full Body",
        "description": "A full-body movement combining several basic exercise positions.",
        "difficulty": "Intermediate",
        "duration": "10 minutes",
        "exercises": [
            "Standard Burpees",
            "Step-Back Burpees",
            "Modified Burpees"
        ],
        "image": "burpees.jpg"
    },

    "mountain-climbers": {
        "name": "Mountain Climbers",
        "category": "Cardio",
        "description": "A dynamic exercise that combines core stability with cardio movement.",
        "difficulty": "Intermediate",
        "duration": "8 minutes",
        "exercises": [
            "Slow Mountain Climbers",
            "Alternating Climbers",
            "Controlled Climbers"
        ],
        "image": "mountain-climbers.jpg"
    },

    "glute-bridges": {
        "name": "Glute Bridges",
        "category": "Lower Body",
        "description": "A floor-based movement that works the glutes and hips.",
        "difficulty": "Beginner",
        "duration": "10 minutes",
        "exercises": [
            "Basic Glute Bridges",
            "Pause Glute Bridges",
            "Single-Leg Practice"
        ],
        "image": "glute-bridges.jpg"
    },

    "dumbbell-rows": {
        "name": "Dumbbell Rows",
        "category": "Strength",
        "description": "A strength exercise that works the back and upper body using dumbbells.",
        "difficulty": "Intermediate",
        "duration": "15 minutes",
        "exercises": [
            "Single-Arm Rows",
            "Supported Rows",
            "Controlled Rows"
        ],
        "image": "dumbbell-rows.jpg"
    },

    "shoulder-press": {
        "name": "Shoulder Press",
        "category": "Strength",
        "description": "An upper-body strength exercise that focuses on the shoulders and arms.",
        "difficulty": "Beginner",
        "duration": "10 minutes",
        "exercises": [
            "Seated Shoulder Press",
            "Standing Shoulder Press",
            "Light Dumbbell Press"
        ],
        "image": "shoulder-press.jpg"
    },

    "bicycle-crunches": {
        "name": "Bicycle Crunches",
        "category": "Core",
        "description": "A core exercise using controlled alternating movements.",
        "difficulty": "Beginner",
        "duration": "8 minutes",
        "exercises": [
            "Slow Bicycle Crunches",
            "Alternating Crunches",
            "Controlled Bicycle Crunches"
        ],
        "image": "bicycle-crunches.jpg"
    },

    "high-knees": {
        "name": "High Knees",
        "category": "Cardio",
        "description": "An energetic cardio movement involving alternating knee lifts.",
        "difficulty": "Beginner",
        "duration": "5 minutes",
        "exercises": [
            "Slow High Knees",
            "Marching High Knees",
            "Steady-Pace High Knees"
        ],
        "image": "high-knees.jpg"
    }

}


# =========================
# WORKOUT DETAIL
# =========================

@app.route("/workout/<workout_name>")
def workout_detail(workout_name):

    workout = workout_data.get(workout_name)

    if workout is None:
        return redirect(url_for("workouts"))

    return render_template(
        "workout-detail.html",
        workout=workout
    )


# =========================
# ACCOUNT
# =========================

@app.route("/account")
def account():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    user = conn.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "account.html",
        user=user
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================
# START APPLICATION
# =========================

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )