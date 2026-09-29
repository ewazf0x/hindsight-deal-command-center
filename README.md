# Sales Deal Intelligence Agent

A memory-first sales copilot for complex opportunities. It turns every customer interaction into durable deal intelligence, so the next brief and answer reflect the full history—not just the latest note.

The included Acme Corp scenario is designed for a clear live demonstration: load four realistic interactions, inspect the evidence-backed Deal Brief, add a material update, and refresh the brief to see the deal posture change.

## What it does

- Retains source interactions in one stable Hindsight bank with timestamps, meaningful document IDs, context, tags, and sales metadata.
- Explicitly recalls relevant memory before each response, then uses Hindsight `reflect()` to produce the Deal Brief and deal Q&A.
- Shows a visible evidence trace: memories recalled, facts cited by Reflect, and a compact set of source excerpts.
- Uses Groq for the deliberately context-free “before memory” comparison, making the value of persistent memory easy to demonstrate.
- Lets the account team log new interactions without losing the prior deal narrative.

## Requirements

- Python 3.11 or newer
- A Hindsight API key
- A Groq API key for the no-memory comparison

## Quick start

1. Create and activate a virtual environment.

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies.

   ```powershell
   pip install -r requirements.txt
   ```

3. Create your local environment file.

   ```powershell
   Copy-Item .env.example .env
   ```

   Add `HINDSIGHT_API_KEY` and `GROQ_API_KEY` to `.env`. The default Hindsight Cloud URL is already configured; only change `HINDSIGHT_BASE_URL` for another Hindsight deployment.

4. Start the application.

   ```powershell
   streamlit run app.py
   ```

## Demo flow

1. Open **Deal Brief** and select **Load Acme's 4-interaction history**.
2. Generate the Deal Brief. Expand **Inspect memory evidence** to show the explicit recall and Reflect evidence.
3. In **Ask Anything**, ask about close risk, competition, or commercial commitments. Expand **Before memory** to compare the history-free Groq answer with the memory-grounded answer.
4. In **Log New Interaction**, use **Load high-impact demo update**, retain it, then regenerate the Deal Brief.
5. Call out the **Latest memory delta**, then expand the saved pre-update brief to compare before and after: security clearance and pilot validation change the close plan while prior commercial conditions remain in view.

Use **Check existing memory** in the sidebar to reconnect to a previously populated bank after a browser refresh.

## Configuration

| Variable | Purpose |
| --- | --- |
| `HINDSIGHT_API_KEY` | Authenticates Hindsight persistent memory. |
| `HINDSIGHT_BASE_URL` | Hindsight endpoint; defaults to Hindsight Cloud. |
| `HINDSIGHT_BANK_ID` | Stable identifier that isolates and preserves this deal's memory. |
| `GROQ_API_KEY` | Authenticates the no-memory comparison model. |
| `GROQ_MODEL` | Groq model used for the comparison. |

Keep `HINDSIGHT_BANK_ID` stable for a deal. Changing it creates a different memory bank; keeping it consistent allows the intelligence to compound over time. Never commit `.env` or API keys.
