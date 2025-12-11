#!/usr/bin/env python3
"""
Arduino UART Reader Test Script (GPIO Serial)
Reads ultrasonic sensor data from Arduino via GPIO serial pins (UART)
No USB required - uses direct GPIO connection
"""

import serial
import time
import sys
import os


def check_uart_available():
    """Check if UART device exists and is accessible."""
    uart_device = '/dev/ttyAMA0'

    if not os.path.exists(uart_device):
        print(f"[ERROR] {uart_device} does not exist!")
        print("\nTroubleshooting:")
        print("  1. Run setup script: ./setup_uart.sh")
        print("  2. Reboot: sudo reboot")
        print("  3. Check wiring:")
        print("     Arduino TX → Pi GPIO 15 (pin 10)")
        print("     Arduino RX → Pi GPIO 14 (pin 8)")
        print("     Arduino GND → Pi GND (pin 6)")
        return False

    # Check permissions
    if not os.access(uart_device, os.R_OK | os.W_OK):
        print(f"[ERROR] No permission to access {uart_device}")
        print("\nFix permissions with:")
        print("  sudo chmod 666 /dev/ttyAMA0")
        print("  OR add user to dialout group:")
        print("  sudo usermod -a -G dialout $USER")
        print("  Then log out and back in")
        return False

    return True


def read_arduino_uart(uart_device='/dev/ttyAMA0', baud_rate=9600):
    """
    Read data from Arduino via UART (GPIO serial pins).

    Args:
        uart_device: UART device path (default: '/dev/ttyAMA0' for Pi 5)
        baud_rate: Baud rate for serial communication (default: 9600)
    """
    try:
        # Open serial connection to UART
        ser = serial.Serial(
            port=uart_device,
            baudrate=baud_rate,
            timeout=1,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )

        print(f"\n{'='*50}")
        print(f"Connected to Arduino via UART")
        print(f"Device: {uart_device}")
        print(f"Baud Rate: {baud_rate}")
        print(f"{'='*50}")
        print("Reading data... (Press Ctrl+C to stop)\n")

        # Wait a moment for Arduino to stabilize
        time.sleep(1)

        # Clear any initial garbage data
        ser.reset_input_buffer()

        line_count = 0

        while True:
            # Read a line from Arduino
            if ser.in_waiting > 0:
                try:
                    # Read and decode the line
                    line = ser.readline().decode('utf-8').strip()

                    if line:  # Only print non-empty lines
                        line_count += 1
                        timestamp = time.strftime("%H:%M:%S")
                        print(f"[{timestamp}] #{line_count}: {line}")

                except UnicodeDecodeError:
                    # Handle any decoding errors
                    print("[ERROR] Could not decode data")
                except Exception as e:
                    print(f"[ERROR] Reading error: {e}")

            # Small delay to prevent CPU spinning
            time.sleep(0.01)

    except serial.SerialException as e:
        print(f"\n[ERROR] Serial connection error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check UART is enabled: ls -l /dev/ttyAMA0")
        print("  2. Check wiring:")
        print("     Arduino TX → Pi GPIO 15 (pin 10)")
        print("     Arduino RX → Pi GPIO 14 (pin 8)")
        print("     Arduino GND → Pi GND (pin 6)")
        print("  3. Make sure Arduino is powered (USB or external)")
        print("  4. Verify Arduino code is uploading Serial.println() data")
        print("  5. Run setup: ./setup_uart.sh && sudo reboot")
        return False

    except KeyboardInterrupt:
        print("\n\nStopped by user")
        return True

    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial connection closed")


def main():
    print("=" * 50)
    print("Arduino UART (GPIO) Reader Test")
    print("=" * 50)
    print("")
    print("This script reads Arduino data via GPIO pins,")
    print("bypassing USB entirely.")
    print("")

    # Check if UART is available
    if not check_uart_available():
        sys.exit(1)

    # Allow manual device override via command line
    uart_device = '/dev/ttyAMA0'
    if len(sys.argv) > 1:
        uart_device = sys.argv[1]
        print(f"Using manually specified device: {uart_device}")

    # Baud rate can be specified as second argument
    baud_rate = 9600
    if len(sys.argv) > 2:
        try:
            baud_rate = int(sys.argv[2])
            print(f"Using baud rate: {baud_rate}")
        except ValueError:
            print(f"Invalid baud rate: {sys.argv[2]}, using default 9600")

    print("")
    print("Wiring Check:")
    print("  Arduino TX (pin 1)  →  Pi GPIO 15 (Physical pin 10)")
    print("  Arduino RX (pin 0)  →  Pi GPIO 14 (Physical pin 8)")
    print("  Arduino GND         →  Pi GND (Physical pin 6)")
    print("  Arduino USB/VIN     →  Power source (5V)")
    print("")

    # Start reading
    read_arduino_uart(uart_device, baud_rate)


if __name__ == "__main__":
    main()
