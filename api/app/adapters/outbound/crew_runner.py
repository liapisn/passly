"""CampaignRunner backed by the real solo-founder-crew Author Flow.

This is the **second HITL adapter** on the framework's seam (alongside the
framework's own DiscordHITL): a `WebHITL` whose `review()` parks the run on an
asyncio Future and surfaces the draft for the web UI, then resolves the Future
when the founder responds over HTTP. That a web surface drops onto the same
HITLContract — unchanged — is the empirical evidence for the §3.8
substitutability claim.

The framework is imported lazily inside methods so importing this module (and
the whole app) needs neither the framework installed nor an API key — which is
what lets CI run the suite framework-free.
"""

from __future__ import annotations

import asyncio
import itertools
import os

from ...domain.models import (
    CampaignState,
    CampaignStatus,
    ReviewGate,
    ShopRecord,
)


class _WebHITL:
    """Implements the framework's HITLContract over HTTP request/response.

    Shares the runner's `states` and `futures` maps (keyed by thread_id;
    gates are sequential per run, so thread_id is a sufficient key).
    """

    def __init__(self, states: dict, futures: dict) -> None:
        self._states = states
        self._futures = futures

    async def review(self, request):  # noqa: ANN001 — framework type, imported lazily
        # Surface the draft for the UI to poll, then block on the founder.
        self._states[request.thread_id] = CampaignState(
            thread_id=request.thread_id,
            status=CampaignStatus.awaiting_review,
            gate=ReviewGate(
                turn=request.turn,
                artifact=request.artifact.content,
                options=[o.action for o in request.options],
            ),
        )
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._futures[request.thread_id] = future
        return await future

    def resolve(self, thread_id: str, decision) -> bool:  # noqa: ANN001
        future = self._futures.pop(thread_id, None)
        if future is None or future.done():
            return False
        future.set_result(decision)
        # Interim state while the graph revises or publishes; the run task
        # overwrites it with the terminal state when it finishes.
        self._states[thread_id] = CampaignState(
            thread_id=thread_id, status=CampaignStatus.drafting
        )
        return True


class SoloFounderCrewRunner:
    def __init__(self) -> None:
        self._states: dict[str, CampaignState] = {}
        self._futures: dict[str, asyncio.Future] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._hitl = _WebHITL(self._states, self._futures)
        self._counter = itertools.count(1)

    async def start(self, shop: ShopRecord) -> str:
        from solo_founder_crew.crew import Crew
        from solo_founder_crew.roles_library import make_marketing

        brief = self._brief_for(shop)
        role = make_marketing(brief)
        crew = Crew(
            brief=brief,
            roles=[role],
            llm=self._make_llm(shop),
            hitl=self._hitl,
            tools=self._publisher_registry(),
        )
        thread_id = f"camp-{next(self._counter)}"
        self._states[thread_id] = CampaignState(
            thread_id=thread_id, status=CampaignStatus.drafting
        )
        self._tasks[thread_id] = asyncio.create_task(
            self._run(crew, role, self._task_for(shop), thread_id)
        )
        return thread_id

    def get(self, thread_id: str) -> CampaignState | None:
        return self._states.get(thread_id)

    async def respond(self, thread_id: str, action: str, feedback: str | None) -> bool:
        from solo_founder_crew.hitl import FounderDecision

        return self._hitl.resolve(
            thread_id, FounderDecision(action=action, feedback=feedback)
        )

    # ── internals ────────────────────────────────────────────────────────

    async def _run(self, crew, role, task: str, thread_id: str) -> None:  # noqa: ANN001
        try:
            result = await crew.author_flow(
                task_description=task, role=role, max_revisions=2, thread_id=thread_id
            )
            self._states[thread_id] = CampaignState(
                thread_id=thread_id,
                status=CampaignStatus(result.status),
                final_artifact=result.approved_artifact,
            )
        except Exception as exc:  # surface, don't crash the server
            self._states[thread_id] = CampaignState(
                thread_id=thread_id, status=CampaignStatus.error, error=str(exc)
            )

    def _make_llm(self, shop: ShopRecord):
        """Real Haiku when a key is present (hybrid posture), else a
        deterministic mock so the demo and dev work offline."""
        if os.environ.get("ANTHROPIC_API_KEY"):
            from solo_founder_crew.llm import AnthropicLLM

            return AnthropicLLM(model="claude-haiku-4-5")

        from solo_founder_crew.llm import MockLLM

        name = shop.name
        offer = shop.design.offer_value
        draft = (
            f"📣 {name} — νέα κάρτα πιστότητας!\n\n"
            f"{offer}. Πρόσθεσέ τη στο Apple Wallet με ένα tap και μάζευε "
            f"σφραγίδες σε κάθε επίσκεψη.\n\nΘα σε περιμένουμε! ☕"
        )
        revised = draft + "\n\nΚλείσε το κινητό, άνοιξε την πόρτα — τα λέμε σύντομα."
        # draft + up to two revisions (max_revisions=2)
        return MockLLM(responses=[draft, revised, revised])

    def _publisher_registry(self):
        from solo_founder_crew.tools import ToolRegistry

        async def publisher(text: str) -> str:
            return f"shipped:{len(text)}chars"

        registry = ToolRegistry()
        registry.register(
            "publisher_tool", publisher, escalates="final_approval_before_publish"
        )
        return registry

    def _brief_for(self, shop: ShopRecord):
        from solo_founder_crew.brief import VentureBrief

        d = shop.design
        data = {
            "venture_id": shop.id,  # shop-1 etc. matches ^[a-z][a-z0-9-]*$
            "name": shop.name,
            "stage": "launched",
            "domain": {
                "industry": "retail",
                "geography": ["GR"],
                "language": ["el"],
            },
            "product": {
                "one_liner": f"{d.offer_value} — wallet loyalty pass for {shop.name}",
                "value_props": [d.offer_value, "Lives in Apple Wallet, no app to install"],
                "channels": ["apple_wallet", "email"],
            },
            "customer": {
                "segment": f"local customers of {shop.name}"
                + (f" in {shop.city}" if shop.city else ""),
            },
            "voice": {
                "tone": "warm, plain Greek, confident",
                "do": ["speak like a neighbourhood shop", "keep it short"],
                "dont": ["no hype words", "no implied existing customers"],
            },
            "constraints": {"out_of_scope": ["physical retail expansion", "non-GR markets"]},
        }
        return VentureBrief(data)

    def _task_for(self, shop: ShopRecord) -> str:
        d = shop.design
        return (
            f"Draft a short launch announcement (Greek) for {shop.name}'s new "
            f"wallet loyalty pass: {d.offer_value}. Match the venture voice, "
            f"respect every constraint, keep it under 120 words, and end with a "
            f"one-line call to action to add the pass to Apple Wallet."
        )
