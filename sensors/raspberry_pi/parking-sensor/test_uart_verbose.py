#!/usr/bin/env python3
"""
Verbose UART test - shows raw bytes to help diagnose connection issues
"""

import serial
import time

def test_uart_raw():
    """Read raw bytes from UART to see if anything is coming through."""
    port = '/dev/ttyAMA0'

    try:
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"Connected to {port}")
        print("Listening for ANY data (raw bytes)...")
        print("Press Ctrl+C to stop\n")

        ser.reset_input_buffer()
        no_data_count = 0

        while True:
            # Check if any bytes waiting
            waiting = ser.in_waiting
            if waiting > 0:
                # Read all available bytes
                data = ser.read(waiting)
                print(f"Received {waiting} bytes: {data}")
                print(f"  Hex: {data.hex()}")
                try:
                    print(f"  Text: {data.decode('utf-8', errors='replace')}")
                except:
                    pass
                print()
                no_data_count = 0
            else:
                no_data_count += 1
                if no_data_count % 10 == 0:
                    print(f"No data received yet... ({no_data_count/10:.0f} seconds)")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        if 'ser' in locals():
            ser.close()

if __name__ == "__main__":
    test_uart_raw()
