"""
Phase 7: ANSYS Session Manager
===============================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System

Manages the lifecycle of ANSYS MAPDL gRPC sessions:
1. Safe launch and shutdown of ansys-mapdl-core instances
2. Reuse of existing active sessions to prevent overhead
3. Context manager interface for clean error recovery
4. Clean workspace directory isolation
"""

import sys
import os
from typing import Optional, Generator
from contextlib import contextmanager
from ansys.mapdl.core import launch_mapdl, Mapdl


class AnsysSessionManager:
    """Manages PyMAPDL process connection and lifecycle."""

    @staticmethod
    @contextmanager
    def get_session(
        existing_mapdl: Optional[Mapdl] = None,
        loglevel: str = "WARNING",
        print_com: bool = False,
        clear_on_start: bool = True
    ) -> Generator[Mapdl, None, None]:
        """Context manager for acquiring and safely releasing an ANSYS MAPDL session."""
        owns_session = False
        mapdl = existing_mapdl

        if mapdl is None:
            # Launch new MAPDL instance
            mapdl = launch_mapdl(loglevel=loglevel, print_com=print_com)
            owns_session = True

        try:
            if clear_on_start:
                mapdl.clear()
            yield mapdl
        finally:
            if owns_session and mapdl is not None:
                try:
                    mapdl.exit()
                except Exception as e:
                    print(f"[AnsysSessionManager] Warning during MAPDL exit: {e}", file=sys.stderr)
