# GPU model baseline (experimental only)

This branch replaces the earlier OpenCode smoke prototype with a deliberately
bounded first-stage inference benchmark. The prior prototype is preserved in
commit b485c525cc03c527d056bacab77e0585edfc3101. It ran model-generated Python
in the CI process; the replacement never executes model-generated source,
invokes model-selected tools, or grants repository credentials to the model.
It asks the local model for JSON test cases and independently checks their
expected results and coverage against the checked-in evaluator.

Run manually on GitLab only on experiment/gpu-capability-probe, with
input run_gpu_smoke=yes. Do not enable scheduled/mirror-triggered pipelines for
this experiment. No paid Duo services; public OSS project only. Do not run if
the account's compute eligibility or budget has changed.

The image is pinned to Ollama 0.40.18 (version checked at runtime); the model
digest prefix is checked and its full digest recorded. The image manifest is pinned to the digest observed in GitLab job 18406584956; OS package versions are not fully locked. The pipeline is capped at 20 min,
model download at 480 s and inference at 360 s. It reports GPU-resident model
bytes, basic generation metrics, case count, coverage and pass/fail. Model
responses are not published. The runner is disposable; the model server and
benchmark run with a stripped environment and unprivileged account.

This is a test-design baseline, not an autonomous coding agent or a comparison
with Codex. A passing result is necessary but not sufficient to proceed to
OpenCode with a reviewed tool policy, filesystem isolation, no credentials,
bounded execution and independent validation. Review the report and job logs
before extending scope. No claim of successful GPU inference until a real run.

## CPU preflight

GitHub Actions runs a CPU-only preflight on pushes to the experiment branch:
Python compilation, the benchmark's six self-test scenarios and the existing
unit tests. It downloads no model and does not call GitLab or any AI service.
Inspect this run before manually launching the GPU benchmark. The GitLab
manual pipeline form now offers the typed input run_gpu_smoke with a safe default of no;
choose yes explicitly for the one bounded run. A preflight success is not
proof of GPU inference or agent coding quality.

Pipeline input is declared in the main file's spec:inputs header; pipeline-level variable entry is not required. The run guard remains manual web-only on this experiment branch.

## First GPU run and corrective change

GitLab job 18406584956 (commit 10bce0c8) pulled the Ollama image and installed Python, then failed at the optional nvidia-smi diagnostic (exit 127). No model was downloaded or evaluated. The diagnostic is now optional; device and driver library visibility is logged, and the Ollama /api/ps size_vram check is still mandatory. A CPU-only run fails. The observed image manifest is pinned. This is a proposed fix pending a new bounded run, not a confirmed inference result.
