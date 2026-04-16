from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import os
import re
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

#configuration #구성
app = Flask(__name__)

# CORS 사용 / Enable CORS
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")
CORS(app, origins=[ALLOWED_ORIGIN])

# JWT 구성 (실패 시 기본값 없음) / JWT config — no insecure fallback
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', '')
jwt = JWTManager(app)

# Rate limit 상수 / Rate limit constants
ENTRY_EXIT_LIMIT = "10 per minute"  # 진입/종료 / Entry/exit
AUTH_LIMIT = "5 per minute"  # 인증 (엄격) / Auth (tighter)

# 요금 제한 / Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# 로깅 설정 / Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# env를 사용한 DB 구성 / DB config using env
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'parking_db')
}

# 컴파일된 정규식 (매 요청마다 컴파일 방지) / Compiled regexes for performance
_PLATE_RE = re.compile(r'^[A-Z0-9\s\-]+$')
_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


# 환경 변수 검증 / Environment validation
def _validate_env():
    """중요한 시크릿 검증 — 없으면 시작 실패 / Fail fast on missing secrets"""
    # JWT 시크릿 必须 설정 / JWT_SECRET_KEY must be set
    jwt_secret = os.getenv('JWT_SECRET_KEY', '')
    if not jwt_secret or jwt_secret == 'your-secret-key-change-this':
        raise RuntimeError(
            'JWT_SECRET_KEY is not set or is still the default placeholder. '
            'Set a strong random secret in your .env file before running.'
        )

    missing = [k for k in ("DB_USER", "DB_NAME") if not os.getenv(k)]
    if missing:
        logger.warning(
            'Missing environment variables: %s — falling back to defaults.',
            ", ".join(missing)
        )
    if not os.getenv("DB_PASSWORD"):
        logger.warning("DB_PASSWORD is empty. Do NOT use an empty password in production.")

    # 센서 API 키 없으면 경고 / Warn if sensor key not set
    sensor_key = os.getenv("SENSOR_API_KEY", "")
    if not sensor_key:
        logger.warning(
            "SENSOR_API_KEY is not set. The /api/sensor/update endpoint is unprotected."
        )


# Raw DB 연결 / Raw DB connection
def _get_raw_connection():
    return mysql.connector.connect(**db_config)


# DB 컨텍스트 매니저 / DB context manager
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


# DB 초기화 / Initialize DB
def init_db():
    try:
        with get_db(dictionary=False) as (conn, cursor):
            # 주차 공간 테이블 만들기 / Create parking spots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parking_spots (
                    spot_id INT PRIMARY KEY,
                    status ENUM('free', 'occupied') DEFAULT 'free'
                )
            """)

            # 주차_기록 테이블 만들기 / Create parking records table
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

            # 사용자 테이블 생성 / Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(80) NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    car_number VARCHAR(20) NOT NULL
                )
            """)

            # 테이블이 비어 있는 경우 기본 주차 공간 삽입 / Seed default parking spots
            cursor.execute("SELECT COUNT(*) FROM parking_spots")
            if cursor.fetchone()[0] == 0:
                cursor.executemany(
                    "INSERT INTO parking_spots (spot_id) VALUES (%s)",
                    [(i,) for i in range(1, 51)]
                )
                logger.info("Seeded 50 default parking spots.")

            conn.commit()
            logger.info("Database initialised successfully.")

    except Error as e:
        logger.error("Database initialisation error: %s", e)
        raise


# 도우미 함수 / Helper functions
def error_response(message, code=400):
    """표준화된 에러 응답 (내부 정보 노출 없음) / Sanitised error response"""
    return jsonify({"error": message}), code


def validate_car_plate(plate: str) -> bool:
    """차량 번호 형식 검증 / Validate car plate format"""
    if not plate or not isinstance(plate, str):
        return False
    return bool(_PLATE_RE.match(plate.strip().upper()))


def _parse_car_plate(data: dict):
    """차량 번호 파싱 및 검증 / Parse and validate car plate"""
    raw = data.get("car_plate", "")
    if not isinstance(raw, str):
        return None, "car_plate must be a string"
    plate = raw.strip().upper()
    if not plate:
        return None, "car_plate is required"
    if not validate_car_plate(plate):
        return None, "Invalid car plate format. Use letters, numbers, and hyphens only."
    return plate, None


def _parse_spot_id(data: dict):
    """spot_id 파싱 및 검증 / Parse and validate spot_id"""
    raw = data.get("spot_id")
    if raw is None:
        return None, "spot_id is required"
    try:
        return int(raw), None
    except (ValueError, TypeError):
        return None, "spot_id must be an integer"


def _check_sensor_key():
    """
    센서 API 키 검증 / Verify shared sensor API key on hardware-facing endpoints.
    X-Sensor-Key 헤더 필요 / Requires X-Sensor-Key header.
    """
    expected = os.getenv("SENSOR_API_KEY", "")
    provided = request.headers.get("X-Sensor-Key", "")
    if not expected or provided != expected:
        return False, error_response("Unauthorized", 401)
    return True, None


# API 엔드포인트 / API endpoints

@app.route('/')
def home():
    return jsonify({
        "message": "Smart Parking System API is running",
        "version": "1.2.0",
        "docs": "/api/docs"
    })


@app.route('/api/docs', methods=['GET'])
def api_documentation():
    """API 문서 엔드포인트 / API documentation endpoint"""
    return jsonify({
        "name": "Smart Parking System API",
        "version": "1.2.0",
        "endpoints": {
            "GET /api/spots": "Get all parking spots with their status",
            "GET /api/spots/available": "Get count of available parking spots",
            "POST /api/entry": "Record car entry (requires car_plate and spot_id)",
            "POST /api/exit": "Record car exit (requires car_plate and spot_id)",
            "GET /api/current": "Get list of currently parked cars (JWT required)",
            "GET /api/history": "Get parking history (JWT required)",
            "POST /api/sensor/update": "Sensor update (X-Sensor-Key header required)",
            "POST /register": "Register new user",
            "POST /login": "User login",
        },
        "rate_limits": "200/day · 50/hr; 10/min entry/exit; 5/min auth",
    })


@app.route("/api/spots", methods=["GET"])
def get_spots():
    """모든 주차 공간 조회 / Get all parking spots"""
    try:
        with get_db() as (_, cursor):
            cursor.execute("SELECT spot_id, status FROM parking_spots ORDER BY spot_id")
            spots = cursor.fetchall()
        logger.info("Retrieved %d parking spots.", len(spots))
        return jsonify(spots), 200
    except Error:
        logger.exception("Error retrieving spots.")
        return error_response("Could not retrieve spots.", 500)


@app.route("/api/spots/available", methods=["GET"])
def get_available_spots():
    """사용 가능한 주차 공간 수 조회 / Get count of available parking spots"""
    try:
        with get_db(dictionary=False) as (_, cursor):
            # 하나의 쿼리로 전체/빈 자리 조회 / Get total and free in one query
            cursor.execute("""
                SELECT
                    SUM(status = 'free') AS available,
                    COUNT(*) AS total
                FROM parking_spots
            """)
            row = cursor.fetchone()
            available = int(row[0] or 0)
            total = int(row[1] or 0)

        pct = round((available / total) * 100, 2) if total else 0
        logger.info("Available spots: %d / %d", available, total)
        return jsonify({
            "available_spots": available,
            "total_spots": total,
            "percentage_free": pct,
        }), 200
    except Error:
        logger.exception("Error retrieving available spots.")
        return error_response("Could not retrieve available spots.", 500)


@app.route("/api/entry", methods=["POST"])
@limiter.limit(ENTRY_EXIT_LIMIT)
def record_entry():
    """차량 진입 기록 / Record car entering the parking lot"""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.")

    car_plate, err = _parse_car_plate(data)
    if err:
        return error_response(err)

    spot_id, err = _parse_spot_id(data)
    if err:
        return error_response(err)

    try:
        with get_db() as (conn, cursor):
            # 트랜잭션 시작 / Start transaction
            conn.start_transaction()

            # 이미 주차되어 있는지 확인 / Check if car already parked
            cursor.execute(
                "SELECT id FROM parking_records WHERE car_plate = %s AND exit_time IS NULL",
                (car_plate,)
            )
            if cursor.fetchone():
                conn.rollback()
                logger.warning("Car %s attempted to park while already parked.", car_plate)
                return error_response("Car is already parked.")

            # 자리 확인 및 잠금 / Check and lock spot
            cursor.execute(
                "SELECT status FROM parking_spots WHERE spot_id = %s FOR UPDATE",
                (spot_id,)
            )
            spot = cursor.fetchone()
            if not spot:
                conn.rollback()
                return error_response("Spot does not exist.")
            if spot["status"] != "free":
                conn.rollback()
                return error_response("Spot is already occupied.")

            # 레코드 삽입 / Insert record
            cursor.execute(
                "INSERT INTO parking_records (car_plate, entry_time, spot_id) VALUES (%s, NOW(), %s)",
                (car_plate, spot_id)
            )
            # 자리 상태 업데이트 / Update spot status
            cursor.execute(
                "UPDATE parking_spots SET status = 'occupied' WHERE spot_id = %s",
                (spot_id,)
            )
            conn.commit()

        logger.info("Car %s parked at spot %d.", car_plate, spot_id)
        return jsonify({
            "message": f"Car {car_plate} parked at spot {spot_id}.",
            "entry_time": "Recorded successfully",
        }), 201

    except Error:
        logger.exception("Entry error for car %s.", car_plate)
        return error_response("Could not record entry. Please try again.", 500)


@app.route("/api/exit", methods=["POST"])
@limiter.limit(ENTRY_EXIT_LIMIT)
def record_exit():
    """차량 진출 기록 / Record car exiting the parking lot"""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.")

    # 차량 번호 검증 / Validate car plate
    car_plate, err = _parse_car_plate(data)
    if err:
        return error_response(err)

    spot_id, err = _parse_spot_id(data)
    if err:
        return error_response(err)

    try:
        with get_db() as (conn, cursor):
            conn.start_transaction()

            # 활성 기록 확인 / Check active record
            cursor.execute(
                """
                SELECT id, entry_time FROM parking_records
                WHERE car_plate = %s AND spot_id = %s AND exit_time IS NULL
                FOR UPDATE
                """,
                (car_plate, spot_id)
            )
            record = cursor.fetchone()
            if not record:
                conn.rollback()
                logger.warning("Exit attempted for %s with no active record.", car_plate)
                return error_response("No active parking record found.")

            # 진출 시간 업데이트 / Update exit time
            cursor.execute(
                "UPDATE parking_records SET exit_time = NOW() WHERE id = %s",
                (record["id"],)
            )
            # 자리 비우기 / Free spot
            cursor.execute(
                "UPDATE parking_spots SET status = 'free' WHERE spot_id = %s",
                (spot_id,)
            )
            conn.commit()

        # 주차 시간 계산 / Calculate parking duration
        entry_time = record["entry_time"]
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=timezone.utc)
        exit_time = datetime.now(timezone.utc)
        hours = round((exit_time - entry_time).total_seconds() / 3600, 2)

        logger.info("Car %s exited spot %d after %.2f hours.", car_plate, spot_id, hours)
        return jsonify({
            "message": f"Car {car_plate} exited from spot {spot_id}.",
            "parking_duration_hours": hours,
            "exit_time": exit_time.isoformat(),
        }), 200

    except Error:
        logger.exception("Exit error for car %s.", car_plate)
        return error_response("Could not record exit. Please try again.", 500)


@app.route("/api/current", methods=["GET"])
@jwt_required()
def current_cars():
    """현재 주차된 차량 목록 (JWT 필요) / Get list of currently parked cars"""
    try:
        with get_db() as (_, cursor):
            cursor.execute("""
                SELECT car_plate, spot_id, entry_time,
                       TIMESTAMPDIFF(MINUTE, entry_time, NOW()) AS minutes_parked
                FROM parking_records
                WHERE exit_time IS NULL
                ORDER BY entry_time DESC
            """)
            cars = cursor.fetchall()
        logger.info("Currently parked: %d cars.", len(cars))
        return jsonify({"count": len(cars), "cars": cars}), 200
    except Error:
        logger.exception("Error retrieving current cars.")
        return error_response("Could not retrieve current cars.", 500)


@app.route("/api/sensor/update", methods=["POST"])
def sensor_update():
    """센서 상태 업데이트 (X-Sensor-Key 필요) / Sensor update with API key auth"""
    ok, err = _check_sensor_key()
    if not ok:
        return err

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be valid JSON.")

    spot_id, err = _parse_spot_id(data)
    if err:
        return error_response(err)

    occupied = data.get("occupied")
    if not isinstance(occupied, bool):
        return error_response("occupied must be a boolean (true/false).")

    new_status = 'occupied' if occupied else 'free'

    try:
        with get_db() as (conn, cursor):
            conn.start_transaction()
            cursor.execute("SELECT spot_id FROM parking_spots WHERE spot_id = %s FOR UPDATE", (spot_id,))
            if not cursor.fetchone():
                conn.rollback()
                return error_response("Spot not found", 404)
            cursor.execute(
                "UPDATE parking_spots SET status = %s WHERE spot_id = %s",
                (new_status, spot_id)
            )
            conn.commit()
        logger.info("Sensor update: spot %d → %s", spot_id, new_status)
        return jsonify({"spot_id": spot_id, "status": new_status}), 200
    except Error:
        logger.exception("Sensor update error.")
        return error_response("Could not update sensor.", 500)


@app.route("/api/history", methods=["GET"])
@jwt_required()
def history():
    """주차 이력 조회 (JWT 필요) / Get parking history with pagination"""
    page = max(1, request.args.get("page", 1, type=int))
    per_page = request.args.get("per_page", 20, type=int)
    if per_page < 1 or per_page > 100:
        per_page = 20
    offset = (page - 1) * per_page

    try:
        # 총 개수 가져오기 / Get total count
        with get_db(dictionary=False) as (_, cnt_cursor):
            cnt_cursor.execute("SELECT COUNT(*) FROM parking_records")
            total = cnt_cursor.fetchone()[0]

        # 현재 페이지의 결과 가져오기 / Get results for the current page
        with get_db() as (_, cursor):
            cursor.execute(
                "SELECT * FROM parking_records ORDER BY entry_time DESC LIMIT %s OFFSET %s",
                (per_page, offset)
            )
            records = cursor.fetchall()

        # 총 페이지 계산 / Calculate total pages
        total_pages = max(1, (total + per_page - 1) // per_page)
        logger.info("History page %d / %d returned.", page, total_pages)
        return jsonify({
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "records": records,
        }), 200
    except Error:
        logger.exception("Error retrieving history.")
        return error_response("Could not retrieve history.", 500)


# 사용자 인증 / User authentication

@app.route("/register", methods=["POST"])
@limiter.limit(AUTH_LIMIT)
def register():
    """새 사용자 등록 (입력 검증 강화) / Register a new user with enhanced validation"""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Invalid JSON.")

    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    car_number = data.get('car_number', '').strip().upper()

    # 모든 필드 확인 / Verify all fields exist
    if not all([name, email, password, car_number]):
        return error_response("All fields are required: name, email, password, car_number.")

    # 이메일 형식 검증 / Validate email format
    if not _EMAIL_RE.match(email):
        return error_response("Invalid email format.")

    # 비밀번호 8자리 이상 (강화) / Password min 8 chars (strengthened)
    if len(password) < 8:
        return error_response("Password must be at least 8 characters.")

    # 차량 번호 검증 / Validate car number
    if not validate_car_plate(car_number):
        return error_response("Invalid car number format. Use letters, numbers, and hyphens only.")

    # 이름 길이 제한 (DB 열과 일치) / Cap name length to match DB column
    if len(name) > 80:
        return error_response("Name must be 80 characters or fewer.")

    try:
        with get_db() as (conn, cursor):
            # 이메일 중복 확인 / Check email redundancy
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return error_response("Email already registered.", 409)

            # 사용자 삽입 / Insert user
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, car_number) VALUES (%s, %s, %s, %s)",
                (name, email, generate_password_hash(password), car_number)
            )
            conn.commit()

        logger.info("New user registered: %s", email)
        return jsonify({"message": "User registered successfully.", "email": email}), 201
    except Error:
        logger.exception("Registration error.")
        return error_response("Could not register user. Please try again.", 500)


@app.route("/login", methods=["POST"])
@limiter.limit(AUTH_LIMIT)
def login():
    """사용자 로그인 (타이밍 공격 방지) / User login with timing attack prevention"""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Invalid JSON.")

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return error_response("Email and password are required.")

    try:
        with get_db() as (_, cursor):
            # 필요한 열만 선택 (SELECT * 금지) / Select only needed columns
            cursor.execute(
                "SELECT id, name, email, car_number, password_hash FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()

        # 타이밍 공격 방지: 사용자가 없어도 항상 해시 검증 / Timing attack prevention
        dummy_hash = generate_password_hash("dummy")
        pwd_ok = check_password_hash(
            user["password_hash"] if user else dummy_hash,
            password
        )
        if not user or not pwd_ok:
            return error_response("Invalid email or password.", 401)

        token = create_access_token(identity=str(user["id"]))
        logger.info("User logged in: %s", email)
        return jsonify({
            "token": token,
            "user": {
                "id": user['id'],
                "name": user['name'],
                "email": user['email'],
                "car_number": user['car_number']
            }
        }), 200
    except Error:
        logger.exception("Login error.")
        return error_response("Could not log in. Please try again.", 500)


# 주요 진입 지점 / Main entry point
if __name__ == "__main__":
    _validate_env()
    init_db()
    logger.info("Starting Smart Parking System API...")

    # 디버그 모드는 env 변수로만 활성화 / Debug is opt-in via env var only
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
