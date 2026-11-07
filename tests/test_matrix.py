import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from plan_matrix import plan, LANGUAGES


class MatrixTests(unittest.TestCase):
    def test_six_platforms_and_nine_languages(self):
        result = plan()
        self.assertEqual(len(LANGUAGES), 9)
        self.assertEqual(len(result["include"]), 52)  # Swift Windows needs toolchain bootstrap
        self.assertEqual(len({j["target"] for j in result["include"]}), 6)

    def test_single(self):
        self.assertEqual(plan("rust", "windows-arm64")["include"][0]["runner"], "windows-11-arm")

    def test_swift_windows_not_misrepresented(self):
        with self.assertRaisesRegex(ValueError, "not bootstrapped"):
            plan("swift", "windows-x64")

    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError):
            plan("unknown", "all")
        with self.assertRaises(ValueError):
            plan("c", "unknown")


if __name__ == "__main__":
    unittest.main()
