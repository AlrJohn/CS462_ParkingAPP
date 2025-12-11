# Test with GPIO 17 (pin 11) and GPIO 27 (pin 13)
import lgpio
import time

TRIG, ECHO = 17, 27  # Physical pins 11 and 13

h = lgpio.gpiochip_open(0)
lgpio.gpio_claim_output(h, TRIG)
lgpio.gpio_claim_input(h, ECHO)

print("Testing with GPIO 17 (TRIG, pin 11) & GPIO 27 (ECHO, pin 13)")
print("Taking 5 measurements...\n")

try:
    for i in range(5):
        lgpio.gpio_write(h, TRIG, 0)
        time.sleep(0.002)
        lgpio.gpio_write(h, TRIG, 1)
        time.sleep(0.00001)
        lgpio.gpio_write(h, TRIG, 0)
        
        timeout = time.time() + 0.1
        while lgpio.gpio_read(h, ECHO) == 0 and time.time() < timeout:
            pass
        pulse_start = time.time()
        
        timeout = time.time() + 0.1
        while lgpio.gpio_read(h, ECHO) == 1 and time.time() < timeout:
            pass
        pulse_end = time.time()
        
        duration = pulse_end - pulse_start
        distance = (duration * 34300) / 2
        
        print(f"{i+1}. {distance:.1f} cm")
        time.sleep(0.3)
        
except Exception as e:
    print(f"Error: {e}")
finally:
    lgpio.gpiochip_close(h)
