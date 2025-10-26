from playwright.sync_api import sync_playwright

def find_clickable_elements(page):
    # All elements that are naturally clickable or have onclick
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
    elements = list(dict.fromkeys(elements))
    
    return elements

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    
    page.goto("https://www.nxcar.in/")
    print("Page Title:", page.title())
    
    # Wait for SPA content to render
    page.wait_for_timeout(3000)  # wait 3 seconds
    
    elements = find_clickable_elements(page)
    print(f"Found {len(elements)} clickable elements on the page.")
    
    for i, el in enumerate(elements, start=1):
        try:
            # Scroll into view
            el.scroll_into_view_if_needed()
            page.wait_for_timeout(200)  # short wait for rendering
            
            text = el.inner_text().strip()
            if text == "":
                text = "<no text>"

            if el.is_visible() and el.is_enabled():
                print(f"[{i}] '{text}' is visible and clickable.")
            else:
                print(f"[{i}] '{text}' is NOT clickable or not visible.")
        
        except Exception as e:
            print(f"[{i}] '{text}' could NOT be tested. Error: {e}")
    
    # Screenshot at the endd
    page.screenshot(path="nxcar_clickable_test.png", full_page=True)
    print("Screenshot saved as nxcar_clickable_test.png")
    
    browser.close()
