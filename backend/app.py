#Start - Test python file

# backend/app.py
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB = "backend/parking.db"

# -------------------------------
# Initialize database
# -------------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS lots (
            lot_id TEXT PRIMARY KEY,
            capacity INTEGER,
            current_count INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lot_id TEXT,
            event_type TEXT,
            timestamp TEXT
        )
    """)
    # Create one example parking lot
    c.execute("INSERT OR IGNORE INTO lots (lot_id, capacity, current_count) VALUES (?, ?, ?)",
              ("A", 10, 0))
    conn.commit()
    conn.close()


# -------------------------------
# Routes
# -------------------------------
@app.route("/update", methods=["POST"])
def update_lot():
    """Called when a car enters or exits."""
    data = request.get_json()
    lot_id = data.get("lot_id")
    event_type = data.get("event_type")  # "in" or "out"

    if not lot_id or event_type not in ("in", "out"):
        return jsonify({"error": "Invalid request"}), 400

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Record the event
    c.execute("INSERT INTO events (lot_id, event_type, timestamp) VALUES (?, ?, ?)",
              (lot_id, event_type, datetime.utcnow().isoformat()))

    # Update count
    if event_type == "in":
        c.execute("UPDATE lots SET current_count = current_count + 1 WHERE lot_id = ?", (lot_id,))
    else:
        c.execute("""
            UPDATE lots
            SET current_count = CASE WHEN current_count > 0 THEN current_count - 1 ELSE 0 END
            WHERE lot_id = ?
        """, (lot_id,))

    conn.commit()
    # Return current status
    row = c.execute("SELECT capacity, current_count FROM lots WHERE lot_id = ?", (lot_id,)).fetchone()
    conn.close()

    if row:
        cap, count = row
        occupancy = round((count / cap) * 100, 1)
        return jsonify({"lot_id": lot_id, "capacity": cap, "current_count": count, "occupancy_pct": occupancy})
    else:
        return jsonify({"error": "Lot not found"}), 404


@app.route("/status", methods=["GET"])
def get_status():
    """Get all parking lot data."""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    rows = c.execute("SELECT lot_id, capacity, current_count FROM lots").fetchall()
    conn.close()

    lots = []
    for lot_id, cap, cur in rows:
        lots.append({
            "lot_id": lot_id,
            "capacity": cap,
            "current_count": cur,
            "occupancy_pct": round((cur / cap) * 100, 1)
        })

    return jsonify(lots)


# -------------------------------
# Run app
# -------------------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=True)
