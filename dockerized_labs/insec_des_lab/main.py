from flask import Flask, render_template, request, make_response
import json
import base64
from dataclasses import dataclass, asdict

app = Flask(__name__)

@dataclass
class User:
    username: str 
    is_admin: bool = False

    def __reduce__(self):
        # Intentionally vulnerable __reduce__ method to match PyGoat
        return (User, (self.username, self.is_admin))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/serialize', methods=['POST'])
def serialize_data():
    username = request.form.get('username', 'guest')
    # Create regular user with admin=False
    user = User(username=username, is_admin=False)
    # Encode only user fields as JSON
    serialized = base64.b64encode(json.dumps(asdict(user)).encode()).decode()
    return render_template('result.html', serialized=serialized)

@app.route('/deserialize', methods=['POST'])
def deserialize_data():
    try:
        serialized_data = request.form.get('serialized_data', '')
        decoded_data = base64.b64decode(serialized_data)
        # Reconstruct user data without loading executable objects
        user_data = json.loads(decoded_data)
        user = User(**user_data) if (
            isinstance(user_data, dict)
            and user_data.keys() <= {'username', 'is_admin'}
            and isinstance(user_data.get('username'), str)
            and isinstance(user_data.get('is_admin', False), bool)
        ) else None
        
        if isinstance(user, User) and isinstance(user.username, str) and isinstance(user.is_admin, bool):
            if user.is_admin:
                message = f"Welcome Admin {user.username}! Here's the secret admin content: ADMIN_KEY_123"
            else:
                message = f"Welcome {user.username}. Only admins can see the secret content."
        else:
            app.logger.warning("Invalid user data submitted for deserialization")
            message = "Invalid user data"
        
        return render_template('result.html', message=message)
    except Exception:
        app.logger.warning("Invalid user data submitted for deserialization")
        return render_template('result.html', message="Error: Invalid user data")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

    
