# ============================================
# ESP32-S3 IoT Controller - Version 1
# ============================================
# A single-file CircuitPython web server for
# controlling one LED module via a mobile
# dashboard. Zero external dependencies.
# ============================================

import sys
import time
import board
import digitalio
import wifi
import socketpool
import ipaddress
import busio
import displayio
import terminalio
import bagaloozy_ili9488
from adafruit_display_text import label

# --------------------------------------------------
# User Configuration
# --------------------------------------------------
WIFI_SSID = "Arian"
WIFI_PASSWORD = "Amir2003Sh@Q%"

ESP32_IP = "192.168.1.4"
NETMASK = "255.255.255.0"
GATEWAY = "192.168.1.1"
DNS = "1.1.1.1"

LED_PIN = 4

# --------------------------------------------------
# ILI9488 SPI TFT LCD
# ESP32-S3 DevKitC-1
# SCK=12, MOSI=11, MISO=13, CS=10, DC=9, RST=14
# --------------------------------------------------
LCD_SCK = 12
LCD_MOSI = 11
LCD_MISO = 13
LCD_CS = 10
LCD_DC = 9
LCD_RST = 14
LCD_WIDTH = 320
LCD_HEIGHT = 480
LCD_BAUDRATE = 24000000

# Text currently shown on the TFT.
LCD_TEXT = "Hello from ESP32-S3!"

# --------------------------------------------------
# Module Registry (expand here in future versions)
# --------------------------------------------------
MODULES = {
    "LED": {
        "type": "digital_output",
        "gpio": LED_PIN
    }
}

# --------------------------------------------------
# GPIO Safety - ESP32-S3
# --------------------------------------------------
# Valid user GPIOs: 0-21, 33-45, 47-48
# Avoid: 22-32 (reserved for SPI/PSRAM) and 46 (input-only)
_RESERVED_PINS = (22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 46)

def is_valid_gpio(pin):
    if not isinstance(pin, int):
        return False
    if pin < 0 or pin > 48:
        return False
    if pin in _RESERVED_PINS:
        return False
    return True

# --------------------------------------------------
# LED Module
# --------------------------------------------------
class LEDModule:
    def __init__(self, pin_num):
        self.pin_num = pin_num
        self.pin = None
        self._valid = False
        self._state = False
        self._init()

    def _init(self):
        if not is_valid_gpio(self.pin_num):
            print("ERROR: Invalid GPIO {}".format(self.pin_num))
            print("Valid range: 0-21, 33-45, 47-48")
            print("Avoid: 22-32 (reserved) and 46 (input-only)")
            print("Exact availability depends on your specific board.")
            return

        pin_obj = None
        for fmt in ("IO{}", "GPIO{}", "GP{}"):
            attr = fmt.format(self.pin_num)
            if hasattr(board, attr):
                pin_obj = getattr(board, attr)
                break

        if pin_obj is None:
            print("ERROR: GPIO {} not found in board pin map.".format(self.pin_num))
            return

        try:
            self.pin = digitalio.DigitalInOut(pin_obj)
            self.pin.direction = digitalio.Direction.OUTPUT
            self.pin.value = False
            self._valid = True
            print("LED Module")
            print("GPIO: {}".format(self.pin_num))
            print("State: OFF")
        except Exception as e:
            print("ERROR: LED init failed: {}".format(e))

    def on(self):
        if self._valid:
            self.pin.value = True
            self._state = True
            return True
        return False

    def off(self):
        if self._valid:
            self.pin.value = False
            self._state = False
            return True
        return False

    def toggle(self):
        if self._valid:
            self._state = not self._state
            self.pin.value = self._state
            return True
        return False

    @property
    def state_str(self):
        if not self._valid:
            return "ERROR"
        return "ON" if self._state else "OFF"

    def get_status(self):
        return {
            "device": "ESP32-S3",
            "module": "LED",
            "gpio": self.pin_num,
            "state": self.state_str
        }

# --------------------------------------------------
# ILI9488 LCD
# --------------------------------------------------
lcd_display = None
lcd_text_label = None
lcd_text_group = None


def _gpio(num):
    """Return the CircuitPython board pin for an ESP32-S3 GPIO."""
    for name in ("IO{}".format(num), "GPIO{}".format(num), "D{}".format(num)):
        if hasattr(board, name):
            return getattr(board, name)
    raise RuntimeError("GPIO {} is not available in board pin map".format(num))


def init_lcd():
    global lcd_display, lcd_text_label, lcd_text_group

    try:
        displayio.release_displays()

        spi = busio.SPI(
            clock=_gpio(LCD_SCK),
            MOSI=_gpio(LCD_MOSI),
            MISO=_gpio(LCD_MISO)
        )

        display_bus = displayio.FourWire(
            spi,
            command=_gpio(LCD_DC),
            chip_select=_gpio(LCD_CS),
            reset=_gpio(LCD_RST),
            baudrate=LCD_BAUDRATE
        )

        lcd_display = bagaloozy_ili9488.ILI9488(
            display_bus,
            width=LCD_WIDTH,
            height=LCD_HEIGHT
        )

        # Background
        root = displayio.Group()

        bitmap = displayio.Bitmap(LCD_WIDTH, LCD_HEIGHT, 1)
        palette = displayio.Palette(1)
        palette[0] = 0x000000
        background = displayio.TileGrid(
            bitmap,
            pixel_shader=palette
        )
        root.append(background)

        # Text area
        lcd_text_label = label.Label(
            terminalio.FONT,
            text=LCD_TEXT,
            color=0xFFFFFF,
            scale=2
        )
        lcd_text_label.x = 10
        lcd_text_label.y = 25

        lcd_text_group = root
        root.append(lcd_text_label)
        lcd_display.show(root)

        print("ILI9488 LCD: OK")
        print("LCD SPI: SCK={}, MOSI={}, MISO={}".format(
            LCD_SCK, LCD_MOSI, LCD_MISO
        ))
        print("LCD: CS={}, DC={}, RST={}".format(
            LCD_CS, LCD_DC, LCD_RST
        ))
        print("LCD text: {}".format(LCD_TEXT))
        return True

    except Exception as e:
        print("ERROR: ILI9488 init failed: {}".format(e))
        lcd_display = None
        lcd_text_label = None
        lcd_text_group = None
        return False


def _url_decode(value):
    """Small URL decoder suitable for CircuitPython."""
    value = value.replace("+", " ")
    out = bytearray()
    i = 0

    while i < len(value):
        if value[i] == "%" and i + 2 < len(value):
            try:
                out.append(int(value[i + 1:i + 3], 16))
                i += 3
                continue
            except ValueError:
                pass

        # ASCII character
        out.extend(value[i].encode("utf-8"))
        i += 1

    try:
        return bytes(out).decode("utf-8")
    except Exception:
        return value


def _get_query_parameter(path, key):
    if "?" not in path:
        return None

    query = path.split("?", 1)[1]
    for item in query.split("&"):
        if "=" in item:
            k, v = item.split("=", 1)
            if k == key:
                return _url_decode(v)
    return None


def set_lcd_text(new_text):
    global LCD_TEXT

    if lcd_text_label is None:
        return False

    # Keep requests bounded so one browser request cannot consume
    # the entire receive buffer / display memory.
    new_text = str(new_text).replace("\x00", " ").strip()
    if not new_text:
        new_text = " "

    if len(new_text) > 300:
        new_text = new_text[:300]

    LCD_TEXT = new_text
    lcd_text_label.text = new_text
    return True


def json_lcd_status():
    safe_text = LCD_TEXT.replace("\\", "\\\\").replace('"', '\\"').replace(
        "\r", "\\r").replace("\n", "\\n")
    body = '{{"success":true,"text":"{}"}}'.format(safe_text)
    return http_response(body, "application/json")


# --------------------------------------------------
# Web Page (inline, mobile-friendly, no CDN)
# Uses ~PIN~, ~CLS~, ~STATE~ as replace markers
# to avoid str.format() parsing CSS braces.
# --------------------------------------------------
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ESP32-S3 IoT</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;max-width:420px;margin:20px auto;padding:0 15px;background:#f0f2f5;color:#333}
.card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:15px}
h1{font-size:1.3em;margin:0 0 8px}
.status{display:flex;align-items:center;gap:8px;font-size:0.95em;color:#28a745;font-weight:500}
.dot{width:10px;height:10px;background:#28a745;border-radius:50%;display:inline-block;box-shadow:0 0 0 3px rgba(40,167,69,0.2)}
h2{font-size:1.1em;margin:0 0 12px;color:#555;border-bottom:1px solid #eee;padding-bottom:8px}
.row{display:flex;justify-content:space-between;padding:6px 0;font-size:1em}
.state{font-size:1.3em;font-weight:700;margin:10px 0}
.state.on{color:#28a745}
.state.off{color:#dc3545}
.state.err{color:#fd7e14}
.btn{display:block;width:100%;padding:14px;margin:8px 0;border:none;border-radius:8px;font-size:1em;font-weight:600;cursor:pointer;transition:opacity 0.15s}
.btn:hover{opacity:0.9}
.btn-on{background:#28a745;color:#fff}
.btn-off{background:#dc3545;color:#fff}
.btn-toggle{background:#007bff;color:#fff}
.input{box-sizing:border-box;width:100%;padding:13px;border:1px solid #ccc;border-radius:8px;font-size:1em;margin:4px 0 8px}
.preview{background:#111;color:#fff;border-radius:8px;padding:12px;min-height:22px;word-break:break-word;margin-bottom:8px}
.small{font-size:.82em;color:#777}
</style>
</head>
<body>
<div class="card">
<h1>ESP32-S3 IoT Controller</h1>
<div class="status"><span class="dot"></span> ONLINE</div>
</div>

<div class="card">
<h2>ILI9488 TFT LCD</h2>
<div class="row"><span>Resolution</span><strong>320 × 480</strong></div>
<div class="row"><span>Current text</span></div>
<div id="preview" class="preview">~LCDTEXT~</div>
<input id="lcdtext" class="input" type="text" maxlength="300"
       placeholder="Type text for the LCD">
<button class="btn btn-toggle" onclick="sendText()">SHOW ON LCD</button>
<div class="small">Enter text here and it will be sent to the TFT.</div>
</div>

<div class="card">
<h2>LED MODULE</h2>
<div class="row"><span>GPIO</span><strong>~PIN~</strong></div>
<div class="row"><span>Status</span><span id="st" class="state ~CLS~">~STATE~</span></div>
<button class="btn btn-on" onclick="c('on')">TURN ON</button>
<button class="btn btn-off" onclick="c('off')">TURN OFF</button>
<button class="btn btn-toggle" onclick="c('toggle')">TOGGLE</button>
</div>

<script>
function c(cmd){
  fetch('/api/led/'+cmd).then(r=>r.json()).then(d=>u(d));
}
function u(d){
  var s=document.getElementById('st');
  s.textContent=d.state;
  s.className='state '+(d.state=='ON'?'on':d.state=='ERROR'?'err':'off');
}
function sendText(){
  var value=document.getElementById('lcdtext').value;
  fetch('/api/lcd?text='+encodeURIComponent(value))
    .then(r=>r.json())
    .then(d=>{
      if(d.success){
        document.getElementById('preview').textContent=d.text;
        document.getElementById('lcdtext').value='';
      } else {
        alert('LCD error');
      }
    })
    .catch(e=>alert('Connection error'));
}
function p(){
  fetch('/api/status').then(r=>r.json()).then(d=>u(d));
  fetch('/api/lcd/status').then(r=>r.json()).then(d=>{
    if(d.success) document.getElementById('preview').textContent=d.text;
  });
}
p();setInterval(p,3000);
</script>
</body>
</html>"""


# --------------------------------------------------
# HTTP Helpers
# --------------------------------------------------
def http_response(body, ctype):
    return "HTTP/1.1 200 OK\r\nContent-Type: {}\r\nConnection: close\r\n\r\n{}".format(ctype, body)

def json_status(led):
    s = led.get_status()
    body = '{{"device":"{}","module":"{}","gpio":{},"state":"{}"}}'.format(
        s["device"], s["module"], s["gpio"], s["state"])
    return http_response(body, "application/json")

def json_cmd(success, state):
    body = '{{"success":{},"state":"{}"}}'.format("true" if success else "false", state)
    return http_response(body, "application/json")

def not_found():
    return "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\nNot Found"

# --------------------------------------------------
# Request Router
# --------------------------------------------------
def handle_request(path, led):
    # Ignore query parameters when matching normal endpoints.
    route = path.split("?", 1)[0]

    if route == "/":
        cls = "err" if led.state_str == "ERROR" else ("on" if led._state else "off")
        safe_text = LCD_TEXT.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        page = HTML_PAGE.replace("~PIN~", str(led.pin_num)).replace(
            "~CLS~", cls).replace("~STATE~", led.state_str).replace(
            "~LCDTEXT~", safe_text)
        return http_response(page, "text/html")

    if route == "/api/status":
        return json_status(led)

    if route == "/api/lcd/status":
        return json_lcd_status()

    if route == "/api/lcd":
        new_text = _get_query_parameter(path, "text")
        if new_text is None:
            return json_lcd_status()
        ok = set_lcd_text(new_text)
        body_text = LCD_TEXT.replace("\\", "\\\\").replace('"', '\\"').replace(
            "\r", "\\r").replace("\n", "\\n")
        body = '{{"success":{},"text":"{}"}}'.format(
            "true" if ok else "false", body_text)
        return http_response(body, "application/json")

    if route == "/api/led/on":
        ok = led.on()
        return json_cmd(ok, led.state_str)
    if route == "/api/led/off":
        ok = led.off()
        return json_cmd(ok, led.state_str)
    if route == "/api/led/toggle":
        ok = led.toggle()
        return json_cmd(ok, led.state_str)

    return not_found()

# --------------------------------------------------
# WiFi Connection
# --------------------------------------------------
def connect_wifi():
    print("Connecting to WiFi...")

    try:
        ip = ipaddress.IPv4Address(ESP32_IP)
        netmask = ipaddress.IPv4Address(NETMASK)
        gateway = ipaddress.IPv4Address(GATEWAY)
        dns = ipaddress.IPv4Address(DNS)

        wifi.radio.set_ipv4_address(
            ipv4=ip,
            netmask=netmask,
            gateway=gateway,
            ipv4_dns=dns
        )

        wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)

        print("WiFi connected!")
        print()
        print("Static IP:")
        print(wifi.radio.ipv4_address)

        print("Gateway:")
        print(wifi.radio.ipv4_gateway)

        print("Subnet:")
        print(wifi.radio.ipv4_subnet)

        return True

    except Exception as e:
        print("ERROR: WiFi connection failed.")
        print(str(e))
        return False

# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    print("=" * 32)
    print("ESP32-S3 IoT Controller")
    print("=" * 32)
    print()

    try:
        ver = ".".join([str(v) for v in sys.implementation.version])
    except:
        ver = "unknown"
    print("CircuitPython: {}".format(ver))
    print()

    led = LEDModule(LED_PIN)
    print()

    init_lcd()
    print()

    if not connect_wifi():
        print()
        print("Check WIFI_SSID and WIFI_PASSWORD in code.py")
        while True:
            time.sleep(5)

    try:
        pool = socketpool.SocketPool(wifi.radio)
        sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        sock.bind(("0.0.0.0", 80))
        sock.listen(1)
        print()
        print("Web server started.")
        print()
        print("Open:")
        print("http://{}".format(str(wifi.radio.ipv4_address)))
        print()
    except Exception as e:
        print("ERROR: Web server failed to start.")
        print(str(e))
        while True:
            time.sleep(5)

    # Pre-allocate receive buffer outside loop
    rx_buf = bytearray(1024)

    while True:
        conn = None
        try:
            conn, addr = sock.accept()

            n = conn.recv_into(rx_buf)
            if n == 0:
                conn.close()
                continue

            req = rx_buf[:n].decode("utf-8")
            lines = req.split("\r\n")
            if not lines:
                conn.close()
                continue

            parts = lines[0].split()
            if len(parts) < 2:
                conn.close()
                continue

            path = parts[1]
            resp = handle_request(path, led)
            data = resp.encode("utf-8")

            sent = 0
            while sent < len(data):
                n = conn.send(data[sent:])
                if n == 0:
                    break
                sent += n

            conn.close()

        except OSError as e:
            # Silently ignore EAGAIN (11) and ETIMEDOUT (116)
            if hasattr(e, 'errno') and e.errno in (11, 116):
                pass
            else:
                print("ERROR in server loop: OSError {}".format(e))
            if conn:
                try:
                    conn.close()
                except:
                    pass

        except Exception as e:
            print("ERROR in server loop: {}".format(e))
            if conn:
                try:
                    conn.close()
                except:
                    pass
            time.sleep(0.05)

main()
