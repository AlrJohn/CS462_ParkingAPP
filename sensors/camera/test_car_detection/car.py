"""
Basic car detection script using YOLO11
Detects cars from images, videos, or webcam feed
"""

from ultralytics import YOLO
import cv2
import argparse


def detect_cars(source, model_size='m', conf_threshold=0.3, save_output=False, iou_threshold=0.5):
    """
    Detect cars using YOLO11 optimized for parking lot rooftop views with occlusion handling

    Args:
        source: Path to image/video or 0 for webcam
        model_size: YOLO11 model size (n, s, m, l, x) - 'm' recommended for occluded vehicles
        conf_threshold: Confidence threshold for detections
        save_output: Whether to save the output
        iou_threshold: IoU threshold for NMS
    """
    # Load YOLO11 model (will download on first run)
    # Medium model is better at detecting partially occluded objects
    model = YOLO(f'yolo11{model_size}.pt')

    # COCO dataset class IDs we want to detect
    # 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
    vehicle_classes = [2, 3, 5, 7]

    print(f"Running YOLO11{model_size} on: {source}")
    print(f"Confidence threshold: {conf_threshold}")
    print(f"IoU threshold: {iou_threshold}")

    # Run detection with parameters optimized for occlusion handling
    results = model.predict(
        source=source,
        conf=conf_threshold,
        iou=iou_threshold,
        classes=vehicle_classes,  # Only detect vehicles
        stream=True,  # Use streaming for videos/webcam
        save=save_output,
        show=True,  # Display results in real-time
        agnostic_nms=False,  # Class-specific NMS better for occluded vehicles
        max_det=300,  # Increase max detections for large parking lots
        augment=True,  # Test-time augmentation for better occlusion handling
        imgsz=1280  # Larger image size preserves detail in occluded regions
    )

    # Process results
    for result in results:
        # Get detection info
        boxes = result.boxes

        if len(boxes) > 0:
            print(f"\nDetected {len(boxes)} vehicle(s):")
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = result.names[cls]
                print(f"  - {class_name}: {conf:.2f}")

        # Press 'q' to quit (for video/webcam)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    input()
    cv2.destroyAllWindows()
    print("\nDetection complete!")


def main():
    parser = argparse.ArgumentParser(description='Car detection using YOLO11 optimized for parking lots with occlusion handling')
    parser.add_argument('source', type=str, nargs='?', default='0',
                        help='Path to image/video file, or 0 for webcam (default: 0)')
    parser.add_argument('--model', type=str, default='m', choices=['n', 's', 'm', 'l', 'x'],
                        help='YOLO11 model size (default: m for occluded vehicles)')
    parser.add_argument('--conf', type=float, default=0.4,
                        help='Confidence threshold (default: 0.4)')
    parser.add_argument('--iou', type=float, default=0.5,
                        help='IoU threshold for NMS (default: 0.5)')
    parser.add_argument('--save', action='store_true',
                        help='Save output results')

    args = parser.parse_args()

    # Convert '0' string to integer for webcam
    source = 0 if args.source == '0' else args.source

    detect_cars(source, args.model, args.conf, args.save, args.iou)


if __name__ == "__main__":
    main()
