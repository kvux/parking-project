import time
try:
    import RPi.GPIO as GPIO
    IS_PI = True
except ImportError:
    IS_PI = False

# Pin Definitions
red_led_pin = 18
green_led_pin = 23

# Initialize GPIO only if on Pi
if IS_PI:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(red_led_pin, GPIO.OUT)
    GPIO.setup(green_led_pin, GPIO.OUT)

# Function to control LEDs based on parking spot status
def control_leds(is_occupied):
    if not IS_PI:
        return
    if is_occupied:
        GPIO.output(red_led_pin, GPIO.HIGH)
        GPIO.output(green_led_pin, GPIO.LOW)
    else:
        GPIO.output(red_led_pin, GPIO.LOW)
        GPIO.output(green_led_pin, GPIO.HIGH)

# Only run the loop when this file is run directly
if __name__ == "__main__":
    try:
        while True:
            is_occupied = False
            control_leds(is_occupied)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        if IS_PI:
            GPIO.cleanup()
