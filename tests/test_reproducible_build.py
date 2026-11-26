"""Regression coverage for differing archive metadata and preserved payloads."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

from tools.build_reproducible import archive_contents, canonicalize, compare

EPOCH = 1795684865


class ReproducibleBuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_wheel_headers_and_order_do_not_change_normalized_bytes(self):
        outputs = []
        for index, names in enumerate((('pkg.py', 'pkg.dist-info/RECORD'),
                                       ('pkg.dist-info/RECORD', 'pkg.py'))):
            raw, output = self.root / f'raw{index}.whl', self.root / f'out{index}.whl'
            with zipfile.ZipFile(raw, 'w') as archive:
                for name in names:
                    member = zipfile.ZipInfo(name, (2020 + index, 1, 1, 0, 0, 0))
                    member.comment = b'variable metadata'
                    member.external_attr = (0o100600 + index) << 16
                    archive.writestr(member, name.encode())
            canonicalize(raw, output, EPOCH)
            self.assertEqual(archive_contents(raw), archive_contents(output))
            outputs.append(output.read_bytes())
        self.assertEqual(*outputs)

    def test_sdist_ownership_timestamps_and_order_do_not_change_normalized_bytes(self):
        outputs = []
        for index, names in enumerate((('pkg/a.py', 'pkg/PKG-INFO'),
                                       ('pkg/PKG-INFO', 'pkg/a.py'))):
            raw, output = self.root / f'raw{index}.tar.gz', self.root / f'out{index}.tar.gz'
            with tarfile.open(raw, 'w:gz') as archive:
                for name in names:
                    member = tarfile.TarInfo(name)
                    member.size = len(name)
                    member.uid = 1000 + index
                    member.uname = f'builder-{index}'
                    member.mtime = EPOCH + index
                    member.pax_headers = {'mtime': str(EPOCH + index) + '.5'}
                    archive.addfile(member, io.BytesIO(name.encode()))
            canonicalize(raw, output, EPOCH)
            self.assertEqual(archive_contents(raw), archive_contents(output))
            outputs.append(output.read_bytes())
        self.assertEqual(*outputs)

    def test_compare_detects_changed_payload(self):
        folders = [self.root / name for name in ('first', 'second')]
        for index, folder in enumerate(folders):
            folder.mkdir()
            with zipfile.ZipFile(folder / 'pkg.whl', 'w') as archive:
                archive.writestr('pkg.py', f'changed={index}')
            with tarfile.open(folder / 'pkg.tar.gz', 'w:gz'):
                pass
        with redirect_stdout(io.StringIO()):
            self.assertFalse(compare(*folders))

    def test_rejects_archive_paths_that_escape_the_source(self):
        raw = self.root / 'unsafe.tar.gz'
        with tarfile.open(raw, 'w:gz') as archive:
            member = tarfile.TarInfo('../outside.py')
            archive.addfile(member, io.BytesIO())
        with self.assertRaisesRegex(ValueError, 'archive path'):
            canonicalize(raw, self.root / 'normalized.tar.gz', EPOCH)
