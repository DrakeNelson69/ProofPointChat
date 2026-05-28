# ProofPointChat
Payment Proof Point Tracker Chat bot

## Basic Python chatbot example

This repository now includes a minimal Flask chatbot in `/app.py` that:
- Parses a user question to find a product name
- Sends `POST` JSON to a Power Automate HTTP endpoint
- Formats a friendly response for the user
- Handles endpoint errors gracefully

### Setup

```bash
pip install -r requirements.txt
python app.py
```

### Configure Power Automate URL

Set your real endpoint before running:

```bash
export POWER_AUTOMATE_URL="https://your-power-automate-endpoint"
```

### Test the chatbot endpoint

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is the latest proof point for Product X?"}'
```

### Run focused tests

```bash
python -m unittest -v
```
