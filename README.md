# Bin Buddy

Bin Buddy is a web application that uses AI to help users learn how to sort waste correctly. Users can take or upload a photo of an item and receive an instant recommendation on whether it belongs in the garbage, recycling, or organics bin. The app also includes structured lessons and an interactive sorting game.

---

## Features

- AI image analysis powered by Claude (Anthropic) to identify items and recommend the correct bin
- User registration and login with email verification and JWT authentication
- Password reset via email
- Learning module with three lessons on waste sorting
- Practice mode and a drag-and-drop sorting game with a leaderboard

---

## Tech Stack

- Python, Flask
- Anthropic Claude API
- SQLite
- Flask-JWT-Extended
- Flask-Limiter
- bcrypt
- Gmail SMTP
- Gunicorn

---

## Setup

**1. Clone the repository**

```bash
git clone https://github.com/YOUR-USERNAME/bin-buddy.git
cd bin-buddy
```

**2. Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the app**

```bash
python app.py
```

The app will be available at http://127.0.0.1:5000.

---

## Project Structure

```
bin-buddy/
├── app.py              # Main Flask application
├── auth.py             # Authentication logic
├── Learning.py         # Learning routes blueprint
├── Practice.py         # Practice route blueprint
├── Game.py             # Game routes and leaderboard
├── database.db         # SQLite database
├── requirements.txt    # Python dependencies
├── Procfile            # Deployment config
├── templates/          # HTML templates
└── asset/              # Images, sounds, and emoji assets
```

---

## Environment Notes

`appfake.py` and `authfake.py` are development versions of `app.py` and `auth.py` included for testing without a full environment setup. Use `app.py` for production.

---

## License

MIT
