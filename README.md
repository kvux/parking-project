<<<<<<< HEAD
# Smart Parking System 

## Overview
A backend API for managing parking spots, car entry/exit, and tracking parking history.

## Features
- View parking spots status
- Park a car (entry)
- Remove a car (exit)
- Prevent duplicate parking
- Track current parked cars
- View parking history
- Real-time sensor-driven spot updates *(new)*
- Automatic LED indicators per spot *(new)*

## Tech Stack
- Python (Flask)
- MySQL
- REST API
- Raspberry Pi + HC-SR04 sensors *(new)*
- Android app *(in development)*

## API Endpoints

### Get all spots
GET /api/spots

### Get available spots
GET /api/spots/available

### Park a car
POST /api/entry
{
  "car_plate": "ABC123",
  "spot_id": 1
}

### Exit a car
POST /api/exit
{
  "car_plate": "ABC123",
  "spot_id": 1
}
### Get currently parked cars *(new)*
GET /api/current

### Get parking history *(new)*
GET /api/history?page=1&per_page=20

### Sensor update *(new)*
POST /api/sensor/update
{
  "spot_id": 1,
  "occupied": true
}

## How to Run
```bash
python -m venv venv
venv\Scripts\activate
pip install flask flask-cors flask-limiter mysql-connector-python python-dotenv requests
python app.py
```

### Sensor loop (Raspberry Pi only) *(new)*
```bash
python module/sensor.py
```
=======
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
>>>>>>> origin/signup-api
