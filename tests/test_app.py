import unittest
from unittest.mock import Mock, patch

import app


class TestProofPointChatbot(unittest.TestCase):
    def test_parse_product_name(self):
        question = "What's the latest proof point for Product X?"
        self.assertEqual(app.parse_product_name(question), "Product X")

    def test_parse_product_name_missing(self):
        question = "What's new today?"
        self.assertIsNone(app.parse_product_name(question))

    def test_format_user_reply(self):
        response = {"status": "Row inserted", "product": "Product X"}
        reply = app.format_user_reply(response, "Product X")
        self.assertIn("Product X", reply)
        self.assertIn("Row inserted", reply)

    @patch("app.requests.post")
    def test_call_power_automate_success(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "Row inserted", "product": "Product X"}
        mock_post.return_value = mock_response

        data, error = app.call_power_automate("Product X")

        self.assertIsNone(error)
        self.assertEqual(data["status"], "Row inserted")
        mock_post.assert_called_once()

    @patch("app.requests.post")
    def test_call_power_automate_error(self, mock_post):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        data, error = app.call_power_automate("Product X")

        self.assertIsNone(data)
        self.assertIn("error (500)", error)


if __name__ == "__main__":
    unittest.main()
