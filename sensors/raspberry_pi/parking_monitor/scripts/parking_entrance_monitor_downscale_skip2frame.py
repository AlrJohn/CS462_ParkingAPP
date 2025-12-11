"""
Parking Lot Entrance Monitor (Headless, Optimized)
- Downscales frames before processing
- Processes every Nth frame (skips frames in between)
- Tracks processing time and effective FPS
- Safe to run on Ubuntu Server / Raspberry Pi with no display

Output video: parking_entrance_output_downscale_skip2frames.mp4
"""

import cv2
from ultralytics import YOLO
import numpy as np
from collections import defaultdict
import argparse
import time


# === Optimization constants ===
# Downscale factor for width/height (0.5 = half-size)
DOWNSCALE_FACTOR = 0.5

# Process every Nth frame (N=3 means process 1, skip 2)
PROCESS_EVERY_N_FRAMES = 3

# Lift the entrance line a bit higher (in pixels, on the *downscaled* frame)
LINE_VERTICAL_OFFSET_PIXELS = -25  # negative = move up, positive = move down


class ParkingEntranceMonitor:
    def __init__(self, video_path, model_path='yolo11m.pt', line_position=None):
        """
        Initialize the parking entrance monitor

        Args:
            video_path: Path to the video file
            model_path: Path to YOLO model
            line_position: Y-coordinate of the entrance line on the *downscaled* frame.
                           If None, it will be set automatically based on frame height.
        """
        self.video_path = video_path
        self.model = YOLO(model_path)
        self.line_position = line_position  # in downscaled coordinates

        # Track history for each vehicle ID (on downscaled frames)
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
            current_y: Current Y position of vehicle centroid (downscaled frame)

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

        # Get original video properties
        orig_fps = cap.get(cv2.CAP_PROP_FPS)
        if orig_fps <= 0 or np.isnan(orig_fps):
            orig_fps = 30.0  # sensible default if FPS can't be read

        orig_fps = float(orig_fps)
        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"Original video: {orig_width}x{orig_height} @ {orig_fps:.2f}fps, {total_frames} frames")

        # Compute downscaled dimensions
        ds_width = int(orig_width * DOWNSCALE_FACTOR)
        ds_height = int(orig_height * DOWNSCALE_FACTOR)

        print(f"Downscaled to: {ds_width}x{ds_height} (factor {DOWNSCALE_FACTOR})")
        print(f"Processing every {PROCESS_EVERY_N_FRAMES}rd frame (skipping {PROCESS_EVERY_N_FRAMES - 1} in between)")

        # If no line_position was provided, set it automatically based on downscaled height
        if self.line_position is None:
            auto_line = int(ds_height * 0.6)  # 60% down the downscaled frame
            # Apply vertical offset (negative = move up)
            self.line_position = max(0, min(ds_height - 1, auto_line + LINE_VERTICAL_OFFSET_PIXELS))
            print(f"Entrance line automatically set at Y={self.line_position} (downscaled)")
        else:
            print(f"Entrance line provided at Y={self.line_position} (downscaled)")

        # Setup video writer if saving
        out = None
        if save_output:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            output_path = 'parking_entrance_output_downscale_skip2frames.mp4'
            # We save the downscaled frames
            out = cv2.VideoWriter(output_path, fourcc, orig_fps, (ds_width, ds_height))
            if not out.isOpened():
                print("Error: Could not open video writer. Output will not be saved.")
                out = None
            else:
                print(f"[INFO] Saving processed video to {output_path}")

        # Timing and counters
        frame_count = 0            # total frames read
        processed_frame_count = 0  # frames actually sent through YOLO
        start_time = time.time()

        print(f"\nProcessing video with entrance line at Y={self.line_position} (downscaled)")
        print("Direction: Below→Above = EXIT, Above→Below = ENTRY\n")

        # Track which IDs we've already counted to avoid double counting too often
        counted_crossings = set()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1

            # Downscale the frame
            frame_small = cv2.resize(frame, (ds_width, ds_height), interpolation=cv2.INTER_LINEAR)

            # Determine if this frame should be processed
            should_process = (frame_count % PROCESS_EVERY_N_FRAMES == 0)

            if should_process:
                processed_frame_count += 1

                # Run YOLO tracking (using built-in ByteTrack) on downscaled frame
                results = self.model.track(
                    frame_small,
                    persist=True,        # Persist tracks between processed frames
                    classes=self.vehicle_classes,
                    conf=0.4,
                    iou=0.5,
                    verbose=False,
                    tracker="bytetrack.yaml"
                )

                # Draw the entrance line
                cv2.line(
                    frame_small,
                    (0, self.line_position),
                    (ds_width, self.line_position),
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

                        # Store position history (downscaled coordinates)
                        self.track_history[track_id].append((cx, cy))

                        # Keep only last 30 positions
                        if len(self.track_history[track_id]) > 30:
                            self.track_history[track_id].pop(0)

                        # Check for line crossing
                        crossing_key = (track_id, frame_count // PROCESS_EVERY_N_FRAMES)
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
                                    frame_small,
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
                                    frame_small,
                                    'EXIT!',
                                    (x1, max(y1 - 10, 0)),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.9,
                                    (0, 0, 255),
                                    2
                                )

                        # Draw bounding box
                        color = (255, 0, 0)  # Blue for tracked vehicles
                        cv2.rectangle(frame_small, (x1, y1), (x2, y2), color, 2)

                        # Draw centroid
                        cv2.circle(frame_small, (cx, cy), 4, (0, 255, 255), -1)

                        # Draw track ID
                        class_name = results[0].names.get(cls, str(cls))
                        label = f'ID:{track_id} {class_name}'
                        cv2.putText(
                            frame_small,
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
                            cv2.polylines(frame_small, [points], False, (230, 230, 230), 2)

            else:
                # For skipped frames, we just draw the line and overlays using the latest counts.
                cv2.line(
                    frame_small,
                    (0, self.line_position),
                    (ds_width, self.line_position),
                    (0, 255, 0),
                    3
                )

            # Draw statistics overlay (on every frame)
            cv2.putText(
                frame_small,
                f'Entries: {self.entries}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            cv2.putText(
                frame_small,
                f'Exits: {self.exits}',
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            cv2.putText(
                frame_small,
                f'Net: {self.entries - self.exits}',
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )
            cv2.putText(
                frame_small,
                f'Frame: {frame_count}/{total_frames}',
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            # Save frame if requested
            if save_output and out is not None:
                out.write(frame_small)

        # Cleanup
        cap.release()
        if out is not None:
            out.release()

        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            effective_fps = processed_frame_count / elapsed_time
        else:
            effective_fps = 0.0

        # Print final statistics
        print(f"\n{'=' * 50}")
        print("FINAL STATISTICS")
        print(f"{'=' * 50}")
        print(f"Total Entries: {self.entries}")
        print(f"Total Exits: {self.exits}")
        print(f"Net Change: {self.entries - self.exits}")
        print(f"Frames Read: {frame_count}/{total_frames}")
        print(f"Frames Processed (YOLO): {processed_frame_count}")
        print(f"Total Processing Time: {elapsed_time:.2f} seconds")
        print(f"Effective YOLO FPS: {effective_fps:.2f} frames/second")
        print(f"{'=' * 50}")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor parking lot entrance for entering/exiting vehicles (headless, downscaled, frame-skipping)'
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
        help='Y-coordinate of entrance line on the *downscaled* frame '
             '(default: automatic ~60%% of height, shifted up by 25px)'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Ignored (kept for compatibility; script is always headless).'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save processed video to parking_entrance_output_downscale_skip2frames.mp4'
    )

    args = parser.parse_args()

    monitor = ParkingEntranceMonitor(args.video, args.model, args.line)
    # show_video argument kept for backwards compatibility but has no effect
    monitor.process_video(show_video=not args.no_display, save_output=args.save)


if __name__ == "__main__":
    main()

