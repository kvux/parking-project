```

## 환경 변수 (Environment Variables)
`.env.example` 파일을 `.env`로 복사한 후 다음 항목을 입력하세요:
- `JWT_SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"` 명령어로 생성
- `SENSOR_API_KEY`: `python -c "import secrets; print(secrets.token_hex(16))"` 명령어로 생성
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (데이터베이스 설정)
- `ALLOWED_ORIGIN` (Android 앱 통신을 위한 CORS 설정Since this is a technical README for a GitHub repository, the Korean version should be professional, clear, and use standard industry terminology (e.g., using "엔드포인트" for "Endpoint" and "요청" for "Request").

Here is the updated Korean version of your documentation:

---

# 스마트 주차 시스템 (Smart Parking System)

[English](https://github.com/kvux/parking-project/blob/main/README.md)

## 개요 (Overview)
실시간 센서 모니터링을 통해 주차 공간 관리, 차량 입/출차, 요금 계산 및 예약을 처리하는 백엔드 API 시스템입니다.

## 주요 기능 (Features)
- 주차 공간 상태 실시간 확인
- 차량 입차 및 출차 처리 (출차 시 자동 요금 계산)
- 중복 주차 방지 로직
- 현재 주차 중인 차량 추적
- 페이지네이션이 적용된 주차 이력 조회
- 초음파 센서(HC-SR04) 기반 실시간 주차면 업데이트
- 주차면별 LED 상태 표시등 자동 제어
- 사용자 등록 및 로그인 (JWT 인증)
- **예약 시스템** (특정 시간대 주차면 예약)
- **자동 요금 계산**
- 차단기 이벤트 로그 기록 (CSV + JSON)

## 기술 스택 (Tech Stack)
- Python (Flask 3.0)
- MySQL
- REST API
- Raspberry Pi + HC-SR04 센서
- Android 앱 *(개발 중)*

## 모듈 구조 (Module Structure)
```
app.py                # 메인 Flask API 서버
module/
  sensor.py           # 라즈베리 파이 센서 루프 (HC-SR04, LED 제어)
  led_controller.py   # LED 제어 유틸리티
  fee_calculator.py   # 주차 요금 계산 로직
  exit_entry.py       # 차단기 이벤트 로그 기록
  reservations.py     # 예약 시스템 로직
```

## API 엔드포인트 (API Endpoints)

### 주차 공간 (Parking Spots)
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|----------|-------------|------|
| GET | `/api/spots` | 전체 주차면 상태 조회 | 없음 |
| GET | `/api/spots/available` | 이용 가능 주차면 수 및 점유율 조회 | 없음 |

### 입/출차 (Entry/Exit)
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|----------|-------------|------|
| POST | `/api/entry` | 차량 입차 `{car_plate, spot_id}` | 없음 |
| POST | `/api/exit` | 차량 출차 → 요금 반환 | 없음 |
| GET | `/api/current` | 현재 주차 중인 차량 목록 | JWT |
| GET | `/api/history` | 주차 이력 조회 `?page=1&per_page=20` | JWT |

### 요금 계산기 (Fee Calculator)
| 메서드 | 엔드포인트 | 설명 |
|--------|----------|-------------|
| POST | `/api/calculate-fee` | 예상 요금 계산 `{entry_time, exit_time, discount_percent}` |

### 예약 (Reservations)
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|----------|-------------|------|
| POST | `/api/reservations` | 예약 생성 `{start_time, end_time, spot_id?}` | JWT |
| GET | `/api/reservations` | 내 예약 목록 조회 | JWT |
| POST | `/api/reservations/<id>/checkin` | 예약 기반 체크인 | JWT |
| POST | `/api/reservations/<id>/cancel` | 예약 취소 | JWT |
| GET | `/api/reservations/verify/<code>` | 예약 코드 확인 (차단기 전용) | 없음 |

### 인증 (Auth)
| 메서드 | 엔드포인트 | 설명 |
|--------|----------|-------------|
| POST | `/register` | 회원가입 `{name, email, password, car_number}` |
| POST | `/login` | 로그인 `{email, password}` → JWT 반환 |

### 센서 (Sensor)
| 메서드 | 엔드포인트 | 설명 |
|--------|----------|-------------|
| POST | `/api/sensor/update` | 센서 데이터 업데이트 `{spot_id, occupied}` + `X-Sensor-Key` 헤더 |

## 요금 규정 (Fee Rules)
- **요금**: 시간당 10,000원
- **회차 시간**: 초기 5분 무료
- **최소 요금**: 1시간 요금 부과 (올림 계산)
- **할인**: 0~100% 할인 지원

## 예약 규정 (Reservation Rules)
- 특정 날짜와 시간대를 지정하여 예약 가능
- 특정 주차면을 직접 선택하거나 시스템 자동 배정 선택 가능
- 체크인 가능 시간: 예약 시작 15분 전부터 15분 후까지
- 자동 배정 시 해당 시간대에 비어 있는 첫 번째 주차면을 할당함

## 실행 방법 (How to Run)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### 센서 루프 (라즈베리 파이 전용)
```bash
python module/sensor.py
```

## 환경 변수 (Environment Variables)
`.env.example` 파일을 `.env`로 복사한 후 다음 항목을 입력하세요:
- `JWT_SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"` 명령어로 생성
- `SENSOR_API_KEY`: `python -c "import secrets; print(secrets.token_hex(16))"` 명령어로 생성
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (데이터베이스 설정)
- `ALLOWED_ORIGIN` (Android 앱 통신을 위한 CORS 설정)
```
