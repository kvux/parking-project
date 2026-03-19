from flask import Flask, jsonify, request
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'parking_db'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def home():
    return "🚗 Smart Parking System API is Running!"

@app.route('/api/spots')
def get_spots():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT spot_id, status FROM parking_spots ORDER BY spot_id")
    spots = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(spots)

@app.route('/api/entry', methods=['POST'])
def record_entry():
    data = request.json
    car_plate = data.get('car_plate')
    spot_id = data.get('spot_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO parking_records (car_plate, entry_time, spot_id) VALUES (%s, NOW(), %s)",
        (car_plate, spot_id)
    )
    cursor.execute(
        "UPDATE parking_spots SET status = 'occupied' WHERE spot_id = %s",
        (spot_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": f"Car {car_plate} entered spot {spot_id}"})

@app.route('/api/exit', methods=['POST'])
def record_exit():
    data = request.json
    car_plate = data.get('car_plate')
    spot_id = data.get('spot_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE parking_records SET exit_time = NOW() WHERE car_plate = %s AND spot_id = %s AND exit_time IS NULL",
        (car_plate, spot_id)
    )
    cursor.execute(
        "UPDATE parking_spots SET status = 'free' WHERE spot_id = %s",
        (spot_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": f"Car {car_plate} exited from spot {spot_id}"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)