# Quick hardware test for HC-SR04
import RPi.GPIO as GPIO
import time

TRIG, ECHO = 2, 3

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(ECHO, GPIO.IN)

print("Testing HC-SR04 sensor...")
print("TRIG: GPIO2 (pin 3)")
print("ECHO: GPIO3 (pin 5)")
print("\nTaking 5 measurements...\n")

try:
    for i in range(5):
        # Trigger pulse
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)
        
        # Wait for echo
        timeout = time.time() + 0.1
        while GPIO.input(ECHO) == 0 and time.time() < timeout:
            pass
        pulse_start = time.time()
        
        timeout = time.time() + 0.1
        while GPIO.input(ECHO) == 1 and time.time() < timeout:
            pass
        pulse_end = time.time()
        
        duration = pulse_end - pulse_start
        distance = (duration * 34300) / 2
        
        print(f"Measurement {i+1}: {distance:.1f} cm")
        time.sleep(0.5)
        
    print("\n✓ Sensor test complete!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
finally:
    GPIO.cleanup()
