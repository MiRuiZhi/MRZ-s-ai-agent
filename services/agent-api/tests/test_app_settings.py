import unittest
import os
import tempfile
from unittest.mock import patch

from agent_api.api.app import create_app
from agent_api.settings import Settings


class AppSettingsTest(unittest.TestCase):
    def test_settings_accepts_agent_runtime_flags_and_ignores_other_service_dotenv_values(self):
        with tempfile.TemporaryDirectory(prefix="agent-settings-") as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                with open(".env", "w", encoding="utf-8") as env_file:
                    env_file.write(
                        "\n".join(
                            [
                                "REACTOR_FAKE_LLM=true",
                                "REACTOR_RUN_MIGRATIONS=false",
                                "REACTOR_RUN_SEED=false",
                                "FILE_SAVE_PATH=/app/skilloutput",
                                "USE_SEARCH_ENGINE=ddg",
                            ]
                        )
                    )

                settings = Settings()

                self.assertTrue(settings.fake_llm)
                self.assertFalse(settings.run_migrations)
                self.assertFalse(settings.run_seed)
            finally:
                os.chdir(original_cwd)

    def test_create_app_rejects_wildcard_cors_in_production(self):
        settings = Settings(environment="production", cors_origins=["*"])

        with patch("agent_api.api.app.get_settings", return_value=settings):
            with self.assertRaisesRegex(ValueError, "CORS wildcard"):
                create_app()


if __name__ == "__main__":
    unittest.main()
