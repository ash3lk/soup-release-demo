import os
import subprocess
import unittest


class CliTests(unittest.TestCase):
    def test_hello(self):
        result = subprocess.run(
            ["soup-demo", "hello"],
            env={**os.environ, "LOGNAME": "ci-user"},
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Hello, ci-user!")

    def test_show_config(self):
        result = subprocess.run(
            ["soup-demo", "show-config"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), '{"language": "en"}')
