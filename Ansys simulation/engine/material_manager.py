"""
Phase 7: Material Manager
==========================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System

Manages linear and non-linear thermal material properties in ANSYS MAPDL:
1. Linear isotropic conduction (KXX, DENS, C) for envelope masonry & concrete
2. Equivalent indoor air domain thermal transport (KXX = 0.35 W/m·K)
3. Non-linear Bio-PCM / Phase Change Material enthalpy tables (MP, ENTH)
4. Association of material IDs to geometric volume components
"""

from typing import Dict
import numpy as np
from ansys.mapdl.core import Mapdl
from .schemas import EnvelopeAssembly, DerivedPhysicsParameters


class MaterialManager:
    """Assigns thermal materials and applies properties to MAPDL volumes."""

    MAT_ID_ENVELOPE = 1
    MAT_ID_AIR = 2

    @classmethod
    def apply_materials(
        cls,
        mapdl: Mapdl,
        materials: EnvelopeAssembly,
        derived: DerivedPhysicsParameters
    ) -> None:
        """Defines thermal material models in MAPDL and assigns them to volume components."""
        mapdl.prep7()

        # ---------------------------------------------------------------------
        # Material 1: Solid Shelter Envelope (Composite Wall / Roof)
        # ---------------------------------------------------------------------
        k_env = derived.envelope_effective_k_w_m_k
        dens_env = materials.wall_material.density_kg_m3
        cp_env = materials.wall_material.specific_heat_j_kg_k

        mapdl.mp("KXX", cls.MAT_ID_ENVELOPE, k_env)
        mapdl.mp("DENS", cls.MAT_ID_ENVELOPE, dens_env)
        mapdl.mp("C", cls.MAT_ID_ENVELOPE, cp_env)

        # Non-Linear Enthalpy curve for Phase Change Material (Bio-PCM)
        if materials.has_pcm:
            t_m = materials.pcm_melt_temp_c
            t_s = t_m - 1.0  # Solidus
            t_l = t_m + 1.0  # Liquidus
            l_f = materials.pcm_latent_heat_j_kg
            rho_pcm = 860.0  # kg/m³
            cp_pcm = 2000.0  # J/kg·K
            delta_h_vol = l_f * rho_pcm  # J/m³

            # Enthalpy definition: H = integral(rho * Cp dT) + Latent
            h_s = rho_pcm * cp_pcm * t_s
            h_l = h_s + delta_h_vol + rho_pcm * cp_pcm * (t_l - t_s)

            # MAPDL MP, ENTH table
            mapdl.mptemp(1, 0.0, t_s, t_l, 60.0)
            mapdl.mpdata("ENTH", cls.MAT_ID_ENVELOPE, 1, 0.0, h_s, h_l, h_l + rho_pcm * cp_pcm * (60.0 - t_l))

        # ---------------------------------------------------------------------
        # Material 2: Indoor Usable Air Cavity Domain
        # ---------------------------------------------------------------------
        # Air equivalent conductivity k=0.35 W/(m·K) captures natural circulation
        mapdl.mp("KXX", cls.MAT_ID_AIR, 0.35)
        mapdl.mp("DENS", cls.MAT_ID_AIR, 1.204)
        mapdl.mp("C", cls.MAT_ID_AIR, 1005.0)

        # ---------------------------------------------------------------------
        # Volume Material Attribution
        # ---------------------------------------------------------------------
        # Assign Material 1 to Solid Envelope
        mapdl.cmsel("S", "SOLID_ENVELOPE")
        mapdl.vatt(mat=cls.MAT_ID_ENVELOPE, type_=1)

        # Assign Material 2 to Core Air Volume
        mapdl.cmsel("S", "AIR_VOL")
        mapdl.vatt(mat=cls.MAT_ID_AIR, type_=1)

        mapdl.vsel("ALL")
