import sqlite3
import bcrypt
import os
import re
import smtplib
import random
import time
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from flask_jwt_extended import create_access_token

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def validate_password(password):
    if len(password) < 12:
        return False, "Password must be at least 12 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, "OK"

def send_email(to, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_ADDRESS
    msg["To"]      = to
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

def send_email_async(to, subject, html_body):
    t = threading.Thread(target=send_email, args=(to, subject, html_body), daemon=True)
    t.start()

def register_user(username, email, password):
    ok, msg = validate_password(password)
    if not ok:
        return {"success": False, "message": msg}

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
    ).fetchone()
    if existing:
        conn.close()
        return {"success": False, "message": "Username or email already in use."}

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn.execute(
        "INSERT INTO users (username, email, password_hash, verified) VALUES (?, ?, ?, 0)",
        (username, email, password_hash)
    )
    conn.commit()

    code = str(random.randint(100000, 999999))
    expires_at = time.time() + 600
    conn.execute(
        "INSERT INTO verification_codes (email, code, expires_at) VALUES (?, ?, ?)",
        (email, code, expires_at)
    )
    conn.commit()
    conn.close()

    html = f"""
    <div style="background:#0a0a0a;padding:40px 20px;font-family:'Courier New',monospace;color:#f5f5f5;max-width:520px;margin:0 auto;border-radius:12px;border:1px solid #1a1a1a;">
      <div style="text-align:center;margin-bottom:28px;">
        <div style="display:inline-block;background:#c8ff00;border-radius:12px;padding:10px 16px;">
          <span style="color:#000;font-weight:700;font-size:18px;letter-spacing:2px;">BIN BUDDY</span>
        </div>
      </div>
      <h2 style="color:#c8ff00;font-size:16px;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;">Verify Your Email</h2>
      <p style="color:#888;font-size:12px;margin-bottom:24px;">Use the code below to verify your account.</p>
      <div style="text-align:center;margin-bottom:24px;">
        <div style="display:inline-block;background:#111;border:1px solid #c8ff00;border-radius:10px;padding:16px 32px;">
          <span style="color:#c8ff00;font-size:32px;font-weight:700;letter-spacing:8px;">{code}</span>
        </div>
        <p style="color:#555;font-size:11px;margin-top:10px;">Expires in 10 minutes</p>
      </div>
      <p style="color:#333;font-size:10px;text-align:center;">If you did not create a Bin Buddy account, ignore this email.</p>
    </div>
    """
    send_email_async(email, "Verify your Bin Buddy account", html)
    return {"success": True, "message": "Account created. Check your email for a verification code."}


def verify_email(email, code):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM verification_codes WHERE email = ? AND code = ? ORDER BY expires_at DESC LIMIT 1",
        (email, code)
    ).fetchone()

    if not row:
        conn.close()
        return {"success": False, "message": "Invalid verification code."}
    if time.time() > row["expires_at"]:
        conn.close()
        return {"success": False, "message": "Verification code has expired."}

    conn.execute("UPDATE users SET verified = 1 WHERE email = ?", (email,))
    conn.execute("DELETE FROM verification_codes WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Email verified. You can now log in."}


def login_user(username, password):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        return {"success": False, "message": "Invalid username or password."}
    if not user["verified"]:
        return {"success": False, "message": "Please verify your email before logging in."}

    token = create_access_token(identity=username)
    return {"success": True, "message": "Login successful.", "token": token}


def request_password_reset(email, device_info):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if not user:
        conn.close()
        return {"success": True, "message": "If that email exists, a reset code has been sent."}

    conn.execute("UPDATE password_resets SET used = 1 WHERE email = ?", (email,))
    code = str(random.randint(100000, 999999))
    expires_at = time.time() + 600
    conn.execute(
        "INSERT INTO password_resets (email, code, expires_at, device_info) VALUES (?, ?, ?, ?)",
        (email, code, expires_at, device_info)
    )
    conn.commit()
    conn.close()

    html = f"""
    <div style="background:#0a0a0a;padding:40px 20px;font-family:'Courier New',monospace;color:#f5f5f5;max-width:520px;margin:0 auto;border-radius:12px;border:1px solid #1a1a1a;">
      <div style="text-align:center;margin-bottom:28px;">
        <div style="display:inline-block;background:#c8ff00;border-radius:12px;padding:10px 16px;">
          <span style="color:#000;font-weight:700;font-size:18px;letter-spacing:2px;">BIN BUDDY</span>
        </div>
      </div>
      <h2 style="color:#c8ff00;font-size:16px;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;">Password Reset Requested</h2>
      <p style="color:#888;font-size:12px;margin-bottom:24px;">A reset was requested for your account.</p>
      <div style="background:#111;border:1px solid #222;border-radius:10px;padding:20px;margin-bottom:24px;">
        <p style="color:#555;font-size:10px;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;">Device / Browser</p>
        <p style="color:#f5f5f5;font-size:13px;margin:0;">{device_info}</p>
      </div>
      <div style="text-align:center;margin-bottom:24px;">
        <p style="color:#555;font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;">Your reset code</p>
        <div style="display:inline-block;background:#111;border:1px solid #c8ff00;border-radius:10px;padding:16px 32px;">
          <span style="color:#c8ff00;font-size:32px;font-weight:700;letter-spacing:8px;">{code}</span>
        </div>
        <p style="color:#555;font-size:11px;margin-top:10px;">Expires in 10 minutes</p>
      </div>
      <div style="background:#1a0000;border:1px solid #3a0000;border-radius:10px;padding:16px;margin-bottom:16px;">
        <p style="color:#ff6b6b;font-size:12px;margin:0;">
          &#9888; <strong>Not you?</strong> Someone else requested this reset. Do not share this code.
          Your password has <strong>not</strong> been changed yet — you are still safe.
        </p>
      </div>
      <p style="color:#333;font-size:10px;text-align:center;">Bin Buddy will never ask for your password via email.</p>
    </div>
    """
    send_email_async(email, "Password Reset Request — Bin Buddy", html)
    return {"success": True, "message": "If that email exists, a reset code has been sent."}


def confirm_password_reset(email, code, new_password):
    ok, msg = validate_password(new_password)
    if not ok:
        return {"success": False, "message": msg}

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM password_resets WHERE email = ? AND code = ? AND used = 0 ORDER BY expires_at DESC LIMIT 1",
        (email, code)
    ).fetchone()

    if not row:
        conn.close()
        return {"success": False, "message": "Invalid or expired reset code."}
    if time.time() > row["expires_at"]:
        conn.close()
        return {"success": False, "message": "Reset code has expired. Please request a new one."}

    new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (row["id"],))
    conn.execute("UPDATE users SET password_hash = ? WHERE email = ?", (new_hash, email))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Password updated successfully."}