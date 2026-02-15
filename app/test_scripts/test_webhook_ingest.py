import asyncio
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY").encode()
WEBHOOK_URL = "http://localhost:8000/api/v1/webhooks/ingest"  # NOTE: Use your own webhook ingestion endpoint


# Creating the required headers and calling the webhook ingest endpoint for testing the webhook delivery task
async def send_webhook(i):
    payload = {"order_id": i}
    raw_body = json.dumps(payload).encode()
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    signature_payload = timestamp.encode() + b"." + raw_body
    signature = hmac.new(SECRET_KEY, signature_payload, hashlib.sha256).hexdigest()
    idempotency_key = str(uuid.uuid4())

    headers = {
        "Content-Type": "application/json",
        "x-timestamp": timestamp,
        "x-signature": signature,
        "Idempotency-Key": idempotency_key,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(WEBHOOK_URL, headers=headers, content=raw_body)
        print(f"[Order {i}] Status: {resp.status_code}, Response: {resp.text}")


async def main():
    # Calling the no. of requests mentioned in loop range concurrently
    tasks = [send_webhook(i) for i in range(1, 6)]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
