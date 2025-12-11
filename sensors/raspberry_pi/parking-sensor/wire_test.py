# Test if we can control the pins at all
import lgpio
import time

h = lgpio.gpiochip_open(0)

# Test GPIO 17 (pin 11)
lgpio.gpio_claim_output(h, 17)
print("Testing GPIO 17 (pin 11) - should blink if wire is good")
print("Measure with multimeter or LED between pin 11 and GND")

for i in range(5):
    lgpio.gpio_write(h, 17, 1)
    print(f"  HIGH (3.3V) - {i+1}/5")
    time.sleep(0.5)
    lgpio.gpio_write(h, 17, 0)
    print(f"  LOW  (0V)")
    time.sleep(0.5)

lgpio.gpiochip_close(h)
print("\nIf you measured voltage changes, the Pi pins work")
print("If not, there's a wiring issue")
