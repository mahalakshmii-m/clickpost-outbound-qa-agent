# 🚀 AI Sales Intelligence Platform

An AI-powered outbound sales quality assurance platform that evaluates SDR outreach using Google Gemini, deterministic business rules, and explainable AI scoring.

Originally developed as a technical assessment inspired by ClickPost's outbound QA workflow, the platform is designed to evaluate account-based sales outreach while preventing unsupported claims and providing actionable feedback.

---

## 🌐 Live Demo

https://sales-outreach-analyzer.streamlit.app

---

## ✨ Features

- Evaluate outbound sales messages across **8 quality criteria**
- Generate an overall **0–100 quality score**
- Hybrid evaluation using **Gemini AI + deterministic business rules**
- Explainable scoring for every criterion
- Business impact assessment
- Hallucination-safe evaluation
- AI-generated message improvements
- Structured JSON output
- Interactive Streamlit interface
- Multiple demo scenarios

---

## 🛠 Tech Stack

### AI & LLM

- Google Gemini AI
- Generative AI (GenAI)
- Prompt Engineering

### Backend

- Python

### Framework

- Streamlit

### Validation & Data

- Pydantic
- Pandas

### Rule Engine

- Hybrid Rule Engine
- Deterministic Validation

### Explainable AI

- Explainable AI (XAI)
- Structured AI Outputs
- Hallucination Guardrails
- AI-assisted Quality Scoring

### Deployment

- Git
- GitHub
- Streamlit Community Cloud

---

## 🏗 Architecture

```
                    User Input
                         │
                         ▼
                Streamlit Interface
                         │
                         ▼
              Hybrid Evaluation Engine
                 ┌───────────────────┐
                 │                   │
                 ▼                   ▼
      Deterministic Rules      Gemini AI
                 │                   │
                 └─────────┬─────────┘
                           ▼
              Pydantic Structured Output
                           ▼
        Explainable Scores • Verdict • Rewrite
```

---

## ▶ Running Locally

Clone the repository

```bash
git clone <repository-url>
cd clickpost-outbound-qa-agent
```

Create a virtual environment

```bash
python -m venv .venv
```

Windows

```bash
.venv\Scripts\activate
```

macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
streamlit run app.py
```

Enter your **Google Gemini API Key** in the sidebar.

---

## 📋 Suggested Demo

1. Select a demo scenario or enter your own inputs.
2. Provide verified account context.
3. Paste an SDR outreach message.
4. Analyze the outreach.
5. Review:
   - Overall quality score
   - AI score breakdown
   - Rule validation
   - Business impact assessment
   - AI-generated improvements
6. Download the structured JSON report.

---

## 🚀 Future Enhancements

- PDF report export
- Radar chart visualization
- Batch CSV evaluation
- CRM integration
- Evaluation history
- FastAPI backend
- Authentication & user accounts
- Model comparison (Gemini vs GPT vs Claude)

---
⚡ Powered by

Gemini AI • Python • Streamlit • Pydantic • Pandas • Git • GitHub

👨‍💻 Developed by Maha
