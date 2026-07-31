# ClickPost Outbound QA Agent

A production-oriented AI agent that evaluates account-level SDR outreach
against ClickPost-style outbound rules and generates an improved version.

## Why this project fits the role

The internship description explicitly mentions an **Outbound QA Agent** that
checks for:

- no generic opener
- quantified value in the buyer's context
- one clear next step

This implementation adds explainable scoring, structured outputs, strict
anti-hallucination rules, and a usable Streamlit interface.

## Features

- Scores eight outbound-quality criteria
- Produces a 0–100 overall score
- Gives a send / revise / reject verdict
- Explains every score with evidence
- Rewrites the message in fewer than 120 words
- Never invents unsupported account facts
- Exports the result as JSON

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Enter your OpenAI API key in the sidebar.

## Suggested demo flow

1. Paste a generic outbound message.
2. Add a verified account signal such as international expansion or logistics hiring.
3. Run the QA agent.
4. Show the score breakdown.
5. Compare the original with the rewritten outreach.
6. Download the structured JSON result.

## Architecture

```text
User input
   ↓
Streamlit interface
   ↓
Outbound quality system prompt
   ↓
OpenAI Responses API + Pydantic structured output
   ↓
Scored criteria + verdict + rewritten message
```

## Evaluation ideas

Create 10–20 test messages across three buckets:

- generic / poor
- moderately personalized
- strong account-level outreach

Track:

- agreement with a human reviewer
- score consistency across repeated runs
- percentage of rewrites that satisfy all hard rules
- average score improvement after rewrite

## Next production improvements

- Store evaluation history in SQLite/Postgres
- Add batch CSV upload
- Add CRM integration
- Add prompt/version tracking
- Add human feedback and regression tests
- Add an API endpoint using FastAPI
