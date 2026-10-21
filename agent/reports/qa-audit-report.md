# DemoBank QA Audit Report

Generated: 2026-10-20T22:38:44
Target: `http://localhost:5173`
PRD: `C:\Users\sjpsr\Agentic-QA-Hackathon-kit\test-website\PRD.md`

Summary: **3 passed**, **2 failed**, **0 unverified**

## Requirement results

| ID | Verdict | Requirement | Evidence |
|---|---|---|---|
| DASH-001 | **PASSED** | The dashboard shows checking and savings accounts with readable balances. | `evidence/01-dashboard.png` |
| TRANSFER-VALID-001 | **PASSED** | A valid transfer decreases the source balance, increases the destination balance, and records the memo. | `evidence/05-valid-transfer.png` |
| TRANSFER-NEG-001 | **FAILED** | Negative transfer amounts must be rejected and must not create a completed transfer. | `evidence/02-negative-transfer.png` |
| FILTER-DATE-001 | **FAILED** | The selected end date is inclusive when filtering transaction history. | `evidence/03-end-date-filter.png` |
| AUTH-LOGOUT-001 | **PASSED** | Logging out returns to the landing page and blocks direct dashboard access. | `evidence/04-logout-protection.png` |

## Details

### DASH-001: PASSED

**Requirement:** The dashboard shows checking and savings accounts with readable balances.
**Expected:** Both accounts are visible and balances use two decimal places.
**Observed:** Dashboard loaded with both seeded accounts and two-decimal balances.

**Reproduction steps:**
1. Open the landing page
2. Click Enter Demo
3. Refresh the dashboard

**Evidence:** evidence/01-dashboard.png

### TRANSFER-VALID-001: PASSED

**Requirement:** A valid transfer decreases the source balance, increases the destination balance, and records the memo.
**Expected:** The source decreases by $25.00, the destination increases by $25.00, and the memo appears in the receipt.
**Observed:** Both balances changed by the expected amount and the memo was visible.

**Reproduction steps:**
1. Open Transfer
2. Record the two current balances
3. Transfer $25.00 from the default source to destination
4. Add the memo QA valid transfer
5. Submit and verify the receipt

**Evidence:** evidence/05-valid-transfer.png

### TRANSFER-NEG-001: FAILED

**Requirement:** Negative transfer amounts must be rejected and must not create a completed transfer.
**Expected:** A clear validation or failure message appears and no success state is shown.
**Observed:** The negative amount was accepted or produced a success state.

**Reproduction steps:**
1. Open Transfer
2. Keep the default source and destination accounts
3. Enter -10 as the amount
4. Submit the transfer

**Evidence:** evidence/02-negative-transfer.png

### FILTER-DATE-001: FAILED

**Requirement:** The selected end date is inclusive when filtering transaction history.
**Expected:** A transaction occurring on 2025-09-03 appears when the end date is 2025-09-03.
**Observed:** The transaction on the selected end date was not visible in the filtered results.

**Reproduction steps:**
1. Open Transactions
2. Set the end date to 2025-09-03
3. Apply filters

**Evidence:** evidence/03-end-date-filter.png

### AUTH-LOGOUT-001: PASSED

**Requirement:** Logging out returns to the landing page and blocks direct dashboard access.
**Expected:** A logged-out user cannot use the protected dashboard route.
**Observed:** Direct dashboard navigation was blocked after logout.

**Reproduction steps:**
1. Click Log out
2. Navigate directly to /dashboard

**Evidence:** evidence/04-logout-protection.png

## Cost estimate

This baseline run uses local Playwright browser automation and does not call a paid model API. Estimated API cost: **$0.00**.