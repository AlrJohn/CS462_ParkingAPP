# Single ultrasonic lane monitor for parking detection
# Hardware: HC-SR04 ultrasonic sensor
# Connections: TRIG=GPIO2 (pin3), ECHO=GPIO3 (pin5), VCC=5V (pin4), GND (pin6)
# WARNING: ECHO outputs 5V - use voltage divider to protect Pi GPIO (3.3V max)

import RPi.GPIO as GPIO
import time
from statistics import median

# ---------------- Pins (BCM numbering) ----------------
TRIG, ECHO = 2, 3  # Physical pins 3 and 5

# ---------------- Tuning ----------------
SAMPLE_INTERVAL = 0.04           # seconds between reads
MEDIAN_COUNT = 3                 # median-of-N for stability
CALIBRATION_SECONDS = 3.0        # time to learn empty-lane distance

# NEAR zone: very close (car entering from sensor side)
NEAR_MAX_CM = 100.0              # anything closer than this = NEAR

# FAR zone: cluster around the empty-lane distance
FAR_BAND_CM = 60.0               # +/- band around empty distance for FAR zone

# Debounce/hysteresis
ENTER_CONFIRM_SAMPLES = 3        # require N consecutive samples inside a zone to count
CLEAR_CONFIRM_SAMPLES = 5        # require N consecutive "clear" samples to reset
MAX_DISTANCE_CM = 10000.0        # sentinel for timeouts/out-of-range

# ---------------- GPIO setup ----------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(ECHO, GPIO.IN)

def distance_cm(timeout=0.03):
    """Measure distance using HC-SR04 ultrasonic sensor"""
    # 10us pulse
    GPIO.output(TRIG, False)
    time.sleep(0.000002)
    GPIO.output(TRIG, True)
    time.sleep(0.000010)
    GPIO.output(TRIG, False)

    # wait for echo start
    t0 = time.time()
    while GPIO.input(ECHO) == 0:
        if time.time() - t0 > timeout:
            return MAX_DISTANCE_CM
    pulse_start = time.time()

    # wait for echo end
    while GPIO.input(ECHO) == 1:
        if time.time() - pulse_start > timeout:
            return MAX_DISTANCE_CM
    pulse_end = time.time()

    dur = pulse_end - pulse_start
    return (dur * 343.0 * 100.0) / 2.0  # m/s -> cm (round trip /2)

def median_cm(n=MEDIAN_COUNT):
    """Take median of N distance readings for stability"""
    return median(distance_cm() for _ in range(n))

def calibrate_empty():
    """Calibrate empty-lane distance by sampling for several seconds"""
    print(f"Calibrating for {CALIBRATION_SECONDS:.1f}s… keep the lane clear.")
    t_end = time.time() + CALIBRATION_SECONDS
    samples = []
    while time.time() < t_end:
        samples.append(median_cm())
        time.sleep(SAMPLE_INTERVAL)
    empty = median(samples) if samples else 300.0
    print(f"Empty-lane distance ≈ {empty:.0f} cm")
    return empty

def classify_zone(d, empty_cm):
    """Return 'NEAR', 'FAR', or 'CLEAR' based on distance"""
    if d < NEAR_MAX_CM:
        return "NEAR"
    # FAR zone is near the empty distance
    if abs(d - empty_cm) <= FAR_BAND_CM:
        return "FAR"
    return "CLEAR"

def main():
    print("=" * 60)
    print("Parking Sensor Monitor - Ultrasonic HC-SR04")
    print("=" * 60)
    print(f"TRIG Pin: GPIO{TRIG} (Physical Pin 3)")
    print(f"ECHO Pin: GPIO{ECHO} (Physical Pin 5)")
    print("=" * 60)
    
    empty_cm = calibrate_empty()
    in_count = 0
    out_count = 0

    zone = "CLEAR"
    consecutive_in_zone = 0
    consecutive_clear = CLEAR_CONFIRM_SAMPLES  # start 'cleared'
    latched = False                            # prevents double counts

    print("\nMonitoring… (NEAR=IN, FAR=OUT)")
    print(f"NEAR< {NEAR_MAX_CM:.0f} cm | FAR≈ {empty_cm:.0f}±{FAR_BAND_CM:.0f} cm")
    print("Press Ctrl+C to stop\n")
    last_log = time.time()

    try:
        while True:
            d = median_cm()
            z = classify_zone(d, empty_cm)

            if z == "CLEAR":
                consecutive_clear += 1
                consecutive_in_zone = 0
                # Release latch after sustained CLEAR
                if consecutive_clear >= CLEAR_CONFIRM_SAMPLES:
                    latched = False
            else:
                consecutive_clear = 0
                consecutive_in_zone += 1

                # Count only on first confirmed entry into a zone
                if not latched and consecutive_in_zone >= ENTER_CONFIRM_SAMPLES:
                    if z == "NEAR":
                        in_count += 1
                        latched = True
                        print(f"🚗 CAR ENTERING  (IN={in_count})")
                    elif z == "FAR":
                        out_count += 1
                        latched = True
                        print(f"🚗 CAR EXITING   (OUT={out_count})")

            # Periodic status update
            now = time.time()
            if now - last_log > 0.5:
                last_log = now
                print(f"d={d:5.0f}cm  zone={z:<5}  IN={in_count}  OUT={out_count}  latched={int(latched)}")

            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print(f"Session Summary:")
        print(f"  Cars IN:  {in_count}")
        print(f"  Cars OUT: {out_count}")
        print(f"  Net:      {in_count - out_count}")
        print("=" * 60)
    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete. Sensor stopped.")

if __name__ == "__main__":
    main()
