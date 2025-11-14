import cv2
import requests
import time
from datetime import datetime
from ultralytics import YOLO

# Configuration
BACKEND_URL = "http://localhost:5000/api/parking-lots/C/occupancy"  # Update to your backend endpoint
CAMERA_INDEX = 0  # Default webcam
CAPTURE_INTERVAL = 5  # Seconds between captures
YOLO_MODEL_PATH = "../../yolo11m.pt"  # Medium YOLO model
PARKING_LOT_ID = "C"

# Initialize YOLO model
model = YOLO(YOLO_MODEL_PATH)

def detect_cars(frame):
    """
    Detect cars in the frame using YOLO
    Returns the count of detected cars
    """
    # Run YOLO inference
    results = model(frame, verbose=False)

    # Filter for car detections (class 2 in COCO dataset)
    # COCO classes: 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
    car_count = 0

    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Get class ID
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            # Count vehicles (car, motorcycle, bus, truck)
            if class_id in [2, 3, 5, 7] and confidence > 0.5:
                car_count += 1

    return car_count

def capture_and_process():
    """Capture an image from webcam, detect cars, and send count to backend"""
    # Initialize camera
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("Error: Could not open camera")
        return False

    # Capture frame
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Error: Could not read frame")
        return False

    # Detect cars in the frame
    car_count = detect_cars(frame)
    print(f"Detected {car_count} cars in parking lot {PARKING_LOT_ID}")

    # Prepare the data to send to backend
    data = {
        'parking_lot_id': PARKING_LOT_ID,
        'occupied_spots': car_count,
        'timestamp': datetime.now().isoformat(),
        'device_id': 'camera_sensor_1'
    }

    try:
        # Send POST request to backend
        response = requests.post(BACKEND_URL, json=data, timeout=10)

        if response.status_code == 200:
            print(f"✓ Successfully updated parking lot {PARKING_LOT_ID} with {car_count} cars at {data['timestamp']}")
            return True
        else:
            print(f"✗ Failed to update backend. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"✗ Error sending data to backend: {e}")
        return False

def main():
    """Main loop for continuous capture, detection, and update"""
    print("Starting YOLO-based parking lot monitoring...")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Parking Lot: {PARKING_LOT_ID}")
    print(f"YOLO Model: {YOLO_MODEL_PATH}")
    print(f"Capture interval: {CAPTURE_INTERVAL} seconds")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            capture_and_process()
            time.sleep(CAPTURE_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping parking lot monitoring...")

if __name__ == "__main__":
    main()
