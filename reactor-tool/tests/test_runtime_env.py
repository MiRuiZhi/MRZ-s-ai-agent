import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reactor_tool.config.env import load_reactor_tool_dotenv


class RuntimeEnvTest(unittest.TestCase):
    def test_should_not_load_parent_dotenv_when_service_dotenv_is_missing(self):
        with tempfile.TemporaryDirectory(prefix="reactor-tool-env-") as temp_dir:
            root = Path(temp_dir)
            service_root = root / "reactor-tool"
            service_root.mkdir()
            (root / ".env").write_text("FILE_SAVE_PATH=/app/skilloutput\n", encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                loaded = load_reactor_tool_dotenv(service_root=service_root)

                self.assertFalse(loaded)
                self.assertIsNone(os.getenv("FILE_SAVE_PATH"))

    def test_should_load_service_dotenv_when_present(self):
        with tempfile.TemporaryDirectory(prefix="reactor-tool-env-") as temp_dir:
            service_root = Path(temp_dir)
            (service_root / ".env").write_text("FILE_SAVE_PATH=file_db_dir\n", encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                loaded = load_reactor_tool_dotenv(service_root=service_root)

                self.assertTrue(loaded)
                self.assertEqual("file_db_dir", os.getenv("FILE_SAVE_PATH"))


if __name__ == "__main__":
    unittest.main()
