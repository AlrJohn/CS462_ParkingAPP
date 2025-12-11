import lgpio as GPIO
import time

TRIG = 23
ECHO = 24

h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

def get_distance():
    GPIO.gpio_write(h, TRIG, 0)
    time.sleep(2)
    print("pulsing")

    GPIO.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)
    GPIO.gpio_write(h, TRIG, 0)
    
    print("timing")
    while GPIO.gpio_read(h, ECHO) == 0:
        pulse_start = time.time()

    print("waiting for high")
    while GPIO.gpio_read(h, ECHO) == 1:
        pulse_end = time.time()
    
    print("calculating")
    pulse_duration = pulse_end - pulse_start  # FIXED: was missing this line
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    
    return distance  # FIXED: was missing return statement

if __name__ == "__main__":
    print("running")
    try:
        while True:
            dist = get_distance()
            print("Dist: {:.2f} cm".format(dist))  # FIXED: was "fist" instead of "dist"
            time.sleep(5)

    except KeyboardInterrupt:
        print("Stopped by user")
        GPIO.gpiochip_close(h)
