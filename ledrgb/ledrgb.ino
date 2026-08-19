#include <Arduino.h>
#include "esp_chip_info.h"
#include "esp_system.h"
#include "esp_flash.h"

void setup() {
  Serial.begin(115200);
  delay(2000);

  esp_chip_info_t chip_info;
  esp_chip_info(&chip_info);

  Serial.println();
  Serial.println("========================================");
  Serial.println("       ESP32 CHIP INFORMATION");
  Serial.println("========================================");

  // CHIP
  Serial.println();
  Serial.println("[ CHIP ]");

  Serial.print("Model: ");

  switch (chip_info.model) {
    case CHIP_ESP32:
      Serial.println("ESP32");
      break;

    case CHIP_ESP32S2:
      Serial.println("ESP32-S2");
      break;

    case CHIP_ESP32S3:
      Serial.println("ESP32-S3");
      break;

    case CHIP_ESP32C3:
      Serial.println("ESP32-C3");
      break;

    case CHIP_ESP32C2:
      Serial.println("ESP32-C2");
      break;

    case CHIP_ESP32C6:
      Serial.println("ESP32-C6");
      break;

    case CHIP_ESP32H2:
      Serial.println("ESP32-H2");
      break;

    default:
      Serial.println("UNKNOWN");
      break;
  }

  Serial.print("Revision: ");
  Serial.println(chip_info.revision);

  Serial.print("CPU cores: ");
  Serial.println(chip_info.cores);

  Serial.print("CPU frequency: ");
  Serial.print(getCpuFrequencyMhz());
  Serial.println(" MHz");


  // FEATURES
  Serial.println();
  Serial.println("[ FEATURES ]");

  Serial.print("WiFi: ");
  Serial.println(
    (chip_info.features & CHIP_FEATURE_WIFI_BGN) ? "YES" : "NO"
  );

  Serial.print("Bluetooth: ");
  Serial.println(
    (chip_info.features & CHIP_FEATURE_BT) ? "YES" : "NO"
  );

  Serial.print("BLE: ");
  Serial.println(
    (chip_info.features & CHIP_FEATURE_BLE) ? "YES" : "NO"
  );

  Serial.print("Embedded Flash: ");
  Serial.println(
    (chip_info.features & CHIP_FEATURE_EMB_FLASH) ? "YES" : "NO"
  );

  Serial.print("Embedded PSRAM: ");
  Serial.println(
    (chip_info.features & CHIP_FEATURE_EMB_PSRAM) ? "YES" : "NO"
  );


  // FLASH
  uint32_t flash_size = 0;

  Serial.println();
  Serial.println("[ FLASH ]");

  if (esp_flash_get_size(NULL, &flash_size) == ESP_OK) {
    Serial.print("Flash size: ");
    Serial.print(flash_size / (1024 * 1024));
    Serial.println(" MB");
  } else {
    Serial.println("Flash size: UNKNOWN");
  }


  // RAM
  Serial.println();
  Serial.println("[ RAM ]");

  Serial.print("Free heap: ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");

  Serial.print("Heap size: ");
  Serial.print(ESP.getHeapSize());
  Serial.println(" bytes");

  Serial.print("PSRAM size: ");
  Serial.print(ESP.getPsramSize());
  Serial.println(" bytes");

  Serial.print("Free PSRAM: ");
  Serial.print(ESP.getFreePsram());
  Serial.println(" bytes");


  // RESET
  Serial.println();
  Serial.println("[ RESET ]");

  Serial.print("Reset reason: ");

  switch (esp_reset_reason()) {

    case ESP_RST_POWERON:
      Serial.println("POWER ON");
      break;

    case ESP_RST_EXT:
      Serial.println("EXTERNAL RESET");
      break;

    case ESP_RST_SW:
      Serial.println("SOFTWARE RESET");
      break;

    case ESP_RST_PANIC:
      Serial.println("PANIC");
      break;

    case ESP_RST_INT_WDT:
      Serial.println("INTERRUPT WATCHDOG");
      break;

    case ESP_RST_TASK_WDT:
      Serial.println("TASK WATCHDOG");
      break;

    case ESP_RST_WDT:
      Serial.println("WATCHDOG");
      break;

    case ESP_RST_BROWNOUT:
      Serial.println("BROWNOUT");
      break;

    case ESP_RST_DEEPSLEEP:
      Serial.println("DEEP SLEEP");
      break;

    default:
      Serial.println("UNKNOWN");
      break;
  }


  // ESP / IDF
  Serial.println();
  Serial.println("[ SOFTWARE ]");

  Serial.print("ESP-IDF version: ");
  Serial.println(ESP.getSdkVersion());

  Serial.print("Arduino ESP32 Core: ");
  Serial.println(ESP_ARDUINO_VERSION_STR);

  Serial.print("Chip revision: ");
  Serial.println(chip_info.revision);


  // SKETCH
  Serial.println();
  Serial.println("[ FLASH / SKETCH ]");

  Serial.print("Sketch size: ");
  Serial.print(ESP.getSketchSize());
  Serial.println(" bytes");

  Serial.print("Free sketch space: ");
  Serial.print(ESP.getFreeSketchSpace());
  Serial.println(" bytes");


  Serial.println();
  Serial.println("========================================");
  Serial.println("             TEST COMPLETE");
  Serial.println("========================================");
}

void loop() {
  Serial.println("ALIVE");
  delay(2000);
}