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
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;max-width:400px;margin:20px auto;padding:0 15px;background:#f0f2f5;color:#333}
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
</style>
</head>
<body>
<div class="card">
<h1>ESP32-S3 IoT Controller</h1>
<div class="status"><span class="dot"></span> ONLINE</div>
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
function c(cmd){fetch('/api/led/'+cmd).then(r=>r.json()).then(d=>u(d));}
function u(d){var s=document.getElementById('st');s.textContent=d.state;s.className='state '+(d.state=='ON'?'on':d.state=='ERROR'?'err':'off');}
function p(){fetch('/api/status').then(r=>r.json()).then(d=>u(d));}
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
    if path == "/":
        cls = "err" if led.state_str == "ERROR" else ("on" if led._state else "off")
        page = HTML_PAGE.replace("~PIN~", str(led.pin_num)).replace("~CLS~", cls).replace("~STATE~", led.state_str)
        return http_response(page, "text/html")
    if path == "/api/status":
        return json_status(led)
    if path == "/api/led/on":
        ok = led.on()
        return json_cmd(ok, led.state_str)
    if path == "/api/led/off":
        ok = led.off()
        return json_cmd(ok, led.state_str)
    if path == "/api/led/toggle":
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