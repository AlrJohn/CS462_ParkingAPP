#!/bin/bash
# Arduino USB Connection Diagnostic Script

echo "=================================================="
echo "Arduino USB Connection Diagnostic"
echo "=================================================="
echo ""

echo "1. Checking USB devices..."
echo "----------------------------"
lsusb
echo ""

echo "2. Checking for Arduino serial ports..."
echo "----------------------------"
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || echo "No Arduino serial ports found (ttyACM* or ttyUSB*)"
echo ""

echo "3. Checking all serial devices..."
echo "----------------------------"
ls -l /dev/ttyAMA* /dev/serial* 2>/dev/null || echo "No serial devices found"
echo ""

echo "4. Checking recent USB kernel messages (requires sudo)..."
echo "----------------------------"
sudo dmesg | grep -i "usb\|tty\|serial" | tail -20
echo ""

echo "5. Checking if pyserial is installed..."
echo "----------------------------"
python3 -c "import serial; print('pyserial version:', serial.__version__)" 2>/dev/null || echo "pyserial NOT installed - install with: pip3 install pyserial"
echo ""

echo "=================================================="
echo "Troubleshooting Steps:"
echo "=================================================="
echo "If Arduino is NOT detected:"
echo "  1. Verify Arduino is plugged into USB port"
echo "  2. Try a different USB cable (must support data, not just power)"
echo "  3. Try a different USB port on the Raspberry Pi"
echo "  4. Check Arduino has power (LED should be lit)"
echo "  5. On your computer, verify Arduino code uploaded successfully"
echo ""
echo "If Arduino IS detected but permission denied:"
echo "  sudo usermod -a -G dialout \$USER"
echo "  Then log out and back in"
echo ""
echo "To watch USB events in real-time:"
echo "  sudo dmesg -w"
echo "  (Then plug/unplug Arduino to see if it's detected)"
echo ""
