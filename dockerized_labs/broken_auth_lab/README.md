# Broken Authentication Lab

This is a deliberately vulnerable web application that demonstrates common authentication vulnerabilities. It is designed for educational purposes to help understand various authentication security issues and their prevention.

## Vulnerabilities Included

1. Weak Password Requirements
2. Plain Text Password Storage
3. Insecure Session Management
4. Vulnerable "Remember Me" Functionality
5. Predictable Password Reset Tokens
6. No Brute Force Protection

## Setup Instructions

### Prerequisites
- Docker
- Docker Compose

### Running the Lab

1. Clone the repository
2. Navigate to the broken_auth_lab directory
3. Build and run the container:
   ```bash
   docker-compose up --build
   ```
4. Access the lab at http://localhost:5000

Compose publishes port 5000 only on the Docker host's loopback interface; direct access from other machines is disabled. The application keeps its container listener on `0.0.0.0:5000` so Docker port forwarding works, with debug mode disabled. When running the image directly, publish it with `-p 127.0.0.1:5000:5000` as well.

`FLASK_DEBUG` defaults to disabled when running `app.py`; only `1` or `true` (case-insensitive) enables debugging, and all other values disable it. Compose explicitly sets `FLASK_DEBUG=0`. Local development, CI, and deployments need no additional configuration to keep debugging disabled. Enable debugging only for trusted local development by setting this variable in the process environment, or overriding the service environment when using Compose. Never enable debugging on an exposed service.

### Default Credentials

The lab comes with two pre-configured users:
- Admin User:
  - Username: admin
  - Password: admin123
  - Email: admin@example.com

- Regular User:
  - Username: user
  - Password: password123
  - Email: user@example.com

## Lab Exercises

1. **Password Policy Bypass**
   - Try to create accounts with weak passwords
   - Observe the lack of password requirements

2. **Session Token Analysis**
   - Login with remember me enabled
   - Analyze the session cookie structure
   - Try to manipulate the session token

3. **Password Reset Exploitation**
   - Request a password reset
   - Analyze the reset token generation
   - Try to predict or manipulate reset tokens

4. **Role Escalation**
   - Login as a regular user
   - Try to escalate privileges to admin

## Security Notice

This application contains intentional security vulnerabilities for educational purposes. DO NOT deploy this in a production environment or expose it to the public internet.

## Prevention Tips

1. Implement strong password policies
2. Use secure password hashing (bcrypt, Argon2)
3. Implement proper session management
4. Use secure token generation
5. Implement rate limiting and brute force protection
6. Use HTTPS
7. Implement proper access controls
8. Enable security headers
9. Use secure configuration in production 
