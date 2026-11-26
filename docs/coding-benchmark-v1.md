# NEXUS Coding Benchmark V1 (experimental screening)

The successful baseline job [18407504207](https://gitlab.com/nexus-open-source/nexus-agent-evaluation-oss/-/jobs/18407504207) at dba3f65 verified CUDA, 4,755,397,016 GPU-resident bytes, 317 generated tokens in 28.045 s, and 8 valid test cases covering distinct, duplicate and empty. End-to-end job duration 5m10s. This is one task, not a Codex comparison.

## Candidates and limits

| Model | Registry size | Manifest check |
| --- | --- | --- |
| qwen2.5-coder:7b | 4.7 GB | exact observed manifest |
| qwen2.5-coder:14b | 9.0 GB | 9ec8897f747e prefix |
| qwen3.5:9b-q4_K_M | 6.6 GB | 56671c2ab938 prefix |
| mimo-v2.6:9b-q4_K_M | 6.6 GB | cc58eacf0e3e prefix |

Catalog: https://ollama.com/library/qwen2.5-coder:14b ; https://ollama.com/library/qwen3.5:9b-q4_K_M ; https://ollama.com/library/mimo-v2.6:9b-q4_K_M . The sizes are download sizes, not guaranteed VRAM requirements. Full digests recorded at runtime; three candidates use published prefixes pending observed full digests. The 7B baseline retains exact digest. All run on the same pinned CUDA image and verified Ollama release with fixed context 4096, temperature 0, seed 42, max 768 output tokens, and thinking disabled on thinking models. One trial each; no statistical confidence claims.

## Run

Only on experimental branch, manual web pipeline, select run_gpu_smoke=compare. Four independent GPU jobs, each limited to 20 minutes; worst case 80 raw runner minutes before any applicable billing multiplier. Do not run if compute budget/eligibility is uncertain. No paid Duo credits, no schedule, no automatic retries. Each job uses an isolated disposable runner, no execution of generated code, no tools, stripped unprivileged environment. Each report contains task results, GPU memory and timing, not raw responses. Failed qualification exits nonzero while artifacts are retained when available. A failed infrastructure job is not a valid score. Review all four reports; do not rank incomplete or CPU-only runs as equivalent. Qualification requires at least 4/5 tasks, both critical tasks passing, and positive GPU memory for all tasks. Compare exact scores first, then timing and memory. A single run does not establish stable performance.

Tasks: unit-test design (validated independently), comprehension using the checked-in evaluator on synthetic cases, multiple-choice regression repair, structured fixture design, and simulated permission adherence. This is **not** actual patch generation, repository editing or tool-use evaluation. The next phase is a sandboxed patch proposal benchmark with independent tests, then OpenCode integration only after model selection. No changes to main, no automatic merges, no financial or private-project use.

CPU preflight compiles the benchmark and executes its deterministic self-tests plus existing tests. It cannot verify GPU compatibility or model performance.

## V1 observed results and V1.1 correction (26 November 2026)

Pipeline [3120214077](https://gitlab.com/nexus-open-source/nexus-agent-evaluation-oss/-/pipelines/3120214077), commit 15e8090: four uploaded JSON reports reviewed. CUDA passed for every job; 7B qualified with 4/5, 14B answered all four completed tasks correctly, Qwen3.5 answered 3/4, MiMo 2/4 with a failed critical bug-repair task. The three non-baseline models timed out on the first task at 150.1 seconds. No raw responses were retained, so incorrect-answer details cannot be reconstructed. A timeout is incomplete, not an observed incorrect answer. No definitive winner. Job IDs 18407939671–18407939674 in the above model order. V1.1 pins all four full observed model digests, uses a separate unscored GPU warmup (240s maximum, same context), retains the 150s per-task cap, all five original scored prompts and 20-minute job cap, and explicitly distinguishes correct, incorrect and incomplete outcomes. A report with incomplete tasks cannot qualify. The first run cannot establish which model is best. Run the same four models once more only after CPU preflight succeeds and compute budget is confirmed. Do not retry the obsolete V1 jobs. The comparison remains screening, not actual coding agent evaluation. No auto merge or execution of model-produced code.

## V1.1 completed screening and provisional selection

Source: all four user-exported GitLab artifacts, each containing cuda-driver-report.json and coding-benchmark-report.json (schema 2, benchmark 1.1). All four report one CUDA device, positive GPU-resident bytes on every task, complete=true, and no incomplete tasks. All five original prompts were scored. These are uploaded reports, not an independent live retrieval of GitLab.

| Model | Passed | Critical failures | Qualified | GPU bytes | Benchmark wall seconds incl. warmup | Job |
| --- | ---: | --- | --- | ---: | ---: | --- |
| Qwen2.5-Coder 14B | 5/5 | none | yes | 9480584559 | 181.760 | [18408460203](https://gitlab.com/nexus-open-source/nexus-agent-evaluation-oss/-/jobs/18408460203) |
| Qwen2.5-Coder 7B | 4/5 | none | yes | 4755397016 | 157.573 | [18408460202](https://gitlab.com/nexus-open-source/nexus-agent-evaluation-oss/-/jobs/18408460202) |
| Qwen3.5 9B Q4_K_M | 3/5 | none | no | 5606337412 | 175.127 | [18408460204](https://gitlab.com/nexus-open-source/nexus-agent-evaluation-oss/-/jobs/18408460204) |
| MiMo V2.6 9B Q4_K_M | 2/5 | bug_repair | no | 5606337412 | 181.226 | [18408460205](https://gitlab.com/nexus-open-source/nexus-agent-evaluation-oss/-/jobs/18408460205) |

The 14B model is the provisional primary candidate; 7B remains a lower-memory fallback. Both passed the critical simulated checks. Selection is scoped to this small structured-response screening under the tested configuration. No proof of general coding performance, secure tool use, or equivalence to Codex. No inference reruns are needed at this stage. Next: design a bounded patch-proposal benchmark on synthetic regressions, assess patches with independent tests in a disposable no-credential environment, and only then evaluate an OpenCode configuration. Keep manual opt-in, no paid services, no main modifications or automatic merge. OpenCode is not installed or validated by this screening.
