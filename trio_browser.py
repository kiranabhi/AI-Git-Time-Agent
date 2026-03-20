import os
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

load_dotenv()

TRIO_URL      = os.getenv("TRIO_URL")
TRIO_USERNAME = os.getenv("TRIO_USERNAME")
TRIO_PASSWORD = os.getenv("TRIO_PASSWORD")
_headless_raw = os.getenv("TRIO_HEADLESS", "false").strip().lower()
HEADLESS      = os.getenv("TRIO_HEADLESS", "true").lower() == "true"

# ── Validate all required env vars are set ────────────────────────────
_required = {
    "TRIO_URL":      TRIO_URL,
    "TRIO_USERNAME": TRIO_USERNAME,
    "TRIO_PASSWORD": TRIO_PASSWORD,
}
_missing = [k for k, v in _required.items() if not v]
if _missing:
    raise EnvironmentError(
        f"❌ Missing required environment variables: {', '.join(_missing)}\n"
        f"   Check your .env file and make sure these are set."
    )

def log_time_to_trio(date: str, hours: float, summary: str):
    """
    Automates Trio timesheet entry using Playwright.
    - Selects the correct day on the calendar
    - Clicks edit on Krasan Consulting project
    - Fills in hours and summary
    - Saves the entry
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()

        try:
            # ── Step 1: Navigate to login page first ─────────────────
            print(f"🌐 Navigating to {TRIO_URL}...")
            page.goto(TRIO_URL)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)  # Extra wait for Angular to render

            # ── Check if we were redirected to login ──────────────────
            # If already on the timesheet page, skip login
            if "login" in page.url.lower() or page.locator('input[type="password"]').count() > 0:
                print("🔐 Login page detected, signing in...")

                # Email — first text input on the page
                page.wait_for_selector('input.form-control', timeout=10000)
                inputs = page.locator('input.form-control')

                # Fill email (first input) and password (type=password input)
                inputs.first.fill(TRIO_USERNAME)

                # Password — target directly by type=password, more reliable than nth-of-type
                page.fill('input[type="password"]', TRIO_PASSWORD)

                page.click('button[type="submit"]')
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)  # Wait for Angular to redirect after login
                print("✅ Logged in")
            else:
                print("✅ Already authenticated, skipping login")

            # ── Navigate to daily time page after login ───────────────
            if "/dailytime" not in page.url.lower():
                page.goto(f"{TRIO_URL}")
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)


            # ── Step 2: Select correct month and year ─────────────────
            target_date  = datetime.strptime(date, "%Y-%m-%d")
            target_day   = target_date.day        # e.g. 19
            target_month = target_date.month      # e.g. 3  (1-based)
            target_year  = str(target_date.year)  # e.g. "2026"

            print(f"📅 Selecting date: {date}")

            # Month select — option values are "0: 1" through "11: 12"
            # Find the option whose value ends with the target month number
            page.select_option(
                'select[name="month"]',
                value=next(
                    f"{i}: {target_month}"
                    for i in range(12)
                    if i == target_month - 1
                )
            )

            # Year select — option values are "0: 2013", "1: 2014", etc.
            page.select_option('select[name="year"]', label=target_year)
            page.wait_for_load_state("networkidle")

            # ── Step 3: Click the correct day on the calendar ─────────
            # ID is 0-indexed: day_0=1st, day_18=19th, day_19=20th
            day_index = target_day - 1
            print(f"📅 Clicking day {target_day} → #day_{day_index}")
            page.click(f'#day_{day_index} div.text-center')  # Click the inner div directly
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)
            print(f"✅ Selected day {target_day}")


            # ── Step 4: Find the Krasan Consulting entry form ─────────
            # Use has_text for partial match — "Krasan Consulting" starts the full project name
            print("🔍 Locating Krasan Consulting project row...")
            krasan_row = page.locator(
                'div.bg-ff-pale-green',
                has_text='Krasan Consulting'   # Partial match — matches any text containing this
            ).first

            krasan_row.wait_for(state="visible", timeout=10000)

            # ── Step 5: Fill in hours ─────────────────────────────────
            hours_input = krasan_row.locator('app-hours-input input')
            hours_input.wait_for(state="visible", timeout=10000)
            hours_input.click(click_count=3)   # Select all existing text
            hours_input.fill(str(hours))
            print(f"✅ Entered hours: {hours}")

            # ── Step 6: Fill in summary/comment ──────────────────────
            comment_box = krasan_row.locator('textarea')
            comment_box.wait_for(state="visible", timeout=10000)
            comment_box.click(click_count=3)   # Select all existing text
            comment_box.fill(summary)
            print(f"✅ Entered summary: {summary[:60]}...")

            # ── Step 7: Trigger onblur to auto-save ───────────────────
            # Trio auto-saves on blur — click outside the form to trigger it
            comment_box.press("Tab")                          # Tab out of textarea
            page.wait_for_timeout(500)
            hours_input.press("Tab")                          # Tab out of hours too
            page.wait_for_timeout(500)
            page.click('h3')                                  # Click the page header to blur
            page.wait_for_timeout(2000)                       # Wait for auto-save to complete
            print("✅ Entry auto-saved via blur")

            # ── Step 8: Screenshot confirmation ──────────────────────
            os.makedirs("./logs", exist_ok=True)
            screenshot_path = f"./logs/trio_confirmation_{date}.png"
            page.screenshot(path=screenshot_path)
            print(f"📸 Screenshot saved → {screenshot_path}")

        except PlaywrightTimeout as e:
            print(f"❌ Playwright timeout: {e}")
            page.screenshot(path="./logs/trio_error.png")
            raise
        except Exception as e:
            print(f"❌ Error during Trio automation: {e}")
            page.screenshot(path="./logs/trio_error.png")
            raise
        finally:
            browser.close()
