# Briefly

Briefly is an evidence-first pre-meeting intelligence product. It researches the previous 30 days, ranks public sources, then creates a concise decision brief with linked evidence, a meeting thesis, practical conversation moves, questions, and watchouts.

## Run locally

```powershell
cd "C:\Users\KIIT\Desktop\hackathon"
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## API keys

The local Tavily key is read from `.streamlit/secrets.toml`. That file is intentionally ignored by Git and must never be committed.

To enable AI synthesis, add your own OpenAI key to the same local file:

```toml
TAVILY_API_KEY = "tvly-your-key"
OPENAI_API_KEY = "sk-your-key"
```

If no OpenAI key is configured, Briefly still retrieves and displays a source-backed evidence ledger without inventing conclusions.

## Safe GitHub submission

Before creating or pushing a repository, verify that secrets are ignored:

```powershell
git status --short
git check-ignore .streamlit/secrets.toml
```

The second command should print `.streamlit/secrets.toml`. Never upload that file. If a secret is ever committed or publicly exposed, revoke it and generate a replacement immediately.

## Architecture

```text
Meeting context
    ↓
Tavily retrieval (30-day window)
    ↓
Source normalization + quality ranking
    ↓
OpenAI Structured Outputs (optional)
    ↓
Decision brief + evidence ledger + meeting plan
```
