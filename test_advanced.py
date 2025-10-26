from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Launch browser fully visible and maximized
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    
    # Create a page with full HD viewport
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    # Open your website
    page.goto("https://parshantyadav.com/")
    
    # Print the page title
    print("Page Title:", page.title())
    
    # Example: click a link or menu if exists (adjust the selector if needed)
    try:
        page.click("text=About")  # clicks the link with text 'About'
        print("Clicked 'About' link")
    except:
        print("'About' link not found, skipping click")
    
    # Take a full-page screenshot
    page.screenshot(path="website_screenshot.png", full_page=True)
    print("Screenshot saved as website_screenshot.png")
    
    # Close the browser
    browser.close()
