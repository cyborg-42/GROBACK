/**
 * WeightScale_4Quad.ino
 * GroBack AI-IoT Smart Shelf — 4-Quadrant Load Cell Firmware
 * ===========================================================
 *
 * Hardware wiring (38-pin ESP32):
 *
 *   All 4 HX711 boards share one Clock line to save GPIO pins.
 *   Each HX711 gets its own unique Data pin.
 *
 *   ┌──────────┬──────────────┬────────────────┬───────────────┐
 *   │ Quadrant │ Zone         │ Clock (shared) │ Data (unique) │
 *   ├──────────┼──────────────┼────────────────┼───────────────┤
 *   │    1     │ Top-Left     │   GPIO 18      │   GPIO 19     │
 *   │    2     │ Top-Right    │   GPIO 18      │   GPIO 21     │
 *   │    3     │ Bottom-Left  │   GPIO 18      │   GPIO 22     │
 *   │    4     │ Bottom-Right │   GPIO 18      │   GPIO 23     │
 *   └──────────┴──────────────┴────────────────┴───────────────┘
 *
 * Physical separation:
 *   Leave a 2 mm air gap between the 4 tray plates so they never
 *   touch each other — each tray sits strictly on its own load cell.
 *
 * Delta-reporting strategy:
 *   The firmware only POSTs to the backend when a quadrant's weight
 *   changes by more than DELTA_THRESHOLD grams since the last report.
 *   This prevents the server from being flooded with identical readings
 *   and ensures the delta-binding algorithm on the backend only fires
 *   on genuine placement / removal events.
 *
 * Dependencies (Arduino Library Manager):
 *   - HX711 by Bogdan Necula  (install: HX711)
 *   - WiFi        (built-in ESP32)
 *   - HTTPClient  (built-in ESP32)
 *
 * Setup:
 *   1. Change WIFI_SSID, WIFI_PASSWORD, SERVER_IP below.
 *   2. Flash. Open Serial Monitor at 115200 baud.
 *   3. When prompted, ensure all trays are EMPTY, then send any char
 *      to tare (zero) all four scales.
 *   4. Calibrate each quadrant using known weights and adjust
 *      CALIBRATION_FACTORS below.
 */

#include "HX711.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>   // optional — for cleaner JSON; remove if not installed

// ─── User configuration — CHANGE THESE ───────────────────────────────────────

const char* WIFI_SSID     = "YOUR_WIFI_SSID";       // <-- your Wi-Fi name
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";   // <-- your Wi-Fi password
const char* SERVER_IP     = "10.65.157.91";          // <-- your PC's LAN IP
const int   SERVER_PORT   = 8000;

// ─── GPIO pin mapping ─────────────────────────────────────────────────────────

const int CLK_PIN = 18;                      // Shared clock for all 4 HX711s
const int DT_PINS[4] = {19, 21, 22, 23};    // Data pins: Q1, Q2, Q3, Q4

// ─── Calibration ──────────────────────────────────────────────────────────────
//
// To calibrate:
//   1. Tare (zero) with empty tray.
//   2. Place a known weight (e.g. 500g) on each quadrant.
//   3. Read the raw value printed on Serial.
//   4. Set factor = known_weight_g / raw_value.
//
// These are placeholder values — replace after calibration.

float CALIBRATION_FACTORS[4] = {
  0.000418,   // Quadrant 1 — replace after calibration
  0.000418,   // Quadrant 2
  0.000418,   // Quadrant 3
  0.000418,   // Quadrant 4
};

// ─── Tuning parameters ────────────────────────────────────────────────────────

// Number of HX711 readings averaged per measurement cycle (reduces noise)
const int   AVERAGES         = 5;

// Only POST to backend if weight changed by more than this many grams.
// Keeps the server quiet during stable readings and ensures the
// delta-binding algorithm sees clean ΔW events.
const float DELTA_THRESHOLD  = 5.0;   // grams

// How often to read all sensors (milliseconds)
const int   READ_INTERVAL_MS = 500;

// How often to force-send even if no delta (keeps server alive)
const int   HEARTBEAT_EVERY  = 20;    // every N cycles (~10 s at 500ms)

// ─── State ────────────────────────────────────────────────────────────────────

HX711 scales[4];
float lastSentWeights[4] = {0, 0, 0, 0};
int   cycleCount         = 0;
bool  allScalesReady     = false;

// ─── Helper: compute endpoint URL ─────────────────────────────────────────────

String weightUrl() {
  return String("http://") + SERVER_IP + ":" + SERVER_PORT + "/api/v1/update-weight";
}

// ─── Setup ────────────────────────────────────────────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("╔═══════════════════════════════════════════╗");
  Serial.println("║   GroBack 4-Quadrant Weight Scale v2.0   ║");
  Serial.println("╚═══════════════════════════════════════════╝");

  // ── Initialise all 4 HX711s ──────────────────────────────────────────────
  Serial.println("\n[INIT] Initialising HX711 sensors...");
  int readyCount = 0;
  for (int i = 0; i < 4; i++) {
    scales[i].begin(DT_PINS[i], CLK_PIN);
    delay(100);
    if (scales[i].is_ready()) {
      scales[i].set_gain(128);
      // Apply calibration factor — get_units() will return grams directly
      scales[i].set_scale(CALIBRATION_FACTORS[i]);
      Serial.printf("  [OK] Q%d — DT=GPIO%d, CLK=GPIO%d, cal=%.6f\n",
                    i+1, DT_PINS[i], CLK_PIN, CALIBRATION_FACTORS[i]);
      readyCount++;
    } else {
      Serial.printf("  [!!] Q%d — NOT DETECTED (DT=GPIO%d) — check wiring\n",
                    i+1, DT_PINS[i]);
    }
  }
  allScalesReady = (readyCount == 4);
  Serial.printf("\n  %d/4 scales detected.\n", readyCount);

  // ── Tare ─────────────────────────────────────────────────────────────────
  Serial.println("\n[TARE] Remove ALL items from ALL trays.");
  Serial.println("       Send any character in Serial Monitor when ready...");
  while (!Serial.available()) delay(100);
  Serial.read();

  Serial.println("[TARE] Zeroing scales...");
  for (int i = 0; i < 4; i++) {
    if (scales[i].is_ready()) {
      scales[i].tare(10);    // average 10 readings for tare accuracy
      Serial.printf("  [OK] Q%d tared (offset=%ld)\n", i+1, scales[i].get_offset());
    }
  }
  Serial.println("[TARE] Done.\n");

  // ── Connect Wi-Fi ─────────────────────────────────────────────────────────
  Serial.printf("[WIFI] Connecting to '%s'", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" CONNECTED");
    Serial.printf("[WIFI] IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println(" FAILED — will retry in loop");
  }

  Serial.println("\n[RUN] Starting monitoring loop...");
  Serial.println("      Q1(g)  | Q2(g)  | Q3(g)  | Q4(g)  | Sent");
  Serial.println("      -------|--------|--------|--------|------");
}

// ─── Loop ─────────────────────────────────────────────────────────────────────

void loop() {
  cycleCount++;
  float weights[4] = {0, 0, 0, 0};
  bool  sent[4]    = {false, false, false, false};

  // ── Read all 4 quadrants ────────────────────────────────────────────────
  for (int i = 0; i < 4; i++) {
    if (!scales[i].is_ready()) {
      weights[i] = lastSentWeights[i];   // hold last good value on sensor error
      continue;
    }

    // Average AVERAGES readings — get_units() applies set_scale() internally
    // returning grams directly. Clamp negatives to 0 (tare drift).
    float raw = scales[i].get_units(AVERAGES);
    weights[i] = max(0.0f, raw);
  }

  // ── Determine which quadrants need a POST ───────────────────────────────
  bool heartbeat = (cycleCount % HEARTBEAT_EVERY == 0);

  for (int i = 0; i < 4; i++) {
    float delta = abs(weights[i] - lastSentWeights[i]);
    if (delta >= DELTA_THRESHOLD || heartbeat) {
      if (WiFi.status() == WL_CONNECTED) {
        bool ok = postWeight(i + 1, weights[i]);
        if (ok) {
          lastSentWeights[i] = weights[i];
          sent[i] = true;
        }
      }
    }
  }

  // ── Serial readout ──────────────────────────────────────────────────────
  Serial.printf("      %6.1f | %6.1f | %6.1f | %6.1f |",
                weights[0], weights[1], weights[2], weights[3]);
  for (int i = 0; i < 4; i++) Serial.print(sent[i] ? " Q" + String(i+1) : "   ");
  Serial.println();

  // ── Reconnect Wi-Fi if lost ─────────────────────────────────────────────
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Reconnecting...");
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  }

  delay(READ_INTERVAL_MS);
}

// ─── POST weight to backend ───────────────────────────────────────────────────

bool postWeight(int quadrant, float weight_grams) {
  HTTPClient http;
  String url = weightUrl();

  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(3000);   // 3 s timeout — don't block the loop for too long

  // Build JSON: {"quadrant": 1, "weight_grams": 450.0}
  String body = "{\"quadrant\":";
  body += quadrant;
  body += ",\"weight_grams\":";
  body += String(weight_grams, 1);
  body += "}";

  int code = http.POST(body);
  bool success = (code == 200);

  if (success) {
    // Parse binding response to surface auto-bind events on Serial
    String resp = http.getString();
    if (resp.indexOf("\"binding\":\"auto\"") >= 0 ||
        resp.indexOf("bound_item") >= 0) {
      Serial.printf("  [BIND] Q%d auto-bound! Response: %s\n", quadrant, resp.c_str());
    }
  } else {
    Serial.printf("  [ERR] Q%d HTTP %d\n", quadrant, code);
  }

  http.end();
  return success;
}
