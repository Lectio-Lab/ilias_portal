import http.client
import tempfile
import threading
import unittest
from pathlib import Path

from http.server import ThreadingHTTPServer

from server import PortalHandler
from state import StateStore


class LocalServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), PortalHandler)
        self.httpd.token = "a" * 48
        self.httpd.state = StateStore(Path(self.temporary.name) / "ilias-state.json")
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.thread.join()
        self.httpd.server_close()
        self.temporary.cleanup()

    def request(self, path, token=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port)
        headers = {} if token is None else {"Authorization": f"Bearer {token}"}
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response.status, body

    def test_health_is_loopback_service_readiness_probe(self):
        status, body = self.request("/healthz")
        self.assertEqual(status, 200)
        self.assertIn(b'"status": "ok"', body)

    def test_rejects_missing_or_wrong_local_token(self):
        self.assertEqual(self.request("/api/ilias/courses/")[0], 401)
        self.assertEqual(self.request("/api/ilias/courses/", "wrong")[0], 401)

    def test_lists_empty_cache_with_valid_local_token(self):
        status, body = self.request("/api/ilias/courses/", "a" * 48)
        self.assertEqual(status, 200)
        self.assertIn(b'"courses": []', body)
