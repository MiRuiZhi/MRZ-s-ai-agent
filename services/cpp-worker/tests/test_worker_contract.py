import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class CppWorkerContractTest(unittest.TestCase):
    def _compile_worker(self, tmp_path: Path) -> Path:
        repo_root = Path(__file__).resolve().parents[3]
        source = repo_root / "services" / "cpp-worker" / "src" / "main.cpp"
        binary = tmp_path / "reactor_cpp_worker"
        subprocess.run(
            ["g++", "-std=c++17", "-O2", str(source), "-o", str(binary)],
            check=True,
        )
        return binary

    def test_worker_executes_command_and_reports_generated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            binary = self._compile_worker(tmp_path)
            workspace = tmp_path / "workspace"
            workspace.mkdir()
            payload = {
                "command": "python3 -c \"from pathlib import Path; Path('result.txt').write_text('hello')\"",
                "cwd": str(workspace),
                "timeoutSeconds": 10,
                "collectFiles": True,
            }
            proc = subprocess.run(
                [str(binary)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
            )

        response = json.loads(proc.stdout)
        self.assertTrue(response["success"])
        self.assertEqual(response["exitCode"], 0)
        self.assertEqual(response["files"][0]["name"], "result.txt")
        self.assertEqual(response["files"][0]["sha256"], "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")

    def test_worker_rejects_cwd_outside_configured_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            binary = self._compile_worker(tmp_path)
            allowed = tmp_path / "allowed"
            denied = tmp_path / "denied"
            allowed.mkdir()
            denied.mkdir()
            payload = {
                "command": "echo nope",
                "cwd": str(denied),
                "timeoutSeconds": 10,
                "collectFiles": False,
            }
            env = dict(os.environ, CPP_WORKER_ROOT=str(allowed))
            proc = subprocess.run(
                [str(binary)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
            )

        response = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse(response["success"])
        self.assertIn("outside CPP_WORKER_ROOT", response["stderr"])


if __name__ == "__main__":
    unittest.main()
