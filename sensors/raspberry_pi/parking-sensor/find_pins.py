# Help identify which pin is which
import lgpio
import time

TRIG, ECHO = 17, 27

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, TRIG)
lgpio.gpio_claim_input(h, ECHO)

print("Pin identification test")
print("=" * 60)
print("Watch your sensor's pins while we test...\n")

try:
    print("Test 1: Pulsing what we THINK is TRIG (GPIO 17, pin 11)")
    print("        You should see activity on the sensor's TRIG pin")
    for i in range(5):
        lgpio.gpio_write(h, TRIG, 1)
        time.sleep(0.2)
        lgpio.gpio_write(h, TRIG, 0)
        time.sleep(0.2)
        print(f"  Pulse {i+1}/5")
    
    print("\nTest 2: Reading what we THINK is ECHO (GPIO 27, pin 13)")
    print(f"        Current ECHO value: {lgpio.gpio_read(h, ECHO)}")
    
    print("\nTest 3: Try swapped - pulse GPIO 27, read GPIO 17")
    lgpio.gpiochip_close(h)
    h = lgpio.gpiochip_open(0)
    lgpio.gpio_claim_output(h, 27)  # Swap: 27 as TRIG
    lgpio.gpio_claim_input(h, 17)   # Swap: 17 as ECHO
    
    print("        Taking measurement with swapped pins...")
    lgpio.gpio_write(h, 27, 0)
    time.sleep(0.5)
    lgpio.gpio_write(h, 27, 1)
    time.sleep(0.00001)
    lgpio.gpio_write(h, 27, 0)
    
    timeout = time.time() + 0.1
    while lgpio.gpio_read(h, 17) == 0 and time.time() < timeout:
        pass
    
    if lgpio.gpio_read(h, 17) == 1:
        pulse_start = time.time()
        print("        ✓ ECHO went HIGH! (pins were swapped)")
        
        timeout = time.time() + 0.1
        while lgpio.gpio_read(h, 17) == 1 and time.time() < timeout:
            pass
        pulse_end = time.time()
        
        distance = ((pulse_end - pulse_start) * 34300) / 2
        print(f"        Distance: {distance:.1f} cm")
        print("\n*** SWAP YOUR WIRES! ***")
    else:
        print("        ✗ Still no response with swapped pins")
        print("        Check physical connections")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    lgpio.gpiochip_close(h)

print("=" * 60)
