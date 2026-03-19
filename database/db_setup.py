import mysql.connector
import os

def get_connection():
    """Create and return a database connection"""
    #databse connection
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root"  # sql pw
    )
    return connection

def create_database():
    """Create the parking database if it doesn't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS parking_db")
        print("✅ Database 'parking_db' created or already exists")
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
    finally:
        cursor.close()
        conn.close()

def create_tables():
    """Create the basic tables"""
    #database
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="parking_db"
    )
    cursor = conn.cursor()
    
    #parking spot create
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_spots (
            spot_id INT PRIMARY KEY,
            status VARCHAR(20) DEFAULT 'free'
        )
    """)
    
    # insert spot
    for i in range(1, 5):
        cursor.execute("""
            INSERT IGNORE INTO parking_spots (spot_id, status) 
            VALUES (%s, 'free')
        """, (i,))
    
    # make record
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parking_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            car_plate VARCHAR(20),
            entry_time DATETIME,
            exit_time DATETIME,
          spot_id INT
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Table created")

if __name__ == "__main__":
    create_database()
    create_tables()
EOF
