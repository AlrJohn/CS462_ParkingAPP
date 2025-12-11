# Try slower, more conservative timing
import lgpio
import time

TRIG, ECHO = 17, 27

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, TRIG)
lgpio.gpio_claim_input(h, ECHO)

print("Testing with slower timing (GPIO 17 & 27)...")

try:
    for i in range(3):
        print(f"\nMeasurement {i+1}:")
        
        # Longer settling time
        lgpio.gpio_write(h, TRIG, 0)
        time.sleep(1)  # 1 second rest
        
        print(f"  ECHO before: {lgpio.gpio_read(h, ECHO)}")
        
        # Longer trigger pulse (some sensors need 15-20us)
        lgpio.gpio_write(h, TRIG, 1)
        time.sleep(0.00002)  # 20 microseconds instead of 10
        lgpio.gpio_write(h, TRIG, 0)
        
        # Give more time for echo to respond
        time.sleep(0.01)  # 10ms delay
        print(f"  ECHO after trigger: {lgpio.gpio_read(h, ECHO)}")
        
        # Standard measurement
        start_wait = time.time()
        timeout = time.time() + 1.0  # Longer timeout
        while lgpio.gpio_read(h, ECHO) == 0 and time.time() < timeout:
            pass
        
        if lgpio.gpio_read(h, ECHO) == 1:
            pulse_start = time.time()
            print(f"  ✓ ECHO went HIGH after {(pulse_start-start_wait)*1000:.1f}ms")
            
            timeout = time.time() + 1.0
            while lgpio.gpio_read(h, ECHO) == 1 and time.time() < timeout:
                pass
            pulse_end = time.time()
            
            duration = pulse_end - pulse_start
            distance = (duration * 34300) / 2
            print(f"  Pulse: {duration*1000:.3f}ms")
            print(f"  Distance: {distance:.1f} cm")
        else:
            print(f"  ✗ ECHO stayed LOW")
            
except Exception as e:
    print(f"Error: {e}")
finally:
    lgpio.gpiochip_close(h)
