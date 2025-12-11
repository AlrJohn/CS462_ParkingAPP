import lgpio as GPIO
import time

TRIG = 23  # Physical pin 16
ECHO = 24  # Physical pin 18

h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

def get_distance():
    # Clean trigger
    GPIO.gpio_write(h, TRIG, 0)
    time.sleep(0.5)  # Shorter delay

    # Send 10us pulse
    GPIO.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)
    GPIO.gpio_write(h, TRIG, 0)

    # Wait for ECHO to go HIGH (with timeout)
    timeout = time.time() + 0.5
    while GPIO.gpio_read(h, ECHO) == 0:
        if time.time() > timeout:
            print("  ✗ Timeout waiting for ECHO HIGH")
            return None
        pulse_start = time.time()

    # Wait for ECHO to go LOW (with timeout)
    timeout = time.time() + 0.5
    while GPIO.gpio_read(h, ECHO) == 1:
        if time.time() > timeout:
            print("  ✗ Timeout waiting for ECHO LOW")
            return None
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    
    return distance

if __name__ == "__main__":
    print("Testing HC-SR04 on GPIO 23 (TRIG) & 24 (ECHO)")
    print("Physical pins 16 & 18")
    print("=" * 60)
    
    try:
        for i in range(5):
            print(f"\nMeasurement {i+1}:")
            dist = get_distance()
            if dist is not None:
                print(f"  ✓ Distance: {dist:.2f} cm")
            else:
                print(f"  ✗ Failed to get reading")
            time.sleep(1)
        
        print("\n" + "=" * 60)
        print("If all measurements timeout, the sensor isn't responding.")
        print("Possible issues:")
        print("  1. Faulty HC-SR04 sensor")
        print("  2. TRIG/ECHO wires swapped")
        print("  3. Bad jumper wires")
        print("  4. Sensor not getting 5V power")

    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        GPIO.gpiochip_close(h)
