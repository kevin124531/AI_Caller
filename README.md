# AI Caller — iMasonsGPT Knowledge Extraction System

A weekly automated calling system that uses **Retell AI** voice agents to conduct expert interviews with digital infrastructure professionals. Recordings are automatically downloaded, transcribed with speaker diarization, and formatted into ChatML JSONL training data for iMasonsGPT fine-tuning.

---

## Full Automated Pipeline

```
python main.py
      ↓
Weekly Scheduler (APScheduler cron)
      ↓
contacts.csv  →  Retell AI Batch Call  →  Voice Agent (LLM-powered interview)
                                                  ↓
                                    Background Poller (every 2 min)
                                                  ↓
                                    data/recordings/<call_id>.mp3
                                                  ↓
                                    AssemblyAI Transcription (speaker diarization)
                                                  ↓
                                    data/transcripts/<call_id>/
                                      conversation.txt
                                      full_transcript.txt
                                      speaker_a_transcript.txt
                                      speaker_b_transcript.txt
                                      transcript_data.json
                                                  ↓
                                    Training Formatter
                                    (expert = assistant, interviewer = user)
                                                  ↓
                                    data/exports/training.jsonl  ← appended each week
```

Everything after `python main.py` is fully automatic — no manual steps required.

---

## Question Categories

Each contact in the CSV is assigned a `question_category`. The agent picks 3–4 questions from that category and adapts based on the responses. All calls begin with a personal check-in before moving to expert questions.

| Category |
|---|
| Data Center Design & Operations |
| Sustainability & Environmental Impact |
| Digital Infrastructure & Networking |
| Industry Trends & Future Outlook |
| Leadership, Strategy & Decision-Making |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Scheduling | APScheduler (async cron) |
| Voice AI | Retell AI (batch outbound calls) |
| Transcription | AssemblyAI (speaker diarization) |
| Training format | ChatML JSONL (compatible with Qwen / LLaMA-Factory) |
| HTTP client | httpx (async) |
| Config | Pydantic Settings |

---

## Project Structure

```
AI_Caller/
├── main.py                        # Scheduler entry point — python main.py
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
│   ├── csv_reader.py              # Contact CSV parser
│   └── recording_poller.py        # Background: download → transcribe → format
│
├── retell/
│   ├── client.py                  # Retell AI HTTP client
│   ├── batch_caller.py            # POST /create-batch-call
│   └── models.py                  # Request/response models
│
├── transcriber/
│   └── audio_transcriber.py       # AssemblyAI transcription with speaker diarization
│
├── formatter/
│   └── qwen_formatter.py          # Transcript → ChatML JSONL (appends to training.jsonl)
│
├── scripts/
│   ├── download_recordings.py     # Manual: download MP3s for a batch or single call
│   └── seed_contacts.py           # Generate sample contacts CSV for testing
│
└── data/
    ├── contacts/                  # contacts.csv goes here
    ├── recordings/                # Downloaded MP3s — <call_id>.mp3
    ├── transcripts/               # Per-call transcript files — <call_id>/
    ├── exports/                   # training.jsonl — grows each week
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
# Retell AI
RETELL_API_KEY=your_retell_api_key
RETELL_AGENT_ID=ag_xxxxxxxxxxxxxxxx
RETELL_FROM_NUMBER=+12025550100

# AssemblyAI
ASSEMBLYAI_API_KEY=your_assemblyai_api_key

# Scheduler (cron — default: every Monday at 9 AM)
SCHEDULER_CRON=0 9 * * 1

# File paths
CONTACTS_CSV_PATH=data/contacts/contacts.csv
RECORDINGS_DIR=data/recordings
TRANSCRIPTS_DIR=data/transcripts
```

### 3. Add contacts

Create `data/contacts/contacts.csv`:

```csv
name,phone,job_title,specialisation,question_category
John Smith,+12025550101,VP of Data Center Engineering,"liquid cooling, high-density compute",Data Center Design & Operations
Jane Doe,+12025550102,Chief Sustainability Officer,"decarbonisation, water efficiency",Sustainability & Environmental Impact
```

Or generate sample contacts for testing:

```powershell
python scripts/seed_contacts.py
```

---

## CSV Format

| Column | Required | Description |
|---|---|---|
| `name` | Yes | Contact's first name (injected into the agent's greeting) |
| `phone` | Yes | E.164 format e.g. `+12025550101` |
| `job_title` | No | Used in JSONL system prompt e.g. `"VP of Infrastructure"` |
| `specialisation` | No | Used in JSONL system prompt e.g. `"liquid cooling, AI workloads"` |
| `question_category` | No | Which question set to use (defaults to Data Center Design & Operations) |

---

## Retell AI Agent Setup

1. Go to [app.retellai.com](https://app.retellai.com) → **Create Agent** → **Single Prompt Agent**
2. Paste the contents of `agent/system_prompt.py` (`SYSTEM_PROMPT_TEMPLATE`) into the prompt box
3. Set **Welcome Message** → **Agent speaks first**
4. Under **Call Settings**, enable **Call Recording**
5. Attach your provisioned phone number to the agent
6. Copy the **Agent ID** into `.env` as `RETELL_AGENT_ID`
7. Hit **Publish**

### Dynamic variables injected per call

| Variable | Source |
|---|---|
| `{{contact_name}}` | CSV `name` column |
| `{{question_category}}` | CSV `question_category` column |

---

## Running

### Start the scheduler

```powershell
python main.py
```

Fires on `SCHEDULER_CRON`. After dispatch, the background poller automatically:
- Downloads each MP3 as calls complete
- Transcribes with AssemblyAI (speaker diarization)
- Appends training pairs to `data/exports/training.jsonl`

### Trigger immediately (without waiting for cron)

```powershell
python -c "import asyncio; from scheduler.weekly_job import run_weekly_survey; asyncio.run(run_weekly_survey())"
```

### Manually download recordings (optional)

```powershell
# Uses the last batch automatically
python scripts/download_recordings.py

# Specific batch
python scripts/download_recordings.py --batch-id batch_abc123

# Single call
python scripts/download_recordings.py --call-id call_xyz456
```

---

## Training Data Format

Each entry in `data/exports/training.jsonl` is a ChatML record:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a VP of Data Center Engineering specialising in liquid cooling, high-density compute. You are an experienced member of iMasons with deep expertise in Data Center Design & Operations. You provide detailed, experience-based insights on digital infrastructure topics, drawing from real-world practice and lessons learned in the field."
    },
    {
      "role": "user",
      "content": "What are the most critical trade-offs between air-cooled and liquid-cooled architectures?"
    },
    {
      "role": "assistant",
      "content": "The biggest trade-off really comes down to..."
    }
  ],
  "metadata": {
    "call_id": "call_abc123",
    "source": "ai_caller",
    "job_title": "VP of Data Center Engineering",
    "specialisation": "liquid cooling, high-density compute",
    "question_category": "Data Center Design & Operations"
  }
}
```

New entries are **appended** each week — the file grows over time. Compatible with **LLaMA-Factory** and **ms-swift** for Qwen fine-tuning.

---

## Speaker Identification

AssemblyAI labels speakers as `Speaker A` and `Speaker B`. The formatter automatically identifies the expert as the speaker with the most total words (the AI interviewer asks short questions; the expert gives long answers). Expert utterances become `assistant` turns; interviewer utterances become `user` turns.

---

## Notes

- **Recording must be enabled** in your Retell agent's Call Settings, otherwise `recording_url` will be empty and no MP3 will be downloaded.
- **AssemblyAI transcription** takes roughly 1–2 minutes per 10-minute call. The poller handles this in a background thread — it won't block other calls from being processed.
- The poller checks every **2 minutes** and gives up after **3 hours**. Both values can be adjusted in `scheduler/recording_poller.py`.
- If a transcript already exists for a call, transcription is skipped and the existing file is reused.
- `data/exports/training.jsonl` is **appended to**, never overwritten — safe to run weekly indefinitely.
