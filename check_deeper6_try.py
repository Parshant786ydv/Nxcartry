import csv
from playwright.sync_api import sync_playwright

# === CONFIG ===
HOME_URL = "https://www.nxcar.in/"
NAV_CLASS = "._right_6uxq0_86"
FOOTER_CLASS = "._footer_3nw8j_11"

SKIP_TEXTS = ["Login", "Sign Up", "Register", "Continue", "🔓 Continue with Google"]
SKIP_KEYWORDS = ["Pune", "Delhi", "Mumbai", "Hyderabad", "Bangalore", "Chennai", "Kolkata", "Maharashtra"]
CAR_KEYWORDS = ["Car", "Cars", "Carz", "Motors"]

REPORT_FILE = "nxcar_site_report.csv"

# === HELPERS ===
def get_clickable_texts(page, scope="BODY"):
    """Extract unique clickable elements but skip NAV + FOOTER unless explicitly checking them"""
    selectors = ["a", "button", "[role='button']", "[onclick]"]
    texts, seen = [], set()

    if scope == "BODY":
        page.evaluate(f"""
            document.querySelectorAll("{NAV_CLASS}, {FOOTER_CLASS}").forEach(el => el.remove());
        """)

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
    """Click an element safely without crashing"""
    try:
        if text in SKIP_TEXTS or any(k in text for k in SKIP_KEYWORDS):
            return text, "Skipped", True

        el = page.query_selector(f"text={text}")
        if not el or not el.is_visible():
            return text, "Not found/visible", False

        el.scroll_into_view_if_needed()
        old_url = page.url
        el.click(timeout=3000)
        page.wait_for_timeout(1500)

        if page.url != old_url:
            page.wait_for_load_state("networkidle")
            return text, "Working (navigated)", True
        else:
            return text, "Working (same page)", True

    except Exception as e:
        return text, f"Not Working ({e})", False


def check_page(page, scope, skip_texts=set(), car_checked=False, body_only=True):
    """Check links/buttons on a page"""
    results = []
    texts = get_clickable_texts(page, scope="BODY" if body_only else scope)

    for text in texts:
        if text in skip_texts:
            continue

        if any(k in text for k in CAR_KEYWORDS):
            if car_checked:
                continue
            car_checked = True

        t, status, ok = safe_click(page, text)
        print(f"[{scope}] {t} → {status}")
        results.append([scope, t, status])
        skip_texts.add(text)

        if "navigated" in status and page.url != HOME_URL:
            page.go_back()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1500)

    return results, skip_texts, car_checked


# === MAIN ===
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    page.goto(HOME_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    results = []
    skip_texts = set()
    car_checked = False

    try:
        # Step 1: Check NAV & FOOTER separately once
        print("\n🔎 Checking NAV links...")
        nav_texts = get_clickable_texts(page, scope="NAV")
        for nav in nav_texts:
            if nav not in SKIP_TEXTS:
                t, status, ok = safe_click(page, nav)
                results.append(["NAV", t, status])
                if "navigated" in status:
                    r, skip_texts, car_checked = check_page(page, f"PAGE:{nav}", skip_texts, car_checked, body_only=True)
                    results.extend(r)
                    page.go_back()
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(1500)

        print("\n🔎 Checking FOOTER links...")
        footer_texts = get_clickable_texts(page, scope="FOOTER")
        for ft in footer_texts:
            if ft not in SKIP_TEXTS:
                t, status, ok = safe_click(page, ft)
                results.append(["FOOTER", t, status])
                if "navigated" in status:
                    r, skip_texts, car_checked = check_page(page, f"PAGE:{ft}", skip_texts, car_checked, body_only=True)
                    results.extend(r)
                    page.go_back()
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(1500)

        # Step 2: Check BODY (excluding nav/footer)
        print("\n🔎 Checking BODY elements...")
        r, skip_texts, car_checked = check_page(page, "BODY", skip_texts, car_checked, body_only=True)
        results.extend(r)

    except KeyboardInterrupt:
        print("⚠️ Stopped midway, saving partial report...")

    # Save final CSV
    with open(REPORT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Scope", "Element", "Status"])
        writer.writerows(results)

    browser.close()
    print(f"\n✅ Report saved as {REPORT_FILE}")
