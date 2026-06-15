import unittest

from server import create_app


class MainlineRoutesTest(unittest.TestCase):
    def test_should_register_python_tool_runtime_mainline_routes(self):
        app = create_app()
        route_paths = {getattr(route, "path", "") for route in app.routes}

        expected_paths = {
            "/v1/tool/code_interpreter",
            "/v1/tool/image_generation",
            "/v1/tool/web_fetch",
            "/v1/tool/mragQuery",
            "/v1/file_tool/upload_file_data",
            "/v1/file_tool/preview/{file_id}/{file_name:path}",
            "/v1/documents/list_knowledge_base",
        }
        self.assertTrue(
            expected_paths.issubset(route_paths),
            f"missing routes: {sorted(expected_paths - route_paths)}",
        )

    def test_should_initialize_runtime_database_on_startup(self):
        app = create_app()
        startup_names = {
            getattr(handler, "__name__", "")
            for handler in app.router.on_startup
        }

        self.assertIn("init_runtime_database", startup_names)


if __name__ == "__main__":
    unittest.main()
