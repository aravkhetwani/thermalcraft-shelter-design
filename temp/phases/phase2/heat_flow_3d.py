"""
3D Spatial Heat-Flow Visualization & Simulation Engine using PyMAPDL and PyVista.
Models a full 3D passive shelter envelope, extracts 3D flux components (TFX, TFY, TFZ),
and generates 3D vector arrow glyphs and interactive cross-sectional cutaways.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np
import pyvista as pv
from ansys.mapdl.core import launch_mapdl, Mapdl


@dataclass
class Shelter3DConfig:
    """Configuration parameters for 3D shelter simulation."""
    length: float = 4.0                  # Outer length in X (m)
    width: float = 3.0                   # Outer width in Y (m)
    height: float = 2.6                  # Outer height in Z (m)
    wall_thickness: float = 0.25         # Wall/roof/floor thickness (m)
    envelope_conductivity: float = 0.80  # Envelope k (0.80 for brick, 0.05 for insulated) in W/(m·K)
    roof_absorptivity: float = 0.85      # Roof solar absorptance (0.85 dark, 0.20 cool roof)
    wall_absorptivity: float = 0.60      # Wall solar absorptance
    solar_flux_roof: float = 600.0       # Solar irradiance on roof (W/m²)
    solar_flux_south_wall: float = 300.0 # Solar irradiance on south wall (W/m²)
    solar_flux_west_wall: float = 250.0  # Solar irradiance on west wall (W/m²)
    outdoor_ambient_temp: float = 38.0   # Ambient shade temperature (°C)
    ground_temp: float = 24.0            # Deep ground contact temperature (°C)
    indoor_target_temp: float = 26.0     # Target comfort (°C)
    occupant_heat_total: float = 500.0   # Total occupant/equipment heat (W)
    h_outdoor: float = 20.0              # Outdoor film coefficient (W/m²·K)
    h_indoor: float = 7.7                # Indoor film coefficient (W/m²·K)
    mesh_size: float = 0.20              # Element size in meters
    element_type: str = "SOLID87"        # 10-node 3D tetrahedral thermal solid element


@dataclass
class Shelter3DResult:
    """Results extracted from 3D thermal simulation."""
    config: Shelter3DConfig
    grid: pv.UnstructuredGrid            # PyVista 3D grid with Temperature and Heat_Flux data
    nodal_temperatures: np.ndarray
    heat_flux_x: np.ndarray              # TFX
    heat_flux_y: np.ndarray              # TFY
    heat_flux_z: np.ndarray              # TFZ
    heat_flux_mag: np.ndarray            # |q|
    sol_air_roof: float
    sol_air_south: float
    sol_air_west: float
    min_temp: float
    max_temp: float
    avg_indoor_temp: float
    peak_flux_mag: float
    avg_flux_mag: float


def run_3d_shelter_simulation(
    config: Shelter3DConfig,
    existing_mapdl: Optional[Mapdl] = None,
    loglevel: str = "WARNING"
) -> Shelter3DResult:
    """Executes a 3D FEA thermal simulation of the shelter in ANSYS MAPDL."""
    should_exit = False
    if existing_mapdl is None:
        mapdl = launch_mapdl(loglevel=loglevel, print_com=False)
        should_exit = True
    else:
        mapdl = existing_mapdl

    try:
        tw = config.wall_thickness
        lx, ly, lz = config.length, config.width, config.height
        
        # 1. Calculate Sol-Air boundary temperatures
        sol_air_roof = config.outdoor_ambient_temp + (config.roof_absorptivity * config.solar_flux_roof / config.h_outdoor)
        sol_air_south = config.outdoor_ambient_temp + (config.wall_absorptivity * config.solar_flux_south_wall / config.h_outdoor)
        sol_air_west = config.outdoor_ambient_temp + (config.wall_absorptivity * config.solar_flux_west_wall / config.h_outdoor)
        
        # Internal room volume and heat generation
        room_vol = (lx - 2*tw) * (ly - 2*tw) * (lz - 2*tw)
        volumetric_hgen = config.occupant_heat_total / room_vol if room_vol > 0 else 0.0

        # 2. Reset and Preprocessor
        mapdl.clear()
        mapdl.prep7()
        mapdl.et(1, config.element_type)

        # Material 1: Solid Envelope
        mapdl.mp("KXX", 1, config.envelope_conductivity)
        
        # Material 2: Indoor Air Domain
        mapdl.mp("KXX", 2, 0.35)

        # 3. 3D Geometry: Create individual blocks
        # Volume 1: Floor Base Slab (Z in [0, tw])
        mapdl.block(0, lx, 0, ly, 0, tw)
        
        # Volume 2: South Wall (Front, Y in [0, tw], Z in [tw, lz - tw])
        mapdl.block(0, lx, 0, tw, tw, lz - tw)
        
        # Volume 3: North Wall (Back, Y in [ly - tw, ly], Z in [tw, lz - tw])
        mapdl.block(0, lx, ly - tw, ly, tw, lz - tw)
        
        # Volume 4: West Wall (Left, X in [0, tw], Y in [tw, ly - tw], Z in [tw, lz - tw])
        mapdl.block(0, tw, tw, ly - tw, tw, lz - tw)
        
        # Volume 5: East Wall (Right, X in [lx - tw, lx], Y in [tw, ly - tw], Z in [tw, lz - tw])
        mapdl.block(lx - tw, lx, tw, ly - tw, tw, lz - tw)
        
        # Volume 6: Roof Slab (Top, Z in [lz - tw, lz])
        mapdl.block(0, lx, 0, ly, lz - tw, lz)
        
        # Volume 7: Indoor Air Cavity
        mapdl.block(tw, lx - tw, tw, ly - tw, tw, lz - tw)

        # 4. Glue all volumes together for monolithic 3D contact
        mapdl.vglue("ALL")

        # 5. Assign Materials
        # Select indoor air domain volume (centered at lx/2, ly/2, lz/2)
        mapdl.vsel("S", "LOC", "X", lx/2.0 - 0.2, lx/2.0 + 0.2)
        mapdl.vsel("R", "LOC", "Y", ly/2.0 - 0.2, ly/2.0 + 0.2)
        mapdl.vsel("R", "LOC", "Z", lz/2.0 - 0.2, lz/2.0 + 0.2)
        mapdl.vatt(mat=2, real=1, type=1)

        # Select envelope volumes
        mapdl.vsel("INVE")
        mapdl.vatt(mat=1, real=1, type=1)
        mapdl.allsel()

        # 6. Meshing
        mapdl.esize(config.mesh_size)
        mapdl.vmesh("ALL")

        # 7. Internal Heat Generation (on Material 2 indoor air elements)
        if volumetric_hgen > 0.01:
            mapdl.esel("S", "MAT", "", 2)
            mapdl.bfe("ALL", "HGEN", 1, volumetric_hgen)
            mapdl.allsel()

        # 8. Boundary Conditions
        # A. Ground base (Z = 0): Constant Ground Temperature
        mapdl.nsel("S", "LOC", "Z", 0)
        mapdl.d("ALL", "TEMP", config.ground_temp)

        # B. Roof (Z = lz): Outdoor Convection + Roof Sol-Air
        mapdl.nsel("S", "LOC", "Z", lz)
        mapdl.sf("ALL", "CONV", config.h_outdoor, sol_air_roof)

        # C. South Wall (Y = 0): Outdoor Convection + South Sol-Air
        mapdl.nsel("S", "LOC", "Y", 0)
        mapdl.sf("ALL", "CONV", config.h_outdoor, sol_air_south)

        # D. West Wall (X = 0): Outdoor Convection + West Sol-Air
        mapdl.nsel("S", "LOC", "X", 0)
        mapdl.sf("ALL", "CONV", config.h_outdoor, sol_air_west)

        # E. North Wall (Y = ly) & East Wall (X = lx): Shaded Convection
        mapdl.nsel("S", "LOC", "Y", ly)
        mapdl.sf("ALL", "CONV", config.h_outdoor, config.outdoor_ambient_temp)

        mapdl.nsel("S", "LOC", "X", lx)
        mapdl.sf("ALL", "CONV", config.h_outdoor, config.outdoor_ambient_temp)

        mapdl.allsel()

        # 9. Solve
        mapdl.finish()
        mapdl.slashsolu()
        mapdl.antype("STATIC")
        mapdl.solve()
        mapdl.finish()

        # 10. Post-Processing & 3D Result Extraction
        mapdl.post1()
        mapdl.set("LAST")

        nodal_temps = mapdl.post_processing.nodal_temperature()
        q_x = mapdl.post_processing.element_values("TF", "X")
        q_y = mapdl.post_processing.element_values("TF", "Y")
        q_z = mapdl.post_processing.element_values("TF", "Z")
        q_mag = np.sqrt(q_x**2 + q_y**2 + q_z**2)

        # 11. Build PyVista 3D Mesh Representation
        grid = mapdl.mesh.grid.copy()
        grid.point_data["Temperature"] = nodal_temps
        
        # Store 3D vector components on cells
        vectors = np.column_stack([q_x, q_y, q_z])
        grid.cell_data["Heat_Flux_Vector"] = vectors
        grid.cell_data["Heat_Flux_Mag"] = q_mag

        # Compute indoor core temperature statistics
        nodes = mapdl.mesh.nodes
        indoor_mask = (
            (nodes[:, 0] >= tw + 0.1) & (nodes[:, 0] <= lx - tw - 0.1) &
            (nodes[:, 1] >= tw + 0.1) & (nodes[:, 1] <= ly - tw - 0.1) &
            (nodes[:, 2] >= tw + 0.1) & (nodes[:, 2] <= lz - tw - 0.1)
        )
        indoor_temps = nodal_temps[indoor_mask]
        avg_t_in = float(np.mean(indoor_temps)) if len(indoor_temps) > 0 else float(np.mean(nodal_temps))

        return Shelter3DResult(
            config=config,
            grid=grid,
            nodal_temperatures=nodal_temps,
            heat_flux_x=q_x,
            heat_flux_y=q_y,
            heat_flux_z=q_z,
            heat_flux_mag=q_mag,
            sol_air_roof=sol_air_roof,
            sol_air_south=sol_air_south,
            sol_air_west=sol_air_west,
            min_temp=float(np.min(nodal_temps)),
            max_temp=float(np.max(nodal_temps)),
            avg_indoor_temp=avg_t_in,
            peak_flux_mag=float(np.max(q_mag)),
            avg_flux_mag=float(np.mean(q_mag))
        )

    finally:
        if should_exit:
            mapdl.exit()


def render_3d_heat_flow_views(
    result: Shelter3DResult,
    save_prefix: str,
    glyph_scale_factor: float = 0.003
) -> Tuple[str, str, str]:
    """
    Generates high-resolution publication-quality 3D PyVista renders:
    1. Full 3D Envelope with 3D Arrow Glyphs
    2. 3D Cross-Sectional Cutaway (Clipping corner to see inside)
    3. 3-Plane Orthogonal Slices (X-Z, Y-Z, X-Y)
    """
    grid = result.grid
    cfg = result.config
    lx, ly, lz = cfg.length, cfg.width, cfg.height

    # Generate 3D Vector Glyphs (Arrows at cell centers)
    centers = grid.cell_centers()
    arrows = centers.glyph(
        orient="Heat_Flux_Vector",
        scale="Heat_Flux_Mag",
        factor=glyph_scale_factor,
        geom=pv.Arrow(shaft_radius=0.04, tip_radius=0.10, tip_length=0.35)
    )

    # -------------------------------------------------------------
    # View 1: 3D Outer Perspective with Vector Arrows
    # -------------------------------------------------------------
    p1 = pv.Plotter(off_screen=True, window_size=(1400, 900))
    p1.set_background("#1e1e24") # Sleek dark background
    p1.add_mesh(
        grid,
        scalars="Temperature",
        cmap="turbo",
        opacity=0.82,
        show_scalar_bar=True,
        scalar_bar_args={"title": "Temperature (°C)", "color": "white", "vertical": True}
    )
    p1.add_mesh(
        arrows,
        color="#ffcc00",
        lighting=True,
        label="Heat Flux Vectors (W/m²)"
    )
    p1.add_text(
        f"3D Shelter Heat-Flow Vector Field\nRoof Sol-Air: {result.sol_air_roof:.1f}°C | Ground: {cfg.ground_temp:.1f}°C",
        position="upper_left", color="white", font_size=11
    )
    p1.camera_position = [(lx*2.2, -ly*1.8, lz*2.0), (lx/2.0, ly/2.0, lz/2.0), (0, 0, 1)]
    p1.add_axes(color="white")
    
    view1_path = f"{save_prefix}_3d_overview.png"
    p1.screenshot(view1_path)
    p1.close()

    # -------------------------------------------------------------
    # View 2: 3D Cross-Sectional Cutaway (Looking inside through Roof & Walls)
    # -------------------------------------------------------------
    p2 = pv.Plotter(off_screen=True, window_size=(1400, 900))
    p2.set_background("#1e1e24")
    
    # Clip box cutaway: Cut out quadrant (X > lx/2, Y < ly/2) to expose indoor room & floor slab
    clipped_grid = grid.clip_box(
        bounds=[0, lx, 0, ly, 0, lz],
        invert=False
    ).clip(normal=[1, -1, 0], origin=[lx/2.0, ly/2.0, lz/2.0], invert=False)

    clipped_arrows = arrows.clip(normal=[1, -1, 0], origin=[lx/2.0, ly/2.0, lz/2.0], invert=False)

    p2.add_mesh(
        clipped_grid,
        scalars="Temperature",
        cmap="turbo",
        show_edges=True,
        edge_color="#333333",
        show_scalar_bar=True,
        scalar_bar_args={"title": "Temperature (°C)", "color": "white"}
    )
    p2.add_mesh(
        clipped_arrows,
        color="#ffff33",
        lighting=True
    )
    p2.add_text(
        f"3D Cutaway Section (Internal Thermal Core & Heat Sinking)\nIndoor Avg T: {result.avg_indoor_temp:.1f}°C | Peak Heat Flux: {result.peak_flux_mag:.1f} W/m²",
        position="upper_left", color="white", font_size=11
    )
    p2.camera_position = [(lx*1.8, -ly*1.6, lz*1.8), (lx/2.0, ly/2.0, lz/2.0), (0, 0, 1)]
    p2.add_axes(color="white")

    view2_path = f"{save_prefix}_3d_cutaway.png"
    p2.screenshot(view2_path)
    p2.close()

    # -------------------------------------------------------------
    # View 3: Orthogonal Slice Planes (X-Z, Y-Z, X-Y)
    # -------------------------------------------------------------
    p3 = pv.Plotter(off_screen=True, window_size=(1400, 900))
    p3.set_background("#1e1e24")
    
    slices = grid.slice_orthogonal(x=lx/2.0, y=ly/2.0, z=lz/2.0)
    p3.add_mesh(
        slices,
        scalars="Temperature",
        cmap="coolwarm",
        show_scalar_bar=True,
        scalar_bar_args={"title": "Temperature (°C)", "color": "white"}
    )
    p3.add_mesh(
        arrows.slice_orthogonal(x=lx/2.0, y=ly/2.0, z=lz/2.0),
        color="#ffdd00",
        lighting=True
    )
    p3.add_text(
        "3D Orthogonal Heat-Flow Slices (X-Z Midplane & Y-Z Midplane)",
        position="upper_left", color="white", font_size=11
    )
    p3.camera_position = [(lx*2.0, -ly*2.0, lz*1.8), (lx/2.0, ly/2.0, lz/2.0), (0, 0, 1)]
    p3.add_axes(color="white")

    view3_path = f"{save_prefix}_3d_slices.png"
    p3.screenshot(view3_path)
    p3.close()

    print(f"3D Renders generated successfully:\n  1. {view1_path}\n  2. {view2_path}\n  3. {view3_path}")
    return view1_path, view2_path, view3_path
