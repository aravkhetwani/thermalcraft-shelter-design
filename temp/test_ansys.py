from ansys.mapdl.core import launch_mapdl

print("Starting ANSYS...")

mapdl = launch_mapdl()

print("Connected!")
print("ANSYS version:", mapdl.version)

# Send a simple calculation to ANSYS
mapdl.input_strings("""
*SET,A,25
*SET,B,4
*SET,C,A*B
""")

result = mapdl.parameters["C"]

print("ANSYS calculated:", result)

mapdl.exit()

print("ANSYS closed.")