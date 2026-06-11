from flask import Flask, render_template, request, make_response
import json
import base64
from dataclasses import dataclass, asdict

app = Flask(__name__)

@dataclass
class User:
    username: str 
    is_admin: bool = False

    pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/serialize', methods=['POST'])
def serialize_data():
    username = request.form.get('username', 'guest')
    # Create regular user with admin=False
    user = User(username=username, is_admin=False)
    serialized = base64.b64encode(json.dumps(asdict(user)).encode()).decode()
    return render_template('result.html', serialized=serialized)

@app.route('/deserialize', methods=['POST'])
def deserialize_data():
    try:
        serialized_data = request.form.get('serialized_data', '')
        decoded_data = base64.b64decode(serialized_data)
        data = json.loads(decoded_data)
        if not isinstance(data, dict) or 'username' not in data or 'is_admin' not in data:
            raise ValueError("Invalid user data format")
        user = User(username=str(data['username']), is_admin=bool(data['is_admin']))

        if isinstance(user, User):
            if user.is_admin:
                message = f"Welcome Admin {user.username}! Here's the secret admin content: ADMIN_KEY_123"
            else:
                message = f"Welcome {user.username}. Only admins can see the secret content."
        else:
            message = "Invalid user data"
        
        return render_template('result.html', message=message)
    except Exception as e:
        return render_template('result.html', message=f"Error: {str(e)}")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)

    