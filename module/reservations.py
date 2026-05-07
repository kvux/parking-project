from datetime import datetime, timedelta
import random
import string
import mysql.connector
from mysql.connector import Error
import os
from contextlib import contextmanager

# DB config using same pattern as app.py
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'parking_db')
}

def _get_raw_connection():
    return mysql.connector.connect(**db_config)

@contextmanager
def get_db(dictionary=True):
    """DB 연결 자동 관리 / Auto-manage DB connection"""
    conn = _get_raw_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield conn, cursor
    finally:
        cursor.close()
        conn.close()

def generate_reservation_code():
    """Generate unique 8-character reservation code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def init_reservation_table():
    """Create reservations table if not exists"""
    try:
        with get_db() as (conn, cursor):
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    spot_id INT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    status ENUM('pending', 'checked_in', 'expired', 'cancelled') DEFAULT 'pending',
                    reservation_code VARCHAR(10) UNIQUE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (spot_id) REFERENCES parking_spots(spot_id),
                    INDEX idx_status_time (status, start_time, end_time)
                )
            """)
            conn.commit()
        print("✅ Reservations table ready")
    except Error as e:
        print(f"❌ Error: {e}")

def create_reservation(user_id, start_time, end_time, spot_id=None):
    """
    Create a new reservation
    Returns: dict with reservation details or error
    """
    try:
        with get_db() as (conn, cursor):
            # Clean up expired reservations first
            cursor.execute("""
                UPDATE reservations SET status = 'expired'
                WHERE status = 'pending' AND end_time < NOW()
            """)
            conn.commit()

            # Check for overlapping reservations if specific spot requested
            if spot_id:
                cursor.execute("""
                    SELECT id FROM reservations 
                    WHERE spot_id = %s 
                    AND status IN ('pending', 'checked_in')
                    AND ((start_time <= %s AND end_time > %s) OR (start_time < %s AND end_time >= %s))
                """, (spot_id, start_time, start_time, end_time, end_time))
                if cursor.fetchone():
                    return {"error": "Spot already reserved for this time slot"}

            # Auto-assign spot if not specified
            if not spot_id:
                cursor.execute("""
                    SELECT ps.spot_id FROM parking_spots ps
                    WHERE ps.status = 'free'
                    AND ps.spot_id NOT IN (
                        SELECT r.spot_id FROM reservations r
                        WHERE r.status IN ('pending', 'checked_in')
                        AND ((r.start_time <= %s AND r.end_time > %s) OR (r.start_time < %s AND r.end_time >= %s))
                    )
                    LIMIT 1
                """, (start_time, start_time, end_time, end_time))
                available = cursor.fetchone()
                if not available:
                    return {"error": "No available spots for this time slot"}
                spot_id = available['spot_id']

            # Generate unique code
            for _ in range(10):
                code = generate_reservation_code()
                cursor.execute("SELECT id FROM reservations WHERE reservation_code = %s", (code,))
                if not cursor.fetchone():
                    break
            else:
                return {"error": "Failed to generate unique code"}

            # Insert reservation
            cursor.execute("""
                INSERT INTO reservations (user_id, spot_id, start_time, end_time, reservation_code)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, spot_id, start_time, end_time, code))
            conn.commit()

            return {
                "id": cursor.lastrowid,
                "reservation_code": code,
                "spot_id": spot_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "status": "pending"
            }
    except Error as e:
        return {"error": str(e)}

def checkin_reservation(code, car_plate):
    """Check in using reservation code"""
    try:
        with get_db() as (conn, cursor):
            cursor.execute("""
                SELECT * FROM reservations 
                WHERE reservation_code = %s AND status = 'pending'
            """, (code,))
            res = cursor.fetchone()

            if not res:
                return {"error": "Invalid or expired reservation code"}

            # Check if within check-in window (15 min before to 15 min after start)
            now = datetime.now()
            checkin_start = res['start_time'] - timedelta(minutes=15)
            checkin_end = res['start_time'] + timedelta(minutes=15)

            if not (checkin_start <= now <= checkin_end):
                return {"error": "Outside check-in window"}

            # Update reservation status
            cursor.execute("""
                UPDATE reservations SET status = 'checked_in' WHERE id = %s
            """, (res['id'],))
            
            # Create parking record for fee calculation on exit
            cursor.execute(
                "INSERT INTO parking_records (car_plate, entry_time, spot_id) VALUES (%s, NOW(), %s)",
                (car_plate, res['spot_id'])
            )
            conn.commit()

            return {
                "message": "Check-in successful",
                "spot_id": res['spot_id'],
                "car_plate": car_plate
            }
    except Error as e:
        return {"error": str(e)}

def cancel_reservation(reservation_id, user_id):
    """Cancel a pending reservation"""
    try:
        with get_db() as (conn, cursor):
            cursor.execute("""
                SELECT * FROM reservations 
                WHERE id = %s AND user_id = %s AND status = 'pending'
            """, (reservation_id, user_id))
            res = cursor.fetchone()

            if not res:
                return {"error": "Reservation not found or cannot be cancelled"}

            cursor.execute("""
                UPDATE reservations SET status = 'cancelled' WHERE id = %s
            """, (reservation_id,))
            conn.commit()

        return {"message": "Reservation cancelled successfully"}
    except Error as e:
        return {"error": str(e)}

def get_user_reservations(user_id):
    """Get all reservations for a user"""
    try:
        with get_db() as (_, cursor):
            cursor.execute("""
                SELECT * FROM reservations 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            return cursor.fetchall()
    except Error as e:
        return {"error": str(e)}
