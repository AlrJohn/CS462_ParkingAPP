"""
Parking Lot Entrance Monitor
Tracks cars entering and exiting the parking lot by detecting line crossings.
Headless version: safe to run on servers with no display (no OpenCV GUI calls).
"""

import cv2
from ultralytics import YOLO
import numpy as np
from collections import defaultdict
import argparse


class ParkingEntranceMonitor:
    def __init__(self, video_path, model_path='yolo11m.pt', line_position=None):
        """
        Initialize the parking entrance monitor

        Args:
            video_path: Path to the video file
            model_path: Path to YOLO model
            line_position: Y-coordinate of the entrance line.
                           If None, it will be set automatically based on frame height.
        """
        self.video_path = video_path
        self.model = YOLO(model_path)
        self.line_position = line_position

        # Track history for each vehicle ID
        self.track_history = defaultdict(list)

        # Counters
        self.entries = 0
        self.exits = 0

        # Vehicle classes to detect (car, motorcycle, bus, truck)
        self.vehicle_classes = [2, 3, 5, 7]

    def get_centroid(self, box):
        """Get the centroid (center point) of a bounding box"""
        x1, y1, x2, y2 = box
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)
        return cx, cy

    def check_line_crossing(self, track_id, current_y):
        """
        Check if a vehicle crossed the entrance line

        Args:
            track_id: ID of the tracked vehicle
            current_y: Current Y position of vehicle centroid

        Returns:
            'entry', 'exit', or None
        """
        if len(self.track_history[track_id]) < 2:
            return None

        previous_y = self.track_history[track_id][-2][1]

        # Check if the vehicle crossed the line
        if previous_y < self.line_position <= current_y:
            # Moved from above to below the line = ENTERING
            return 'entry'
        elif previous_y > self.line_position >= current_y:
            # Moved from below to above the line = EXITING
            return 'exit'

        return None

    def process_video(self, show_video=False, save_output=False):
        """
        Process the video and track vehicles crossing the entrance line.

        NOTE: This version is fully headless. The 'show_video' argument is kept
        for compatibility but is ignored; no windows are ever opened.

        Args:
            show_video: Ignored (kept for API compatibility)
            save_output: Whether to save the processed video
        """
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            print(f"Error: Could not open video file {self.video_path}")
            return

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or np.isnan(fps):
            fps = 30.0  # sensible default if FPS can't be read

        fps = float(fps)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"Video: {width}x{height} @ {fps:.2f}fps, {total_frames} frames")

        # If no line_position was provided, set it automatically (e.g., 60% down from the top)
        if self.line_position is None:
            self.line_position = int(height * 0.6)
            print(f"Entrance line automatically set at Y={self.line_position}")
        else:
            print(f"Entrance line provided at Y={self.line_position}")

        # Setup video writer if saving
        out = None
        if save_output:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            output_path = 'parking_entrance_output.mp4'
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            if not out.isOpened():
                print("Error: Could not open video writer. Output will not be saved.")
                out = None
            else:
                print(f"[INFO] Saving processed video to {output_path}")

        frame_count = 0

        print(f"\nProcessing video with entrance line at Y={self.line_position}")
        print("Direction: Below→Above = EXIT, Above→Below = ENTRY\n")

        # Track which IDs we've already counted to avoid double counting too often
        counted_crossings = set()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # Run YOLO tracking (using built-in ByteTrack)
            results = self.model.track(
                frame,
                persist=True,  # Persist tracks between frames
                classes=self.vehicle_classes,
                conf=0.4,
                iou=0.5,
                verbose=False,
                tracker="bytetrack.yaml"
            )

            # Draw the entrance line
            cv2.line(
                frame,
                (0, self.line_position),
                (width, self.line_position),
                (0, 255, 0),
                3
            )

            # Process detections
            if results and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                confidences = results[0].boxes.conf.cpu().numpy()
                classes = results[0].boxes.cls.cpu().numpy().astype(int)

                for box, track_id, conf, cls in zip(boxes, track_ids, confidences, classes):
                    x1, y1, x2, y2 = map(int, box)
                    cx, cy = self.get_centroid(box)

                    # Store position history
                    self.track_history[track_id].append((cx, cy))

                    # Keep only last 30 positions
                    if len(self.track_history[track_id]) > 30:
                        self.track_history[track_id].pop(0)

                    # Check for line crossing
                    crossing_key = (track_id, frame_count // 10)  # Allow recounting every 10 frames

                    if crossing_key not in counted_crossings:
                        crossing = self.check_line_crossing(track_id, cy)

                        if crossing == 'entry':
                            self.entries += 1
                            counted_crossings.add(crossing_key)
                            print(
                                f"Frame {frame_count}: Vehicle {track_id} ENTERED "
                                f"(Total: {self.entries} in, {self.exits} out)"
                            )
                            # Draw entry notification
                            cv2.putText(
                                frame,
                                'ENTRY!',
                                (x1, max(y1 - 10, 0)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.9,
                                (0, 255, 0),
                                2
                            )

                        elif crossing == 'exit':
                            self.exits += 1
                            counted_crossings.add(crossing_key)
                            print(
                                f"Frame {frame_count}: Vehicle {track_id} EXITED "
                                f"(Total: {self.entries} in, {self.exits} out)"
                            )
                            # Draw exit notification
                            cv2.putText(
                                frame,
                                'EXIT!',
                                (x1, max(y1 - 10, 0)),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.9,
                                (0, 0, 255),
                                2
                            )

                    # Draw bounding box
                    color = (255, 0, 0)  # Blue for tracked vehicles
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    # Draw centroid
                    cv2.circle(frame, (cx, cy), 4, (0, 255, 255), -1)

                    # Draw track ID
                    class_name = results[0].names.get(cls, str(cls))
                    label = f'ID:{track_id} {class_name}'
                    cv2.putText(
                        frame,
                        label,
                        (x1, max(y1 - 30, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        2
                    )

                    # Draw track trail
                    points = np.array(self.track_history[track_id], dtype=np.int32)
                    if len(points) > 1:
                        cv2.polylines(frame, [points], False, (230, 230, 230), 2)

            # Draw statistics overlay
            cv2.putText(
                frame,
                f'Entries: {self.entries}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            cv2.putText(
                frame,
                f'Exits: {self.exits}',
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            cv2.putText(
                frame,
                f'Net: {self.entries - self.exits}',
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )
            cv2.putText(
                frame,
                f'Frame: {frame_count}/{total_frames}',
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            # Save frame if requested
            if save_output and out is not None:
                out.write(frame)

            # NOTE: no display code here (headless)

        # Cleanup
        cap.release()
        if out is not None:
            out.release()

        # Print final statistics
        print(f"\n{'=' * 50}")
        print("FINAL STATISTICS")
        print(f"{'=' * 50}")
        print(f"Total Entries: {self.entries}")
        print(f"Total Exits: {self.exits}")
        print(f"Net Change: {self.entries - self.exits}")
        print(f"Frames Processed: {frame_count}/{total_frames}")
        print(f"{'=' * 50}")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor parking lot entrance for entering/exiting vehicles (headless)'
    )
    parser.add_argument('video', type=str, help='Path to video file')
    parser.add_argument(
        '--model',
        type=str,
        default='yolo11m.pt',
        help='Path to YOLO model (default: yolo11m.pt)'
    )
    parser.add_argument(
        '--line',
        type=int,
        default=None,
        help='Y-coordinate of entrance line (default: automatic ~60%% of frame height)'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Ignored (kept for compatibility; script is always headless).'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save processed video to parking_entrance_output.mp4'
    )

    args = parser.parse_args()

    monitor = ParkingEntranceMonitor(args.video, args.model, args.line)
    # show_video argument kept for backwards compatibility but has no effect
    monitor.process_video(show_video=not args.no_display, save_output=args.save)


if __name__ == "__main__":
    main()

