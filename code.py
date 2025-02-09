# SPDX-FileCopyrightText: © 2025 Peter Tacon <contacto@petertacon.com>
#
# SPDX-License-Identifier: MIT

"""LoRa Transceiver - Test of Send package"""

# Core Libraries
import time
import board
import busio
import digitalio
import terminalio
import displayio

# Radio, LED and OLED Libraries
import neopixel
from adafruit_display_text import label
import adafruit_displayio_ssd1306
import adafruit_rfm9x

# CPU and Button Libraries
import microcontroller
import keypad

# ------------- Configuration ------------- #
# LoRa Radio Frequency
RADIO_FREQ_MHZ = 915.0  # Set to 868.0 in EU, or as appropriate

# Time (in seconds) after which we consider connection "lost" if no packets arrive
DISCONNECT_TIMEOUT = 10

# NeoPixel Colors (R, G, B)
COLOR_DISCONNECTED = (255, 0, 0)   # Red
COLOR_CONNECTED    = (0, 255, 0)   # Green
COLOR_RECEIVING    = (0, 0, 255)   # Blue

# ------------- Setup Hardware ------------- #

displayio.release_displays()

# Use for I2C
i2c = board.I2C()

# Create the SSD1306 OLED class.
display_bus = displayio.I2CDisplay(i2c, device_address=0x3c)

WIDTH = 128
HEIGHT = 32
BORDER = 5

display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)

# Setup LoRa Radio
cs_pin = digitalio.DigitalInOut(board.RFM_CS)
reset_pin = digitalio.DigitalInOut(board.RFM_RST)
rfm9x = adafruit_rfm9x.RFM9x(board.SPI(), cs_pin, reset_pin, RADIO_FREQ_MHZ)
rfm9x.tx_power = 23  # Max power, adjust as needed
# Optionally, set the encryption key (must match on both ends!)
# rfm9x.encryption_key = b"\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08"

# NeoPixel
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2, auto_write=True)
pixel[0] = COLOR_DISCONNECTED

# BOOT/USER button setup
# NOTE: Adjust to the actual pin if the BOOT button is not user-accessible.
button = keypad.Keys((board.BUTTON,), value_when_pressed=False)

# ------------- Variables ------------- #
received_count = 0
last_message = ""
last_packet_time = 0  # track the last time we received a packet

# ------------- Helper Functions ------------- #

def show_oled_info(last_msg, count, temp_c):
    """
    Update the SSD1306 display with:
    - Last received message
    - Count of messages
    - CPU temperature
    """
    # Make the display context
    splash = displayio.Group()
    display.root_group = splash
    
    #Draw first rectangle
    color_bitmap = displayio.Bitmap(64, 16, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF # White
    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    # Draw a smaller inner rectangle
    inner_bitmap = displayio.Bitmap(62, 14, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0x000000 # Black
    inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=1, y=1)
    splash.append(inner_sprite)

    #Draw second rectangle
    color_bitmap = displayio.Bitmap(128, 16, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF # White
    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=16)
    splash.append(bg_sprite)

    # Draw a smaller inner 2nd rectangle
    inner_bitmap = displayio.Bitmap(126, 14, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0x000000 # Black
    inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=1, y=17)
    splash.append(inner_sprite)

    # Draw title label
    text = "LoRa test"
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=5, y=7)

    # Draw count label
    text2 = f"Count:{count}"
    text_area2 = label.Label(terminalio.FONT, text=text2, color=0xFFFF00, x=69, y=5)

    # Draw CPU label
    text3 = f"{temp_c:.1f}C"
    text_area3 = label.Label(terminalio.FONT, text=text3, color=0xFFFF00, x=5, y=23)
    
    # Draw message label
    text4 = f"{last_msg}"
    text_area4 = label.Label(terminalio.FONT, text=text4, color=0xFFFF00, x=50, y=23)

    splash.append(text_area)
    splash.append(text_area2)
    splash.append(text_area3)
    splash.append(text_area4)

def update_neopixel():
    """
    Update NeoPixel based on connectivity status.
    - If no packets for > DISCONNECT_TIMEOUT => Red
    - Else => Green
    (When actively receiving, we'll briefly set Blue in the main loop.)
    """
    if (time.monotonic() - last_packet_time) > DISCONNECT_TIMEOUT:
        pixel[0] = COLOR_DISCONNECTED
    else:
        pixel[0] = COLOR_CONNECTED

# ------------- Main Loop ------------- #
while True:
    # 1) Check if we received any LoRa packets
    packet = rfm9x.receive(timeout=0.1)  # Non-blocking, short timeout
    if packet is not None:
        # We got a packet!
        pixel[0] = COLOR_RECEIVING  # Turn Blue while we process
        try:
            received_str = str(packet, "utf-8")
        except:
            received_str = "<Decode Error>"
        last_message = received_str
        received_count += 1
        last_packet_time = time.monotonic()
        
        # Show the info on OLED
        cpu_temp = microcontroller.cpu.temperature
        show_oled_info(last_message, received_count, cpu_temp)
        
        # Give a small delay to show "receiving" color
        time.sleep(0.2)
        update_neopixel()  # Return to connected or disconnected color

    # 2) Check if the button is pressed; if so, send a LoRa packet
    
    button_press = button.events.get()
    if button_press:
        if button_press.pressed:
            # Actually send something
            send_str = "Hi RP2040 1"
            rfm9x.send(send_str.encode("utf-8"))
            print("Package Sent")
        else:
            print("COMM Error")

    # 3) Periodically update CPU temp on the display if nothing else changes
    if (time.monotonic() - last_packet_time) < DISCONNECT_TIMEOUT:
        # Only update the screen if connected, so we see live temperature
        cpu_temp = microcontroller.cpu.temperature
        show_oled_info(last_message, received_count, cpu_temp)

    # 4) Check time since last packet to determine connection status (Red/Green)
    update_neopixel()
    
    time.sleep(1)