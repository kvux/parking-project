import RPi.GPIO as GPIO
import time

# Pin Definitions
red_led_pin = 18  # GPIO pin for red LED
green_led_pin = 23  # GPIO pin for green LED

# Initialize GPIO
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
GPIO.setup(red_led_pin, GPIO.OUT)
GPIO.setup(green_led_pin, GPIO.OUT)

# Function to control LEDs based on parking spot status

def control_leds(is_occupied):
    if is_occupied:
        GPIO.output(red_led_pin, GPIO.HIGH)  # Turn on red LED
        GPIO.output(green_led_pin, GPIO.LOW)  # Turn off green LED
    else:
        GPIO.output(red_led_pin, GPIO.LOW)  # Turn off red LED
        GPIO.output(green_led_pin, GPIO.HIGH)  # Turn on green LED

# Example usage
try:
    while True:
        # Simulating parking spot status (replace this with actual logic)
        is_occupied = False  # Change to True or False based on your logic
        control_leds(is_occupied)
        time.sleep(1)  # Check every second

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()  # Clean up GPIO on exit
