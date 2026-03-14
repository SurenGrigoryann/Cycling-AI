from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_jwt_extended import JWTManager, create_access_token, decode_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from auth import register_user, login_user
from functools import wraps
import os
import json
import anthropic

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "x7k#mP9$qL2@nR5&vT8*wY3")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "flask-session-secret")

jwt = JWTManager(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day"])

# 1. CHANGED: API key pulled from environment, not hardcoded
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# 2. ADDED: login_required decorator to protect pages
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get("access_token")
        if not token:
            return redirect(url_for("login_page"))
        try:
            decode_token(token)
        except Exception:
            session.clear()
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    image_data = data.get('image')

    if ',' in image_data:
        image_data = image_data.split(',')[1]

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": 'Identify the main item in this image. Respond ONLY with valid JSON, no markdown: {"item": "item name", "bin": "Garbage" or "Recycling" or "Organic", "explanation": "one short sentence why this bin is correct", "confident": true or false}. Set confident to false if the image is blurry, unclear, contains no identifiable item, or you are genuinely unsure which bin is correct.'
                        }
                    ]
                }
            ]
        )
        text = response.content[0].text.strip()
        if '```' in text:
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        result = json.loads(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    result = register_user(data['username'], data['email'], data['password'])
    return jsonify(result)

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    result = login_user(data['username'], data['password'])
    # 3. ADDED: store token in session on successful login
    if result.get("success") and result.get("token"):
        session["access_token"] = result["token"]
    return jsonify(result)

# 4. ADDED: logout route to clear the session
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# 5. CHANGED: added @login_required to block unauthenticated access
@app.route('/tutorial')
@login_required
def tutorial():
    return render_template('tutorial.html')

# Add this anywhere in app.py before the if __name__ == '__main__': line

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    app.run(debug=True)