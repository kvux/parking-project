# Smart Parking System

[한국어](https://github.com/kvux/parking-project/blob/main/README.ko.md)

## Overview
A backend API for managing parking spots, car entry/exit, and tracking parking history.

## Features
- View parking spots status
- Park a car (entry)
- Remove a car (exit)
- Prevent duplicate parking
- Track current parked cars
- View parking history
- Real-time sensor-driven spot updates
- Automatic LED indicators per spot
- User registration and login (JWT)

## Tech Stack
- Python (Flask)
- MySQL
- REST API
- Raspberry Pi + HC-SR04 sensors
- Android app *(in development)*

## API Endpoints

### Get all spots
`GET /api/spots`

### Get available spots
`GET /api/spots/available`

### Park a car
`POST /api/entry`
```json
{ "car_plate": "ABC123", "spot_id": 1 }
```

### Exit a car
`POST /api/exit`
```json
{ "car_plate": "ABC123", "spot_id": 1 }
```

### Get currently parked cars
`GET /api/current` *(JWT required)*

### Get parking history
`GET /api/history?page=1&per_page=20` *(JWT required)*

### Sensor update
`POST /api/sensor/update` *(requires X-Sensor-Key header)*
```json
{ "spot_id": 1, "occupied": true }
```

### Register
`POST /register`
```json
{ "name": "Name", "email": "email@test.com", "password": "12345678", "car_number": "12가 3456" }
```

### Login
`POST /login`
```json
{ "email": "email@test.com", "password": "12345678" }
```

## How to Run
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Sensor loop (Raspberry Pi only)
```bash
python module/sensor.py
```
