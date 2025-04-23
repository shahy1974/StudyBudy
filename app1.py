from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('FLASK_SECRET_KEY')  # From .env file

# DeepSeek API Config
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

users = {}  # Temporary user storage,replace with database in production


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            if request.is_json:
                return jsonify({'success': True})
            return redirect(url_for('ask'))
        
        error = {'error': 'Invalid credentials'}
        return jsonify(error), 401 if request.is_json else render_template('login.html', error=error['error'])
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        
        if username in users:
            error = {'error': 'Username exists'}
            return jsonify(error), 400 if request.is_json else render_template('signup.html', error=error['error'])
            
        users[username] = {
            'password': generate_password_hash(data.get('password')),
            'email': data.get('email')
        }
        
        if request.is_json:
            return jsonify({'success': True})
        return redirect(url_for('login'))
    
    return render_template('signup.html')


@app.route('/ask', methods=['GET', 'POST'])
def ask():
   if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        question = request.json.get('question')
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": question}],
            "temperature": 0.7
        }
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            answer = response.json()['choices'][0]['message']['content']
            return jsonify({'answer': answer})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return render_template('ask.html')

#log out

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# Static files route
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)