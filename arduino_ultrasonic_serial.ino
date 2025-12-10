/*
 * Ultrasonic Sensor Serial Output for Raspberry Pi
 * Reads distance from HC-SR04 ultrasonic sensor
 * Sends data via Serial (works with both USB and GPIO UART)
 *
 * Wiring:
 *   Ultrasonic VCC  -> Arduino 5V
 *   Ultrasonic GND  -> Arduino GND
 *   Ultrasonic TRIG -> Arduino Pin 9
 *   Ultrasonic ECHO -> Arduino Pin 10
 *
 * For GPIO connection to Raspberry Pi:
 *   Arduino TX (pin 1) -> Pi GPIO 15 (pin 10)
 *   Arduino RX (pin 0) -> Pi GPIO 14 (pin 8)
 *   Arduino GND        -> Pi GND
 */

// Pin definitions
const int trigPin = 9;
const int echoPin = 10;

// Variables
long duration;
int distance;

void setup() {
  // Initialize serial communication at 9600 baud
  Serial.begin(9600);

  // Initialize ultrasonic sensor pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // Wait for serial to initialize
  delay(1000);

  Serial.println("Ultrasonic Sensor Initialized");
  Serial.println("Distance readings in cm:");
}

void loop() {
  // Clear the trigger pin
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  // Send 10us pulse to trigger
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Read the echo pin (returns time in microseconds)
  duration = pulseIn(echoPin, TIMEOUT, 30000); // 30ms timeout

  // Calculate distance in cm (speed of sound = 343 m/s)
  // distance = duration * 0.034 / 2
  distance = duration * 0.034 / 2;

  // Check for valid reading
  if (distance == 0 || distance > 400) {
    Serial.println("Out of range");
  } else {
    // Send formatted output
    Serial.print("Distance: ");
    Serial.print(distance);
    Serial.println(" cm");
  }

  // Wait before next reading
  delay(500);  // Read every 500ms
}
