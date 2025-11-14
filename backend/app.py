# Backend Flask API for Parking App
# Penn State Abington - CMPSC 462 Final Project

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime, time
import threading
import time as time_module
from config import API_KEY, ALLOWED_ORIGINS, HOST, PORT, DEBUG

app = Flask(__name__)

# Enable CORS for frontend access
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# API Key validation function
def validate_api_key():
    """Validate API key from request headers."""
    provided_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if not provided_key:
        return False, "API key is required. Please provide X-API-Key header."
    if provided_key != API_KEY:
        return False, "Invalid API key."
    return True, None

# API Key decorator
def require_api_key(f):
    """Decorator to require API key for endpoints."""
    def decorated_function(*args, **kwargs):
        is_valid, error_msg = validate_api_key()
        if not is_valid:
            return jsonify({"error": error_msg}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# File path for parking data persistence
PARKING_DATA_FILE = "parking_data.json"

# Define parking lot capacities (fixed capacity for each lot)
lot_capacities = {
    "G": 169,
    "H": 238,
    "J": 153,
    "M": 167
}

# Initialize parking lots dictionary (4 lots: G, H, J, M, each starting at full capacity)
parking_lots = {
    "G": lot_capacities["G"],
    "H": lot_capacities["H"],
    "J": lot_capacities["J"],
    "M": lot_capacities["M"]
}

# -------------------------------
# Data Persistence Functions
# -------------------------------

def load_parking_data():
    """Load parking lot data from JSON file on startup."""
    global parking_lots
    if os.path.exists(PARKING_DATA_FILE):
        try:
            with open(PARKING_DATA_FILE, 'r') as f:
                data = json.load(f)
                # Validate that all lots G, H, J, M exist and have valid values
                for lot in ["G", "H", "J", "M"]:
                    capacity = lot_capacities[lot]
                    if lot in data and 0 <= data[lot] <= capacity:
                        parking_lots[lot] = data[lot]
                    else:
                        parking_lots[lot] = capacity  # Default to full capacity if invalid data
            print(f"Loaded parking data: {parking_lots}")
        except (json.JSONDecodeError, FileNotFoundError):
            print("Invalid or missing parking data file. Using default values.")
    else:
        print("No parking data file found. Using default values (all lots at full capacity).")

def save_parking_data():
    """Save current parking lot data to JSON file."""
    try:
        with open(PARKING_DATA_FILE, 'w') as f:
            json.dump(parking_lots, f, indent=2)
        print(f"Saved parking data: {parking_lots}")
    except Exception as e:
        print(f"Error saving parking data: {e}")

def reset_daily_data():
    """Reset all parking lots to full capacity (daily reset at 6 AM)."""
    global parking_lots
    for lot in parking_lots:
        parking_lots[lot] = lot_capacities[lot]
    save_parking_data()
    print("Daily reset completed: All lots reset to full capacity")

def daily_reset_scheduler():
    """Background thread to check for 6 AM daily reset."""
    while True:
        now = datetime.now()
        # Check if it's 6 AM
        if now.hour == 6 and now.minute == 0:
            reset_daily_data()
            # Sleep for 1 minute to avoid multiple resets
            time_module.sleep(60)
        else:
            # Check every minute
            time_module.sleep(60)

# -------------------------------
# API Endpoints
# -------------------------------

@app.route("/updateLotCount", methods=["POST"])
@require_api_key
def update_lot_count():
    """Update parking lot count when a car enters or exits."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        lot = data.get("lot")
        delta = data.get("delta")
        
        # Validate input
        if not lot or lot not in parking_lots:
            return jsonify({"error": f"Invalid lot. Must be one of: {list(parking_lots.keys())}"}), 400
        
        if delta is None or not isinstance(delta, int):
            return jsonify({"error": "Invalid delta. Must be an integer (-1 for car entering, +1 for car exiting)"}), 400
        
        if delta not in [-1, 1]:
            return jsonify({"error": "Delta must be -1 (car entering) or +1 (car exiting)"}), 400
        
        # Update available spaces
        current_spaces = parking_lots[lot]
        new_spaces = current_spaces + delta
        capacity = lot_capacities[lot]
        
        # Ensure spaces stay within valid range (0 to capacity)
        if new_spaces < 0:
            new_spaces = 0
        elif new_spaces > capacity:
            new_spaces = capacity
        
        parking_lots[lot] = new_spaces
        
        # Save to file
        save_parking_data()
        
        # Calculate occupancy percentage
        occupied_spaces = capacity - new_spaces
        occupancy_pct = round((occupied_spaces / capacity) * 100, 1)
        
        # Return updated lot information
        return jsonify({
            "lot": lot,
            "available_spaces": new_spaces,
            "capacity": capacity,
            "occupied_spaces": occupied_spaces,
            "occupancy_pct": occupancy_pct,
            "action": "car_entered" if delta == -1 else "car_exited"
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/setLotOccupancy", methods=["POST"])
@require_api_key
def set_lot_occupancy():
    """Set parking lot occupancy based on absolute count (for camera sensors)."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        lot = data.get("lot")
        occupied_count = data.get("occupied_count")

        # Validate input
        if not lot or lot not in parking_lots:
            return jsonify({"error": f"Invalid lot. Must be one of: {list(parking_lots.keys())}"}), 400

        if occupied_count is None or not isinstance(occupied_count, int):
            return jsonify({"error": "Invalid occupied_count. Must be an integer."}), 400

        if occupied_count < 0:
            return jsonify({"error": "occupied_count cannot be negative"}), 400

        capacity = lot_capacities[lot]

        # Ensure occupied count doesn't exceed capacity
        if occupied_count > capacity:
            occupied_count = capacity

        # Calculate available spaces (capacity - occupied)
        new_available_spaces = capacity - occupied_count

        # Update parking lot
        parking_lots[lot] = new_available_spaces

        # Save to file
        save_parking_data()

        # Calculate occupancy percentage
        occupancy_pct = round((occupied_count / capacity) * 100, 1)

        # Return updated lot information
        return jsonify({
            "lot": lot,
            "available_spaces": new_available_spaces,
            "capacity": capacity,
            "occupied_spaces": occupied_count,
            "occupancy_pct": occupancy_pct,
            "message": f"Lot {lot} updated with {occupied_count} occupied spots"
        })

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/getLotCount", methods=["GET"])
@require_api_key
def get_lot_count():
    """Get occupancy information for all parking lots."""
    try:
        lots_data = []

        for lot, available_spaces in parking_lots.items():
            capacity = lot_capacities[lot]
            occupied_spaces = capacity - available_spaces
            occupancy_pct = round((occupied_spaces / capacity) * 100, 1)

            lots_data.append({
                "lot": lot,
                "available_spaces": available_spaces,
                "capacity": capacity,
                "occupied_spaces": occupied_spaces,
                "occupancy_pct": occupancy_pct
            })

        return jsonify(lots_data)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500



# -------------------------------
# Initialize and Run App
# -------------------------------

if __name__ == "__main__":
    # Load existing data on startup
    load_parking_data()
    
    # Start daily reset scheduler in background thread
    reset_thread = threading.Thread(target=daily_reset_scheduler, daemon=True)
    reset_thread.start()
    
    print("Starting Parking App Backend...")
    print(f"Available lots: {list(parking_lots.keys())}")
    print(f"API Key: {API_KEY[:20]}... (first 20 chars)")
    print(f"CORS enabled for origins: {ALLOWED_ORIGINS}")
    print("Endpoints:")
    print("  POST /updateLotCount - Update lot count (requires API key)")
    print("  POST /setLotOccupancy - Set lot occupancy by count (requires API key)")
    print("  GET /getLotCount - Get all lot data (requires API key)")
    print(f"Server running on {HOST}:{PORT}")
    
    app.run(host=HOST, port=PORT, debug=DEBUG)