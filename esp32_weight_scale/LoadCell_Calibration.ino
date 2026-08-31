#include "HX711.h"

// HX711 circuit wiring
const int LOADCELL_DOUT_PIN = 13;  // DT pin
const int LOADCELL_SCK_PIN = 27;   // SCK pin

HX711 scale;

// Calibration variables
long zero_offset = 0;      // Will be set by taring
float calibration_factor = 1.0;  // Will be computed from known weight

void setup() {
  Serial.begin(115200);

  // Wait for serial monitor
  unsigned long startTime = millis();
  while (!Serial && (millis() - startTime < 3000)) {
    // Wait up to 3 seconds
  }

  Serial.println("\n=== LOAD CELL CALIBRATION TOOL ===");
  Serial.println("Commands:");
  Serial.println("  'z' - Tare (set zero offset) - ensure no weight on scale");
  Serial.println("  'c' - Calibrate - put known weight on scale, then enter weight in grams");
  Serial.println("  'w' - Show weight in grams (using current calibration)");
  Serial.println("  'r' - Show raw ADC reading");
  Serial.println("  't' - Tare and show raw offset");
  Serial.println();

  // Initialize the scale
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);

  if (!scale.is_ready()) {
    Serial.println("✗ HX711 not found - check wiring!");
    while (1);  // Halt
  }

  Serial.println("✓ HX711 found and ready");
  scale.set_gain(128);

  // Initial tare (optional - user can do it)
  // scale.tare();
  // zero_offset = scale.get_offset();
  // Serial.println("✓ Initial tare completed");
}

void loop() {
  if (Serial.available()) {
    char command = Serial.read();

    switch (command) {
      case 'z':  // Tare
        Serial.println("\n>>> Taring... Ensure NO weight on the scale <<<");
        scale.tare();
        zero_offset = scale.get_offset();
        Serial.printf("✓ Tare complete. Zero offset: %ld\n", zero_offset);
        break;

      case 'c':  // Calibrate with known weight
        Serial.println("\n>>> CALIBRATION MODE <<<");
        Serial.println("Put a KNOWN weight on the scale.");
        Serial.println("Enter the weight in grams (e.g., 150.0) and press Enter:");

        // Wait for user input
        while (!Serial.available()) {
          // Wait for input
        }
        float known_weight = Serial.parseFloat();  // Read the number

        // Clear any remaining input
        while (Serial.available()) Serial.read();

        if (known_weight <= 0) {
          Serial.println("✗ Invalid weight. Must be positive.");
          break;
        }

        // Take multiple readings and average
        Serial.println("Taking readings...");
        long sum = 0;
        int readings = 10;
        for (int i = 0; i < readings; i++) {
          if (scale.is_ready()) {
            sum += scale.read();
            delay(100);
          }
        }
        long average_raw = sum / readings;

        // Calculate calibration factor: grams per raw count
        // Assuming linear: weight = (raw - zero_offset) * calibration_factor
        // So calibration_factor = weight / (raw - zero_offset)
        long raw_offset = average_raw - zero_offset;
        if (raw_offset != 0) {
          calibration_factor = known_weight / (float)raw_offset;
          Serial.printf("✓ Calibration complete!\n");
          Serial.printf("  Known weight: %.1f g\n", known_weight);
          Serial.printf("  Raw offset: %ld\n", raw_offset);
          Serial.printf("  Calibration factor: %.6f g/raw count\n", calibration_factor);
          Serial.printf("  (Use this factor in your final code)\n");
        } else {
          Serial.println("✗ Raw offset is zero - check weight placement");
        }
        break;

      case 'w':  // Show weight in grams
        if (scale.is_ready()) {
          long raw = scale.read();
          float weight = (raw - zero_offset) * calibration_factor;
          Serial.printf("Raw: %ld | Zero: %ld | Weight: %.2f g\n",
                       raw, zero_offset, weight);
        } else {
          Serial.println("HX711 not ready");
        }
        break;

      case 'r':  // Show raw ADC
        if (scale.is_ready()) {
          long raw = scale.read();
          Serial.printf("Raw ADC: %ld\n", raw);
        } else {
          Serial.println("HX711 not ready");
        }
        break;

      case 't':  // Tare and show offset
        Serial.println("\n>>> Taring... Ensure NO weight on the scale <<<");
        scale.tare();
        zero_offset = scale.get_offset();
        Serial.printf("✓ Tare complete. Zero offset: %ld\n", zero_offset);
        Serial.printf("  Raw reading after tare: %ld\n", scale.read());
        break;

      default:
        Serial.println("Unknown command. Try: z, c, w, r, t");
    }
  }

  // Optional: periodic output of raw reading
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 1000) {  // Print every second
    lastPrint = millis();
    if (scale.is_ready()) {
      long raw = scale.read();
      Serial.printf("Raw: %ld | Zero: %ld | Delta: %ld\n",
                   raw, zero_offset, (raw - zero_offset));
    }
  }

  delay(10);  // Small delay to prevent hogging CPU
}