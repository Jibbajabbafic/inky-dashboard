import asyncio
import io
import os
import threading
import time
from urllib.parse import urlparse

import gpiod
import gpiodevice
from dotenv import load_dotenv
from font_fredoka_one import FredokaOne
from gpiod.line import Bias, Direction, Value
from inky.auto import auto
from inky.mock import InkyMockImpression
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import async_playwright

# Configuration values
load_dotenv()
HA_URL = os.environ.get("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
LED_BLINK_INTERVAL = float(os.environ.get("LED_BLINK_INTERVAL", 0.2))
DISPLAY_SATURATION = float(os.environ.get("DISPLAY_SATURATION", 0.1))
DISPLAY_WAIT_TIME = int(os.environ.get("DISPLAY_WAIT_TIME", 30))


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
            display_ha_dashboard(inky_display)
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


def display_ha_dashboard(inky_display):
    print("Capturing Home Assistant dashboard...", flush=True)
    image = get_ha_screenshot(HA_URL, HA_TOKEN, inky_display.width, inky_display.height)
    display_image(inky_display, image)


async def _capture_ha_screenshot(
    url: str, token: str, width: int, height: int
) -> Image.Image:
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={"width": width, "height": height})
        page = await context.new_page()
        await page.goto(base_url)
        await page.evaluate(
            """([baseUrl, token, expires]) => {
                localStorage.setItem('hassTokens', JSON.stringify({
                    access_token: token,
                    token_type: 'Bearer',
                    expires_in: 3600,
                    hassUrl: baseUrl,
                    clientId: baseUrl + '/',
                    expires: expires,
                    refresh_token: ''
                }));
            }""",
            [base_url, token, int(time.time() * 1000) + 3600000],
        )
        await page.goto(url, wait_until="networkidle", timeout=60000)
        screenshot_bytes = await page.screenshot()
        await browser.close()
    return Image.open(io.BytesIO(screenshot_bytes))


def get_ha_screenshot(url: str, token: str, width: int, height: int) -> Image.Image:
    return asyncio.run(_capture_ha_screenshot(url, token, width, height))


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


def display_image(inky_display, image):
    inky_display.set_image(image, saturation=DISPLAY_SATURATION)
    print("Updating display...", flush=True)
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
