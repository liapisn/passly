"""Postgres CampaignRepository — durable campaign runs and founder gates.

New in the relational move: campaigns previously lived only in the crew
runner's in-process dicts, so `start` / poll / `respond` had to be served by
the same process. Persisting the gate is what lets those three requests land on
three different instances — the precondition for running the API serverless.

This adapter is storage only. The crew runner still holds its own in-memory
state; swapping it onto this repository (and onto a Postgres LangGraph
checkpointer) is the separate serverless refactor.
"""

from __future__ import annotations

from ...domain.models import CampaignState, CampaignStatus, ReviewGate
from .db import get_pool


def _to_state(row: dict) -> CampaignState:
    gate = None
    if row["status"] == CampaignStatus.awaiting_review.value:
        gate = ReviewGate(
            turn=row["gate_turn"],
            artifact=row["gate_artifact"],
            options=list(row["gate_options"] or []),
        )
    return CampaignState(
        thread_id=row["thread_id"],
        status=CampaignStatus(row["status"]),
        gate=gate,
        final_artifact=row["final_artifact"],
        error=row["error"],
    )


class PostgresCampaignRepository:
    def __init__(self, pool=None) -> None:
        self._pool = pool or get_pool()

    def save(self, shop_id: str, state: CampaignState) -> CampaignState:
        """Upsert a run's current state, keyed by thread_id.

        Gate columns are cleared on any non-gate status so a stale draft can
        never be shown next to a terminal outcome — the DB's
        `campaigns_gate_complete` check enforces the other direction.
        """
        gate = state.gate if state.status == CampaignStatus.awaiting_review else None
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                insert into campaigns (
                    thread_id, shop_id, status,
                    gate_turn, gate_artifact, gate_options,
                    final_artifact, error
                ) values (%s, %s, %s, %s, %s, %s, %s, %s)
                on conflict (thread_id) do update set
                    status         = excluded.status,
                    gate_turn      = excluded.gate_turn,
                    gate_artifact  = excluded.gate_artifact,
                    gate_options   = excluded.gate_options,
                    final_artifact = excluded.final_artifact,
                    error          = excluded.error
                returning thread_id, status, gate_turn, gate_artifact,
                          gate_options, final_artifact, error
                """,
                (
                    state.thread_id,
                    shop_id,
                    state.status.value,
                    gate.turn if gate else None,
                    gate.artifact if gate else None,
                    gate.options if gate else None,
                    state.final_artifact,
                    state.error,
                ),
            ).fetchone()
        return _to_state(row)

    def get(self, thread_id: str) -> CampaignState | None:
        with self._pool.connection() as conn:
            row = conn.execute(
                """
                select thread_id, status, gate_turn, gate_artifact,
                       gate_options, final_artifact, error
                  from campaigns
                 where thread_id = %s
                """,
                (thread_id,),
            ).fetchone()
        return _to_state(row) if row else None
