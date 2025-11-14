import cv2
import requests
from datetime import datetime
from ultralytics import YOLO

# Configuration
BACKEND_URL = "https://cs462-parkingapp.onrender.com/updateLotCount"
API_KEY = "123"
YOLO_MODEL_PATH = "../../yolo11m.pt"  # Medium YOLO model
PARKING_LOT_ID = "H"
TEST_IMAGE_PATH = "psu_parking_lot.jpeg"  # Test image in the same directory

# Initialize YOLO model
print("Loading YOLO model...")
model = YOLO(YOLO_MODEL_PATH)
print("Model loaded successfully!")

def detect_cars(frame):
    """
    Detect cars in the frame using YOLO
    Returns the count of detected cars
    """
    # Run YOLO inference with parameters matching car.py for consistency
    results = model.predict(
        source=frame,
        conf=0.3,  # Match car.py confidence threshold
        iou=0.5,   # Match car.py IoU threshold
        classes=[2, 3, 5, 7],  # Only detect vehicles
        agnostic_nms=False,
        max_det=300,
        augment=True,  # Test-time augmentation for better detection
        imgsz=1280,    # Larger image size preserves detail
        verbose=False
    )

    # Count all detected vehicles
    car_count = 0

    for result in results:
        boxes = result.boxes
        car_count += len(boxes)

    return car_count

def process_test_image():
    """Load test image, detect cars, and send count to backend"""
    print(f"\nProcessing test image: {TEST_IMAGE_PATH}")

    # Load the test image
    frame = cv2.imread(TEST_IMAGE_PATH)

    if frame is None:
        print(f"Error: Could not load image from {TEST_IMAGE_PATH}")
        return False

    print("Image loaded successfully!")

    # Detect cars in the frame
    print("Running car detection...")
    car_count = detect_cars(frame)
    print(f" Detected {car_count} cars in parking lot {PARKING_LOT_ID}")

    # Get current lot capacity from backend first
    print("\nFetching current parking lot data...")
    try:
        headers = {'X-API-Key': API_KEY}
        response = requests.get(
            "https://cs462-parkingapp.onrender.com/getLotCount",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            lots_data = response.json()
            # Find lot C data (assuming backend will be updated to include C)
            lot_c_data = next((lot for lot in lots_data if lot['lot'] == PARKING_LOT_ID), None)

            if lot_c_data:
                current_capacity = lot_c_data['capacity']
                current_occupied = lot_c_data['occupied_spaces']
                print(f"Current lot C - Capacity: {current_capacity}, Occupied: {current_occupied}")
            else:
                print(f"Warning: Lot {PARKING_LOT_ID} not found in backend response")
    except Exception as e:
        print(f"Warning: Could not fetch current lot data: {e}")

    # Calculate delta based on detected cars
    # For camera sensor, we're setting absolute occupancy, but backend uses delta
    # So we send the detected count as the new occupied count
    print(f"\nSending update to backend...")
    print(f"Detected occupied spots: {car_count}")

    # Prepare the data to send to backend
    # Note: Based on the backend code, we need to use delta (-1 for entering, +1 for exiting)
    # For a camera-based absolute count, we would need a different endpoint
    # For now, let's just demonstrate the update with the detection result

    data = {
        'lot': PARKING_LOT_ID,
        'delta': -1,  # This is just for demonstration
        'detected_cars': car_count,  # Adding this for information
        'timestamp': datetime.now().isoformat(),
        'device_id': 'camera_sensor_test'
    }

    try:
        # Send POST request to backend with API key
        headers = {'X-API-Key': API_KEY}
        response = requests.post(BACKEND_URL, json=data, headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()
            print(f" Successfully updated parking lot {PARKING_LOT_ID}")
            print(f"Response: {result}")
            return True
        else:
            print(f" Failed to update backend. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f" Error sending data to backend: {e}")
        return False

def main():
    """Main function to run test"""
    print("=" * 60)
    print("YOLO-based Parking Lot Monitoring - Test Mode")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Parking Lot: {PARKING_LOT_ID}")
    print(f"YOLO Model: {YOLO_MODEL_PATH}")
    print(f"Test Image: {TEST_IMAGE_PATH}")
    print("=" * 60)

    process_test_image()

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
