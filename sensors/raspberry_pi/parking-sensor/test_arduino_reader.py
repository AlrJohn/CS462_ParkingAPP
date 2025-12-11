#!/usr/bin/env python3
"""
Arduino USB Reader Test Script
Reads ultrasonic sensor data from Arduino via USB serial connection
"""

import serial
import serial.tools.list_ports
import time
import sys


def find_arduino_port():
    """
    Auto-detect Arduino USB port.
    Returns the port name if found, None otherwise.
    """
    print("Scanning for Arduino...")
    ports = serial.tools.list_ports.comports()

    for port in ports:
        print(f"Found port: {port.device} - {port.description}")
        # Arduino typically shows up as ttyACM0 or ttyUSB0
        if 'ACM' in port.device or 'USB' in port.device:
            print(f"Arduino likely at: {port.device}")
            return port.device

    # If no Arduino-specific port found, try common defaults
    common_ports = ['/dev/ttyACM0', '/dev/ttyUSB0', '/dev/ttyACM1', '/dev/ttyUSB1']
    for port in common_ports:
        try:
            # Try to open the port briefly to test
            test_serial = serial.Serial(port, 9600, timeout=1)
            test_serial.close()
            print(f"Found working port: {port}")
            return port
        except (serial.SerialException, FileNotFoundError):
            continue

    return None


def read_arduino(port, baud_rate=9600):
    """
    Read data from Arduino via serial connection.

    Args:
        port: Serial port name (e.g., '/dev/ttyACM0')
        baud_rate: Baud rate for serial communication (default: 9600)
    """
    try:
        # Open serial connection
        ser = serial.Serial(port, baud_rate, timeout=1)
        print(f"\n{'='*50}")
        print(f"Connected to Arduino on {port} at {baud_rate} baud")
        print(f"{'='*50}")
        print("Reading data... (Press Ctrl+C to stop)\n")

        # Wait a moment for Arduino to reset after serial connection
        time.sleep(2)

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
        print("Make sure:")
        print("  1. Arduino is plugged into USB")
        print("  2. You have permission to access the port (try: sudo usermod -a -G dialout $USER)")
        print("  3. No other program is using the port")
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
    print("Arduino USB Reader Test")
    print("=" * 50)

    # Auto-detect Arduino port
    port = find_arduino_port()

    if port is None:
        print("\n[ERROR] Could not find Arduino!")
        print("\nAvailable ports:")
        ports = serial.tools.list_ports.comports()
        if ports:
            for p in ports:
                print(f"  - {p.device}: {p.description}")
        else:
            print("  No serial ports found!")

        print("\nTroubleshooting:")
        print("  1. Check Arduino is plugged into USB")
        print("  2. Check USB cable supports data transfer (not power-only)")
        print("  3. Try: ls -l /dev/ttyACM* /dev/ttyUSB*")
        print("  4. Try running with sudo if permission denied")
        sys.exit(1)

    # Allow manual port override via command line
    if len(sys.argv) > 1:
        port = sys.argv[1]
        print(f"Using manually specified port: {port}")

    # Baud rate can be specified as second argument
    baud_rate = 9600
    if len(sys.argv) > 2:
        try:
            baud_rate = int(sys.argv[2])
            print(f"Using baud rate: {baud_rate}")
        except ValueError:
            print(f"Invalid baud rate: {sys.argv[2]}, using default 9600")

    # Start reading
    read_arduino(port, baud_rate)


if __name__ == "__main__":
    main()
