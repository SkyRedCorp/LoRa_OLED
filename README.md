# LoRa_OLED
LoRa Transceiver - Test of Send package

This is a transceiver who sends to the other board a string every single time the button is pressed. In the screen it will show the string, the times every module received the word and the CPU temperature on the device. and due every board has a integrated NeoPixel, when both modules are connected and receiving the data, it is turning on in Green, if a board is receiving the string, it is turning Blue, but if there's no connection, it will Red the color.

Board: Adafruit Feather RP2040 RFM95

For SSD1306 screen, I've modified the following example: https://wokwi.com/projects/309427357921313345
But followed same wiring schematics

Additional Libraries:
- adafruit_rfm9x
- adafruit_displayio_ssd1306
- adafruit_display_text
- neopixel
