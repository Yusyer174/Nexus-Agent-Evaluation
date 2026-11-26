# GPU model baseline (experimental only)

This branch replaces the earlier OpenCode smoke prototype with a deliberately
bounded first-stage inference benchmark. The prior prototype is preserved in
commit b485c525cc03c527d056bacab77e0585edfc3101. It ran model-generated Python
in the CI process; the replacement never executes model-generated source,
invokes model-selected tools, or grants repository credentials to the model.
It asks the local model for JSON test cases and independently checks their
expected results and coverage against the checked-in evaluator.

Run manually on GitLab only on experiment/gpu-capability-probe, with
NEXUS_RUN_GPU_SMOKE=yes. Do not enable scheduled/mirror-triggered pipelines for
this experiment. No paid Duo services; public OSS project only. Do not run if
the account's compute eligibility or budget has changed.

The image is pinned to Ollama 0.40.18 (version checked at runtime); the model
digest prefix is checked and its full digest recorded. OS package versions and
image manifest digest are not fully locked. The pipeline is capped at 20 min,
model download at 480 s and inference at 360 s. It reports GPU-resident model
bytes, basic generation metrics, case count, coverage and pass/fail. Model
responses are not published. The runner is disposable; the model server and
benchmark run with a stripped environment and unprivileged account.

This is a test-design baseline, not an autonomous coding agent or a comparison
with Codex. A passing result is necessary but not sufficient to proceed to
OpenCode with a reviewed tool policy, filesystem isolation, no credentials,
bounded execution and independent validation. Review the report and job logs
before extending scope. No claim of successful GPU inference until a real run.
