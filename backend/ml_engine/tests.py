import unittest
from ml_engine.adaptive_engine import adjust_difficulty


class AdaptiveEngineTests(unittest.TestCase):
    def test_adjust_difficulty(self):
        self.assertEqual(adjust_difficulty(0.9, "Easy"), "Medium")
        self.assertEqual(adjust_difficulty(0.3, "Hard"), "Medium")
        self.assertEqual(adjust_difficulty(0.7, "Medium"), "Medium")


if __name__ == "__main__":
    unittest.main()
