# Distribution preparation and publication approval

NEXUS Agent Evaluation remains an unpublished **0.3.0rc1** candidate. This procedure prepares and validates wheel and source archives without uploading them. The evaluator still supports Python 3.10+, uses the MIT license and has no runtime dependencies. A release, tag, TestPyPI upload or PyPI upload needs a separate owner decision.

## Documentation and package metadata

The package description uses [the repository README](../README.md). Its documentation links use absolute GitHub URLs so they work both on GitHub and in PyPI's Markdown renderer. The in-page Action section link remains a fragment. Links to `main` describe current documentation; immutable Git commit references identify reviewed Action behavior and historical evidence.

The README deliberately documents checkout installation while publication is pending. After an approved publication, update that wording and add the exact published install command, including `--pre` or an explicit version for a release candidate. Wheels contain the evaluator and console entry point; source archives also contain synthetic CLI fixtures, tests and Markdown documentation. Use a Git checkout for the complete browser laboratory.

## Controlled build profile

[The pinned requirements](../tools/requirements-build.txt) identify the build frontend, backend and their build dependencies. They are development tools, not evaluator runtime dependencies. The reproducibility workflow uses CPython **3.13.18**. Ordinary installation keeps the backend minimum of setuptools 77.0.3 and the existing Python 3.10–3.13 distribution matrix.

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

- ZIP entries have sorted names, fixed UTC timestamps, Unix file modes and no varying comments or extra fields.
- TAR entries have sorted names, regular-file mode 0644, directory mode 0755, uid/gid zero, empty owner/group names and fixed timestamps. Links and special file types are rejected.
- gzip uses a fixed epoch, empty original filename and explicit compression level 9.

`SOURCE_DATE_EPOCH` alone is insufficient to claim reproducibility of arbitrary backend output. Canonicalization also removes variable TAR/gzip headers. The wheel's `RECORD` is preserved because member payloads remain unchanged. [Python's gzip documentation](https://docs.python.org/3.13/library/gzip.html) describes the timestamp controls; [the setuptools reproducibility discussion](https://github.com/pypa/setuptools/issues/2133) explains the sdist issue.

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

## Future Trusted Publishing setup

The owner must approve the package name, exact version, source commit, artifact hashes and publication destination before any account or workflow setup. A public PyPI 404 is not proof of name ownership, availability or reservation. A [pending Trusted Publisher](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/) also does not reserve a name until its first use.

After separate approval, configure the publisher for the exact GitHub owner, repository, publication workflow filename and protected environment. Use separate PyPI and TestPyPI publishers/environments if both destinations are eventually authorized; testing an upload also constitutes publication. Keep the current workflows unable to publish until that decision.

The proposed job boundary is:

| Job | Permissions and inputs | Required behavior |
| --- | --- | --- |
| Build | `contents: read`, no OIDC token | Check out the approved immutable commit, use the controlled profile, build twice, compare and retain one canonical artifact set plus hashes/reports. |
| Validate | `contents: read`, no OIDC token | Download that retained set by the producing run/artifact identity, verify its SHA-256 manifest, run Twine and installation checks; do not rebuild it. |
| Publish | `contents: read`, job-scoped `id-token: write`, owner-protected `pypi` environment | Run only after validation and human approval. Download the same artifacts, recheck hashes and upload exactly that set using PyPA's publishing action pinned to a reviewed commit. |

Configure required environment reviewers, prevent self-review where supported and restrict deployment branches/refs to the approved publication source. Do not permit publication from pull requests or arbitrary forks. A publication job must not execute untrusted PR code, build packages or install project dependencies after receiving publishing authority. Keep build/validation outside that job. Treat the artifact-producing run ID, commit and expected hashes as approval inputs rather than accepting an arbitrary artifact name.

No long-lived PyPI token is required for [Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/). Grant `id-token: write` only to the future publishing job; do not add `contents: write`, `packages: write` or release permissions to build/test jobs. The owner must configure and review both the GitHub environment and PyPI publisher before enabling the workflow. This guide does not activate either service.

## Recovery from a defective publication

1. Stop further publications and retain the producing commit, hashes, reports and install reproduction. If publisher identity or account access is suspect, the owner should disable the publisher and investigate access before any retry.
2. Diagnose with public synthetic inputs. For a security-sensitive report follow [the security policy](../SECURITY.md), keeping credentials and private data out of public issues.
3. Ask the owner to [yank the affected release](https://docs.pypi.org/project-management/yanking/) with a clear reason when appropriate. Yanking is not deletion or a guarantee that existing installations disappear; exact version pins may still select the release.
4. Prepare a reviewed correction with a new version, updated notes and the complete build/validation process. Do not overwrite or try to reuse already published filenames. A corrected upload, version change, yank or deletion requires owner authorization.
5. Update users with the affected versions, reproduction and recommended fixed version. Do not claim that publishing a fix automatically updates consumers.

See [PyPA's publication workflow guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) for the separation of build and publishing jobs. The outstanding owner decisions are name/account ownership, release timing/version, destinations, required reviewers, publisher identity, retained artifact approval and any recovery action.
