"""CrewGateway adapter backed by the real solo-founder-crew framework.

The framework is an external system, so it sits behind a port like any other
driven dependency. The import is local to the method so importing this module
(and the whole app) stays cheap and the heavy framework only loads when a crew
call actually happens.
"""

from __future__ import annotations


class SoloFounderCrewGateway:
    def role_catalogue(self) -> list[str]:
        from solo_founder_crew.roles_library import ROLE_LIBRARY

        return sorted(ROLE_LIBRARY.keys())
