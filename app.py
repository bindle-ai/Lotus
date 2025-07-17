from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lotus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'change-this-secret'

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self):
        return serializer.dumps(self.email, salt='email-confirm')

    @staticmethod
    def confirm_token(token, expiration=3600):
        try:
            email = serializer.loads(token, salt='email-confirm', max_age=expiration)
        except (BadSignature, SignatureExpired):
            return None
        return email

def send_confirmation_email(email, token):
    confirm_url = f"http://localhost:5000/confirm/{token}"
    # For demo purposes we just print the confirmation link
    print(f"Confirm your account by visiting: {confirm_url}")

with app.app_context():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'message': 'Missing fields'}), 400
    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 400
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    token = user.generate_confirmation_token()
    send_confirmation_email(user.email, token)
    return jsonify({'message': 'User registered. Please check your email to confirm account.'}), 201

@app.route('/confirm/<token>', methods=['GET'])
def confirm_email(token):
    email = User.confirm_token(token)
    if not email:
        return jsonify({'message': 'Invalid or expired token'}), 400
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        return jsonify({'message': 'Account already confirmed'}), 200
    user.confirmed = True
    db.session.commit()
    return jsonify({'message': 'Account confirmed'}), 200

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({'message': 'Missing fields'}), 400
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    if not user.confirmed:
        return jsonify({'message': 'Please confirm your account before logging in.'}), 403
    return jsonify({'message': f'Welcome, {user.username}!'}), 200

if __name__ == '__main__':
    app.run(debug=True)
