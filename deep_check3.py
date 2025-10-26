import csv
from playwright.sync_api import sync_playwright

# Buttons to skip completely
NAVIGATION_BUTTON_TEXTS = ["Login", "Sign Up", "Register", "Next", "Continue"]

def get_car_cards(page):
    """Return first 1–2 car listing elements only."""
    # Cars are usually links or divs with text (custom selector for Nxcar)
    car_cards = page.query_selector_all("a, div:has-text('Delhi'), div:has-text('Pune'), div:has-text('Bangalore')")
    return car_cards[:2]  # take only first 2

def safe_click(page, el):
    """Click element safely if not navigation."""
    try:
        text = el.inner_text().strip() if el else "<no text>"

        if not el or not el.is_visible():
            return text, "Not visible", False

        if any(nav in text for nav in NAVIGATION_BUTTON_TEXTS):
            return text, "Navigation button skipped", True

        el.scroll_into_view_if_needed()
        el.click(timeout=3000)
        page.wait_for_timeout(800)
        return text, "Clicked successfully", True

    except Exception as e:
        return "<no text>", f"Click failed: {e}", False

def scroll_whole_page(page, step=500):
    """Scroll entire page once to load all cars."""
    height = page.evaluate("() => document.body.scrollHeight")
    for y in range(0, height + step, step):
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(500)
    print("Scrolled through full page.")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    # Open website
    page.goto("https://www.nxcar.in/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # Step 1: Scroll page fully (lazy load all cars)
    scroll_whole_page(page)

    # Step 2: Test only 1–2 car cards
    car_cards = get_car_cards(page)
    results = []
    for i, el in enumerate(car_cards, start=1):
        text, status, ok = safe_click(page, el)
        results.append([text, status, ok])
        print(f"[Car {i}] '{text}': {status}")

    # Step 3: Save report
    with open("nxcar_clickable_short.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Element Text", "Status", "Clickable"])
        for i, row in enumerate(results, start=1):
            writer.writerow([i] + row)
    print("CSV report saved as nxcar_clickable_short.csv")

    # Screenshot
    page.screenshot(path="nxcar_clickable_short.png", full_page=True)
    print("Screenshot saved as nxcar_clickable_short.png")

    browser.close()
