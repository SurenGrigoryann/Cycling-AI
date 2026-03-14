from flask import Flask, render_template, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from auth import register_user, login_user
import os
import json
import anthropic

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "x7k#mP9$qL2@nR5&vT8*wY3"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600

jwt = JWTManager(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day"])

client = anthropic.Anthropic(api_key="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")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
@jwt_required()
def analyze():
    current_user = get_jwt_identity()
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

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    result = login_user(data['username'], data['password'])
    return jsonify(result)

@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html')


if __name__ == '__main__':
    app.run(debug=True)


