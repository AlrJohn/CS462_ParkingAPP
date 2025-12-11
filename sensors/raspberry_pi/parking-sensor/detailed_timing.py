# Detailed timing diagnostic
import lgpio
import time

TRIG, ECHO = 17, 27

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, TRIG)
lgpio.gpio_claim_input(h, ECHO)

print("Detailed timing test with GPIO 17 & 27")
print("=" * 60)

try:
    for i in range(3):
        print(f"\nMeasurement {i+1}:")
        
        # Ensure clean state
        lgpio.gpio_write(h, TRIG, 0)
        time.sleep(0.5)  # Longer settling time
        
        echo_initial = lgpio.gpio_read(h, ECHO)
        print(f"  Initial ECHO state: {echo_initial}")
        
        # Send trigger pulse
        lgpio.gpio_write(h, TRIG, 1)
        time.sleep(0.00001)  # 10 microseconds
        lgpio.gpio_write(h, TRIG, 0)
        
        # Wait for ECHO to go HIGH
        timeout_start = time.time()
        timeout = timeout_start + 0.5
        while lgpio.gpio_read(h, ECHO) == 0 and time.time() < timeout:
            pass
        
        if lgpio.gpio_read(h, ECHO) == 0:
            print(f"  ✗ ECHO never went HIGH (timeout)")
            continue
            
        pulse_start = time.time()
        wait_high = pulse_start - timeout_start
        print(f"  ECHO went HIGH after {wait_high*1000:.3f} ms")
        
        # Wait for ECHO to go LOW
        timeout = time.time() + 0.5
        while lgpio.gpio_read(h, ECHO) == 1 and time.time() < timeout:
            pass
        
        pulse_end = time.time()
        pulse_duration = pulse_end - pulse_start
        
        print(f"  Pulse duration: {pulse_duration*1000:.3f} ms")
        
        distance = (pulse_duration * 34300) / 2
        print(f"  Distance: {distance:.1f} cm")
        
        if pulse_duration < 0.000001:  # Less than 1 microsecond
            print(f"  ✗ Pulse too short - likely still a wiring issue")
        elif distance < 2:
            print(f"  ✗ Distance too small - check sensor placement")
        elif distance > 400:
            print(f"  ✗ Distance too large - possible timeout")
        else:
            print(f"  ✓ Distance looks good!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    lgpio.gpiochip_close(h)
    
print("\n" + "=" * 60)
