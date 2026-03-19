from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)

#database main
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'parking_db'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)


def error_response(message, code=400):
    return jsonify({"error": message}), code


@app.route('/')
def home():
    return jsonify({"message": "Smart Parking System API is running"})


#get all spot

@app.route('/api/spots', methods=['GET'])
def get_spots():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT spot_id, status FROM parking_spots ORDER BY spot_id")
        spots = cursor.fetchall()

        return jsonify(spots), 200

    except Error as e:
        return error_response(str(e), 500)

    finally:
        cursor.close()
        conn.close()



# check avaialble spot

@app.route('/api/spots/available', methods=['GET'])
def get_available_spots():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM parking_spots WHERE status = 'free'")
        count = cursor.fetchone()[0]

        return jsonify({"available_spots": count}), 200

    except Error as e:
        return error_response(str(e), 500)

    finally:
        cursor.close()
        conn.close()


#record entry

@app.route('/api/entry', methods=['POST'])
def record_entry():
    data = request.get_json()

    if not data:
        return error_response("Invalid JSON input")

    car_plate = data.get('car_plate')
    spot_id = data.get('spot_id')

    if not car_plate or not spot_id:
        return error_response("car_plate and spot_id are required")
cursor.execute("""
    SELECT * FROM parking_records 
    WHERE car_plate = %s AND exit_time IS NULL
""", (car_plate,))

active = cursor.fetchone()

if active:
    return error_response("Car is already parked")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # check spot ok?
        cursor.execute("SELECT status FROM parking_spots WHERE spot_id = %s", (spot_id,))
        spot = cursor.fetchone()

        if not spot:
            return error_response("Spot does not exist")

        if spot['status'] != 'free':
            return error_response("Spot already occupied")

        # insert record
        cursor.execute(
            "INSERT INTO parking_records (car_plate, entry_time, spot_id) VALUES (%s, NOW(), %s)",
            (car_plate, spot_id)
        )

        #update spot
        cursor.execute(
            "UPDATE parking_spots SET status = 'occupied' WHERE spot_id = %s",
            (spot_id,)
        )

        conn.commit()

        return jsonify({
            "message": f"Car {car_plate} parked at spot {spot_id}"
        }), 201

    except Error as e:
        return error_response(str(e), 500)

    finally:
        cursor.close()
        conn.close()


# record exit

@app.route('/api/exit', methods=['POST'])
def record_exit():
    data = request.get_json()

    if not data:
        return error_response("Invalid JSON input")

    car_plate = data.get('car_plate')
    spot_id = data.get('spot_id')

    if not car_plate or not spot_id:
        return error_response("car_plate and spot_id are required")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        #check active
        cursor.execute("""
            SELECT * FROM parking_records 
            WHERE car_plate = %s AND spot_id = %s AND exit_time IS NULL
        """, (car_plate, spot_id))

        record = cursor.fetchone()

        if not record:
            return error_response("No active parking record found")

        #exit upd
        cursor.execute("""
            UPDATE parking_records 
            SET exit_time = NOW() 
            WHERE id = %s
        """, (record['id'],))

        #spot free
        cursor.execute(
            "UPDATE parking_spots SET status = 'free' WHERE spot_id = %s",
            (spot_id,)
        )

        conn.commit()

        return jsonify({
            "message": f"Car {car_plate} exited from spot {spot_id}"
        }), 200

    except Error as e:
        return error_response(str(e), 500)

    finally:
        cursor.close()
        conn.close()


#parked car now
@app.route('/api/current', methods=['GET'])
def current_cars():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT car_plate, spot_id, entry_time 
            FROM parking_records 
            WHERE exit_time IS NULL
        """)

        data = cursor.fetchall()

        return jsonify(data), 200

    except Error as e:
        return error_response(str(e), 500)

    finally:
        cursor.close()
        conn.close()



#history

@app.route('/api/history', methods=['GET'])
def history():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM parking_records 
            ORDER BY entry_time DESC
        """)

        data = cursor.fetchall()

        return jsonify(data), 200

    except Error as e:
        return error_response(str(e), 500)

    finally:
        cursor.close()
        conn.close()

#run

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
