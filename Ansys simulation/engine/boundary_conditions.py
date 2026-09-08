"""
Phase 7: Boundary Conditions Manager
====================================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System

Applies physical thermal boundary conditions on 3D envelope exterior faces & interior domain:
1. Outer Roof: Convective Robin film condition with sol-air temperature (h_out, T_sol-air_roof)
2. Outer Walls (South, North, West, East): Directional sol-air film conditions
3. Ground Base Slab: Soil conduction film boundary (h_ground, T_ground)
4. Internal Air Cavity: Volumetric body heat generation (BFE,,HGEN)
"""

from typing import Dict
from ansys.mapdl.core import Mapdl
from .schemas import DerivedPhysicsParameters, ShelterGeometry


class BoundaryConditionsManager:
    """Applies Robin convection, Sol-Air radiation, and internal loads in MAPDL."""

    @classmethod
    def apply_steady_state_bcs(
        cls,
        mapdl: Mapdl,
        geom: ShelterGeometry,
        derived: DerivedPhysicsParameters
    ) -> None:
        """Applies all Robin film and volumetric thermal boundary conditions."""
        lx = geom.length_m
        ly = geom.width_m
        lz = geom.height_m

        h_out = derived.h_outdoor_w_m2_k
        h_ground = 10.0  # Ground contact film conductance [W/m²·K]

        # ---------------------------------------------------------------------
        # 1. External Roof (Z = lz)
        # ---------------------------------------------------------------------
        mapdl.nsel("S", "LOC", "Z", lz - 0.001, lz + 0.001)
        mapdl.sf("ALL", "CONV", h_out, derived.sol_air_roof_c)

        # ---------------------------------------------------------------------
        # 2. South Wall (Y = 0)
        # ---------------------------------------------------------------------
        mapdl.nsel("S", "LOC", "Y", -0.001, 0.001)
        mapdl.sf("ALL", "CONV", h_out, derived.sol_air_south_c)

        # ---------------------------------------------------------------------
        # 3. North Wall (Y = ly)
        # ---------------------------------------------------------------------
        mapdl.nsel("S", "LOC", "Y", ly - 0.001, ly + 0.001)
        mapdl.sf("ALL", "CONV", h_out, derived.sol_air_north_c)

        # ---------------------------------------------------------------------
        # 4. West Wall (X = 0)
        # ---------------------------------------------------------------------
        mapdl.nsel("S", "LOC", "X", -0.001, 0.001)
        mapdl.sf("ALL", "CONV", h_out, derived.sol_air_west_c)

        # ---------------------------------------------------------------------
        # 5. East Wall (X = lx)
        # ---------------------------------------------------------------------
        mapdl.nsel("S", "LOC", "X", lx - 0.001, lx + 0.001)
        mapdl.sf("ALL", "CONV", h_out, derived.sol_air_east_c)

        # ---------------------------------------------------------------------
        # 6. Foundation Slab (Z = 0)
        # ---------------------------------------------------------------------
        mapdl.nsel("S", "LOC", "Z", -0.001, 0.001)
        mapdl.d("ALL", "TEMP", derived.ground_boundary_temp_c)

        # ---------------------------------------------------------------------
        # 7. Internal Core Volumetric Heat Generation (Air Domain Elements)
        # ---------------------------------------------------------------------
        if derived.volumetric_heat_gen_w_m3 > 0.001:
            mapdl.esel("S", "MAT", "", 2)
            mapdl.bfe("ALL", "HGEN", 1, derived.volumetric_heat_gen_w_m3)

        mapdl.allsel()
