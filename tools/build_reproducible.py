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
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]


def safe_name(name):
    clean = name[:-1] if name.endswith('/') else name
    path = PurePosixPath(clean)
    if (path.is_absolute() or '..' in path.parts or '\\' in name or not path.parts
            or clean != path.as_posix() or ':' in path.parts[0]):
        raise ValueError(f'unsupported archive path: {name!r}')
    return path


def _archive_members(path):
    """Read payloads and executable modes; reject ambiguous member layouts."""
    result, modes, entries = {}, {}, {}

    def register(name, directory, mode, data):
        name = str(safe_name(name))
        if name in entries or mode & 0o7000 or (directory and data):
            raise ValueError(f'unsupported or duplicate archive member: {name}')
        entries[name] = directory
        if not directory:
            result[name] = data
            modes[name] = 0o755 if mode & 0o111 else 0o644

    if path.name.endswith('.whl'):
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                mode = member.external_attr >> 16
                kind, directory = stat.S_IFMT(mode), member.is_dir()
                if (kind not in (0, stat.S_IFREG, stat.S_IFDIR)
                        or (kind == stat.S_IFDIR and not directory)
                        or (kind == stat.S_IFREG and directory)
                        or (member.external_attr & 0x10 and not directory)):
                    raise ValueError(f'unsupported ZIP member type: {member.filename}')
                register(member.filename, directory, mode, archive.read(member))
    else:
        with tarfile.open(path) as archive:
            for member in archive:
                if member.isdir():
                    if member.size:
                        raise ValueError(f'nonempty TAR directory member: {member.name}')
                    register(member.name, True, member.mode, b'')
                elif member.type in (tarfile.REGTYPE, tarfile.AREGTYPE) and not member.issparse():
                    register(member.name, False, member.mode, archive.extractfile(member).read())
                else:
                    raise ValueError(f'unsupported or duplicate archive member: {member.name}')
    for name in entries:
        if any(str(parent) in entries and not entries[str(parent)]
               for parent in safe_name(name).parents):
            raise ValueError(f'file/directory collision in archive: {name}')
    return result, modes


def archive_contents(path):
    """Return regular file bytes, rejecting ambiguous or special members."""
    return _archive_members(path)[0]


def canonicalize(source, destination, epoch):
    """Preserve file payloads while fixing ordering, modes and archive headers."""
    if not 315532800 <= epoch <= 4294967295:
        raise ValueError('SOURCE_DATE_EPOCH must be in the ZIP/gzip range (1980 to 2106)')
    files, modes = _archive_members(source)
    if source.name.endswith('.whl'):
        timestamp = datetime.fromtimestamp(epoch, timezone.utc).timetuple()[:6]
        with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9) as archive:
            for name, data in sorted(files.items()):
                member = zipfile.ZipInfo(name, timestamp)
                member.create_system = 3
                member.external_attr = (stat.S_IFREG | modes[name]) << 16
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
                            member.mode = modes[name]
                            member.size = len(data)
                            archive.addfile(member, io.BytesIO(data))
    if _archive_members(destination) != (files, modes):
        raise ValueError('archive normalization changed file payloads or executable modes')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_distributions(folder):
    """Resolve generated filenames without inferring or comparing versions."""
    wheels = list(folder.glob('*.whl'))
    sources = list(folder.glob('*.tar.gz'))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError('expected exactly one wheel and one sdist per build')
    if any(not p.is_file() or p.is_symlink() for p in (*sources, *wheels)):
        raise ValueError('distribution paths must be regular files, not symlinks')
    return sources[0], wheels[0]


def compare(first, second):
    left = {p.name: p for p in find_distributions(first)}
    right = {p.name: p for p in find_distributions(second)}
    if left.keys() != right.keys():
        raise ValueError('build directories contain different distribution filenames')
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
                    if os.name == 'nt' and member.mode & 0o111:
                        raise ValueError('executable Git source members require a POSIX build host')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(member).read())
                    target.chmod(member.mode & 0o777)
                else:
                    raise ValueError(f'unsupported source member: {member.name}')
        subprocess.run([sys.executable, '-m', 'build', '--no-isolation', '--outdir', str(raw),
                        str(source)], env=environment, check=True, timeout=180)
        artifacts = find_distributions(raw)
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
