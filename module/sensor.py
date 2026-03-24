import time
import logging
import requests

logger = logging.getLogger(__name__)

# How close (cm) before we consider a spot occupied
OCCUPIED_THRESHOLD_CM = 20
# How long between readings per spot (seconds)
POLL_INTERVAL = 1.0
# Your Flask server address
API_BASE_URL = "http://localhost:5000"

try:
    import RPi.GPIO as GPIO
    IS_PI = True
except ImportError:
    IS_PI = False
    logger.warning("RPi.GPIO not found — running in mock mode")

# Each spot: { spot_id: (TRIG_pin, ECHO_pin) }
SPOT_SENSOR_MAP = {
    1: (5, 6),
    2: (13, 19),
    3: (26, 20),
    4: (21, 16),
}

LED_PIN_MAP = {
    1: {"red": 18, "green": 23},
    2: {"red": 24, "green": 25},
    3: {"red": 8,  "green": 7},
    4: {"red": 12, "green": 11},
}


def setup_gpio():
    if not IS_PI:
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for spot_id, (trig, echo) in SPOT_SENSOR_MAP.items():
        GPIO.setup(trig, GPIO.OUT)
        GPIO.setup(echo, GPIO.IN)
    for spot_id, pins in LED_PIN_MAP.items():
        GPIO.setup(pins["red"],   GPIO.OUT)
        GPIO.setup(pins["green"], GPIO.OUT)


def read_distance_cm(trig, echo):
    """Fire HC-SR04 and return distance in cm. Returns None on timeout."""
    if not IS_PI:
        # Mock: return a random-ish value for testing
        import random
        return random.choice([10, 10, 10, 80, 80])  # mostly occupied

    GPIO.output(trig, False)
    time.sleep(0.02)

    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)

    timeout = time.time() + 0.04  # 40ms timeout
    while GPIO.input(echo) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return None

    timeout = time.time() + 0.04
    while GPIO.input(echo) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return None

    duration = pulse_end - pulse_start
    distance = (duration * 34300) / 2  # speed of sound
    return round(distance, 1)


def set_led(spot_id, is_occupied):
    """Red = occupied, Green = free."""
    if not IS_PI or spot_id not in LED_PIN_MAP:
        return
    pins = LED_PIN_MAP[spot_id]
    GPIO.output(pins["red"],   GPIO.HIGH if is_occupied else GPIO.LOW)
    GPIO.output(pins["green"], GPIO.LOW  if is_occupied else GPIO.HIGH)


def notify_api(spot_id, is_occupied):
    """Tell the Flask server about a status change."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/sensor/update",
            json={"spot_id": spot_id, "occupied": is_occupied},
            timeout=3
        )
        if resp.status_code == 200:
            logger.info(f"Spot {spot_id} → {'occupied' if is_occupied else 'free'} — API OK")
        else:
            logger.warning(f"Spot {spot_id} API returned {resp.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Spot {spot_id} API call failed: {e}")


def run_sensor_loop():
    """Main loop — runs forever on the Pi."""
    setup_gpio()
    # Track last known state to avoid spamming the API
    last_state = {spot_id: None for spot_id in SPOT_SENSOR_MAP}

    logger.info(f"Sensor loop started — monitoring {len(SPOT_SENSOR_MAP)} spots")

    try:
        while True:
            for spot_id, (trig, echo) in SPOT_SENSOR_MAP.items():
                distance = read_distance_cm(trig, echo)

                if distance is None:
                    logger.warning(f"Spot {spot_id}: sensor timeout")
                    continue

                is_occupied = distance < OCCUPIED_THRESHOLD_CM
                set_led(spot_id, is_occupied)

                # Only call the API if the state actually changed
                if is_occupied != last_state[spot_id]:
                    notify_api(spot_id, is_occupied)
                    last_state[spot_id] = is_occupied

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Sensor loop stopped")
    finally:
        if IS_PI:
            GPIO.cleanup()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_sensor_loop()
