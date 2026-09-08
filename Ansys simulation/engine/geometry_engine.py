"""
Phase 7: 3D Geometry Engine
============================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System

Constructs conformal 3D multi-volume parametric passive shelter geometry in ANSYS MAPDL.
Implements the verified 7-Block Orthogonal Glued Geometry methodology:
- Volume 1: Foundation Base Slab (Z in [0, t_floor])
- Volume 2: South Wall (Front, Y in [0, t_wall])
- Volume 3: North Wall (Back, Y in [L_y - t_wall, L_y])
- Volume 4: West Wall (Left, X in [0, t_wall])
- Volume 5: East Wall (Right, X in [L_x - t_wall, L_x])
- Volume 6: Indoor Usable Air Cavity Domain
- Volume 7: Roof Slab (Z in [L_z - t_roof, L_z])
- Conformal Interface: mapdl.vglue("ALL")
"""

from typing import Tuple, List, Dict
from ansys.mapdl.core import Mapdl
from .schemas import ShelterGeometry


class GeometryEngine:
    """Generates 3D multi-volume geometry in ANSYS MAPDL."""

    @classmethod
    def build_shelter_geometry(cls, mapdl: Mapdl, geom: ShelterGeometry) -> Dict[str, any]:
        """Creates the 7 discrete non-overlapping volumes, glues them, and indexes volume groups."""
        lx = geom.length_m
        ly = geom.width_m
        lz = geom.height_m
        tw = geom.wall_thickness_m
        tr = geom.roof_thickness_m
        tf = geom.floor_thickness_m

        mapdl.prep7()

        # 1. Volume 1: Foundation Base Slab (Z in [0, tf])
        mapdl.block(0, lx, 0, ly, 0, tf)

        # 2. Volume 2: South Wall (Y in [0, tw], Z in [tf, lz - tr])
        mapdl.block(0, lx, 0, tw, tf, lz - tr)

        # 3. Volume 3: North Wall (Y in [ly - tw, ly], Z in [tf, lz - tr])
        mapdl.block(0, lx, ly - tw, ly, tf, lz - tr)

        # 4. Volume 4: West Wall (X in [0, tw], Y in [tw, ly - tw], Z in [tf, lz - tr])
        mapdl.block(0, tw, tw, ly - tw, tf, lz - tr)

        # 5. Volume 5: East Wall (X in [lx - tw, lx], Y in [tw, ly - tw], Z in [tf, lz - tr])
        mapdl.block(lx - tw, lx, tw, ly - tw, tf, lz - tr)

        # 6. Volume 6: Core Usable Air Cavity (X in [tw, lx - tw], Y in [tw, ly - tw], Z in [tf, lz - tr])
        mapdl.block(tw, lx - tw, tw, ly - tw, tf, lz - tr)

        # 7. Volume 7: Roof Slab (Z in [lz - tr, lz])
        mapdl.block(0, lx, 0, ly, lz - tr, lz)

        # 8. Glue all 7 volumes together to ensure shared conformal nodes across interfaces
        mapdl.vglue("ALL")

        # 9. Identify Core Air Volume vs Solid Envelope Volumes
        # Select volume containing the room center point
        center_x = lx / 2.0
        center_y = ly / 2.0
        center_z = tf + (lz - tf - tr) / 2.0

        mapdl.vsel("S", "LOC", "X", tw + 0.01, lx - tw - 0.01)
        mapdl.vsel("R", "LOC", "Y", tw + 0.01, ly - tw - 0.01)
        mapdl.vsel("R", "LOC", "Z", tf + 0.01, lz - tr - 0.01)

        # Tag components
        mapdl.cm("AIR_VOL", "VOLU")

        mapdl.vsel("ALL")
        mapdl.cmsel("U", "AIR_VOL")
        mapdl.cm("SOLID_ENVELOPE", "VOLU")
        mapdl.vsel("ALL")

        return {
            "lx": lx,
            "ly": ly,
            "lz": lz,
            "tw": tw,
            "tr": tr,
            "tf": tf,
            "center": (center_x, center_y, center_z)
        }
