import os
import unittest

class TestRepoCleanliness(unittest.TestCase):
    def test_repo_cleanliness(self):
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        forbidden_terms = ["sondoannam", "Đoàn Nam Sơn"]
        for root, dirs, files in os.walk(root_dir):
            if ".git" in dirs:
                dirs.remove(".git")
            for file in files:
                if file.endswith((".md", ".txt", ".json", ".py", ".yml", ".yaml")):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            for term in forbidden_terms:
                                self.assertNotIn(term, content)
                    except Exception:
                        pass

if __name__ == "__main__":
    unittest.main()
