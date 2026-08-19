# IoT Projects Technical Audit

Date: 2026-08-19

This document is a source-level technical audit of the IoT projects in this repository. It records findings only; it does not change runtime behavior.

## Scope

The repository contains Arduino, CircuitPython, ESP32-S3, TFT/OLED-style display, LED/RGB LED, Wi-Fi web server, BLE, and USB HID security-lab projects.

Important constraints followed during the audit:

- No GitHub repositories were created.
- No files or projects were deleted.
- No runtime code behavior was changed.
- Existing hardware functionality was preserved.

## Project Inventory

### ESP32-S3TFTSPIWebServerLED

- **Purpose:** Arduino ESP32-S3 web server that controls an RGB LED and writes user-provided text to an ILI9488 TFT display.
- **Board:** ESP32-S3, likely DevKit-style board.
- **Language:** C++ / Arduino.
- **Framework:** Arduino ESP32 core.
- **Hardware:** ESP32-S3, ILI9488 320x480 TFT, XPT2046 touch controller, RGB LED.
- **Pins:**
  - RGB LED: R=GPIO4, G=GPIO5, B=GPIO6.
  - TFT SPI: SCLK=GPIO12, MOSI=GPIO11, MISO=GPIO13, DC=GPIO9, CS=GPIO10, RST=GPIO14.
  - Touch: CS=GPIO21, shared SPI on GPIO12/GPIO11/GPIO13.
- **Dependencies:** `WiFi.h`, `WebServer.h`, `LovyanGFX.hpp`.
- **Current status:** Prototype / strong portfolio candidate.
- **Problems:** Blocking Wi-Fi connection loop; no authentication; possible Arduino ESP32 Core 2.x vs 3.x LEDC compatibility issue; possible RGB common-anode/common-cathode mismatch.
- **Security issues:** Hardcoded SSID/password; unauthenticated web endpoints.
- **Documentation quality:** Inline comments exist, but no project README.
- **Portfolio value:** High.
- **Recommended improvements:** Move secrets to local config, add README/wiring diagram, add Wi-Fi timeout/fallback AP, document Arduino core version, confirm RGB LED type.

### ledrgb

- **Purpose:** ESP32 diagnostics sketch that prints chip model, features, flash/RAM info, reset reason, ESP-IDF version, Arduino core version, sketch size, and an `ALIVE` heartbeat.
- **Board:** ESP32 family.
- **Language:** C++ / Arduino.
- **Framework:** Arduino ESP32 core.
- **Hardware:** No external hardware required.
- **Pins:** None.
- **Dependencies:** `Arduino.h`, `esp_chip_info.h`, `esp_system.h`, `esp_flash.h`.
- **Current status:** Utility/demo sketch.
- **Problems:** Folder name is misleading because it is not an RGB LED project.
- **Security issues:** None found.
- **Documentation quality:** Serial output is descriptive; no README.
- **Portfolio value:** Low as a standalone project, useful as a utility.
- **Recommended improvements:** Rename later with approval to `esp32-chip-info` or `esp32-diagnostics`; add README with board setup and sample output.

### led-web-ui-pwm-esp32s3

- **Purpose:** CircuitPython ESP32-S3 web server that controls one LED through HTTP endpoints and a mobile-friendly dashboard.
- **Board:** ESP32-S3.
- **Language:** CircuitPython.
- **Framework:** CircuitPython.
- **Hardware:** ESP32-S3 and one LED or LED module.
- **Pins:** LED=GPIO4.
- **Dependencies:** `sys`, `time`, `board`, `digitalio`, `wifi`, `socketpool`, `ipaddress`.
- **Current status:** Working prototype / demo.
- **Problems:** Folder says PWM but code uses digital on/off control; static IP is hardcoded; Wi-Fi failure blocks forever; no README.
- **Security issues:** Hardcoded Wi-Fi credentials; unauthenticated HTTP endpoints.
- **Documentation quality:** Good inline comments, no external documentation.
- **Portfolio value:** Medium.
- **Recommended improvements:** Rename or implement PWM, move secrets to `settings.toml`, document wiring and current-limiting resistor, add DHCP or configurable IP support.

### code_lcd_web.py

- **Purpose:** CircuitPython ESP32-S3 web server that controls a digital LED and an ILI9488 TFT display.
- **Board:** ESP32-S3 DevKitC-1 according to inline comments.
- **Language:** CircuitPython.
- **Framework:** CircuitPython.
- **Hardware:** ESP32-S3, ILI9488 SPI TFT, one LED module.
- **Pins:** LED=GPIO4; TFT SCK=GPIO12, MOSI=GPIO11, MISO=GPIO13, CS=GPIO10, DC=GPIO9, RST=GPIO14.
- **Dependencies:** `sys`, `time`, `board`, `digitalio`, `wifi`, `socketpool`, `ipaddress`, `busio`, `displayio`, `terminalio`, `bagaloozy_ili9488`, `adafruit_display_text`.
- **Current status:** Prototype; likely related to or superseded by the Arduino TFT web server project.
- **Problems:** Root-level standalone file lacks a project folder; hardcoded network config; external display driver not documented; no README.
- **Security issues:** Hardcoded Wi-Fi credentials; unauthenticated HTTP APIs.
- **Documentation quality:** Good inline comments, poor reproducibility.
- **Portfolio value:** High if cleaned up.
- **Recommended improvements:** Move into its own folder, document dependencies and display driver, move secrets to `settings.toml`, add photos and wiring diagram.

### ble-ledrgb-circuitpython

- **Purpose:** CircuitPython BLE UART RGB LED controller for ESP32-S3.
- **Board:** ESP32-S3.
- **Language:** CircuitPython.
- **Framework:** CircuitPython.
- **Hardware:** ESP32-S3 and external common-anode RGB LED.
- **Pins:** Common anode to 3.3V; R=GPIO4, G=GPIO5, B=GPIO6.
- **Dependencies:** `time`, `board`, `pwmio`, `microcontroller`, `adafruit_ble`, `ProvideServicesAdvertisement`, `UARTService`.
- **Current status:** Working prototype / demo.
- **Problems:** Direct use of `microcontroller.pin.GPIOx` can be less portable than board aliases; missing BLE app instructions; no resistor guidance.
- **Security issues:** BLE UART has no documented pairing/authorization boundary.
- **Documentation quality:** Good inline wiring comments, no README.
- **Portfolio value:** Medium-high.
- **Recommended improvements:** Add README with wiring, resistor values, BLE app workflow, commands, and security limitation notes.

### esp32-fullbadusb

- **Purpose:** CircuitPython ESP32-S3 USB HID DuckyScript interpreter that runs commands from `payload.txt`.
- **Board:** ESP32-S3 DevKit-style board with USB HID support.
- **Language:** CircuitPython plus DuckyScript-style payloads.
- **Framework:** CircuitPython.
- **Hardware:** ESP32-S3 USB HID, optional BOOT button, optional onboard LED.
- **Pins:** Button candidates include `IO0`, `BUTTON`, `BOOT0`, `GP0`; LED candidates include `LED`, `IO38`, `IO2`, `IO48`, `IO47`, `NEOPIXEL`.
- **Dependencies:** `usb_hid`, `board`, `digitalio`, `time`, `os`, `sys`, `traceback`, `adafruit_hid`.
- **Current status:** Security lab / offensive HID prototype.
- **Problems:** Auto-executes payload if no button is detected; payload contains destructive and credential-theft behavior; stealth options are present in `boot.py` as comments.
- **Security issues:** Critical. Payload behavior includes firewall changes, hidden admin user creation, RDP enabling, persistence, Wi-Fi credential export, and other invasive actions.
- **Documentation quality:** PDFs exist, but no plain-text `README.md` suitable for source review.
- **Portfolio value:** Sensitive; not suitable for public portfolio as-is.
- **Recommended improvements:** Replace harmful payloads with benign demos, disable auto-fire, add safety/legal warnings, quarantine under a `security-lab` folder.

### esp32-fullbadusb/webserver

- **Purpose:** CircuitPython ESP32-S3 BadUSB variant with Wi-Fi AP and web UI for payload/prank triggering.
- **Board:** ESP32-S3.
- **Language:** CircuitPython.
- **Framework:** CircuitPython.
- **Hardware:** ESP32-S3 USB HID, Wi-Fi AP, optional LED.
- **Pins:** LED candidates include `LED`, `IO38`, `IO2`, `IO48`, `IO47`.
- **Dependencies:** `usb_hid`, `board`, `digitalio`, `time`, `os`, `sys`, `wifi`, `socketpool`, `adafruit_hid`.
- **Current status:** Broken / incomplete.
- **Problems:** Python syntax error due to unescaped quotes in HTML string concatenation; weak AP password; auto-executes payload; unauthenticated Wi-Fi trigger surface.
- **Security issues:** Critical. Combines USB HID payload execution with wireless triggering and weak AP credentials.
- **Documentation quality:** PDF exists, no source-level README.
- **Portfolio value:** Low as-is.
- **Recommended improvements:** Fix syntax only after approval, remove harmful payloads, disable auto-execute, require physical confirmation, add warnings.

### esp32-fullbadusb/advancedwithpowershell

- **Purpose:** DuckyScript interpreter copy paired with an aggressive PowerShell-based payload.
- **Board:** ESP32-S3.
- **Language:** CircuitPython plus DuckyScript/PowerShell.
- **Framework:** CircuitPython.
- **Hardware:** ESP32-S3 USB HID.
- **Pins:** Same button/LED candidate approach as parent BadUSB project.
- **Dependencies:** Same as parent BadUSB project.
- **Current status:** Dangerous offensive prototype.
- **Problems:** Payload includes credential harvesting, browser database copying, cookies, persistence, WMI persistence, reverse shell behavior, LSASS dumping, and event log clearing.
- **Security issues:** Critical; highest-risk project in the repository.
- **Documentation quality:** PDF exists, no plain-text safety documentation.
- **Portfolio value:** Only suitable as private, controlled cybersecurity-lab material after major safety changes.
- **Recommended improvements:** Do not publish as-is; replace with benign payloads; move under `security-lab`; disable auto-execution; add strong warnings.

## Critical Problems

1. Hardcoded Wi-Fi credentials are present in multiple projects.
2. BadUSB payloads contain destructive, credential-theft, persistence, reverse-shell, and log-clearing behavior.
3. BadUSB auto-fire behavior is unsafe.
4. The BadUSB webserver variant has a Python syntax error.
5. Multiple web/BLE projects expose unauthenticated local control surfaces.

## Bugs

1. `esp32-fullbadusb/webserver/code.py` does not parse because of unescaped quotes in generated HTML.
2. `led-web-ui-pwm-esp32s3` claims PWM but uses digital output only.
3. `ledrgb` is misnamed because it is a chip diagnostics sketch, not an RGB project.
4. Arduino LEDC API usage may depend on Arduino ESP32 Core 3.x.
5. Several Wi-Fi projects block indefinitely when connection fails.

## Security Issues

1. Hardcoded Wi-Fi credentials.
2. Weak AP password in the BadUSB webserver variant.
3. No authentication on HTTP control endpoints.
4. BLE UART security limitations are undocumented.
5. BadUSB payloads include high-risk offensive behavior and should not be published or run casually.

## Hardware and Wiring Issues

1. RGB common-anode/common-cathode mismatch risk between projects.
2. Missing resistor/current-limit documentation for LEDs.
3. TFT voltage and logic-level assumptions are not documented.
4. GPIO availability is board-dependent and should be documented per board.
5. Shared SPI bus wiring for TFT and touch should be documented clearly.

## Documentation Problems

1. Most projects lack `README.md`.
2. Existing PDFs are less reviewable than Markdown documentation.
3. Dependency versions are not pinned.
4. Board package / CircuitPython versions are not documented.
5. Wiring diagrams are missing.
6. No reproducibility checklist exists.
7. Security-lab projects need prominent legal and safety warnings.

## Projects Worth Keeping

- `ESP32-S3TFTSPIWebServerLED`
- `code_lcd_web.py`
- `ble-ledrgb-circuitpython`
- `led-web-ui-pwm-esp32s3`
- `ledrgb` as a utility
- `esp32-fullbadusb` only as a private, clearly marked security-lab project

## Projects Worth Merging

- Merge concepts from `led-web-ui-pwm-esp32s3` and `code_lcd_web.py`.
- Treat `ESP32-S3TFTSPIWebServerLED` and `code_lcd_web.py` as Arduino and CircuitPython versions of a similar TFT web-control idea.
- Align RGB pin/common-anode documentation across RGB projects.

## Projects Worth Separating

- Separate security-lab projects from normal IoT projects.
- Move root-level `code_lcd_web.py` into its own folder.
- Separate generated test artifacts from source and payloads.

## Portfolio Candidates

Strong candidates:

1. ESP32-S3 TFT + RGB Web Controller.
2. CircuitPython TFT Web Dashboard.
3. BLE RGB Controller.

Support/utility candidates:

1. ESP32 Diagnostics Tool.
2. LED Web Controller after renaming or adding real PWM.

Not recommended public as-is:

1. BadUSB projects.

## Recommended Final Folder Structure

```text
iot/
├── README.md
├── LICENSE
├── arduino/
│   ├── esp32s3-tft-rgb-web-controller/
│   │   ├── ESP32-S3TFTSPIWebServerLED.ino
│   │   ├── LGFX_ILI9488.h
│   │   ├── README.md
│   │   ├── wiring.md
│   │   └── secrets.example.h
│   └── esp32-chip-info/
│       ├── esp32-chip-info.ino
│       └── README.md
├── circuitpython/
│   ├── esp32s3-led-web-controller/
│   │   ├── code.py
│   │   ├── README.md
│   │   └── settings.example.toml
│   ├── esp32s3-tft-led-web-controller/
│   │   ├── code.py
│   │   ├── README.md
│   │   ├── requirements.md
│   │   └── settings.example.toml
│   └── esp32s3-ble-rgb-controller/
│       ├── code.py
│       ├── README.md
│       └── wiring.md
└── security-lab/
    └── esp32s3-hid-duckyscript-lab/
        ├── README.md
        ├── SAFETY.md
        ├── boot.py
        ├── code.py
        ├── payloads/
        │   ├── harmless-demo.txt
        │   └── legacy-dangerous-payloads/
        └── sample-output/
```

## Recommended README Template

```markdown
# Project Name

## Overview
Short description of what the project does.

## Hardware
- Board:
- Display:
- Sensors/modules:
- LEDs:
- Power supply:

## Wiring
| Function | Board Pin | Module Pin | Notes |
|---|---:|---|---|

## Software
- Language:
- Framework:
- Board package / CircuitPython version:
- Libraries:

## Configuration
Explain Wi-Fi/settings/secrets without committing real credentials.

## Installation
Step-by-step setup.

## Usage
How to run, access web UI/BLE/serial output.

## API / Commands
HTTP endpoints, BLE commands, serial commands, etc.

## Safety Notes
Voltage, current, GPIO warnings.

## Troubleshooting
Common failures and fixes.

## Photos / Screenshots
Optional but recommended for portfolio.
```

For BadUSB/security-lab projects, also add:

```markdown
## Legal and Ethical Use
This project is for authorized lab systems only.

## Safe Demo Payloads Only
Default payload must be harmless.

## Explicit Trigger Required
No auto-fire by default.

## What Not To Do
Do not run against third-party systems.
Do not collect credentials.
Do not create persistence.
Do not disable security controls.
```

## Recommended Cleanup Plan

### Phase 1: Safety and Secrets

1. Remove real Wi-Fi credentials from source and replace with examples.
2. Add `.gitignore` entries for local secrets files.
3. Disable BadUSB auto-fire.
4. Replace harmful payloads with harmless demos if approved.

### Phase 2: Documentation

1. Add root inventory README.
2. Add per-project READMEs.
3. Add wiring tables and dependency lists.
4. Add project status labels: demo, prototype, finished, security-lab only.

### Phase 3: Structure

1. Move `code_lcd_web.py` into a project folder.
2. Rename misleading folders.
3. Separate Arduino, CircuitPython, and security-lab projects.

### Phase 4: Code Quality

1. Fix the BadUSB webserver syntax error if keeping that project.
2. Add Wi-Fi connection timeouts.
3. Add optional fallback AP mode.
4. Make pin assignments configurable.
5. Document Arduino Core 2.x vs 3.x compatibility.
