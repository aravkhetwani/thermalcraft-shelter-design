from ansys.mapdl.core import launch_mapdl
import matplotlib.pyplot as plt

print("1. Starting ANSYS...")

mapdl = launch_mapdl(
    loglevel="DEBUG",
    print_com=True
)

print(f"2. Connected to ANSYS {mapdl.version}")

# --------------------------------------------------
# PREPROCESSING
# --------------------------------------------------

print("3. Entering preprocessing...")

mapdl.clear()
mapdl.prep7()

# 2D thermal element
print("4. Defining element...")

mapdl.et(1, "PLANE77")

# Material
print("5. Defining material...")

thermal_conductivity = 0.8  # W/(m·K)

mapdl.mp("KXX", 1, thermal_conductivity)

# Geometry
print("6. Creating wall...")

width = 1.0       # m
height = 0.2      # m

mapdl.blc4(0, 0, width, height)

# Mesh
print("7. Meshing wall...")

mapdl.esize(0.05)
mapdl.amesh("ALL")

print("8. Mesh completed.")

# --------------------------------------------------
# BOUNDARY CONDITIONS
# --------------------------------------------------

print("9. Applying boundary conditions...")

outside_temperature = 40  # °C
inside_temperature = 25   # °C

# Left side = outside = 40°C
mapdl.nsel("S", "LOC", "X", 0)
mapdl.d("ALL", "TEMP", outside_temperature)

# Right side = inside = 25°C
mapdl.nsel("S", "LOC", "X", width)
mapdl.d("ALL", "TEMP", inside_temperature)

# Select everything again
mapdl.allsel()

print("10. Boundary conditions completed.")

# --------------------------------------------------
# SOLUTION
# --------------------------------------------------

print("11. Starting ANSYS solver...")

mapdl.finish()
mapdl.slashsolu()

mapdl.antype("STATIC")
mapdl.solve()

print("12. ANSYS solver finished.")

mapdl.finish()

# --------------------------------------------------
# POST PROCESSING
# --------------------------------------------------

print("13. Reading results...")

mapdl.post1()
mapdl.set("LAST")

print("14. Results loaded.")

# Get nodal temperatures
nodal_temperatures = mapdl.post_processing.nodal_temperature()

# Get nodal coordinates
nodes = mapdl.mesh.nodes

x_coordinates = nodes[:, 0]
y_coordinates = nodes[:, 1]

print("15. Results received.")

print("Number of nodes:", len(nodal_temperatures))

print("Minimum temperature:",
      nodal_temperatures.min(), "°C")

print("Maximum temperature:",
      nodal_temperatures.max(), "°C")

# --------------------------------------------------
# DISPLAY SOME RAW DATA
# --------------------------------------------------

print("\nFirst 10 nodes:")

for i in range(min(10, len(nodal_temperatures))):
    print(
        f"Node {i + 1}: "
        f"X={x_coordinates[i]:.3f} m, "
        f"Y={y_coordinates[i]:.3f} m, "
        f"T={nodal_temperatures[i]:.2f} °C"
    )

# --------------------------------------------------
# PLOT TEMPERATURE FIELD
# --------------------------------------------------

print("\n16. Creating temperature plot...")

plt.figure(figsize=(10, 3))

scatter = plt.scatter(
    x_coordinates,
    y_coordinates,
    c=nodal_temperatures,
    cmap="hot",
    s=50
)

plt.colorbar(scatter, label="Temperature (°C)")

plt.xlabel("X position (m)")
plt.ylabel("Y position (m)")

plt.title("Temperature Distribution Through Wall")

plt.tight_layout()

plt.show()

# --------------------------------------------------
# EXIT
# --------------------------------------------------

mapdl.exit()

print("17. ANSYS closed.")