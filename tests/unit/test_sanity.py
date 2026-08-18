import unittest
from pathlib import Path


class SanityTest(unittest.TestCase):
    def test_versions_env_has_no_placeholders(self):
        text = Path("config/versions.env").read_text()
        self.assertNotIn("<tag>", text)
        self.assertNotIn("<version>", text)


if __name__ == "__main__":
    unittest.main()
