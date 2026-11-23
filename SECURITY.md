# Security policy

This is an educational, standalone Python evaluator. It does **not** execute agent actions, grant permissions, validate evidence authenticity, or provide runtime isolation.

## Supported scope

The current 0.2.x prototype is maintained on a best-effort basis. Its input validation and report generation are testable, but it is **not certified for security-critical or financial decisions**.

## Reporting a potential vulnerability

Please do not post credentials, private agent outputs, unpublished exploit details, or private infrastructure information in public issues.

If GitHub's **Report a vulnerability** / private vulnerability reporting option is enabled for this repository, use it. Otherwise, open a public issue with only a high-level description (no exploit details) and request a private disclosure channel before sending sensitive material.

Useful information includes the affected version or commit, platform and Python version, minimal *synthetic* reproduction, expected versus actual behavior, and a suggested mitigation if known.

Security reports and fixes are considered case by case; no response SLA is promised.

## Responsible use

Do not equate a passing evaluator report with permission to execute actions, independently validated safety, or approval to run a real-world multi-agent system.
