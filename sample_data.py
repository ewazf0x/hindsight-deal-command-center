"""Seed data for the Acme Corp enterprise deal demo.

The module deliberately keeps all sample history in plain Python structures so it
can be loaded into Hindsight without pulling in a database or a fixture library.
Each interaction has a stable, meaningful ``document_id`` and a ready-to-use
memory payload for ``client.retain(...)``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


# Keep this identifier stable. A Hindsight bank is the persistent memory for one
# deal, so every retain/reflect operation for Acme should use this same value.
ACME_DEAL_BANK_ID = "sales-deal-acme-corp"


@dataclass(frozen=True, slots=True)
class DealProfile:
    """High-level information shown in the app sidebar and memory context."""

    account_name: str
    opportunity_name: str
    product: str
    stage: str
    owner: str
    estimated_arr_usd: int
    target_close_date: str
    champion: str
    economic_buyer: str
    description: str

    def as_metadata(self) -> dict[str, str]:
        """Return flat, Hindsight-friendly metadata shared by every record."""

        return {
            "account": self.account_name,
            "opportunity": self.opportunity_name,
            "product": self.product,
            "deal_stage": self.stage,
            "deal_owner": self.owner,
            "estimated_arr_usd": str(self.estimated_arr_usd),
            "target_close_date": self.target_close_date,
            "champion": self.champion,
            "economic_buyer": self.economic_buyer,
        }


@dataclass(frozen=True, slots=True)
class DealInteraction:
    """One sales interaction, formatted for reliable Hindsight retention."""

    document_id: str
    occurred_at: str
    interaction_type: str
    title: str
    participants: tuple[str, ...]
    content: str
    context: str
    metadata: Mapping[str, str]

    def to_memory_payload(self) -> dict[str, Any]:
        """Return keyword arguments compatible with a Hindsight retain call.

        The caller supplies ``bank_id=ACME_DEAL_BANK_ID`` separately, which makes
        the shared bank explicit at the call site.
        """

        return {
            "document_id": self.document_id,
            "content": self.content,
            "context": self.context,
            "metadata": dict(self.metadata),
        }


ACME_DEAL = DealProfile(
    account_name="Acme Corp",
    opportunity_name="Acme Corp — Atlas Revenue Intelligence",
    product="Atlas Revenue Intelligence",
    stage="Late-stage negotiation",
    owner="Jordan Lee",
    estimated_arr_usd=180_000,
    target_close_date="2026-10-30",
    champion="Maya Chen, VP Revenue Operations",
    economic_buyer="Daniel Ortiz, Chief Revenue Officer",
    description=(
        "Enterprise manufacturer with a 46-person enterprise sales team. Acme is "
        "evaluating Atlas to improve forecast accuracy, rep coaching, and deal-risk "
        "visibility before its FY27 planning cycle."
    ),
)


SAMPLE_INTERACTIONS: tuple[DealInteraction, ...] = (
    DealInteraction(
        document_id="acme-corp-2026-09-02-discovery",
        occurred_at="2026-09-02",
        interaction_type="Discovery call",
        title="Revenue Operations discovery with Maya Chen",
        participants=(
            "Maya Chen — VP Revenue Operations, Acme Corp",
            "Owen Brooks — Director of Sales Operations, Acme Corp",
            "Jordan Lee — Account Executive, Atlas",
        ),
        context=(
            "Initial discovery for the Acme Corp Atlas Revenue Intelligence "
            "opportunity. Capture business pain, stakeholders, success criteria, "
            "and commitments that should influence future deal strategy."
        ),
        metadata={
            **ACME_DEAL.as_metadata(),
            "date": "2026-09-02",
            "interaction_type": "discovery",
            "source": "sample_history",
            "priority": "high",
        },
        content="""Meeting notes — Revenue Operations discovery

Acme's enterprise sales organization has 46 account executives and 12 frontline
managers selling into complex manufacturing accounts. Maya Chen said forecast
calls currently consume most of Monday because managers reconcile Salesforce,
Gong notes, and spreadsheet rollups by hand. Their board has challenged the CRO
on forecast variance after two consecutive quarters missed the committed number.

Primary outcomes Acme wants from Atlas:
1. Detect stalled late-stage opportunities before the weekly forecast call.
2. Give managers evidence-based coaching prompts rather than relying on call
   anecdotes.
3. Reduce forecast-preparation time from roughly six hours per manager per week
   to under two hours.

Maya is the operational champion and will coordinate evaluation. Daniel Ortiz
(CRO) is the economic buyer; he cares most about forecast accuracy and avoiding
another end-of-quarter surprise. Owen Brooks will lead day-to-day rollout if the
deal closes. Maya described the budget as "real but not unlimited" and expects a
business case tied to rep productivity before asking Daniel for approval.

Risks / objections raised:
- Reps have resisted prior tools that added manual data entry.
- Sales leadership will not tolerate a second dashboard that conflicts with
  Salesforce.
- Acme's FY27 planning cycle makes an October decision important; a November 9
  kickoff is the desired outcome.

Commitments:
- Maya will share a redacted forecast-variance report and introduce Owen to the
  Atlas team by September 5.
- Jordan will return a quantified value hypothesis using Acme's manager-hours
  estimate before the September 12 technical validation session.
""",
    ),
    DealInteraction(
        document_id="acme-corp-2026-09-12-technical-validation",
        occurred_at="2026-09-12",
        interaction_type="Technical validation",
        title="Security and integration review; competitor position clarified",
        participants=(
            "Owen Brooks — Director of Sales Operations, Acme Corp",
            "Elena Novak — Chief Information Security Officer, Acme Corp",
            "Ravi Shah — Enterprise Architect, Acme Corp",
            "Jordan Lee — Account Executive, Atlas",
            "Nina Patel — Solutions Engineer, Atlas",
        ),
        context=(
            "Technical validation for the Acme opportunity. Preserve security "
            "requirements, integration dependencies, competitor information, and "
            "the conditions for moving into procurement."
        ),
        metadata={
            **ACME_DEAL.as_metadata(),
            "date": "2026-09-12",
            "interaction_type": "technical_validation",
            "source": "sample_history",
            "priority": "high",
            "competitors": "Gong, Clari",
        },
        content="""Meeting notes — Technical validation and security review

Ravi confirmed Salesforce Sales Cloud is Acme's system of record. Atlas must use
Okta SSO and SCIM provisioning, connect through a least-privilege Salesforce
service account, and write risk signals back to Salesforce rather than requiring
reps to work in a separate system. Elena requires US data residency, a completed
security questionnaire, SOC 2 Type II documentation, and written confirmation
that Acme conversation data will not be used to train shared models.

Owen proposed a 30-day pilot with 18 enterprise AEs and three managers. The pilot
will be considered successful if Atlas identifies at least five materially at-risk
opportunities that managers validate, and if the Salesforce write-back works
without rep-side manual updates. He wants the pilot environment live by September 18.

Competitive context:
- Acme already has Gong, but its contract renews on December 31. Maya views Gong
  as strong for call recording but insufficient for cross-opportunity risk and
  forecasting workflow.
- Clari was evaluated by Finance last year. Owen said its implementation felt too
  heavy and the team did not trust the resulting forecast categories.
- Atlas is currently preferred for the combined deal-risk and manager-coaching
  story, but no vendor has been selected.

Risks / objections raised:
- Elena will block the pilot if the no-training language is vague or if the
  Salesforce permission model is broader than read/write access to agreed fields.
- Owen needs proof that Atlas complements Gong instead of creating duplicate
  work for reps.

Commitments:
- Nina will send the SOC 2 report, data-processing addendum, architecture
  diagram, and a scoped Salesforce permission matrix by September 15.
- Ravi will nominate an integration engineer once Elena clears the documentation.
""",
    ),
    DealInteraction(
        document_id="acme-corp-2026-09-19-pricing-procurement",
        occurred_at="2026-09-19",
        interaction_type="Pricing and procurement",
        title="Commercial review with Procurement; budget ceiling surfaced",
        participants=(
            "Priya Nair — Director of Strategic Procurement, Acme Corp",
            "Maya Chen — VP Revenue Operations, Acme Corp",
            "Jordan Lee — Account Executive, Atlas",
            "Erin Wallace — Deal Desk, Atlas",
        ),
        context=(
            "Commercial and procurement discussion for Acme. Retain pricing "
            "constraints, legal requirements, approval path, and any commitments "
            "that matter to closing strategy."
        ),
        metadata={
            **ACME_DEAL.as_metadata(),
            "date": "2026-09-19",
            "interaction_type": "pricing_procurement",
            "source": "sample_history",
            "priority": "critical",
            "commercial_status": "negotiating",
        },
        content="""Meeting notes — Pricing and procurement review

Atlas presented a 250-seat enterprise package at $198,000 annual subscription
plus a one-time $18,000 implementation fee. Priya said Acme's approved first-year
ceiling is $180,000 all-in. She is open to a two-year agreement if Atlas holds the
renewal increase to no more than 5% and removes the implementation fee; she does
not have authority to exceed the ceiling.

Maya reiterated that the budget case depends on showing fewer forecast-surprise
losses and manager time savings. She will support a two-year term only if the
pilot success criteria and Salesforce write-back are explicitly represented in
the order form or statement of work.

Procurement process and blockers:
- Acme requires its MSA addendum, DPA, security questionnaire, and vendor
  insurance certificate before routing for signature.
- Priya needs a revised order form by September 23 to reserve the October 30 target
  close in the procurement queue.
- Legal typically takes 10 business days after it receives a complete packet.
- Auto-renewal language and unrestricted price increases are non-starters.

Negotiation signal: Priya did not challenge product fit; price and contractual
protections are the active obstacles. She said that a compliant $180,000 all-in,
two-year proposal would be "straightforward to sponsor" internally.

Commitments:
- Jordan and Erin will return a revised two-year proposal at $180,000 first-year
  total, with implementation waived and a 5% renewal cap, by September 23.
- Maya will bring Daniel Ortiz into the next commercial review after the revised
  proposal is received.
""",
    ),
    DealInteraction(
        document_id="acme-corp-2026-09-26-executive-commitment",
        occurred_at="2026-09-26",
        interaction_type="Executive alignment",
        title="CRO conditional commitment and close plan",
        participants=(
            "Daniel Ortiz — Chief Revenue Officer, Acme Corp",
            "Maya Chen — VP Revenue Operations, Acme Corp",
            "Priya Nair — Director of Strategic Procurement, Acme Corp",
            "Jordan Lee — Account Executive, Atlas",
        ),
        context=(
            "Executive alignment conversation for the Acme opportunity. Capture "
            "the economic buyer's decision criteria, conditional commitment, final "
            "risks, and the concrete close plan."
        ),
        metadata={
            **ACME_DEAL.as_metadata(),
            "date": "2026-09-26",
            "interaction_type": "executive_alignment",
            "source": "sample_history",
            "priority": "critical",
            "decision_status": "conditional_verbal_commitment",
        },
        content="""Meeting notes — Executive alignment and conditional commitment

Daniel Ortiz reviewed the value hypothesis and said Atlas is the leading option
because it addresses forecast confidence without asking managers to create more
spreadsheets. He confirmed this is now a choice between Atlas and renewing Gong;
Clari is no longer an active finalist. Daniel wants a November 9 kickoff so the
new process is established before Q4 pipeline reviews.

Daniel made a conditional verbal commitment: he will sponsor approval and ask
Finance to release funds if the final agreement is $180,000 all-in for year one,
the two-year renewal cap remains at 5%, and Elena signs off on the security and
Salesforce permission package. He does not view this as a signed deal yet; the
conditions must be resolved before he will authorize a signature.

Final decision criteria:
- The pilot must demonstrate at least five manager-validated at-risk deals
  and Salesforce write-back with no rep-side manual updates.
- Security approval must include explicit no-training language for Acme data.
- The order form must waive implementation, preserve the $180,000 first-year
  total, and attach the pilot success criteria.

Close plan:
- Atlas sends the revised order form and complete security/legal packet by
  September 29.
- Elena and Ravi will complete the security review by October 13.
- Priya will route the approved package to Daniel and Finance by October 21.
- Daniel expects signature by October 30 if no new security or legal issues arise.

Risk assessment: The deal has a credible executive sponsor and a defined path,
but it remains at risk if security approval slips or Atlas changes the agreed
commercial terms. Maya asked for a short weekly status note until signature.
""",
    ),
)


def get_sample_interactions() -> tuple[DealInteraction, ...]:
    """Return the immutable four-interaction Acme history for demo seeding."""

    return SAMPLE_INTERACTIONS


if len(SAMPLE_INTERACTIONS) != 4:  # Defensive guard: the demo is intentionally four beats.
    raise RuntimeError("Acme demo history must contain exactly four interactions.")
