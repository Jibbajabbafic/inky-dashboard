import threading
import time

import gpiod
import gpiodevice
from font_fredoka_one import FredokaOne
from gpiod.line import Bias, Direction, Value
from inky.auto import auto
from PIL import Image, ImageDraw, ImageFont

LED_PIN = 13
LED_BLINK_INTERVAL = 0.2

DISPLAY_SATURATION = 0.1
DISPLAY_WAIT_TIME = 30


def main():
    print("Hello from inky-dashboard!", flush=True)

    # Find the gpiochip device we need, we'll use
    # gpiodevice for this, since it knows the right device
    # for its supported platforms.
    chip = gpiodevice.find_chip_by_platform()

    # Setup for the LED pin
    led = chip.line_offset_from_id(LED_PIN)
    gpio = chip.request_lines(
        consumer="inky",
        config={
            led: gpiod.LineSettings(direction=Direction.OUTPUT, bias=Bias.DISABLED)
        },
    )

    inky_display = auto(ask_user=True, verbose=True)
    try:
        while True:
            print("Drawing...", flush=True)
            stop_blink = threading.Event()
            blink_thread = threading.Thread(
                target=blink_led,
                args=(gpio, led, stop_blink, LED_BLINK_INTERVAL),
                daemon=True,
            )
            blink_thread.start()
            draw_current_time(inky_display)
            stop_blink.set()
            blink_thread.join()
            gpio.set_value(led, Value.INACTIVE)
            print(f"Waiting {DISPLAY_WAIT_TIME}s...", flush=True)
            time.sleep(DISPLAY_WAIT_TIME)
    except KeyboardInterrupt:
        print("Stopped.", flush=True)
    finally:
        gpio.set_value(led, Value.INACTIVE)


def blink_led(gpio, led, stop_event, interval=0.5):
    while not stop_event.is_set():
        gpio.set_value(led, Value.ACTIVE)
        stop_event.wait(interval)
        gpio.set_value(led, Value.INACTIVE)
        stop_event.wait(interval)


def draw_current_time(inky_display):
    print("Setting up drawing context...", flush=True)
    # Create new PIL image with a white background
    image = Image.new(
        "P", (inky_display.width, inky_display.height), inky_display.WHITE
    )
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(FredokaOne, 72)

    # draw some shapes
    draw.rectangle((50, 50, 200, 200), fill=inky_display.YELLOW)  # Rectangle
    draw.ellipse((150, 150, 300, 300), fill=inky_display.RED)  # Circle (ellipse)
    draw.line((0, 0, 400, 400), fill=inky_display.BLUE, width=10)  # Diagonal line

    # draw text
    current_time = time.strftime("%H:%M:%S")
    centre_point = get_centre_point_for_text(inky_display, current_time, font)
    draw.text(centre_point, current_time, inky_display.BLACK, font)

    inky_display.set_image(image, saturation=DISPLAY_SATURATION)
    print("Updating display...", flush=True)
    start_time = time.time()
    inky_display.show()
    duration = time.time() - start_time
    print(f"Displayed in {duration:.2f}s", flush=True)


def get_centre_point_for_text(display, text, font):
    _, _, w, h = font.getbbox(text)
    x = (display.width / 2) - (w / 2)
    y = (display.height / 2) - (h / 2)
    return (x, y)


if __name__ == "__main__":
    main()
