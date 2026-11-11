import os
import subprocess
import unittest


class CliTests(unittest.TestCase):
    def test_hello(self):
        result = subprocess.run(
            ["soup-demo", "hello"],
            env={**os.environ, "LOGNAME": "ci-user"},
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Hello, ci-user!")
