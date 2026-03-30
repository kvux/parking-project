from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    car_number = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'car_number': self.car_number
        }

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not all(k in data for k in ['name', 'email', 'password', 'car_number']):
        return jsonify({'error': '모든 필드를 입력해주세요'}), 400
    if len(data['password']) < 6:
        return jsonify({'error': '비밀번호는 6자리 이상'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '이미 존재하는 이메일'}), 400
    
    user = User(
        name=data['name'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        car_number=data['car_number']
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify([u.to_dict() for u in User.query.all()])

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    return jsonify(User.query.get_or_404(id).to_dict())

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    db.session.delete(User.query.get_or_404(id))
    db.session.commit()
    return '', 204

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
