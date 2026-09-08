"""
Phase 7: Physics Preprocessor
==============================
Smart India Hackathon (SIH 2026) — Passive Thermal Shelter System

Converts high-level validated user/dashboard parameters into physically rigorous
quantities and boundary conditions required by ANSYS MAPDL FEA:
1. Convection film coefficients (McAdams wind correlation)
2. Directional Sol-Air temperatures for multi-faceted exterior envelope
3. Usable air cavity geometry & internal volumetric heat generation
4. Multi-layer composite equivalent thermal conductivity
5. Convective ventilation exchange capacity
"""

from typing import Tuple
from .schemas import SimulationInput, DerivedPhysicsParameters


class PhysicsPreprocessor:
    """Deterministic converter from high-level input schema to ANSYS physics parameters."""

    AIR_DENSITY_KG_M3 = 1.204       # Standard air density at 20°C [kg/m³]
    AIR_SPECIFIC_HEAT_J_KG_K = 1005 # Air specific heat capacity [J/(kg·K)]

    @classmethod
    def process(cls, sim_input: SimulationInput) -> DerivedPhysicsParameters:
        """Derives all required ANSYS physics parameters from the input contract."""
        climate = sim_input.climate
        shelter = sim_input.shelter
        materials = sim_input.materials
        site = sim_input.site
        loads = sim_input.internal_loads
        vent = sim_input.ventilation

        # 1. External Convection Film Coefficient (McAdams Wind Correlation)
        # h_out = 5.7 + 3.8 * v_wind [W/(m²·K)]
        v_wind = climate.wind_speed_m_s
        h_outdoor = max(10.0, 5.7 + 3.8 * v_wind)

        # 2. Internal Natural Convection Film Coefficient (ASHRAE / CIBSE Standard)
        h_indoor = 7.7

        # 3. Multi-Orientation Directional Solar Irradiance Fractions
        # Standard building physics solar distribution on vertical facades vs horizontal roof
        i_peak = climate.solar_irradiance_peak_w_m2
        i_roof = i_peak
        i_south = 0.50 * i_peak
        i_west = 0.40 * i_peak
        i_north = 0.15 * i_peak  # Diffuse solar component on shaded north wall
        i_east = 0.25 * i_peak

        # 4. Sol-Air Temperatures: T_sol-air = T_ambient + (alpha * I) / h_out
        t_amb = climate.ambient_temp_c
        alpha_roof = materials.roof_solar_absorptivity
        alpha_wall = materials.wall_solar_absorptivity

        sol_air_roof = t_amb + (alpha_roof * i_roof / h_outdoor)
        sol_air_south = t_amb + (alpha_wall * i_south / h_outdoor)
        sol_air_west = t_amb + (alpha_wall * i_west / h_outdoor)
        sol_air_north = t_amb + (alpha_wall * i_north / h_outdoor)
        sol_air_east = t_amb + (alpha_wall * i_east / h_outdoor)

        # 5. Foundation Boundary Temperature
        ground_temp = site.ground_temp_c

        # 6. Room Geometry & Internal Usable Air Volume
        lx, ly, lz = shelter.length_m, shelter.width_m, shelter.height_m
        tw = shelter.wall_thickness_m
        tr = shelter.roof_thickness_m
        tf = shelter.floor_thickness_m

        lx_int = max(0.1, lx - 2.0 * tw)
        ly_int = max(0.1, ly - 2.0 * tw)
        lz_int = max(0.1, lz - tf - tr)
        room_vol = lx_int * ly_int * lz_int

        # 7. Internal Volumetric Heat Generation: q_vol = Q_total / V_room [W/m³]
        q_internal_watts = loads.total_heat_watts
        q_vol = q_internal_watts / room_vol if room_vol > 0.0 else 0.0

        # 8. Multi-Layer Composite Equivalent Thermal Conductivity
        # R_wall = L_base / k_base + L_ins / k_ins [m²·K/W]
        k_base = materials.wall_material.conductivity_w_m_k
        r_base = tw / k_base
        r_ins = 0.0
        total_wall_thickness = tw

        if materials.insulation_material and materials.insulation_thickness_wall_m > 0.0:
            d_ins = materials.insulation_thickness_wall_m
            k_ins = materials.insulation_material.conductivity_w_m_k
            r_ins = d_ins / k_ins
            total_wall_thickness += d_ins

        r_effective = r_base + r_ins
        k_effective = total_wall_thickness / r_effective if r_effective > 0.0 else k_base

        # 9. Ventilation Convective Heat Removal Capacity: C_vent = m_dot * Cp [W/K]
        ach = vent.air_changes_per_hour
        vol_flow_m3_s = (ach * room_vol) / 3600.0
        mass_flow_kg_s = vol_flow_m3_s * cls.AIR_DENSITY_KG_M3
        c_vent = mass_flow_kg_s * cls.AIR_SPECIFIC_HEAT_J_KG_K

        return DerivedPhysicsParameters(
            h_outdoor_w_m2_k=round(h_outdoor, 4),
            h_indoor_w_m2_k=round(h_indoor, 4),
            sol_air_roof_c=round(sol_air_roof, 3),
            sol_air_south_c=round(sol_air_south, 3),
            sol_air_west_c=round(sol_air_west, 3),
            sol_air_north_c=round(sol_air_north, 3),
            sol_air_east_c=round(sol_air_east, 3),
            ground_boundary_temp_c=round(ground_temp, 3),
            room_air_volume_m3=round(room_vol, 3),
            volumetric_heat_gen_w_m3=round(q_vol, 4),
            envelope_effective_k_w_m_k=round(k_effective, 4),
            envelope_effective_r_m2_k_w=round(r_effective, 4),
            ventilation_heat_removal_w_per_k=round(c_vent, 4)
        )
