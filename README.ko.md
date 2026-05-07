# Smart Parking System (스마트 주차 시스템)

[영어](https://github.com/kvux/parking-project/blob/main/README.md)

## 개요
주차 자리, 차량 입출차, 주차 이력 관리를 위한 백엔드 API입니다.

## 주요 기능
- 주차 자리 상태 확인
- 차량 입차 (입차)
- 차량 출차 (출차)
- 중복 주차 방지
- 현재 주차 중인 차량 추적
- 주차 이력 확인
- 실시간 센서 기반 자리 업데이트
- 자리별 자동 LED 표시등

## 기술 스택
- Python (Flask)
- MySQL
- REST API
- Raspberry Pi + HC-SR04 센서
- Android 앱 (개발 중)

## API 엔드포인트

### 전체 자리 조회
GET /api/spots





### 이용 가능한 자리 조회
GET /api/spots/available

### 입차
POST /api/entry
```json
{
  "car_plate": "가1234",
  "spot_id": 1
}
```

### 출차
POST /api/exit
```json
{
  "car_plate": "가1234",
  "spot_id": 1
}
```

### 현재 주차 중인 차량 조회
GET /api/current

### 주차 이력 조회
GET /api/history?page=1&per_page=20

### 센서 업데이트
POST /api/sensor/update
```json
{
  "spot_id": 1,
  "occupied": true
}
```












### 사용자 등록
POST /register
```json
{
  "name": "홍길동",
  "email": "email@test.com",
  "password": "123456",
  "car_number": "12가 3456"
}
```

### 로그인
POST /login
```json
{
  "email": "email@test.com",
  "password": "123456"
}
```

### 전체 사용자 조회
GET /users

### 사용자 조회
GET /users/<id>

### 사용자 삭제
DELETE /users/<id>

### 서버 상태 확인
GET /health

## 실행 방법









































```bash
python -m venv venv
venv\Scripts\activate
pip install flask flask-cors flask-limiter flask-jwt-extended flask-sqlalchemy werkzeug mysql-connector-python python-dotenv requests
python app.py
```

### 센서 루프 (Raspberry Pi만 해당)
```bash
python module/sensor.py
```
