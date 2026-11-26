"""Regression coverage for differing archive metadata and preserved payloads."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import stat
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
                    member.external_attr = (0o100600 if index == 0 else 0o100640) << 16
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

    def test_executable_modes_survive_zip_and_tar_normalization(self):
        for extension in ('whl', 'tar.gz'):
            with self.subTest(format=extension):
                raw, output = self.root / f'executable.{extension}', self.root / f'fixed.{extension}'
                if extension == 'whl':
                    with zipfile.ZipFile(raw, 'w') as archive:
                        member = zipfile.ZipInfo('pkg.data/scripts/run')
                        member.create_system = 3
                        member.external_attr = (stat.S_IFREG | 0o755) << 16
                        archive.writestr(member, b'#!/bin/sh\nexit 0\n')
                else:
                    with tarfile.open(raw, 'w:gz') as archive:
                        member = tarfile.TarInfo('pkg/run')
                        member.mode, member.size = 0o755, 1
                        archive.addfile(member, io.BytesIO(b'x'))
                canonicalize(raw, output, EPOCH)
                if extension == 'whl':
                    with zipfile.ZipFile(output) as archive:
                        mode = (archive.infolist()[0].external_attr >> 16) & 0o777
                else:
                    with tarfile.open(output) as archive:
                        mode = archive.getmember('pkg/run').mode
                self.assertEqual(mode, 0o755)
                self.assertEqual(archive_contents(raw), archive_contents(output))

    def test_zip_rejects_special_types_and_inconsistent_directory_entries(self):
        cases = [('link', stat.S_IFLNK | 0o777, b'target'),
                 ('fifo', stat.S_IFIFO | 0o644, b''),
                 ('directory', stat.S_IFDIR | 0o755, b''),
                 ('directory-data/', stat.S_IFDIR | 0o755, b'not a directory'),
                 ('privileged', stat.S_IFREG | 0o4755, b'x')]
        for index, (name, mode, data) in enumerate(cases):
            with self.subTest(member=name):
                raw = self.root / f'special-{index}.whl'
                with zipfile.ZipFile(raw, 'w') as archive:
                    member = zipfile.ZipInfo(name)
                    member.create_system = 3
                    member.external_attr = mode << 16
                    archive.writestr(member, data)
                with self.assertRaises(ValueError):
                    archive_contents(raw)

        raw = self.root / 'directory-data.tar.gz'
        with tarfile.open(raw, 'w:gz') as archive:
            member = tarfile.TarInfo('pkg')
            member.type, member.size = tarfile.DIRTYPE, 1
            archive.addfile(member, io.BytesIO(b'x'))
        with self.assertRaises(ValueError):
            archive_contents(raw)

    def test_zip_and_tar_reject_aliased_or_colliding_member_paths(self):
        cases = [('pkg.py', './pkg.py'), ('pkg/a', 'pkg//a'),
                 ('pkg', 'pkg/file'), ('pkg/', 'pkg')]
        for extension in ('whl', 'tar.gz'):
            for index, names in enumerate(cases):
                with self.subTest(format=extension, names=names):
                    raw = self.root / f'ambiguous-{index}.{extension}'
                    if extension == 'whl':
                        with zipfile.ZipFile(raw, 'w') as archive:
                            for name in names:
                                archive.writestr(name, b'' if name.endswith('/') else b'x')
                    else:
                        with tarfile.open(raw, 'w:gz') as archive:
                            for name in names:
                                member = tarfile.TarInfo(name)
                                if name.endswith('/'):
                                    member.type = tarfile.DIRTYPE
                                    archive.addfile(member)
                                else:
                                    member.size = 1
                                    archive.addfile(member, io.BytesIO(b'x'))
                    with self.assertRaises(ValueError):
                        archive_contents(raw)

    def test_distribution_discovery_uses_generated_names_and_rejects_ambiguity(self):
        from tools.build_reproducible import find_distributions
        source = self.root / 'another_name-9.2rc3.tar.gz'
        wheel = self.root / 'another_name-9.2rc3-py3-none-any.whl'
        source.touch()
        with self.assertRaises(ValueError):
            find_distributions(self.root)
        wheel.touch()
        (self.root / 'build-details.json').write_text('{}', encoding='utf-8')
        self.assertEqual(find_distributions(self.root), (source, wheel))
        (self.root / 'extra.whl').touch()
        with self.assertRaises(ValueError):
            find_distributions(self.root)
