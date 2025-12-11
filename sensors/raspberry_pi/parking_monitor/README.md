# Parking Monitor

Video processing system for tracking vehicles entering and exiting a parking lot using YOLO object detection.

## Project Structure

```
parking_monitor/
├── models/          # YOLO model files (.pt)
├── videos/          # Input video files
├── scripts/         # Processing scripts
├── output/          # Processed videos and reports
└── README.md        # This file
```

## Requirements

- Python 3.13
- OpenCV (opencv-python-headless)
- Ultralytics YOLO
- NumPy
- PyTorch (installed automatically with ultralytics)

## Installation

All dependencies are already installed on this Raspberry Pi.

## Usage

### IMPORTANT: Raspberry Pi Headless Mode

Since this Raspberry Pi uses `opencv-python-headless` (no GUI libraries), the video display window will not work. You must run the script in one of these modes:

### 1. Process and Save Video (Recommended):

```bash
cd ~/parking_monitor
python3 scripts/parking_entrance_monitor.py videos/parking_lot_entrance.MOV --save --no-display --line 400
```

This will:
- Process the video without displaying it
- Save the annotated video to `parking_entrance_output.mp4`
- Print statistics to the console
- Use line position Y=400 (adjust as needed)

### 2. Find the Right Line Position (Interactive):

First, extract a frame to find the right Y-coordinate for the line:

```bash
cd ~/parking_monitor
python3 -c "import cv2; cap = cv2.VideoCapture('videos/parking_lot_entrance.MOV'); ret, frame = cap.read(); print(f'Video dimensions: {frame.shape[1]}x{frame.shape[0]}'); cap.release()"
```

This will print the video dimensions. The Y-coordinate should be where the arrows are across the entrance (typically around 1/3 to 1/2 of the video height).

### 3. Process with Custom Settings:

```bash
# Process with specific line position
python3 scripts/parking_entrance_monitor.py videos/parking_lot_entrance.MOV --line 500 --no-display

# Process and save with custom model
python3 scripts/parking_entrance_monitor.py videos/parking_lot_entrance.MOV --model models/yolo11m.pt --save --no-display --line 450
```

## How It Works

1. **Vehicle Detection**: Uses YOLO11 to detect cars, motorcycles, buses, and trucks
2. **Tracking**: ByteTrack algorithm maintains consistent IDs across frames
3. **Line Crossing**: Monitors vehicle centroids crossing the entrance line
   - Above → Below = Entry (coming into parking lot)
   - Below → Above = Exit (leaving parking lot)
4. **Visualization**: Annotates video with bounding boxes, tracking trails, and statistics

## Output

The annotated video includes:
- Green horizontal line at the entrance
- Blue bounding boxes around vehicles
- Yellow centroids for each vehicle
- Gray tracking trails
- Entry/Exit notifications (green/red text)
- Live statistics (entries, exits, net change)

Console output shows:
- Real-time entry/exit events with vehicle IDs
- Frame-by-frame progress
- Final statistics summary

## Example Output

```
Video: 1920x1080 @ 30fps, 450 frames
Entrance line set at Y=400

Processing video with entrance line at Y=400
Direction: Below→Above = EXIT, Above→Below = ENTRY

Frame 45: Vehicle 3 ENTERED (Total: 1 in, 0 out)
Frame 102: Vehicle 5 ENTERED (Total: 2 in, 0 out)
Frame 234: Vehicle 3 EXITED (Total: 2 in, 1 out)
...

==================================================
FINAL STATISTICS
==================================================
Total Entries: 12
Total Exits: 8
Net Change: +4
Frames Processed: 450/450
==================================================
```

## Viewing the Output

After processing, you can:

1. **Copy the output video to your computer**:
   ```bash
   scp sensei@192.168.1.213:~/parking_monitor/parking_entrance_output.mp4 .
   ```

2. **View it locally** with any video player

## Command-line Options

```
python3 scripts/parking_entrance_monitor.py <video_path> [options]

Required:
  video                 Path to video file

Optional:
  --model PATH         Path to YOLO model (default: yolo11m.pt)
  --line Y             Y-coordinate of entrance line (default: interactive selection)
  --no-display         Run without displaying video (required on this Pi)
  --save              Save processed video to parking_entrance_output.mp4
```

## Notes

- The YOLO model processes each frame to detect vehicles
- Tracking IDs persist across frames to avoid double-counting
- Processing speed: ~2-5 FPS on Raspberry Pi (varies by model)
- A 30-second video at 30fps (900 frames) takes ~3-7 minutes to process
- Use `--no-display` flag on Raspberry Pi (opencv-headless doesn't support GUI)

## Troubleshooting

**ImportError: libGL.so.1**
- Already fixed - using opencv-python-headless

**Video processing is slow**
- This is normal on Raspberry Pi
- Consider processing shorter clips
- The 'm' model (yolo11m.pt) is a good balance of speed and accuracy

**Can't see the video while processing**
- Use `--save` to create an output video you can view later
- Or use SSH with X11 forwarding (not recommended, very slow)
