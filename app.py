from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import mysql.connector
from mysql.connector import Error
import os
import re
import logging
from datetime import datetime

#configuration
app = Flask(__name__)

# Enable CORS
CORS(app)

# rate limit
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# db config using env
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'), 
    'database': os.getenv('DB_NAME', 'parking_db')
}

# db func
def get_db_connection():
    """Create and return a database connection"""
    return mysql.connector.connect(**db_config)

def init_db():
    """Initialize database tables if they don't exist"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # create parking spot table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_spots (
                spot_id INT PRIMARY KEY,
                status ENUM('free', 'occupied') DEFAULT 'free'
            )
         """)
        
        # Create parking_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                car_plate VARCHAR(20) NOT NULL,
                entry_time DATETIME NOT NULL,
                exit_time DATETIME,
                spot_id INT NOT NULL,
                FOREIGN KEY (spot_id) REFERENCES parking_spots(spot_id),
                INDEX idx_car_plate (car_plate),
                INDEX idx_active (exit_time)
            )
        """)  
        
        # Insert default parking spots if table is empty
        cursor.execute("SELECT COUNT(*) FROM parking_spots")
        count = cursor.fetchone()[0]
        
        if count == 0:
            for i in range(1, 51):  # Create 50 parking spots
                cursor.execute("INSERT INTO parking_spots (spot_id) VALUES (%s)", (i,))
            logger.info(f"Created {50} default parking spots")
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Error as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

#helper function
def error_response(message, code=400):
    """Return standardized error response"""
    return jsonify({"error": message}), code

def validate_car_plate(car_plate):
    """Validate car plate format"""
    if not car_plate or not isinstance(car_plate, str):
        return False
    # Allow letters, numbers, hyphens, and spaces (adjust regex as needed)
    return bool(re.match(r'^[A-Z0-9\s-]+$', car_plate.strip().upper()))

#api end points

@app.route('/')
def home():
    return jsonify({
        "message": "Smart Parking System API is running",
        "version": "1.0.0",
        "docs": "/api/docs"
    })

@app.route('/api/docs', methods=['GET'])
def api_documentation():
    """API documentation endpoint"""
    return jsonify({
        "name": "Smart Parking System API",
        "version": "1.0.0",
        "endpoints": {
            "GET /api/spots": "Get all parking spots with their status",
            "GET /api/spots/available": "Get count of available parking spots",
            "POST /api/entry": "Record car entry (requires car_plate and spot_id)",
            "POST /api/exit": "Record car exit (requires car_plate and spot_id)",
            "GET /api/current": "Get list of currently parked cars",
            "GET /api/history": "Get parking history (supports pagination)",
            "GET /api/docs": "This documentation"
        },
        "rate_limits": "200 requests per day, 50 per hour",
        "contact": "admin@parkingsystem.com"
    })

@app.route('/api/spots', methods=['GET'])
def get_spots():
    """Get all parking spots"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT spot_id, status FROM parking_spots ORDER BY spot_id")
        spots = cursor.fetchall()
        
        logger.info(f"Retrieved {len(spots)} parking spots")

        return jsonify(spots), 200

    except Error as e:
        logger.error(f"Error getting spots: {str(e)}")
        return error_response(str(e), 500)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/spots/available', methods=['GET'])
def get_available_spots():
    """Get count of available parking spots"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM parking_spots WHERE status = 'free'")
        count = cursor.fetchone()[0]
        
        # get total spot
        cursor.execute("SELECT COUNT(*) FROM parking_spots")
        total = cursor.fetchone()[0]
        
        logger.info(f"Available spots: {count}/{total}")

        return jsonify({
            "available_spots": count,
            "total_spots": total,
            "percentage_free": round((count/total)*100, 2) if total > 0 else 0
        }), 200

    except Error as e:
        logger.error(f"Error getting available spots: {str(e)}")
        return error_response(str(e), 500)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/entry', methods=['POST'])
@limiter.limit("10 per minute")  # rate limit for entry point
def record_entry():
    """Record a car entering the parking lot"""
    data = request.get_json()

    if not data:
        return error_response("Invalid JSON input")

    # Sanitize inputs
    car_plate = data.get('car_plate', '').strip().upper()
    spot_id = data.get('spot_id')

    # Validate inputs
    if not car_plate or not spot_id:
        return error_response("car_plate and spot_id are required")
    
    if not validate_car_plate(car_plate):
        return error_response("Invalid car plate format. Use letters, numbers, and hyphens only.")
    
    # Validate spot_id is an integer
    try:
        spot_id = int(spot_id)
    except (ValueError, TypeError):
        return error_response("spot_id must be an integer")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if car already parked
        cursor.execute("""
            SELECT * FROM parking_records
            WHERE car_plate = %s AND exit_time IS NULL
        """, (car_plate,))
        active = cursor.fetchone()

        if active:
            logger.warning(f"Car {car_plate} attempted to park while already parked")
            return error_response("Car is already parked")

        # Check if spot exists and is free
        cursor.execute("SELECT status FROM parking_spots WHERE spot_id = %s", (spot_id,))
        spot = cursor.fetchone()

        if not spot:
            return error_response("Spot does not exist")

        if spot['status'] != 'free':
            return error_response("Spot already occupied")

        # Insert record
        cursor.execute(
            "INSERT INTO parking_records (car_plate, entry_time, spot_id) VALUES (%s, NOW(), %s)",
            (car_plate, spot_id)
        )

        # Update spot
        cursor.execute(
            "UPDATE parking_spots SET status = 'occupied' WHERE spot_id = %s",
            (spot_id,)
        )

        conn.commit()
        
        logger.info(f"Car {car_plate} parked at spot {spot_id}")

        return jsonify({
            "message": f"Car {car_plate} parked at spot {spot_id}",
            "entry_time": "Recorded successfully"
        }), 201

    except Error as e:
        logger.error(f"Entry error for car {car_plate}: {str(e)}")
        return error_response(str(e), 500)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/exit', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limiting for exit endpoint
def record_exit():
    """Record a car exiting the parking lot"""
    data = request.get_json()

    if not data:
        return error_response("Invalid JSON input")

    # Sanitize inputs
    car_plate = data.get('car_plate', '').strip().upper()
    spot_id = data.get('spot_id')

    if not car_plate or not spot_id:
        return error_response("car_plate and spot_id are required")

    # Validate spot_id is an integer
    try:
        spot_id = int(spot_id)
    except (ValueError, TypeError):
        return error_response("spot_id must be an integer")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check active record
        cursor.execute("""
            SELECT * FROM parking_records
            WHERE car_plate = %s AND spot_id = %s AND exit_time IS NULL
        """, (car_plate, spot_id))

        record = cursor.fetchone()

        if not record:
            logger.warning(f"Exit attempted for car {car_plate} with no active record")
            return error_response("No active parking record found")

        # Update exit
        cursor.execute("""
            UPDATE parking_records
            SET exit_time = NOW()
            WHERE id = %s
        """, (record['id'],))

        # Free spot
        cursor.execute(
            "UPDATE parking_spots SET status = 'free' WHERE spot_id = %s",
            (spot_id,)
        )

        conn.commit()
        
        # Calculate parking duration
        entry_time = record['entry_time']
        exit_time = datetime.now()
        duration = exit_time - entry_time
        hours = round(duration.total_seconds() / 3600, 2)
        
        logger.info(f"Car {car_plate} exited from spot {spot_id}. Parked for {hours} hours")

        return jsonify({
            "message": f"Car {car_plate} exited from spot {spot_id}",
            "parking_duration_hours": hours,
            "exit_time": exit_time.isoformat()
        }), 200

    except Error as e:
        logger.error(f"Exit error for car {car_plate}: {str(e)}")
        return error_response(str(e), 500)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/current', methods=['GET'])
def current_cars():
    """Get list of currently parked cars"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT car_plate, spot_id, entry_time,
                   TIMESTAMPDIFF(MINUTE, entry_time, NOW()) as minutes_parked
            FROM parking_records
            WHERE exit_time IS NULL
            ORDER BY entry_time DESC
        """)

        data = cursor.fetchall()
        
        logger.info(f"Retrieved {len(data)} currently parked cars")

        return jsonify({
            "count": len(data),
            "cars": data
        }), 200

    except Error as e:
        logger.error(f"Error getting current cars: {str(e)}")
        return error_response(str(e), 500)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
@app.route('/api/sensor/update', methods=['POST'])
def sensor_update():
    """Called by sensor.py when a spot's state changes."""
    data = request.get_json()
    if not data:
        return error_response("Invalid JSON")

    spot_id  = data.get('spot_id')
    occupied = data.get('occupied')

    if spot_id is None or occupied is None:
        return error_response("spot_id and occupied are required")

    try:
        spot_id = int(spot_id)
    except (ValueError, TypeError):
        return error_response("spot_id must be an integer")

    new_status = 'occupied' if occupied else 'free'

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT spot_id FROM parking_spots WHERE spot_id = %s", (spot_id,))
        if not cursor.fetchone():
            return error_response("Spot not found", 404)
        cursor.execute(
            "UPDATE parking_spots SET status = %s WHERE spot_id = %s",
            (new_status, spot_id)
        )
        conn.commit()
        logger.info(f"Sensor update: spot {spot_id} → {new_status}")
        return jsonify({"spot_id": spot_id, "status": new_status}), 200
    except Error as e:
        logger.error(f"Sensor update error: {e}")
        return error_response(str(e), 500)
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        
@app.route('/api/history', methods=['GET'])
def history():
    """Get parking history with pagination"""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Validate pagination
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
            
        offset = (page - 1) * per_page

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM parking_records")
        total = cursor.fetchone()['total']

        # Get paginated results
        cursor.execute("""
            SELECT * FROM parking_records
            ORDER BY entry_time DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))

        data = cursor.fetchall()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page

        logger.info(f"Retrieved history page {page}/{total_pages}")

        return jsonify({
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "records": data
        }), 200

    except Error as e:
        logger.error(f"Error getting history: {str(e)}")
        return error_response(str(e), 500)

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# ==================== MAIN ENTRY POINT ====================
if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start the app
    logger.info("Starting Smart Parking System API...")
    app.run(debug=True, host='0.0.0.0', port=5000)
