from flask import Flask, render_template, request, jsonify
import os
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

    # Strip the data URL prefix if present
    if ',' in image_data:
        image_data = image_data.split(',')[1]

    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=300,
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
                            "text": "What do you see in this image? Be concise and descriptive, max 2-3 sentences."
                        }
                    ]
                }
            ]
        )
        result = response.content[0].text
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
