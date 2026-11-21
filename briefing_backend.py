"""Evidence retrieval, ranking, and structured synthesis for Briefly."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse

import requests


TRUSTED_DOMAINS = (".gov", ".edu", "reuters.com", "apnews.com", "bloomberg.com", "ft.com", "wsj.com")

BRIEF_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "headline": {"type": "string"},
        "executive_summary": {"type": "string"},
        "meeting_thesis": {"type": "string"},
        "signals": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "what_changed": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["High", "Medium", "Low"]},
                    "source_index": {"type": "integer"},
                },
                "required": ["title", "what_changed", "why_it_matters", "confidence", "source_index"],
            },
        },
        "meeting_plan": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"moment": {"type": "string"}, "move": {"type": "string"}},
                "required": ["moment", "move"],
            },
        },
        "questions": {"type": "array", "items": {"type": "string"}},
        "watchouts": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["headline", "executive_summary", "meeting_thesis", "signals", "meeting_plan", "questions", "watchouts"],
}


@dataclass(frozen=True)
class Source:
    title: str
    url: str
    snippet: str
    published_date: str
    domain: str
    quality: int


def _quality(url: str) -> int:
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    return 3 if any(domain.endswith(item) or domain == item for item in TRUSTED_DOMAINS) else 2


def retrieve_evidence(subject: str, api_key: str, days: int = 30) -> list[Source]:
    """Retrieve and normalize recent, relevant web evidence through Tavily."""
    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": api_key,
            "query": f"{subject} latest news announcements leadership product launches partnerships funding",
            "topic": "news",
            "days": days,
            "max_results": 10,
            "search_depth": "advanced",
        },
        timeout=35,
    )
    response.raise_for_status()
    raw = response.json().get("results", [])
    evidence = [
        Source(
            title=item.get("title", "Untitled source"),
            url=item.get("url", ""),
            snippet=item.get("content", "").strip(),
            published_date=item.get("published_date", "Date unavailable"),
            domain=urlparse(item.get("url", "")).netloc.removeprefix("www."),
            quality=_quality(item.get("url", "")),
        )
        for item in raw
        if item.get("url") and item.get("content")
    ]
    return sorted(evidence, key=lambda item: item.quality, reverse=True)


def demo_brief(subject: str, meeting_date: date, objective: str) -> dict:
    """An honest, useful empty-state briefing that never makes up facts."""
    objective_text = objective or "understand priorities and identify a valuable next step"
    return {
        "headline": "Research workspace ready",
        "executive_summary": f"Briefly is ready to prepare you for {subject} on {meeting_date:%d %b %Y}. Connect research and model credentials to turn recent, source-backed evidence into a decision brief.",
        "meeting_thesis": f"Use the first few minutes to confirm the meeting objective: {objective_text}.",
        "signals": [],
        "meeting_plan": [
            {"moment": "Open", "move": "Set a shared outcome and confirm the most important topic to resolve."},
            {"moment": "Explore", "move": "Use the evidence to ask what has changed and where attention is focused now."},
            {"moment": "Close", "move": "Name an owner, a next action, and a date for follow-up."},
        ],
        "questions": [
            f"What has changed most recently for {subject}?",
            "Which priority should guide this conversation?",
            "What concrete next step would make this meeting valuable?",
        ],
        "watchouts": ["No claims are shown until the app can verify them against a source."],
    }


def evidence_only_brief(subject: str, meeting_date: date, objective: str, sources: list[Source]) -> dict:
    """A transparent fallback when retrieval is configured but AI synthesis is not."""
    signals = [
        {
            "title": source.title,
            "what_changed": source.snippet[:360],
            "why_it_matters": "Review the original source and decide whether this development changes your meeting agenda.",
            "confidence": "Medium",
            "source_index": index,
        }
        for index, source in enumerate(sources[:4], start=1)
    ]
    brief = demo_brief(subject, meeting_date, objective)
    brief.update(
        {
            "headline": "Evidence collected - synthesis unavailable",
            "executive_summary": f"Briefly retrieved {len(sources)} recent sources on {subject}. Add an OpenAI API key to convert these signals into a tailored analysis.",
            "signals": signals,
            "watchouts": ["These are retrieved source excerpts, not AI-generated conclusions.", "Verify each source before using it in a meeting."],
        }
    )
    return brief


def synthesize_briefing(
    subject: str,
    meeting_date: date,
    objective: str,
    sources: list[Source],
    api_key: str,
    model: str,
) -> dict:
    """Create a strict, source-indexed briefing using the OpenAI Responses API."""
    if not sources:
        return demo_brief(subject, meeting_date, objective)

    from openai import OpenAI

    source_packet = "\n\n".join(
        f"SOURCE {index}\nTITLE: {source.title}\nURL: {source.url}\nDATE: {source.published_date}\nCONTENT: {source.snippet[:1800]}"
        for index, source in enumerate(sources, start=1)
    )
    prompt = f"""You are Briefly, an evidence-first meeting intelligence analyst.
Prepare a concise, decision-ready briefing for a meeting with: {subject}
Meeting date: {meeting_date:%d %B %Y}
Objective: {objective or 'Understand priorities and identify a useful next step.'}

Rules:
- Use only claims directly supported by the numbered sources.
- Select 3 to 5 material developments, not a news dump.
- Every signal must cite exactly one source_index.
- Explain business implications in plain language.
- Use High only where the source directly supports the claim; otherwise Medium or Low.
- Do not invent numbers, people, dates, or strategy.
- The meeting plan must be practical and tailored to the objective.

Evidence packet:
{source_packet}"""

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        input=prompt,
        text={"format": {"type": "json_schema", "name": "meeting_brief", "strict": True, "schema": BRIEF_SCHEMA}},
    )
    return json.loads(response.output_text)
