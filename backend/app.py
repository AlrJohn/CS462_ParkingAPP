# Backend Flask API for Parking App
# Penn State Abington - CMPSC 462 Final Project

from flask import Flask, request, jsonify
import json
from flask_cors import CORS
import os
from datetime import datetime, time
import threading
import time as time_module

app = Flask(__name__)
CORS(app)

# File path for parking data persistence
PARKING_DATA_FILE = "parking_data.json"

# Initialize parking lots dictionary (13 lots: A through M, each with 100 available spaces)
parking_lots = {
    "A": 100, "B": 100, "C": 100, "D": 100
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
                # Validate that all lots A-M exist and have valid values
                for lot in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M"]:
                    if lot in data and 0 <= data[lot] <= 100:
                        parking_lots[lot] = data[lot]
                    else:
                        parking_lots[lot] = 100  # Default to 100 if invalid data
            print(f"Loaded parking data: {parking_lots}")
        except (json.JSONDecodeError, FileNotFoundError):
            print("Invalid or missing parking data file. Using default values.")
    else:
        print("No parking data file found. Using default values (all lots at 100).")

def save_parking_data():
    """Save current parking lot data to JSON file."""
    try:
        with open(PARKING_DATA_FILE, 'w') as f:
            json.dump(parking_lots, f, indent=2)
        print(f"Saved parking data: {parking_lots}")
    except Exception as e:
        print(f"Error saving parking data: {e}")

def reset_daily_data():
    """Reset all parking lots to 100 available spaces (daily reset at 6 AM)."""
    global parking_lots
    for lot in parking_lots:
        parking_lots[lot] = 100
    save_parking_data()
    print("Daily reset completed: All lots reset to 100 available spaces")

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
        
        # Ensure spaces stay within valid range (0-100)
        if new_spaces < 0:
            new_spaces = 0
        elif new_spaces > 100:
            new_spaces = 100
        
        parking_lots[lot] = new_spaces
        
        # Save to file
        save_parking_data()
        
        # Calculate occupancy percentage
        occupied_spaces = 100 - new_spaces
        occupancy_pct = round((occupied_spaces / 100) * 100, 1)
        
        # Return updated lot information
        return jsonify({
            "lot": lot,
            "available_spaces": new_spaces,
            "capacity": 100,
            "occupied_spaces": occupied_spaces,
            "occupancy_pct": occupancy_pct,
            "action": "car_entered" if delta == -1 else "car_exited"
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/getLotCount", methods=["GET"])
def get_lot_count():
    """Get occupancy information for all parking lots."""
    try:
        lots_data = []
        
        for lot, available_spaces in parking_lots.items():
            occupied_spaces = 100 - available_spaces
            occupancy_pct = round((occupied_spaces / 100) * 100, 1)
            
            lots_data.append({
                "lot": lot,
                "available_spaces": available_spaces,
                "capacity": 100,
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
    print("Endpoints:")
    print("  POST /updateLotCount - Update lot count")
    print("  GET /getLotCount - Get all lot data")
    
    app.run(host="0.0.0.0", port=5002, debug=True)