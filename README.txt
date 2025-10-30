============================================================
PSUPark System Architecture
                +---------------------------+
                |      Users / Students     |
                +-------------+-------------+
                     |                   |
                     v                   v
             +----------------+   +------------------+
             |     Web App    |   |     Mobile App   |
             +--------+-------+   +--------+---------+
                      |                    |
                      |      REST API      |
                      v                    v
                 +-------------------------------+
                 |        Flask Backend API      |
                 | - Receive sensor events       |
                 | - Update parking counts       |
                 | - Serve real-time data        |
                 +--------------+----------------+
                                |
                                | DB Write / Read
                                v
                    +---------------------------+
                    |        Database           |
                    | Postgres / MongoDB        |
                    +-----------+---------------+
                                ^
                                | Parking Count Updates
                                |
+-------------------------------------------------------------------+
|                     Parking Lot Sensor Network                    |
|                                                                   |
|   +-----------------+    +-----------------+    +----------------+|
|   | Ultrasonic Unit |    | IR Beam Sensor |    | Camera + ML    | |
|   +--------+--------+    +--------+--------+    +-------+--------+|
|            |                     |                     |          |
|            +----------+----------+----------+----------+          |
|                       |                                     (HTTP or MQTT)
|                       v                                           |
|              +------------------------+                           |
|              |  Microcontroller       |<--------------------------+
|              | ESP32 / Pi / Arduino   |
|              +------------------------+
+-------------------------------------------------------------------+

============================================================
Backend Classes
+--------------------+
|     ParkingLot     |
+--------------------+
| lot_id             |
| name               |
| location           |
| total_slots        |
| current_count      |
+--------------------+
| update_count()     |
| get_available()    |
+---------+----------+
          ^
          | 1 to many
          |
+---------+----------+
|   SensorDevice     |
+--------------------+
| device_id          |
| lot_id             |
| type (ultra/IR/cam)|
| status             |
+--------------------+
| validate_signal()  |
| send_update()      |
+---------+----------+
          |
          | creates
          v
+--------------------+
|    SensorEvent     |
+--------------------+
| event_id           |
| device_id          |
| timestamp          |
| delta (+1 / -1)    |
+--------------------+
| log_event()        |
| push_to_lot()      |
+--------------------+

+--------------------+
|       User         |
+--------------------+
| user_id            |
| email              |
| role               |
| password_hash      |
+--------------------+
| authenticate()     |
| favorites()        |
+--------------------+

============================================================
Sensor Firmware / Embedded Diagram
                         +---------------------------+
                         |   SensorController (IF)   |
                         +---------------------------+
                         | read_data()               |
                         | detect_event()            |
                         | send_to_api()             |
                         +-------------+-------------+
                                       ^
           +---------------------------+--------------------------+
           |                           |                          |
           v                           v                          v
+-----------------------+    +--------------------+    +------------------------+
| UltrasonicController  |    | IRBreakBeamControl|    | CameraVisionController |
+-----------------------+    +--------------------+    +------------------------+
| trigger_pin           |    | input_pin          |    | camera_input           |
| echo_pin              |    |                    |    | ML_model               |
| distance_threshold    |    |                    |    | frame_rate             |
+-----------------------+    +--------------------+    +------------------------+
| measure_distance()    |    | detect_break()     |    | detect_vehicles()      |
| detect_event()        |    | detect_event()     |    | detect_event()         |
| send_to_api()         |    | send_to_api()      |    | send_to_api()          |
+-----------------------+    +--------------------+    +------------------------+

============================================================
Data Flow Diagram
        Car enters/exits
              |
               v
        +--------------+
        |   Sensor     |
        +------+-------+
               |
           Raw signal
               v
        +-----------------+
        | Microcontroller |
               |
        +------+----------+
        POST /event (+1 / -1)
               v
        +--------------+
        | Flask API    |
        +------+-------+
               |
        Update parking count
               v
        +--------------+
        | Database     |
        +------+-------+
               |
        Serve live status
               v
    +------------------------+
    | Web & Mobile Clients  |
    +------------------------+
               |
        Show available parking

============================================================