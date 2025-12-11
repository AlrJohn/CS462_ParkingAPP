# Final comprehensive hardware test
import lgpio as GPIO
import time

TRIG = 23
ECHO = 24

h = GPIO.gpiochip_open(0)
GPIO.gpio_claim_output(h, TRIG)
GPIO.gpio_claim_input(h, ECHO)

print("=" * 60)
print("FINAL HARDWARE DIAGNOSTIC")
print("=" * 60)
print("\nWiring verified:")
print("  HC-SR04 VCC  → Pi 5V (pin 2)")
print("  HC-SR04 TRIG → Pi GPIO 23 (pin 16)")
print("  HC-SR04 ECHO → Pi GPIO 24 (pin 18)")
print("  HC-SR04 GND  → Pi GND (pin 6)")
print("\n" + "=" * 60)

try:
    # Test 1: Can we control TRIG?
    print("\n1. Testing TRIG control...")
    GPIO.gpio_write(h, TRIG, 0)
    time.sleep(0.1)
    trig_low = GPIO.gpio_read(h, TRIG)
    GPIO.gpio_write(h, TRIG, 1)
    time.sleep(0.1)
    trig_high = GPIO.gpio_read(h, TRIG)
    GPIO.gpio_write(h, TRIG, 0)
    
    print(f"   TRIG LOW: {trig_low}, TRIG HIGH: {trig_high}")
    if trig_low == 0 and trig_high == 1:
        print("   ✓ TRIG pin is working")
    else:
        print("   ✗ TRIG pin control failed")
    
    # Test 2: Monitor ECHO for any activity
    print("\n2. Monitoring ECHO for 3 seconds...")
    print("   (Trigger sensor and watch for ANY change)")
    
    changes = []
    last_state = GPIO.gpio_read(h, ECHO)
    print(f"   Initial ECHO state: {last_state}")
    
    # Send 10 triggers over 3 seconds
    for i in range(10):
        GPIO.gpio_write(h, TRIG, 1)
        time.sleep(0.00001)
        GPIO.gpio_write(h, TRIG, 0)
        
        # Monitor for 300ms after each trigger
        for j in range(30):
            current = GPIO.gpio_read(h, ECHO)
            if current != last_state:
                changes.append((i, current))
                print(f"   ECHO changed to {current} after trigger {i+1}")
                last_state = current
            time.sleep(0.01)
    
    if len(changes) == 0:
        print("\n   ✗ ECHO NEVER CHANGED STATE")
        print("\n" + "=" * 60)
        print("DIAGNOSIS: SENSOR NOT RESPONDING")
        print("=" * 60)
        print("\nLikely causes (in order):")
        print("  1. ⚠️  FAULTY HC-SR04 SENSOR (most common)")
        print("  2. 🔌 Bad jumper wires (try different wires)")
        print("  3. 🍞 Poor breadboard connections")
        print("  4. 🔋 Sensor not getting 5V (measure with multimeter)")
        print("\nRecommended actions:")
        print("  → Try a DIFFERENT HC-SR04 sensor")
        print("  → Replace ALL jumper wires")
        print("  → Test with a multimeter: VCC should be ~5V")
    else:
        print(f"\n   ✓ ECHO changed {len(changes)} times - sensor is responding!")
        print("   Attempting distance measurement...")
        
        # If we detected changes, try a measurement
        GPIO.gpio_write(h, TRIG, 0)
        time.sleep(0.5)
        GPIO.gpio_write(h, TRIG, 1)
        time.sleep(0.00001)
        GPIO.gpio_write(h, TRIG, 0)
        
        timeout = time.time() + 0.1
        while GPIO.gpio_read(h, ECHO) == 0 and time.time() < timeout:
            pass
        
        if GPIO.gpio_read(h, ECHO) == 1:
            pulse_start = time.time()
            while GPIO.gpio_read(h, ECHO) == 1:
                pass
            pulse_end = time.time()
            distance = ((pulse_end - pulse_start) * 34300) / 2
            print(f"   Distance: {distance:.1f} cm")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    GPIO.gpiochip_close(h)

print("\n" + "=" * 60)
