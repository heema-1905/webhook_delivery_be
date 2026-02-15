# Webhook Delivery System

## Overview

This project implements a robust **Webhook Delivery System** built with **FastAPI** and **MongoDB**. It provides reliable ingestion, delivery, and retry mechanisms for webhook events, designed to handle high throughput while ensuring idempotency, rate limiting, and failure recovery.

The system supports:

* HMAC-based request authentication
* Idempotency keys to prevent duplicate processing
* Retry logic with exponential backoff
* Rate-limiting per endpoint
* Real-time event status tracking

---

## Table of Contents

* [Features](#features)
* [Architecture](#architecture)
* [Getting Started](#getting-started)
* [Configuration](#configuration)
* [Running the System](#running-the-system)
* [Testing Webhooks](#testing-webhooks)
* [Retry & Rate Limiting](#retry--rate-limiting)
---

## Features

1. **Webhook Ingestion**

   * Receives webhook POST requests.
   * Validates HMAC signatures passed into the headers to ensure authenticity.
   * Stores events in MongoDB with initial status `RECEIVED`.

2. **Webhook Delivery Worker**

   * Processes queued events asynchronously.
   * Calls downstream receive URL endpoint.
   * Implements **retry logic** with exponential backoff if success response is not received after calling downstream URL.
   * Marks permanent failures after maximum retries.

3. **Rate Limiting**

   * Limits requests per second per downstream target to prevent overload.
   * Downstream receive URL enpoint is rate limited to 3 request/ sec


4. **Idempotency Handling**

   * Ensures duplicate events are not processed multiple times.

5. **Event Status Tracking**

   * Tracks `RECEIVED`, `FAILED_TEMPORARILY`, `FAILED_PERMANENTLY`, and `DELIVERED`.

---

## Architecture

```
 ┌───────────────────────┐
 │     Webhook Client     │
 └──────────┬────────────┘
            │ POST /webhook
            ▼
 ┌───────────────────────┐
 │  FastAPI Ingestion    │
 │   Endpoint           │
 └──────────┬────────────┘
            │ Validate HMAC
            | Validate idempotency
            │ Store in MongoDB
            ▼
 ┌───────────────────────┐
 │ Delivery Worker Queue │
 └──────────┬────────────┘
            │ Async Delivery
            │ Retry Logic
            ▼
 ┌───────────────────────┐
 │ Downstream Services   │
 └───────────────────────┘
```

* **MongoDB** stores the event payload, status, timestamps, and retry metadata.
* **FastAPI worker** handles delivery asynchronously using `asyncio` for high throughput.

---

## Getting Started

### Prerequisites

* Python 3.11+
* MongoDB 6.x
* `pip` for dependency management

### Installation

```bash
# 1. Create project folder
mkdir Webhook-Delivery-System
cd Webhook-Delivery-System

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# 3. Clone backend repository
git clone https://github.com/heema-1905/webhook-delivery-system.git webhook_delivery_be
cd webhook_delivery_be

# 4. Install dependencies
pip install -r requirements.txt
```

---

## Configuration

All sensitive settings are stored in `.env`:
* Refer .env.temp file and include all keys mentioned in that file in your .env.
* Assign appropriate values to your .env file.

---

## Running the System

### Start the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```



## Running the Delivery Worker Separately

To run the background delivery worker as a separate process:

```bash
python -m app.webhook_entry
````

* This allows the delivery worker to run independently from the API server.
* Useful for scaling delivery processing or isolating heavy delivery tasks.
* The worker continuously polls MongoDB for queued events and processes them asynchronously.

## Testing Webhooks

To test the webhook ingestion endpoint, send a `POST` request with valid HMAC authentication headers and timestamp.

> **Note:** For backend testing, generate the `X-Signature`, `X-Timestamp`, and `X-Idempotency-Key` using the `test_webhook_ingest_headers` utility located inside the `test_scripts` folder.

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/ingest \
  -H "Content-Type: application/json" \
  -H "X-Signature: <generated_hmac>" \
  -H "X-Timestamp: <current_timestamp>" \
  -H "X-Idempotency-Key: abc123" \
  -d '{
        "data": {
            "order_id": 123,
            "event_type": "order_created"
        }
      }'
```

### Important Notes

* `X-Signature` must be generated using the shared secret and request payload.
* `X-Timestamp` should be the current UTC timestamp.
* `X-Idempotency-Key` prevents duplicate event processing if the same request is sent multiple times.

---

## Concurrency Testing

To evaluate how the delivery worker behaves under concurrent load:

1. Navigate to the `test_scripts` directory.
2. Run the `test_webhook_ingest.py` script.
3. Adjust the request range inside the script to simulate multiple simultaneous webhook ingestion requests.

This allows you to:

* Test ingestion under concurrent traffic.
* Observe retry behavior and rate limiting.
* Validate that the delivery worker processes events reliably without duplication or race conditions.


## Retry & Rate Limiting

* Retry logic uses **exponential backoff**: each retry waits longer before the next attempt.
* Failed deliveries are marked `FAILED_TEMPORARILY` until `MAX_RETRY_ATTEMPTS` is reached.
* Permanent failures are marked `FAILED_PERMANENTLY`.
* Rate limiting ensures downstream services are not overwhelmed (default 3 req/sec).
