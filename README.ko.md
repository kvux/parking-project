# 스마트 주차 시스템

[English](https://github.com/kvux/parking-project/blob/main/README.md)

## 개요
주차 공간 관리, 차량 입/출차, 요금 계산, 실시간 센서 모니터링 및 예약을 위한 백엔드 API입니다.

## 기능
- 주차 공간 상태 조회
- 차량 입차 / 출차 (자동 요금 계산)
- 중복 주차 방지
- 현재 주차된 차량 조회
- 페이지네이션 지원 주차 이력 조회
- HC-SR04 센서 기반 실시간 주차 공간 업데이트
- 공간별 자동 LED 표시
- 사용자 회원가입 및 로그인 (JWT)
- **예약 시스템** (특정 시간대 주차 공간 예약)
- **자동 요금 계산**
- 차단기 이벤트 로깅 (CSV + JSON)

## 기술 스택
- Python (Flask 3.0)
- MySQL
- REST API
- Raspberry Pi + HC-SR04 센서
- Android 앱 *(개발 중)*

## 모듈 구조
app.py # 메인 Flask API 서버 module/ sensor.py # Pi 센서 루프 (HC-SR04, LED 제어) led_controller.py # LED 제어 유틸리티 fee_calculator.py # 주차 요금 계산 exit_entry.py # 차단기 이벤트 로깅 reservations.py # 예약 시스템 로직


## API 엔드포인트

### 주차 공간
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/api/spots` | 전체 주차 공간 조회 | 없음 |
| GET | `/api/spots/available` | 사용 가능 공간 수 + % 조회 | 없음 |

### 입차/출차
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/api/entry` | 차량 입차 `{car_plate, spot_id}` | 없음 |
| POST | `/api/exit` | 차량 출차 → 요금 반환 | 없음 |
| GET | `/api/current` | 현재 주차된 차량 목록 | JWT |
| GET | `/api/history` | 주차 이력 `?page=1&per_page=20` | JWT |

### 요금 계산
| 메서드 | 엔드포인트 | 설명 |
|--------|----------|------|
| POST | `/api/calculate-fee` | 요금 미리보기 `{entry_time, exit_time, discount_percent}` |

### 예약
| 메서드 | 엔드포인트 | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/api/reservations` | 예약 생성 `{start_time, end_time, spot_id?}` | JWT |
| GET | `/api/reservations` | 내 예약 목록 | JWT |
| POST | `/api/reservations/<id>/checkin` | 예약으로 체크인 | JWT |
| POST | `/api/reservations/<id>/cancel` | 예약 취소 | JWT |
| GET | `/api/reservations/verify/<code>` | 예약 코드 확인 (게이트) | 없음 |

### 인증
| 메서드 | 엔드포인트 | 설명 |
|--------|----------|------|
| POST | `/register` | 회원가입 `{name, email, password, car_number}` |
| POST | `/login` | 로그인 `{email, password}` → JWT 반환 |

### 센서
| 메서드 | 엔드포인트 | 설명 |
|--------|----------|------|
| POST | `/api/sensor/update` | 센서 업데이트 `{spot_id, occupied}` + `X-Sensor-Key` 헤더 |

## 요금 규칙
- **요율**: 시간당 10,000원
- **무료 시간**: 최초 5분 무료
- **최소 요금**: 1시간 (올림)
- **할인**: 지원 (0-100%)

## 예약 규칙
- 특정 날짜/시간대 예약 가능
- 특정 공간 선택 또는 시스템 자동 배정
- 체크인 가능 시간: 시작 시간 기준 15분 전 ~ 15분 후
- 자동 배정: 해당 시간대에 사용 가능한 첫 번째 공간 배정

## 실행 방법
python module/sensor.py
환경 변수
.env.example을 .env로 복사 후 입력:

JWT_SECRET_KEY (필수) — 생성: python -c "import secrets; print(secrets.token_hex(32))"
SENSOR_API_KEY (필수) — 생성: python -c "import secrets; print(secrets.token_hex(16))"
DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
ALLOWED_ORIGIN (Android 앱 CORS origin)
