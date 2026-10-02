"""Exercise the public setup command and generated Rust CLI in disposable projects."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/setup.py"
PROJECT = "https://linear.app/example/project/sample-123"


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="scwlkr-setup-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project with spaces"
        self.root.mkdir()

    def setup(self, action="apply", *args, ok=True, env=None):
        result = subprocess.run([sys.executable, str(SCRIPT), action, str(self.root), *args],
                                text=True, capture_output=True, env=env)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stdout + result.stderr)
        return json.loads(result.stdout if result.stdout else result.stderr)

    def first_apply(self):
        return self.setup("apply", "--team", "Example", "--linear-project", PROJECT)

    def cli(self, *args, env=None):
        return subprocess.run([str(self.root / "project"), *args], cwd=self.temp.name,
                              text=True, capture_output=True, env=env)

    def snapshot(self):
        return {str(path.relative_to(self.root)): (path.read_bytes(), path.stat().st_mtime_ns)
                for path in self.root.rglob("*") if path.is_file() and "target" not in path.parts}

    def test_new_project_and_repeat_run(self):
        self.setup("apply", ok=False)
        self.assertEqual(list(self.root.iterdir()), [])
        result = self.first_apply()
        self.assertIn("project", result["changed"])
        stack = (SKILL / "assets/technical-stack.md").read_text().strip()
        self.assertIn(stack, (self.root / "AGENTS.md").read_text())
        checked = self.setup("check")
        self.assertTrue(checked["ready"])
        self.assertEqual(checked["ci_alignment"], "pending")
        self.assertFalse((self.root / ".github").exists())
        self.assertIn("setup:ci-discovery", (self.root / "SETUP-TODO.md").read_text())
        self.assertIn("app_commands=0", self.cli("doctor").stdout)
        self.assertTrue((self.root / "SETUP-TODO.md").is_file())
        self.assertEqual(self.cli("unknown").returncode, 2)
        before = self.snapshot()
        self.assertEqual(self.setup()["changed"], [])
        self.assertEqual(self.snapshot(), before)

    def test_existing_project_preserves_content_and_real_process_contract(self):
        original = "# Product\n\nNever change the signed protocol.\n"
        (self.root / "AGENTS.md").write_text(original)
        (self.root / "README.md").write_text("Owner-written documentation.\n")
        (self.root / "package.json").write_text(json.dumps({
            "name": "example", "packageManager": "npm@10.0.0", "scripts": {"test": "unused"},
        }))
        self.first_apply()
        self.assertTrue((self.root / "AGENTS.md").read_text().startswith(original))
        self.assertEqual((self.root / "README.md").read_text(), "Owner-written documentation.\n")
        binary = Path(self.temp.name) / "bin"
        binary.mkdir()
        shim = binary / "npm"
        shim.write_text("#!/usr/bin/env python3\nimport json,os,sys\n"
                        "print(json.dumps({'args':sys.argv[1:], 'cwd':os.getcwd()}))\n"
                        "sys.exit(0 if sys.argv[1:] == ['--version'] else 23)\n")
        shim.chmod(0o755)
        env = {**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"]}
        result = self.cli("test", "two words", "$(touch SHOULD_NOT_EXIST)", env=env)
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertEqual(json.loads(result.stdout), {
            "args": ["run", "test", "--", "two words", "$(touch SHOULD_NOT_EXIST)"],
            "cwd": str(self.root.resolve()),
        })
        self.assertFalse((self.root / "SHOULD_NOT_EXIST").exists())
        self.assertEqual(self.cli("test", "--help", env=env).returncode, 0)
        self.assertTrue(self.setup("check", env=env)["ready"])
        shim.write_text("#!/bin/sh\nexit 1\n")
        self.assertFalse(self.setup("check", ok=False, env=env)["ready"])
        self.assertEqual(self.setup()["changed"], [])

    def test_pnpm_default_and_existing_lockfile_choices(self):
        package = self.root / "package.json"
        package.write_text(json.dumps({"scripts": {"test": "unused"}}))
        route = self.setup("inspect")["routes"][0]
        self.assertEqual((route["program"], route["args"]), ("pnpm", ["run", "test"]))
        self.first_apply()
        binary = Path(self.temp.name) / "bin"
        binary.mkdir()
        shim = binary / "pnpm"
        shim.write_text("#!/usr/bin/env python3\nimport json,sys\n"
                        "print(json.dumps(sys.argv[1:]))\nsys.exit(19)\n")
        shim.chmod(0o755)
        env = {**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"]}
        result = self.cli("test", "two words", env=env)
        self.assertEqual(result.returncode, 19, result.stderr)
        self.assertEqual(json.loads(result.stdout), ["run", "test", "two words"])
        for lock, manager in (("package-lock.json", "npm"), ("yarn.lock", "yarn"),
                              ("bun.lock", "bun"), ("pnpm-lock.yaml", "pnpm")):
            with self.subTest(lock=lock):
                path = self.root / lock
                path.write_text("{}\n")
                self.assertEqual(self.setup("inspect")["routes"][0]["program"], manager)
                path.unlink()

    def test_owned_old_instructions_upgrade_without_changing_product(self):
        self.first_apply()
        agents = self.root / "AGENTS.md"
        old = ("<!-- scwlkr-project-setup:start -->\n## Project standards\n\n"
               f"Project: {self.root.name}. Linear team **Example**, project {PROJECT}.\n"
               "Prefer Rust backends and TypeScript/React web frontends.\n"
               "<!-- scwlkr-project-setup:end -->")
        owner = "# Owner\n\nKeep the existing Swift app until its migration is scheduled.\n\n"
        agents.write_text(owner + old + "\n\nOwner footer.\n")
        state_path = self.root / "tools/project-cli/setup.json"
        state = json.loads(state_path.read_text())
        state["hashes"]["agent_block"] = hashlib.sha256(old.encode()).hexdigest()
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        product = self.root / "App.swift"
        product.write_text("// Existing product source.\n")
        result = self.setup()
        self.assertEqual(set(result["changed"]), {"AGENTS.md", "tools/project-cli/setup.json"})
        stack = (SKILL / "assets/technical-stack.md").read_text().strip()
        self.assertIn(stack, agents.read_text())
        self.assertTrue(agents.read_text().startswith(owner))
        self.assertTrue(agents.read_text().endswith("\n\nOwner footer.\n"))
        self.assertEqual(product.read_text(), "// Existing product source.\n")
        before = self.snapshot()
        self.assertEqual(self.setup()["changed"], [])
        self.assertEqual(self.snapshot(), before)

    def test_existing_rust_app_runs_through_cli(self):
        (self.root / "Cargo.toml").write_text('[package]\nname="fixture-app"\nversion="0.1.0"\nedition="2021"\n[workspace]\n')
        (self.root / "src").mkdir()
        (self.root / "src/main.rs").write_text('fn main() { println!("{}", std::env::args().nth(1).unwrap()); }\n')
        self.first_apply()
        result = self.cli("run", "real app behavior")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "real app behavior")
        self.assertEqual(self.setup()["changed"], [])

    def test_customizations_survive(self):
        self.first_apply()
        routes = self.root / "tools/project-cli/src/routes.rs"
        routes.write_text(routes.read_text() + "\n// Owner extension point.\n")
        agents = self.root / "AGENTS.md"
        agents.write_text(agents.read_text().replace("## Project standards", "## Project standards\n\nOwner-specific guidance."))
        before = self.snapshot()
        result = self.setup()
        self.assertIn("tools/project-cli/src/routes.rs", result["preserved"])
        self.assertIn("AGENTS.md setup block", result["preserved"])
        self.assertEqual(self.snapshot(), before)

    def test_readiness_requires_cli_examples_except_explicit_bootstrap(self):
        self.first_apply()
        agents = self.root / "AGENTS.md"
        managed = agents.read_text()
        old = ("## Verification\nRun `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, "
               "and `cargo test`.\n```sh\nCARGO_NET_OFFLINE=true cargo xtask verify\n```\n")
        agents.write_text(old + managed)
        result = self.setup("check", ok=False)
        self.assertFalse(result["ready"])
        self.assertEqual({item["line"] for item in result["command_conflicts"]}, {2, 4})
        self.assertEqual(len(self.setup("inspect")["command_conflicts"]), 4)
        repaired = old.replace("cargo fmt --check", "./project fmt").replace("cargo ", "./project ")
        bootstrap = "## CLI bootstrap\n```sh\ncargo build --manifest-path tools/project-cli/Cargo.toml\n```\n"
        agents.write_text(repaired + bootstrap + managed)
        self.assertTrue(self.setup("check")["ready"])
        agents.write_text(bootstrap + "## Normal work\nRun `cargo test`.\n" + managed)
        self.assertFalse(self.setup("check", ok=False)["ready"])

    def test_collisions_and_symlinks_do_not_partially_apply(self):
        (self.root / "project").write_text("unrelated file")
        before = self.snapshot()
        self.setup("apply", "--team", "Example", "--linear-project", PROJECT, ok=False)
        self.assertEqual(self.snapshot(), before)
        (self.root / "project").unlink()
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        (self.root / "tools").symlink_to(outside, target_is_directory=True)
        self.setup("apply", "--team", "Example", "--linear-project", PROJECT, ok=False)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.root / "AGENTS.md").exists())

    def test_ci_handoff_preserves_workflows_and_completed_owner_work(self):
        workflow = self.root / ".github/workflows/verify.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("name: CI\non: [pull_request]\njobs:\n  verify:\n    runs-on: ubuntu-latest\n"
                            "    steps:\n      - run: cargo test\n")
        original = workflow.read_bytes()
        todo = self.root / "SETUP-TODO.md"
        owner = "# Owner handoff\n\n- [x] Preserve the signed protocol.\n"
        todo.write_text(owner)
        ci = self.setup("inspect")["ci"]
        self.assertEqual({item["id"] for item in ci["todos"]}, {"ci-scope", "ci-cache", "ci-verify"})
        self.first_apply()
        self.assertEqual(workflow.read_bytes(), original)
        self.assertTrue(todo.read_text().startswith(owner))
        todo.write_text(todo.read_text().replace("- [ ] Separate", "- [x] Separate") + "\nOwner evidence retained.\n")
        before = self.snapshot()
        self.assertEqual(self.setup()["changed"], [])
        self.assertEqual(self.snapshot(), before)
        # A filtered/cached workflow is only a hint; required results still need verification.
        workflow.write_text("on:\n  pull_request:\n    paths: ['src/**']\njobs:\n  verify:\n"
                            "    steps:\n      - uses: actions/cache@v4\n      - run: cargo test\n")
        ci = self.setup("inspect")["ci"]
        self.assertEqual([item["id"] for item in ci["todos"]], ["ci-verify"])
        self.assertEqual(ci["alignment"], "pending")
        # One cached workflow cannot mask an expensive, unscoped sibling.
        (workflow.parent / "other.yml").write_bytes(original)
        ci = self.setup("inspect")["ci"]
        self.assertEqual({item["id"] for item in ci["todos"]}, {"ci-scope", "ci-cache", "ci-verify"})

    def test_ci_inspection_reports_unread_and_custom_provider_without_execution(self):
        workflow = self.root / ".github/workflows/large.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text("#" * 65537)
        ci = self.setup("inspect")["ci"]
        self.assertEqual(ci["unread"], [".github/workflows/large.yml"])
        self.assertEqual({item["id"] for item in ci["todos"]}, {"ci-review", "ci-verify"})
        workflow.unlink()
        (self.root / "Jenkinsfile").write_text("sh 'touch SHOULD_NOT_EXIST'\n")
        self.first_apply()
        self.assertFalse((self.root / "SHOULD_NOT_EXIST").exists())
        self.assertEqual(self.setup("inspect")["ci"]["files"][0]["file"], "Jenkinsfile")
        for number in range(33):
            (workflow.parent / f"{number}.yml").write_text("on: [pull_request]\n")
        ci = self.setup("inspect")["ci"]
        self.assertTrue(ci["truncated"])
        self.assertEqual(len(ci["files"]), 32)
        self.assertIn("ci-review", {item["id"] for item in ci["todos"]})


if __name__ == "__main__":
    unittest.main()
