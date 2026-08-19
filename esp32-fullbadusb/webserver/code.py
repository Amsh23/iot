# ============================================================
# ESP32-S3 COMPLETE BadUSB v5.2 - FULLY FIXED
# No f-strings, no newlines in strings, CircuitPython compatible
# ============================================================

import usb_hid
import board
import digitalio
import time
import os
import sys
import wifi
import socketpool

print("=" * 50)
print("[COMPLETE v5.2] ESP32-S3 BadUSB + Free WiFi AP")
print("=" * 50)

# ============================================================
# CONFIGURATION
# ============================================================

AP_SSID = "Free_WiFi_Guest"
AP_PASSWORD = "12345678"
AP_CHANNEL = 6

WEB_PORT = 80
PAYLOAD_FILE = "payload.txt"
AUTO_EXECUTE_DELAY = 3

# ============================================================
# HID INIT
# ============================================================

try:
    from adafruit_hid.keyboard import Keyboard
    from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
    from adafruit_hid.keycode import Keycode
    print("[OK] adafruit_hid imported")
except ImportError as e:
    print("[ERROR] adafruit_hid NOT FOUND!")
    sys.exit(1)

try:
    kbd = Keyboard(usb_hid.devices)
    layout = KeyboardLayoutUS(kbd)
    print("[OK] HID Keyboard ready")
except Exception as e:
    print("[ERROR] HID init failed:", e)
    sys.exit(1)

# ============================================================
# LED
# ============================================================

led = None
led_candidates = [
    ("LED", getattr(board, "LED", None)),
    ("IO38", getattr(board, "IO38", None)),
    ("IO2", getattr(board, "IO2", None)),
    ("IO48", getattr(board, "IO48", None)),
    ("IO47", getattr(board, "IO47", None)),
]

for name, pin in led_candidates:
    if pin is None:
        continue
    try:
        l = digitalio.DigitalInOut(pin)
        l.direction = digitalio.Direction.OUTPUT
        print("[OK] LED on", name)
        led = l
        break
    except:
        pass

def led_on():
    if led: led.value = True
def led_off():
    if led: led.value = False
def led_blink(count=1, delay=0.2):
    for _ in range(count):
        led_on(); time.sleep(delay)
        led_off(); time.sleep(delay)

# ============================================================
# KEYCODE MAP
# ============================================================

KEYCODE_MAP = {
    "A": Keycode.A, "B": Keycode.B, "C": Keycode.C, "D": Keycode.D,
    "E": Keycode.E, "F": Keycode.F, "G": Keycode.G, "H": Keycode.H,
    "I": Keycode.I, "J": Keycode.J, "K": Keycode.K, "L": Keycode.L,
    "M": Keycode.M, "N": Keycode.N, "O": Keycode.O, "P": Keycode.P,
    "Q": Keycode.Q, "R": Keycode.R, "S": Keycode.S, "T": Keycode.T,
    "U": Keycode.U, "V": Keycode.V, "W": Keycode.W, "X": Keycode.X,
    "Y": Keycode.Y, "Z": Keycode.Z,
    "0": Keycode.ZERO, "1": Keycode.ONE, "2": Keycode.TWO,
    "3": Keycode.THREE, "4": Keycode.FOUR, "5": Keycode.FIVE,
    "6": Keycode.SIX, "7": Keycode.SEVEN, "8": Keycode.EIGHT,
    "9": Keycode.NINE,
    "ENTER": Keycode.ENTER, "RETURN": Keycode.RETURN,
    "ESC": Keycode.ESCAPE, "ESCAPE": Keycode.ESCAPE,
    "TAB": Keycode.TAB, "SPACE": Keycode.SPACE,
    "BACKSPACE": Keycode.BACKSPACE, "DELETE": Keycode.DELETE,
    "INSERT": Keycode.INSERT, "HOME": Keycode.HOME, "END": Keycode.END,
    "PAGEUP": Keycode.PAGE_UP, "PAGEDOWN": Keycode.PAGE_DOWN,
    "UP": Keycode.UP_ARROW, "UPARROW": Keycode.UP_ARROW,
    "DOWN": Keycode.DOWN_ARROW, "DOWNARROW": Keycode.DOWN_ARROW,
    "LEFT": Keycode.LEFT_ARROW, "LEFTARROW": Keycode.LEFT_ARROW,
    "RIGHT": Keycode.RIGHT_ARROW, "RIGHTARROW": Keycode.RIGHT_ARROW,
    "GUI": Keycode.GUI, "WINDOWS": Keycode.GUI, "COMMAND": Keycode.GUI,
    "SHIFT": Keycode.LEFT_SHIFT, "ALT": Keycode.LEFT_ALT,
    "CTRL": Keycode.LEFT_CONTROL, "CONTROL": Keycode.LEFT_CONTROL,
    "F1": Keycode.F1, "F2": Keycode.F2, "F3": Keycode.F3,
    "F4": Keycode.F4, "F5": Keycode.F5, "F6": Keycode.F6,
    "F7": Keycode.F7, "F8": Keycode.F8, "F9": Keycode.F9,
    "F10": Keycode.F10, "F11": Keycode.F11, "F12": Keycode.F12,
    "MINUS": Keycode.MINUS, "EQUAL": Keycode.EQUALS, "EQUALS": Keycode.EQUALS,
    "LEFTBRACKET": Keycode.LEFT_BRACKET, "RIGHTBRACKET": Keycode.RIGHT_BRACKET,
    "BACKSLASH": Keycode.BACKSLASH, "SEMICOLON": Keycode.SEMICOLON,
    "QUOTE": Keycode.QUOTE, "APOSTROPHE": Keycode.QUOTE,
    "GRAVE": Keycode.GRAVE_ACCENT, "COMMA": Keycode.COMMA,
    "PERIOD": Keycode.PERIOD, "SLASH": Keycode.FORWARD_SLASH,
    "CAPSLOCK": Keycode.CAPS_LOCK, "PRINTSCREEN": Keycode.PRINT_SCREEN,
    "SCROLLLOCK": Keycode.SCROLL_LOCK, "PAUSE": Keycode.PAUSE,
    "BREAK": Keycode.PAUSE, "NUMLOCK": Keycode.KEYPAD_NUMLOCK,
    "MENU": Keycode.APPLICATION, "APP": Keycode.APPLICATION,
}

def parse_combo(keys_str):
    keys = keys_str.split()
    kcs = []
    for k in keys:
        ku = k.upper()
        if ku in KEYCODE_MAP:
            kcs.append(KEYCODE_MAP[ku])
        elif len(k) == 1 and k.upper() in KEYCODE_MAP:
            kcs.append(KEYCODE_MAP[k.upper()])
    return kcs

def exec_line(line, default_delay=0):
    line = line.strip()
    if not line:
        return default_delay
    if line.startswith("REM "):
        return default_delay
    if line.startswith("DEFAULT_DELAY ") or line.startswith("DEFAULTDELAY "):
        try:
            return int(line.split(None, 1)[1])
        except:
            return default_delay
    if line.startswith("DELAY "):
        try:
            time.sleep(int(line.split(None, 1)[1]) / 1000.0)
        except:
            pass
        return default_delay
    if line.startswith("STRING "):
        layout.write(line[7:])
        return default_delay
    if line.startswith("STRINGLN "):
        layout.write(line[9:])
        kbd.press(Keycode.ENTER)
        kbd.release_all()
        return default_delay
    kcs = parse_combo(line)
    if kcs:
        for kc in kcs:
            kbd.press(kc)
        kbd.release_all()
    return default_delay

def run_payload(path):
    print("[+] Running:", path)
    try:
        with open("/" + path, "r") as f:
            lines = f.readlines()
    except OSError as e:
        print("[!] Error:", e)
        led_blink(5, 0.1)
        return
    dd = 0
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        if line.strip().upper().startswith("REPEAT "):
            try:
                cnt = int(line.strip().split(None, 1)[1])
                if i > 0:
                    prev = lines[i-1].rstrip("\n")
                    for _ in range(cnt):
                        r = exec_line(prev, dd)
                        if isinstance(r, int): dd = r
                        time.sleep(dd / 1000.0)
            except Exception as e:
                print("[!] REPEAT error:", e)
        else:
            r = exec_line(line, dd)
            if isinstance(r, int): dd = r
            time.sleep(dd / 1000.0)
        i += 1
    print("[+] Payload finished!")
    led_blink(3, 0.3)

# ============================================================
# AUTO-EXECUTE
# ============================================================

def get_ap_ip():
    try:
        return str(wifi.radio.ipv4_address_ap)
    except:
        return "192.168.4.1"

def auto_execute():
    print("[AUTO] Starting in", AUTO_EXECUTE_DELAY, "s...")
    for i in range(AUTO_EXECUTE_DELAY, 0, -1):
        print("[AUTO]", i, "...")
        led_blink(1, 0.1)
        time.sleep(1)

    print("[AUTO] Executing payload!")
    led_on()
    run_payload(PAYLOAD_FILE)
    led_off()

    ap_ip = get_ap_ip()
    print("[AUTO] ESP32 AP IP:", ap_ip)

    # Write IP to Notepad
    print("[AUTO] Writing IP to Notepad...")
    time.sleep(1)

    kbd.press(Keycode.LEFT_GUI, Keycode.R)
    kbd.release_all()
    time.sleep(0.5)
    layout.write("notepad")
    kbd.press(Keycode.ENTER)
    kbd.release_all()
    time.sleep(1)

    layout.write("========================================")
    kbd.press(Keycode.ENTER)
    kbd.release_all()
    layout.write("ESP32-S3 BadUSB Controller")
    kbd.press(Keycode.ENTER)
    kbd.release_all()
    layout.write("========================================")
    kbd.press(Keycode.ENTER)
    kbd.release_all()
    layout.write("Connect to WiFi: " + AP_SSID)
    kbd.press(Keycode.ENTER)
    kbd.release_all()
    layout.write("WiFi Password: " + (AP_PASSWORD if AP_PASSWORD else "(Open)"))
    kbd.press(Keycode.ENTER)
    kbd.release_all()
    layout.write("Web Control: http://" + ap_ip)
    kbd.press(Keycode.ENTER)
    kbd.release_all()
    layout.write("========================================")

    print("[AUTO] Notepad done!")

    # Open and close CMD
    print("[AUTO] Opening CMD...")
    time.sleep(1)
    kbd.press(Keycode.LEFT_GUI, Keycode.R)
    kbd.release_all()
    time.sleep(0.5)
    layout.write("cmd")
    kbd.press(Keycode.ENTER)
    kbd.release_all()
    time.sleep(2)

    layout.write("exit")
    kbd.press(Keycode.ENTER)
    kbd.release_all()
    print("[AUTO] CMD closed!")
    print("[AUTO] All done!")
    led_blink(5, 0.2)

# ============================================================
# FREE WIFI AP + WEB SERVER
# ============================================================

def start_ap_and_web():
    try:
        print("[WiFi] Creating AP:", AP_SSID)
        if AP_PASSWORD:
            wifi.radio.start_ap(AP_SSID, AP_PASSWORD, channel=AP_CHANNEL)
        else:
            wifi.radio.start_ap(AP_SSID, channel=AP_CHANNEL)

        ap_ip = get_ap_ip()
        print("[WiFi] AP started! IP:", ap_ip)
        print("[WiFi] SSID:", AP_SSID)
        print("[WiFi] Password:", AP_PASSWORD if AP_PASSWORD else "Open")

        pool = socketpool.SocketPool(wifi.radio)
        server_socket = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", WEB_PORT))
        server_socket.listen(2)
        server_socket.setblocking(False)
        print("[Web] Server running on http://" + ap_ip + ":" + str(WEB_PORT))

        return server_socket
    except Exception as e:
        print("[WiFi/Web] Error:", e)
        return None

def build_html(ap_ip):
    # Build HTML using simple string concatenation - NO f-strings, NO newlines in quotes
    html = "HTTP/1.1 200 OK\r\n"
    html += "Content-Type: text/html\r\n"
    html += "Connection: close\r\n"
    html += "\r\n"
    html += "<!DOCTYPE html><html><head><meta charset="UTF-8">"
    html += "<meta name="viewport" content="width=device-width, initial-scale=1.0">"
    html += "<title>ESP32 BadUSB</title>"
    html += "<style>"
    html += "body{font-family:Arial;background:#1a1a2e;color:#fff;text-align:center;padding:20px}"
    html += "h1{color:#e94560;font-size:28px;margin-bottom:10px}"
    html += ".info{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);"
    html += "border-radius:12px;padding:15px;margin-bottom:20px;text-align:left}"
    html += ".info p{margin:5px 0;font-size:14px;color:#0ff}"
    html += "button{width:100%;padding:18px;margin:8px 0;border:none;border-radius:12px;"
    html += "font-size:16px;font-weight:bold;cursor:pointer;color:#fff}"
    html += ".fire{background:#e94560}.rick{background:#f39c12}"
    html += ".bsod{background:#9b59b6}.prank{background:#00d2ff}"
    html += ".lock{background:#2c3e50}.vol{background:#27ae60}"
    html += ".mute{background:#c0392b}.cmd{background:#8e44ad}"
    html += "</style></head><body>"
    html += "<h1>ESP32-S3 BadUSB</h1>"
    html += "<div class="info">"
    html += "<p>WiFi: <strong>" + AP_SSID + "</strong></p>"
    html += "<p>Pass: <strong>" + (AP_PASSWORD if AP_PASSWORD else "Open") + "</strong></p>"
    html += "<p>IP: <strong>" + ap_ip + "</strong></p>"
    html += "</div>"
    html += "<a href="/fire"><button class="fire">FIRE PAYLOAD</button></a>"
    html += "<a href="/rickroll"><button class="rick">Rick Roll</button></a>"
    html += "<a href="/bsod"><button class="bsod">Fake BSOD</button></a>"
    html += "<a href="/prank"><button class="prank">Prank Type</button></a>"
    html += "<a href="/lock"><button class="lock">Lock Screen</button></a>"
    html += "<a href="/volup"><button class="vol">Vol MAX</button></a>"
    html += "<a href="/mute"><button class="mute">Mute</button></a>"
    html += "<a href="/cmd"><button class="cmd">Open CMD</button></a>"
    html += "<p style="margin-top:20px;color:#888;font-size:12px">ESP32-S3 v5.2</p>"
    html += "</body></html>"
    return html

def handle_web_request(client_socket):
    try:
        # Receive data
        buffer = bytearray(1024)
        try:
            bytes_received = client_socket.recv_into(buffer)
        except OSError as e:
            if hasattr(e, 'errno') and e.errno == 11:
                return
            raise

        if bytes_received == 0:
            try:
                client_socket.close()
            except:
                pass
            return

        # Decode
        try:
            request = buffer[:bytes_received].decode("utf-8")
        except:
            request = str(buffer[:bytes_received])

        ap_ip = get_ap_ip()
        html = build_html(ap_ip)

        # Handle commands
        if "/fire" in request:
            print("[Web] FIRE!")
            run_payload(PAYLOAD_FILE)
        elif "/rickroll" in request:
            print("[Web] Rick Roll!")
            kbd.press(Keycode.LEFT_GUI, Keycode.R)
            kbd.release_all()
            time.sleep(0.5)
            layout.write("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            kbd.press(Keycode.ENTER)
            kbd.release_all()
        elif "/bsod" in request:
            print("[Web] BSOD!")
            kbd.press(Keycode.LEFT_GUI, Keycode.R)
            kbd.release_all()
            time.sleep(0.5)
            layout.write("notepad")
            kbd.press(Keycode.ENTER)
            kbd.release_all()
            time.sleep(1)
            layout.write("A problem has been detected and Windows has been shut down...")
        elif "/prank" in request:
            print("[Web] Prank!")
            import random
            for _ in range(50):
                layout.write(chr(random.randint(65, 90)))
                time.sleep(0.05)
        elif "/lock" in request:
            print("[Web] Lock!")
            kbd.press(Keycode.LEFT_GUI, Keycode.L)
            kbd.release_all()
        elif "/volup" in request:
            print("[Web] Vol UP!")
            for _ in range(10):
                kbd.press(Keycode.F12)
                kbd.release_all()
                time.sleep(0.1)
        elif "/mute" in request:
            print("[Web] Mute!")
            kbd.press(Keycode.F10)
            kbd.release_all()
        elif "/cmd" in request:
            print("[Web] CMD!")
            kbd.press(Keycode.LEFT_GUI, Keycode.R)
            kbd.release_all()
            time.sleep(0.5)
            layout.write("cmd")
            kbd.press(Keycode.ENTER)
            kbd.release_all()

        # Send response
        try:
            client_socket.send(html.encode())
        except:
            pass

        # Close connection
        try:
            client_socket.close()
        except:
            pass

    except Exception as e:
        print("[Web] Error:", e)
        try:
            client_socket.close()
        except:
            pass

# ============================================================
# MAIN
# ============================================================

print("[DEBUG] Waiting for USB enumeration...")
time.sleep(2)

# Check payload
files = os.listdir("/")
print("[DEBUG] Root files:", files)

if PAYLOAD_FILE not in files:
    print("[ERROR] '" + PAYLOAD_FILE + "' NOT FOUND!")
    while True:
        led_blink(1, 0.5)
        time.sleep(1)
else:
    print("[OK] '" + PAYLOAD_FILE + "' found")

# Start WiFi AP and Web Server FIRST
print("[MAIN] Starting WiFi AP and Web Server...")
server_socket = start_ap_and_web()

# Auto-execute payload
auto_execute()

print("[MAIN] Ready! Connect to WiFi and open browser!")

# Main loop
while True:
    if server_socket:
        try:
            client, addr = server_socket.accept()
            print("[Web] Client from", addr)
            handle_web_request(client)
        except OSError as e:
            if hasattr(e, 'errno') and e.errno == 11:
                pass
            else:
                print("[Web] Accept error:", e)
        except Exception as e:
            print("[Web] Accept error:", e)

    time.sleep(0.1)
