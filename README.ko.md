스마트 주차 시스템 (Smart Parking System)English개요실시간 센서 모니터링을 통해 주차 공간 관리, 차량 입/출차, 요금 계산 및 예약을 처리하는 백엔드 API 시스템입니다.주요 기능주차 상태 조회: 주차면의 실시간 점유 상태 확인입/출차 관리: 차량 입차 처리 및 출차 시 자동 요금 계산중복 주차 방지: 이미 점유된 자리에 대한 중복 주차 차단차량 추적: 현재 주차 중인 차량의 실시간 정보 조회주차 이력: 페이지네이션이 적용된 전체 주차 기록 열람하드웨어 연동: HC-SR04 초음파 센서를 활용한 실시간 상태 업데이트시각적 알림: 각 주차면별 LED 표시등 자동 제어사용자 인증: JWT 기반의 회원가입 및 로그인 시스템예약 시스템: 특정 시간대에 원하는 주차면 사전 예약로그 기록: 차단기 이벤트 데이터 저장 (CSV + JSON)기술 스택언어 및 프레임워크: Python (Flask 3.0)데이터베이스: MySQL통신: REST API하드웨어: Raspberry Pi + HC-SR04 초음파 센서클라이언트: Android 앱 (개발 중)프로젝트 구조app.py                # 메인 Flask API 서버
module/
  sensor.py           # 라즈베리 파이 센서 루프 (HC-SR04, LED 제어)
  led_controller.py   # LED 제어 유틸리티
  fee_calculator.py   # 주차 요금 계산 로직
  exit_entry.py       # 차단기 이벤트 로그 기록
  reservations.py     # 예약 시스템 로직
API 엔드포인트주차 공간 (Parking Spots)메서드엔드포인트설명인증GET/api/spots전체 주차면 상태 조회없음GET/api/spots/available이용 가능 주차면 수 및 점유율 조회없음입/출차 (Entry/Exit)메서드엔드포인트설명인증POST/api/entry차량 입차 {car_plate, spot_id}없음POST/api/exit차량 출차 → 요금 반환없음GET/api/current현재 주차 중인 차량 목록JWTGET/api/history주차 이력 조회 ?page=1&per_page=20JWT예약 시스템 (Reservations)메서드엔드포인트설명인증POST/api/reservations예약 생성 {start_time, end_time, spot_id?}JWTGET/api/reservations내 예약 목록 조회JWTPOST/api/reservations/<id>/checkin예약 기반 체크인JWTGET/api/reservations/verify/<code>예약 코드 검증 (차단기 전용)없음요금 및 인증 (Fee & Auth)메서드엔드포인트설명POST/api/calculate-fee예상 요금 미리보기POST/register회원가입 {name, email, password, car_number}POST/login로그인 및 JWT 토큰 발급요금 및 예약 규정기본 요금: 시간당 10,000 KRW (1시간 단위 올림 계산)회차 시간: 초기 5분 무료 주차 가능예약 체크인: 예약 시작 시간 전후 15분 이내에만 체크인 가능자동 배정: 특정 자리를 지정하지 않을 경우 사용 가능한 첫 번째 자리를 자동 배정실행 방법Bash# 가상환경 설정 및 라이브러리 설치
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 서버 실행
python app.py
센서 루프 실행 (라즈베리 파이 전용)Bashpython module/sensor.py
환경 변수 설정.env.example 파일을 복사하여 .env 파일을 생성한 후 아래 내용을 설정하세요:JWT_SECRET_KEY: 보안을 위한 JWT 비밀키SENSOR_API_KEY: 센서 데이터 전송용 API 키DB_HOST, DB_USER, DB_PASSWORD, DB_NAME: MySQL 연결 정보ALLOWED_ORIGIN: Android 앱과의 통신을 위한 CORS 설정 (선택 사항)
