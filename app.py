from flask import Flask, render_template, request, jsonify
import os
import json
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic(api_key="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")

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
                            "text": 'Identify the main item in this image. Respond ONLY with valid JSON, no markdown: {"item": "item name", "bin": "Garbage" or "Recycling" or "Organic", "explanation": "one short sentence why this bin is correct"}'
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

if __name__ == '__main__':
    app.run(debug=True)
