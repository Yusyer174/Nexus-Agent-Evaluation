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

## Second GPU run and diagnostic-only mode

Job 18406865347 at c1ba291b downloaded and verified Qwen2.5-Coder 7B (4.7 GB), generated 395 tokens, and uploaded a report with gpu_bytes=0. NVIDIA device nodes were present, but the ldconfig diagnostic printed no matching driver libraries. Model quality was not assessed. This is an infrastructure failure, not a benchmark pass. The next manually authorized run uses the CUDA base image recommended in https://docs.gitlab.com/ci/runners/hosted_runners/gpu_enabled/ and checks libcuda.so.1, cuInit and cuDeviceGetCount as an unprivileged user, without loading any model. Select run_gpu_smoke=diagnostics. The old model job is now hidden and yes is no longer accepted. This supersedes the earlier launch instructions until the CUDA diagnostic is reviewed. No scheduled runs or paid services. The CUDA image uses the documented version tag; its manifest digest is not independently verified yet. A passing device probe does not establish successful model inference.

## Third run passed; integrated CUDA model benchmark

Job 18407264267 at 581b743 completed in 29 seconds: Tesla T4, 15360 MiB, driver 580.178.04; cuInit=0, cuDeviceGetCount=0, device_count=1, passed=true under nobody. The CUDA image is now pinned to the manifest observed in that job. The model job is re-enabled with input yes, while diagnostics remains a separate optional driver-only job. Both are manual-only; no scheduled jobs. The new model job uses the validated CUDA base and explicitly preserves the same driver library search path under its stripped unprivileged environment. It checks CUDA before downloading any model. Ollama 0.40.18 is downloaded as the official versioned Linux amd64 release archive and SHA-256 verified against the digest from the GitHub releases API before extraction as nobody. The model manifest digest is now checked in full against the observed second-run digest. The checked-in evaluator and independent JSON oracle remain unchanged. The model benchmark has not yet run in this environment; binary compatibility and GPU inference remain unverified. No model output is executed. This supersedes the diagnostic-only instructions above.
