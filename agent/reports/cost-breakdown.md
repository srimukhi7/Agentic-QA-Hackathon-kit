# DemoBank QA Agent Cost Breakdown

## Demonstrated run

| Component | Usage | Estimated cost |
|---|---:|---:|
| PRD ingestion | 1 local file read containing 36 bullet requirements | $0.00 |
| Browser execution | 5 Playwright checks using local Chromium | $0.00 |
| Screenshots and evidence | 5 local PNG screenshots | $0.00 |
| Audit report generation | Local Python Markdown and JSON generation | $0.00 |
| External model/API calls | None in the demonstrated run | $0.00 |
| **Total estimated run cost** |  | **$0.00** |

## Notes

The demonstrated agent run uses local Playwright browser automation and local Python report generation. It does not send the synthetic DemoBank data, screenshots, or PRD contents to a paid external model API. Therefore, the measured API and token cost for the demonstrated run is $0.00.

The implementation is intentionally transparent and reproducible. A future version could add an optional language model for broader requirement decomposition and adaptive scenario planning; that would be priced separately based on the selected model and token usage.
