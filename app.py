import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "OncoAI Clinical Decision Support API is Live and Operational", 200

@app.route('/health')
def health():
    return "Healthy", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
