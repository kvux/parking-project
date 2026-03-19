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

## Tech Stack
- Python (Flask)
- MySQL
- REST API

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

## How to Run

```bash
python -m venv venv
venv\Scripts\activate
pip install flask mysql-connector-python python-dotenv flask-cors flask-limiter
python app.py
