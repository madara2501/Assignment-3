import os
import secrets
import hashlib
import smtplib

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import psycopg2
from psycopg2.extras import RealDictCursor

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template,
    make_response
)

from dotenv import load_dotenv

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key"
)


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "assignment3_auth"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "")
}


OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5
SESSION_EXPIRY_HOURS = 2


# ============================================================
# DATABASE
# ============================================================

def get_db_connection():

    return psycopg2.connect(
        **DB_CONFIG,
        cursor_factory=RealDictCursor
    )


# ============================================================
# OTP GENERATION
# ============================================================

def generate_otp():

    return f"{secrets.randbelow(1000000):06d}"


# ============================================================
# SEND OTP EMAIL
# ============================================================

def send_otp_email(receiver_email, otp):

    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password:

        raise RuntimeError(
            "SMTP_EMAIL or SMTP_PASSWORD is missing."
        )

    message = EmailMessage()

    message["Subject"] = "Assignment 3 - Email Verification OTP"
    message["From"] = sender_email
    message["To"] = receiver_email

    message.set_content(
        f"""
Hello,

Your verification OTP is:

{otp}

This OTP will expire in {OTP_EXPIRY_MINUTES} minutes.

If you did not request this OTP, please ignore this email.

Regards,
Assignment 3 Authentication System
"""
    )

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as smtp:

        smtp.login(
            sender_email,
            sender_password
        )

        smtp.send_message(message)


# ============================================================
# CREATE OTP
# ============================================================

def create_otp(user_id, email):

    otp = generate_otp()

    # Hash OTP before storing.
    otp_hash = generate_password_hash(otp)

    expires_at = (
        datetime.now(timezone.utc)
        +
        timedelta(minutes=OTP_EXPIRY_MINUTES)
    )

    connection = get_db_connection()

    try:

        cursor = connection.cursor()

        # Invalidate previous OTPs.
        cursor.execute(
            """
            UPDATE otp_codes
            SET used = TRUE
            WHERE user_id = %s
            AND used = FALSE
            """,
            (user_id,)
        )

        # Store new OTP hash.
        cursor.execute(
            """
            INSERT INTO otp_codes
            (
                user_id,
                otp_hash,
                expires_at
            )
            VALUES
            (%s, %s, %s)
            """,
            (
                user_id,
                otp_hash,
                expires_at
            )
        )

        connection.commit()

    finally:

        cursor.close()
        connection.close()


    # Send OTP.
    send_otp_email(
        email,
        otp
    )


# ============================================================
# VERIFY OTP
# ============================================================

def verify_otp(user_id, submitted_otp):

    connection = get_db_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM otp_codes
            WHERE user_id = %s
            AND used = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,)
        )

        otp_record = cursor.fetchone()

        if not otp_record:

            return False


        # Check expiration.
        if otp_record["expires_at"] <= datetime.now(timezone.utc):

            cursor.execute(
                """
                UPDATE otp_codes
                SET used = TRUE
                WHERE id = %s
                """,
                (otp_record["id"],)
            )

            connection.commit()

            return False


        # Check attempts.
        if otp_record["attempts"] >= MAX_OTP_ATTEMPTS:

            cursor.execute(
                """
                UPDATE otp_codes
                SET used = TRUE
                WHERE id = %s
                """,
                (otp_record["id"],)
            )

            connection.commit()

            return False


        # Verify OTP hash.
        if not check_password_hash(
            otp_record["otp_hash"],
            submitted_otp
        ):

            cursor.execute(
                """
                UPDATE otp_codes
                SET attempts = attempts + 1
                WHERE id = %s
                """,
                (otp_record["id"],)
            )

            connection.commit()

            return False


        # OTP is valid.
        cursor.execute(
            """
            UPDATE otp_codes
            SET used = TRUE
            WHERE id = %s
            """,
            (otp_record["id"],)
        )


        cursor.execute(
            """
            UPDATE users
            SET is_verified = TRUE
            WHERE id = %s
            """,
            (user_id,)
        )

        connection.commit()

        return True

    finally:

        cursor.close()
        connection.close()


# ============================================================
# SESSION TOKEN
# ============================================================

def hash_token(token):

    return hashlib.sha256(
        token.encode()
    ).hexdigest()


def create_session(user_id):

    token = secrets.token_urlsafe(32)

    token_hash = hash_token(token)

    expires_at = (
        datetime.now(timezone.utc)
        +
        timedelta(hours=SESSION_EXPIRY_HOURS)
    )

    connection = get_db_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO user_sessions
            (
                user_id,
                session_token_hash,
                expires_at
            )
            VALUES
            (%s, %s, %s)
            """,
            (
                user_id,
                token_hash,
                expires_at
            )
        )

        connection.commit()

    finally:

        cursor.close()
        connection.close()

    return token


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return """
    <h1>Assignment 3 Authentication System</h1>

    <a href="/register">Register</a>
    <br><br>

    <a href="/login">Login</a>
    <br><br>

    <a href="/health">Health Check</a>
    """


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "GET":

        return render_template(
            "register.html"
        )


    full_name = request.form.get(
        "full_name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    role = request.form.get(
        "role",
        "student"
    )


    if not full_name or not email or not password:

        return "All fields are required."


    if len(password) < 8:

        return "Password must contain at least 8 characters."


    if role not in [
        "student",
        "instructor"
    ]:

        return "Invalid role."


    connection = get_db_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        if cursor.fetchone():

            return """
            <h2>Email already registered.</h2>

            <a href="/login">
                Login
            </a>
            """


        # Hash password.
        password_hash = generate_password_hash(
            password
        )


        cursor.execute(
            """
            INSERT INTO users
            (
                full_name,
                email,
                password_hash,
                role
            )
            VALUES
            (%s, %s, %s, %s)
            RETURNING id
            """,
            (
                full_name,
                email,
                password_hash,
                role
            )
        )

        user = cursor.fetchone()

        connection.commit()

    finally:

        cursor.close()
        connection.close()


    # ========================================================
    # CREATE OTP
    # ========================================================

    try:

        create_otp(
            user["id"],
            email
        )

    except Exception as error:

        print(
            "OTP email error:",
            error
        )

        return f"""
        <h2>Account created.</h2>

        <p>
        However, OTP could not be sent.
        </p>

        <p>
        Check your SMTP configuration.
        </p>

        <a href="/login">
            Login
        </a>
        """


    return redirect(
        url_for(
            "verify_otp_page",
            user_id=user["id"]
        )
    )


# ============================================================
# OTP PAGE
# ============================================================

@app.route(
    "/verify-otp/<int:user_id>",
    methods=["GET", "POST"]
)
def verify_otp_page(user_id):

    if request.method == "GET":

        return render_template(
            "verify_otp.html",
            user_id=user_id
        )


    otp = request.form.get(
        "otp",
        ""
    ).strip()


    if not otp.isdigit() or len(otp) != 6:

        return "Enter a valid 6-digit OTP."


    if verify_otp(
        user_id,
        otp
    ):

        session_token = create_session(
            user_id
        )

        response = make_response(
            redirect(
                url_for("dashboard")
            )
        )

        response.set_cookie(
            "session_token",
            session_token,
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=SESSION_EXPIRY_HOURS * 3600
        )

        return response


    return """
    <h2>Invalid or expired OTP.</h2>

    <a href="javascript:history.back()">
        Try Again
    </a>
    """


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "GET":

        return render_template(
            "login.html"
        )


    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )


    connection = get_db_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

    finally:

        cursor.close()
        connection.close()


    if not user:

        return "Invalid email or password."


    if not check_password_hash(
        user["password_hash"],
        password
    ):

        return "Invalid email or password."


    if not user["is_verified"]:

        try:

            create_otp(
                user["id"],
                user["email"]
            )

        except Exception as error:

            print(
                "OTP error:",
                error
            )

        return redirect(
            url_for(
                "verify_otp_page",
                user_id=user["id"]
            )
        )


    session_token = create_session(
        user["id"]
    )

    response = make_response(
        redirect(
            url_for("dashboard")
        )
    )

    response.set_cookie(
        "session_token",
        session_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=SESSION_EXPIRY_HOURS * 3600
    )

    return response


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    token = request.cookies.get("session_token")

    if not token:
        return redirect(url_for("login"))

    token_hash = hash_token(token)

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                u.id,
                u.full_name,
                u.email,
                u.role,
                u.is_verified
            FROM users u
            JOIN user_sessions s
                ON u.id = s.user_id
            WHERE s.session_token_hash = %s
            AND s.expires_at > CURRENT_TIMESTAMP
            """,
            (token_hash,)
        )

        user = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    if not user:
        return redirect(url_for("login"))

    return render_template("dashboard.html", user=user)


# ============================================================
# STUDENT AREA
# ============================================================

@app.route("/student")
def student():

    return """
    <h1>Student Area</h1>

    <p>
    This area is intended for student users.
    </p>

    <a href="/dashboard">
        Dashboard
    </a>
    """


# ============================================================
# INSTRUCTOR AREA
# ============================================================

@app.route("/instructor")
def instructor():

    return """
    <h1>Instructor Area</h1>

    <p>
    This area is intended for instructor users.
    </p>

    <a href="/dashboard">
        Dashboard
    </a>
    """


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    token = request.cookies.get(
        "session_token"
    )


    if token:

        token_hash = hash_token(
            token
        )

        connection = get_db_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM user_sessions
                WHERE session_token_hash = %s
                """,
                (token_hash,)
            )

            connection.commit()

        finally:

            cursor.close()
            connection.close()


    response = make_response(
        redirect(
            url_for("login")
        )
    )

    response.delete_cookie(
        "session_token"
    )

    return response


# ============================================================
# HEALTH
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "healthy",
        "service": "Assignment 3 Authentication System"
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )