#include "HX711.h"
#include <WiFi.h>
#include <HTTPClient.h>

// WiFi settings
const char* ssid = "YOUR_WIFI_SSID";     // CHANGE THIS
const char* password = "YOUR_WIFI_PASSWORD"; // CHANGE THIS

// Backend settings
const char* backendUrl = "http://YOUR_PC_IP:8000/api/v1/update-weight"; // CHANGE THIS

// HX711 circuit wiring - 4 load cells
const int SCK_PIN = 27;  // Shared clock pin
const int DT_PINS[4] = {13, 14, 25, 26};  // Data pins for quadrants 1-4

// Calibration factors - TO BE DETERMINED PER LOAD CELL
// These are example values - replace with your own calibration factors
// Format: grams per raw ADC count (after taring)
float calibration_factors[4] = {
  0.1,  // Quadrant 1 - placeholder
  0.1,  // Quadrant 2 - placeholder
  0.1,  // Quadrant 3 - placeholder
  0.1   // Quadrant 4 - placeholder
};

// Zero offsets - will be set during tare in setup
long zero_offsets[4] = {0, 0, 0, 0};

// HX711 instances
HX711 scales[4];

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== GroBack 4-Quadrant Weight Scale ===");

  // Initialize each scale
  for (int i = 0; i < 4; i++) {
    scales[i].begin(DT_PINS[i], SCK_PIN);
    if (scales[i].is_ready()) {
      Serial.printf("✓ Quadrant %d: DT=%d, SCK=%d - READY\n", i+1, DT_PINS[i], SCK_PIN);
      scales[i].set_gain(128);
    } else {
      Serial.printf("✗ Quadrant %d: DT=%d, SCK=%d - NOT FOUND\n", i+1, DT_PINS[i], SCK_PIN);
    }
  }

  // Tare all scales (reset zero offset)
  Serial.println("\nTaring all scales... Ensure NO weight on any quadrant.");
  for (int i = 0; i < 4; i++) {
    if (scales[i].is_ready()) {
      scales[i].tare();
      zero_offsets[i] = scales[i].get_offset();
      Serial.printf("  Quadrant %d zero offset: %ld\n", i+1, zero_offsets[i]);
    }
  }
  Serial.println("Tare complete.");

  // Connect to WiFi
  Serial.printf("\nConnecting to %s ", ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" CONNECTED");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  Serial.println("\nStarting weight monitoring...");
  Serial.println("Format: Q1(g) | Q2(g) | Q3(g) | Q4(g)");
  Serial.println("----------------------------------------");
}

void loop() {
  // Read all quadrants
  int readyCount = 0;
  float weights[4] = {0, 0, 0, 0};

  for (int i = 0; i < 4; i++) {
    if (scales[i].is_ready()) {
      long raw = scales[i].read();  // Raw ADC reading
      // Apply tare and calibration: weight = (raw - zero_offset) * factor
      weights[i] = (raw - zero_offsets[i]) * calibration_factors[i];
      readyCount++;
    } else {
      weights[i] = -9999;  // Indicate error
    }
  }

  // Print to serial for monitoring
  if (readyCount > 0) {
    Serial.printf("Q1: %6.1f | Q2: %6.1f | Q3: %6.1f | Q4: %6.1f | Ready: %d/4\n",
                 weights[0], weights[1], weights[2], weights[3], readyCount);
  }

  // Send to backend if all scales ready
  if (readyCount == 4 && WiFi.status() == WL_CONNECTED) {
    // We'll send each quadrant individually as per backend endpoint expects
    // Alternatively, we could send all at once but backend expects per quadrant
    for (int i = 0; i < 4; i++) {
      if (scales[i].is_ready()) {
        sendWeightToBackend(i+1, weights[i]);  // quadrant number 1-4
      }
    }
  }

  delay(1000);  // Update once per second
}

void sendWeightToBackend(int quadrant, float weight_grams) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected");
    return;
  }

  HTTPClient http;
  http.begin(backendUrl);
  http.addHeader("Content-Type", "application/json");

  // Create JSON payload: {"quadrant": 1, "weight_grams": 450.0}
  String payload = "{\"quadrant\":";
  payload += quadrant;
  payload += ",\"weight_grams\":";
  payload += String(weight_grams, 1);  // 1 decimal place
  payload += "}";

  int httpResponseCode = http.POST(payload);

  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("✓ Sent Q%d: %.1fg - HTTP %d: %s\n", quadrant, weight_grams, httpResponseCode, response.c_str());
  } else {
    Serial.printf("✗ HTTP Error sending Q%d: %.1fg - Code: %d\n", quadrant, weight_grams, httpResponseCode);
  }

  http.end();  // Free resources
}