from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # headless=False opens the browser visibly
    page = browser.new_page()
    page.goto("https://parshantyadav.com/")
    print("Page Title:", page.title())
    browser.close()
