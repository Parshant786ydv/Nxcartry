import csv
from playwright.sync_api import sync_playwright

# Texts to skip
SKIP_TEXTS = ["Login", "Sign Up", "Register", "Next", "Continue"]

# Keywords
CAR_KEYWORDS = ["Cars", "Carz", "Motors", "Bazar"]
IMPORTANT_KEYWORDS = ["Apply", "Buy", "Enquiry", "Contact", "Submit"]

def get_clickable_texts(page):
    selectors = ["button", "a", "[role='button']", "[onclick]"]
    texts, seen = [], set()
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

def safe_click(page, text, home_url):
    try:
        if text in SKIP_TEXTS:
            return text, "Login/Signup skipped", True

        el = page.query_selector(f"text={text}")
        if not el:
            return text, "Not found on re-query", False

        if not el.is_visible():
            return text, "Not visible", False

        # First try normal click
        try:
            el.scroll_into_view_if_needed()
            el.click(timeout=3000)
        except Exception:
            # Fallback: force JS click (useful for footer & overlay issues)
            try:
                page.evaluate("(el) => el.click()", el)
            except Exception as e2:
                return text, f"Click failed (JS fallback too): {e2}", False

        page.wait_for_timeout(1500)

        # If URL changed (navigated), go back to Home
        if page.url != home_url:
            page.wait_for_timeout(2000)  # let it load
            page.goto(home_url)
            page.wait_for_load_state("networkidle")

        return text, "Clicked successfully", True
    except Exception as e:
        return text, f"Click failed: {e}", False

def scroll_and_test(page, home_url, step=600):
    height = page.evaluate("() => document.body.scrollHeight")
    all_texts = []
    results = []

    # Collect clickable texts
    for y in range(0, height + step, step):
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(500)
        all_texts.extend(get_clickable_texts(page))

    # Deduplicate
    unique_texts = list(dict.fromkeys(all_texts))

    dealer_checked = False
    for i, text in enumerate(unique_texts, start=1):
        if any(k in text for k in CAR_KEYWORDS):
            if not dealer_checked:
                dealer_checked = True
                t, status, ok = safe_click(page, text, home_url)
                results.append([t, "Dealer/Car tested once - " + status, ok])
                print(f"[{i}] '{t}': Dealer/Car tested once")
            else:
                results.append([text, "Dealer/Car skipped", True])
                print(f"[{i}] '{text}': Dealer/Car skipped")
            continue

        if any(kw in text for kw in IMPORTANT_KEYWORDS) or len(text.split()) <= 3:
            t, status, ok = safe_click(page, text, home_url)
            results.append([t, status, ok])
            print(f"[{i}] '{t}': {status}")

    return results

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    home_url = "https://www.nxcar.in/"
    page.goto(home_url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    results = scroll_and_test(page, home_url)

    # Save CSV report
    with open("nxcar_clickable_report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "Element Text", "Status", "Clickable"])
        for i, row in enumerate(results, start=1):
            writer.writerow([i] + row)

    print("✅ Report saved as nxcar_clickable_report.csv")
    browser.close()