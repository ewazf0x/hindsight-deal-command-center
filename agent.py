"""Core memory and reasoning services for the Sales Deal Intelligence Agent.

The design is intentionally memory-first:
* every source interaction is retained in one stable Hindsight bank;
* Hindsight reflect() produces every memory-backed brief and answer;
* Groq produces the deliberately context-free baseline used in the live demo.

Keeping the integration behind this small service layer makes it straightforward
to connect a CRM, call recorder, or email source later without changing the UI.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

from sample_data import ACME_DEAL, ACME_DEAL_BANK_ID, DealInteraction, get_sample_interactions


load_dotenv()

DEFAULT_HINDSIGHT_BASE_URL = "https://api.hindsight.vectorize.io"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


class AgentError(RuntimeError):
    """Base exception for an expected application-level failure."""


class ConfigurationError(AgentError):
    """Raised when a requested capability does not have its required API key."""


class MemoryServiceError(AgentError):
    """Raised when Hindsight cannot retain or reflect over deal memory."""


@dataclass(frozen=True, slots=True)
class AgentSettings:
    """Runtime configuration loaded from environment variables."""

    hindsight_api_key: str | None
    hindsight_base_url: str
    bank_id: str
    groq_api_key: str | None
    groq_model: str

    @classmethod
    def from_environment(cls) -> "AgentSettings":
        """Load configuration without exposing or logging any secret values."""

        return cls(
            hindsight_api_key=_clean_environment_value("HINDSIGHT_API_KEY"),
            hindsight_base_url=(
                _clean_environment_value("HINDSIGHT_BASE_URL")
                or DEFAULT_HINDSIGHT_BASE_URL
            ).rstrip("/"),
            bank_id=_clean_environment_value("HINDSIGHT_BANK_ID") or ACME_DEAL_BANK_ID,
            groq_api_key=_clean_environment_value("GROQ_API_KEY"),
            groq_model=_clean_environment_value("GROQ_MODEL") or DEFAULT_GROQ_MODEL,
        )


@dataclass(frozen=True, slots=True)
class MemoryTrace:
    """A compact, user-facing trace showing that persistent memory was consulted."""

    bank_id: str
    recalled_count: int
    reflected_fact_count: int
    source_excerpts: tuple[str, ...]
    recall_note: str | None = None


@dataclass(frozen=True, slots=True)
class IntelligenceResponse:
    """A Hindsight-generated answer with transparent memory evidence."""

    text: str
    trace: MemoryTrace
    engine_label: str = "Hindsight Reflect"


@dataclass(frozen=True, slots=True)
class BaselineResponse:
    """The deliberately history-free answer used for the before/after demo."""

    text: str
    generated_by_groq: bool
    status_note: str | None = None


@dataclass(frozen=True, slots=True)
class MemoryWriteResult:
    """Result returned after an interaction is safely retained."""

    document_id: str
    retained_items: int
    message: str


@dataclass(frozen=True, slots=True)
class MemoryBankStatus:
    """A lightweight view of the existing persistent Hindsight bank."""

    bank_id: str
    fact_count: int

    @property
    def is_populated(self) -> bool:
        """Whether the bank contains any retained memory facts."""

        return self.fact_count > 0


class SalesDealIntelligenceAgent:
    """Owns the Hindsight bank and the supporting no-memory Groq baseline."""

    def __init__(self, settings: AgentSettings | None = None) -> None:
        self.settings = settings or AgentSettings.from_environment()
        self._hindsight: Hindsight | None = None
        self._groq: Groq | None = None
        self._bank_ready = False

    @property
    def has_memory_credentials(self) -> bool:
        """Whether Hindsight operations can be authenticated."""

        return bool(self.settings.hindsight_api_key)

    @property
    def has_groq_credentials(self) -> bool:
        """Whether the optional before-memory comparison can use Groq."""

        return bool(self.settings.groq_api_key)

    def seed_sample_history(self) -> MemoryWriteResult:
        """Load the four Acme source interactions idempotently into Hindsight.

        Stable document IDs plus update_mode="replace" mean a demo can be reset
        safely without creating duplicate source documents.
        """

        client = self._memory_client()
        self._ensure_bank(client)

        retained_items = 0
        document_ids: list[str] = []
        for interaction in get_sample_interactions():
            response = self._retain_sample_interaction(client, interaction)
            retained_items += _response_item_count(response)
            document_ids.append(interaction.document_id)

        return MemoryWriteResult(
            document_id=", ".join(document_ids),
            retained_items=retained_items,
            message="Acme's four historical interactions are now persistent deal memory.",
        )

    def inspect_memory_bank(self) -> MemoryBankStatus:
        """Check whether a persistent Acme bank already contains extracted facts.

        This makes a prior demo session discoverable without retaining the sample
        history again. Hindsight stores many extracted facts per source document,
        so the count is intentionally labelled as memory facts, not interactions.
        """

        client = self._memory_client()
        self._ensure_bank(client)
        try:
            response = client.list_memories(
                bank_id=self.settings.bank_id,
                limit=1,
                offset=0,
            )
        except Exception as exc:
            raise MemoryServiceError(
                _memory_error_message("inspect the persistent deal memory", exc)
            ) from exc

        total = getattr(response, "total", None)
        if total is None:
            total = len(getattr(response, "items", None) or [])
        try:
            fact_count = max(0, int(total))
        except (TypeError, ValueError):
            fact_count = 0
        return MemoryBankStatus(bank_id=self.settings.bank_id, fact_count=fact_count)

    def log_interaction(
        self,
        *,
        occurred_at: datetime,
        interaction_type: str,
        participants: str,
        notes: str,
        objections: str = "",
        commitments: str = "",
        next_step: str = "",
        title: str = "",
    ) -> MemoryWriteResult:
        """Retain a new sales interaction with high-quality sales context."""

        clean_type = interaction_type.strip()
        clean_notes = notes.strip()
        if not clean_type:
            raise AgentError("Choose an interaction type before saving it to memory.")
        if not clean_notes:
            raise AgentError("Add interaction notes before saving them to memory.")

        client = self._memory_client()
        self._ensure_bank(client)

        event_time = _as_utc_datetime(occurred_at)
        event_slug = _slugify(clean_type)
        document_id = (
            f"acme-corp:interaction:{event_time.strftime('%Y%m%dT%H%M%SZ')}:"
            f"{event_slug}:{uuid4().hex[:8]}"
        )
        clean_title = title.strip() or f"{clean_type} — Acme Corp"
        clean_participants = participants.strip() or "Participants not recorded"

        content = _format_logged_interaction(
            title=clean_title,
            occurred_at=event_time,
            interaction_type=clean_type,
            participants=clean_participants,
            notes=clean_notes,
            objections=objections.strip(),
            commitments=commitments.strip(),
            next_step=next_step.strip(),
        )
        metadata = {
            **ACME_DEAL.as_metadata(),
            "date": event_time.date().isoformat(),
            "interaction_type": event_slug,
            "source": "user_logged",
            "participants": clean_participants,
        }

        try:
            response = client.retain(
                bank_id=self.settings.bank_id,
                document_id=document_id,
                content=content,
                context=(
                    "New Acme Corp sales interaction. Extract durable deal intelligence: "
                    "stakeholders, objections, competitor signals, commercial terms, dates, "
                    "commitments, risks, and next steps. Preserve the difference between an "
                    "explicit customer commitment and a seller inference."
                ),
                metadata=metadata,
                timestamp=event_time,
                tags=["sales-deal", "acme-corp", "user-logged", event_slug],
                update_mode="replace",
            )
        except Exception as exc:  # SDK errors vary by transport and deployment.
            raise MemoryServiceError(_memory_error_message("save this interaction", exc)) from exc

        _ensure_retain_succeeded(response)
        return MemoryWriteResult(
            document_id=document_id,
            retained_items=_response_item_count(response),
            message="New interaction retained. Future reflections will use it with the full deal history.",
        )

    def generate_deal_brief(self) -> IntelligenceResponse:
        """Generate the main Deal Brief directly through Hindsight reflect()."""

        return self._reflect(
            query="""Create a rigorous, executive-ready Deal Brief for the Acme Corp opportunity.

Synthesize every relevant retained interaction into concise Markdown. Begin with
an executive snapshot that states deal health and why. Then use these exact
sections: Latest memory delta; Buying committee and influence; Business case and
success metrics; Competition and differentiation; Commercial position; Risks and
open conditions; Commitments and close plan; Recommended next actions.

The Latest memory delta must identify the newest material update, explain how it
changes the prior deal view, and call out any remaining dependency. Include
specific dates, owners, amounts, and conditions where retained. Distinguish a
customer's explicit commitment from a sales inference. Reconcile changes over
time, surface contradictions or unknowns plainly, and do not invent information
that is absent from memory.""",
            context=(
                "You are preparing a pre-call intelligence brief for the account team. "
                "The output must be decision-useful, evidence-grounded, and based on Acme's "
                "persistent deal memory rather than generic sales advice."
            ),
        )

    def answer_question(self, question: str) -> IntelligenceResponse:
        """Answer a user question through Hindsight's memory-aware reasoning."""

        clean_question = question.strip()
        if not clean_question:
            raise AgentError("Ask a specific question about the Acme opportunity.")

        return self._reflect(
            query=(
                f"Answer this question about the Acme Corp deal: {clean_question}\n\n"
                "Use only retained deal evidence. Be direct and practical. Name relevant "
                "stakeholders, dates, amounts, commitments, objections, or uncertainty when "
                "they are available. If the history does not support an answer, say so rather "
                "than guessing."
            ),
            context=(
                "You are a precise sales intelligence analyst. The requester needs an answer "
                "that reflects the entire deal history, including earlier commitments and any "
                "later changes to them."
            ),
        )

    def generate_no_memory_baseline(self, question: str) -> BaselineResponse:
        """Ask Groq for an intentionally context-free answer for the live comparison."""

        clean_question = question.strip() or "What should I know before my next customer call?"
        if not self.has_groq_credentials:
            return BaselineResponse(
                text=(
                    "Without retained interaction history, I cannot responsibly identify the "
                    "deal's stakeholders, risks, pricing, objections, or next step. I would need "
                    "the account team's notes before offering a specific recommendation."
                ),
                generated_by_groq=False,
                status_note="GROQ_API_KEY is not configured; displaying a safe history-free baseline.",
            )

        try:
            completion = self._groq_client().chat.completions.create(
                model=self.settings.groq_model,
                temperature=0.1,
                max_tokens=220,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a careful B2B sales assistant. You have no meeting notes, "
                            "CRM history, or customer memory. Do not invent names, prices, dates, "
                            "competitors, commitments, or deal stage. Explain briefly what cannot "
                            "be known and give a useful generic next step."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Account: Acme Corp. Answer this sales question without access to any "
                            f"deal history: {clean_question}"
                        ),
                    },
                ],
            )
            text = (completion.choices[0].message.content or "").strip()
            if text:
                return BaselineResponse(text=text, generated_by_groq=True)
        except Exception:
            # The baseline is a demo aid; a temporarily unavailable Groq service must
            # never prevent the persistent-memory workflow from working.
            pass

        return BaselineResponse(
            text=(
                "Without retained interaction history, I cannot responsibly identify the deal's "
                "stakeholders, risks, pricing, objections, or next step. I would first collect "
                "the account team's notes and decision criteria."
            ),
            generated_by_groq=False,
            status_note="Groq did not return a response; displaying a safe history-free baseline.",
        )

    def _reflect(self, *, query: str, context: str) -> IntelligenceResponse:
        """Recall relevant evidence, then run a high-budget Hindsight reflection."""

        client = self._memory_client()
        self._ensure_bank(client)
        recalled_sources, recall_note = self._recall_relevant_memories(client, query)
        try:
            response = client.reflect(
                bank_id=self.settings.bank_id,
                query=query,
                context=context,
                budget="high",
                max_tokens=2_000,
                include_facts=True,
            )
        except Exception as exc:  # SDK errors vary by transport and deployment.
            raise MemoryServiceError(_memory_error_message("reflect over deal memory", exc)) from exc

        response_text = str(getattr(response, "text", "") or "").strip()
        if not response_text:
            raise MemoryServiceError(
                "Hindsight returned an empty reflection. Confirm that the deal history has been loaded."
            )

        return IntelligenceResponse(
            text=response_text,
            trace=_trace_from_reflection(
                response,
                self.settings.bank_id,
                recalled_sources=recalled_sources,
                recall_note=recall_note,
            ),
        )

    def _recall_relevant_memories(
        self,
        client: Hindsight,
        query: str,
    ) -> tuple[tuple[Any, ...], str | None]:
        """Retrieve focused evidence for transparency before Hindsight reflects.

        Reflect already performs its own retrieval. This explicit recall is used
        to make the evidence visible to the operator. A recall-only issue never
        removes the stronger Reflect path.
        """

        try:
            response = client.recall(
                bank_id=self.settings.bank_id,
                query=query,
                budget="high",
                max_tokens=1_400,
            )
        except Exception:
            return (
                (),
                "A separate recall trace was unavailable; Hindsight Reflect still queried the bank.",
            )

        results = getattr(response, "results", None)
        if results is None:
            results = getattr(response, "memories", None)
        return tuple(results or ()), None

    def _retain_sample_interaction(self, client: Hindsight, interaction: DealInteraction) -> Any:
        """Retain one source record with an explicit event time and durable metadata."""

        try:
            response = client.retain(
                bank_id=self.settings.bank_id,
                timestamp=_as_utc_datetime(datetime.fromisoformat(interaction.occurred_at)),
                tags=[
                    "sales-deal",
                    "acme-corp",
                    "sample-history",
                    str(interaction.metadata["interaction_type"]),
                ],
                update_mode="replace",
                **interaction.to_memory_payload(),
            )
        except Exception as exc:  # Preserve the interaction identity in the UI error.
            raise MemoryServiceError(
                _memory_error_message(f"load '{interaction.title}'", exc)
            ) from exc

        _ensure_retain_succeeded(response)
        return response

    def _ensure_bank(self, client: Hindsight) -> None:
        """Create or update the stable bank once per running app instance."""

        if self._bank_ready:
            return

        try:
            client.create_bank(
                bank_id=self.settings.bank_id,
                name="Acme Corp Deal Intelligence",
                background=(
                    "Persistent intelligence for the Atlas Revenue Intelligence opportunity at "
                    "Acme Corp. Preserve the entire sales narrative across discovery, technical "
                    "validation, pricing, procurement, executive alignment, and new interactions."
                ),
                retain_mission=(
                    "Extract durable sales facts: stakeholders and roles, business pains, success "
                    "metrics, objections, competitors, pricing and terms, dates, dependencies, "
                    "risks, and explicit commitments. Keep source timing and certainty clear."
                ),
                reflect_mission=(
                    "Act as a rigorous B2B sales deal intelligence analyst. Build answers from "
                    "stored evidence, reconcile the timeline, distinguish fact from inference, "
                    "and clearly state when the record is incomplete."
                ),
            )
        except Exception as exc:
            raise MemoryServiceError(
                _memory_error_message("initialize the deal memory bank", exc)
            ) from exc

        self._bank_ready = True

    def _memory_client(self) -> Hindsight:
        """Create and reuse the official Hindsight client only when it is needed."""

        if not self.has_memory_credentials:
            raise ConfigurationError(
                "Add HINDSIGHT_API_KEY to .env, then restart Streamlit to use persistent deal memory."
            )
        if self._hindsight is None:
            try:
                self._hindsight = Hindsight(
                    base_url=self.settings.hindsight_base_url,
                    api_key=self.settings.hindsight_api_key,
                    timeout=60.0,
                )
            except Exception as exc:
                raise ConfigurationError(
                    "Could not initialize the Hindsight client. Check HINDSIGHT_BASE_URL and your API key."
                ) from exc
        return self._hindsight

    def _groq_client(self) -> Groq:
        """Create and reuse the Groq client for the pre-memory comparison only."""

        if not self.has_groq_credentials:
            raise ConfigurationError("Add GROQ_API_KEY to .env to generate the no-memory baseline.")
        if self._groq is None:
            self._groq = Groq(api_key=self.settings.groq_api_key)
        return self._groq


def _clean_environment_value(name: str) -> str | None:
    """Return a stripped environment value, treating whitespace as unset."""

    value = os.getenv(name, "").strip()
    return value or None


def _as_utc_datetime(value: datetime | date) -> datetime:
    """Normalize source times so temporal retrieval is reliable in Hindsight."""

    if isinstance(value, datetime):
        timestamp = value
    else:
        timestamp = datetime.combine(value, time(hour=12), tzinfo=timezone.utc)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _slugify(value: str) -> str:
    """Create a compact metadata/tag-safe identifier without another dependency."""

    parts = [
        part
        for part in "".join(char if char.isalnum() else " " for char in value.lower()).split()
    ]
    return "-".join(parts) or "interaction"


def _format_logged_interaction(
    *,
    title: str,
    occurred_at: datetime,
    interaction_type: str,
    participants: str,
    notes: str,
    objections: str,
    commitments: str,
    next_step: str,
) -> str:
    """Make manual notes legible to Hindsight's fact and timeline extraction."""

    return f"""Sales interaction — {title}

Occurred at: {occurred_at.isoformat()}
Interaction type: {interaction_type}
Participants: {participants}

Notes:
{notes}

Objections or concerns:
{objections or 'None recorded'}

Commitments made or received:
{commitments or 'None recorded'}

Next step:
{next_step or 'Not specified'}
"""


def _ensure_retain_succeeded(response: Any) -> None:
    """Convert an unsuccessful SDK response into a clear application failure."""

    if getattr(response, "success", True) is False:
        raise MemoryServiceError("Hindsight did not confirm that this interaction was retained.")


def _response_item_count(response: Any) -> int:
    """Read the public retain count defensively across compatible SDK releases."""

    try:
        return int(getattr(response, "items_count", 1))
    except (TypeError, ValueError):
        return 1


def _trace_from_reflection(
    response: Any,
    bank_id: str,
    *,
    recalled_sources: tuple[Any, ...] = (),
    recall_note: str | None = None,
) -> MemoryTrace:
    """Merge explicit recall evidence with Hindsight's reflection evidence."""

    based_on = getattr(response, "based_on", None)
    memories = getattr(based_on, "memories", None)
    if memories is None and isinstance(based_on, (list, tuple)):
        memories = based_on
    source_memories = list(memories or [])

    excerpts: list[str] = []
    for source in (*recalled_sources, *source_memories):
        excerpt = _source_excerpt(source)
        if excerpt and excerpt not in excerpts:
            excerpts.append(excerpt)
        if len(excerpts) == 6:
            break
    return MemoryTrace(
        bank_id=bank_id,
        recalled_count=len(recalled_sources),
        reflected_fact_count=len(source_memories),
        source_excerpts=tuple(excerpts),
        recall_note=recall_note,
    )


def _source_excerpt(source: Any) -> str:
    """Turn a Hindsight fact into a short display string without assuming SDK internals."""

    text = str(getattr(source, "text", "") or getattr(source, "content", "") or "").strip()
    if not text:
        return ""
    source_type = str(getattr(source, "type", "memory") or "memory")
    occurred_at = str(
        getattr(source, "occurred_at", "")
        or getattr(source, "occurred_start", "")
        or getattr(source, "mentioned_at", "")
        or ""
    ).strip()
    prefix = " · ".join(part for part in (source_type.title(), occurred_at[:10]) if part)
    clipped_text = text if len(text) <= 300 else f"{text[:297].rstrip()}..."
    return f"{prefix}: {clipped_text}" if prefix else clipped_text


def _memory_error_message(action: str, error: Exception) -> str:
    """Keep transport detail useful but concise and avoid leaking configuration."""

    detail = str(error).strip().replace("\n", " ")
    if len(detail) > 260:
        detail = f"{detail[:257]}..."
    suffix = f" Details: {detail}" if detail else ""
    return f"Unable to {action} in Hindsight.{suffix}"
