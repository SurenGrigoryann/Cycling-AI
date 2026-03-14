import sqlite3
import bcrypt

DB_PATH = r"C:\Users\Mobeen\OneDrive\Desktop\Recycling AI\Cycling-AI\database.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def register_user(username, email, password):
   # password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
          #  (username, email, password_hash)
        )
        conn.commit()
        conn.close()
        return {"success": True, "message": "User registered successfully"}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username or email already exists"}

def login_user(username, password):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user["password_hash"]):
        return {"success": True, "message": "Login successful"}
    return {"success": False, "message": "Invalid username or password"}