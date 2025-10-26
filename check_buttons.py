from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Launch browser maximized
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    # Open website
    page.goto("https://www.nxcar.in/")
    print("Page Title:", page.title())
    
    # Find all buttons and links
    elements = page.query_selector_all("button, a")
    print(f"Found {len(elements)} buttons/links on the page.")
    
    for i, el in enumerate(elements, start=1):
        try:
            text = el.inner_text().strip()
            if text == "":
                text = "<no text>"
            
            # Check if element is visible and enabled (clickable)
            if el.is_visible() and el.is_enabled():
                print(f"[{i}] Element '{text}' is visible and clickable.")
            else:
                print(f"[{i}] Element '{text}' is NOT clickable or not visible.")
            
        except Exception as e:
            print(f"[{i}] Element '{text}' could NOT be tested. Error: {e}")
    
    # Take a full-page screenshot of the main page
    page.screenshot(path="buttons_test_safe_final.png", full_page=True)
    print("Screenshot saved as buttons_test_safe_final.png")
    
    browser.close()
