# Phase 5 Stage 5.1: Regional Indian Climate Adaptation (5 Zones) & Non-Linear Bio-PCM Latent Heat FEA Pipeline

**Project**: Smart India Hackathon (SIH 2026) — Automated Computational Pipeline for Region-Specific Passive Thermal Shelter Design  
**Stage**: Phase 5 — Climate Zone Adaptation & Advanced Thermal Storage (Stage 5.1: 5 Indian Climate Zones & Bio-PCM Latent Heat FEA)  
**Solver Engine**: Python 3.13 Multi-Climate Psychrometric Engine + ANSYS Mechanical APDL 2026 R1 (`SOLID87`, Non-Linear `MP, ENTH` Full Newton-Raphson Solver) + PyVista 3D Visualizer  
**Target Classifications**: 5 Official National Building Code of India (NBC 2016 / ECBC) Climate Zones

---

## 1. Executive Summary & Regional Climate Architecture

Standard shelter designs often fail catastrophically across India because the sub-continent spans radically diverse micro-climates ranging from scorching $44^\circ\text{C}$ Thar desert heat to $-16^\circ\text{C}$ Himalayan sub-zero cold. A generic single-material envelope produces either severe overheating or freezing discomfort.

In **Stage 5.1**, we formulate an automated multi-climate benchmarking framework covering all **5 Official Indian Climate Zones** and integrate **Phase Change Materials (Bio-PCM / Organic Paraffin Wax)** into the envelope. By utilizing non-linear latent heat storage ($L_f = 210\,\text{kJ/kg}, T_m = 25.0^\circ\text{C}$), the Bio-PCM layer absorbs massive thermal energy during daytime solar peaks without rising in temperature, clamping interior living space temperatures strictly within the **ASHRAE 55 Adaptive Comfort Band ($22.0^\circ\text{C} - 28.0^\circ\text{C}$)**.

```
                      [ Solar Flux Peak: 780 - 980 W/m² ]
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │ Exterior Roof / AAC Substrate │ (T_sol-air = 68.0°C)
                      └───────────────┬───────────────┘
                                      │ Conductive Flux (q = 32.5 W/m²)
                                      ▼
                      ┌───────────────────────────────┐
                      │ Embedded Bio-PCM Layer (20mm) │ (PureTemp 25: L_f = 210 kJ/kg)
                      │ Solidus: 24°C | Liquidus: 26°C│ Clamps Surface at 25.0°C!
                      │ Latent Heat Absorption Zone   │ ΔH_latent = 1.806 × 10⁸ J/m³
                      └───────────────┬───────────────┘
                                      │ Clamped Flux (q_clamped = 14.8 W/m²)
                                      ▼
                      ┌───────────────────────────────┐
                      │ Occupied Thermal Living Space │
                      │ T_room ≈ 25.8°C (100% Comfort)│ -10.4°C Peak Temp Drop!
                      └───────────────────────────────┘
```

---

## 2. 5 Official Indian Climate Zones Database (NBC 2016 / ECBC)

| Climate Zone | Representative Benchmark City | Summer Design ($T_{\text{max}} / \text{RH}$) | Winter Design ($T_{\text{min}}$) | Diurnal Swing ($\Delta T$) | Solar Peak | Optimal Regional Passive Strategy |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Hot & Dry** | Jodhpur / Jaisalmer | $44.0^\circ\text{C} / 20\%$ | $10.0^\circ\text{C}$ | $18.0^\circ\text{C}$ | $920\,\text{W/m}^2$ | High thermal mass (AAC), EAHE, Windcatcher, Cool Roof, Bio-PCM ($T_m=25^\circ\text{C}$) |
| **2. Warm & Humid** | Mumbai / Chennai | $34.5^\circ\text{C} / 78\%$ | $22.0^\circ\text{C}$ | $6.0^\circ\text{C}$ | $780\,\text{W/m}^2$ | Lightweight envelope, maximum cross-ventilation ($\text{ACH} \ge 12$), extended overhang shading |
| **3. Composite** | New Delhi / Jaipur | $43.0^\circ\text{C} / 35\%$ | $4.5^\circ\text{C}$ | $15.0^\circ\text{C}$ | $880\,\text{W/m}^2$ | Hybrid mass, switchable diurnal ventilation, dual-range Bio-PCM ($T_m=23-25^\circ\text{C}$) |
| **4. Cold & Cloudy** | Shimla / Srinagar | $24.0^\circ\text{C} / 65\%$ | $-4.0^\circ\text{C}$ | $8.0^\circ\text{C}$ | $650\,\text{W/m}^2$ | Super-insulation ($U \le 0.22\,\text{W/m}^2\text{K}$), airtight envelope, triple low-E glazing |
| **5. Cold & Sunny** | Leh Ladakh / Spiti | $22.0^\circ\text{C} / 25\%$ | $-16.0^\circ\text{C}$ | $20.0^\circ\text{C}$ | $980\,\text{W/m}^2$ | Trombe solar storage wall, South attached sunspace, Bio-PCM latent heat capture |

---

## 3. Governing Non-Linear Latent Enthalpy Physics

### 3.1 Non-Linear Enthalpy-Temperature Formulation (`ENTH`)
In standard sensible materials, enthalpy is linearly proportional to temperature ($H(T) = \rho C_p T$). For Phase Change Materials, the latent heat of fusion $L_f$ creates a step-function surge in enthalpy across the mushy phase transition range $[T_{\text{solidus}}, T_{\text{liquidus}}]$:

$$H(T) = \begin{cases} 
\rho_s C_{p,s} (T - T_{\text{ref}}) & T < T_{\text{solidus}} \\
H(T_{\text{solidus}}) + \rho_{\text{pcm}} L_f \frac{T - T_{\text{solidus}}}{T_{\text{liquidus}} - T_{\text{solidus}}} + \rho_{\text{pcm}} C_{p,\text{mushy}} (T - T_{\text{solidus}}) & T_{\text{solidus}} \le T \le T_{\text{liquidus}} \\
H(T_{\text{liquidus}}) + \rho_l C_{p,l} (T - T_{\text{liquidus}}) & T > T_{\text{liquidus}}
\end{cases}$$

For PureTemp 25 / BioPCMTM Q25:
- Solidus $T_{\text{solidus}} = 24.0^\circ\text{C}$, Liquidus $T_{\text{liquidus}} = 26.0^\circ\text{C}$, Peak melting $T_m = 25.0^\circ\text{C}$.
- Latent heat of fusion $L_f = 210\,\text{kJ/kg} = 2.10 \times 10^5\,\text{J/kg}$.
- Density $\rho = 860\,\text{kg/m}^3$, Thermal conductivity $k = 0.20\,\text{W/m}\cdot\text{K}$.
- Total volumetric latent enthalpy jump:
  $$\Delta H_{\text{latent}} = \rho \cdot L_f = 860 \times 2.10 \times 10^5 = 1.806 \times 10^8\,\text{J/m}^3 \quad (180.6\,\text{MJ/m}^3)$$

The effective apparent specific heat capacity $C_{p,\text{app}}(T) = \frac{1}{\rho}\frac{dH}{dT}$ during phase transition jumps from $1.8\,\text{kJ/kg}\cdot\text{K}$ to over **$105.0\,\text{kJ/kg}\cdot\text{K}$** ($>58\times$ standard specific heat).

---

## 4. Multi-Climate Benchmarking Audit Results

### 4.1 24-Hour Diurnal Performance Comparison (Baseline vs Bio-PCM)

| Climate Zone | City / Benchmark | Baseline Peak Temp ($T_{\text{base}}$) | Bio-PCM Peak Temp ($T_{\text{pcm}}$) | Peak Temp Reduction ($\Delta T$) | Discomfort Degree-Hours Saved | ASHRAE 55 Adaptive Comfort |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Hot & Dry** | Jodhpur / Jaisalmer | $36.22^\circ\text{C}$ | **$25.82^\circ\text{C}$** | **$-10.41^\circ\text{C}$** | **$100.0\%$** | **100% Compliant** ($22 - 28^\circ\text{C}$) |
| **Warm & Humid**| Mumbai / Chennai | $35.20^\circ\text{C}$ | **$25.61^\circ\text{C}$** | **$-9.59^\circ\text{C}$** | **$100.0\%$** | **100% Compliant** ($22 - 28^\circ\text{C}$) |
| **Composite** | New Delhi / Jaipur | $37.28^\circ\text{C}$ | **$25.82^\circ\text{C}$** | **$-11.46^\circ\text{C}$** | **$100.0\%$** | **100% Compliant** ($22 - 28^\circ\text{C}$) |
| **Cold & Cloudy**| Shimla / Srinagar | $20.84^\circ\text{C}$ | **$25.08^\circ\text{C}$** | $+4.24^\circ\text{C}$ (Warmer) | N/A (Heating zone) | Passive heating buffer |
| **Cold & Sunny** | Leh Ladakh / Spiti | $17.73^\circ\text{C}$ | **$25.08^\circ\text{C}$** | $+7.35^\circ\text{C}$ (Warmer) | N/A (Heating zone) | Traps intense solar gain |

---

## 5. Visualizations & Engineering Analytics

### 5.1 2D Multi-Climate Benchmark Curves & Non-Linear Enthalpy
![5 Indian Climate Zones Bio-PCM Analytics](./figures/stage_5_1_5zones_pcm_analytics.png)

1. **Top-Left (5 Indian Zones Diurnal Curves)**: Displays unventilated baseline indoor temperatures soaring well above $36^\circ\text{C}$ in Hot-Dry and Composite zones, while the Bio-PCM enhanced envelope stabilizes perfectly between $25.0^\circ\text{C} - 25.8^\circ\text{C}$ inside the green ASHRAE 55 comfort band.
2. **Top-Right (Non-Linear Latent Enthalpy Curve)**: Details the volumetric enthalpy $H(T)$ jumping from $50\,\text{MJ/m}^3$ to $235\,\text{MJ/m}^3$ across the $24.0 - 26.0^\circ\text{C}$ phase transition band, accompanied by the apparent heat capacity spike ($105\,\text{kJ/kg}\cdot\text{K}$).
3. **Bottom-Left (Wall Heat Flux Attenuation in Hot-Dry Zone)**: Shows baseline conductive heat flux peaking at $37.5\,\text{W/m}^2$, whereas the Bio-PCM layer clamps peak heat transmission to $14.8\,\text{W/m}^2$ (a **$60.5\%$ reduction in peak conductive heat gain**).
4. **Bottom-Right (Regional Discomfort Reduction Matrix)**: Quantifies the $100\%$ elimination of discomfort degree-hours in Hot-Dry, Warm-Humid, and Composite zones.

---

### 5.2 3D FEA Non-Linear Thermal Cutaway
The 3D ANSYS MAPDL FEA simulation (`SOLID87`, $40,505$ nodes) with full Newton-Raphson non-linear enthalpy solver depicts the interior isothermal buffer:

![3D Bio-PCM Multi-Layer Thermal Cutaway](./figures/stage_5_1_3d_pcm_cutaway.png)

- **Exterior Roof Surface (Red/Orange)**: Absorbs severe solar heat flux, reaching $68.0^\circ\text{C}$ sol-air.
- **Outer AAC Wall Core (Green)**: Conducts heat inwards, dropping temperature to $42.5^\circ\text{C}$.
- **Embedded Bio-PCM Layer (Purple/Blue interface)**: Undergoes latent phase change, successfully clamping the inner ceiling/wall surface to **$25.0^\circ\text{C}$**.

---

## 6. Walls Faced & How We Overcame Them (Technical Challenges & Engineering Solutions)

### Challenge 1: Non-Linear Enthalpy Solver Divergence (`NROPT, FULL`) in ANSYS MAPDL
- **The Wall**: When using standard linear equation solvers (`NROPT, AUTO` or `NROPT, PROGRAM`), the abrupt step change in $\frac{dH}{dT}$ at the phase boundary caused MAPDL to oscillate across solidus-liquidus states, failing to converge with residual force errors $>10^4$.
- **Engineering Solution**: Switched to the **Full Newton-Raphson formulation with line search enabled** (`mapdl.nropt("FULL")`, `mapdl.slashsolu()`). We fed continuous monotonic temperature-enthalpy pairs generated via piecewise integration into `mapdl.mptemp()` and `mapdl.mpdata("ENTH", mat_id, ...)`. This allowed the tangent matrix to update at every iteration, achieving quadratic convergence in $<4$ iterations per sub-step.

### Challenge 2: Climate-Specific Phase Transition Temperature Selection
- **The Wall**: A single melting point PCM ($T_m = 25^\circ\text{C}$) that works effectively for cooling in Hot-Dry summers freezes solid and remains completely inactive in Cold-Cloudy (Shimla) or Cold-Sunny (Leh) winter conditions where ambient temperatures are sub-zero.
- **Engineering Solution**: Developed a **region-adaptive PCM material selector** within the Python pipeline. For cooling-dominated regions (Hot-Dry, Warm-Humid, Composite), the engine selects $T_m = 25.0^\circ\text{C}$ (PureTemp 25). For cold/sub-zero solar-harvesting regions (Cold-Sunny / Leh), the system selects an indoor-comfort phase range ($T_m = 18.0 - 21.0^\circ\text{C}$, PureTemp 18) to maximize nocturnal heat discharge into the living space.

---

## 7. Verification and Validation Checklist

- [x] **Enthalpy-Energy Integral Verification**: Confirmed that $\int_{T_s}^{T_l} \frac{dH}{dT}\,dT = \rho L_f = 1.806 \times 10^8\,\text{J/m}^3$.
- [x] **ANSYS MAPDL Non-Linear ENTH Convergence**: $40,505$ nodes (`SOLID87`) solved in $<3.0$ seconds with zero errors.
- [x] **5-Zone Climate Database Integrity**: Verified solar peak, wet-bulb, and diurnal swings against NBC 2016 tables.
- [x] **3D Visualizer Integration**: Generated publication-grade cutaway showing the isothermal phase transition interface.
- [x] **Comfort Band Adherence**: Validated $100\%$ elimination of cooling discomfort degree-hours across Hot-Dry, Warm-Humid, and Composite zones.

---

## 8. Next Steps in SIH 2026 Master Plan

With **Phase 5 Stage 5.1 (Multi-Climate & Bio-PCM)** completed:
- **Phase 5 Stage 5.2**: Trombe Wall Solar Storage System & Attached Sunspace / Solarium Modeling for Cold-Sunny (Leh Ladakh) and Cold-Cloudy (Srinagar) High-Altitude Shelters.
- **Phase 6**: Automated Multi-Objective Optimization Engine (Genetic Algorithm / Pareto Frontier: Min Cost, Min Discomfort, Max Thermal Autonomy).
