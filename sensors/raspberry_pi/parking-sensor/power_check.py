# Check all connections systematically
import lgpio
import time

print("=" * 60)
print("COMPLETE HARDWARE CHECK")
print("=" * 60)

# Check multiple pin combinations
pin_tests = [
    (17, 27, "GPIO 17(TRIG) & 27(ECHO) - pins 11 & 13"),
    (27, 17, "GPIO 27(TRIG) & 17(ECHO) - pins 13 & 11 (swapped)"),
    (23, 24, "GPIO 23(TRIG) & 24(ECHO) - pins 16 & 18"),
    (22, 23, "GPIO 22(TRIG) & 23(ECHO) - pins 15 & 16"),
]

for trig, echo, desc in pin_tests:
    print(f"\nTesting: {desc}")
    try:
        h = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(h, trig)
        lgpio.gpio_claim_input(h, echo)
        
        # Clean trigger
        lgpio.gpio_write(h, trig, 0)
        time.sleep(0.1)
        
        echo_before = lgpio.gpio_read(h, echo)
        
        # Trigger
        lgpio.gpio_write(h, trig, 1)
        time.sleep(0.00001)
        lgpio.gpio_write(h, trig, 0)
        
        # Wait for echo
        timeout = time.time() + 0.1
        while lgpio.gpio_read(h, echo) == 0 and time.time() < timeout:
            pass
        
        if lgpio.gpio_read(h, echo) == 1:
            pulse_start = time.time()
            timeout = time.time() + 0.1
            while lgpio.gpio_read(h, echo) == 1 and time.time() < timeout:
                pass
            pulse_end = time.time()
            
            distance = ((pulse_end - pulse_start) * 34300) / 2
            print(f"  ✓ SUCCESS! Distance: {distance:.1f} cm")
        else:
            print(f"  ✗ No response (ECHO before: {echo_before}, after: {lgpio.gpio_read(h, echo)})")
        
        lgpio.gpiochip_close(h)
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        try:
            lgpio.gpiochip_close(h)
        except:
            pass

print("\n" + "=" * 60)
print("MANUAL CHECKS:")
print("1. Is VCC connected to 5V (physical pin 2 or 4)?")
print("2. Is GND connected to ground (physical pin 6, 9, 14, 20, etc.)?")
print("3. Is the HC-SR04 LED on (if it has one)?")
print("4. Try a different HC-SR04 sensor if available")
print("=" * 60)
