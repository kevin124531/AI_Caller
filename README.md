# AI Caller — Automated Survey Calling System

A fully automated weekly survey calling system that uses **Retell AI** voice agents to call contacts, conduct adaptive surveys, store transcripts, and export fine-tuning data for **Qwen / LLaMA** models.

---

## Architecture Overview

```
Weekly Scheduler (APScheduler cron)
        ↓
Contact CSV  →  Retell AI Batch Call  →  Voice Agent (LLM-powered)
                                                  ↓
                                         Webhook Receiver  →  PostgreSQL + S3
                                                  ↓
                                    Transcript Processor + Auto-Scorer
                                                  ↓
                                    JSONL Export  →  Fine-tuning Pipeline
```

**Flow:**
1. Cron fires on a schedule (default: Monday 9 AM)
2. Contacts loaded from CSV → batch call dispatched to Retell AI
3. Retell voice agent runs adaptive survey with each contact
4. `call_ended` webhook POSTs transcript + metadata to this server
5. Transcript parsed, scored, and saved to PostgreSQL (raw JSON to S3)
6. Export script converts transcripts to ShareGPT JSONL for fine-tuning

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Scheduling | APScheduler (async cron) |
| Database | PostgreSQL + SQLAlchemy async (asyncpg) |
| HTTP client | httpx (async) |
| Voice AI | Retell AI (batch calls + webhook) |
| Cloud storage | AWS S3 (optional backup) |
| Sentiment scoring | VADER (vaderSentiment) |
| Config | Pydantic Settings |
| Training format | ShareGPT JSONL |
| Testing | pytest + pytest-asyncio + moto |

---

## Project Structure

```
AI_Caller/
├── main.py                    # FastAPI app entry point
├── requirements.txt
├── .env                       # Your secrets (never commit)
├── .env.example               # Template
│
├── agent/
│   └── system_prompt.py       # Survey agent prompt template
│
├── config/
│   └── settings.py            # Pydantic settings (loads .env)
│
├── scheduler/
│   ├── cron_runner.py         # APScheduler setup
│   ├── weekly_job.py          # Reads CSV → dispatches batch calls
│   └── csv_reader.py          # Contact CSV parser
│
├── retell/
│   ├── client.py              # Retell AI HTTP client
│   ├── batch_caller.py        # POST /v2/batch-call
│   └── models.py              # Request/response models
│
├── webhook/
│   ├── router.py              # POST /webhook/retell endpoint
│   ├── event_handler.py       # Event dispatcher
│   └── models.py              # Retell webhook payload models
│
├── processor/
│   ├── pipeline.py            # Orchestrates full call processing
│   ├── transcript_parser.py   # Parses utterances + timing
│   └── scorer.py              # VADER sentiment + heuristic scoring
│
├── store/
│   ├── database.py            # Async SQLAlchemy engine
│   ├── models.py              # ORM: Call, Transcript, Segment, Score
│   ├── repository.py          # DB query/mutation helpers
│   └── s3_uploader.py         # Upload raw JSON to S3
│
├── formatter/
│   ├── qwen_formatter.py      # Transcript → ShareGPT format
│   ├── export_job.py          # Batch JSONL export logic
│   └── schemas.py             # ShareGPT / Alpaca data models
│
├── scripts/
│   ├── create_tables.py       # One-time DB table creation
│   ├── seed_contacts.py       # Generate sample contacts CSV
│   └── run_export.py          # Manual training data export
│
└── data/
    ├── contacts/              # contacts.csv goes here
    └── exports/               # training_YYYYMMDD.jsonl output
```

---

## Prerequisites

- Python 3.10+
- PostgreSQL running locally or remotely
- Retell AI account with a provisioned phone number and agent
- ngrok (for local webhook testing)
- AWS account + S3 bucket (optional — for raw transcript backup)

---

## Setup

### 1. Install dependencies

```powershell
cd "D:\ML Postgrad\AI_Caller"
pip install -r requirements.txt
```

### 2. Configure environment

```powershell
cp .env.example .env
```

Edit `.env` with your values:

```env
# Retell AI
RETELL_API_KEY=your_retell_api_key
RETELL_AGENT_ID=ag_xxxxxxxxxxxxxxxx
RETELL_FROM_NUMBER=+12025550100
RETELL_WEBHOOK_SECRET=your_webhook_secret

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_caller

# AWS S3 (optional — leave blank to skip)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET=

# Scheduler
SCHEDULER_CRON=0 9 * * 1   # Every Monday at 9 AM

# Contacts
CONTACTS_CSV_PATH=data/contacts/contacts.csv
```

### 3. Set up the database

```powershell
python scripts/create_tables.py
```

### 4. Add contacts

Either create `data/contacts/contacts.csv` manually:

```csv
name,phone,survey_topic,week_label
John Smith,+12025550101,Product Feedback,Week 1
Jane Doe,+12025550102,Product Feedback,Week 1
```

Or generate sample contacts for testing:

```powershell
python scripts/seed_contacts.py
```

---

## Running the App

### Start the server

```powershell
uvicorn main:app --reload
```

The app starts on `http://localhost:8000`. The scheduler starts automatically.

### Expose webhook for local testing (ngrok)

In a second terminal:

```powershell
ngrok http 8000
```

Copy the `https://xxxx.ngrok.io` URL and set your webhook in the Retell dashboard to:

```
https://xxxx.ngrok.io/webhook/retell
```

### Health check

```
GET http://localhost:8000/health
```

---

## Retell AI Agent Setup

1. Go to [app.retellai.com](https://app.retellai.com) → **Create Agent** → **Single Prompt Agent**
2. Paste the contents of `agent/system_prompt.py` into the prompt box
3. Set **Welcome Message** to **Agent speaks first**
4. Under **Webhook Settings**, set the webhook URL to `https://your-domain/webhook/retell`
5. Under **Phone Numbers**, attach your provisioned number
6. Copy the **Agent ID** from the top of the page into `.env` as `RETELL_AGENT_ID`
7. Hit **Publish**

### Dynamic variables injected per call

| Variable | Source |
|---|---|
| `{{contact_name}}` | CSV `name` column |
| `{{survey_topic}}` | CSV `survey_topic` column |
| `{{week_label}}` | CSV `week_label` column |

---

## Exporting Training Data

After calls have been processed, export transcripts as ShareGPT JSONL:

```powershell
python scripts/run_export.py
```

Output: `data/exports/training_YYYYMMDD_HHMMSS.jsonl`

Each line is a ShareGPT-format record:

```json
{
  "conversations": [
    {"from": "system", "value": "You are a survey interviewer..."},
    {"from": "human", "value": "Hello?"},
    {"from": "gpt", "value": "Hi, is this John? ..."},
    ...
  ],
  "call_id": "call_abc123"
}
```

Use this file directly with **LLaMA-Factory** or **ms-swift** for fine-tuning Qwen.

---

## Database Schema

| Table | Description |
|---|---|
| `calls` | Call metadata (IDs, numbers, status, timestamps, duration) |
| `transcripts` | One per call — S3 key, export flag |
| `transcript_segments` | Per-utterance rows (role, content, start_ms, end_ms) |
| `scores` | Auto-scoring dimensions per call (sentiment, completion rate, etc.) |

---

## Auto-Scoring Dimensions

The scorer (`processor/scorer.py`) assigns a `[0.0, 1.0]` float per dimension:

| Dimension | Method |
|---|---|
| `sentiment` | VADER compound score normalised to [0, 1] |
| `completion_rate` | Ratio of expected survey questions detected by regex |
| `avg_response_length` | Average user words per turn (normalised to 50-word target) |
| `user_turn_count` | Raw count of user utterances |

---

## Scripts Reference

| Script | Purpose |
|---|---|
| `scripts/create_tables.py` | Create all DB tables (run once) |
| `scripts/seed_contacts.py` | Generate sample `contacts.csv` for testing |
| `scripts/run_export.py` | Manually trigger JSONL training data export |

---

## Notes

- **S3 is optional.** If AWS credentials are blank, S3 upload fails silently and `s3_key` is `NULL` in the DB. All transcript data is still saved to PostgreSQL.
- **The scheduler fires automatically** when the app starts, based on `SCHEDULER_CRON`. You can also trigger a batch call manually via `scheduler/weekly_job.py`.
- **Webhook signature verification** uses HMAC-SHA256 with `RETELL_WEBHOOK_SECRET`. Set this in both your `.env` and the Retell dashboard.
- For production, replace ngrok with a deployed server (Railway, Render, VPS) and update the webhook URL in the Retell dashboard.
