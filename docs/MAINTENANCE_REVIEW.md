# NEXUS maintenance review

Reviewed 2026-11-23 against [main at 62a5c10](https://github.com/Yusyer174/Nexus-Agent-Evaluation/commit/62a5c10f02ef75148baf8c0ae6000f9f40032656). The downloaded archive matched all 26 tracked files. The original 26 unit tests passed on Windows with Python 3.13.18. The highest-value work is protecting input files and making the composite action evaluate literal caller-supplied paths.

Follow-up on 2026-11-23: [PR 12](https://github.com/Yusyer174/Nexus-Agent-Evaluation/pull/12) was reviewed and squash-merged as [8907a72](https://github.com/Yusyer174/Nexus-Agent-Evaluation/commit/8907a72a963163a82a49f7eb4b1ff47c8ce1390b), after all ten hosted jobs passed. The sections below retain the original audit evidence. The final section records the subsequent packaging work and refreshed collaboration research.

## Prioritized audit

| Problem | Current evidence | Severity | Developer impact | Improvement | Verification |
| --- | --- | --- | --- | --- | --- |
| Report output can overwrite a hard-linked input | In [evaluator.py](../evaluator.py), `Path.resolve()` compares names. A temporary hard link to predictions returned exit 0 and replaced the input with a report. | High, data loss defect | A CI report can destroy its fixture. | Compare existing file identity as well as resolved paths. | Hard links to either input exit 2; both names retain original bytes; unrelated reports remain writable. |
| Action filenames can become CLI options | [action.yml](../action.yml) passes positional inputs before options. A cases value of `--help` returned 0 with no report in the equivalent CLI invocation. | High, integration defect | A successful Action step need not mean an evaluation occurred. | Put options first, bind their values with `=`, then use `--` before filenames. | Actual composite action accepts dash-prefixed filenames, rejects nonexistent `--help`, and writes reports for accepted and rejected evaluations. |
| Action portability and path assumptions lack coverage | [Action smoke CI](../.github/workflows/action-smoke.yml) covered Linux and simple paths; [CLI portability CI](../.github/workflows/cross-platform.yml) already covers three OSes. Shell variables are quoted correctly. | Medium, verification gap | Consumers cannot infer Action behavior from CLI-only tests. | Run the actual composite action on all three OSes, from an action directory containing spaces, with caller filenames containing spaces and shell characters. Explicitly use the caller workspace. | Passing smoke matrix; critical failure still rejects with threshold 0. |
| Main and version 0.2.0 identify different behavior | [Metadata](../pyproject.toml) remains 0.2.0 after several merged changes; [changelog](../CHANGELOG.md) already separates unreleased work. GitHub releases list was empty. | Medium, release readiness | A version alone cannot identify the exact implementation. | Use commit pins now; prepare a reviewed 0.2.1 release plan below. | Built artifacts install outside the source tree; release approval precedes publication. |
| Build metadata uses a deprecated license table | The baseline wheel/sdist build succeeds, but setuptools warns that the table form should migrate before 2027-02-18. The sdist includes tests without their example fixtures. | Medium, release readiness | Future builds may fail, and unpacked sdist tests cannot reproduce the checkout. | In the separate packaging task, adopt SPDX metadata with an appropriate backend floor and include test fixtures or exclude incomplete tests. Keep the MIT terms unchanged. | No license deprecation warning; sdist tests and clean installation pass. |
| Persistent assistant guidance is missing | No Copilot instructions in the live tree. | Medium, maintenance gap | Future changes may confuse declared outputs with runtime enforcement. | Add concise [Copilot instructions](../.github/copilot-instructions.md). | Commands match existing entry points; require regression tests and unchanged critical gates. |
| Some validation branches lack explicit tests | Duplicate case JSON keys already reject, but [issue 9](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/9) requests its regression. The roadmap's general portability task partly duplicates existing CI. | Low, contributor opportunity | A small contribution can protect existing behavior. | Retain issue 9; make later tasks precise and avoid duplicate issues. | New tests fail on the intended regression and pass on Python 3.10–3.13. |

The implementation scope is the two demonstrated defects, their integration coverage, and persistent contributor guidance. The remaining entries are follow-up work, not claims that features have shipped.

## Local verification

- Windows, Python 3.13.18: all 28 unit tests pass. The new hard-link regression failed against the original implementation before the fix.
- Accepted synthetic CLI example exits 0; the critical rejection exits 1 at both default and zero thresholds. Saved JSON matches stdout in each run.
- The actual Action run block passes locally under a POSIX shell for spaces, shell characters and dash-prefixed names, and exits 2 for a missing file named `--help`. GitHub's smoke matrix verifies the composite runner and Bash on all three OSes.
- Wheel and sdist builds succeed. Wheel metadata declares Python 3.10+, zero runtime dependencies, the console entry point and the unchanged MIT license; the wheel contains the current evaluator source.
- The fresh Windows console launcher was blocked by Application Control (WinError 4551). The installed module is checked separately outside the checkout; this does not establish that the blocked launcher works on this machine.
- Internal documentation targets and local Markdown anchors pass the link check. The complete diff and added files were reviewed; a credential-pattern scan is an additional check, not proof that arbitrary content is safe to publish.

Hosted checks for the implementation at [bda7355](https://github.com/Yusyer174/Nexus-Agent-Evaluation/commit/bda7355b024a22aa07a75e5bf8e911f6a870ebdf) all passed: [Python 3.10–3.13 tests and installed command](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/runs/45180266452), [three-platform composite action](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/runs/45180266621), and [three-platform CLI](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/runs/45180266625). Review the latest PR checks before merging. Passing checks concern declared-output evaluation, not agent runtime safety.

## Validation and integration findings

The evaluator rejects duplicate case IDs, duplicate JSON object keys, invalid case fields and prediction IDs. Malformed or missing predictions fail their case; duplicate actions and evidence IDs fail through the shared list validator. A boolean is required for `critical`; numbers and strings are rejected. The threshold range check rejects NaN and infinities. Critical failures and unexpected prediction IDs close the gate even at threshold zero. Case results retain input order; unexpected IDs, missing evidence and forbidden actions are sorted. The two path and argument defects above do not require changing these semantics.

The input parser currently accepts Python JSON extensions such as NaN in ignored metadata. Strict RFC JSON parsing would be a separate compatibility decision. Large or deeply nested inputs have no explicit resource limit. A file identity check prevents accidental aliases; it does not provide protection against a concurrent process replacing paths during evaluation.

All three existing workflows request only `contents: read`; none use `pull_request_target` or auto-merge. The caller must provide Python 3.10+ and Bash for the composite action. It runs the bundled source and installs no runtime dependencies. The consumer example pins a historical commit and uploads reports with `if: always()`, so a valid rejection can still be inspected. An invalid invocation need not produce a report. Existing reports should be removed before a new run if reused paths could leave stale artifacts.

Main's [unit CI](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/runs/45150433748), [Action CI](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/runs/45150433772) and [CLI portability CI](https://github.com/Yusyer174/Nexus-Agent-Evaluation/actions/runs/45150433703) passed. These links describe the audited baseline; PR checks provide evidence for changed code.

Open PRs [5](https://github.com/Yusyer174/Nexus-Agent-Evaluation/pull/5) and [6](https://github.com/Yusyer174/Nexus-Agent-Evaluation/pull/6) update setup-python and checkout in the unit workflow. This work leaves those updates to their existing reviews. Open issues [8](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/8) and [9](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/9) already cover independent feedback and a beginner test. No replacement issues are needed.

The quickstart already includes synthetic positive and negative cases, expected exits, a trial guide and an integration contract. The project has no runtime dependencies, but building/installing requires build tooling. A first-time user must install Python separately. Cross-platform interpreter names and checking exit status deserve a short clarification in the trial guide. No obsolete source files were identified.

## Positioning and useful upstream patterns

| Reference | Useful pattern | Overlap and boundary |
| --- | --- | --- |
| [FastAPI quickstart](https://github.com/fastapi/fastapi#example) | Runnable input, command and observable output together; installation prerequisites and linked deeper documentation. | A web framework is a developer-experience reference, not an evaluator competitor. NEXUS should retain its smaller walkthrough rather than copy branding or maturity claims. |
| [Promptfoo deterministic metrics](https://github.com/promptfoo/promptfoo/blob/main/site/docs/configuration/expected-outputs/deterministic.md) | Explicit assertion semantics, model/provider integrations, and CI documentation. | Deterministic checks are not unique to NEXUS. Promptfoo already supports equality, JSON validation, custom Python and tool/trajectory assertions, alongside model evaluation. Prefer it when provider orchestration, red teaming or richer assertions are needed. |
| [Strands Evals](https://github.com/strands-agents/evals) | Separate output and trace evaluators, testable examples, serialization guidance and a contributor process. | Its trajectory, tool and experiment support is broader. NEXUS's declared action membership cannot evaluate tool arguments, ordering, execution or multi-turn outcomes. |
| [OpenAgent Eval](https://github.com/OpenAgentHQ/openagent-eval#try-it-in-60-seconds--no-api-key-needed) | An offline mock quickstart, CLI validation, contributor setup and report options. | Offline operation is not unique either. Its retrieval/generation metrics and pipeline analysis are better suited to RAG evaluation. |

NEXUS can serve a small Python project that already exports decisions and needs exact strings, action-set membership, required evidence IDs and an explicit critical-case gate without installing an evaluation framework. Its useful tradeoff is the small standard-library implementation and narrow contract. Plain unittest assertions may be simpler for a single bespoke check. A green report proves only that the supplied declarations match the supplied cases.

## Release and compatibility plan

1. Keep the package version unchanged in this maintenance PR. Pin installations and Action references to a reviewed immutable commit until a release is approved.
2. Prepare a separate 0.2.1 candidate covering the unreleased fixes and integrations, with a dated changelog and explicit compatibility notes. Successful evaluations retain their report keys and gate semantics; accidental input aliases now error, and Action filenames become literal arguments.
3. Build wheel and sdist, inspect license and metadata, install from the sdist/wheel in clean environments outside the repository, and run both examples through the installed command on supported Python versions. Confirm a fresh checkout's documented commands.
4. Have the owner review the candidate, decide whether a prerelease is appropriate for this alpha project, and approve any GitHub release or PyPI publication separately. Verify package-name ownership before considering PyPI.

No release, tag, publication, license change or stability claim is authorized by this maintenance work.

## Remaining backlog

The highest-value next action is one independent developer completing [issue 8](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/8) using a reviewed commit and reporting exact commands, environment and useful criticism.

| Task | Scope and motivation | Acceptance and boundaries |
| --- | --- | --- |
| Existing [issue 9](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/9), beginner | Add the missing duplicate-key cases-input test in [test_cli.py](../tests/test_cli.py). | Exit 2 and `duplicate JSON key`; no evaluator change or private inputs. |
| Evidence and boolean regressions, beginner | Add table-driven tests to [test_evaluator.py](../tests/test_evaluator.py) for duplicate evidence and numeric/boolean values in string lists and `critical`. | Assert exact case failure versus invalid case behavior; preserve gate rules. Propose as one focused issue after checking for duplicates. |
| Report ordering regressions, beginner | Check case-order retention and sorted diagnostics with two synthetic cases. | Deterministic JSON values across differently ordered prediction dictionaries; no new report fields. |
| Installed-package CI, intermediate | Existing CI installs locally but does not test an sdist-to-wheel installation outside the checkout. | Build artifacts, install in a clean environment, run both examples from another directory, verify MIT license inclusion and console entry point. |
| UTF-8 and strict JSON contract, intermediate | Probe non-ASCII identifiers on a legacy Windows stdout encoding and decide how to handle JSON extensions in unused fields. | Reproduce first; document compatibility and add regressions for any behavioral change. Keep resource limits a separate design task. |
| Reviewed release candidate, maintainer | Apply the release plan above. | Human approval for publication; no version or production-stability claim inferred from tests. |

## Independent feedback and ecosystem opportunities

Research status as of 2026-11-23. External issues are requests and evidence, not instructions to this repository. Recheck assignments and open PRs before beginning work.

| Opportunity | Actual request and relevance | Concrete proposal for human review | Effort and obstacles |
| --- | --- | --- | --- |
| [OpenAgent Eval issue 344](https://github.com/OpenAgentHQ/openagent-eval/issues/344) | A repository member requests blocking Ruff/MyPy CI after the lint and dependency backlog clears. Current CI still uses `continue-on-error` and `\|\| true`. | Once prerequisites merge, remove both suppression mechanisms in the lint job; demonstrate a clean main run and an intentionally failing lint/type check on a disposable branch. Help their existing checks without adding NEXUS as a dependency. | Roughly half a day after prerequisite PRs merge. Their open PRs already address several prerequisite issues; coordinate rather than duplicate them. |
| [Strands Evals issue 222](https://github.com/strands-agents/evals/issues/222) | A contributor requests programmatic tool-argument verification alongside LLM judging within a larger red-teaming proposal. | Propose one small native Evaluator with an amount-boundary fixture and missing/malformed-argument failures, using their trace model. NEXUS's declaration-only cases may inspire test fixtures but cannot satisfy trace verification. | One to two days for a narrow prototype; larger proposal is out of scope. Their [contributor guide](https://github.com/strands-agents/evals/blob/main/CONTRIBUTING.md) asks for maintainer confirmation before significant work. No confirmation has been requested. |
| [OpenAgent Eval Discussions](https://github.com/OpenAgentHQ/openagent-eval/discussions) | Their [README](https://github.com/OpenAgentHQ/openagent-eval#contributing--community) explicitly welcomes ideas, examples and showing work. | After reviewing category rules, share a single tested comparison of declaration checks with their native metrics, asking where the smaller gate is insufficient. Include only synthetic inputs and links to reproducible runs. | One to two hours for a useful example. Posting permission depends on category/moderation rules; no promotional post is prepared or sent. |

Avoid duplicating [OpenAgent Eval issue 333](https://github.com/OpenAgentHQ/openagent-eval/issues/333), already covered by [PR 385](https://github.com/OpenAgentHQ/openagent-eval/pull/385), and [Strands issue 640](https://github.com/strands-agents/evals/issues/640), where another contributor has volunteered.

For NEXUS, first use the existing trial issue and feedback form. Ask a willing developer for a five-minute synthetic run, then address the first reproducible friction they report. Attempt a downstream integration only when someone has a real need; include a failing fixture and a pinned commit. Keep each status distinct: invitation sent, response received, tool actually tested, external contribution merged, downstream integration independently verified. This session sends no invitations or third-party messages and establishes none of those adoption outcomes.

## Public account presentation

The [profile README](https://github.com/Yusyer174/Yusyer174) already states the author's student status, links both public projects and distinguishes declaration checks from runtime safety. It links the housing project's reproducible baseline and model card rather than claiming classification accuracy. The [housing README](https://github.com/Yusyer174/house-prices-prediction-portfolio) links its historical CI results; this maintenance review does not rerun or independently validate that model.

The evaluator currently has no repository topics and a broad description, “Open-source evaluation framework for AI agents.” Recommended owner settings:

- Description: “Dependency-free Python CLI and GitHub Action for deterministic checks of declared agent decisions, actions and evidence IDs.”
- Topics: `python`, `ai-agents`, `evaluation`, `testing`, `github-actions`, `deterministic`.
- Pin NEXUS Agent Evaluation first, then the housing baseline. Retain the profile's clear learning/research context.
- Keep the existing trial and contributor links current after releases. Avoid adding adoption claims until independently supported.

These are separate owner tasks; no profile repository, account setting, topics, visibility or pins were changed.

## Packaging follow-up

The old sdist reproduced the fixture defect: all 28 tests errored after extraction because the examples were absent. Artifact regressions also failed on missing documentation and the wheel's absent `License-Expression`. The follow-up uses an explicit [source manifest](../MANIFEST.in), SPDX MIT metadata and setuptools 77.0.3+. This follows the [PyPA metadata guidance](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) and [setuptools source-file guidance](https://setuptools.pypa.io/en/latest/userguide/miscellaneous.html); the MIT license text and Python 3.10 requirement remain unchanged.

The [distribution checker](../tests/check_distribution.py) checks real artifacts, runs the unpacked source suite, and installs both sdist and wheel into fresh virtual environments before invoking the console command from a separate directory. Its [CI workflow](../.github/workflows/package.yml) covers the minimum backend on Python 3.10, and isolated builds on Python 3.13 across Linux, Windows and macOS. These checks replace the baseline's missing installed-artifact coverage. They do not publish packages or releases.

Locally, the checkout's 28 tests and the three artifact checks for contents, metadata and unpacked tests pass for both the current backend and setuptools 77.0.3. Both builds succeed without the former license-table deprecation. The full local installation check fails during virtual-environment preparation; a separate import confirms Windows Application Control blocks `pyexpat`. This environment limitation is not suppressed or skipped in the checker. Review the hosted installation results before merging the follow-up. The documented version remains 0.2.0 until a separately approved release decision.

## Collaboration follow-up

The existing public feedback invitation [issue 8](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/8) and beginner task [issue 9](https://github.com/Yusyer174/Nexus-Agent-Evaluation/issues/9) remain open with zero comments. Searches for `involves:Yusyer174` in the public OpenAgent Eval, Strands Evals and Promptfoo repositories returned no matching issues or PRs. This scoped search does not establish whether messages were sent through other channels. No new invitation, reply, independent test, merged external contribution or verified downstream integration is claimed here.

Two technical proposals are ready for human review, without posting them:

1. **OpenAgent Eval [issue 344](https://github.com/OpenAgentHQ/openagent-eval/issues/344), blocking lint checks.** The issue remains open without an assignee or comments. Prerequisite work is already in open PRs [372](https://github.com/OpenAgentHQ/openagent-eval/pull/372), [373](https://github.com/OpenAgentHQ/openagent-eval/pull/373), [374](https://github.com/OpenAgentHQ/openagent-eval/pull/374), [382](https://github.com/OpenAgentHQ/openagent-eval/pull/382) and [383](https://github.com/OpenAgentHQ/openagent-eval/pull/383); do not duplicate it. Draft proposal: “After the prerequisite fixes merge, I can prepare a focused change removing both failure-suppression mechanisms from the Ruff and MyPy steps. Validation would include a green clean checkout plus disposable changes containing one lint violation and one type error, each causing CI to fail. I would leave integration-test policy and evaluation behavior outside this PR.” Estimate: half a day once prerequisites are ready. Maintainer coordination and a new check for competing PRs are still needed.

2. **Promptfoo [issue 12525](https://github.com/promptfoo/promptfoo/issues/12525), corrupted CSV fixtures.** The report requests an explicit error or warning for invalid UTF-8. The reporter has already offered an implementation; the issue has no comments or assignee. Current [CSV loading code](https://github.com/promptfoo/promptfoo/blob/a7eee9df7f4da0b4a92b3ea147f12832a866f138/src/util/testCaseReader.ts#L344) still reads UTF-8 directly. Draft proposal: “I can independently review the proposed CSV decoding fix with byte-level fixtures for UTF-8, UTF-8 BOM, cp1252, cp949 and truncated multibyte sequences. I would check that valid input is preserved and invalid input is reported before an echo-provider evaluation can pass. This can be a focused regression-test review of your PR, without duplicating your implementation or adding another evaluation dependency.” Estimate: one to two hours after a candidate PR exists. The reported runtime bug has not been independently executed in this session, and no maintainer acceptance is assumed.

The newly checked Promptfoo [issue 12513](https://github.com/promptfoo/promptfoo/issues/12513) is already claimed in its comments; avoid a competing implementation. The earlier Strands [issue 222](https://github.com/strands-agents/evals/issues/222) remains a possible larger native-evaluator proposal, subject to maintainer confirmation. None of these opportunities justifies promotional posts or presenting NEXUS as runtime enforcement.
