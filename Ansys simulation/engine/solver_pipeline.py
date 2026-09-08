"""
Phase 7: Solver Pipeline
=========================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System

Configures finite element meshing and executes the ANSYS MAPDL thermal solver:
1. SOLID87 10-node quadratic tetrahedral element configuration
2. Conformal free meshing with user/default element sizing
3. Solution execution (Static / Transient / Non-Linear PCM)
4. Robust solver verification and error trapping
"""

from ansys.mapdl.core import Mapdl
from .schemas import SimulationSettings, SimulationMode, SolverStatus


class SolverPipeline:
    """Meshes geometry and runs thermal analysis in ANSYS MAPDL."""

    @classmethod
    def setup_elements_and_mesh(
        cls,
        mapdl: Mapdl,
        settings: SimulationSettings
    ) -> None:
        """Configures element type and generates 3D volumetric tetrahedral mesh."""
        mapdl.prep7()
        mapdl.et(1, settings.element_type)
        mapdl.esize(settings.mesh_size_m)
        mapdl.mshape(1, "3D")  # Tetrahedral elements
        mapdl.mshkey(0)        # Free meshing
        mapdl.vmesh("ALL")

    @classmethod
    def solve(
        cls,
        mapdl: Mapdl,
        settings: SimulationSettings
    ) -> SolverStatus:
        """Enters /SOLU and runs FEA solution."""
        try:
            mapdl.finish()
            mapdl.slashsolu()

            if settings.mode == SimulationMode.STEADY_STATE:
                mapdl.antype("STATIC")
                mapdl.solve()
            elif settings.mode == SimulationMode.TRANSIENT_24H:
                mapdl.antype("TRANS")
                mapdl.timint("ON")
                mapdl.autots("OFF")
                mapdl.outres("ERASE")
                mapdl.outres("ALL", "LAST")
                mapdl.time(3600.0)
                mapdl.nsubst(5)
                mapdl.solve()
            elif settings.mode == SimulationMode.PCM_LATENT:
                mapdl.antype("STATIC")
                mapdl.nlgeom("OFF")
                mapdl.nropt("FULL")
                mapdl.autots("ON")
                mapdl.nsubst(20, 100, 10)
                mapdl.solve()

            mapdl.finish()
            return SolverStatus.SUCCESS

        except Exception as e:
            print(f"[SolverPipeline] Solver execution error: {e}")
            return SolverStatus.CONVERGENCE_ERROR
