import os
import re
from typing import Optional, Tuple

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Replace this placeholder (or set POWER_AUTOMATE_URL env var) with your real Power Automate HTTP URL.
POWER_AUTOMATE_URL = os.getenv(
    "POWER_AUTOMATE_URL", "https://YOUR_POWER_AUTOMATE_ENDPOINT_URL_HERE"
)


def parse_product_name(user_input: str) -> Optional[str]:
    """Extract a product name from a natural-language user question."""
    if not user_input:
        return None

    cleaned = " ".join(user_input.strip().split())

    patterns = [
        r"(?:proof\s*point(?:s)?|latest\s+proof\s*point)\s+(?:for|about)\s+([A-Za-z0-9][A-Za-z0-9\s\-_/&]+?)(?:[?.!]|$)",
        r"(?:for|about)\s+([A-Za-z0-9][A-Za-z0-9\s\-_/&]+?)(?:[?.!]|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    fallback = re.search(
        r"(product\s+[A-Za-z0-9][A-Za-z0-9\s\-_/&]+?)(?:[?.!]|$)",
        cleaned,
        flags=re.IGNORECASE,
    )
    if fallback:
        return fallback.group(1).strip()

    return None


def call_power_automate(product_name: str) -> Tuple[Optional[dict], Optional[str]]:
    """Send the product to Power Automate and return (response_json, error_message)."""
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
def chat() -> tuple:
    """Simple chatbot API endpoint: POST {"message": "..."}."""
    body = request.get_json(silent=True) or {}
    user_message = body.get("message", "")
    reply = handle_user_question(user_message)
    return jsonify({"reply": reply})


if __name__ == "__main__":
    # Run locally with: python app.py
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
