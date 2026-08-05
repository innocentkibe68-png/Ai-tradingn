import os
import logging
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

TRADINGVIEW_URL = "https://www.tradingview.com/chart/?symbol=FX_IDC:EURUSD&interval=15"
OUTPUT_DIR = Path("evidence")
OUTPUT_FILE = OUTPUT_DIR / "eurusd_tradingview.png"


def capture_tradingview(max_retries: int = 2):
    """
    Captures a TradingView chart with retry logic and sanity checks 
    to prevent blank or loading-screen screenshots.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, max_retries + 1):
        logger.info(f"Attempting TradingView capture (Attempt {attempt}/{max_retries})...")
        try:
            with sync_playwright() as p:
                # Added --no-sandbox and --disable-web-security for GitHub Actions stability
                browser = p.chromium.launch(
                    headless=True, 
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-web-security"]
                )
                page = browser.new_page(viewport={"width": 1600, "height": 1000})
                
                logger.info("Navigating to TradingView...")
                # domcontentloaded is faster and more reliable than networkidle for TradingView
                page.goto(TRADINGVIEW_URL, wait_until="domcontentloaded", timeout=60_000)
                
                # 1. Wait for the actual chart canvas to exist in the DOM
                page.wait_for_selector("canvas.chart-canvas", timeout=30_000)
                
                # 2. Fixed buffer for candles and indicators to physically render on the canvas
                logger.info("Chart DOM loaded. Waiting 8s for visual render...")
                page.wait_for_timeout(8_000) 
                
                # 3. Capture
                page.screenshot(path=str(OUTPUT_FILE), full_page=False)
                browser.close()
            
            # 4. Sanity Check: File Size
            # A real 1600x1000 chart with candles/grid is almost always > 40KB. 
            # A blank white screen or loading spinner is usually < 15KB.
            file_size = os.path.getsize(OUTPUT_FILE)
            if file_size < 15_000:
                logger.warning(f"Screenshot too small ({file_size} bytes), likely blank. Retrying...")
                time.sleep(3)
                continue 
            
            logger.info(f"✅ Successfully captured TradingView chart ({file_size} bytes)")
            return  # Success! Exit the function.
            
        except Exception as e:
            logger.error(f"Capture attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise RuntimeError(f"Failed to capture TradingView after {max_retries} attempts.")
            time.sleep(3)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    capture_tradingview()
