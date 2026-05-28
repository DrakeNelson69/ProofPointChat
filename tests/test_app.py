import unittest
from json import JSONDecodeError
from unittest.mock import Mock, patch

import app


class TestProofPointChatbot(unittest.TestCase):
    def setUp(self):
        self.original_power_automate_url = app.POWER_AUTOMATE_URL
        app.POWER_AUTOMATE_URL = "https://example.com/power-automate"

    def tearDown(self):
        app.POWER_AUTOMATE_URL = self.original_power_automate_url

    def test_parse_product_name(self):
        question = "What's the latest proof point for Product X?"
        self.assertEqual(app.parse_product_name(question), "Product X")

    def test_parse_product_name_missing(self):
        question = "What's new today?"
        self.assertIsNone(app.parse_product_name(question))

    def test_parse_product_name_with_special_characters(self):
        question = "Can you share proof points about Product A/B-1 & Co.?"
        self.assertEqual(app.parse_product_name(question), "Product A/B-1 & Co")

    def test_parse_product_name_trailing_punctuation_trimmed(self):
        question = "Tell me about product Alpha-1!?"
        self.assertEqual(app.parse_product_name(question), "product Alpha-1")

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
        mock_post.assert_called_once_with(
            app.POWER_AUTOMATE_URL, json={"product": "Product X"}, timeout=15
        )

    @patch("app.requests.post")
    def test_call_power_automate_error(self, mock_post):
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        data, error = app.call_power_automate("Product X")

        self.assertIsNone(data)
        self.assertIn("error (500)", error)

    def test_call_power_automate_missing_endpoint(self):
        app.POWER_AUTOMATE_URL = ""

        data, error = app.call_power_automate("Product X")

        self.assertIsNone(data)
        self.assertIn("not configured", error)

    @patch("app.requests.post")
    def test_call_power_automate_request_exception(self, mock_post):
        mock_post.side_effect = app.requests.RequestException("network down")

        data, error = app.call_power_automate("Product X")

        self.assertIsNone(data)
        self.assertIn("couldn't reach", error)

    @patch("app.requests.post")
    def test_call_power_automate_invalid_json(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = JSONDecodeError("not json", "response_body", 0)
        mock_post.return_value = mock_response

        data, error = app.call_power_automate("Product X")

        self.assertIsNone(data)
        self.assertIn("invalid JSON", error)

    @patch("app.call_power_automate")
    def test_handle_user_question_success(self, mock_call):
        mock_call.return_value = (
            {"status": "Row inserted", "product": "Product X"},
            None,
        )

        reply = app.handle_user_question("What's the latest proof point for Product X?")

        self.assertIn("Product X", reply)
        self.assertIn("Row inserted", reply)

    def test_handle_user_question_missing_product(self):
        reply = app.handle_user_question("Can you help me?")
        self.assertIn("couldn't determine the product name", reply)

    @patch("app.call_power_automate")
    def test_chat_endpoint(self, mock_call):
        mock_call.return_value = (
            {"status": "Row inserted", "product": "Product X"},
            None,
        )
        with app.app.test_client() as client:
            response = client.post(
                "/chat", json={"message": "What's the latest proof point for Product X?"}
            )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertIn("reply", body)
        self.assertIn("Product X", body["reply"])

    def test_chat_endpoint_invalid_json(self):
        with app.app.test_client() as client:
            response = client.post(
                "/chat", data="{invalid", headers={"Content-Type": "application/json"}
            )

        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertIn("Invalid JSON payload", body["reply"])

    def test_chat_endpoint_empty_message(self):
        with app.app.test_client() as client:
            response = client.post("/chat", json={"message": ""})

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertIn("couldn't determine the product name", body["reply"])


if __name__ == "__main__":
    unittest.main()
