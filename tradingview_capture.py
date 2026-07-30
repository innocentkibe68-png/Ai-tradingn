from pathlib import Path

from playwright.sync_api import sync_playwright


TRADINGVIEW_URL = (
    "https://www.tradingview.com/chart/"
    "?symbol=FX_IDC%3AEURUSD&interval=15"
)

OUTPUT_DIR = Path("evidence")
OUTPUT_FILE = OUTPUT_DIR / "eurusd_tradingview.png"


def capture_tradingview():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            viewport={
                "width": 1600,
                "height": 1000,
            }
        )

        print("Opening TradingView...")
        page.goto(
            TRADINGVIEW_URL,
            wait_until="domcontentloaded",
            timeout=60_000,
        )

        # Give the chart time to render.
        page.wait_for_timeout(15_000)

        page.screenshot(
            path=str(OUTPUT_FILE),
            full_page=False,
        )

        print(f"TradingView screenshot saved to: {OUTPUT_FILE}")

        browser.close()


if __name__ == "__main__":
    capture_tradingview()