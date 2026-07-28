import bpy
import bmesh
import math
import mathutils

# --- SETTINGS ---
RESOLUTION = 250    # Detail of the shell (150x150). Try 200 if your Mac is fast.
POWER = 8           # The "8" from your TriplexPow[p, 8]
MAX_ITER = 12       # Lowered for speed; the Mandelbulb is math-heavy!

# --- Mandelbulb Math ---
def mandelbulb_height(cx, cy, cz):
    x, y, z = 0.0, 0.0, 0.0
    for i in range(MAX_ITER):
        r = math.sqrt(x*x + y*y + z*z)
        if r > 2.0: return i
        
        # Convert to polar coordinates
        theta = math.atan2(y, x)
        phi = math.asin(z / r) if r != 0 else 0
        
        # Scale and Rotate (The Triplex Power)
        rn = r ** POWER
        theta_n = theta * POWER
        phi_n = phi * POWER
        
        # Convert back to Cartesian
        x = rn * math.cos(theta_n) * math.cos(phi_n) + cx
        y = rn * math.sin(theta_n) * math.cos(phi_n) + cy
        z = rn * -math.sin(phi_n) + cz
        
    return MAX_ITER

# --- Setup Scene ---
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

mesh_data = bpy.data.meshes.new("Mandelbulb")
obj = bpy.data.objects.new("Mandelbulb", mesh_data)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()
# Use a UV Sphere as the base mesh to displace
bmesh.ops.create_uvsphere(bm, u_segments=RESOLUTION, v_segments=RESOLUTION, radius=1.0)

print("Calculating Mandelbulb surface... (this is complex math!)")

for v in bm.verts:
    # Normalize the sphere vertex to get a direction
    direction = v.co.normalized()
    
    # Trace along the ray to find the surface (simplified Ray-March)
    hit_dist = 0.0
    for step in range(15):
        test_dist = 1.2 - (step * 0.08)
        p = direction * test_dist
        if mandelbulb_height(p.x, p.y, p.z) >= MAX_ITER - 2:
            hit_dist = test_dist
            break
    
    # Deform the sphere vertex to the Mandelbulb surface
    if hit_dist > 0:
        v.co = direction * hit_dist
    else:
        v.co = direction * 0.5 # Core

# Finalize Mesh
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(mesh_data)
bm.free()

# --- Styling ---
bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth()

# Material: Iridescent/Pearlescent
mat = bpy.data.materials.new(name="MandelbulbShell")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 1.0, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.5
    bsdf.inputs['Roughness'].default_value = 0.2
    bsdf.inputs['Sheen Weight'].default_value = 1.0
obj.data.materials.append(mat)

print("Mandelbulb Shell Created.")