import json
import threading
import unittest
import urllib.request

from app import make_server


class AppTest(unittest.TestCase):
    def test_health(self):
        server = make_server(0)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health", timeout=5
            ) as res:
                self.assertEqual(res.status, 200)
                self.assertEqual(json.loads(res.read()), {"ok": True})
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
