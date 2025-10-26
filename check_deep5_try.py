import csv
from playwright.sync_api import sync_playwright

# Skip these buttons (login/signup etc.)
SKIP_TEXTS = ["Login", "Sign Up", "Register", "Next", "Continue", "🔓 Continue with Google"]

# Keywords for special handling
CAR_KEYWORDS = ["Cars", "Carz", "Motors", "Bazar"]
IMPORTANT_KEYWORDS = ["Apply", "Buy", "Enquiry", "Contact", "Submit"]

REPORT_FILE = "nxcar_fullsite_report.csv"


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

        try:
            el.scroll_into_view_if_needed()
            el.click(timeout=3000)
        except Exception:
            try:
                page.evaluate("(el) => el.click()", el)
            except Exception as e2:
                return text, f"Click failed (JS fallback too): {e2}", False

        page.wait_for_timeout(1500)

        # If URL changed (navigation), wait and go back
        if page.url != home_url:
            page.wait_for_timeout(2000)
            page.goto(home_url)
            page.wait_for_load_state("networkidle")

        return text, "Clicked successfully", True
    except Exception as e:
        return text, f"Click failed: {e}", False


def scroll_and_test(page, home_url, step=600, skip_nav_footer=False):
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
        if skip_nav_footer and text in NAV_FOOTER_TEXTS:
            continue  # Skip nav/footer when testing inner pages

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


def save_results(results, mode="w"):
    with open(REPORT_FILE, mode, newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if mode == "w":  # fresh file
            writer.writerow(["#", "Scope", "Element Text", "Status", "Clickable"])
        for i, row in enumerate(results, start=1):
            writer.writerow([i] + row)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(no_viewport=True)
    page = context.new_page()

    home_url = "https://www.nxcar.in/used-car-dealer/dream--cars-1490"
    page.goto(home_url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    results_all = []

    try:
        # First, test Home (Nav + Footer + Main)
        results_home = scroll_and_test(page, home_url)
        results_all.extend([["HOME", t, s, ok] for t, s, ok in results_home])
        save_results(results_all, "w")  # save immediately

        # Collect nav + footer texts (to skip later)
        NAV_FOOTER_TEXTS = [r[0] for r in results_home]

        # Now test each Nav/Footer element by visiting its page
        for t, s, ok in results_home:
            if not ok or t in SKIP_TEXTS:
                continue
            if "skipped" in s.lower():
                continue

            print(f"\n➡️ Navigating via '{t}'...")
            el = page.query_selector(f"text={t}")
            if not el:
                continue
            try:
                el.click(timeout=3000)
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)

                # Test inner page (skip nav/footer)
                sub_results = scroll_and_test(page, home_url, skip_nav_footer=True)
                results_all.extend([["PAGE:" + t, tt, ss, okk] for tt, ss, okk in sub_results])
                save_results(results_all, "a")

                page.goto(home_url)
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)
            except Exception as e:
                results_all.append(["PAGE:" + t, t, f"Nav click failed: {e}", False])
                save_results(results_all, "a")

    except KeyboardInterrupt:
        print("⚠️ Stopped by user, saving partial report...")
        save_results(results_all, "a")

    browser.close()
    print(f"✅ Full/Partial Report saved as {REPORT_FILE}")
