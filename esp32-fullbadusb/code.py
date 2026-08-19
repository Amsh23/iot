# ============================================================
# ESP32-S3 DevKit - DuckyScript Interpreter (FIXED v2)
# Bug fix: os.listdir("/") returns names without leading /
# ============================================================

import usb_hid
import board
import digitalio
import time
import os
import sys
import traceback

print("=" * 50)
print("[DEBUG] ESP32-S3 DuckyScript v2.0")
print("=" * 50)

# --- HID libs ---
try:
    from adafruit_hid.keyboard import Keyboard
    from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
    from adafruit_hid.keycode import Keycode
    print("[OK] adafruit_hid imported")
except ImportError as e:
    print("[ERROR] adafruit_hid NOT FOUND!")
    print("[ERROR] Copy adafruit_hid/ folder to lib/ on CIRCUITPY drive")
    sys.exit(1)

# --- Init HID ---
try:
    kbd = Keyboard(usb_hid.devices)
    layout = KeyboardLayoutUS(kbd)
    print("[OK] HID Keyboard ready")
except Exception as e:
    print("[ERROR] HID init failed:", e)
    sys.exit(1)

# --- Find BOOT button ---
button = None
pin_candidates = [
    ("IO0", getattr(board, "IO0", None)),
    ("BUTTON", getattr(board, "BUTTON", None)),
    ("BOOT0", getattr(board, "BOOT0", None)),
    ("GP0", getattr(board, "GP0", None)),
]

for name, pin in pin_candidates:
    if pin is None:
        continue
    try:
        btn = digitalio.DigitalInOut(pin)
        btn.direction = digitalio.Direction.INPUT
        btn.pull = digitalio.Pull.UP
        print(f"[OK] Button on {name}")
        button = btn
        break
    except Exception as e:
        print(f"[SKIP] {name} failed: {e}")

if button is None:
    print("[WARN] No button found! Auto-fire in 5s.")

# --- Find LED ---
led = None
led_candidates = [
    ("LED", getattr(board, "LED", None)),
    ("IO38", getattr(board, "IO38", None)),
    ("IO2", getattr(board, "IO2", None)),
    ("IO48", getattr(board, "IO48", None)),
    ("IO47", getattr(board, "IO47", None)),
    ("NEOPIXEL", getattr(board, "NEOPIXEL", None)),
]

for name, pin in led_candidates:
    if pin is None:
        continue
    try:
        l = digitalio.DigitalInOut(pin)
        l.direction = digitalio.Direction.OUTPUT
        print(f"[OK] LED on {name}")
        led = l
        break
    except:
        pass

if led is None:
    print("[WARN] No LED found")

def led_on():
    if led: led.value = True
def led_off():
    if led: led.value = False
def led_blink(count=1, delay=0.2):
    for _ in range(count):
        led_on(); time.sleep(delay)
        led_off(); time.sleep(delay)

# --- Check payload (FIXED: no leading slash in check) ---
PAYLOAD_FILE = "payload.txt"  # FIXED: was "/payload.txt"

try:
    files = os.listdir("/")
    print("[DEBUG] Root files:", files)
except Exception as e:
    print("[ERROR] Cannot list files:", e)
    files = []

if PAYLOAD_FILE not in files:
    print(f"[ERROR] '{PAYLOAD_FILE}' NOT FOUND!")
    print("[ERROR] Create payload.txt on CIRCUITPY drive")
    while True:
        led_blink(1, 0.5)
        time.sleep(1)
else:
    print(f"[OK] '{PAYLOAD_FILE}' found")

# --- KEYCODE MAP ---
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
    print(f"[+] Running: {path}")
    try:
        with open("/" + path, "r") as f:
            lines = f.readlines()
    except OSError as e:
        print(f"[!] Error: {e}")
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
                print(f"[!] REPEAT error: {e}")
        else:
            r = exec_line(line, dd)
            if isinstance(r, int): dd = r
            time.sleep(dd / 1000.0)
        i += 1
    print("[+] Payload finished!")
    led_blink(3, 0.3)

# --- MAIN ---
print("[DEBUG] Waiting for USB enumeration...")
time.sleep(2)
print("[DEBUG] Ready!")
if button:
    print("[DEBUG] Press BOOT button to fire")
else:
    print("[DEBUG] Auto-fire in 5 seconds...")

led_blink(2, 0.1)
start_time = time.monotonic()

while True:
    if not button and time.monotonic() - start_time > 5:
        print("[AUTO-FIRE] Executing payload...")
        led_on()
        run_payload(PAYLOAD_FILE)
        led_off()
        while True:
            time.sleep(1)

    if button and not button.value:
        print("[+] Button pressed! Executing...")
        led_on()
        time.sleep(0.3)
        run_payload(PAYLOAD_FILE)
        led_off()
        print("[+] Done. Reset to run again.")
        while True:
            time.sleep(1)

    time.sleep(0.05)
