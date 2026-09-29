"""Streamlit interface for the memory-first Sales Deal Intelligence Agent."""

from __future__ import annotations

import html
from datetime import date, datetime, time
from typing import Any

import streamlit as st

from agent import (
    AgentError,
    BaselineResponse,
    IntelligenceResponse,
    SalesDealIntelligenceAgent,
)
from sample_data import ACME_DEAL


st.set_page_config(
    page_title="Sales Deal Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_design_system() -> None:
    """Apply a restrained, dark-friendly visual system without extra dependencies."""

    st.markdown(
        """
        <style>
            :root {
                --canvas: #08111f;
                --surface: #101d2e;
                --surface-raised: #14243a;
                --line: rgba(148, 181, 222, 0.18);
                --ink: #eaf2ff;
                --muted: #96a9c1;
                --mint: #67e8c3;
                --blue: #7ab8ff;
                --amber: #f7c66a;
                --danger: #ff94a3;
            }

            .stApp {
                background:
                    radial-gradient(circle at 78% -8%, rgba(47, 138, 190, 0.22), transparent 32rem),
                    radial-gradient(circle at 0% 25%, rgba(30, 101, 110, 0.18), transparent 25rem),
                    var(--canvas);
                color: var(--ink);
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0d1929 0%, #091321 100%);
                border-right: 1px solid var(--line);
            }

            [data-testid="stSidebar"] * {
                color: var(--ink);
            }

            h1, h2, h3 {
                letter-spacing: -0.025em;
            }

            .hero {
                max-width: 880px;
                padding: 1.15rem 0 1.6rem 0;
            }

            .eyebrow {
                color: var(--mint);
                font-size: 0.73rem;
                font-weight: 750;
                letter-spacing: 0.14em;
                margin-bottom: 0.55rem;
            }

            .hero h1 {
                color: var(--ink);
                font-size: clamp(2.1rem, 4vw, 3.45rem);
                font-weight: 740;
                line-height: 1.04;
                margin: 0 0 0.6rem 0;
            }

            .hero p {
                color: var(--muted);
                font-size: 1.05rem;
                line-height: 1.6;
                margin: 0;
            }

            .memory-banner {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.82rem 1rem;
                margin: 0.15rem 0 1.15rem 0;
                background: rgba(28, 106, 111, 0.18);
                border: 1px solid rgba(103, 232, 195, 0.35);
                border-radius: 0.7rem;
                color: var(--ink);
            }

            .memory-led {
                width: 0.65rem;
                height: 0.65rem;
                border-radius: 50%;
                background: var(--mint);
                box-shadow: 0 0 0.6rem rgba(103, 232, 195, 0.9);
                flex: 0 0 auto;
            }

            .memory-label {
                color: var(--mint);
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.11em;
            }

            .memory-detail {
                color: var(--muted);
                font-size: 0.84rem;
                margin-left: auto;
                text-align: right;
            }

            .comparison-card {
                height: 100%;
                border: 1px solid var(--line);
                border-radius: 0.8rem;
                padding: 1rem 1.05rem;
                background: rgba(16, 29, 46, 0.78);
            }

            .comparison-card--baseline {
                border-color: rgba(247, 198, 106, 0.28);
            }

            .comparison-card--memory {
                border-color: rgba(103, 232, 195, 0.33);
                background: rgba(16, 52, 61, 0.45);
            }

            .card-kicker {
                color: var(--muted);
                font-size: 0.7rem;
                font-weight: 800;
                letter-spacing: 0.11em;
                margin-bottom: 0.35rem;
            }

            .comparison-card--memory .card-kicker {
                color: var(--mint);
            }

            .comparison-card--baseline .card-kicker {
                color: var(--amber);
            }

            .comparison-card h4 {
                margin: 0 0 0.45rem 0;
                color: var(--ink);
                font-size: 1rem;
            }

            .comparison-card p {
                color: var(--muted);
                line-height: 1.5;
                margin: 0;
                font-size: 0.88rem;
            }

            .trace-chip {
                display: inline-block;
                padding: 0.35rem 0.62rem;
                border: 1px solid rgba(103, 232, 195, 0.42);
                border-radius: 999px;
                background: rgba(39, 130, 114, 0.15);
                color: var(--mint);
                font-size: 0.72rem;
                font-weight: 750;
                letter-spacing: 0.04em;
            }

            .sidebar-label {
                color: var(--muted);
                font-size: 0.7rem;
                font-weight: 800;
                letter-spacing: 0.11em;
                text-transform: uppercase;
            }

            .sidebar-deal {
                color: var(--ink);
                font-size: 1.32rem;
                font-weight: 700;
                margin: 0.15rem 0 0.45rem 0;
            }

            .sidebar-copy {
                color: var(--muted);
                font-size: 0.84rem;
                line-height: 1.45;
            }

            [data-testid="stMetric"] {
                background: rgba(20, 36, 58, 0.58);
                border: 1px solid var(--line);
                border-radius: 0.6rem;
                padding: 0.6rem 0.7rem;
            }

            [data-testid="stMetricLabel"] {
                color: var(--muted);
            }

            [data-testid="stMetricValue"] {
                color: var(--ink);
            }

            .stButton > button {
                border-radius: 0.58rem;
                font-weight: 650;
            }

            div[data-baseweb="tab-list"] {
                gap: 0.55rem;
                border-bottom: 1px solid var(--line);
                margin-bottom: 1.1rem;
            }

            button[data-baseweb="tab"] {
                height: 2.65rem;
                color: var(--muted);
                font-weight: 650;
            }

            button[data-baseweb="tab"][aria-selected="true"] {
                color: var(--mint);
            }

            [data-testid="stChatMessage"] {
                border: 1px solid var(--line);
                border-radius: 0.75rem;
                background: rgba(16, 29, 46, 0.6);
                margin-bottom: 0.85rem;
            }

            .stTextArea textarea, .stTextInput input {
                background: rgba(9, 19, 33, 0.9);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def get_agent() -> SalesDealIntelligenceAgent:
    """Keep one configured API client bundle for the lifetime of this app process."""

    return SalesDealIntelligenceAgent()


def initialize_state() -> None:
    """Set predictable session state without relying on a local database."""

    defaults: dict[str, Any] = {
        "sample_history_loaded": False,
        "memory_document_count": 0,
        "memory_fact_count": None,
        "memory_revision": 0,
        "last_brief_revision": -1,
        "brief_response": None,
        "previous_brief_response": None,
        "chat_messages": [],
        "last_memory_event": "No interactions retained in this browser session.",
        "new_interaction_time": time(hour=10),
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def memory_is_available() -> bool:
    """Whether there is at least one recorded interaction to reflect over."""

    return (
        st.session_state.memory_document_count > 0
        or (st.session_state.memory_fact_count or 0) > 0
    )


DEMO_FOLLOW_UP = {
    "new_interaction_title": "Security clearance and pilot validation complete",
    "new_interaction_type": "Executive review",
    "new_interaction_date": date(2026, 10, 13),
    "new_interaction_time": time(hour=15),
    "new_interaction_participants": (
        "Elena Novak (CISO), Ravi Shah (Enterprise Architect), Maya Chen (VP RevOps), "
        "Jordan Lee (Atlas)"
    ),
    "new_interaction_notes": (
        "Elena approved the no-training language, US data residency, and scoped Salesforce "
        "permission matrix. Ravi confirmed Salesforce write-back is working with no rep-side "
        "manual updates. Maya reported that the pilot surfaced six materially at-risk deals, "
        "all validated by managers. Daniel said there are no remaining product or security "
        "concerns and he expects Finance to approve once Procurement routes the final packet."
    ),
    "new_interaction_objections": (
        "No new technical or commercial blockers. Legal needs the final order form attached "
        "to the procurement packet."
    ),
    "new_interaction_commitments": (
        "Elena cleared security. Maya will provide the pilot validation summary. Priya will "
        "route the final packet to Daniel and Finance by October 21."
    ),
    "new_interaction_next_step": (
        "Atlas sends the final order form and pilot summary today; Procurement routes by October 21."
    ),
}


def prepare_demo_follow_up() -> None:
    """Fill the logging form with a material update for the live before/after demo."""

    st.session_state.update(DEMO_FOLLOW_UP)


def render_sidebar(agent: SalesDealIntelligenceAgent) -> None:
    """Render fixed account context and live persistent-memory state."""

    with st.sidebar:
        st.markdown('<div class="sidebar-label">Deal command center</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="sidebar-deal">{html.escape(ACME_DEAL.account_name)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="sidebar-copy">{html.escape(ACME_DEAL.description)}</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        first_metric, second_metric = st.columns(2)
        first_metric.metric("Stage", ACME_DEAL.stage)
        second_metric.metric("Est. ARR", f"USD {ACME_DEAL.estimated_arr_usd // 1_000}k")
        st.metric("Target close", ACME_DEAL.target_close_date)

        st.markdown('<div class="sidebar-label">Buying committee</div>', unsafe_allow_html=True)
        st.caption(f"Champion  ·  {ACME_DEAL.champion}")
        st.caption(f"Economic buyer  ·  {ACME_DEAL.economic_buyer}")

        st.divider()
        st.markdown('<div class="sidebar-label">Persistent memory</div>', unsafe_allow_html=True)
        st.metric("New interactions", st.session_state.memory_document_count)
        fact_count = st.session_state.memory_fact_count
        st.metric("Bank memory facts", fact_count if fact_count is not None else "—")
        st.caption(f"Bank  ·  {agent.settings.bank_id}")
        st.caption(st.session_state.last_memory_event)

        if agent.has_memory_credentials:
            st.success("Hindsight memory configured")
        else:
            st.warning("Hindsight API key required")

        if st.button(
            "Check existing memory",
            use_container_width=True,
            disabled=not agent.has_memory_credentials,
        ):
            try:
                with st.spinner("Checking the persistent Acme memory bank..."):
                    status = agent.inspect_memory_bank()
                st.session_state.memory_fact_count = status.fact_count
                st.session_state.last_memory_event = (
                    f"Reconnected to {status.fact_count} retained memory facts."
                    if status.is_populated
                    else "The persistent bank is ready for its first interaction."
                )
                if status.is_populated:
                    st.success("Existing deal memory is ready to use.")
                else:
                    st.info("No retained facts yet. Load the Acme sample history to begin.")
            except AgentError as exc:
                st.error(str(exc))

        if agent.has_groq_credentials:
            st.caption("Groq baseline comparison configured")
        else:
            st.caption("Groq baseline is optional until its API key is added.")

        with st.expander("What the agent retains"):
            st.markdown(
                "- Stakeholders and influence\n"
                "- Objections, risks, and competitors\n"
                "- Pricing, legal, and security conditions\n"
                "- Dates, commitments, and close-plan changes"
            )


def render_memory_banner(agent: SalesDealIntelligenceAgent) -> None:
    """Make active memory status unmistakable across the main workflow."""

    if memory_is_available():
        detail_parts: list[str] = []
        if st.session_state.memory_document_count:
            detail_parts.append(
                f"{st.session_state.memory_document_count} interactions added this session"
            )
        if st.session_state.memory_fact_count is not None:
            detail_parts.append(f"{st.session_state.memory_fact_count} extracted facts in bank")
        detail_parts.append(f"bank {agent.settings.bank_id}")
        detail = " · ".join(detail_parts)
        label = "PERSISTENT MEMORY ACTIVE"
    else:
        detail = "Load the Acme history to activate deal-level memory."
        label = "MEMORY NOT YET LOADED"

    st.markdown(
        f"""
        <div class="memory-banner">
            <div class="memory-led"></div>
            <div>
                <div class="memory-label">{label}</div>
                <div style="color: #d9e8fa; font-size: 0.92rem; margin-top: 0.16rem;">
                    Hindsight retains the deal narrative across sessions.
                </div>
            </div>
            <div class="memory-detail">{html.escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_before_after_explainer() -> None:
    """Show the live-demo value proposition before any reflection is generated."""

    before, after = st.columns(2)
    with before:
        st.markdown(
            """
            <div class="comparison-card comparison-card--baseline">
                <div class="card-kicker">BEFORE · NO HISTORY</div>
                <h4>Generic and cautious</h4>
                <p>A model without interaction history cannot know the sponsor, the price ceiling,
                the security blocker, or what was promised last week.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with after:
        st.markdown(
            """
            <div class="comparison-card comparison-card--memory">
                <div class="card-kicker">AFTER · HINDSIGHT MEMORY</div>
                <h4>Specific, timeline-aware intelligence</h4>
                <p>Reflect reasons over the full deal record, connecting a new update to earlier
                objections, competitor posture, terms, and commitments.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_memory_trace(response: IntelligenceResponse) -> None:
    """Render proof that a response was grounded in the configured Hindsight bank."""

    trace = response.trace
    evidence_parts: list[str] = []
    if trace.recalled_count:
        evidence_parts.append(f"{trace.recalled_count} relevant memories recalled")
    if trace.reflected_fact_count:
        evidence_parts.append(f"{trace.reflected_fact_count} facts cited by Reflect")
    source_phrase = " · ".join(evidence_parts) or "persistent bank queried"
    st.markdown(
        f'<span class="trace-chip">◆ HINDSIGHT MEMORY CONSULTED · '
        f'{html.escape(source_phrase)}</span>',
        unsafe_allow_html=True,
    )
    with st.expander("Inspect memory evidence", expanded=False):
        st.caption(f"Reflection bank: {trace.bank_id}")
        if trace.recall_note:
            st.caption(trace.recall_note)
        if trace.source_excerpts:
            for excerpt in trace.source_excerpts:
                st.markdown(f"- {excerpt}")
        else:
            st.caption(
                "The connected Hindsight deployment did not return individual fact excerpts "
                "for this reflection, but the persistent bank was queried."
            )


def trace_label(response: IntelligenceResponse) -> str:
    """Build a compact retrieval-and-reflection label for saved chat history."""

    trace = response.trace
    parts: list[str] = []
    if trace.recalled_count:
        parts.append(f"{trace.recalled_count} memories recalled")
    if trace.reflected_fact_count:
        parts.append(f"{trace.reflected_fact_count} facts cited")
    return " · ".join(parts) or "persistent bank queried"


def baseline_label(response: BaselineResponse, agent: SalesDealIntelligenceAgent) -> str:
    """Describe whether the deliberately history-free comparison used Groq."""

    if response.generated_by_groq:
        return f"Generated by Groq ({agent.settings.groq_model}) with no deal history"
    return response.status_note or "No interaction history was supplied to the baseline"


def render_deal_brief(response: IntelligenceResponse) -> None:
    """Present the direct Hindsight reflection as the primary output."""

    st.markdown("### Memory-powered Deal Brief")
    st.caption("Generated directly with Hindsight Reflect from the retained Acme deal history.")
    with st.container(border=True):
        st.markdown(response.text)
    render_memory_trace(response)


def render_memory_evolution() -> None:
    """Let a live demo compare the brief before and after a retained update."""

    previous_brief = st.session_state.previous_brief_response
    if previous_brief is None:
        return

    st.markdown("### Memory evolution")
    st.success(
        "This brief incorporates a newer retained interaction. The Latest memory delta above "
        "shows how the deal view changed while preserving earlier context."
    )
    with st.expander("Compare the Deal Brief before the latest memory update", expanded=False):
        st.caption("This version was generated before the most recent interaction entered Hindsight.")
        st.markdown(previous_brief.text)
        st.caption(f"Prior brief evidence: {trace_label(previous_brief)}")
        for excerpt in previous_brief.trace.source_excerpts:
            st.markdown(f"- {excerpt}")


def render_chat_history() -> None:
    """Rehydrate prior question/answer pairs after normal Streamlit reruns."""

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                st.markdown(
                    f'<span class="trace-chip">◆ HINDSIGHT MEMORY CONSULTED · '
                    f'{html.escape(message.get("evidence_label", "persistent bank queried"))}</span>',
                    unsafe_allow_html=True,
                )
                with st.expander("Before memory: context-free baseline", expanded=False):
                    st.caption(message.get("baseline_label", "No-history baseline"))
                    st.markdown(message.get("baseline", ""))


def ask_and_render(agent: SalesDealIntelligenceAgent, question: str) -> None:
    """Generate a Groq baseline and a Hindsight reflection side by side in chat."""

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        baseline = agent.generate_no_memory_baseline(question)
        with st.spinner("Hindsight is connecting the question to the complete deal history..."):
            response = agent.answer_question(question)

        st.markdown("#### With persistent deal memory")
        st.markdown(response.text)
        render_memory_trace(response)

        with st.expander("Before memory: context-free baseline", expanded=False):
            st.caption(baseline_label(baseline, agent))
            st.markdown(baseline.text)

    st.session_state.chat_messages.extend(
        [
            {"role": "user", "content": question},
            {
                "role": "assistant",
                "content": "#### With persistent deal memory\n\n" + response.text,
                "evidence_label": trace_label(response),
                "baseline": baseline.text,
                "baseline_label": baseline_label(baseline, agent),
            },
        ]
    )


def render_deal_brief_tab(agent: SalesDealIntelligenceAgent) -> None:
    """Render the main demo workflow: retain, reflect, refresh."""

    st.markdown("## The deal brief gets smarter as the memory grows")
    st.caption(
        "Retain source interactions once. Then regenerate the same brief whenever the deal changes."
    )
    render_memory_banner(agent)
    render_before_after_explainer()
    st.write("")

    controls, status = st.columns([1.45, 1])
    with controls:
        load_label = (
            "Refresh Acme sample history"
            if st.session_state.sample_history_loaded
            else "Load Acme's 4-interaction history"
        )
        if st.button(
            load_label,
            type="primary",
            use_container_width=True,
            disabled=not agent.has_memory_credentials,
        ):
            try:
                with st.spinner("Retaining discovery, technical, commercial, and executive history..."):
                    result = agent.seed_sample_history()
                if not st.session_state.sample_history_loaded:
                    st.session_state.memory_document_count += 4
                st.session_state.sample_history_loaded = True
                st.session_state.memory_revision += 1
                st.session_state.brief_response = None
                st.session_state.last_memory_event = "Sample history refreshed in Hindsight."
                try:
                    memory_status = agent.inspect_memory_bank()
                    st.session_state.memory_fact_count = memory_status.fact_count
                    st.success(
                        f"{result.message} Hindsight extracted {memory_status.fact_count} memory facts."
                    )
                except AgentError:
                    st.success(result.message)
            except AgentError as exc:
                st.error(str(exc))

    with status:
        if memory_is_available():
            wording = (
                "Brief is current"
                if st.session_state.last_brief_revision == st.session_state.memory_revision
                else "Brief needs a memory refresh"
            )
            st.info(wording)
        else:
            st.info("No source interactions loaded yet.")

    generate_disabled = not agent.has_memory_credentials or not memory_is_available()
    if st.button(
        "Generate Deal Brief from memory",
        type="secondary",
        use_container_width=True,
        disabled=generate_disabled,
    ):
        try:
            with st.spinner("Hindsight Reflect is synthesizing the complete deal narrative..."):
                st.session_state.brief_response = agent.generate_deal_brief()
            st.session_state.last_brief_revision = st.session_state.memory_revision
            st.success("Deal Brief refreshed from persistent memory.")
        except AgentError as exc:
            st.error(str(exc))

    if not agent.has_memory_credentials:
        st.warning(
            "Add HINDSIGHT_API_KEY to .env and restart the app to load or reflect over deal memory."
        )
    elif not memory_is_available():
        st.info(
            "Start by loading Acme's history, or use Check existing memory in the sidebar "
            "to reconnect to a prior demo session."
        )

    response = st.session_state.brief_response
    if response is not None:
        st.write("")
        render_deal_brief(response)
        render_memory_evolution()


def render_ask_anything_tab(agent: SalesDealIntelligenceAgent) -> None:
    """Render memory-backed deal chat and a clearly labelled no-memory comparison."""

    st.markdown("## Ask anything about the deal")
    st.caption(
        "Every memory-enabled answer comes from Hindsight Reflect. Expand the comparison to see "
        "what a context-free model could say before the history existed."
    )
    render_memory_banner(agent)

    if not memory_is_available():
        st.info("Load the sample history in Deal Brief before asking a memory-powered question.")
        return
    if not agent.has_memory_credentials:
        st.warning("Add HINDSIGHT_API_KEY to .env and restart the app to use deal chat.")
        return

    suggested_question: str | None = None
    st.markdown("Try a high-signal question")
    options = [
        "What could stop this deal from closing by the target date?",
        "What did Acme commit to, and what do we still owe them?",
        "How should we position against Gong and Clari?",
    ]
    option_columns = st.columns(3)
    for column, option in zip(option_columns, options):
        if column.button(option, use_container_width=True):
            suggested_question = option

    render_chat_history()
    typed_question = st.chat_input("Ask about stakeholders, risk, pricing, commitments, or next steps")
    question = typed_question or suggested_question
    if not question:
        return

    try:
        ask_and_render(agent, question)
    except AgentError as exc:
        st.error(str(exc))


def render_log_interaction_tab(agent: SalesDealIntelligenceAgent) -> None:
    """Capture a new interaction and retain its decision-relevant detail."""

    st.markdown("## Log a new interaction")
    st.caption(
        "A new note is retained with a meaningful document ID, context, timestamp, metadata, and "
        "sales-specific tags. The next reflection sees it alongside the complete prior history."
    )
    render_memory_banner(agent)

    if not agent.has_memory_credentials:
        st.warning("Add HINDSIGHT_API_KEY to .env and restart the app to save interaction memory.")
        return

    with st.expander("Demo accelerator: make the brief visibly smarter", expanded=False):
        st.write(
            "Load a realistic security-clearance and pilot-validation update. Save it, then "
            "refresh the Deal Brief to see the new information change the deal posture."
        )
        if st.button("Load high-impact demo update", use_container_width=True):
            prepare_demo_follow_up()
            st.success("The interaction form is ready to review and retain.")

    with st.form("new_interaction_form", clear_on_submit=True):
        left, right = st.columns(2)
        with left:
            title = st.text_input(
                "Interaction title",
                placeholder="e.g. Security approval follow-up with Elena",
                key="new_interaction_title",
            )
            interaction_type = st.selectbox(
                "Interaction type",
                [
                    "Customer call",
                    "Email",
                    "Executive review",
                    "Technical workshop",
                    "Pricing / procurement",
                    "Internal account review",
                ],
                key="new_interaction_type",
            )
        with right:
            interaction_date = st.date_input("Interaction date", key="new_interaction_date")
            interaction_time = st.time_input("Interaction time", key="new_interaction_time")
            participants = st.text_input(
                "Participants",
                placeholder="e.g. Elena Novak (CISO), Ravi Shah (EA), Jordan Lee",
                key="new_interaction_participants",
            )

        notes = st.text_area(
            "What happened? *",
            height=160,
            placeholder=(
                "Capture the customer language, decisions, context, and signals. "
                "Specific detail gives future reflections better evidence."
            ),
            key="new_interaction_notes",
        )
        details_left, details_right = st.columns(2)
        with details_left:
            objections = st.text_area(
                "Objections / risks",
                height=105,
                placeholder="What could slow, block, or change the deal?",
                key="new_interaction_objections",
            )
        with details_right:
            commitments = st.text_area(
                "Commitments made or received",
                height=105,
                placeholder="Who committed to what, and by when?",
                key="new_interaction_commitments",
            )
        next_step = st.text_input(
            "Next step",
            placeholder="e.g. Elena to confirm the revised permission matrix by Friday",
            key="new_interaction_next_step",
        )
        submitted = st.form_submit_button("Retain interaction in Hindsight", type="primary")

    if not submitted:
        return

    try:
        occurred_at = datetime.combine(interaction_date, interaction_time)
        with st.spinner("Extracting durable deal intelligence and writing it to persistent memory..."):
            result = agent.log_interaction(
                occurred_at=occurred_at,
                interaction_type=interaction_type,
                participants=participants,
                notes=notes,
                objections=objections,
                commitments=commitments,
                next_step=next_step,
                title=title,
            )
        st.session_state.memory_document_count += 1
        st.session_state.memory_revision += 1
        if st.session_state.brief_response is not None:
            st.session_state.previous_brief_response = st.session_state.brief_response
        st.session_state.brief_response = None
        st.session_state.last_memory_event = f"New {interaction_type.lower()} retained in Hindsight."
        try:
            memory_status = agent.inspect_memory_bank()
            st.session_state.memory_fact_count = memory_status.fact_count
        except AgentError:
            pass
        st.success(result.message)
        st.info(
            "Memory changed. Return to Deal Brief and refresh it to see the latest memory delta "
            "and updated risk posture."
        )
    except AgentError as exc:
        st.error(str(exc))


def main() -> None:
    """Run the app."""

    apply_design_system()
    initialize_state()
    agent = get_agent()
    render_sidebar(agent)

    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">MEMORY-FIRST REVENUE INTELLIGENCE</div>
            <h1>Every deal conversation, remembered.</h1>
            <p>Turn scattered sales interactions into a living, evidence-grounded view of the
            Acme Corp opportunity — then watch that view improve when new information arrives.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    deal_brief_tab, ask_tab, log_tab = st.tabs(
        ["◆ Deal Brief", "◈ Ask Anything", "＋ Log New Interaction"]
    )
    with deal_brief_tab:
        render_deal_brief_tab(agent)
    with ask_tab:
        render_ask_anything_tab(agent)
    with log_tab:
        render_log_interaction_tab(agent)


if __name__ == "__main__":
    main()
