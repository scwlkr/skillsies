"""Integration checks against a built scanner; all writable fixtures are temporary."""

import errno
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest


class ScannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get("MACBOOK_SCAN_BINARY")
        cls.binary = Path(configured) if configured else (
            Path.home() / "Library/Caches/macbook-cleanup/target/release/macbook-scan"
        )
        if not cls.binary.is_file() or not os.access(cls.binary, os.X_OK):
            raise RuntimeError(
                "Build scanner/Cargo.toml in release mode, then set "
                "MACBOOK_SCAN_BINARY to the executable; unavailable: " + str(cls.binary)
            )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macbook-scan-test-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()

    def write(self, relative, data=b"sample" * 1024):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def command(self, roots=None, extra=()):
        args = [str(self.binary), "--home", str(self.home), "--threads", "4",
                "--top", "100", "--min-candidate-bytes", "1"]
        for root in roots if roots is not None else [self.home]:
            args.extend(["--root", str(root)])
        return subprocess.run(args + list(extra), capture_output=True, text=True, timeout=30)

    def scan(self, roots=None, extra=()):
        result = self.command(roots, extra)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    @staticmethod
    def allocated(paths):
        seen = set()
        total = 0
        for path in paths:
            stat = path.stat()
            key = (stat.st_dev, stat.st_ino)
            if key not in seen:
                seen.add(key)
                total += stat.st_blocks * 512
        return total

    def test_exact_totals_include_directory_blocks_and_scan_is_read_only(self):
        first = self.write("alpha/a.bin")
        second = self.write("alpha/nested/b.bin", b"b" * 19001)
        paths = [self.home, first.parent, second.parent, first, second]
        before = {str(p): (p.stat().st_mtime_ns, p.stat().st_size) for p in paths}
        result = self.scan()
        self.assertEqual(result["allocated_bytes"], self.allocated(paths))
        self.assertEqual(result["logical_bytes"], first.stat().st_size + second.stat().st_size)
        self.assertEqual((result["files"], result["directories"]), (2, 3))
        self.assertEqual(result["error_count"], 0)
        self.assertEqual(before, {str(p): (p.stat().st_mtime_ns, p.stat().st_size) for p in paths})
        for field in ("errors", "roots", "excluded", "top_files", "top_directories", "candidates"):
            self.assertIsInstance(result[field], list)
        for field in ("hardlink_duplicates", "symlinks_skipped", "external_mounts_skipped", "dataless_skipped"):
            self.assertEqual(result[field], 0)

    def test_hardlinks_are_counted_once_across_distinct_roots(self):
        original = self.write("one/original.bin")
        linked = self.home / "two/copy.bin"
        linked.parent.mkdir()
        os.link(original, linked)
        result = self.scan([original.parent, linked.parent])
        self.assertEqual(result["allocated_bytes"], self.allocated([original.parent, linked.parent, original]))
        self.assertEqual(result["logical_bytes"], original.stat().st_size)
        self.assertEqual(result["hardlink_duplicates"], 1)
        self.assertEqual(len(result["top_files"]), 1)

    def test_sparse_file_uses_allocation_instead_of_logical_size(self):
        sparse = self.home / "sparse.bin"
        with sparse.open("wb") as handle:
            handle.seek(64 * 1024 * 1024)
            handle.write(b"x")
        stat = sparse.stat()
        if stat.st_blocks * 512 >= stat.st_size:
            self.skipTest("fixture filesystem does not support sparse allocation")
        result = self.scan()
        self.assertEqual(result["logical_bytes"], stat.st_size)
        self.assertEqual(result["allocated_bytes"], self.allocated([self.home, sparse]))
        self.assertLess(result["allocated_bytes"], result["logical_bytes"])

    def test_symlinks_are_not_followed_and_symlink_roots_are_refused(self):
        outside = self.write("outside/secret.bin", b"x" * 90001)
        inside = self.home / "inside"
        inside.mkdir()
        (inside / "shortcut").symlink_to(outside.parent, target_is_directory=True)
        (inside / "loop").symlink_to(inside, target_is_directory=True)
        result = self.scan([inside])
        self.assertEqual(result["files"], 0)
        self.assertEqual(result["symlinks_skipped"], 2)
        self.assertEqual(result["allocated_bytes"], inside.stat().st_blocks * 512)
        rejected = self.command([inside / "shortcut"])
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("real directory", rejected.stderr)

    def test_overlapping_roots_are_deduplicated(self):
        payload = self.write("nested/deep/payload.bin")
        result = self.scan([payload.parent, self.home, payload.parent.parent, self.home])
        self.assertEqual(result["roots"], [str(self.home)])
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["allocated_bytes"], self.allocated(
            [self.home, payload.parent.parent, payload.parent, payload]))

    def test_exclusions_prune_whole_subtrees_and_preserve_similar_names(self):
        forbidden = self.write("private/hidden.bin")
        kept = self.write("private-other/kept.bin")
        self.write(".tall-talents/also-hidden.bin")
        result = self.scan(extra=["--exclude", str(forbidden.parent)])
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["allocated_bytes"], self.allocated([self.home, kept.parent, kept]))
        self.assertEqual([row["path"] for row in result["top_files"]], [str(kept)])
        rejected = self.command([forbidden.parent], ["--exclude", str(forbidden.parent)])
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("excluded root", rejected.stderr)

    def test_data_volume_alias_exclusion_and_vm_protection(self):
        forbidden = self.write("sensitive/payload.bin")
        kept = self.write("ordinary.bin")
        alias = "/System/Volumes/Data" + str(forbidden.parent)
        result = self.scan(extra=["--exclude", alias])
        self.assertEqual(result["files"], 1)
        self.assertEqual([row["path"] for row in result["top_files"]], [str(kept)])
        self.assertIn("/private/var/vm", result["excluded"])
        # These are refusal checks only; the scanner must not descend into real VM storage.
        for root in (Path("/private/var/vm"), Path("/var/vm"),
                     Path("/System/Volumes/Data/private/var/vm")):
            if root.is_dir() and not root.is_symlink():
                rejected = self.command([root])
                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn("excluded root", rejected.stderr)

    def test_parent_components_in_exclusion_are_normalized(self):
        forbidden = self.write("sensitive/payload.bin")
        self.write("ordinary.bin")
        (self.home / "anchor").mkdir()
        result = self.scan(extra=["--exclude", str(self.home / "anchor/../sensitive")])
        self.assertEqual(result["files"], 1)
        self.assertNotIn(str(forbidden), [row["path"] for row in result["top_files"]])

    def test_non_utf8_filename_produces_json_and_a_coverage_warning(self):
        path = os.fsencode(self.home) + b"/non-utf8-\xff.bin"
        try:
            with open(path, "wb") as handle:
                handle.write(b"sample")
        except OSError as error:
            if error.errno == errno.EILSEQ:
                self.skipTest("fixture filesystem refuses non-UTF8 filenames")
            raise
        result = self.scan()
        self.assertEqual(result["files"], 1)
        self.assertEqual(result["allocated_bytes"],
                         self.home.stat().st_blocks * 512 + os.stat(path).st_blocks * 512)
        self.assertEqual(len(result["top_files"]), 1)
        self.assertIn("\ufffd", result["top_files"][0]["path"])
        self.assertGreater(result["error_count"], 0)

    def test_build_classification_requires_the_owning_project_manifest(self):
        self.write("cargo/Cargo.toml", b"[package]\nname='fixture'\n")
        cargo = self.write("cargo/target/build.bin").parent
        self.write("node/package.json", b'{"name":"fixture"}')
        node = self.write("node/node_modules/pkg/index.js").parent.parent
        arbitrary = self.write("user/target/important.bin").parent
        arbitrary_node = self.write("user/node_modules/important.bin").parent
        result = self.scan()
        candidates = {row["path"]: row for row in result["candidates"]}
        self.assertEqual(set(candidates), {str(cargo), str(node)})
        for path in (cargo, node):
            self.assertEqual(candidates[str(path)]["category"], "build")
            self.assertEqual(candidates[str(path)]["risk"], "review")
        self.assertNotIn(str(arbitrary), candidates)
        self.assertNotIn(str(arbitrary_node), candidates)

    def test_candidate_sizes_do_not_overlap(self):
        self.write("Library/Caches/project/Cargo.toml", b"[package]\n")
        self.write("Library/Caches/project/target/build.bin")
        self.write("Downloads/setup.dmg")
        self.write("Downloads/setup.zip")
        result = self.scan()
        candidates = [Path(row["path"]) for row in result["candidates"]]
        self.assertEqual(len(candidates), 3)
        for left in candidates:
            for right in candidates:
                if left != right:
                    self.assertFalse(left.is_relative_to(right))
        self.assertLessEqual(sum(row["allocated_bytes"] for row in result["candidates"]),
                             result["allocated_bytes"])

    def test_missing_roots_and_absent_root_argument_fail(self):
        for roots in ([self.home / "missing"], []):
            result = self.command(roots)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertIn("macbook-scan:", result.stderr)

    def test_permission_denied_is_reported_without_claiming_full_coverage(self):
        blocked = self.write("blocked/secret.bin").parent
        if os.geteuid() == 0:
            self.skipTest("root bypasses directory read permissions")
        blocked.chmod(0)
        try:
            try:
                list(blocked.iterdir())
            except PermissionError:
                pass
            else:
                self.skipTest("fixture filesystem bypasses directory read permissions")
            result = self.scan()
            self.assertGreater(result["error_count"], 0)
            self.assertTrue(result["errors"])
            self.assertEqual(result["files"], 0)
        finally:
            blocked.chmod(0o700)

    def test_10000_small_files_match_du_allocation(self):
        if not shutil.which("du"):
            self.skipTest("du is unavailable for allocation cross-check")
        root = self.home / "benchmark"
        for group in range(100):
            directory = root / f"g{group:03d}"
            directory.mkdir(parents=True)
            for index in range(100):
                (directory / f"f{index:03d}").write_bytes(b"benchmark" * 16)
        start = time.perf_counter()
        result = self.scan([root])
        scanner_seconds = time.perf_counter() - start
        start = time.perf_counter()
        du = subprocess.run(["du", "-k", "-s", str(root)], capture_output=True,
                            text=True, check=True, timeout=30)
        du_seconds = time.perf_counter() - start
        self.assertEqual(result["files"], 10000)
        self.assertEqual(result["directories"], 101)
        self.assertEqual(result["allocated_bytes"], int(du.stdout.split()[0]) * 1024)
        output = os.environ.get("MACBOOK_SCAN_BENCHMARK_OUTPUT")
        if output:
            Path(output).write_text(json.dumps({
                "fixture": "10000 files in 100 subdirectories; warm filesystem metadata",
                "scanner_seconds": scanner_seconds, "du_seconds": du_seconds,
                "allocated_bytes": result["allocated_bytes"],
                "note": "One local fixture timing; not a universal speed claim.",
            }, indent=2) + "\n")


if __name__ == "__main__":
    unittest.main()
