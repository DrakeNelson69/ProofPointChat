import os
import re
from typing import Optional, Tuple, Union

import requests
from flask import Flask, Response, jsonify, request

app = Flask(__name__)

# Replace this placeholder (or set POWER_AUTOMATE_URL env var) with your real Power Automate HTTP URL.
POWER_AUTOMATE_URL = os.getenv(
    "POWER_AUTOMATE_URL", ""
).strip()


def parse_product_name(user_input: str) -> Optional[str]:
    """Extract a product name from a natural-language user question."""
    if not user_input:
        return None

    cleaned = " ".join(user_input.strip().split())
    lowered = cleaned.lower()

    def extract_after(marker: str) -> Optional[str]:
        marker_index = lowered.find(marker)
        if marker_index == -1:
            return None
        candidate = cleaned[marker_index + len(marker) :]
        candidate = re.split(r"[?.!]", candidate, maxsplit=1)[0].strip()
        return candidate or None

    for marker in (
        "latest proof point for ",
        "latest proof point about ",
        "proof points for ",
        "proof points about ",
        "proof point for ",
        "proof point about ",
    ):
        product = extract_after(marker)
        if product:
            return product

    if "proof point" in lowered or "proof points" in lowered:
        for marker in ("for ", "about "):
            product = extract_after(marker)
            if product:
                return product

    # Matches product names beginning with "product " where the name starts alphanumeric
    # and may include spaces, hyphens, underscores, slashes, and ampersands.
    product_match = re.search(r"\bproduct\s+[A-Za-z0-9][A-Za-z0-9\s\-_/&]*", cleaned, re.I)
    if product_match:
        return product_match.group(0).strip().rstrip(".,!?;:")

    return None


def call_power_automate(product_name: str) -> Tuple[Optional[dict], Optional[str]]:
    """Send the product to Power Automate and return (response_json, error_message)."""
    if not POWER_AUTOMATE_URL:
        return None, "the Power Automate endpoint URL is not configured yet"

    payload = {"product": product_name}

    try:
        response = requests.post(POWER_AUTOMATE_URL, json=payload, timeout=15)
    except requests.RequestException:
        return None, "I couldn't reach the proof point service"

    if not response.ok:
        return (
            None,
            f"the proof point service returned an error ({response.status_code})",
        )

    try:
        return response.json(), None
    except ValueError:
        return None, "the proof point service returned invalid JSON"


def format_user_reply(power_automate_response: dict, product_name: str) -> str:
    """Turn Power Automate JSON into a friendly chatbot reply."""
    status = power_automate_response.get("status")
    product = power_automate_response.get("product", product_name)

    if status:
        return f"Great news — I found an update for {product}: {status}."

    return f"I found a response for {product}, but it did not include a status message."


def handle_user_question(user_message: str) -> str:
    """Main chatbot flow: parse, call endpoint, format response."""
    product_name = parse_product_name(user_message)
    if not product_name:
        return (
            "I couldn't determine the product name. "
            "Please ask like: 'What's the latest proof point for Product X?'"
        )

    power_automate_response, error = call_power_automate(product_name)
    if error:
        return f"Sorry, {error}. Please try again in a moment."

    return format_user_reply(power_automate_response, product_name)


@app.post("/chat")
def chat() -> Union[Response, Tuple[Response, int]]:
    """Simple chatbot API endpoint: POST {"message": "..."}."""
    body = request.get_json(silent=True)
    if body is None and request.data:
        return (
            jsonify({"reply": "Invalid JSON payload. Please send valid JSON with a 'message' field."}),
            400,
        )

    body = body or {}
    user_message = body.get("message", "")
    reply = handle_user_question(user_message)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    # Run locally with: python app.py
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=debug_mode)
