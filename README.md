# 🚀 AI-Powered Outbound Sales QA Agent

An AI-powered outbound sales quality assurance agent that evaluates SDR outreach messages using Google Gemini, deterministic business rules, and explainable AI scoring before they are sent to prospective customers.

The application analyzes message quality across eight sales criteria, performs automated rule-based validations, generates evidence-backed AI feedback, rewrites the outreach for improved effectiveness, and produces a structured quality report to help sales teams send more personalized, accurate, and high-converting outbound messages.

---

## 🌐 Live Demo

https://outbound-sales-messages-analyzer.streamlit.app

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


                         User Input
                              │
                              ▼
                    Streamlit Web Interface
                              │
                              ▼
                   Hybrid Evaluation Engine
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
        Deterministic Rule Checks      Gemini AI Analysis
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                   Merge Evaluation Results
                                  │
                                  ▼
                Pydantic Validation & Parsing
                                  │
                                  ▼
                       Structured Output
                                  │
                                  ▼
      ┌──────────────────────────────────────────────────────┐
      │ • Quality Score                                      │
      │ • Criteria-wise Feedback                             │
      │ • Verdict                                            │
      │ • Improved Rewrite                                   │
      │ • JSON Export                                        │
      └──────────────────────────────────────────────────────┘
```

---

## ▶ Running Locally

Clone the repository

```bash
git clone https://github.com/mahalakshmii-m/outbound-sales-qa-agent.git
cd outbound-sales-qa-agent
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
