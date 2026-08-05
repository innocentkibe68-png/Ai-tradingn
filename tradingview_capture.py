 import os
import time
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

TRADINGVIEW_URL = (
    "https://www.tradingview.com/chart/"
    "?symbol=FX_IDC%3AEURUSD&interval=15"
)

OUTPUT_DIR = Path("evidence")
OUTPUT_FILE = OUTPUT_DIR / "eurusd_tradingview.png"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def is_blank(path: Path, min_std: float = 20.0, min_bytes: int = 15_000) -> bool:
    """True if the screenshot looks blank or failed to render."""
    size = os.path.getsize(path)
    if size < min_bytes:
        logger.warning(f"File too small ({size} bytes).")
        return True
    try:
        from PIL import Image
        import numpy as np
        img = np.array(Image.open(path).convert("L"))
        std = float(img.std())
        logger.info(f"Pixel std: {std:.2f}")
        return std < min_std
    except Exception as e:
        logger.warning(f"PIL validation unavailable ({e}); relying on file size only.")
        return False


def capture_tradingview(max_retries: int = 3):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, max_retries + 1):
        logger.info(f"Capture attempt {attempt}/{max_retries}...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )
                context = browser.new_context(
                    viewport={"width": 1600, "height": 1000},
                    user_agent=USER_AGENT,   # don't announce ourselves as a bot
                )
                page = context.new_page()

                page.goto(
                    TRADINGVIEW_URL,
                    wait_until="domcontentloaded",
                    timeout=60_000,
                )

                # Generic canvas wait — no fragile class names
                try:
                    page.wait_for_selector("canvas", timeout=20_000)
                    logger.info("Canvas element present.")
                except Exception:
                    logger.warning("No canvas within 20s; continuing with fixed render wait.")

                # Render buffer for candles to physically paint
                page.wait_for_timeout(12_000)

                logger.info(f"Page title: {page.title()}")

                page.screenshot(path=str(OUTPUT_FILE), full_page=False)
                browser.close()

            if is_blank(OUTPUT_FILE):
                logger.warning("Screenshot looks blank. Retrying...")
                time.sleep(3)
                continue

            logger.info("Capture validated: chart content present.")
            return

        except Exception as e:
            logger.error(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise RuntimeError(
                    f"Failed to capture TradingView after {max_retries} attempts."
                )
            time.sleep(3)

    raise RuntimeError("All captures were blank or failed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    capture_tradingview()