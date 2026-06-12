import unittest
from unittest.mock import patch

from agent_api.api.app import create_app
from agent_api.settings import Settings


class AppSettingsTest(unittest.TestCase):
    def test_create_app_rejects_wildcard_cors_in_production(self):
        settings = Settings(environment="production", cors_origins=["*"])

        with patch("agent_api.api.app.get_settings", return_value=settings):
            with self.assertRaisesRegex(ValueError, "CORS wildcard"):
                create_app()


if __name__ == "__main__":
    unittest.main()
