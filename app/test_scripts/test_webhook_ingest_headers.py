import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

# Test script for generating the headers for manually testing the webhook ingestion endpoint

load_dotenv()

# MUST match settings.SECRET_KEY in your FastAPI app
SECRET_KEY = os.getenv("SECRET_KEY").encode()

# Example payload (this will be sent as raw body)
payload = {"event_type": None, "user_id": "12345", "amount": 600}

# Convert to raw bytes EXACTLY how it will be sent
raw_body = json.dumps(payload).encode()

# Generate timestamp (ISO 8601, UTC)
timestamp = datetime.now(tz=timezone.utc).isoformat()

# Construct signature payload exactly like your backend:
# x_timestamp.encode() + b"." + raw_body
signature_payload = timestamp.encode() + b"." + raw_body

idempotency_key = str(uuid.uuid4())
# Generate HMAC SHA256
signature = hmac.new(
    key=SECRET_KEY, msg=signature_payload, digestmod=hashlib.sha256
).hexdigest()

print("\n=== HEADERS TO USE ===")
print("Idempotency-Key:", idempotency_key)
print("x-timestamp:", timestamp)
print("x-signature:", signature)

print("\n=== RAW BODY TO SEND ===")
print(raw_body.decode())
