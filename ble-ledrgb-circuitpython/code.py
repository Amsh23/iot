import time
import board
import pwmio
import microcontroller

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService


# ============================================================
# RGB EXTERNAL LED
#
# Common Anode
#
# RGB pin 1 -> 3.3V
# RGB pin 2 -> GPIO4 = RED
# RGB pin 3 -> GPIO5 = GREEN
# RGB pin 4 -> GPIO6 = BLUE
# ============================================================

print("STARTING RGB...")


red = pwmio.PWMOut(
    microcontroller.pin.GPIO4,
    frequency=1000,
    duty_cycle=65535
)

green = pwmio.PWMOut(
    microcontroller.pin.GPIO5,
    frequency=1000,
    duty_cycle=65535
)

blue = pwmio.PWMOut(
    microcontroller.pin.GPIO6,
    frequency=1000,
    duty_cycle=65535
)


def set_rgb(r, g, b):

    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))

    # Common Anode:
    # LOW  = ON
    # HIGH = OFF

    red.duty_cycle = 65535 - (r * 257)
    green.duty_cycle = 65535 - (g * 257)
    blue.duty_cycle = 65535 - (b * 257)

    print(
        "RGB:",
        r,
        g,
        b
    )


# ============================================================
# LED TEST
# ============================================================

print("RGB TEST")

set_rgb(255, 0, 0)
time.sleep(0.5)

set_rgb(0, 255, 0)
time.sleep(0.5)

set_rgb(0, 0, 255)
time.sleep(0.5)

set_rgb(0, 0, 0)

print("RGB TEST DONE")


# ============================================================
# BLE
# ============================================================

print()
print("STARTING BLE...")


ble = BLERadio()

ble.name = "ESP32-S3-RGB"

uart = UARTService()

advertisement = ProvideServicesAdvertisement(
    uart
)


ble.start_advertising(
    advertisement
)


print()
print("================================")
print("ESP32-S3 RGB BLE READY")
print("================================")
print()
print("DEVICE:")
print("ESP32-S3-RGB")
print()
print("UART COMMANDS:")
print("255,0,0")
print("0,255,0")
print("0,0,255")
print("255,255,255")
print("FF6600")
print("RED")
print("GREEN")
print("BLUE")
print("WHITE")
print("OFF")
print()
print("================================")


# ============================================================
# COMMAND
# ============================================================

def handle_command(command):

    command = command.strip()

    if not command:
        return

    print(
        "RX:",
        command
    )


    # --------------------------------------------------------
    # HEX
    # Example:
    #
    # FF0000
    # FF6600
    # 00FFFF
    # --------------------------------------------------------

    if command.startswith("#"):
        command = command[1:]


    if len(command) == 6:

        try:

            r = int(
                command[0:2],
                16
            )

            g = int(
                command[2:4],
                16
            )

            b = int(
                command[4:6],
                16
            )

            set_rgb(
                r,
                g,
                b
            )

            uart.write(
                (
                    "OK "
                    + command
                    + "\n"
                ).encode()
            )

            return

        except ValueError:
            pass


    # --------------------------------------------------------
    # RGB
    #
    # Example:
    # 255,0,0
    # 100,20,255
    # --------------------------------------------------------

    try:

        parts = command.split(",")

        if len(parts) == 3:

            r = int(parts[0])
            g = int(parts[1])
            b = int(parts[2])

            set_rgb(
                r,
                g,
                b
            )

            uart.write(
                (
                    "OK "
                    + str(r)
                    + ","
                    + str(g)
                    + ","
                    + str(b)
                    + "\n"
                ).encode()
            )

            return

    except ValueError:
        pass


    # --------------------------------------------------------
    # NAMED COLORS
    # --------------------------------------------------------

    command = command.upper()


    if command == "RED":

        set_rgb(
            255,
            0,
            0
        )

        uart.write(
            b"OK RED\n"
        )

        return


    if command == "GREEN":

        set_rgb(
            0,
            255,
            0
        )

        uart.write(
            b"OK GREEN\n"
        )

        return


    if command == "BLUE":

        set_rgb(
            0,
            0,
            255
        )

        uart.write(
            b"OK BLUE\n"
        )

        return


    if command == "WHITE":

        set_rgb(
            255,
            255,
            255
        )

        uart.write(
            b"OK WHITE\n"
        )

        return


    if command == "YELLOW":

        set_rgb(
            255,
            255,
            0
        )

        uart.write(
            b"OK YELLOW\n"
        )

        return


    if command == "PURPLE":

        set_rgb(
            255,
            0,
            255
        )

        uart.write(
            b"OK PURPLE\n"
        )

        return


    if command == "CYAN":

        set_rgb(
            0,
            255,
            255
        )

        uart.write(
            b"OK CYAN\n"
        )

        return


    if command == "OFF":

        set_rgb(
            0,
            0,
            0
        )

        uart.write(
            b"OK OFF\n"
        )

        return


    uart.write(
        b"ERROR\n"
    )


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    try:

        if not ble.connected:

            if not ble.advertising:

                print(
                    "Advertising..."
                )

                ble.start_advertising(
                    advertisement
                )

            time.sleep(0.1)

            continue


        # ----------------------------------------------------
        # BLE CONNECTED
        # ----------------------------------------------------

        if uart.in_waiting:

            data = uart.read(
                uart.in_waiting
            )

            if data:

                try:

                    text = data.decode(
                        "utf-8"
                    )

                    commands = text.split(
                        "\n"
                    )

                    for command in commands:

                        handle_command(
                            command
                        )

                except Exception as e:

                    print(
                        "RX ERROR:",
                        e
                    )


        time.sleep(0.02)


    except Exception as e:

        print(
            "BLE ERROR:",
            type(e).__name__,
            e
        )

        time.sleep(1)