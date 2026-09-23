"""
Resume Review Agent
--------------------
A single-agent CrewAI application that compares a resume against a job
description and returns a structured, honest review. Built for beginners.

Run locally with:  streamlit run app.py
"""

import streamlit as st

# ---------------------------------------------------------------------------
# 1. PAGE CONFIG (must be the first Streamlit command)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Resume Review Agent",
    page_icon="📄",
    layout="centered",
)

# ---------------------------------------------------------------------------
# 2. SAFE IMPORTS
#    If a required package failed to install, show a friendly message
#    instead of crashing with a raw ImportError traceback.
# ---------------------------------------------------------------------------
try:
    from pypdf import PdfReader
except ImportError:
    st.error(
        "The PDF reading library (pypdf) is not installed. "
        "Please check requirements.txt and redeploy the app."
    )
    st.stop()

try:
    from crewai import Agent, Task, Crew, LLM
except ImportError:
    st.error(
        "The CrewAI library is not installed. "
        "Please check requirements.txt and redeploy the app."
    )
    st.stop()

import io

# ---------------------------------------------------------------------------
# 3. SECRETS / CONFIGURATION
#    Everything sensitive comes from Streamlit secrets, never hard-coded.
# ---------------------------------------------------------------------------
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def get_groq_config():
    """
    Reads the Groq API key and model name from Streamlit secrets.
    Stops the app with a friendly message if the key is missing.
    """
    api_key = st.secrets.get("GROQ_API_KEY", None)
    # This is Groq's own model ID (as shown at console.groq.com/docs/models),
    # e.g. "openai/gpt-oss-120b" — do NOT add a "groq/" prefix here.
    raw_model_name = st.secrets.get("GROQ_MODEL", "openai/gpt-oss-120b")

    if not api_key or not str(api_key).strip():
        st.error(
            "⚠️ No Groq API key was found.\n\n"
            "If you are the app owner: open your Streamlit Community Cloud "
            "app settings → **Secrets**, and add:\n\n"
            "```\nGROQ_API_KEY = \"your-key-here\"\n```\n\n"
            "Then reboot the app."
        )
        st.stop()

    # CrewAI routes any model string starting with "openai/" through its
    # native OpenAI-compatible client, which respects a custom base_url.
    # Groq's API is OpenAI-compatible, so we send requests there instead
    # of OpenAI, using this native path (no LiteLLM dependency required).
    crewai_model = f"openai/{raw_model_name}"

    return api_key, crewai_model


GROQ_API_KEY, GROQ_MODEL = get_groq_config()

# ---------------------------------------------------------------------------
# 4. HELPER: EXTRACT TEXT FROM AN UPLOADED PDF
# ---------------------------------------------------------------------------
def extract_pdf_text(uploaded_file) -> str:
    """
    Extracts text from an uploaded PDF file.
    Returns an empty string and shows a warning if nothing could be read
    (e.g. the PDF is a scanned image with no text layer, or is corrupted).
    """
    try:
        file_bytes = uploaded_file.read()
        reader = PdfReader(io.BytesIO(file_bytes))

        if len(reader.pages) == 0:
            st.warning("The uploaded PDF appears to have no pages.")
            return ""

        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)

        full_text = "\n".join(text_parts).strip()

        if not full_text:
            st.warning(
                "No readable text was found in this PDF. It may be a "
                "scanned image without a text layer. Please try pasting "
                "the resume text directly instead."
            )
            return ""

        return full_text

    except Exception:
        st.error(
            "This PDF could not be read. It may be corrupted, password "
            "protected, or in an unsupported format. Please try a "
            "different file or paste the resume text instead."
        )
        return ""


# ---------------------------------------------------------------------------
# 5. HELPER: BUILD AND RUN THE CREWAI CREW
# ---------------------------------------------------------------------------
def build_crew(resume_text: str, job_description: str) -> Crew:
    """
    Builds exactly one Agent, one Task, and one Crew.
    """
    llm = LLM(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        temperature=0.2,
    )

    reviewer = Agent(
        role="Senior Resume Reviewer and Career Coach",
        goal=(
            "Objectively compare a candidate's resume against a target job "
            "description and produce an honest, structured, and actionable review."
        ),
        backstory=(
            "You are a meticulous, experienced technical recruiter and career "
            "coach. You have reviewed thousands of resumes and always base "
            "your judgments strictly on the evidence in front of you. You "
            "never guess, assume, or invent details that are not explicitly "
            "written in the resume."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    task_description = f"""
Compare the RESUME below against the JOB DESCRIPTION below.

=== RESUME ===
{resume_text}

=== JOB DESCRIPTION ===
{job_description}

STRICT ACCURACY RULE (follow this exactly):
- Only state that a skill, tool, qualification, achievement, or experience
  is present if it is EXPLICITLY written in the resume text above.
- Never invent, assume, or infer experience, certifications, projects,
  skills, or education that are not clearly stated.
- If something cannot be determined from the resume, label it clearly as
  "Unknown / Not Demonstrated" rather than guessing.

Produce your review in clean Markdown using EXACTLY these section headers,
in this order:

## Match Summary
A short (3-5 sentence) honest overview of how well this resume fits this
specific job description.

## Skills Found
Bullet list of skills/tools explicitly present in the resume that are
relevant to the job description.

## Missing Requirements
Bullet list of requirements from the job description that are not present
anywhere in the resume.

## Unclear / Not Demonstrated
Bullet list of job requirements that might be met, but the resume does not
clearly demonstrate them.

## Experience Gaps
Bullet list describing gaps between the required experience and what the
resume shows.

## Education / Qualification Gaps
Bullet list describing gaps between required education/qualifications and
what the resume shows. If none, state "No significant gaps found."

## Resume Improvements
Bullet list of specific, actionable improvements the candidate can make to
their resume (wording, structure, quantifying results, etc.).

## Keywords to Consider
Bullet list of keywords/phrases from the job description the candidate
could naturally add to their resume, IF genuinely supported by their real
experience (never suggest fabricating anything).

## Priority Action Plan
A numbered list (3-5 items) of the highest-impact next steps the candidate
should take, in priority order.
"""

    review_task = Task(
        description=task_description,
        expected_output=(
            "A complete Markdown document with all nine required section "
            "headers, each filled with specific, evidence-based content."
        ),
        agent=reviewer,
    )

    crew = Crew(
        agents=[reviewer],
        tasks=[review_task],
        verbose=False,
        memory=False,
    )

    return crew


def run_review(resume_text: str, job_description: str):
    """
    Runs the crew and returns (success: bool, result_text_or_error: str).
    Never raises — always returns a user-safe message on failure.
    """
    try:
        crew = build_crew(resume_text, job_description)
        result = crew.kickoff()
        return True, str(result)

    except Exception as e:
        error_text = str(e).lower()

        if "rate limit" in error_text or "429" in error_text:
            friendly = (
                "🚦 Groq's rate limit was reached. Please wait a minute "
                "and try again."
            )
        elif "timeout" in error_text or "timed out" in error_text:
            friendly = (
                "⏱️ The request took too long and timed out. Please try "
                "again — if it keeps happening, try a shorter resume or "
                "job description."
            )
        elif "api key" in error_text or "unauthorized" in error_text or "401" in error_text:
            friendly = (
                "🔑 The Groq API key was rejected. Please double-check the "
                "GROQ_API_KEY value in your app's Secrets settings."
            )
        elif "native provider" in error_text or "litellm" in error_text:
            friendly = (
                "⚙️ The AI model connection is misconfigured. This is a "
                "setup issue, not something caused by your input. Please "
                "let the app owner know so they can check the LLM "
                "configuration in app.py."
            )
        elif "model" in error_text and ("not found" in error_text or "decommission" in error_text):
            friendly = (
                "🤖 The configured Groq model is unavailable or has been "
                "retired. Please update GROQ_MODEL in your app's Secrets "
                "to a currently supported Groq production model."
            )
        else:
            friendly = (
                "❌ Something went wrong while generating the review. "
                "Please try again in a moment. If the problem continues, "
                "try shortening the resume or job description."
            )

        return False, friendly


# ---------------------------------------------------------------------------
# 6. USER INTERFACE
# ---------------------------------------------------------------------------
st.title("📄 Resume Review Agent")
st.write(
    "Paste or upload a resume, paste a target job description, and get a "
    "structured, honest review — no invented skills, no guesswork."
)

with st.expander("🔒 Privacy Notice", expanded=False):
    st.write(
        "Your resume and job description are sent securely to the "
        "configured LLM provider (Groq) only to generate this review. "
        "Nothing is permanently stored by this application."
    )

st.subheader("1. Your Resume")
resume_input_method = st.radio(
    "How would you like to provide your resume?",
    options=["Paste text", "Upload PDF"],
    horizontal=True,
)

resume_text = ""

if resume_input_method == "Paste text":
    resume_text = st.text_area(
        "Paste your resume text here",
        height=220,
        placeholder="Paste the full text of your resume...",
    )
else:
    uploaded_pdf = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])
    if uploaded_pdf is not None:
        with st.spinner("Extracting text from PDF..."):
            resume_text = extract_pdf_text(uploaded_pdf)
        if resume_text:
            st.success("Resume text extracted successfully.")
            with st.expander("Preview extracted text"):
                st.text(resume_text[:2000] + ("..." if len(resume_text) > 2000 else ""))

st.subheader("2. Target Job Description")
job_description = st.text_area(
    "Paste the job description here",
    height=220,
    placeholder="Paste the full job description text...",
)

st.divider()

review_clicked = st.button("🔍 Review My Resume", type="primary", use_container_width=True)

if review_clicked:
    # --- Input validation ---
    if not resume_text or not resume_text.strip():
        st.warning("Please paste your resume text or upload a readable PDF before continuing.")
    elif not job_description or not job_description.strip():
        st.warning("Please paste the target job description before continuing.")
    elif len(resume_text.strip()) < 30:
        st.warning("The resume text looks too short to review. Please check your input.")
    elif len(job_description.strip()) < 30:
        st.warning("The job description looks too short to review. Please check your input.")
    else:
        with st.spinner("Analyzing your resume against the job description... this can take up to a minute."):
            success, output = run_review(resume_text.strip(), job_description.strip())

        st.divider()
        if success:
            st.subheader("📋 Your Resume Review")
            st.markdown(output)
        else:
            st.error(output)

st.divider()
st.caption(
    "Built with Streamlit, CrewAI, and Groq. This tool provides guidance "
    "only and does not guarantee job outcomes."
)
