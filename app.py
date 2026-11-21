"""Briefly - evidence-first intelligence for high-stakes meetings."""

from __future__ import annotations

import os
from datetime import date, timedelta

import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from briefing_backend import Source, demo_brief, evidence_only_brief, retrieve_evidence, synthesize_briefing


st.set_page_config(page_title="Briefly", page_icon=":material/auto_awesome:", layout="wide")


def get_secret(name: str) -> str:
    """Read a key from Streamlit secrets first, then the local environment."""
    try:
        return str(st.secrets.get(name, os.getenv(name, "")))
    except StreamlitSecretNotFoundError:
        # A secrets.toml file is optional; sidebar entry and environment variables still work.
        return os.getenv(name, "")


def initialize_state() -> None:
    st.session_state.setdefault("briefing", None)
    st.session_state.setdefault("sources", [])
    st.session_state.setdefault("brief_subject", "")
    st.session_state.setdefault("brief_date", date.today() + timedelta(days=3))
    st.session_state.setdefault("brief_objective", "")


def confidence_icon(level: str) -> str:
    return {"High": ":material/verified:", "Medium": ":material/fact_check:", "Low": ":material/help:"}.get(level, ":material/help:")


def source_for(signal: dict, sources: list[Source]) -> Source | None:
    index = signal.get("source_index", 0)
    if isinstance(index, int) and 0 < index <= len(sources):
        return sources[index - 1]
    return None


def briefing_markdown(briefing: dict, subject: str, sources: list[Source]) -> str:
    document = [f"# {briefing['headline']}", f"## {subject}", "", briefing["executive_summary"], "", "## Meeting thesis", briefing["meeting_thesis"], "", "## What changed"]
    for signal in briefing["signals"]:
        document.append(f"- **{signal['title']}** ({signal['confidence']} confidence): {signal['what_changed']}  \n  *Why it matters:* {signal['why_it_matters']}")
        source = source_for(signal, sources)
        if source:
            document.append(f"  Source: {source.url}")
    document.extend(["", "## Meeting plan"])
    document.extend(f"- **{item['moment']}:** {item['move']}" for item in briefing["meeting_plan"])
    document.extend(["", "## Questions to ask"])
    document.extend(f"- {question}" for question in briefing["questions"])
    document.extend(["", "## Watchouts"])
    document.extend(f"- {watchout}" for watchout in briefing["watchouts"])
    return "\n".join(document)


initialize_state()

with st.sidebar:
    st.logo("assets/briefly-logo.svg", size="large")
    st.caption("A clear point of view before the conversation starts.")
    st.divider()
    st.subheader("Connections")
    tavily_key = st.text_input("Tavily API key", value=get_secret("TAVILY_API_KEY"), type="password", key="tavily_key", help="Retrieves recent public web sources.")
    openai_key = st.text_input("OpenAI API key", value=get_secret("OPENAI_API_KEY"), type="password", key="openai_key", help="Builds the structured briefing from retrieved evidence.")
    model = st.selectbox("Analysis model", ["gpt-4o-mini", "gpt-4o"], key="analysis_model")
    st.caption("Keys are used for this session only and are never written to disk.")
    st.divider()
    st.subheader("The Briefly method")
    st.markdown("1. Capture the meeting objective\n2. Retrieve the latest evidence\n3. Separate signal from noise\n4. Build a cited conversation plan")

header, header_action = st.columns([4, 1], vertical_alignment="center")
with header:
    st.title("Know the room before you enter it")
    st.markdown("Briefly turns the last 30 days of public signals into a source-linked point of view, so every important meeting starts with context instead of catch-up.")
with header_action:
    if st.button("Open sample", icon=":material/visibility:", width="stretch"):
        today = date.today() + timedelta(days=3)
        st.session_state.briefing = demo_brief("your meeting counterpart", today, "align on a meaningful next step")
        st.session_state.sources = []
        st.session_state.brief_subject = "Your meeting counterpart"
        st.session_state.brief_date = today
        st.session_state.brief_objective = "Align on a meaningful next step"

st.divider()

with st.container(border=True):
    st.subheader("Prepare for the conversation")
    st.caption("Tell Briefly who is in the room and what a successful outcome looks like.")
    with st.form("briefing_form", border=False):
        primary, secondary = st.columns([1.15, 0.85], vertical_alignment="bottom")
        with primary:
            subject = st.text_input("Who are you meeting?", placeholder="Company, executive, customer, or prospect", key="subject")
        with secondary:
            meeting_date = st.date_input("Meeting date", value=date.today() + timedelta(days=3), min_value=date.today(), key="meeting_date")
        objective = st.text_area("What would make this meeting a success?", placeholder="For example: assess a partnership opportunity, understand strategic priorities, or agree on a commercial next step.", height=104, key="objective")
        generate = st.form_submit_button("Build decision brief", icon=":material/auto_awesome:", type="primary", width="stretch")

output = st.container()

if generate:
    if not subject.strip():
            st.error("Add the company or person you are preparing to meet.", icon=":material/person_search:")
    else:
        sources: list[Source] = []
        with st.status("Building your briefing", expanded=True) as status:
            if tavily_key:
                st.write("Searching the last 30 days for relevant reporting and announcements")
                try:
                    sources = retrieve_evidence(subject.strip(), tavily_key)
                    st.write(f"Collected and ranked {len(sources)} candidate sources")
                except requests.RequestException as error:
                    st.warning(f"Research service could not be reached: {error}")
            else:
                st.write("Research key not connected - preparing an evidence-ready workspace")

            if sources and openai_key:
                st.write("Synthesizing only from retrieved evidence")
                try:
                    briefing = synthesize_briefing(subject.strip(), meeting_date, objective.strip(), sources, openai_key, model)
                except Exception as error:  # API and model errors are shown without losing sources.
                    st.warning(f"AI synthesis could not complete: {error}")
                    briefing = evidence_only_brief(subject.strip(), meeting_date, objective.strip(), sources)
            elif sources:
                st.write("Showing source-backed evidence while AI synthesis is disconnected")
                briefing = evidence_only_brief(subject.strip(), meeting_date, objective.strip(), sources)
            else:
                briefing = demo_brief(subject.strip(), meeting_date, objective.strip())
            status.update(label="Briefing ready", state="complete", expanded=False)

        st.session_state.briefing = briefing
        st.session_state.sources = sources
        st.session_state.brief_subject = subject.strip()
        st.session_state.brief_date = meeting_date
        st.session_state.brief_objective = objective.strip()

briefing = st.session_state.briefing
sources = st.session_state.sources

with output:
    if not briefing:
        st.space("medium")
        st.info("Start with a meeting counterpart and an objective. Briefly will build a research-backed workspace and attach evidence to every material claim.", icon=":material/lightbulb:")
    else:
        st.space("small")
        report_header, report_action = st.columns([4, 1], vertical_alignment="center")
        with report_header:
            st.caption(f"DECISION BRIEF  •  {st.session_state.brief_date:%d %b %Y}")
            st.header(st.session_state.brief_subject)
            st.markdown(f"**{briefing['headline']}**  \n{briefing['executive_summary']}")
        with report_action:
            st.download_button(
                "Download .md",
                data=briefing_markdown(briefing, st.session_state.brief_subject, sources),
                file_name=f"briefly-{st.session_state.brief_subject.lower().replace(' ', '-')}.md",
                mime="text/markdown",
                icon=":material/download:",
                width="stretch",
            )

        metric_one, metric_two, metric_three = st.columns(3)
        metric_one.metric("Evidence reviewed", len(sources), help="Sources collected during the 30-day research window.")
        metric_two.metric("Decision signals", len(briefing["signals"]), help="Material developments selected for the meeting.")
        metric_three.metric("Meeting date", st.session_state.brief_date.strftime("%d %b"))
        st.divider()

        overview, evidence, meeting_plan = st.tabs(["Executive view", "Evidence ledger", "Meeting plan"])
        with overview:
            st.subheader("The meeting thesis")
            st.write(briefing["meeting_thesis"])
            st.subheader("What changed")
            if not briefing["signals"]:
                st.info("No evidence claims yet. Connect Tavily to retrieve recent sources; connect OpenAI as well for a tailored analysis.", icon=":material/manage_search:")
            for position, signal in enumerate(briefing["signals"], start=1):
                source = source_for(signal, sources)
                with st.container(border=True):
                    signal_heading, signal_confidence = st.columns([5, 1], vertical_alignment="center")
                    signal_heading.markdown(f"**{position}. {signal['title']}**")
                    signal_confidence.caption(f"{confidence_icon(signal['confidence'])} {signal['confidence']}")
                    st.write(signal["what_changed"])
                    st.caption(f"WHY IT MATTERS  •  {signal['why_it_matters']}")
                    if source:
                        st.link_button(f"Open source · {source.domain}", source.url, icon=":material/open_in_new:", width="content")

        with evidence:
            st.subheader("Evidence ledger")
            st.caption("Briefly ranks source quality before synthesis. Open the original source before relying on a material claim.")
            if not sources:
                st.info("No sources have been retrieved yet.", icon=":material/article:")
            for number, source in enumerate(sources, start=1):
                with st.expander(f"{number}. {source.title}", icon=":material/article:"):
                    st.caption(f"{source.domain}  •  {source.published_date}  •  source-quality {source.quality}/3")
                    st.write(source.snippet)
                    st.link_button("Read original source", source.url, icon=":material/open_in_new:")

        with meeting_plan:
            st.subheader("A practical way to run the conversation")
            plan_columns = st.columns(len(briefing["meeting_plan"]))
            for column, step in zip(plan_columns, briefing["meeting_plan"]):
                with column:
                    with st.container(border=True, height="stretch"):
                        st.caption(step["moment"].upper())
                        st.write(step["move"])
            st.subheader("Questions worth carrying in")
            for question in briefing["questions"]:
                st.markdown(f"- {question}")
            if briefing["watchouts"]:
                st.subheader("Watchouts")
                for watchout in briefing["watchouts"]:
                    st.warning(watchout, icon=":material/visibility:")
