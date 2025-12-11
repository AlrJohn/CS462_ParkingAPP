"""
Parking Lot Entrance Monitor (Classical OpenCV + ROI on Full Frame, Headless, v2)

- Uses background subtraction + contour detection (no YOLO, no deep learning)
- Crops a region-of-interest (ROI) around the driveway to "zoom in" for processing
- Tracks moving blobs as vehicles using a simple centroid-based tracker
- Counts entries and exits based on a horizontal line crossing
- Processing is done on a downscaled ROI for speed
- Output video is the FULL original frame, with ROI highlighted and overlays drawn in place
- Improved crossing logic: uses overall motion direction to avoid misclassifying entries as exits
- Detection merging: consolidates multiple boxes on the same vehicle
- Spatial cooldown: prevents multiple counts for the same vehicle crossing
- Designed to run headless on Ubuntu Server / Raspberry Pi
"""

import cv2
import numpy as np
import argparse
import time
import math


# ===== Tunable parameters =====

# Target width for ROI processing (keeps aspect ratio)
DOWNSCALE_WIDTH_ROI = 480

# Minimum blob area in *downscaled ROI* to be considered a vehicle
# Increased to filter out noise from trees, shadows, etc.
MIN_CONTOUR_AREA = 1500

# Aspect ratio filter to reject tall skinny blobs (likely people)
# w/h must be >= this value to be considered a vehicle
MIN_ASPECT_RATIO = 1.2

# Max pixel distance (downscaled ROI) to match detection to an existing track
MAX_TRACK_DIST = 80

# Forget tracks not seen for this many frames
TRACK_FORGET_FRAMES = 30

# Keep tracks near the counting line alive longer (helps with slow/stopped vehicles)
TRACK_FORGET_FRAMES_NEAR_LINE = 60

# Distance from line (pixels) to consider a track "near" the line
NEAR_LINE_DISTANCE = 50

# Move line a bit up from auto position (negative = up, positive = down)
# Auto line is at ~75% of ROI height; this offset is applied on top of that.
LINE_VERTICAL_OFFSET_PIXELS = -65

# Minimum total vertical movement (in downscaled ROI pixels) required
# before we trust a track's direction for counting.
MIN_TOTAL_MOVE_PIXELS = 10

# Detection merging: max distance between detections to merge them
MERGE_DETECTION_DISTANCE = 60

# Spatial cooldown: ignore crossings within this horizontal distance (pixels)
# of a recent crossing
CROSSING_SPATIAL_COOLDOWN_DIST = 100

# Spatial cooldown: how many frames to remember recent crossings
CROSSING_COOLDOWN_FRAMES = 15

# When matching detections to tracks, expand search distance for tracks
# that haven't been seen recently (helps re-identify stopped vehicles)
MAX_TRACK_DIST_LOST = 120


class SimpleTrack:
    """Represents a single tracked object (vehicle)."""

    def __init__(self, track_id, cx, cy, frame_idx):
        self.id = track_id
        self.history = [(cx, cy)]
        self.last_centroid = (cx, cy)
        self.last_seen_frame = frame_idx
        self.first_y = cy  # remember starting vertical position
        self.velocity = (0, 0)  # (vx, vy) velocity estimate
        # For counting
        self.has_counted_entry = False
        self.has_counted_exit = False

    def update_position(self, cx, cy, frame_idx):
        """Update track position and velocity estimate."""
        # Calculate velocity from last position
        if len(self.history) > 0:
            prev_x, prev_y = self.last_centroid
            frames_elapsed = frame_idx - self.last_seen_frame
            if frames_elapsed > 0:
                vx = (cx - prev_x) / frames_elapsed
                vy = (cy - prev_y) / frames_elapsed
                # Smooth velocity with previous estimate
                alpha = 0.7  # weight for new velocity
                self.velocity = (alpha * vx + (1 - alpha) * self.velocity[0],
                                alpha * vy + (1 - alpha) * self.velocity[1])

        self.last_centroid = (cx, cy)
        self.history.append((cx, cy))
        self.last_seen_frame = frame_idx

    def predict_position(self, frame_idx):
        """Predict where track should be based on velocity."""
        frames_since_seen = frame_idx - self.last_seen_frame
        if frames_since_seen == 0:
            return self.last_centroid

        pred_x = self.last_centroid[0] + self.velocity[0] * frames_since_seen
        pred_y = self.last_centroid[1] + self.velocity[1] * frames_since_seen
        return (int(pred_x), int(pred_y))


class ParkingEntranceMonitorCVROI:
    def __init__(self, video_path, line_position=None):
        """
        Args:
            video_path: path to the input video
            line_position: Y coordinate (in downscaled ROI) for the entrance line.
                           If None, it will be chosen automatically based on ROI height.
        """
        self.video_path = video_path
        self.line_position = line_position

        # Tracking / counting state
        self.tracks = {}          # track_id -> SimpleTrack
        self.next_track_id = 1
        self.entries = 0
        self.exits = 0

        # Spatial cooldown: track recent crossings as (x_pos, frame_idx, direction)
        # direction: 'entry' or 'exit'
        self.recent_crossings = []

        # ROI bounds in original frame coordinates (fractions)
        # Left & top unchanged; right & bottom extended as requested.
        self.x_left_frac = 1.0 / 4.0      # ~33%
        self.x_right_frac = 0.90          # was 0.75, now 0.80 (5% more to the right)
        self.y_top_frac = 1.0 / 3.0       # ~33%
        self.y_bottom_frac = 0.90         # was 0.75, now 0.85 (10% further down)

        # These will be computed once we know frame size
        self.roi_x_left = None
        self.roi_x_right = None
        self.roi_y_top = None
        self.roi_y_bottom = None

        # ROI size and scale (original -> downscaled ROI)
        self.roi_width = None
        self.roi_height = None
        self.roi_scale = None  # ds_width / roi_width

    def _auto_line_position(self, roi_height_ds):
        """Automatically choose a line position (in downscaled ROI coordinates)."""
        # Lower line by ~10% (75% of ROI height) then apply offset.
        base = int(roi_height_ds * 0.75)
        line_y = base + LINE_VERTICAL_OFFSET_PIXELS
        line_y = max(0, min(roi_height_ds - 1, line_y))
        return line_y

    def _distance(self, p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    def _merge_nearby_detections(self, detections):
        """
        Merge detections that are too close together (likely the same vehicle).
        Uses a simple greedy clustering approach.

        Args:
            detections: list of (x, y, w, h, cx, cy) tuples

        Returns:
            merged_detections: list of merged (x, y, w, h, cx, cy) tuples
        """
        if len(detections) <= 1:
            return detections

        # Convert to mutable list
        remaining = list(detections)
        merged = []

        while remaining:
            # Start a new cluster with the first remaining detection
            cluster = [remaining.pop(0)]

            # Find all detections close to this cluster
            i = 0
            while i < len(remaining):
                det = remaining[i]
                # Check if this detection is close to any detection in the cluster
                is_close = False
                for cluster_det in cluster:
                    dist = self._distance(
                        (det[4], det[5]),  # cx, cy of detection
                        (cluster_det[4], cluster_det[5])  # cx, cy of cluster detection
                    )
                    if dist < MERGE_DETECTION_DISTANCE:
                        is_close = True
                        break

                if is_close:
                    cluster.append(remaining.pop(i))
                else:
                    i += 1

            # Merge the cluster into a single detection
            if len(cluster) == 1:
                merged.append(cluster[0])
            else:
                # Compute bounding box that encompasses all detections in cluster
                min_x = min(det[0] for det in cluster)
                min_y = min(det[1] for det in cluster)
                max_x = max(det[0] + det[2] for det in cluster)
                max_y = max(det[1] + det[3] for det in cluster)

                merged_x = min_x
                merged_y = min_y
                merged_w = max_x - min_x
                merged_h = max_y - min_y
                merged_cx = merged_x + merged_w // 2
                merged_cy = merged_y + merged_h // 2

                merged.append((merged_x, merged_y, merged_w, merged_h, merged_cx, merged_cy))

        return merged

    def _match_detections_to_tracks(self, detections, frame_idx):
        """
        Greedy centroid matching with prediction:
        - detections: list of (x, y, w, h, cx, cy) in downscaled ROI coords
        - Uses predicted positions for tracks that haven't been seen recently
        - Adaptive matching distance for lost tracks
        Updates self.tracks in-place.
        """
        unmatched_detections = detections.copy()
        # First try to match each detection to the closest existing track (within MAX_TRACK_DIST)
        for track in self.tracks.values():
            best_det = None
            best_dist = None

            # Use predicted position if track hasn't been seen recently
            frames_since_seen = frame_idx - track.last_seen_frame
            if frames_since_seen > 0:
                compare_pos = track.predict_position(frame_idx)
                # Use larger search radius for tracks that were lost
                max_dist = MAX_TRACK_DIST_LOST if frames_since_seen > 1 else MAX_TRACK_DIST
            else:
                compare_pos = track.last_centroid
                max_dist = MAX_TRACK_DIST

            for det in unmatched_detections:
                _, _, _, _, cx, cy = det
                dist = self._distance(compare_pos, (cx, cy))
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_det = det

            if best_det is not None and best_dist is not None and best_dist <= max_dist:
                # Assign this detection to the track
                x, y, w, h, cx, cy = best_det
                track.update_position(cx, cy, frame_idx)
                unmatched_detections.remove(best_det)

        # Any remaining unmatched detections become new tracks
        for det in unmatched_detections:
            x, y, w, h, cx, cy = det
            new_track = SimpleTrack(self.next_track_id, cx, cy, frame_idx)
            self.tracks[self.next_track_id] = new_track
            self.next_track_id += 1

        # Forget old tracks that haven't been seen recently
        # Use adaptive persistence: keep tracks near the line alive longer
        to_delete = []
        for track_id, track in self.tracks.items():
            # Check if track is near the counting line
            track_y = track.last_centroid[1]
            dist_to_line = abs(track_y - self.line_position)

            # Use longer timeout for tracks near the line (helps with stopped vehicles)
            if dist_to_line < NEAR_LINE_DISTANCE:
                forget_threshold = TRACK_FORGET_FRAMES_NEAR_LINE
            else:
                forget_threshold = TRACK_FORGET_FRAMES

            if frame_idx - track.last_seen_frame > forget_threshold:
                to_delete.append(track_id)
        for tid in to_delete:
            del self.tracks[tid]

    def _is_too_close_to_recent_crossing(self, x_pos, frame_idx, direction):
        """
        Check if a potential crossing is too close (spatially and temporally)
        to a recent crossing of the same direction.

        Args:
            x_pos: horizontal position of the crossing
            frame_idx: current frame number
            direction: 'entry' or 'exit'

        Returns:
            True if too close to recent crossing, False otherwise
        """
        for recent_x, recent_frame, recent_dir in self.recent_crossings:
            # Only compare crossings of the same direction
            if recent_dir != direction:
                continue

            # Check if within temporal cooldown
            if frame_idx - recent_frame > CROSSING_COOLDOWN_FRAMES:
                continue

            # Check if within spatial cooldown
            if abs(x_pos - recent_x) < CROSSING_SPATIAL_COOLDOWN_DIST:
                return True

        return False

    def _check_crossings(self, frame_idx):
        """
        For each track, check whether it crossed the line between its last two positions.
        Uses overall vertical movement direction to decide whether to count an entry or exit.
        Applies spatial cooldown to prevent duplicate counts.
        """
        # Clean up old crossings from recent_crossings list
        self.recent_crossings = [
            (x, frame, direction)
            for x, frame, direction in self.recent_crossings
            if frame_idx - frame <= CROSSING_COOLDOWN_FRAMES
        ]

        for track in self.tracks.values():
            # If we've already counted either entry or exit for this track, skip further counting
            if track.has_counted_entry or track.has_counted_exit:
                continue

            if len(track.history) < 2:
                continue

            prev_y = track.history[-2][1]
            curr_y = track.history[-1][1]
            curr_x = track.history[-1][0]

            # Total vertical movement from first detection
            dy_total = track.history[-1][1] - track.first_y

            # Ignore tiny movements (noise)
            if abs(dy_total) < MIN_TOTAL_MOVE_PIXELS:
                continue

            # Overall direction: >0 => moving down, <0 => moving up
            moving_down = dy_total > 0
            moving_up = dy_total < 0

            # moved from above to below -> entry (only if overall moving down)
            if (
                prev_y < self.line_position <= curr_y and
                moving_down and
                not track.has_counted_entry
            ):
                # Check spatial cooldown
                if not self._is_too_close_to_recent_crossing(curr_x, frame_idx, 'entry'):
                    self.entries += 1
                    track.has_counted_entry = True
                    self.recent_crossings.append((curr_x, frame_idx, 'entry'))

            # moved from below to above -> exit (only if overall moving up)
            elif (
                prev_y > self.line_position >= curr_y and
                moving_up and
                not track.has_counted_exit
            ):
                # Check spatial cooldown
                if not self._is_too_close_to_recent_crossing(curr_x, frame_idx, 'exit'):
                    self.exits += 1
                    track.has_counted_exit = True
                    self.recent_crossings.append((curr_x, frame_idx, 'exit'))

    def _roi_to_full_coords(self, x_ds, y_ds):
        """
        Map coordinates from downscaled ROI (x_ds, y_ds) back to full-frame coordinates.
        """
        x_roi = x_ds / self.roi_scale
        y_roi = y_ds / self.roi_scale
        x_full = int(x_roi + self.roi_x_left)
        y_full = int(y_roi + self.roi_y_top)
        return x_full, y_full

    def _box_roi_to_full(self, x_ds, y_ds, w_ds, h_ds):
        """
        Map a bounding box from downscaled ROI coords back to full-frame coords.
        """
        x1_ds = x_ds
        y1_ds = y_ds
        x2_ds = x_ds + w_ds
        y2_ds = y_ds + h_ds

        x1_full, y1_full = self._roi_to_full_coords(x1_ds, y1_ds)
        x2_full, y2_full = self._roi_to_full_coords(x2_ds, y2_ds)

        return x1_full, y1_full, x2_full, y2_full

    def process_video(self, save_output=False):
        """
        Main processing function: runs classical background-subtraction-based vehicle tracking on an ROI,
        but outputs the full original frame with ROI and overlays.
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

        print(f"Video: {orig_width}x{orig_height} @ {orig_fps:.2f} fps, {total_frames} frames")

        # Compute ROI bounds in original coordinates
        self.roi_x_left = int(orig_width * self.x_left_frac)
        self.roi_x_right = int(orig_width * self.x_right_frac)
        self.roi_y_top = int(orig_height * self.y_top_frac)
        self.roi_y_bottom = int(orig_height * self.y_bottom_frac)

        # Sanity: clamp
        self.roi_x_left = max(0, min(self.roi_x_left, orig_width - 1))
        self.roi_x_right = max(0, min(self.roi_x_right, orig_width))
        self.roi_y_top = max(0, min(self.roi_y_top, orig_height - 1))
        self.roi_y_bottom = max(0, min(self.roi_y_bottom, orig_height))

        self.roi_width = self.roi_x_right - self.roi_x_left
        self.roi_height = self.roi_y_bottom - self.roi_y_top
        print(f"ROI (original coords): x[{self.roi_x_left}:{self.roi_x_right}], "
              f"y[{self.roi_y_top}:{self.roi_y_bottom}] => {self.roi_width}x{self.roi_height}")

        # Compute downscaled ROI dimensions
        self.roi_scale = DOWNSCALE_WIDTH_ROI / float(self.roi_width)
        ds_width = DOWNSCALE_WIDTH_ROI
        ds_height = int(self.roi_height * self.roi_scale)
        print(f"Downscaled ROI: {ds_width}x{ds_height}")

        # Set line position if needed (in downscaled ROI)
        if self.line_position is None:
            self.line_position = self._auto_line_position(ds_height)
        print(f"Entrance line in downscaled ROI at Y={self.line_position}")

        # Background subtractor (applied only on ROI)
        # Balanced parameters: detect slow vehicles without too much noise
        back_sub = cv2.createBackgroundSubtractorMOG2(
            history=600, varThreshold=40, detectShadows=True
        )
        # Moderate learning rate: slow enough to detect slow cars, fast enough to adapt
        learning_rate = 0.005

        # Video writer (full original frame)
        out = None
        if save_output:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            output_path = "parking_entrance_output_opencv_roi_fullframe_v2.mp4"
            out = cv2.VideoWriter(output_path, fourcc, orig_fps, (orig_width, orig_height))
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

            # Crop ROI from original frame
            roi = frame[self.roi_y_top:self.roi_y_bottom, self.roi_x_left:self.roi_x_right]
            if roi.size == 0:
                # Something is wrong with ROI definition
                print("Empty ROI encountered, stopping.")
                break

            # Downscale ROI
            roi_small = cv2.resize(roi, (ds_width, ds_height), interpolation=cv2.INTER_LINEAR)

            # Convert to grayscale
            gray = cv2.cvtColor(roi_small, cv2.COLOR_BGR2GRAY)

            # Apply background subtractor with moderate learning rate
            # (helps detect slow cars while adapting to lighting changes)
            fgmask = back_sub.apply(gray, learningRate=learning_rate)

            # Balanced threshold: detects vehicles without too much noise
            _, fgmask = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)

            # Morphological operations to clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel, iterations=1)
            fgmask = cv2.dilate(fgmask, kernel, iterations=2)

            # Find contours (potential vehicles) in ROI
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detections = []
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                area = w * h
                if area < MIN_CONTOUR_AREA:
                    continue  # too small to be a vehicle candidate

                aspect_ratio = w / float(h) if h > 0 else 0
                if aspect_ratio < MIN_ASPECT_RATIO:
                    # likely a person or vertical blob, skip
                    continue

                cx = x + w // 2
                cy = y + h // 2
                detections.append((x, y, w, h, cx, cy))

            # Merge nearby detections (NEW: reduces multiple boxes on same vehicle)
            detections = self._merge_nearby_detections(detections)

            # Update tracks with the new detections (in downscaled ROI coords)
            self._match_detections_to_tracks(detections, frame_idx)

            # Check line crossings (now with spatial cooldown)
            self._check_crossings(frame_idx)

            # ----- DRAWING ON FULL FRAME -----

            # First, draw ROI rectangle on full frame
            cv2.rectangle(
                frame,
                (self.roi_x_left, self.roi_y_top),
                (self.roi_x_right, self.roi_y_bottom),
                (0, 255, 255),
                2
            )

            # Draw entrance line mapped to full-frame coords
            line_left_full = self._roi_to_full_coords(0, self.line_position)
            line_right_full = self._roi_to_full_coords(ds_width, self.line_position)
            cv2.line(
                frame,
                line_left_full,
                line_right_full,
                (0, 255, 0),
                2
            )

            # Draw tracks on full frame
            for track in self.tracks.values():
                cx_ds, cy_ds = track.last_centroid
                cx_full, cy_full = self._roi_to_full_coords(cx_ds, cy_ds)

                # Draw centroid
                cv2.circle(frame, (cx_full, cy_full), 4, (0, 255, 255), -1)
                # Draw ID label
                cv2.putText(
                    frame,
                    f"ID:{track.id}",
                    (cx_full - 10, cy_full - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    1
                )
                # Draw history trail
                if len(track.history) > 1:
                    pts_full = []
                    for (hx, hy) in track.history:
                        fx, fy = self._roi_to_full_coords(hx, hy)
                        pts_full.append([fx, fy])
                    pts_full = np.array(pts_full, dtype=np.int32)
                    cv2.polylines(frame, [pts_full], False, (230, 230, 230), 2)

            # Draw detections (bounding boxes) in full frame
            for x_ds, y_ds, w_ds, h_ds, cx, cy in detections:
                x1_full, y1_full, x2_full, y2_full = self._box_roi_to_full(x_ds, y_ds, w_ds, h_ds)
                cv2.rectangle(frame, (x1_full, y1_full), (x2_full, y2_full), (255, 0, 0), 2)

            # Draw stats (top-left of full frame)
            cv2.putText(
                frame,
                f"Entries: {self.entries}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            cv2.putText(
                frame,
                f"Exits: {self.exits}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            cv2.putText(
                frame,
                f"Net: {self.entries - self.exits}",
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2
            )
            cv2.putText(
                frame,
                f"Frame: {frame_idx}/{total_frames}",
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            # Write frame if requested
            if save_output and out is not None:
                out.write(frame)

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
        print("FINAL STATISTICS (Classical OpenCV + ROI on Full Frame, v2)")
        print("=" * 50)
        print(f"Total Entries: {self.entries}")
        print(f"Total Exits: {self.exits}")
        print(f"Net Change: {self.entries - self.exits}")
        print(f"Frames Processed: {frame_idx}/{total_frames}")
        print(f"Total Time: {elapsed:.2f} s")
        print(f"Effective Processing FPS (downscaled ROI): {fps_effective:.2f}")
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Parking lot entrance monitor using classical OpenCV on an ROI "
                    "(no YOLO, headless, full-frame output, v2)."
    )
    parser.add_argument("video", type=str, help="Path to input video file")
    parser.add_argument(
        "--line",
        type=int,
        default=None,
        help="Y position of entrance line (in downscaled ROI coords). "
             "If omitted, it is chosen automatically."
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save annotated video to parking_entrance_output_opencv_roi_fullframe_v2.mp4"
    )

    args = parser.parse_args()

    monitor = ParkingEntranceMonitorCVROI(args.video, args.line)
    monitor.process_video(save_output=args.save)


if __name__ == "__main__":
    main()
