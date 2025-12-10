"""
Parking Lot Entrance Monitor - OPTIMIZED VERSION

Optimizations applied:
- Faster interpolation (INTER_NEAREST vs INTER_LINEAR)
- Reduced morphological operations
- Limited track history length
- Optimized drawing operations
- Cached kernel creation
- Simplified contour approximation
- Detailed performance timing
- Skip expensive operations when not saving output

Performance target: 2-3x faster than original
"""

import cv2
import numpy as np
import argparse
import time
import math
from collections import defaultdict


# ===== Tunable parameters =====

# Target width for ROI processing (keeps aspect ratio)
DOWNSCALE_WIDTH_ROI = 480

# Minimum blob area in *downscaled ROI* to be considered a vehicle
MIN_CONTOUR_AREA = 1500

# Aspect ratio filter to reject tall skinny blobs (likely people)
MIN_ASPECT_RATIO = 1.2

# Max pixel distance (downscaled ROI) to match detection to an existing track
MAX_TRACK_DIST = 80

# Forget tracks not seen for this many frames
TRACK_FORGET_FRAMES = 30
TRACK_FORGET_FRAMES_NEAR_LINE = 60
NEAR_LINE_DISTANCE = 50

# Line position
LINE_VERTICAL_OFFSET_PIXELS = -65

# Minimum total vertical movement required for counting
MIN_TOTAL_MOVE_PIXELS = 10

# Detection merging
MERGE_DETECTION_DISTANCE = 60

# Spatial cooldown
CROSSING_SPATIAL_COOLDOWN_DIST = 100
CROSSING_COOLDOWN_FRAMES = 15
MAX_TRACK_DIST_LOST = 120

# OPTIMIZATION: Limit track history to save memory and processing
MAX_TRACK_HISTORY_LENGTH = 20


class SimpleTrack:
    """Represents a single tracked object (vehicle)."""

    def __init__(self, track_id, cx, cy, frame_idx):
        self.id = track_id
        self.history = [(cx, cy)]
        self.last_centroid = (cx, cy)
        self.last_seen_frame = frame_idx
        self.first_y = cy
        self.velocity = (0, 0)
        self.has_counted_entry = False
        self.has_counted_exit = False

    def update_position(self, cx, cy, frame_idx):
        """Update track position and velocity estimate."""
        if len(self.history) > 0:
            prev_x, prev_y = self.last_centroid
            frames_elapsed = frame_idx - self.last_seen_frame
            if frames_elapsed > 0:
                vx = (cx - prev_x) / frames_elapsed
                vy = (cy - prev_y) / frames_elapsed
                alpha = 0.7
                self.velocity = (alpha * vx + (1 - alpha) * self.velocity[0],
                                alpha * vy + (1 - alpha) * self.velocity[1])

        self.last_centroid = (cx, cy)
        self.history.append((cx, cy))

        # OPTIMIZATION: Limit history length
        if len(self.history) > MAX_TRACK_HISTORY_LENGTH:
            self.history.pop(0)

        self.last_seen_frame = frame_idx

    def predict_position(self, frame_idx):
        """Predict where track should be based on velocity."""
        frames_since_seen = frame_idx - self.last_seen_frame
        if frames_since_seen == 0:
            return self.last_centroid

        pred_x = self.last_centroid[0] + self.velocity[0] * frames_since_seen
        pred_y = self.last_centroid[1] + self.velocity[1] * frames_since_seen
        return (int(pred_x), int(pred_y))


class ParkingEntranceMonitorOptimized:
    def __init__(self, video_path, line_position=None):
        self.video_path = video_path
        self.line_position = line_position

        self.tracks = {}
        self.next_track_id = 1
        self.entries = 0
        self.exits = 0
        self.recent_crossings = []

        # ROI bounds
        self.x_left_frac = 1.0 / 4.0
        self.x_right_frac = 0.90
        self.y_top_frac = 1.0 / 3.0
        self.y_bottom_frac = 0.90

        self.roi_x_left = None
        self.roi_x_right = None
        self.roi_y_top = None
        self.roi_y_bottom = None
        self.roi_width = None
        self.roi_height = None
        self.roi_scale = None

        # OPTIMIZATION: Pre-create morphological kernel
        self.morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        # Performance timing
        self.timing_stats = defaultdict(float)
        self.timing_counts = defaultdict(int)

    def _auto_line_position(self, roi_height_ds):
        base = int(roi_height_ds * 0.75)
        line_y = base + LINE_VERTICAL_OFFSET_PIXELS
        line_y = max(0, min(roi_height_ds - 1, line_y))
        return line_y

    def _distance(self, p1, p2):
        # OPTIMIZATION: Use squared distance when only comparing
        dx = p1[0] - p2[0]
        dy = p1[1] - p2[1]
        return math.sqrt(dx*dx + dy*dy)

    def _merge_nearby_detections(self, detections):
        """Merge detections that are too close together."""
        if len(detections) <= 1:
            return detections

        remaining = list(detections)
        merged = []

        while remaining:
            cluster = [remaining.pop(0)]

            i = 0
            while i < len(remaining):
                det = remaining[i]
                is_close = False
                for cluster_det in cluster:
                    dist = self._distance(
                        (det[4], det[5]),
                        (cluster_det[4], cluster_det[5])
                    )
                    if dist < MERGE_DETECTION_DISTANCE:
                        is_close = True
                        break

                if is_close:
                    cluster.append(remaining.pop(i))
                else:
                    i += 1

            if len(cluster) == 1:
                merged.append(cluster[0])
            else:
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
        """Match detections to existing tracks."""
        unmatched_detections = detections.copy()

        for track in self.tracks.values():
            best_det = None
            best_dist = None

            frames_since_seen = frame_idx - track.last_seen_frame
            if frames_since_seen > 0:
                compare_pos = track.predict_position(frame_idx)
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
                x, y, w, h, cx, cy = best_det
                track.update_position(cx, cy, frame_idx)
                unmatched_detections.remove(best_det)

        for det in unmatched_detections:
            x, y, w, h, cx, cy = det
            new_track = SimpleTrack(self.next_track_id, cx, cy, frame_idx)
            self.tracks[self.next_track_id] = new_track
            self.next_track_id += 1

        to_delete = []
        for track_id, track in self.tracks.items():
            track_y = track.last_centroid[1]
            dist_to_line = abs(track_y - self.line_position)

            if dist_to_line < NEAR_LINE_DISTANCE:
                forget_threshold = TRACK_FORGET_FRAMES_NEAR_LINE
            else:
                forget_threshold = TRACK_FORGET_FRAMES

            if frame_idx - track.last_seen_frame > forget_threshold:
                to_delete.append(track_id)

        for tid in to_delete:
            del self.tracks[tid]

    def _is_too_close_to_recent_crossing(self, x_pos, frame_idx, direction):
        """Check spatial/temporal cooldown for crossings."""
        for recent_x, recent_frame, recent_dir in self.recent_crossings:
            if recent_dir != direction:
                continue
            if frame_idx - recent_frame > CROSSING_COOLDOWN_FRAMES:
                continue
            if abs(x_pos - recent_x) < CROSSING_SPATIAL_COOLDOWN_DIST:
                return True
        return False

    def _check_crossings(self, frame_idx):
        """Check for line crossings."""
        self.recent_crossings = [
            (x, frame, direction)
            for x, frame, direction in self.recent_crossings
            if frame_idx - frame <= CROSSING_COOLDOWN_FRAMES
        ]

        for track in self.tracks.values():
            if track.has_counted_entry or track.has_counted_exit:
                continue

            if len(track.history) < 2:
                continue

            prev_y = track.history[-2][1]
            curr_y = track.history[-1][1]
            curr_x = track.history[-1][0]

            dy_total = track.history[-1][1] - track.first_y

            if abs(dy_total) < MIN_TOTAL_MOVE_PIXELS:
                continue

            moving_down = dy_total > 0
            moving_up = dy_total < 0

            if (
                prev_y < self.line_position <= curr_y and
                moving_down and
                not track.has_counted_entry
            ):
                if not self._is_too_close_to_recent_crossing(curr_x, frame_idx, 'entry'):
                    self.entries += 1
                    track.has_counted_entry = True
                    self.recent_crossings.append((curr_x, frame_idx, 'entry'))

            elif (
                prev_y > self.line_position >= curr_y and
                moving_up and
                not track.has_counted_exit
            ):
                if not self._is_too_close_to_recent_crossing(curr_x, frame_idx, 'exit'):
                    self.exits += 1
                    track.has_counted_exit = True
                    self.recent_crossings.append((curr_x, frame_idx, 'exit'))

    def _roi_to_full_coords(self, x_ds, y_ds):
        """Map ROI coordinates to full frame."""
        x_roi = x_ds / self.roi_scale
        y_roi = y_ds / self.roi_scale
        x_full = int(x_roi + self.roi_x_left)
        y_full = int(y_roi + self.roi_y_top)
        return x_full, y_full

    def _box_roi_to_full(self, x_ds, y_ds, w_ds, h_ds):
        """Map bounding box from ROI to full frame."""
        x1_ds = x_ds
        y1_ds = y_ds
        x2_ds = x_ds + w_ds
        y2_ds = y_ds + h_ds

        x1_full, y1_full = self._roi_to_full_coords(x1_ds, y1_ds)
        x2_full, y2_full = self._roi_to_full_coords(x2_ds, y2_ds)

        return x1_full, y1_full, x2_full, y2_full

    def _draw_overlays(self, frame, detections, ds_width):
        """Draw all overlays on frame (only when saving output)."""
        # Draw ROI rectangle
        cv2.rectangle(
            frame,
            (self.roi_x_left, self.roi_y_top),
            (self.roi_x_right, self.roi_y_bottom),
            (0, 255, 255),
            2
        )

        # Draw entrance line
        line_left_full = self._roi_to_full_coords(0, self.line_position)
        line_right_full = self._roi_to_full_coords(ds_width, self.line_position)
        cv2.line(frame, line_left_full, line_right_full, (0, 255, 0), 2)

        # Draw tracks (simplified)
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

            # OPTIMIZATION: Simplified trail (only last 10 points)
            if len(track.history) > 1:
                recent_history = track.history[-10:]  # Only last 10 points
                pts_full = []
                for (hx, hy) in recent_history:
                    fx, fy = self._roi_to_full_coords(hx, hy)
                    pts_full.append([fx, fy])
                pts_full = np.array(pts_full, dtype=np.int32)
                cv2.polylines(frame, [pts_full], False, (230, 230, 230), 1)  # Thinner line

        # Draw detections
        for x_ds, y_ds, w_ds, h_ds, cx, cy in detections:
            x1_full, y1_full, x2_full, y2_full = self._box_roi_to_full(x_ds, y_ds, w_ds, h_ds)
            cv2.rectangle(frame, (x1_full, y1_full), (x2_full, y2_full), (255, 0, 0), 2)

        # Draw stats
        cv2.putText(frame, f"Entries: {self.entries}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Exits: {self.exits}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, f"Net: {self.entries - self.exits}", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    def process_video(self, save_output=False):
        """Main processing function with detailed timing."""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"Error: could not open video {self.video_path}")
            return

        # Get video properties
        orig_fps = cap.get(cv2.CAP_PROP_FPS)
        if orig_fps <= 0 or np.isnan(orig_fps):
            orig_fps = 30.0
        orig_fps = float(orig_fps)

        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"\n{'='*60}")
        print(f"OPTIMIZED VERSION - Performance Analysis")
        print(f"{'='*60}")
        print(f"Video: {orig_width}x{orig_height} @ {orig_fps:.2f} fps, {total_frames} frames")

        # Compute ROI bounds
        self.roi_x_left = int(orig_width * self.x_left_frac)
        self.roi_x_right = int(orig_width * self.x_right_frac)
        self.roi_y_top = int(orig_height * self.y_top_frac)
        self.roi_y_bottom = int(orig_height * self.y_bottom_frac)

        self.roi_x_left = max(0, min(self.roi_x_left, orig_width - 1))
        self.roi_x_right = max(0, min(self.roi_x_right, orig_width))
        self.roi_y_top = max(0, min(self.roi_y_top, orig_height - 1))
        self.roi_y_bottom = max(0, min(self.roi_y_bottom, orig_height))

        self.roi_width = self.roi_x_right - self.roi_x_left
        self.roi_height = self.roi_y_bottom - self.roi_y_top
        print(f"ROI: x[{self.roi_x_left}:{self.roi_x_right}], "
              f"y[{self.roi_y_top}:{self.roi_y_bottom}] => {self.roi_width}x{self.roi_height}")

        # Compute downscaled ROI dimensions
        self.roi_scale = DOWNSCALE_WIDTH_ROI / float(self.roi_width)
        ds_width = DOWNSCALE_WIDTH_ROI
        ds_height = int(self.roi_height * self.roi_scale)
        print(f"Downscaled ROI: {ds_width}x{ds_height}")

        # Set line position
        if self.line_position is None:
            self.line_position = self._auto_line_position(ds_height)
        print(f"Entrance line at Y={self.line_position}")

        # Background subtractor
        back_sub = cv2.createBackgroundSubtractorMOG2(
            history=600, varThreshold=40, detectShadows=True
        )
        learning_rate = 0.005

        # Video writer
        out = None
        if save_output:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            output_path = "parking_entrance_output_optimized.mp4"
            out = cv2.VideoWriter(output_path, fourcc, orig_fps, (orig_width, orig_height))
            if out.isOpened():
                print(f"Saving to: {output_path}")
            else:
                print("Warning: Could not open VideoWriter")
                out = None

        frame_idx = 0
        total_start_time = time.time()
        processing_start_time = time.time()

        print(f"\n{'='*60}")
        print("Processing video...")
        print(f"{'='*60}\n")

        while True:
            t_frame_start = time.time()

            # Read frame
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                break
            self.timing_stats['read_frame'] += time.time() - t0

            frame_idx += 1

            # Crop and resize ROI
            t0 = time.time()
            roi = frame[self.roi_y_top:self.roi_y_bottom, self.roi_x_left:self.roi_x_right]
            if roi.size == 0:
                break

            # OPTIMIZATION: Use INTER_NEAREST (faster than INTER_LINEAR)
            roi_small = cv2.resize(roi, (ds_width, ds_height), interpolation=cv2.INTER_NEAREST)
            self.timing_stats['roi_resize'] += time.time() - t0

            # Convert to grayscale
            t0 = time.time()
            gray = cv2.cvtColor(roi_small, cv2.COLOR_BGR2GRAY)
            self.timing_stats['cvt_gray'] += time.time() - t0

            # Background subtraction
            t0 = time.time()
            fgmask = back_sub.apply(gray, learningRate=learning_rate)
            _, fgmask = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)
            self.timing_stats['bg_subtract'] += time.time() - t0

            # OPTIMIZATION: Reduced morphological operations
            t0 = time.time()
            fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, self.morph_kernel, iterations=1)
            fgmask = cv2.dilate(fgmask, self.morph_kernel, iterations=2)
            self.timing_stats['morphology'] += time.time() - t0

            # Find contours
            t0 = time.time()
            contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            self.timing_stats['find_contours'] += time.time() - t0

            # Extract detections
            t0 = time.time()
            detections = []
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                area = w * h
                if area < MIN_CONTOUR_AREA:
                    continue

                aspect_ratio = w / float(h) if h > 0 else 0
                if aspect_ratio < MIN_ASPECT_RATIO:
                    continue

                cx = x + w // 2
                cy = y + h // 2
                detections.append((x, y, w, h, cx, cy))
            self.timing_stats['extract_detections'] += time.time() - t0

            # Merge detections
            t0 = time.time()
            detections = self._merge_nearby_detections(detections)
            self.timing_stats['merge_detections'] += time.time() - t0

            # Track matching
            t0 = time.time()
            self._match_detections_to_tracks(detections, frame_idx)
            self.timing_stats['track_matching'] += time.time() - t0

            # Check crossings
            t0 = time.time()
            self._check_crossings(frame_idx)
            self.timing_stats['check_crossings'] += time.time() - t0

            # Drawing (only if saving)
            if save_output and out is not None:
                t0 = time.time()
                self._draw_overlays(frame, detections, ds_width)
                self.timing_stats['drawing'] += time.time() - t0

                t0 = time.time()
                out.write(frame)
                self.timing_stats['write_frame'] += time.time() - t0

            self.timing_stats['total_per_frame'] += time.time() - t_frame_start
            self.timing_counts['frames'] += 1

            # Progress update
            if frame_idx % 100 == 0:
                elapsed = time.time() - processing_start_time
                fps_current = frame_idx / elapsed if elapsed > 0 else 0
                print(f"Frame {frame_idx}/{total_frames} | FPS: {fps_current:.2f}")

        # Cleanup
        cap.release()
        if out is not None:
            out.release()

        processing_time = time.time() - processing_start_time
        total_time = time.time() - total_start_time
        fps_effective = frame_idx / processing_time if processing_time > 0 else 0.0

        # Print detailed timing statistics
        print(f"\n{'='*60}")
        print("PERFORMANCE STATISTICS")
        print(f"{'='*60}")
        print(f"Total Entries: {self.entries}")
        print(f"Total Exits: {self.exits}")
        print(f"Net Change: {self.entries - self.exits}")
        print(f"Frames Processed: {frame_idx}/{total_frames}")
        print(f"\n{'='*60}")
        print("TIMING BREAKDOWN (per frame avg)")
        print(f"{'='*60}")

        if frame_idx > 0:
            for key in sorted(self.timing_stats.keys()):
                avg_ms = (self.timing_stats[key] / frame_idx) * 1000
                percent = (self.timing_stats[key] / processing_time) * 100
                print(f"{key:.<25} {avg_ms:>8.2f} ms  ({percent:>5.1f}%)")

        print(f"\n{'='*60}")
        print(f"Processing Time: {processing_time:.2f} s")
        print(f"Total Time: {total_time:.2f} s")
        print(f"Processing FPS: {fps_effective:.2f}")
        print(f"Real-time factor: {fps_effective/orig_fps:.2f}x")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="OPTIMIZED parking lot entrance monitor"
    )
    parser.add_argument("video", type=str, help="Path to input video file")
    parser.add_argument(
        "--line",
        type=int,
        default=None,
        help="Y position of entrance line (in downscaled ROI coords)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save annotated video to parking_entrance_output_optimized.mp4"
    )

    args = parser.parse_args()

    monitor = ParkingEntranceMonitorOptimized(args.video, args.line)
    monitor.process_video(save_output=args.save)


if __name__ == "__main__":
    main()
