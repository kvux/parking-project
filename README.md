# Smart Parking Backend

## Install
```bash
pip install flask flask-sqlalchemy werkzeug
```

## Run
```bash
python app.py
```

## API

**Register:**
```bash
POST /register
{"name": "이름", "email": "email@test.com", "password": "123456", "car_number": "12가 3456"}
```

**Get Users:** `GET /users`

**Get User:** `GET /users/<id>`

**Delete User:** `DELETE /users/<id>`

**Health:** `GET /health`
