#include <WiFi.h>
#include <WebServer.h>
#include "LGFX_ILI9488.h"   // همان فایل خودت با 40MHz و تاچ فعال

LGFX tft;
WebServer server(80);

// ============================================
// WiFi (حالت Station)
// ============================================
const char* ssid     = "Arian";
const char* password = "Amir2003Sh@Q%";

// ============================================
// RGB LED (پایه‌های 4 و 5 و 6)
// ============================================
#define LED_R 4
#define LED_G 5
#define LED_B 6
#define COMMON_ANODE false
#define PWM_FREQ 5000
#define PWM_RESOLUTION 8

int redValue = 0, greenValue = 0, blueValue = 0;
String displayText = "Hello ESP32!";

void setRGB(int r, int g, int b) {
  r = constrain(r, 0, 255);
  g = constrain(g, 0, 255);
  b = constrain(b, 0, 255);
  redValue = r; greenValue = g; blueValue = b;
#if COMMON_ANODE
  r = 255 - r; g = 255 - g; b = 255 - b;
#endif
  ledcWrite(LED_R, r);
  ledcWrite(LED_G, g);
  ledcWrite(LED_B, b);
}

void showText(String text) {
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawString(text, 10, 200);
}

// ============================================
// صفحه وب (همان HTML قبلی)
// ============================================
String makeWebPage() {
  String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ESP32-S3 TFT Control</title>
<style>
body { font-family: Arial; background: #111; color: white; text-align: center; margin: 0; padding: 25px; }
.container { max-width: 500px; margin: auto; }
h1 { margin-bottom: 30px; }
.card { background: #222; padding: 20px; border-radius: 18px; margin-bottom: 20px; }
input[type=text] { width: 90%; padding: 15px; border-radius: 10px; border: none; font-size: 18px; margin-bottom: 15px; box-sizing: border-box; }
button { background: #00aaff; color: white; border: none; padding: 14px 20px; margin: 4px; border-radius: 10px; font-size: 17px; }
input[type=color] { width: 100px; height: 60px; border: none; background: none; }
.slider { width: 90%; }
.value { font-size: 18px; margin: 8px; }
.status { color: #00ff88; }
</style>
</head>
<body>
<div class="container">
<h1>ESP32-S3 TFT Control</h1>
<div class="card">
<h2>Display Text</h2>
<form action="/text">
<input type="text" name="text" placeholder="Write something..." maxlength="60">
<br>
<button type="submit">Show on TFT</button>
</form>
</div>
<div class="card">
<h2>RGB LED</h2>
<input type="color" id="colorPicker" value="#000000" oninput="changeColor(this.value)">
<br><br>
<button onclick="setColor(255,0,0)">RED</button>
<button onclick="setColor(0,255,0)">GREEN</button>
<button onclick="setColor(0,0,255)">BLUE</button>
<br>
<button onclick="setColor(255,255,255)">WHITE</button>
<button onclick="setColor(0,0,0)">OFF</button>
</div>
<div class="card">
<h2>RGB Sliders</h2>
<div class="value">Red: <span id="rv">0</span></div>
<input class="slider" type="range" min="0" max="255" value="0" id="r" oninput="updateRGB()">
<div class="value">Green: <span id="gv">0</span></div>
<input class="slider" type="range" min="0" max="255" value="0" id="g" oninput="updateRGB()">
<div class="value">Blue: <span id="bv">0</span></div>
<input class="slider" type="range" min="0" max="255" value="0" id="b" oninput="updateRGB()">
</div>
<div class="card">
<p class="status">ESP32-S3 ONLINE</p>
<p>TFT: ILI9488 320x480</p>
<p>WiFi: <span id="wifiName">---</span></p>
<p>IP: <span id="ipAddr">---</span></p>
</div>
</div>
<script>
let timer;
function setColor(r, g, b) {
    document.getElementById("r").value = r;
    document.getElementById("g").value = g;
    document.getElementById("b").value = b;
    updateRGB();
}
function updateRGB() {
    let r = document.getElementById("r").value;
    let g = document.getElementById("g").value;
    let b = document.getElementById("b").value;
    document.getElementById("rv").innerText = r;
    document.getElementById("gv").innerText = g;
    document.getElementById("bv").innerText = b;
    clearTimeout(timer);
    timer = setTimeout(function() {
        fetch("/rgb?r=" + r + "&g=" + g + "&b=" + b);
    }, 30);
}
function changeColor(hex) {
    let r = parseInt(hex.substring(1,3), 16);
    let g = parseInt(hex.substring(3,5), 16);
    let b = parseInt(hex.substring(5,7), 16);
    setColor(r, g, b);
}
window.onload = function() {
    document.getElementById("wifiName").innerText = "Arian";
    document.getElementById("ipAddr").innerText = window.location.hostname;
}
</script>
</body>
</html>
)rawliteral";
  return html;
}

// ============================================
// Web Handlers
// ============================================
void handleRoot() {
  server.send(200, "text/html", makeWebPage());
}

void handleText() {
  if (server.hasArg("text")) {
    displayText = server.arg("text");
    Serial.print("Text: "); Serial.println(displayText);
    showText(displayText);
  }
  server.sendHeader("Location", "/");
  server.send(303);
}

void handleRGB() {
  if (server.hasArg("r") && server.hasArg("g") && server.hasArg("b")) {
    int r = server.arg("r").toInt();
    int g = server.arg("g").toInt();
    int b = server.arg("b").toInt();
    setRGB(r, g, b);
    Serial.printf("RGB: %d %d %d\n", r, g, b);
  }
  server.send(200, "text/plain", "OK");
}

// ============================================
// SETUP (ترتیب: TFT → WiFi → وب سرور)
// ============================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("==============================");
  Serial.println("ESP32-S3 TFT + RGB WEB (Station)");
  Serial.println("==============================");

  // ---------- RGB (ابتدا) ----------
  ledcAttach(LED_R, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(LED_G, PWM_FREQ, PWM_RESOLUTION);
  ledcAttach(LED_B, PWM_FREQ, PWM_RESOLUTION);
  setRGB(0, 0, 0);
  Serial.println("RGB initialized.");

  // ---------- TFT (دوم - مثل کد clock) ----------
  Serial.println("Initializing TFT...");
  tft.init();
  tft.setRotation(1);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawString("Connecting WiFi...", 40, 100);
  Serial.println("TFT initialized.");

  delay(100);  // کمی مکث برای تثبیت ولتاژ

  // ---------- WiFi (سوم) ----------
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("WiFi: " + String(ssid), 40, 140);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // نمایش IP روی TFT
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.drawString("WiFi Connected!", 40, 100);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("IP: " + WiFi.localIP().toString(), 40, 140);

  // ---------- وب سرور (چهارم) ----------
  server.on("/", handleRoot);
  server.on("/text", handleText);
  server.on("/rgb", handleRGB);
  server.begin();
  Serial.println("Web server started!");
  Serial.print("Open http://");
  Serial.println(WiFi.localIP());
  Serial.println("==============================");
}

void loop() {
  server.handleClient();
}