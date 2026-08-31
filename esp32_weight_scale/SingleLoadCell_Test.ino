#include "HX711.h"

// HX711 circuit wiring for single load cell
const int LOADCELL_DOUT_PIN = 13;  // DT pin
const int LOADCELL_SCK_PIN = 27;   // SCK pin

HX711 scale;

void setup() {
  Serial.begin(115200);

  // Wait for serial monitor to open
  unsigned long startTime = millis();
  while (!Serial && (millis() - startTime < 3000)) {
    // Wait up to 3 seconds
  }

  Serial.println("\n=== SINGLE LOAD CELL TEST ===");

  // Initialize the scale
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);

  if (scale.is_ready()) {
    Serial.println("✓ HX711 found and ready");

    // Set gain to 128 (channel A)
    scale.set_gain(128);

    // Tare the scale (reset to zero)
    scale.tare();
    Serial.println("✓ Scale tared (zero offset set)");
    Serial.println();
    Serial.println("Place weight on the load cell and watch the readings.");
    Serial.println("Readings are raw ADC counts (24-bit signed integer).");
    Serial.println("----------------------------------------");
  } else {
    Serial.println("✗ HX711 not found - check wiring!");
    Serial.println("Check:");
    Serial.println("  - DT pin to GPIO13");
    Serial.println("  - SCK pin to GPIO27");
    Serial.println("  - VCC to 3.3V, GND to GND");
    Serial.println("  - Load cell wires to HX711 E± and A±");
  }
}

void loop() {
  if (scale.is_ready()) {
    long reading = scale.read();  // Raw 24-bit ADC reading

    // Also get weight in arbitrary units (after tare)
    // Note: Without calibration factor, this is just raw/tare
    double weight = scale.get_value(5);  // Average 5 readings

    Serial.print("Raw ADC: ");
    Serial.print(reading);
    Serial.print(" | Value: ");
    Serial.print(weight);
    Serial.print(" | ");

    // Show if we detect significant change from zero
    if (abs(weight) > 100) {  // Adjust threshold as needed
      Serial.print("WEIGHT DETECTED! ");
    }

    Serial.println();
  } else {
    Serial.println("HX711 not ready");
  }

  delay(500);  // Read twice per second
}