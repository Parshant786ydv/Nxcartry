import csv
from playwright.sync_api import sync_playwright

def get_clickable_elements(page):
    # Candidate selectors for clickable elements
    selectors = [
        "button",
        "a",
        "[role='button']",
        "[onclick]",
        "div:has-text('Login')",
        "span:has-text('Login')"
    ]
    elements = []
    for sel in selectors:
        elements.extend(page.query_selector_all(sel))
    
    # Remove duplicates
    return list(dict.fromkeys(elements))

def check_element(el):
    # Assign text first to avoid NameError
    try:
        text = el.inner_text().strip()
    except:
        text = "<no text>"
    
    # Skip elements not visible at all
    if not el.is_visible():
        return text, "Not visible", False
    
    # Try scroll into view
    try:
        el.scroll_into_view_if_needed(timeout=2000)
    except:
        return text, "Could not scroll (maybe hidden/modal/iframe)", False
    
    # Check if enabled
    if el.is_enabled():
        return text, "Clickable", True
    else:
        return text, "Visible but not clickable", False

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    
    page.goto("https://www.nxcar.in/")
    print("Page Title:", page.title())
    
    # Wait SPA content to load
    page.wait_for_timeout(4000)
    
    elements = get_clickable_elements(page)
    print(f"Found {len(elements)} candidate clickable elements.")
    
    results = []
    for i, el in enumerate(elements, start=1):
        text, status, clickable = check_element(el)
        print(f"[{i}] '{text}': {status}")
        results.append([i, text, status, clickable])
    
    # Save results to CSV
    with open("nxcar_clickable_report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Element Text", "Status", "Clickable"])
        writer.writerows(results)
    print("CSV report saved as nxcar_clickable_report.csv")
    
    # Take full-page screenshot
    page.screenshot(path="nxcar_clickable_full.png", full_page=True)
    print("Screenshot saved as nxcar_clickable_full.png")
    
    browser.close()