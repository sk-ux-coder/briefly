# Briefly

## Evidence-first intelligence for important meetings

Briefly helps you enter a high-stakes conversation prepared. Give it a company or person, a meeting date, and the outcome you want. It researches relevant developments from the previous 30 days and creates a concise, source-linked briefing with:

- An executive summary and meeting thesis
- Material recent developments with confidence labels
- A source ledger for verification
- A practical conversation plan
- Questions to carry into the room
- Watchouts and uncertainty signals

## Why Briefly

Meeting preparation is often scattered across search tabs, press releases, company pages, and news articles. Briefly turns that fragmented research into a focused decision brief while keeping evidence attached to the claims that matter.

## Technology

- Streamlit for the interactive application
- Tavily for recent web research
- OpenAI Structured Outputs for consistent briefing generation
- A source-ranking and evidence-normalization layer between retrieval and synthesis

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The application opens at `http://localhost:8501`.

For local development, credentials can be provided through Streamlit's secrets mechanism:

```toml
TAVILY_API_KEY = "tvly-your-key"
OPENAI_API_KEY = "sk-your-key"
```

Save that content as `.streamlit/secrets.toml` on your own machine. Never commit the file or publish API keys in the repository.

## Deploy on Streamlit Community Cloud

Briefly is designed to deploy directly from GitHub.

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Select **Create app**.
3. Choose the repository `sk-ux-coder/briefly`.
4. Select branch `main`.
5. Set the entrypoint to `app.py`.
6. Open **Advanced settings**.
7. In the **Secrets** field, add:

```toml
TAVILY_API_KEY = "tvly-your-key"
OPENAI_API_KEY = "sk-your-key"
```

8. Click **Deploy**.

The deployed app receives its own `streamlit.app` URL. API keys belong in the deployment's Secrets settings, not in GitHub. See the [official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [official secrets guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Architecture

```text
Meeting context
    ↓
Tavily retrieval - previous 30 days
    ↓
Source normalization and quality ranking
    ↓
Evidence packet
    ↓
OpenAI structured synthesis
    ↓
Decision brief, evidence ledger, and meeting plan
```

## Repository

[github.com/sk-ux-coder/briefly](https://github.com/sk-ux-coder/briefly)
