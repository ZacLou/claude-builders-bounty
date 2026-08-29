#!/usr/bin/env python3
"""Unit tests for pre-tool-use.py destructive-command blocker."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).with_name("pre-tool-use.py").resolve()


class TestPreToolUseHook(unittest.TestCase):
    def run_hook(self, command: str, tool_name: str = "Bash") -> subprocess.CompletedProcess:
        payload = json.dumps({"tool_name": tool_name, "tool_input": {"command": command}})
        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = "/tmp/test-project"
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=payload,
            text=True,
            capture_output=True,
            env=env,
        )

    def assert_blocked(self, command: str) -> None:
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 2, f"Expected block for: {command}\n{result.stderr}")
        self.assertIn("BLOCKED", result.stderr)

    def assert_allowed(self, command: str) -> None:
        result = self.run_hook(command)
        self.assertEqual(result.returncode, 0, f"Expected allow for: {command}\n{result.stderr}")

    def test_blocks_rm_rf(self):
        self.assert_blocked("rm -rf /tmp/data")
        self.assert_blocked("rm -fr /tmp/data")
        self.assert_blocked("rm -r -f /tmp/data")

    def test_blocks_force_push(self):
        self.assert_blocked("git push --force origin main")
        self.assert_blocked("git push -f origin main")

    def test_allows_force_with_lease(self):
        self.assert_allowed("git push --force-with-lease origin main")

    def test_allows_normal_push(self):
        self.assert_allowed("git push origin main")

    def test_blocks_drop_table(self):
        self.assert_blocked("DROP TABLE users;")
        self.assert_blocked("drop table if exists logs;")

    def test_blocks_truncate_table(self):
        self.assert_blocked("TRUNCATE TABLE logs;")

    def test_blocks_unqualified_delete(self):
        self.assert_blocked("DELETE FROM sessions;")

    def test_allows_qualified_delete(self):
        self.assert_allowed("DELETE FROM sessions WHERE id = 1;")

    def test_blocks_disk_overwrite(self):
        self.assert_blocked("dd if=/dev/zero of=/dev/sda bs=1M")
        self.assert_blocked("mkfs.ext4 /dev/sda1")

    def test_allows_safe_dd(self):
        # dd to a regular file is fine.
        self.assert_allowed("dd if=/dev/zero of=image.iso bs=1M count=100")

    def test_allows_normal_commands(self):
        self.assert_allowed("ls -la")
        self.assert_allowed("rm /tmp/old.txt")
        self.assert_allowed("npm run build")

    def test_ignores_non_bash_tools(self):
        result = self.run_hook("rm -rf /", tool_name="Edit")
        self.assertEqual(result.returncode, 0)

    def test_log_written(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / ".claude" / "hooks" / "blocked.log"
            payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/data"}})
            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = "/tmp/test-project"
            subprocess.run(
                [sys.executable, str(HOOK)],
                input=payload,
                text=True,
                capture_output=True,
                env={**env, "HOME": tmpdir},
            )
            self.assertTrue(log_path.exists())
            self.assertIn("rm-rf", log_path.read_text())


if __name__ == "__main__":
    unittest.main()
