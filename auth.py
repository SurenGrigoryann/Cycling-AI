import sqlite3
import bcrypt
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

DB_PATH = os.environ.get("DB_PATH", "database.db")

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            verify_code TEXT
        )
    ''')
    conn.commit()
    conn.close()

def send_verification_email(email, code):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = email
    msg['Subject'] = "Bin Buddy — Your Verification Code"

    body = f"""
    <html>
    <body style="background:#080808;font-family:sans-serif;padding:40px;color:#f0f0f0;">
        <div style="max-width:400px;margin:0 auto;background:#111;border:1px solid #222;border-radius:16px;padding:32px;text-align:center;">
            <h1 style="color:#c8ff00;letter-spacing:0.1em;">BIN BUDDY</h1>
            <p style="color:#888;margin-bottom:24px;">Your verification code:</p>
            <div style="font-size:2.5rem;font-weight:800;letter-spacing:0.3em;color:#c8ff00;background:#0d0d0d;padding:20px;border-radius:12px;margin-bottom:24px;">
                {code}
            </div>
            <p style="color:#555;font-size:0.8rem;">This code expires in 10 minutes.</p>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def register_user(username, email, password):
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    code = str(random.randint(100000, 999999))

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, email, password_hash, verified, verify_code) VALUES (?, ?, ?, 0, ?)",
            (username, email, password_hash, code)
        )
        conn.commit()
        conn.close()

        # Send verification email
        sent = send_verification_email(email, code)
        if sent:
            return {"success": True, "message": "Check your email for the verification code", "requires_verification": True}
        else:
            return {"success": False, "message": "Account created but email failed to send"}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username or email already exists"}

def verify_code(email, code):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if not user:
        conn.close()
        return {"success": False, "message": "User not found"}

    if user["verify_code"] == code:
        conn.execute("UPDATE users SET verified = 1, verify_code = NULL WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Email verified!"}

    conn.close()
    return {"success": False, "message": "Invalid code"}

def login_user(username, password):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not user:
        return {"success": False, "message": "Invalid username or password"}

    if not user["verified"]:
        return {"success": False, "message": "Please verify your email first"}

    if bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        return {"success": True, "message": "Login successful"}

    return {"success": False, "message": "Invalid username or password"}

init_db()