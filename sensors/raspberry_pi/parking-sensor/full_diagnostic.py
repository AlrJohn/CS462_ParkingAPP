# Full diagnostic - check everything
import lgpio
import time

TRIG, ECHO = 2, 3

print("=" * 60)
print("FULL HC-SR04 DIAGNOSTIC")
print("=" * 60)

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, TRIG)
lgpio.gpio_claim_input(h, ECHO)

try:
    # Test 1: Control TRIG pin
    print("\n1. Testing TRIG pin control...")
    lgpio.gpio_write(h, TRIG, 0)
    time.sleep(0.1)
    print(f"   TRIG set to LOW: {lgpio.gpio_read(h, TRIG)}")
    
    lgpio.gpio_write(h, TRIG, 1)
    time.sleep(0.1)
    print(f"   TRIG set to HIGH: {lgpio.gpio_read(h, TRIG)}")
    
    lgpio.gpio_write(h, TRIG, 0)
    print(f"   TRIG set to LOW again: {lgpio.gpio_read(h, TRIG)}")
    
    # Test 2: Monitor ECHO for 2 seconds
    print("\n2. Monitoring ECHO pin for 2 seconds...")
    print("   (Move your hand in front of sensor)")
    end_time = time.time() + 2
    changes = 0
    last_state = lgpio.gpio_read(h, ECHO)
    
    while time.time() < end_time:
        current_state = lgpio.gpio_read(h, ECHO)
        if current_state != last_state:
            changes += 1
            print(f"   ECHO changed to: {current_state}")
            last_state = current_state
        time.sleep(0.01)
    
    print(f"   Total state changes: {changes}")
    if changes == 0:
        print("   ✗ ECHO never changed - possible wiring issue!")
    
    # Test 3: Send trigger and watch carefully
    print("\n3. Detailed trigger test...")
    lgpio.gpio_write(h, TRIG, 0)
    time.sleep(0.5)
    
    echo_before = lgpio.gpio_read(h, ECHO)
    print(f"   ECHO before trigger: {echo_before}")
    
    # Send 10us pulse
    lgpio.gpio_write(h, TRIG, 1)
    time.sleep(0.00001)
    lgpio.gpio_write(h, TRIG, 0)
    
    # Check ECHO state over time
    for ms in [1, 5, 10, 50, 100]:
        time.sleep(ms / 1000.0)
        echo_state = lgpio.gpio_read(h, ECHO)
        print(f"   ECHO at +{ms}ms: {echo_state}")
    
    print("\n4. Recommendation:")
    if changes == 0 and echo_before == 1:
        print("   ECHO is stuck HIGH - possible issues:")
        print("   - TRIG and ECHO wires might be swapped")
        print("   - Faulty sensor")
        print("   - Wrong pins (try GPIO 17 & 27 instead)")
    elif changes == 0 and echo_before == 0:
        print("   ECHO is stuck LOW - possible issues:")
        print("   - No power to sensor (check VCC/GND)")
        print("   - Faulty sensor")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
finally:
    lgpio.gpiochip_close(h)

print("=" * 60)
