# Distribution preparation and publication approval

NEXUS Agent Evaluation remains an unpublished **0.3.0rc1** candidate. This procedure prepares and validates wheel and source archives without uploading them. The evaluator still supports Python 3.10+, uses the MIT license and has no runtime dependencies. A release, tag, TestPyPI upload or PyPI upload needs a separate owner decision.

## Documentation and package metadata

The package description uses [the repository README](../README.md). Its documentation links use absolute GitHub URLs so they work both on GitHub and in PyPI's Markdown renderer. The in-page Action section link remains a fragment. Links to `main` describe current documentation; immutable Git commit references identify reviewed Action behavior and historical evidence.

The README deliberately documents checkout installation while publication is pending. After an approved publication, update that wording and add the exact published install command, including `--pre` or an explicit version for a release candidate. Wheels contain the evaluator and console entry point; source archives also contain synthetic CLI fixtures, tests and Markdown documentation. Use a Git checkout for the complete browser laboratory.

## Controlled build profile

[The pinned requirements](../tools/requirements-build.txt) identify the build frontend, backend and their build dependencies. They are development tools, not evaluator runtime dependencies. The reproducibility workflow uses CPython **3.13.18**. Ordinary installation keeps the backend minimum of setuptools 77.0.3 and the existing Python 3.10–3.13 distribution matrix.

Version pins control the selected versions; they do not cryptographically authenticate downloaded tools. This profile uses the configured package index over HTTPS and checks installed versions, but it is not a hash-locked, offline or hermetic supply chain. For a stricter publication bootstrap, review the exact tool wheels and their SHA-256 hashes and install a complete approved dependency set with `--require-hashes` or an approved offline wheelhouse. Hashes obtained only from the same download channel do not independently authenticate a publisher. See [pip's secure-install guidance](https://pip.pypa.io/en/stable/topics/secure-installs/). No runtime dependency or account configuration is added by this limitation note.

[The build utility](../tools/build_reproducible.py) snapshots the current committed `HEAD` with `git archive`. It refuses tracked local edits, excludes untracked files and does not use checkout caches, existing egg metadata or developer virtual environments. Run it from a checkout with Git on PATH after committing the files under review. It never changes the checkout or overwrites a nonempty output directory.

Two independent source snapshots and virtual environments must use the same commit, Python version, pinned tool versions and `SOURCE_DATE_EPOCH`. The default epoch is the commit's Unix timestamp; an explicitly supplied epoch is recorded in the build report. Do not substitute the current wall clock. The epoch must fit both ZIP and gzip timestamps (1980 through early 2106).

On Linux or macOS, from the repository root:

```sh
python3.13 -m venv .repro-env-a
python3.13 -m venv .repro-env-b
.repro-env-a/bin/python -m pip install -r tools/requirements-build.txt
.repro-env-b/bin/python -m pip install -r tools/requirements-build.txt
export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"
.repro-env-a/bin/python tools/build_reproducible.py build --output-dir dist/repro-a
.repro-env-b/bin/python tools/build_reproducible.py build --output-dir dist/repro-b
python3.13 tools/build_reproducible.py compare dist/repro-a dist/repro-b
```

On PowerShell use `python` for the installed 3.13.18 interpreter, `.repro-env-a/Scripts/python.exe` and `.repro-env-b/Scripts/python.exe`, and set `$env:SOURCE_DATE_EPOCH = git show -s --format=%ct HEAD`. Use fresh empty output directories for each attempt. No activation or system-wide environment/configuration changes are needed.

The standard backend builds an sdist and then builds its wheel. The utility normalizes the resulting archives, preserving and comparing every regular file's bytes before and after normalization:

- ZIP entries have sorted names, fixed UTC timestamps, Unix file modes and no varying comments or extra fields. Regular files retain their executable/nonexecutable distinction as mode 0755/0644.
- TAR entries have sorted names, regular-file mode 0755/0644 according to their executable bits, directory mode 0755, uid/gid zero, empty owner/group names and fixed timestamps. Links, special/privileged types, duplicate or aliased names, and file/directory collisions are rejected in both formats. Directory entries cannot hide a payload.
- gzip uses a fixed epoch, empty original filename and explicit compression level 9.

`SOURCE_DATE_EPOCH` alone is insufficient to claim reproducibility of arbitrary backend output. Canonicalization also removes variable TAR/gzip headers. The wheel's `RECORD` is preserved because member payloads remain unchanged. [Python's gzip documentation](https://docs.python.org/3.13/library/gzip.html) describes the timestamp controls; [the setuptools reproducibility discussion](https://github.com/pypa/setuptools/issues/2133) explains the sdist issue.

The committed NEXUS inputs currently contain no executable source files. Git executable modes are retained when snapshotting on POSIX; a Windows host rejects executable Git source members because its filesystem cannot reliably retain those POSIX mode bits. Use a POSIX build host for such inputs rather than silently stripping executable permissions.

Each output directory contains a `build-details.json` with commit, epoch, Python, operating system, zlib, tool versions and distribution SHA-256 hashes. The comparison command checks exact artifact filenames, payload bytes and full archive hashes, and fails if either archive differs. Preserve these reports with the tested artifacts. Report matching hashes only after that command succeeds. This profile establishes repeatability within the recorded environment; it does not promise identical compression across arbitrary Python/zlib versions or operating systems.

## Validate the exact artifacts

Use only the canonical artifacts from the first build after the comparison succeeds:

```sh
python -m pip install twine==7.0.0
python -m twine check --strict dist/repro-a/*.whl dist/repro-a/*.tar.gz
python -m unittest discover -s tests -v
python tests/check_distribution.py --sdist dist/repro-a/nexus_agent_evaluation-0.3.0rc1.tar.gz --wheel dist/repro-a/nexus_agent_evaluation-0.3.0rc1-py3-none-any.whl
```

Use actual artifact filenames if the reviewed version changes. The checker verifies metadata, license, fixtures, extracted-source tests, the synthetic consumer demonstration and both fresh installations outside the source tree. Accepted/rejected reports must agree with stdout and critical rejection must remain effective at threshold zero. Invalid invocations retain exit status 2.

Windows Application Control can block a newly generated console launcher with WinError 4551. Record that failure and rely on the hosted three-platform checks for that launcher; do not disable protections, suppress the failing checker or treat module execution as proof that the launcher passed. Twine's strict check validates metadata/description rendering, not documentation link targets or namespace ownership.

The [read-only reproducibility workflow](../.github/workflows/reproducible-package.yml) builds twice in separate virtual environments, compares them and validates the first set. It has no publication job, token configuration, tag creation or release creation. Existing general packaging checks remain in place.

CI resolves exactly one regular wheel and one regular sdist from the generated directory and rejects missing, additional or symlinked artifacts. It does not assume a filename containing `0.3.0rc1`, infer versions, or implement the project/artifact version-consistency task in issue #30. The versioned commands above are examples for this first candidate.

## Future Trusted Publishing setup

The owner must approve the package name, exact version, source commit, artifact hashes and publication destination before any account or workflow setup. A public PyPI 404 is not proof of name ownership, availability or reservation. A [pending Trusted Publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) also does not reserve a name until its first use.

After separate approval, configure the publisher for the exact GitHub owner, repository, publication workflow filename and protected environment. Use separate PyPI and TestPyPI publishers/environments if both destinations are eventually authorized; testing an upload also constitutes publication. Keep the current workflows unable to publish until that decision.

The proposed job boundary is:

| Job | Permissions and inputs | Required behavior |
| --- | --- | --- |
| Build | `contents: read`, no OIDC token | Check out the approved immutable commit, use the controlled profile, build twice, compare and retain one canonical artifact set plus hashes/reports. |
| Validate | `contents: read`, no OIDC token | Download that retained set by the producing run/artifact identity, verify its SHA-256 manifest, run Twine and installation checks; do not rebuild it. |
| Publish | `contents: read`, job-scoped `id-token: write`, owner-protected `pypi` environment | Run only after validation and human approval. Download the same artifacts, recheck hashes and upload exactly that set using PyPA's publishing action pinned to a reviewed commit. |

Configure required environment reviewers and restrict deployment branches/refs to the approved publication source. GitHub permits up to six reviewer users/teams with at least read access; only one listed reviewer approval is required. Required reviewers are available for public repositories on Free, Pro and Team plans. If self-review prevention is enabled, the initiating owner cannot approve their own deployment: arrange an actual second reviewer before enabling it. An environment name alone does not enforce approval. See [GitHub's environment requirements](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

Do not permit publication from pull requests or arbitrary forks. A publication job must not execute untrusted PR code, build packages or install project dependencies after receiving publishing authority. Keep build/validation outside that job. Treat the artifact-producing run ID, commit and expected hashes as approval inputs rather than accepting an arbitrary artifact name.

No long-lived PyPI token is required for [Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/). Grant `id-token: write` only to the future publishing job; do not add `contents: write`, `packages: write` or release permissions to build/test jobs. The owner must configure and review both the GitHub environment and PyPI publisher before enabling the workflow. This guide does not activate either service.

## Owner checklist for the first candidate publication

1. Sign in to the intended PyPI and TestPyPI accounts and verify control of `nexus-agent-evaluation` separately on both services. Check their project pages and the normalized name; if an existing project is controlled by someone else, resolve ownership or choose a reviewed name before building. An absent public project does not reserve it. Enable account 2FA and a recovery method.
2. Approve the exact source commit and `0.3.0rc1` metadata, review the tool-integrity limitation above, and confirm the evaluator/license/runtime requirements remain unchanged. The release notes are the reviewed [changelog](../CHANGELOG.md): deterministic declared decisions/action membership/evidence IDs, critical rejection and invalid-input exits, synthetic declaration lab, Unicode CLI support and packaging work. Do not describe the synthetic tests as model accuracy, production security, independent adoption or evidence authentication.
3. After separate authorization, create and protect `testpypi` and `pypi` environments, choose real eligible reviewers and allowed refs, and configure each service's publisher with the exact repository owner, repository, workflow filename and environment. Review any future workflow change before enabling job-scoped OIDC permissions; none are enabled here.
4. Build twice from that approved commit, compare complete archives and payloads, and validate the first set with Twine, installations and the supported runtime matrix. Retain its wheel, sdist and `build-details.json` with the producing run ID, commit, epoch, environment/tool versions and SHA-256 manifest. Store a durable copy before CI artifact retention expires; a log of hashes alone is not a retained package. No rebuild is permitted between approval and upload.
5. Authorize **TestPyPI first** as a separate publication action. Upload only the retained approved set; verify the served files match its hashes, installation and description links. TestPyPI and PyPI are separate services and a successful test upload does not grant permission to upload to PyPI.
6. After consumer verification, request explicit PyPI authorization for the same version and exact artifact hashes. Promote the retained files without rebuilding, recheck their hashes in the protected publishing job, and verify the resulting PyPI files. Tags and GitHub releases remain separate owner decisions. Update the unpublished/install wording only when the real publication has succeeded.

### External consumer commands after an authorized upload

Use a fresh Python 3.10+ environment outside the checkout. On POSIX the following commands select only TestPyPI and this dependency-free wheel; on Windows use `.nexus-consumer/Scripts/python.exe` in place of `.nexus-consumer/bin/python`:

```sh
python -m venv .nexus-consumer
.nexus-consumer/bin/python -m pip download --index-url https://test.pypi.org/simple/ --no-deps --only-binary=:all: --dest downloaded "nexus-agent-evaluation==0.3.0rc1"
.nexus-consumer/bin/python -m pip hash downloaded/*.whl
.nexus-consumer/bin/python -m pip install --no-index --no-deps downloaded/*.whl
.nexus-consumer/bin/python -I -m evaluator --help
```

Compare the downloaded wheel hash with the owner-approved manifest before installation. In PowerShell resolve the one downloaded wheel explicitly rather than relying on shell wildcard expansion. After an approved PyPI publication, repeat in a new environment with `--index-url https://pypi.org/simple/`; do not mix the indexes with `--extra-index-url`.

Save the following public synthetic smoke check as `consumer_smoke.py` in that external directory and run `.nexus-consumer/bin/python consumer_smoke.py` (or the Windows interpreter path above):

```python
import json
from pathlib import Path
import subprocess
import sys

Path("cases.json").write_text(json.dumps([{
    "id": "public-smoke", "expected_decision": "allow",
    "allowed_actions": [], "critical": True,
}]), encoding="utf-8")
for name, decision in (("accepted", "allow"), ("rejected", "deny")):
    Path(name + ".json").write_text(json.dumps({"public-smoke": {
        "decision": decision, "actions": [], "evidence": [],
    }}), encoding="utf-8")
for fixture, expected in (("accepted", 0), ("rejected", 1), ("missing", 2)):
    output = Path(fixture + "-report.json")
    assert not output.exists(), "use a fresh directory for each consumer check"
    result = subprocess.run([
        sys.executable, "-I", "-m", "evaluator", "--min-pass-rate=0",
        "--output", str(output), "cases.json", fixture + ".json",
    ], capture_output=True, text=True, timeout=30)
    assert result.returncode == expected, result.stderr
    if expected == 2:
        assert not result.stdout and result.stderr and not output.exists()
    else:
        report = json.loads(result.stdout)
        assert report == json.loads(output.read_text(encoding="utf-8"))
        assert report["accepted"] is (expected == 0)
        assert report["gate_passed"] is (expected == 0)
print("Observed expected CLI exits: 0, 1, 2")
```

Also run the installed `nexus-evaluate` command for the accepted and rejected fixtures and inspect its exit status (0 and 1). Module success does not establish launcher success on systems that block generated executables. The wheel has no bundled example fixtures; the synthetic files above belong to the caller.

## Recovery from a defective publication

1. Stop further publications and retain the producing commit, hashes, reports and install reproduction. If publisher identity or account access is suspect, the owner should disable the publisher and investigate access before any retry.
2. Diagnose with public synthetic inputs. For a security-sensitive report follow [the security policy](../SECURITY.md), keeping credentials and private data out of public issues.
3. Ask the owner to [yank the affected release](https://docs.pypi.org/project-management/yanking/) with a clear reason when appropriate. Yanking is not deletion or a guarantee that existing installations disappear; exact version pins may still select the release.
4. Prepare a reviewed correction with a new version, updated notes and the complete build/validation process. Do not overwrite or try to reuse already published filenames. A corrected upload, version change, yank or deletion requires owner authorization.
5. Update users with the affected versions, reproduction and recommended fixed version. Do not claim that publishing a fix automatically updates consumers.

See [PyPA's publication workflow guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) for the separation of build and publishing jobs. The outstanding owner decisions are name/account ownership, release timing/version, destinations, required reviewers, publisher identity, retained artifact approval and any recovery action.
