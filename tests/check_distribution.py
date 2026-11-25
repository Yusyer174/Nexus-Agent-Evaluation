"""Check built distributions without importing the checkout (Python 3.10+).

Run after `python -m build`:
    python tests/check_distribution.py --sdist dist/name.tar.gz --wheel dist/name.whl
"""
import argparse
import configparser
from email.parser import BytesParser
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import unittest
import venv
import zipfile


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="nexus distribution checks ")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.workspace = Path(cls.temporary.name)
        unpacked = cls.workspace / "unpacked"
        roots = set()
        with tarfile.open(cls.sdist) as archive:
            for member in archive.getmembers():
                name = PurePosixPath(member.name)
                if name.is_absolute() or ".." in name.parts:
                    raise ValueError(f"invalid archive path: {member.name}")
                roots.add(name.parts[0])
                if member.isdir():
                    continue
                if not member.isfile():
                    raise ValueError(f"unsupported archive member: {member.name}")
                target = unpacked.joinpath(*name.parts)
                if not target.resolve().is_relative_to(unpacked.resolve()):
                    raise ValueError(f"archive path escapes destination: {member.name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source:
                    target.write_bytes(source.read())
        if len(roots) != 1:
            raise ValueError("sdist must contain one top-level directory")
        cls.source = unpacked / roots.pop()

    def run_command(self, command, cwd, timeout=180):
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        result = subprocess.run(command, cwd=cwd, env=environment,
                                capture_output=True, text=True, timeout=timeout)
        return result

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sdist_contains_tests_fixtures_and_documentation(self):
        required = {
            "evaluator.py", "pyproject.toml", "LICENSE", "README.md",
            "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", "action.yml",
            "examples/cases.json", "examples/predictions.json",
            "examples/rejected-predictions.json",
            "examples/github-actions/evaluate-agent.yml",
            "examples/consumer/cases.json", "examples/consumer/predictions.json",
            "examples/consumer/rejected-predictions.json", "examples/consumer/run_demo.py",
            "tests/test_cli.py", "tests/test_evaluator.py", "tests/check_distribution.py",
            "tests/test_report_contract.py", "tests/test_declaration_lab.py",
            "docs/DECLARATION_LAB.md",
            "docs/INTEGRATION.md", "docs/TRY_IT.md", "docs/ROADMAP.md",
            "docs/CONSUMER_TRIAL.md",
        }
        missing = sorted(path for path in required if not (self.source / path).is_file())
        self.assertEqual(missing, [], f"sdist is incomplete: {missing}")

    def test_wheel_metadata_entry_point_and_license(self):
        with zipfile.ZipFile(self.wheel) as archive:
            metadata_paths = [name for name in archive.namelist()
                              if name.endswith(".dist-info/METADATA")]
            self.assertEqual(len(metadata_paths), 1)
            metadata_path = metadata_paths[0]
            info = metadata_path.rsplit("/", 1)[0]
            metadata = BytesParser().parsebytes(archive.read(metadata_path))
            source_metadata = BytesParser().parsebytes((self.source / "PKG-INFO").read_bytes())
            self.assertEqual(metadata["Name"], "nexus-agent-evaluation")
            self.assertEqual(metadata["Version"], source_metadata["Version"])
            self.assertEqual(metadata["Requires-Python"], ">=3.10")
            self.assertEqual(metadata["License-Expression"], "MIT")
            self.assertEqual(metadata.get_all("License-File"), ["LICENSE"])
            self.assertFalse(metadata.get_all("Requires-Dist"), "runtime dependencies were added")
            self.assertEqual(archive.read(info + "/licenses/LICENSE"),
                             (self.source / "LICENSE").read_bytes())
            self.assertEqual(archive.read("evaluator.py"), (self.source / "evaluator.py").read_bytes())
            entry_points = configparser.ConfigParser()
            entry_points.read_string(archive.read(info + "/entry_points.txt").decode("utf-8"))
            self.assertEqual(entry_points["console_scripts"]["nexus-evaluate"], "evaluator:main")

    def test_regression_suite_runs_from_sdist(self):
        result = self.run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                                  self.source)
        self.assert_success(result)

    def test_consumer_demo_runs_from_sdist(self):
        output = self.workspace / "consumer results"
        result = self.run_command(
            [sys.executable, str(self.source / "examples/consumer/run_demo.py"),
             "--evaluator", str(self.source / "evaluator.py"), "--output-dir", str(output)],
            self.workspace)
        self.assert_success(result)
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual([row["observed_exit"] for row in summary["observations"]], [0, 1, 2])

    def test_both_distributions_install_and_run_outside_source(self):
        for label, artifact in (("sdist", self.sdist), ("wheel", self.wheel)):
            with self.subTest(distribution=label):
                environment = self.workspace / (label + " environment")
                venv.EnvBuilder(with_pip=True).create(environment)
                scripts = environment / ("Scripts" if os.name == "nt" else "bin")
                python = scripts / ("python.exe" if os.name == "nt" else "python")
                command = scripts / ("nexus-evaluate.exe" if os.name == "nt" else "nexus-evaluate")
                caller = self.workspace / (label + " caller")
                caller.mkdir()
                self.assert_success(self.run_command(
                    [str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-deps", str(artifact)],
                    caller))
                imported = self.run_command([str(python), "-I", "-c",
                                             "import evaluator; print(evaluator.__file__)"], caller)
                self.assert_success(imported)
                self.assertTrue(Path(imported.stdout.strip()).resolve().is_relative_to(environment.resolve()),
                                imported.stdout)
                for fixture, expected in (("predictions.json", 0), ("rejected-predictions.json", 1)):
                    with self.subTest(distribution=label, fixture=fixture):
                        output = caller / (fixture + ".report.json")
                        result = self.run_command(
                            [str(command), str(self.source / "examples/cases.json"),
                             str(self.source / "examples" / fixture),
                             "--min-pass-rate=0", "--output", str(output)], caller)
                        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                        report = json.loads(result.stdout)
                        self.assertEqual(report, json.loads(output.read_text(encoding="utf-8")))
                        self.assertIs(report["accepted"], expected == 0)
                        self.assertEqual(report["total"], 3)
                        self.assertEqual(report["critical_failures"], [] if expected == 0 else ["permissions-01"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdist", type=Path, required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    args, test_args = parser.parse_known_args()
    DistributionTests.sdist = args.sdist.resolve()
    DistributionTests.wheel = args.wheel.resolve()
    unittest.main(argv=[sys.argv[0], *test_args], verbosity=2)
