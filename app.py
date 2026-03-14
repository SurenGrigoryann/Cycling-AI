from flask import Flask, render_template, request, jsonify
import os
import base64
from openai import OpenAI
 
app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
 
@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    image_data = data.get('image')  # base64 image
 
    # Strip the data URL prefix if present
    if ',' in image_data:
        image_data = image_data.split(',')[1]
 
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "What do you see in this image? Be concise and descriptive, max 2-3 sentences."
                    }
                ]
            }
        ],
        max_tokens=200
    )
 
    result = response.choices[0].message.content
    return jsonify({'result': result})
 
if __name__ == '__main__':
    app.run(debug=True)
