import unittest

from app.services import chat_service


class ChatServiceFormattingTest(unittest.TestCase):
    def test_sanitize_answer_removes_markdown_bullets_and_commas(self):
        raw = "* First item, second item\n* Another item, final item"

        self.assertEqual(
            chat_service.sanitize_answer(raw),
            "First item second item\nAnother item final item",
        )


if __name__ == "__main__":
    unittest.main()
