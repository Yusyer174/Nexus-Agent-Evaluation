"""Build canonical archives from a Git commit, or compare two build directories.

Build tooling only. Requires Git and the pinned requirements-build.txt profile.
The evaluator and its normal setuptools backend do not import this module.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
from importlib import metadata
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import tarfile
import tempfile
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or not path.parts:
        raise ValueError(f'unsupported archive path: {name!r}')
    return path


def archive_contents(path):
    """Return regular file bytes, rejecting ambiguous or special members."""
    result = {}
    if path.name.endswith('.whl'):
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                safe_name(member.filename)
                if member.is_dir():
                    continue
                if member.filename in result:
                    raise ValueError(f'duplicate archive member: {member.filename}')
                result[member.filename] = archive.read(member)
    else:
        with tarfile.open(path) as archive:
            for member in archive:
                safe_name(member.name)
                if member.isdir():
                    continue
                if not member.isfile() or member.name in result:
                    raise ValueError(f'unsupported or duplicate archive member: {member.name}')
                result[member.name] = archive.extractfile(member).read()
    return result


def canonicalize(source, destination, epoch):
    """Preserve file payloads while fixing ordering, modes and archive headers."""
    if not 315532800 <= epoch <= 4294967295:
        raise ValueError('SOURCE_DATE_EPOCH must be in the ZIP/gzip range (1980 to 2106)')
    files = archive_contents(source)
    if source.name.endswith('.whl'):
        timestamp = datetime.fromtimestamp(epoch, timezone.utc).timetuple()[:6]
        with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9) as archive:
            for name, data in sorted(files.items()):
                member = zipfile.ZipInfo(name, timestamp)
                member.create_system = 3
                member.external_attr = 0o100644 << 16
                member.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(member, data, compresslevel=9)
    else:
        directories = {str(parent) for name in files for parent in safe_name(name).parents
                       if str(parent) != '.'}
        with destination.open('xb') as output:
            with gzip.GzipFile(filename='', mode='wb', fileobj=output,
                               compresslevel=9, mtime=epoch) as compressed:
                with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
                    for name in sorted(directories | files.keys()):
                        member = tarfile.TarInfo(name)
                        member.mtime = epoch
                        if name in directories:
                            member.type = tarfile.DIRTYPE
                            member.mode = 0o755
                            archive.addfile(member)
                        else:
                            data = files[name]
                            member.mode = 0o644
                            member.size = len(data)
                            archive.addfile(member, io.BytesIO(data))
    if archive_contents(destination) != files:
        raise ValueError('archive normalization changed file payloads')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(first, second):
    def artifacts(folder):
        return {p.name: p for p in folder.iterdir()
                if p.name.endswith(('.whl', '.tar.gz'))}
    left, right = artifacts(first), artifacts(second)
    if not left or left.keys() != right.keys():
        raise ValueError('build directories contain different or no distribution filenames')
    if sum(name.endswith('.whl') for name in left) != 1 or len(left) != 2:
        raise ValueError('expected exactly one wheel and one sdist per build')
    report = {}
    for name in sorted(left):
        same_payload = archive_contents(left[name]) == archive_contents(right[name])
        first_hash, second_hash = sha256(left[name]), sha256(right[name])
        report[name] = {'first_sha256': first_hash, 'second_sha256': second_hash,
                        'identical_payload': same_payload,
                        'identical_archive': first_hash == second_hash}
    print(json.dumps(report, indent=2))
    return all(row['identical_payload'] and row['identical_archive'] for row in report.values())


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def build(output):
    # Keep the published snapshot independent of untracked files and local caches.
    if git('status', '--porcelain', '--untracked-files=no').strip():
        raise ValueError('commit tracked changes before building the release snapshot')
    from packaging.requirements import Requirement
    versions = {}
    for line in (ROOT / 'tools/requirements-build.txt').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        requirement = Requirement(line)
        if requirement.marker and not requirement.marker.evaluate():
            continue
        actual = metadata.version(requirement.name)
        if actual not in requirement.specifier:
            raise ValueError(f'{requirement.name}: expected {requirement.specifier}, found {actual}')
        versions[requirement.name] = actual
    revision = git('rev-parse', 'HEAD').decode().strip()
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH', git('show', '-s', '--format=%ct', 'HEAD').decode().strip()))
    if not 315532800 <= epoch <= 4294967295:
        raise ValueError('SOURCE_DATE_EPOCH must be in the ZIP/gzip range (1980 to 2106)')
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('output directory must be empty; existing results are never overwritten')
    environment = os.environ.copy()
    environment['SOURCE_DATE_EPOCH'] = str(epoch)
    environment.pop('PYTHONPATH', None)
    environment.pop('PYTHONHOME', None)
    with tempfile.TemporaryDirectory(prefix='nexus reproducible build ') as temporary:
        workspace = Path(temporary)
        source, raw = workspace / 'source', workspace / 'raw'
        source.mkdir()
        with tarfile.open(fileobj=io.BytesIO(git('archive', '--format=tar', 'HEAD'))) as archive:
            for member in archive:
                name = safe_name(member.name)
                target = source.joinpath(*name.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
                else:
                    raise ValueError(f'unsupported source member: {member.name}')
        subprocess.run([sys.executable, '-m', 'build', '--no-isolation', '--outdir', str(raw),
                        str(source)], env=environment, check=True, timeout=180)
        artifacts = sorted(raw.iterdir())
        if len(artifacts) != 2 or not any(p.suffix == '.whl' for p in artifacts):
            raise ValueError('build did not produce exactly a wheel and an sdist')
        for artifact in artifacts:
            canonicalize(artifact, output / artifact.name, epoch)
    report = {'source_commit': revision, 'source_date_epoch': epoch,
              'python': platform.python_version(), 'platform': platform.system(),
              'zlib': zlib.ZLIB_RUNTIME_VERSION, 'tools': versions,
              'sha256': {p.name: sha256(p) for p in sorted(output.iterdir())}}
    (output / 'build-details.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    builder = commands.add_parser('build')
    builder.add_argument('--output-dir', type=Path, required=True)
    comparison = commands.add_parser('compare')
    comparison.add_argument('first', type=Path)
    comparison.add_argument('second', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'build':
            build(args.output_dir.resolve())
            return 0
        return 0 if compare(args.first.resolve(), args.second.resolve()) else 1
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(2, f'Build verification error: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
