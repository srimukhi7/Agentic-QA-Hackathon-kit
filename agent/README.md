# DemoBank Agentic QA Agent

This agent reads the DemoBank PRD, drives the running browser application with Playwright, checks high-value requirements, captures screenshots, and creates a requirement-level Markdown audit report.

## Run

```powershell
python main.py --url http://localhost:5173 --prd ..\test-website\PRD.md --headed
```

Outputs are written to:

- `reports/qa-audit-report.md`
- `reports/results.json`
- `evidence/*.png`

The current baseline uses local browser automation and does not require a paid model API. It is intentionally small and transparent so each verdict can be reproduced.

## Known limitations

- The first version targets the supplied DemoBank interface.
- It checks a focused set of high-value scenarios rather than every PRD sentence.
- Some checks may be marked unverified if the target is unavailable or the UI changes.
- It does not test performance, infrastructure, real payments, or denial-of-service behavior.
