# AI Caller — iMasonsGPT Knowledge Extraction System

A weekly automated calling system that uses **Retell AI** voice agents to conduct expert interviews with digital infrastructure professionals. Recordings are saved as MP3s for downstream transcription and fine-tuning of iMasonsGPT.

---

## Architecture

```
Weekly Scheduler (APScheduler cron)
        ↓
contacts.csv  →  Retell AI Batch Call  →  Voice Agent (LLM-powered interview)
                                                  ↓
                                    scripts/download_recordings.py
                                                  ↓
                                    data/recordings/<call_id>.mp3
                                                  ↓
                                    Your transcription pipeline
```

---

## Question Categories

Each contact in the CSV is assigned a `question_category`. The agent picks 3–4 questions from that category and adapts based on the responses.

| Category |
|---|
| Data Center Design & Operations |
| Sustainability & Environmental Impact |
| Digital Infrastructure & Networking |
| Industry Trends & Future Outlook |
| Leadership, Strategy & Decision-Making |

All calls also begin with a personal check-in (how was your week, what are you working on, etc.) before moving to expert questions.

---

## Project Structure

```
AI_Caller/
├── main.py                        # Scheduler entry point (python main.py)
├── requirements.txt
├── .env                           # Your secrets (never commit)
├── .env.example                   # Template
│
├── agent/
│   └── system_prompt.py           # Interview prompt with all question categories
│
├── config/
│   └── settings.py                # Pydantic settings (loads .env)
│
├── scheduler/
│   ├── cron_runner.py             # APScheduler setup
│   ├── weekly_job.py              # Reads CSV → dispatches batch calls → saves state
│   └── csv_reader.py              # Contact CSV parser
│
├── retell/
│   ├── client.py                  # Retell AI HTTP client
│   ├── batch_caller.py            # POST /v2/batch-call
│   └── models.py                  # Request/response models
│
├── scripts/
│   ├── download_recordings.py     # Poll Retell API → download MP3s
│   └── seed_contacts.py           # Generate sample contacts CSV
│
└── data/
    ├── contacts/                  # contacts.csv goes here
    ├── recordings/                # Downloaded MP3s saved here
    └── state/                     # last_batch.json (auto-created by scheduler)
```

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

Edit `.env`:

```env
RETELL_API_KEY=your_retell_api_key
RETELL_AGENT_ID=ag_xxxxxxxxxxxxxxxx
RETELL_FROM_NUMBER=+12025550100

SCHEDULER_CRON=0 9 * * 1        # Every Monday at 9 AM
CONTACTS_CSV_PATH=data/contacts/contacts.csv
RECORDINGS_DIR=data/recordings
```

### 3. Add contacts

Create `data/contacts/contacts.csv`:

```csv
name,phone,question_category
John Smith,+12025550101,Data Center Design & Operations
Jane Doe,+12025550102,Sustainability & Environmental Impact
```

Or generate sample contacts for testing:

```powershell
python scripts/seed_contacts.py
```

---

## Retell AI Agent Setup

1. Go to [app.retellai.com](https://app.retellai.com) → **Create Agent** → **Single Prompt Agent**
2. Paste the contents of `agent/system_prompt.py` (the `SYSTEM_PROMPT_TEMPLATE` string) into the prompt box
3. Set **Welcome Message** → **Agent speaks first**
4. Attach your provisioned phone number to the agent
5. Copy the **Agent ID** from the top of the page into `.env` as `RETELL_AGENT_ID`
6. Hit **Publish**

### Dynamic variables used

| Variable | Source | Example |
|---|---|---|
| `{{contact_name}}` | CSV `name` column | `"John Smith"` |
| `{{question_category}}` | CSV `question_category` column | `"Data Center Design & Operations"` |

---

## Running

### Start the scheduler

```powershell
python main.py
```

The scheduler runs in the background and fires on `SCHEDULER_CRON`. It dispatches the batch call and saves the `batch_call_id` to `data/state/last_batch.json`.

To trigger a call immediately without waiting for the cron, you can run the job directly:

```powershell
python -c "import asyncio; from scheduler.weekly_job import run_weekly_survey; asyncio.run(run_weekly_survey())"
```

### Download recordings

After calls have completed (usually within an hour), run:

```powershell
# Uses the last batch automatically
python scripts/download_recordings.py

# Or specify a batch explicitly
python scripts/download_recordings.py --batch-id batch_abc123

# Or download a single call
python scripts/download_recordings.py --call-id call_xyz456
```

MP3s are saved to `data/recordings/<call_id>.mp3`.

---

## CSV Format

| Column | Required | Description |
|---|---|---|
| `name` | Yes | Contact's first name (used in greeting) |
| `phone` | Yes | E.164 format, e.g. `+12025550101` |
| `question_category` | No | One of the 5 categories (defaults to Data Center Design & Operations) |

---

## Notes

- **No server or ngrok needed.** The system is fully outbound — it dispatches calls and polls for results. No webhook or public URL required.
- **Recording must be enabled** in your Retell agent settings for `recording_url` to be populated on completed calls.
- If `download_recordings.py` shows "No recording URL" for a call, check that recording is turned on in the Retell dashboard under the agent's **Call Settings**.
