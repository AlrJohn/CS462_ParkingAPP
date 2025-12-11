# Quick hardware test for HC-SR04 on Raspberry Pi 5
import lgpio
import time

TRIG, ECHO = 2, 3

# Open GPIO chip (Pi 5 uses gpiochip0)
h = lgpio.gpiochip_open(0)

# Set up pins
lgpio.gpio_claim_output(h, TRIG)
lgpio.gpio_claim_input(h, ECHO)

print("Testing HC-SR04 sensor on Raspberry Pi 5...")
print("TRIG: GPIO2 (pin 3)")
print("ECHO: GPIO3 (pin 5)")
print("Voltage divider: 5kΩ + 10kΩ")
print("\nTaking 5 measurements...\n")

try:
    for i in range(5):
        # Trigger pulse
        lgpio.gpio_write(h, TRIG, 0)
        time.sleep(0.000002)
        lgpio.gpio_write(h, TRIG, 1)
        time.sleep(0.00001)
        lgpio.gpio_write(h, TRIG, 0)
        
        # Wait for echo start
        timeout = time.time() + 0.1
        while lgpio.gpio_read(h, ECHO) == 0 and time.time() < timeout:
            pass
        pulse_start = time.time()
        
        # Wait for echo end
        timeout = time.time() + 0.1
        while lgpio.gpio_read(h, ECHO) == 1 and time.time() < timeout:
            pass
        pulse_end = time.time()
        
        duration = pulse_end - pulse_start
        distance = (duration * 34300) / 2
        
        print(f"Measurement {i+1}: {distance:.1f} cm")
        time.sleep(0.5)
        
    print("\n✓ Sensor test complete!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    lgpio.gpiochip_close(h)
