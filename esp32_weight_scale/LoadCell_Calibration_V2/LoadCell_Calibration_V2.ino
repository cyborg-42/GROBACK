
  #include "HX711.h"

  // HX711 circuit wiring
  const int LOADCELL_DOUT_PIN = 13;  // DT pin
  const int LOADCELL_SCK_PIN = 27;   // SCK pin

  HX711 scale;

  void setup() {
    Serial.begin(115200);

    // Wait for serial monitor
    unsigned long startTime = millis();
    while (!Serial && (millis() - startTime < 3000)) {
      // Wait up to 3 seconds
    }

    Serial.println("\n=== LOAD CELL VERIFICATION TEST ===");
    Serial.println("Checking if HX711 detects weight changes...");

    // Initialize the scale
    scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);

    if (!scale.is_ready()) {
      Serial.println("✗ HX711 not found - check wiring!");
      while (1);  // Halt
    }

    Serial.println("✓ HX711 found and ready");
    scale.set_gain(128);

    // Don't tare yet - we want to see raw values
    Serial.println("Place weight on load cell and watch for changes.");
    Serial.println("Readings are raw ADC counts (24-bit signed integer).");
    Serial.println("----------------------------------------");
  }

  void loop() {
    if (scale.is_ready()) {
      long reading = scale.read();  // Raw 24-bit ADC reading

      Serial.print("Raw ADC: ");
      Serial.print(reading);

      // Simple change detection
      static long last_reading = 0;
      if (abs(reading - last_reading) > 5) {
        Serial.print("  <-- CHANGE DETECTED!");
        last_reading = reading;
      }

      Serial.println();
    } else {
      Serial.println("HX711 not ready");
    }

    delay(500);  // Read twice per second
  }