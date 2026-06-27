"""Crew use cases. Thin today (role catalogue); the seam through which P3 will
drive the marketing crew. Depends on the CrewGateway port, so tests use a fake
and never import the heavy framework."""

from __future__ import annotations

from ..domain.ports import CrewGateway


class CrewService:
    def __init__(self, crew: CrewGateway) -> None:
        self._crew = crew

    def role_catalogue(self) -> list[str]:
        return self._crew.role_catalogue()
