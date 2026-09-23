# 📄 Resume Review Agent

A beginner-friendly, single-agent AI app that compares a resume against a
job description and gives a structured, honest review — built with
**CrewAI**, **Streamlit**, and **Groq**.

It **never invents** skills, experience, or education that aren't actually
in the resume. If something can't be confirmed, it's labeled
"Unknown / Not Demonstrated."

---

## 1. How It Works (Architecture)

- **1 CrewAI Agent** — a "Senior Resume Reviewer" persona.
- **1 CrewAI Task** — one instruction that asks the agent to compare the
  resume and job description and return a 9-section Markdown report.
- **1 CrewAI Crew** — runs that single agent on that single task.
- **Streamlit** — the web interface: text boxes, PDF upload, buttons, and
  the final formatted report.
- **Groq** — the LLM provider that actually generates the review text,
  called through CrewAI's built-in `LLM` class.

No databases, no multi-agent chains, no authentication, no Docker — just
one file (`app.py`) doing one job well.

---

## 2. Project File Structure

```
resume-review-agent/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    └── secrets.toml.example
```

> Note: your **real** secrets file (`.streamlit/secrets.toml`) is only
> used if you run the app locally, and it is excluded from GitHub by
> `.gitignore`. On Streamlit Community Cloud, you'll paste your key into
> the dashboard instead (see Step 5 below) — you do not upload a real
> secrets file at all.

---

## 3. GitHub Setup Instructions

1. Go to [github.com](https://github.com) and click **New repository**.
2. Name it `resume-review-agent` (or anything you like), set it to
   **Public** or **Private**, and click **Create repository**.
3. On the new repo's page, click **uploading an existing file**.
4. Drag in all five items exactly as they appear above: `app.py`,
   `requirements.txt`, `README.md`, `.gitignore`, and the whole
   `.streamlit` folder (containing `secrets.toml.example`).
   - If GitHub's uploader won't accept a folder directly, create the file
     `.streamlit/secrets.toml.example` by typing that full path into the
     "Create new file" box — GitHub will make the folder automatically.
5. Scroll down and click **Commit changes**.

You should now see all 5 items listed in your repository.

---

## 4. Get a Groq API Key

1. Go to [console.groq.com](https://console.groq.com) and sign in.
2. Open **API Keys** in the left sidebar.
3. Click **Create API Key**, name it anything, and **copy the key**
   immediately (you won't be able to see it again).

---

## 5. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with
   your GitHub account.
2. Click **Create app** → **Deploy a public app from GitHub** (or
   "Yup, I have an app").
3. Choose:
   - **Repository:** `your-username/resume-review-agent`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **Advanced settings...** before deploying:
   - Under **Python version**, select **3.11**.
   - Under **Secrets**, paste the following, replacing the placeholder
     with your real Groq key:
     ```
     GROQ_API_KEY = "your-real-groq-key-here"
     GROQ_MODEL = "openai/gpt-oss-120b"
     ```
5. Click **Save**, then click **Deploy**.
6. Wait for the build to finish (this can take a few minutes — CrewAI is a
   fairly large library). Your app will open automatically when it's
   ready.

---

## 6. Common Errors and Fixes

| Error / Symptom | Cause | Fix |
|---|---|---|
| "No Groq API key was found" | `GROQ_API_KEY` missing from Secrets | Go to your app → **Settings → Secrets**, add the key exactly as shown in Step 5, then **Reboot app**. |
| App stuck on "Installing dependencies..." for a long time | CrewAI's dependencies are large (several hundred MB) | This is normal on first deploy; it can take several minutes. If it fails outright, check the build log for the exact package that failed. |
| Build fails mentioning `onnxruntime` or `chromadb` | These are internal dependencies of CrewAI unrelated to this app's features, and can occasionally fail to build on certain platforms | Reboot the app once (Streamlit Cloud sometimes retries successfully). If it persists, note the exact error and consider pinning `crewai` to a nearby patch version in `requirements.txt`. |
| "The Groq API key was rejected" | Key was copied incorrectly, has extra spaces, or was revoked | Regenerate a new key in the Groq console and update your app's Secrets. |
| "Groq's rate limit was reached" | Too many requests in a short time on the free tier | Wait about a minute and click the review button again. |
| "Groq could not find the model ..." (404 `model_not_found`) | Either Groq retired the model, or the model ID was altered before reaching Groq (older versions of this app let CrewAI strip the `openai/` from `openai/gpt-oss-120b`) | `app.py` now passes `provider="openai"` so the ID is sent unchanged. Make sure `GROQ_MODEL` in Secrets is Groq's exact ID from [console.groq.com/docs/models](https://console.groq.com/docs/models), e.g. `openai/gpt-oss-120b` or `llama-3.3-70b-versatile`, then **Reboot app**. |
| PDF upload gives "No readable text was found" | The PDF is a scanned image with no real text layer | Switch to "Paste text" and paste the resume content directly. |
| App loads but the review is empty or cut off | The resume or job description was extremely long | Try trimming to the most relevant sections and try again. |

---

## 7. Plain-English Explanation (for Beginners)

Think of this app as a very focused, very honest assistant:

1. You give it two things: your **resume** and a **job description**.
2. It hands both to a single AI "reviewer" persona (the CrewAI Agent),
   along with strict instructions: *only talk about what's actually in the
   resume — never make anything up.*
3. That reviewer (powered by a Groq-hosted AI model) reads both documents
   and writes back a structured report: what matches, what's missing,
   what's unclear, and what to improve — organized into clear sections.
4. Streamlit is just the "front window" — the part you actually see and
   click buttons on. It collects your input, shows a loading spinner while
   the AI thinks, and displays the final report neatly formatted.
5. Your API key (which pays for and authorizes the AI calls) is kept in a
   private "Secrets" vault provided by Streamlit Cloud — it's never
   visible in your code or on GitHub.

That's the whole app: one form in, one AI reviewer, one structured report
out.
