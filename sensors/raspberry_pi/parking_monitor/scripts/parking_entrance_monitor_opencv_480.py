"""
Parking Lot Entrance Monitor (Classical OpenCV Version, Headless)

- Uses background subtraction + contour detection (no YOLO, no deep learning)
- Tracks moving blobs as vehicles using a simple centroid-based tracker
- Counts entries and exits based on a horizontal line crossing
- Downscales frames for speed
- Designed to run headless on Ubuntu Server / Raspberry Pi
"""

import cv2
import numpy as np
from collections import defaultdict
import argparse
import time
import math


# ===== Tunable parameters =====
DOWNSCALE_WIDTH = 480        # target width for processing (keeps aspect ratio)
MIN_CONTOUR_AREA = 800       # minimum blob area to be considered a vehicle (in downscaled pixels)
MAX_TRACK_DIST = 50          # max pixel distance (downscaled) to match detection to an existing track
TRACK_FORGET_FRAMES = 30     # forget tracks not seen for this many frames
LINE_VERTICAL_OFFSET_PIXELS = -25  # negative moves line up from auto position


class SimpleTrack:
    """Represents a single tracked object (vehicle)."""
    def __init__(self, track_id, cx, cy, frame_idx):
        self.id = track_id
        self.history = [(cx, cy)]
        self.last_centroid = (cx, cy)
        self.last_seen_frame = frame_idx
        # For counting
        self.has_counted_entry = False
        self.has_counted_exit = False


class ParkingEntranceMonitorCV:
    def __init__(self, video_path, line_position=None):
        """
        Args:
            video_path: path to the input video
            line_position: Y coordinate (in downscaled frame) for the entrance line.
                           If None, it will be chosen automatically based on frame height.
        """
        self.video_path = video_path
        self.line_position = line_position

        # Tracking / counting state
        self.tracks = {}          # track_id -> SimpleTrack
        self.next_track_id = 1
        self.entries = 0
        self.exits = 0

    def _auto_line_position(self, height_ds):
        """Automatically choose a line position (in downscaled coordinates)."""
        base = int(height_ds * 0.6)  # around 60% down the frame
        line_y = base + LINE_VERTICAL_OFFSET_PIXELS
        line_y = max(0, min(height_ds - 1, line_y))
        return line_y

    def _distance(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _match_detections_to_tracks(self, detections, frame_idx):
        """
        Simple greedy centroid matching:
        - detections: list of (x, y, w, h, cx, cy)
        Updates self.tracks in-place.
        """
        unmatched_detections = detections.copy()
        # First try to match each detection to the closest existing track (within MAX_TRACK_DIST)
        for track in self.tracks.values():
            best_det = None
            best_dist = None
            for det in unmatched_detections:
                _, _, _, _, cx, cy = det
                dist = self._distance(track.last_centroid, (cx, cy))
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_det = det

            if best_det is not None and best_dist is not None and best_dist <= MAX_TRACK_DIST:
                # Assign this detection to the track
                x, y, w, h, cx, cy = best_det
                track.last_centroid = (cx, cy)
                track.history.append((cx, cy))
                track.last_seen_frame = frame_idx
                unmatched_detections.remove(best_det)

        # Any remaining unmatched detections become new tracks
        for det in unmatched_detections:
            x, y, w, h, cx, cy = det
            new_track = SimpleTrack(self.next_track_id, cx, cy, frame_idx)
            self.tracks[self.next_track_id] = new_track
            self.next_track_id += 1

        # Forget old tracks that haven't been seen recently
        to_delete = []
        for track_id, track in self.tracks.items():
            if frame_idx - track.last_seen_frame > TRACK_FORGET_FRAMES:
                to_delete.append(track_id)
        for tid in to_delete:
            del self.tracks[tid]

    def _check_crossings(self):
        """
        For each track, check whether it crossed the line between its last two positions.
        Updates self.entries / self.exits and the track flags.
        """
        for track in self.tracks.values():
            if len(track.history) < 2:
                continue

            prev_y = track.history[-2][1]
            curr_y = track.history[-1][1]

            # moved from above to below -> entry (if not already counted)
            if prev_y < self.line_position <= curr_y and not track.has_counted_entry:
                self.entries += 1
                track.has_counted_entry = True

            # moved from below to above -> exit (if not already counted)
            elif prev_y > self.line_position >= curr_y and not track.has_counted_exit:
                self.exits += 1
                track.has_counted_exit = True

    def process_video(self, save_output=False):
        """
        Main processing function: runs classical background-subtraction-based vehicle tracking.
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"Error: could not open video {self.video_path}")
            return

        # Get original properties
        orig_fps = cap.get(cv2.CAP_PROP_FPS)
        if orig_fps <= 0 or np.isnan(orig_fps):
            orig_fps = 30.0  # fallback
        orig_fps = float(orig_fps)

        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Compute downscaled dimensions
        scale = DOWNSCALE_WIDTH / float(orig_width)
        ds_width = DOWNSCALE_WIDTH
        ds_height = int(orig_height * scale)

        print(f"Video: {orig_width}x{orig_height} @ {orig_fps:.2f} fps, {total_frames} frames")
        print(f"Downscaled to: {ds_width}x{ds_height}")

        # Set line position if needed
        if self.line_position is None:
            self.line_position = self._auto_line_position(ds_height)
        print(f"Entrance line at Y={self.line_position} (downscaled coordinates)")

        # Background subtractor
        back_sub = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=True
        )

        # Video writer (downscaled)
        out = None
        if save_output:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            output_path = "parking_entrance_output_opencv_classical.mp4"
            out = cv2.VideoWriter(output_path, fourcc, orig_fps, (ds_width, ds_height))
            if out.isOpened():
                print(f"[INFO] Saving annotated video to {output_path}")
            else:
                print("[WARN] Could not open VideoWriter; no output will be saved.")
                out = None

        frame_idx = 0
        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            # Downscale frame
            frame_small = cv2.resize(frame, (ds_width, ds_height), interpolation=cv2.INTER_LINEAR)

            # Convert to grayscale
            gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

            # Apply background subtractor
            fgmask = back_sub.apply(gray)

            # Remove shadows (MOG2 shadows ~127)
            _, fgmask = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)

            # Morphological operations to clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel, iterations=2)
            fgmask = cv2.dilate(fgmask, kernel, iterations=2)

            # Find contours (potential vehicles)
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detections = []
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                area = w * h
                if area < MIN_CONTOUR_AREA:
                    continue  # too small to be a vehicle candidate

                cx = x + w // 2
                cy = y + h // 2
                detections.append((x, y, w, h, cx, cy))

            # Update tracks with the new detections
            self._match_detections_to_tracks(detections, frame_idx)

            # Check line crossings
            self._check_crossings()

            # Draw entrance line
            cv2.line(
                frame_small,
                (0, self.line_position),
                (ds_width, self.line_position),
                (0, 255, 0),
                2
            )

            # Draw tracks
            for track in self.tracks.values():
                cx, cy = track.last_centroid
                # Draw centroid
                cv2.circle(frame_small, (int(cx), int(cy)), 4, (0, 255, 255), -1)
                # Draw ID label
                cv2.putText(
                    frame_small,
                    f"ID:{track.id}",
                    (int(cx) - 10, int(cy) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    1
                )
                # Draw history trail
                if len(track.history) > 1:
                    pts = np.array(track.history, dtype=np.int32)
                    cv2.polylines(frame_small, [pts], False, (230, 230, 230), 2)

            # Draw detections (bounding boxes)
            for x, y, w, h, cx, cy in detections:
                cv2.rectangle(frame_small, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Draw stats
            cv2.putText(
                frame_small,
                f"Entries: {self.entries}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            cv2.putText(
                frame_small,
                f"Exits: {self.exits}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            cv2.putText(
                frame_small,
                f"Net: {self.entries - self.exits}",
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )
            cv2.putText(
                frame_small,
                f"Frame: {frame_idx}/{total_frames}",
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            # Write frame if requested
            if save_output and out is not None:
                out.write(frame_small)

            # Optional: progress print every N frames
            if frame_idx % 100 == 0:
                print(f"Processed {frame_idx}/{total_frames} frames...")

        # Cleanup
        cap.release()
        if out is not None:
            out.release()

        elapsed = time.time() - start_time
        fps_effective = frame_idx / elapsed if elapsed > 0 else 0.0

        print("\n" + "=" * 50)
        print("FINAL STATISTICS (Classical OpenCV)")
        print("=" * 50)
        print(f"Total Entries: {self.entries}")
        print(f"Total Exits: {self.exits}")
        print(f"Net Change: {self.entries - self.exits}")
        print(f"Frames Processed: {frame_idx}/{total_frames}")
        print(f"Total Time: {elapsed:.2f} s")
        print(f"Effective Processing FPS (downscaled): {fps_effective:.2f}")
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Parking lot entrance monitor using classical OpenCV (no YOLO, headless)."
    )
    parser.add_argument("video", type=str, help="Path to input video file")
    parser.add_argument(
        "--line",
        type=int,
        default=None,
        help="Y position of entrance line (in downscaled coords). "
             "If omitted, it is chosen automatically."
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save annotated video to parking_entrance_output_opencv_classical.mp4"
    )

    args = parser.parse_args()

    monitor = ParkingEntranceMonitorCV(args.video, args.line)
    monitor.process_video(save_output=args.save)


if __name__ == "__main__":
    main()

