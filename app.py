from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_jwt_extended import JWTManager, create_access_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from auth import register_user, login_user, verify_email, request_password_reset, confirm_password_reset
from Learning import learning_bp
from Practice import practice_bp
from Game import game_bp
import os
import json
import anthropic

app = Flask(__name__)
app.register_blueprint(learning_bp)
app.register_blueprint(practice_bp)
app.register_blueprint(game_bp)

app.config["JWT_SECRET_KEY"] = "x7k#mP9$qL2@nR5&vT8*wY3"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 60 * 60 * 24 * 30  # 30 days

jwt = JWTManager(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day"])

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

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

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    result = verify_email(data['email'], data['code'])
    return jsonify(result)

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login_page_FINAL.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    result = login_user(data['username'], data['password'])
    return jsonify(result)

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    user_agent = request.headers.get('User-Agent', 'Unknown device')
    device_info = user_agent[:120]
    result = request_password_reset(data['email'], device_info)
    return jsonify(result)

@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    result = confirm_password_reset(data['email'], data['code'], data['new_password'])
    return jsonify(result)

@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')

# Serve character animation frames with clean URLs
@app.route('/asset/<animation>/<filename>')
@limiter.exempt
def serve_asset(animation, filename):
    base = os.path.join(app.root_path, 'asset')
    if animation == 'happy':
        directory = os.path.join(base, 'happy asset', 'happy asset')
    elif animation == 'sad':
        directory = os.path.join(base, 'sad asset', 'sad asset')
    else:
        return 'Not found', 404
    return send_from_directory(directory, filename)

print(os.environ.get("EMAIL_ADDRESS"))
print(os.environ.get("EMAIL_PASSWORD"))

if __name__ == '__main__':
    app.run(debug=True)