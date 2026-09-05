#include "HX711.h"

#define LOADCELL_DOUT_PIN 13
#define LOADCELL_SCK_PIN  27

HX711 scale;

void setup() {
  Serial.begin(115200);
  Serial.println("HX711 Simple Test");
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  if (scale.is_ready()) {
    Serial.println("HX711 ready");
  } else {
    Serial.println("HX711 not found");
    while(1);
  }
  scale.set_gain(128);
}

void loop() {
  if (scale.is_ready()) {
    long val = scale.read();
    Serial.print("Raw: ");
    Serial.println(val);
  }
  delay(500);
}