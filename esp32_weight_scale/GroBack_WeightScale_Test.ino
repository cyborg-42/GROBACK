/*
  GroBack Weight Scale Test - Reading 4 Load Cells via HX711
  For initial setup and calibration of the weight sensing system
*/

#include "HX711.h"

// HX711 circuit wiring - using shared SCK (clock) and separate DT (data) pins
const int SCK_PIN = 27;  // Shared clock pin for all HX711 modules
const int DT_PINS[4] = {13, 14, 25, 26};  // Data pins for each quadrant

// Create HX711 instances
HX711 scales[4];

void setup() {
  Serial.begin(115200);
  Serial.println("\nGroBack Weight Scale Test Initializing...");

  // Initialize each scale
  for (int i = 0; i < 4; i++) {
    scales[i].begin(DT_PINs[i], SCK_PIN);
    Serial.printf("Scale %d initialized on DT=%d, SCK=%d\n", i+1, DT_PINs[i], SCK_PIN);

    // Set gain to 128 (channel A, default)
    scales[i].set_gain(128);

    // Tare the scale (reset to zero)
    scales[i].tare();
    Serial.printf("Scale %d tared\n", i+1);
  }

  Serial.println("\nAll scales initialized and tared.");
  Serial.println("Place known weights on each quadrant to verify readings.");
  Serial.println("Readings are in raw ADC counts (higher = more weight).");
  Serial.println("----------------------------------------");
}

void loop() {
  Serial.print("Raw Readings: ");

  for (int i = 0; i < 4; i++) {
    if (scales[i].is_ready()) {
      // Read raw ADC value (24-bit signed integer)
      long raw reading = scales[i].read();
      Serial.print(raw reading);

      if (i < 3) Serial.print(" | ");
    } else {
      Serial.print("HX711 not found");
    }
  }

  Serial.println();
  delay(500);  // Read twice per second
}