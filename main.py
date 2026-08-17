import io
import os
import textwrap
import threading
import time

import gpiod
import gpiodevice
import requests
from dotenv import load_dotenv
from font_fredoka_one import FredokaOne
from gpiod.line import Bias, Direction, Value
from inky.auto import auto
from inky.mock import InkyMockImpression
from PIL import Image, ImageDraw, ImageFont

# Configuration values
load_dotenv()
# Required environment variables
IMAGE_URL = os.environ["IMAGE_URL"]
# Optional environment variables with defaults
IMAGE_TOKEN = os.environ.get("IMAGE_TOKEN", "")
LED_BLINK_INTERVAL = float(os.environ.get("LED_BLINK_INTERVAL", 0.2))
DISPLAY_SATURATION = float(os.environ.get("DISPLAY_SATURATION", 0.1))
DISPLAY_WAIT_TIME = int(os.environ.get("DISPLAY_WAIT_TIME", 1800))


def main():
    print("Starting inky-dashboard!", flush=True)

    mock, gpio, led = setup_inky_led()

    if mock:
        print("Using InkyMockImpression for simulation.", flush=True)
        inky_display = InkyMockImpression(resolution=(800, 480))
    else:
        inky_display = auto(ask_user=True, verbose=True)

    try:
        while True:
            print("Drawing...", flush=True)
            if not mock:
                stop_blink = threading.Event()
                blink_thread = threading.Thread(
                    target=blink_led,
                    args=(gpio, led, stop_blink, LED_BLINK_INTERVAL),
                    daemon=True,
                )
                blink_thread.start()
            try:
                display_fetched_image(inky_display)
            except Exception as e:
                print(f"Error while updating display: {e}", flush=True)
                draw_error_message(inky_display, str(e))
            if not mock:
                stop_blink.set()
                blink_thread.join()
                gpio.set_value(led, Value.INACTIVE)
            print(f"Waiting {DISPLAY_WAIT_TIME}s...", flush=True)
            time.sleep(DISPLAY_WAIT_TIME)
    except KeyboardInterrupt:
        print("Stopped.", flush=True)
    finally:
        if not mock:
            gpio.set_value(led, Value.INACTIVE)


def setup_inky_led():
    led_pin = 13

    print("Setting up LED GPIO...", flush=True)
    try:
        # Find the gpiochip device we need, we'll use
        # gpiodevice for this, since it knows the right device
        # for its supported platforms.
        chip = gpiodevice.find_chip_by_platform()
        # Setup for the LED pin
        led = chip.line_offset_from_id(led_pin)
        gpio = chip.request_lines(
            consumer="inky",
            config={
                led: gpiod.LineSettings(direction=Direction.OUTPUT, bias=Bias.DISABLED)
            },
        )
        return False, gpio, led
    except Exception as e:
        print(f"Not on Raspberry Pi or failed to setup LED GPIO: {e}", flush=True)
        return True, None, None


def display_fetched_image(inky_display):
    url = build_image_url(IMAGE_URL, inky_display.width, inky_display.height)
    print(f"Fetching image from {url}...", flush=True)
    image = fetch_image(url, IMAGE_TOKEN, inky_display.width, inky_display.height)
    display_image(inky_display, image)


def build_image_url(base_url: str, width: int, height: int) -> str:
    path, _, query = base_url.partition("?")
    query = query.replace("?", "&")  # tolerate accidental extra '?' separators
    pairs = [p for p in query.split("&") if p and not p.startswith("viewport=")]
    pairs.append(f"viewport={width}x{height}")
    return f"{path}?{'&'.join(pairs)}"


def fetch_image(url: str, token: str, width: int, height: int) -> Image.Image:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    start_time = time.monotonic()
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    print(f"Fetched image in {time.monotonic() - start_time:.2f}s", flush=True)
    image = Image.open(io.BytesIO(response.content))
    if image.size != (width, height):
        image = image.resize((width, height))
    return image


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

    display_image(inky_display, image)


def draw_error_message(inky_display, message):
    print("Rendering error message to display...", flush=True)
    image = Image.new(
        "P", (inky_display.width, inky_display.height), inky_display.WHITE
    )
    draw = ImageDraw.Draw(image)

    title_font = ImageFont.truetype(FredokaOne, 36)
    body_font = ImageFont.truetype(FredokaOne, 20)

    padding = 20
    draw.text((padding, padding), "Error", inky_display.RED, title_font)

    wrapped = textwrap.wrap(message, width=60)
    y = padding + 50
    for line in wrapped:
        draw.text((padding, y), line, inky_display.BLACK, body_font)
        y += 26

    display_image(inky_display, image)


def display_image(inky_display, image):
    inky_display.set_image(image, saturation=DISPLAY_SATURATION)
    print(f"Updating display (saturation = {DISPLAY_SATURATION})...", flush=True)
    start_time = time.monotonic()
    inky_display.show()
    duration = time.monotonic() - start_time
    print(f"Displayed in {duration:.2f}s", flush=True)


def get_centre_point_for_text(inky_display, text, font):
    _, _, w, h = font.getbbox(text)
    x = (inky_display.width / 2) - (w / 2)
    y = (inky_display.height / 2) - (h / 2)
    return (x, y)


if __name__ == "__main__":
    main()
