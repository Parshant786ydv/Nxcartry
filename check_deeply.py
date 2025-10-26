import csv
from playwright.sync_api import sync_playwright

# Buttons to skip completely
NAVIGATION_BUTTON_TEXTS = ["Login", "Sign Up", "Register", "Next", "Continue"]

def get_clickable_texts(page):
    """Collect unique texts of clickable elements currently on the screen."""
    selectors = [
        "button",
        "a",
        "[role='button']",
        "[onclick]",
        "div",
        "span"
    ]
    texts = []
    seen = set()
    for sel in selectors:
        for el in page.query_selector_all(sel):
            try:
                text = el.inner_text().strip()
            except:
                text = ""
            if text and text not in seen:
                seen.add(text)
                texts.append(text)
    return texts

def safe_click(page, text):
    """Re-find element by its text and click it freshly each time."""
    try:
        if any(nav in text for nav in NAVIGATION_BUTTON_TEXTS):
            return text, "Navigation button (skipped)", True

        el = page.query_selector(f"text={text}")
        if not el:
            return text, "Not found on re-query", False

        if not el.is_visible():
            return text, "Not visible", False

        el.scroll_into_view_if_needed()
        el.click(timeout=3000)
        page.wait_for_timeout(500)
        return text, "Clicked successfully", True
    except Exception as e:
        return text, f"Click failed: {e}", False

def scroll_and_test(page, step=500):
    """Scroll down the page, gather clickable texts, then test them."""
    height = page.evaluate("() => document.body.scrollHeight")
    all_texts = []
    results = []

    # Step 1: Collect all clickable texts while scrolling
    for y in range(0, height + step, step):
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(800)
        all_texts.extend(get_clickable_texts(page))

    # Deduplicate
    unique_texts = list(dict.fromkeys(all_texts))

    # Step 2: Test all texts, but only 1 car card
    car_clicked = False
    for i, text in enumerate(unique_texts, start=1):
        # Detect car listings (usually contain city names or dealer names)
        if any(city in text for city in ["Delhi", "Pune", "Bangalore", "Mumbai", "Carz", "Cars"]):
            if car_clicked:
                results.append([text, "Car listing skipped (already tested one)", True])
                print(f"[{i}] '{text}': Skipped extra car listing")
                continue
            else:
                car_clicked = True

        t, status, ok = safe_click(page, text)
        results.append([t, status, ok])
        print(f"[{i}] '{t}': {status}")

    return results

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)  # full screen
    page = context.new_page()

    page.goto("https://www.nxcar.in/")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    results = scroll_and_test(page)

    # Save CSV report
    with open("nxcar_clickable_fullsite.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Element Text", "Status", "Clickable"])
        for i, row in enumerate(results, start=1):
            writer.writerow([i] + row)
    print("CSV report saved as nxcar_clickable_fullsite.csv")

    # Full screenshot
    page.screenshot(path="nxcar_clickable_fullsite.png", full_page=True)
    print("Screenshot saved as nxcar_clickable_fullsite.png")

    browser.close()
