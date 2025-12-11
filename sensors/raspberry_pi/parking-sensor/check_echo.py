# Simple ECHO pin state checker
import lgpio
import time

TRIG, ECHO = 2, 3
h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, TRIG)
lgpio.gpio_claim_input(h, ECHO)

print("Checking ECHO pin behavior...")
print("Watch the ECHO state as we trigger the sensor:\n")

try:
    for i in range(3):
        print(f"Test {i+1}:")
        print(f"  ECHO before trigger: {lgpio.gpio_read(h, ECHO)}")
        
        # Send trigger
        lgpio.gpio_write(h, TRIG, 1)
        time.sleep(0.00001)
        lgpio.gpio_write(h, TRIG, 0)
        
        time.sleep(0.001)  # Small delay
        print(f"  ECHO after trigger:  {lgpio.gpio_read(h, ECHO)}")
        
        time.sleep(0.5)
        
except Exception as e:
    print(f"Error: {e}")
finally:
    lgpio.gpiochip_close(h)
