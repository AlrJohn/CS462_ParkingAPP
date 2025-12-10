"""
Parking Lot Entrance Counter - HEADLESS VERSION (Count Only)

Pure processing mode - NO video output, NO visualization
Optimized for maximum speed and minimal resource usage

Focus: Get accurate entry/exit counts as fast as possible
"""

import cv2
import numpy as np
import argparse
import time
import math
from collections import defaultdict


# ===== Configuration =====

DOWNSCALE_WIDTH_ROI = 480
MIN_CONTOUR_AREA = 1500
MIN_ASPECT_RATIO = 1.2
MAX_TRACK_DIST = 80
TRACK_FORGET_FRAMES = 30
TRACK_FORGET_FRAMES_NEAR_LINE = 60
NEAR_LINE_DISTANCE = 50
LINE_VERTICAL_OFFSET_PIXELS = -65
MIN_TOTAL_MOVE_PIXELS = 10
MERGE_DETECTION_DISTANCE = 60
CROSSING_SPATIAL_COOLDOWN_DIST = 100
CROSSING_COOLDOWN_FRAMES = 15
MAX_TRACK_DIST_LOST = 120
MAX_TRACK_HISTORY_LENGTH = 20

# ROI configuration (from existing scripts)
ROI_X_LEFT_FRAC = 1.0 / 4.0
ROI_X_RIGHT_FRAC = 0.90
ROI_Y_TOP_FRAC = 1.0 / 3.0
ROI_Y_BOTTOM_FRAC = 0.90


class Track:
    """Lightweight track object for counting."""
    __slots__ = ['id', 'history', 'last_x', 'last_y', 'last_frame',
                 'first_y', 'vx', 'vy', 'counted_entry', 'counted_exit']

    def __init__(self, track_id, cx, cy, frame_idx):
        self.id = track_id
        self.history = [(cx, cy)]
        self.last_x = cx
        self.last_y = cy
        self.last_frame = frame_idx
        self.first_y = cy
        self.vx = 0.0
        self.vy = 0.0
        self.counted_entry = False
        self.counted_exit = False

    def update(self, cx, cy, frame_idx):
        """Update track position."""
        frames_elapsed = frame_idx - self.last_frame
        if frames_elapsed > 0:
            vx = (cx - self.last_x) / frames_elapsed
            vy = (cy - self.last_y) / frames_elapsed
            # Smooth velocity
            alpha = 0.7
            self.vx = alpha * vx + (1 - alpha) * self.vx
            self.vy = alpha * vy + (1 - alpha) * self.vy

        self.last_x = cx
        self.last_y = cy
        self.history.append((cx, cy))

        # Limit history
        if len(self.history) > MAX_TRACK_HISTORY_LENGTH:
            self.history.pop(0)

        self.last_frame = frame_idx

    def predict(self, frame_idx):
        """Predict position based on velocity."""
        dt = frame_idx - self.last_frame
        if dt == 0:
            return self.last_x, self.last_y
        return int(self.last_x + self.vx * dt), int(self.last_y + self.vy * dt)


class EntranceCounter:
    """Headless entrance/exit counter - pure processing, no visualization."""

    def __init__(self, video_path, line_position=None, frame_skip=2):
        self.video_path = video_path
        self.line_position = line_position
        self.frame_skip = frame_skip  # Process every Nth frame (1=all, 2=every other, 3=every third)

        self.tracks = {}
        self.next_id = 1
        self.entries = 0
        self.exits = 0
        self.recent_crossings = []

        # Pre-create kernel
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        # Timing
        self.timing = defaultdict(float)

    def _distance_sq(self, x1, y1, x2, y2):
        """Squared distance for faster comparison."""
        dx = x1 - x2
        dy = y1 - y2
        return dx*dx + dy*dy

    def _merge_detections(self, detections):
        """Merge nearby detections."""
        if len(detections) <= 1:
            return detections

        remaining = list(detections)
        merged = []
        merge_dist_sq = MERGE_DETECTION_DISTANCE * MERGE_DETECTION_DISTANCE

        while remaining:
            cluster = [remaining.pop(0)]

            i = 0
            while i < len(remaining):
                det = remaining[i]
                is_close = False

                for cluster_det in cluster:
                    dist_sq = self._distance_sq(det[4], det[5], cluster_det[4], cluster_det[5])
                    if dist_sq < merge_dist_sq:
                        is_close = True
                        break

                if is_close:
                    cluster.append(remaining.pop(i))
                else:
                    i += 1

            if len(cluster) == 1:
                merged.append(cluster[0])
            else:
                # Merge bounding boxes
                min_x = min(d[0] for d in cluster)
                min_y = min(d[1] for d in cluster)
                max_x = max(d[0] + d[2] for d in cluster)
                max_y = max(d[1] + d[3] for d in cluster)
                w = max_x - min_x
                h = max_y - min_y
                cx = min_x + w // 2
                cy = min_y + h // 2
                merged.append((min_x, min_y, w, h, cx, cy))

        return merged

    def _match_tracks(self, detections, frame_idx):
        """Match detections to tracks."""
        unmatched = detections.copy()

        for track in self.tracks.values():
            best_det = None
            best_dist_sq = None

            # Predict position for lost tracks
            dt = frame_idx - track.last_frame
            if dt > 0:
                px, py = track.predict(frame_idx)
                max_dist = MAX_TRACK_DIST_LOST if dt > 1 else MAX_TRACK_DIST
            else:
                px, py = track.last_x, track.last_y
                max_dist = MAX_TRACK_DIST

            max_dist_sq = max_dist * max_dist

            for det in unmatched:
                dist_sq = self._distance_sq(px, py, det[4], det[5])
                if (best_dist_sq is None or dist_sq < best_dist_sq) and dist_sq <= max_dist_sq:
                    best_dist_sq = dist_sq
                    best_det = det

            if best_det is not None:
                track.update(best_det[4], best_det[5], frame_idx)
                unmatched.remove(best_det)

        # Create new tracks
        for det in unmatched:
            self.tracks[self.next_id] = Track(self.next_id, det[4], det[5], frame_idx)
            self.next_id += 1

        # Remove old tracks
        to_delete = []
        for tid, track in self.tracks.items():
            dist_to_line = abs(track.last_y - self.line_position)
            threshold = TRACK_FORGET_FRAMES_NEAR_LINE if dist_to_line < NEAR_LINE_DISTANCE else TRACK_FORGET_FRAMES

            if frame_idx - track.last_frame > threshold:
                to_delete.append(tid)

        for tid in to_delete:
            del self.tracks[tid]

    def _check_crossings(self, frame_idx):
        """Check for line crossings and update counts."""
        # Clean old crossings
        self.recent_crossings = [
            (x, f, d) for x, f, d in self.recent_crossings
            if frame_idx - f <= CROSSING_COOLDOWN_FRAMES
        ]

        for track in self.tracks.values():
            if track.counted_entry or track.counted_exit:
                continue

            if len(track.history) < 2:
                continue

            prev_y = track.history[-2][1]
            curr_y = track.history[-1][1]
            curr_x = track.history[-1][0]

            dy_total = curr_y - track.first_y

            if abs(dy_total) < MIN_TOTAL_MOVE_PIXELS:
                continue

            # Check for crossing
            if prev_y < self.line_position <= curr_y and dy_total > 0:
                # Entry
                if not self._too_close_to_recent(curr_x, frame_idx, 'entry'):
                    self.entries += 1
                    track.counted_entry = True
                    self.recent_crossings.append((curr_x, frame_idx, 'entry'))

            elif prev_y > self.line_position >= curr_y and dy_total < 0:
                # Exit
                if not self._too_close_to_recent(curr_x, frame_idx, 'exit'):
                    self.exits += 1
                    track.counted_exit = True
                    self.recent_crossings.append((curr_x, frame_idx, 'exit'))

    def _too_close_to_recent(self, x, frame_idx, direction):
        """Check spatial/temporal cooldown."""
        for rx, rf, rd in self.recent_crossings:
            if rd == direction and abs(x - rx) < CROSSING_SPATIAL_COOLDOWN_DIST:
                return True
        return False

    def process(self):
        """Process video and return counts."""
        t_total = time.time()

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"ERROR: Cannot open {self.video_path}")
            return None

        # Video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or np.isnan(fps):
            fps = 30.0

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"\n{'='*60}")
        print(f"HEADLESS COUNTER - Pure Processing Mode")
        print(f"{'='*60}")
        print(f"Video: {width}x{height} @ {fps:.1f} fps | {total_frames} frames")

        # ROI setup
        roi_x1 = int(width * ROI_X_LEFT_FRAC)
        roi_x2 = int(width * ROI_X_RIGHT_FRAC)
        roi_y1 = int(height * ROI_Y_TOP_FRAC)
        roi_y2 = int(height * ROI_Y_BOTTOM_FRAC)

        roi_width = roi_x2 - roi_x1
        roi_height = roi_y2 - roi_y1

        scale = DOWNSCALE_WIDTH_ROI / float(roi_width)
        ds_width = DOWNSCALE_WIDTH_ROI
        ds_height = int(roi_height * scale)

        print(f"ROI: [{roi_x1}:{roi_x2}, {roi_y1}:{roi_y2}] => {roi_width}x{roi_height}")
        print(f"Downscaled: {ds_width}x{ds_height}")

        # Line position
        if self.line_position is None:
            base = int(ds_height * 0.75)
            self.line_position = base + LINE_VERTICAL_OFFSET_PIXELS
            self.line_position = max(0, min(ds_height - 1, self.line_position))

        print(f"Line position: Y={self.line_position}")
        if self.frame_skip > 0:
            print(f"Frame skip: Skipping {self.frame_skip} frame(s) after each processed frame")
            print(f"  -> Processing frames: 1, {self.frame_skip + 2}, {2*(self.frame_skip + 1) + 1}, ...")
        else:
            print(f"Frame skip: Processing ALL frames")

        # Background subtractor
        bg_sub = cv2.createBackgroundSubtractorMOG2(
            history=600, varThreshold=40, detectShadows=True
        )
        learning_rate = 0.005

        print(f"\n{'='*60}")
        print("Processing...")
        print(f"{'='*60}\n")

        frame_idx = 0
        processed_frames = 0
        t_process = time.time()

        while True:
            # ALWAYS grab the next frame (fast - just advances position)
            if not cap.grab():
                break

            frame_idx += 1

            # Decide if we should process this frame
            # With --skip 2: process frames 1, 4, 7, 10... (skip 2 frames after each processed frame)
            # Formula: process frame if (frame_idx - 1) is divisible by (skip + 1)
            if (frame_idx - 1) % (self.frame_skip + 1) != 0:
                continue  # Skip processing (frame already grabbed, just not decoded)

            # Decode the frame we just grabbed
            t0 = time.time()
            ret, frame = cap.retrieve()
            if not ret:
                break
            self.timing['read'] += time.time() - t0

            processed_frames += 1

            # Extract and resize ROI
            t0 = time.time()
            roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
            roi_small = cv2.resize(roi, (ds_width, ds_height), interpolation=cv2.INTER_NEAREST)
            self.timing['resize'] += time.time() - t0

            # Grayscale
            t0 = time.time()
            gray = cv2.cvtColor(roi_small, cv2.COLOR_BGR2GRAY)
            self.timing['gray'] += time.time() - t0

            # Background subtraction
            t0 = time.time()
            mask = bg_sub.apply(gray, learningRate=learning_rate)
            _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
            self.timing['bgsub'] += time.time() - t0

            # Morphology
            t0 = time.time()
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel, iterations=1)
            mask = cv2.dilate(mask, self.kernel, iterations=2)
            self.timing['morph'] += time.time() - t0

            # Contours
            t0 = time.time()
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            self.timing['contours'] += time.time() - t0

            # Extract detections
            t0 = time.time()
            detections = []
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w * h < MIN_CONTOUR_AREA:
                    continue
                if h > 0 and (w / float(h)) < MIN_ASPECT_RATIO:
                    continue
                detections.append((x, y, w, h, x + w//2, y + h//2))
            self.timing['detect'] += time.time() - t0

            # Merge
            t0 = time.time()
            detections = self._merge_detections(detections)
            self.timing['merge'] += time.time() - t0

            # Track matching
            t0 = time.time()
            self._match_tracks(detections, frame_idx)
            self.timing['track'] += time.time() - t0

            # Check crossings
            t0 = time.time()
            self._check_crossings(frame_idx)
            self.timing['cross'] += time.time() - t0

            # Progress
            if processed_frames % 100 == 0:
                elapsed = time.time() - t_process
                current_fps = processed_frames / elapsed
                print(f"Processed {processed_frames} frames ({frame_idx}/{total_frames} total) | "
                      f"FPS: {current_fps:.1f} | "
                      f"Entries: {self.entries} | Exits: {self.exits}")

        cap.release()

        process_time = time.time() - t_process
        total_time = time.time() - t_total

        # Calculate correct metrics
        video_duration = total_frames / fps  # How long the video is in seconds
        realtime_factor = video_duration / process_time  # Video duration / processing time
        process_fps = processed_frames / process_time  # How fast we process frames

        # Results
        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")
        print(f"Entries: {self.entries}")
        print(f"Exits: {self.exits}")
        print(f"Net Change: {self.entries - self.exits}")
        print(f"\n{'='*60}")
        print("PERFORMANCE")
        print(f"{'='*60}")
        print(f"Video Duration: {video_duration:.2f}s @ {fps:.1f} fps")
        print(f"Total Frames in Video: {total_frames}")
        print(f"Frames Read: {frame_idx}")
        print(f"Frames Processed: {processed_frames} ({100*processed_frames/frame_idx:.1f}%)")
        print(f"Processing Time: {process_time:.2f}s")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Processing Speed: {process_fps:.2f} frames/sec")
        print(f"Realtime Factor: {realtime_factor:.2f}x", end="")
        if realtime_factor >= 1.0:
            print(f" ✓ FASTER than realtime!")
        else:
            print(f" (slower than realtime)")
        if self.frame_skip > 0:
            theoretical_speedup = self.frame_skip + 1
            print(f"Theoretical Speedup: {theoretical_speedup:.1f}x (skipping {self.frame_skip} frames each time)")

        # Timing breakdown
        if processed_frames > 0:
            print(f"\n{'='*60}")
            print("TIMING BREAKDOWN (avg per processed frame)")
            print(f"{'='*60}")
            for key in sorted(self.timing.keys()):
                avg_ms = (self.timing[key] / processed_frames) * 1000
                pct = (self.timing[key] / process_time) * 100
                print(f"{key:.<15} {avg_ms:>7.2f} ms ({pct:>5.1f}%)")

        print(f"{'='*60}\n")

        return {
            'entries': self.entries,
            'exits': self.exits,
            'net': self.entries - self.exits,
            'process_fps': process_fps,
            'realtime_factor': realtime_factor,
            'video_duration': video_duration,
            'total_frames': frame_idx,
            'processed_frames': processed_frames,
            'process_time': process_time
        }


def main():
    parser = argparse.ArgumentParser(
        description="Headless entrance counter - pure processing, no video output"
    )
    parser.add_argument("video", help="Input video file")
    parser.add_argument("--line", type=int, help="Line Y position (ROI coords)")
    parser.add_argument("--skip", type=int, default=2,
                        help="Skip N frames after each processed frame (default: 2 = process frames 1,4,7,10..., 0 = process all frames)")

    args = parser.parse_args()

    counter = EntranceCounter(args.video, args.line, args.skip)
    result = counter.process()

    if result:
        print(f"\nFinal: {result['entries']} entries, {result['exits']} exits, "
              f"net={result['net']} | "
              f"Realtime: {result['realtime_factor']:.2f}x "
              f"({result['processed_frames']}/{result['total_frames']} frames processed)")


if __name__ == "__main__":
    main()
