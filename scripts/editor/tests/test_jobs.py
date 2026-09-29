"""core.jobs: one job at a time, streamed subprocess output, exit codes."""

import sys
import time
import unittest
from pathlib import Path

from _helpers import TempRepo  # noqa: F401  (puts the editor dir on sys.path)
from core.jobs import JobRunner, python_exe, run_subprocess


def wait(runner: JobRunner, seconds: float = 10.0) -> dict:
    deadline = time.monotonic() + seconds
    while runner.busy() and time.monotonic() < deadline:
        time.sleep(0.02)
    return runner.json()


class JobRunnerTests(unittest.TestCase):
    def test_runs_one_job_at_a_time_and_records_result(self):
        r = JobRunner()
        gate = []

        def slow(runner):
            runner.log_line("hello")
            while not gate:
                time.sleep(0.01)
            return {"answer": 42}

        job = r.start("demo", slow, extra="x")
        self.assertTrue(job["running"] and job["extra"] == "x")
        with self.assertRaises(RuntimeError):
            r.start("demo", slow)
        gate.append(1)
        j = wait(r)
        self.assertFalse(j["running"])
        self.assertEqual(j["result"], {"answer": 42})
        self.assertIsNone(j["error"])
        self.assertTrue(j["log"][0].endswith("hello"))
        # a crash is reported, not raised
        r.start("boom", lambda runner: 1 / 0)
        j = wait(r)
        self.assertIn("ZeroDivisionError", j["error"])
        self.assertTrue(any("FAILED" in line for line in j["log"]))

    def test_subprocess_output_streams_in_order(self):
        lines = []
        code = run_subprocess(
            [python_exe(), "-c", "import sys; print('one'); print('two', file=sys.stderr); print('tres ñ'); sys.exit(3)"],
            Path.cwd(),
            lines.append,
        )
        self.assertEqual(code, 3)
        body = [l for l in lines if not l.startswith("$ ")]
        self.assertEqual(body[:3], ["one", "two", "tres ñ"])
        self.assertEqual(body[-1], "exit code 3")

    def test_python_exe_is_a_console_interpreter(self):
        exe = python_exe()
        self.assertTrue(Path(exe).is_file())
        self.assertNotEqual(Path(exe).name.lower(), "pythonw.exe")
        self.assertEqual(Path(exe).parent, Path(sys.executable).parent)


if __name__ == "__main__":
    unittest.main()
