from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


@dataclass
class Result:
    requirement_id: str
    requirement: str
    verdict: str
    expected: str
    observed: str
    evidence: list[str]
    reproduction: list[str]


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"
REPORTS = ROOT / "reports"


def read_requirements(prd_path: Path) -> list[str]:
    text = prd_path.read_text(encoding="utf-8")
    requirements: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("-") and len(line) > 3:
            requirements.append(line[1:].strip())
    return requirements


def visible_text(page: Page) -> str:
    return re.sub(r"\s+", " ", page.locator("body").inner_text()).strip()


def screenshot(page: Page, name: str) -> str:
    path = EVIDENCE / f"{name}.png"
    # Playwright is more reliable on Windows when given a forward-slash path.
    page.screenshot(path=path.as_posix(), full_page=True)
    return str(path.relative_to(ROOT)).replace("\\", "/")


def test_session_and_dashboard(page: Page) -> Result:
    evidence: list[str] = []
    reproduction = ["Open the landing page", "Click Enter Demo", "Refresh the dashboard"]
    try:
        page.goto(page.url or "http://localhost:5173", wait_until="networkidle")
        page.get_by_role("button", name="Enter Demo").click()
        page.get_by_role("heading", name=re.compile("Welcome", re.I)).wait_for()
        evidence.append(screenshot(page, "01-dashboard"))
        text = visible_text(page)
        has_accounts = "Everyday Checking" in text and "Rainy Day Savings" in text
        has_balances = bool(re.search(r"\$[\d,]+\.\d{2}", text))
        verdict = "passed" if has_accounts and has_balances else "failed"
        observed = "Dashboard loaded with both seeded accounts and two-decimal balances." if verdict == "passed" else "Dashboard did not show both expected accounts and balances."
        return Result(
            "DASH-001",
            "The dashboard shows checking and savings accounts with readable balances.",
            verdict,
            "Both accounts are visible and balances use two decimal places.",
            observed,
            evidence,
            reproduction,
        )
    except Exception as exc:
        return Result("DASH-001", "The dashboard shows checking and savings accounts with readable balances.", "unverified", "Dashboard loads with both accounts.", f"The browser test could not complete: {exc}", evidence, reproduction)


def test_invalid_transfer(page: Page) -> Result:
    evidence: list[str] = []
    reproduction = [
        "Open Transfer",
        "Keep the default source and destination accounts",
        "Enter -10 as the amount",
        "Submit the transfer",
    ]
    try:
        page.get_by_role("link", name="Transfer", exact=True).click()
        page.get_by_label("Amount (USD)").fill("-10")
        page.get_by_role("button", name="Transfer funds").click()
        page.wait_for_timeout(700)
        evidence.append(screenshot(page, "02-negative-transfer"))
        text = visible_text(page)
        rejected = bool(re.search(r"must|invalid|positive|greater|not completed|error", text, re.I)) and "Transfer complete" not in text
        verdict = "passed" if rejected else "failed"
        observed = "The negative amount was rejected without a success state." if rejected else "The negative amount was accepted or produced a success state."
        return Result(
            "TRANSFER-NEG-001",
            "Negative transfer amounts must be rejected and must not create a completed transfer.",
            verdict,
            "A clear validation or failure message appears and no success state is shown.",
            observed,
            evidence,
            reproduction,
        )
    except PlaywrightTimeoutError as exc:
        return Result("TRANSFER-NEG-001", "Negative transfer amounts must be rejected and must not create a completed transfer.", "unverified", "Negative amount is rejected.", f"The expected control was not available: {exc}", evidence, reproduction)
    except Exception as exc:
        return Result("TRANSFER-NEG-001", "Negative transfer amounts must be rejected and must not create a completed transfer.", "unverified", "Negative amount is rejected.", f"The browser test could not complete: {exc}", evidence, reproduction)


def money_value(value: str) -> Decimal:
    cleaned = value.replace("$", "").replace(",", "").strip()
    return Decimal(cleaned)


def test_valid_transfer(page: Page) -> Result:
    evidence: list[str] = []
    reproduction = [
        "Open Transfer",
        "Record the two current balances",
        "Transfer $25.00 from the default source to destination",
        "Add the memo QA valid transfer",
        "Submit and verify the receipt",
    ]
    try:
        page.get_by_role("link", name="Transfer", exact=True).click()
        page.locator('[data-testid="transfer-balance"]').first.wait_for()
        before = [money_value(value) for value in page.locator('[data-testid="transfer-balance"]').all_inner_texts()]
        source_id = page.locator("#source").input_value()
        destination_id = page.locator("#destination").input_value()
        source_values = page.locator("#source option").evaluate_all("options => options.map(option => option.value)")
        destination_values = page.locator("#destination option").evaluate_all("options => options.map(option => option.value)")
        source_index = source_values.index(source_id) - 1
        destination_index = destination_values.index(destination_id) - 1
        page.get_by_label("Amount (USD)").fill("25.00")
        page.get_by_label(re.compile("Memo", re.I)).fill("QA valid transfer")
        page.get_by_role("button", name="Transfer funds").click()
        page.get_by_text("Transfer complete", exact=True).wait_for()
        after = [money_value(value) for value in page.locator('[data-testid="transfer-balance"]').all_inner_texts()]
        source_changed = after[source_index] == before[source_index] - Decimal("25.00")
        destination_changed = after[destination_index] == before[destination_index] + Decimal("25.00")
        memo_visible = "QA valid transfer" in visible_text(page)
        evidence.append(screenshot(page, "05-valid-transfer"))
        passed = source_changed and destination_changed and memo_visible
        return Result(
            "TRANSFER-VALID-001",
            "A valid transfer decreases the source balance, increases the destination balance, and records the memo.",
            "passed" if passed else "failed",
            "The source decreases by $25.00, the destination increases by $25.00, and the memo appears in the receipt.",
            "Both balances changed by the expected amount and the memo was visible." if passed else "The transfer receipt or one of the expected balance changes was missing.",
            evidence,
            reproduction,
        )
    except Exception as exc:
        return Result("TRANSFER-VALID-001", "A valid transfer decreases the source balance, increases the destination balance, and records the memo.", "unverified", "The valid transfer is atomic and recorded.", f"The browser test could not complete: {exc}", evidence, reproduction)


def test_end_date_filter(page: Page) -> Result:
    evidence: list[str] = []
    reproduction = [
        "Open Transactions",
        "Set the end date to 2025-09-03",
        "Apply filters",
    ]
    try:
        page.get_by_role("link", name="Transactions", exact=True).click()
        page.get_by_label("End date").fill("2025-09-03")
        page.get_by_role("button", name="Apply filters").click()
        page.wait_for_timeout(700)
        evidence.append(screenshot(page, "03-end-date-filter"))
        text = visible_text(page)
        included = "Returned demo deposit" in text or "09/03/2025" in text or "09/03/25" in text
        verdict = "passed" if included else "failed"
        observed = "The transaction on the selected end date was included." if included else "The transaction on the selected end date was not visible in the filtered results."
        return Result(
            "FILTER-DATE-001",
            "The selected end date is inclusive when filtering transaction history.",
            verdict,
            "A transaction occurring on 2025-09-03 appears when the end date is 2025-09-03.",
            observed,
            evidence,
            reproduction,
        )
    except Exception as exc:
        return Result("FILTER-DATE-001", "The selected end date is inclusive when filtering transaction history.", "unverified", "The end date is inclusive.", f"The browser test could not complete: {exc}", evidence, reproduction)


def test_logout(page: Page) -> Result:
    evidence: list[str] = []
    reproduction = ["Click Log out", "Navigate directly to /dashboard"]
    try:
        page.get_by_role("button", name="Log out").click()
        page.get_by_role("button", name="Enter Demo").wait_for()
        page.goto(page.url.rstrip("/") + "/dashboard", wait_until="networkidle")
        blocked = page.get_by_role("button", name="Enter Demo").is_visible()
        evidence.append(screenshot(page, "04-logout-protection"))
        return Result(
            "AUTH-LOGOUT-001",
            "Logging out returns to the landing page and blocks direct dashboard access.",
            "passed" if blocked else "failed",
            "A logged-out user cannot use the protected dashboard route.",
            "Direct dashboard navigation was blocked after logout." if blocked else "The protected dashboard remained accessible after logout.",
            evidence,
            reproduction,
        )
    except Exception as exc:
        return Result("AUTH-LOGOUT-001", "Logging out returns to the landing page and blocks direct dashboard access.", "unverified", "Protected dashboard access is blocked.", f"The browser test could not complete: {exc}", evidence, reproduction)


def write_report(results: list[Result], prd_path: Path, target_url: str) -> Path:
    passed = sum(result.verdict == "passed" for result in results)
    failed = sum(result.verdict == "failed" for result in results)
    unverified = sum(result.verdict == "unverified" for result in results)
    lines = [
        "# DemoBank QA Audit Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Target: `{target_url}`",
        f"PRD: `{prd_path}`",
        "",
        f"Summary: **{passed} passed**, **{failed} failed**, **{unverified} unverified**",
        "",
        "## Requirement results",
        "",
        "| ID | Verdict | Requirement | Evidence |",
        "|---|---|---|---|",
    ]
    for result in results:
        evidence = ", ".join(f"`{item}`" for item in result.evidence) or "None"
        lines.append(f"| {result.requirement_id} | **{result.verdict.upper()}** | {result.requirement} | {evidence} |")
    lines.extend(["", "## Details", ""])
    for result in results:
        lines.extend(
            [
                f"### {result.requirement_id}: {result.verdict.upper()}",
                "",
                f"**Requirement:** {result.requirement}",
                f"**Expected:** {result.expected}",
                f"**Observed:** {result.observed}",
                "",
                "**Reproduction steps:**",
                *[f"{index}. {step}" for index, step in enumerate(result.reproduction, start=1)],
                "",
                f"**Evidence:** {', '.join(result.evidence) if result.evidence else 'None'}",
                "",
            ]
        )
    lines.extend(
        [
            "## Cost estimate",
            "",
            "This baseline run uses local Playwright browser automation and does not call a paid model API. Estimated API cost: **$0.00**.",
        ]
    )
    report_path = REPORTS / "qa-audit-report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    (REPORTS / "results.json").write_text(json.dumps([asdict(result) for result in results], indent=2), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DemoBank specification-driven QA checks.")
    parser.add_argument("--url", default="http://localhost:5173")
    parser.add_argument("--prd", default=str(ROOT.parent / "test-website" / "PRD.md"))
    parser.add_argument("--headed", action="store_true", help="Show the browser while tests run.")
    args = parser.parse_args()

    EVIDENCE.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    prd_path = Path(args.prd).resolve()
    requirements = read_requirements(prd_path)
    print(f"Read {len(requirements)} bullet requirements from {prd_path.name}.")

    results: list[Result] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not args.headed)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(args.url, wait_until="networkidle")
        results.append(test_session_and_dashboard(page))
        results.append(test_valid_transfer(page))
        results.append(test_invalid_transfer(page))
        results.append(test_end_date_filter(page))
        results.append(test_logout(page))
        browser.close()

    report_path = write_report(results, prd_path, args.url)
    print(f"Completed {len(results)} checks.")
    for result in results:
        print(f"{result.verdict.upper():10} {result.requirement_id}: {result.observed}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
