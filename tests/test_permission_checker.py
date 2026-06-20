import os
import tempfile
import unittest
from pathlib import Path

from safety.permission_checker import PermissionChecker


class PermissionCheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self.checker = PermissionChecker(self.workspace)

    def tearDown(self):
        self.temp.cleanup()

    def test_allows_normal_workspace_file(self):
        self.assertEqual(
            self.checker.check_path(Path("README.md")),
            (True, "allowed"),
        )

    def test_denies_required_sensitive_patterns(self):
        denied = [
            ".env",
            ".env.local",
            "private.key",
            "config.secret.json",
            "aws_credentials",
            "database_password.txt",
            ".ssh/id_rsa",
            ".gnupg/private-keys-v1.d/key",
            "certificate.pem",
            "client.crt",
            "bundle.p12",
        ]

        for path in denied:
            with self.subTest(path=path):
                allowed, reason = self.checker.check_path(Path(path))
                self.assertFalse(allowed)
                self.assertIn("禁止", reason)

    def test_denies_traversal_and_absolute_external_paths(self):
        self.assertFalse(self.checker.check_path(Path("../.env"))[0])
        outside = self.workspace.parent / "outside.txt"
        self.assertFalse(self.checker.check_path(outside)[0])

    def test_denies_symlink_that_resolves_outside_workspace(self):
        outside = self.workspace.parent / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        link = self.workspace / "linked.txt"
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable in this environment")

        self.assertFalse(self.checker.check_path(Path("linked.txt"))[0])
