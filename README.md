# Smart Parking System

[한국어](https://github.com/kvux/parking-project/blob/main/README.ko.md)

## Overview
A backend API for managing parking spots, car entry/exit, fee calculation, and reservations with real-time sensor monitoring.

## Features
- View parking spots status
- Park a car (entry) / Exit a car (exit with automatic fee calculation)
- Prevent duplicate parking
- Track current parked cars
- View parking history with pagination
- Real-time sensor-driven spot updates (HC-SR04)
- Automatic LED indicators per spot
- User registration and login (JWT)
- **Reservation system** (book spots for specific time slots)
- **Automatic fee calculation** (10,000 KRW/hour, 5-min grace period)
- Barrier event logging (CSV + JSON)

## Tech Stack
- Python (Flask 3.0)
- MySQL
- REST API
- Raspberry Pi + HC-SR04 sensors
- Android app *(in development)*

## Module Structure
```
app.py                    # Main Flask API server
module/
  sensor.py               # Pi sensor loop (HC-SR04, LED control)
  led_controller.py       # LED control utilities
  fee_calculator.py      # Parking fee calculation
  exit_entry.py          # Barrier event logging
  reservations.py        # Reservation system logic
```

## API Endpoints

### Parking Spots
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/spots` | Get all parking spots | None |
| GET | `/api/spots/available` | Get available count + % | None |

### Entry/Exit
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/entry` | Car entry `{car_plate, spot_id}` | None |
| POST | `/api/exit` | Car exit → returns fee | None |
| GET | `/api/current` | Currently parked cars | JWT |
| GET | `/api/history` | Parking history `?page=1&per_page=20` | JWT |

### Fee Calculator
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/calculate-fee` | Preview fee `{entry_time, exit_time, discount_percent}` |

### Reservations
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/reservations` | Create reservation `{start_time, end_time, spot_id?}` | JWT |
| GET | `/api/reservations` | List my reservations | JWT |
| POST | `/api/reservations/<id>/checkin` | Check in with reservation | JWT |
| POST | `/api/reservations/<id>/cancel` | Cancel reservation | JWT |
| GET | `/api/reservations/verify/<code>` | Verify reservation code (gate) | None |

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register `{name, email, password, car_number}` |
| POST | `/login` | Login `{email, password}` → returns JWT |

### Sensor
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sensor/update` | Sensor update `{spot_id, occupied}` + `X-Sensor-Key` header |

## Fee Rules
- **Rate**: 10,000 KRW per hour
- **Grace period**: First 5 minutes free
- **Minimum charge**: 1 hour (rounded up)
- **Discounts**: Supported (0-100%)

## Reservation Rules
- Book for specific date/time slots
- Option to choose specific spot or let system auto-assign
- Check-in window: 15 min before to 15 min after start time
- Auto-assignment finds first available spot for the time slot

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

## Environment Variables
Copy `.env.example` to `.env` and fill in:
- `JWT_SECRET_KEY` (required) — generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- `SENSOR_API_KEY` (required) — generate with: `python -c "import secrets; print(secrets.token_hex(16))"`
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `ALLOWED_ORIGIN` (CORS origin for Android app)
