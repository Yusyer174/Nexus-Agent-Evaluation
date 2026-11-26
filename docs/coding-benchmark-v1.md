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
