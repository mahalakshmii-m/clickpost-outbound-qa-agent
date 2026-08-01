import json
import os
import re
from datetime import datetime
from typing import List, Literal

import pandas as pd
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Outbound Sales QA Agent",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .result-card {
        background: linear-gradient(
            145deg,
            rgba(30, 41, 59, 0.95),
            rgba(15, 23, 42, 0.95)
        );
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 16px;
        padding: 20px 22px;
        min-height: 128px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
    }

    .result-label {
        color: #94a3b8;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .result-value {
        color: #f8fafc;
        font-size: 30px;
        font-weight: 750;
        line-height: 1.1;
    }

    .result-caption {
        color: #cbd5e1;
        font-size: 13px;
        margin-top: 10px;
    }

    .score-poor {
        border-top: 4px solid #ef4444;
    }

    .score-average {
        border-top: 4px solid #f59e0b;
    }

    .score-good {
        border-top: 4px solid #22c55e;
    }

    .verdict-danger {
        color: #f87171;
    }

    .verdict-warning {
        color: #fbbf24;
    }

    .verdict-success {
        color: #4ade80;
    }

    .business-impact-card {
        background: linear-gradient(
            145deg,
            rgba(30, 41, 59, 0.96),
            rgba(15, 23, 42, 0.96)
        );
        border: 1px solid rgba(59, 130, 246, 0.30);
        border-left: 5px solid #3b82f6;
        border-radius: 14px;
        padding: 18px 20px;
        margin: 14px 0 20px 0;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
    }

    .business-impact-title {
        color: #93c5fd;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 7px;
    }

    .business-impact-text {
        color: #f8fafc;
        font-size: 16px;
        line-height: 1.55;
    }

    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(90deg, #2563eb, #3b82f6);
        color: white;
        border: none;
        border-radius: 10px;
        min-height: 46px;
        font-weight: 700;
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.28);
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(90deg, #1d4ed8, #2563eb);
        color: white;
        border: none;
    }

    div[data-testid="stDownloadButton"] button {
        border-radius: 10px;
        min-height: 44px;
        font-weight: 700;
    }

    h1 {
        margin-bottom: 0.15rem !important;
    }

    h3 {
        margin-top: 0.2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# STRUCTURED OUTPUT MODELS
# ---------------------------------------------------------

class CriterionScore(BaseModel):
    criterion: str
    score: int = Field(ge=0, le=10)
    explanation: str
    evidence: str
    recommendation: str


class QAResult(BaseModel):
    overall_score: int = Field(ge=0, le=100)

    verdict: Literal[
        "Ready to send",
        "Needs revision",
        "Do not send",
    ]

    criteria: List[CriterionScore]

    key_issues: List[str]
    strengths: List[str]

    improved_message: str
    suggested_subject_line: str

    one_line_reasoning: str
    business_impact_summary: str


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

CRITERIA_NAMES = [
    "Account specificity",
    "Evidence-based trigger or signal",
    "Relevant post-purchase or shipping pain",
    "Quantified or concrete business value",
    "Buyer relevance",
    "Credibility and proof",
    "Clear single next step",
    "Brevity and natural tone",
]


SYSTEM_PROMPT = """
You are a senior outbound quality-assurance agent for ClickPost.

ClickPost is a post-purchase experience and shipping intelligence platform
for enterprise and mid-market e-commerce brands.

Your role is to evaluate SDR outreach like a strict, revenue-focused
sales leader.

Evaluate exactly these eight criteria, each from 0 to 10:

1. Account specificity
2. Evidence-based trigger or signal
3. Relevant post-purchase or shipping pain
4. Quantified or concrete business value
5. Buyer relevance
6. Credibility and proof
7. Clear single next step
8. Brevity and natural tone

SCORING RULES:

- 0 to 3: Weak, absent, generic, unsupported, or irrelevant.
- 4 to 6: Partially effective but needs improvement.
- 7 to 8: Strong and mostly ready.
- 9 to 10: Exceptional, specific, credible, and highly relevant.

STRICT GUARDRAILS:

- Never invent customer names, metrics, carrier stacks, integrations,
  company events, problems, or achievements.
- Use only the information supplied in the account context and signal.
- Explicitly identify missing evidence.
- Penalize generic phrases such as:
  "I hope you are doing well",
  "best solution",
  "revolutionary platform",
  and "industry-leading" when unsupported.
- Penalize vague claims without proof.
- Penalize multiple calls to action.
- Penalize unnecessary length and unnatural AI-style wording.
- The improved message must remain under 120 words.
- The improved message must contain one clear next step.
- Do not include fabricated quantified benefits.
- If a quantified value is unavailable, write a specific qualitative
  business outcome instead.
- Preserve the original outreach channel and intent.
- The verdict must be exactly:
  "Ready to send", "Needs revision", or "Do not send".
- Return exactly eight criterion objects.
- Provide specific evidence and actionable recommendations.
"""


DEMO_SCENARIOS = {
    "Choose a demo scenario": {
        "persona": "VP / Head of E-commerce Operations",
        "context": "",
        "signal": "",
        "draft": "",
    },
    "Weak generic outreach": {
        "persona": "VP / Head of E-commerce Operations",
        "context": (
            "A fashion e-commerce brand recently launched shipping "
            "to customers in the United States."
        ),
        "signal": (
            "The company is hiring two logistics operations managers "
            "after its international expansion."
        ),
        "draft": (
            "Hi, I hope you are doing well. ClickPost provides the best "
            "shipping solution for e-commerce companies. We help brands "
            "improve logistics. Can we schedule a call to discuss?"
        ),
    },
    "Average outreach": {
        "persona": "Head of Logistics",
        "context": (
            "A fast-growing beauty brand sells through its own website "
            "and recently expanded into three new Indian cities."
        ),
        "signal": (
            "The company has posted customer updates about delayed "
            "deliveries during periods of high order volume."
        ),
        "draft": (
            "Hi, I noticed your expansion into three new cities. "
            "Scaling order volume can make delivery visibility harder "
            "for operations teams. ClickPost helps e-commerce brands "
            "manage shipment tracking and customer communication. "
            "Would you be open to a short call next week?"
        ),
    },
    "Strong personalized outreach": {
        "persona": "VP of Customer Experience",
        "context": (
            "An online electronics retailer recently introduced "
            "same-day delivery in two metro cities."
        ),
        "signal": (
            "Its support page now contains a dedicated section for "
            "same-day delivery status and delay questions."
        ),
        "draft": (
            "Hi, I noticed your team recently launched same-day delivery "
            "in two metro cities and added new support guidance for delivery "
            "status questions. That usually increases pressure on customer "
            "experience teams when shipment updates are fragmented. "
            "ClickPost helps centralize post-purchase tracking and proactive "
            "customer communication. Would a 15-minute discussion on how "
            "your team is handling same-day delivery visibility be useful?"
        ),
    },
}


# ---------------------------------------------------------
# DETERMINISTIC RULE ENGINE
# ---------------------------------------------------------

def run_rule_checks(draft_message: str) -> List[dict]:
    """Run transparent non-AI checks against the outreach draft."""

    text = draft_message.strip()
    lower_text = text.lower()
    words = re.findall(r"\b[\w'-]+\b", text)

    checks = []

    generic_openers = [
        "i hope you are doing well",
        "hope you're doing well",
        "hope you are well",
        "trust you are doing well",
    ]

    unsupported_claims = [
        "best solution",
        "industry-leading",
        "revolutionary",
        "world-class",
        "number one",
        "#1",
        "game-changing",
    ]

    generic_opener_found = any(
        phrase in lower_text for phrase in generic_openers
    )

    unsupported_claim_found = any(
        phrase in lower_text for phrase in unsupported_claims
    )

    question_count = text.count("?")

    has_number = bool(
        re.search(
            r"\b\d+(?:\.\d+)?%?\b",
            text,
        )
    )

    first_person_count = len(
        re.findall(
            r"\b(i|we|our|us|clickpost)\b",
            lower_text,
        )
    )

    buyer_language_count = len(
        re.findall(
            r"\b(you|your|team|customers|operations|buyers)\b",
            lower_text,
        )
    )

    checks.append(
        {
            "Rule": "No generic opener",
            "Status": "Fail" if generic_opener_found else "Pass",
            "Details": (
                "Generic opening phrase detected."
                if generic_opener_found
                else "The message avoids common generic opening phrases."
            ),
        }
    )

    checks.append(
        {
            "Rule": "No unsupported superlatives",
            "Status": "Fail" if unsupported_claim_found else "Pass",
            "Details": (
                "An unsupported marketing claim was detected."
                if unsupported_claim_found
                else "No obvious unsupported superlative was found."
            ),
        }
    )

    checks.append(
        {
            "Rule": "Single clear CTA",
            "Status": "Pass" if question_count == 1 else "Review",
            "Details": (
                "Exactly one question or CTA detected."
                if question_count == 1
                else f"{question_count} question marks detected. "
                "Use one clear next step."
            ),
        }
    )

    checks.append(
        {
            "Rule": "Message length",
            "Status": "Pass" if len(words) <= 120 else "Fail",
            "Details": f"{len(words)} words detected. Target: 120 or fewer.",
        }
    )

    checks.append(
        {
            "Rule": "Concrete value",
            "Status": "Pass" if has_number else "Review",
            "Details": (
                "A concrete numeric reference is present."
                if has_number
                else "No numeric value is present. This is acceptable only "
                "when no verified metric is available."
            ),
        }
    )

    checks.append(
        {
            "Rule": "Buyer-focused language",
            "Status": (
                "Pass"
                if buyer_language_count >= first_person_count
                else "Review"
            ),
            "Details": (
                f"Buyer-focused references: {buyer_language_count}; "
                f"seller-focused references: {first_person_count}."
            ),
        }
    )

    return checks


# ---------------------------------------------------------
# GEMINI ANALYSIS
# ---------------------------------------------------------

def analyse_message(
    client: genai.Client,
    model: str,
    persona: str,
    company_context: str,
    observed_signal: str,
    draft_message: str,
    rule_checks: List[dict],
) -> QAResult:

    rule_summary = json.dumps(rule_checks, indent=2)

    user_prompt = f"""
TARGET PERSONA:
{persona or "Not supplied"}

VERIFIED ACCOUNT CONTEXT:
{company_context or "Not supplied"}

OBSERVED BUYING SIGNAL:
{observed_signal or "Not supplied"}

DRAFT OUTREACH:
{draft_message}

DETERMINISTIC RULE-CHECK RESULTS:
{rule_summary}

Analyse the draft using both the supplied account information and the
rule-check results.

Do not treat a deterministic rule result as unquestionable truth.
Use it as supporting evidence and apply business judgement.

Return exactly eight criteria using the required criterion names.
"""

    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=QAResult,
        ),
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    result = QAResult.model_validate_json(response.text)

    if len(result.criteria) != 8:
        raise RuntimeError(
            "Gemini did not return exactly eight scoring criteria."
        )

    return result


# ---------------------------------------------------------
# REPORT CREATION
# ---------------------------------------------------------

def create_download_report(
    result: QAResult,
    persona: str,
    company_context: str,
    observed_signal: str,
    draft_message: str,
    rule_checks: List[dict],
    model: str,
) -> str:

    report = {
        "report_metadata": {
            "generated_at_utc": datetime.utcnow().isoformat() + "Z",
            "application": "ClickPost Outbound QA Agent",
            "model": model,
        },
        "input": {
            "target_persona": persona,
            "verified_account_context": company_context,
            "observed_buying_signal": observed_signal,
            "draft_outreach": draft_message,
        },
        "deterministic_rule_checks": rule_checks,
        "ai_evaluation": result.model_dump(),
    }

    return json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
    )


# ---------------------------------------------------------
# UI HELPERS
# ---------------------------------------------------------

def display_rule_checks(rule_checks: List[dict]) -> None:
    st.subheader("Deterministic quality checks")

    passed = sum(
        item["Status"] == "Pass"
        for item in rule_checks
    )

    st.caption(
        f"{passed} of {len(rule_checks)} automated checks passed."
    )

    rule_df = pd.DataFrame(rule_checks)

    st.dataframe(
        rule_df,
        use_container_width=True,
        hide_index=True,
    )


def display_score_breakdown(result: QAResult) -> None:
    st.subheader("AI score breakdown")

    for item in result.criteria:
        st.markdown(
            f"**{item.criterion} — {item.score}/10**"
        )

        st.progress(item.score / 10)

        with st.expander(
            f"View reasoning: {item.criterion}"
        ):
            st.write(item.explanation)

            st.markdown("**Evidence**")
            st.write(item.evidence)

            st.markdown("**Recommendation**")
            st.write(item.recommendation)


def display_comparison(
    original_message: str,
    improved_message: str,
) -> None:
    st.subheader("Original vs improved outreach")

    original_column, improved_column = st.columns(2)

    with original_column:
        st.markdown("#### Original message")
        st.text_area(
            "Original outreach",
            value=original_message,
            height=260,
            disabled=True,
            label_visibility="collapsed",
        )

    with improved_column:
        st.markdown("#### Improved message")
        st.text_area(
            "Improved outreach",
            value=improved_message,
            height=260,
            label_visibility="collapsed",
        )


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "selected_demo" not in st.session_state:
    st.session_state.selected_demo = "Choose a demo scenario"

if "persona" not in st.session_state:
    st.session_state.persona = "VP / Head of E-commerce Operations"

if "company_context" not in st.session_state:
    st.session_state.company_context = ""

if "observed_signal" not in st.session_state:
    st.session_state.observed_signal = ""

if "draft_message" not in st.session_state:
    st.session_state.draft_message = ""


def load_demo() -> None:
    selected = st.session_state.selected_demo
    demo = DEMO_SCENARIOS[selected]

    st.session_state.persona = demo["persona"]
    st.session_state.company_context = demo["context"]
    st.session_state.observed_signal = demo["signal"]
    st.session_state.draft_message = demo["draft"]


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    st.header("Configuration")

    api_key = st.text_input(
        "Gemini API key",
        type="password",
        value=os.getenv("GEMINI_API_KEY", ""),
        help=(
            "The key is used only during this session "
            "and is not displayed in the report."
        ),
    )

    model = st.text_input(
        "Gemini model",
        value=os.getenv(
            "GEMINI_MODEL",
            "gemini-flash-latest",
        ),
    )

    st.divider()

    st.subheader("Demo scenarios")

    st.selectbox(
        "Load a prepared example",
        options=list(DEMO_SCENARIOS.keys()),
        key="selected_demo",
        on_change=load_demo,
    )

    st.divider()

    st.markdown(
        """
### Why this is more than an API wrapper

✅ Hybrid AI + rule engine  
✅ Explainable scoring  
✅ Anti-hallucination guardrails  
✅ Structured Pydantic output  
✅ Recruiter-ready scenarios  
✅ Downloadable audit report
"""
    )


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------

st.markdown("""
# 🚀 Outbound Sales QA Agent

### Evaluate, improve, and validate outbound sales messages using Generative AI

""")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.info("🤖 **Gemini AI**")

with c2:
    st.info("⚡ **Hybrid Rule Engine**")

with c3:
    st.info("🛡 **Hallucination Safe**")

with c4:
    st.info("📊 **Explainable Scoring**")

st.info(
    "The agent combines deterministic quality checks with Gemini-based "
    "business judgement. It does not invent customer data or performance claims."
)


# ---------------------------------------------------------
# INPUT FORM
# ---------------------------------------------------------

with st.form("qa_form"):
    left, right = st.columns([1, 1])

    with left:
        persona = st.text_input(
            "Target buyer",
            key="persona",
            placeholder="Example: VP of E-commerce Operations",
        )

        company_context = st.text_area(
            "Verified account context",
            key="company_context",
            height=180,
            placeholder=(
                "Add only verified information about the account, "
                "such as expansion, hiring, delivery model, markets, "
                "or public operational changes."
            ),
        )

        observed_signal = st.text_area(
            "Observed buying signal",
            key="observed_signal",
            height=145,
            placeholder=(
                "Example: The company recently expanded internationally "
                "and is hiring logistics operations managers."
            ),
        )

    with right:
        draft_message = st.text_area(
            "Draft SDR outreach",
            key="draft_message",
            height=390,
            placeholder=(
                "Paste the outbound message that should be evaluated."
            ),
        )

    submitted = st.form_submit_button(
        "🚀 Analyze Outreach",
        type="primary",
        use_container_width=True,
    )


# ---------------------------------------------------------
# ANALYSIS OUTPUT
# ---------------------------------------------------------

if submitted:
    if not api_key:
        st.error(
            "Add your Gemini API key in the sidebar."
        )

    elif not draft_message.strip():
        st.error(
            "Paste a draft outreach message."
        )

    elif not company_context.strip() and not observed_signal.strip():
        st.warning(
            "No verified account context or buying signal was supplied. "
            "The agent can still review the draft, but personalization "
            "scores will be low."
        )

    else:
        try:
            rule_checks = run_rule_checks(
                draft_message
            )

            with st.spinner(
                "Running deterministic checks and Gemini evaluation..."
            ):
                client = genai.Client(
                    api_key=api_key
                )

                result = analyse_message(
                    client=client,
                    model=model,
                    persona=persona,
                    company_context=company_context,
                    observed_signal=observed_signal,
                    draft_message=draft_message,
                    rule_checks=rule_checks,
                )

            st.divider()

            criteria_passed = sum(
                item.score >= 7
                for item in result.criteria
            )

            automated_checks_passed = sum(
                item["Status"] == "Pass"
                for item in rule_checks
            )

            if result.overall_score >= 75:
                score_class = "score-good"
            elif result.overall_score >= 45:
                score_class = "score-average"
            else:
                score_class = "score-poor"

            if result.verdict == "Ready to send":
                verdict_class = "verdict-success"
            elif result.verdict == "Needs revision":
                verdict_class = "verdict-warning"
            else:
                verdict_class = "verdict-danger"

            metric_1, metric_2, metric_3, metric_4 = st.columns(4)

            with metric_1:
                st.markdown(
                    f"""
                    <div class="result-card {score_class}">
                        <div class="result-label">🏆 Quality score</div>
                        <div class="result-value">{result.overall_score}/100</div>
                        <div class="result-caption">
                            Overall outbound readiness
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with metric_2:
                st.markdown(
                    f"""
                    <div class="result-card {score_class}">
                        <div class="result-label">⚖️ Final verdict</div>
                        <div class="result-value {verdict_class}">
                            {result.verdict}
                        </div>
                        <div class="result-caption">
                            Recommended sending decision
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with metric_3:
                st.markdown(
                    f"""
                    <div class="result-card">
                        <div class="result-label">🤖 AI criteria meeting benchmark</div>
                        <div class="result-value">{criteria_passed}/8</div>
                        <div class="result-caption">
                            {criteria_passed} of 8 criteria scored 7 or higher
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with metric_4:
                st.markdown(
                    f"""
                    <div class="result-card">
                        <div class="result-label">✅ Rule checks passed</div>
                        <div class="result-value">
                            {automated_checks_passed}/{len(rule_checks)}
                        </div>
                        <div class="result-caption">
                            Deterministic checks cleared
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if result.verdict == "Ready to send":
                st.success(
                    result.one_line_reasoning
                )

            elif result.verdict == "Needs revision":
                st.warning(
                    result.one_line_reasoning
                )

            else:
                st.error(
                    result.one_line_reasoning
                )

            st.markdown(
                f"""
                <div class="business-impact-card">
                    <div class="business-impact-title">
                        💼 Business impact assessment
                    </div>
                    <div class="business-impact-text">
                        {result.business_impact_summary}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            tabs = st.tabs(
                [
                    "Score breakdown",
                    "Rule checks",
                    "Message improvement",
                    "Issues and strengths",
                ]
            )

            with tabs[0]:
                display_score_breakdown(
                    result
                )

            with tabs[1]:
                display_rule_checks(
                    rule_checks
                )

            with tabs[2]:
                st.markdown("#### Suggested subject line")

                st.text_input(
                    "Suggested subject line",
                    value=result.suggested_subject_line,
                    label_visibility="collapsed",
                )

                display_comparison(
                    original_message=draft_message,
                    improved_message=result.improved_message,
                )

            with tabs[3]:
                issue_column, strength_column = st.columns(2)

                with issue_column:
                    st.markdown("#### Key issues")

                    if result.key_issues:
                        for issue in result.key_issues:
                            st.write(f"• {issue}")
                    else:
                        st.write(
                            "No major issues identified."
                        )

                with strength_column:
                    st.markdown("#### Existing strengths")

                    if result.strengths:
                        for strength in result.strengths:
                            st.write(f"• {strength}")
                    else:
                        st.write(
                            "No significant strengths identified."
                        )

            downloadable_report = create_download_report(
                result=result,
                persona=persona,
                company_context=company_context,
                observed_signal=observed_signal,
                draft_message=draft_message,
                rule_checks=rule_checks,
                model=model,
            )

            st.divider()

            st.download_button(
                "📥 Download complete QA report (JSON)",
                data=downloadable_report,
                file_name="clickpost_outbound_qa_report.json",
                mime="application/json",
                use_container_width=True,
            )

        except Exception as exc:
            st.error(
                f"Could not complete the analysis: {exc}"
            )

            st.info(
                "Confirm that the Gemini API key is correct, "
                "the selected model is available to your account, "
                "and all packages were installed successfully."
            )


# ---------------------------------------------------------
# PROJECT EXPLANATION
# ---------------------------------------------------------

with st.expander("How the system works"):
    st.markdown(
        """
1. **Input validation** checks whether a draft and account information exist.
2. A **deterministic rule engine** detects generic openers, unsupported
   superlatives, message length, CTA count, and buyer-focused language.
3. **Gemini structured output** evaluates eight revenue-focused criteria.
4. **Pydantic validation** ensures predictable and typed results.
5. The system produces an improved message without inventing account facts.
6. A complete JSON report can be downloaded for audit or integration.
"""
    )