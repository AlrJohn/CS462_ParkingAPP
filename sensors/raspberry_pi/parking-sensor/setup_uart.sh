#!/bin/bash
# Setup UART on Raspberry Pi 5 for Arduino communication

echo "=================================================="
echo "Raspberry Pi 5 UART Setup for Arduino"
echo "=================================================="
echo ""

# 1. Disable serial console (so we can use UART for Arduino)
echo "1. Disabling serial console on UART..."
sudo raspi-config nonint do_serial 1  # Disable serial console
sudo raspi-config nonint do_serial_hw 0  # Enable serial hardware

# 2. Enable UART in config
echo "2. Enabling UART in boot config..."
if ! grep -q "enable_uart=1" /boot/firmware/config.txt; then
    echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt
    echo "Added enable_uart=1 to config.txt"
else
    echo "UART already enabled in config.txt"
fi

# 3. Check current user is in dialout group
echo "3. Adding user to dialout group..."
sudo usermod -a -G dialout $USER

echo ""
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "IMPORTANT: You must REBOOT for changes to take effect:"
echo "  sudo reboot"
echo ""
echo "After reboot, the UART will be available at /dev/ttyAMA0"
echo ""
echo "Wiring:"
echo "  Arduino TX (pin 1)  →  Pi GPIO 15 (Physical pin 10)"
echo "  Arduino RX (pin 0)  →  Pi GPIO 14 (Physical pin 8)"
echo "  Arduino GND         →  Pi GND (Physical pin 6)"
echo ""
echo "Test with: python3 test_arduino_uart.py"
echo ""
