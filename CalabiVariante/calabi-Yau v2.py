import bpy
import bmesh
import math
import cmath

# --- SETTINGS ---
N = 4               # Complexity (Higher = more "petals")
RESOLUTION = 160     # Detail of each individual patch
ALPHA_T = 0.25      # The 't' parameter from your script (0.0 to 1.0)
SCALE = 2.0

# --- Calabi-Yau Math ---
def calabi_yau(z, k1, k2, alpha):
    # z1 = Exp[2Pi I k1/n] * Cosh[z]^(2/n)
    # z2 = Exp[2Pi I k2/n] * Sinh[z]^(2/n)
    
    phi1 = (2 * math.pi * k1) / N
    phi2 = (2 * math.pi * k2) / N
    
    z1 = cmath.exp(complex(0, phi1)) * (cmath.cosh(z)**(2/N))
    z2 = cmath.exp(complex(0, phi2)) * (cmath.sinh(z)**(2/N))
    
    # Coordinates: {Re[z1], Re[z2], Cos[alpha]Im[z1] + Sin[alpha]Im[z2]}
    x = z1.real
    y = z2.real
    z_coord = math.cos(alpha) * z1.imag + math.sin(alpha) * z2.imag
    
    return (x, y, z_coord)

# --- Setup Scene ---
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

mesh_data = bpy.data.meshes.new("CalabiYau")
obj = bpy.data.objects.new("CalabiYau", mesh_data)
bpy.context.collection.objects.link(obj)
bm = bmesh.new()

alpha = (0.25 + ALPHA_T) * math.pi

print(f"Generating Calabi-Yau Manifold (N={N})...")

# The Mathematica script tables k1 and k2 from 0 to N-1
for k1 in range(N):
    for k2 in range(N):
        # Create a grid for each k-pair patch
        # x range [-1, 1], y range [0, Pi/2]
        verts = []
        for ix in range(RESOLUTION + 1):
            for iy in range(RESOLUTION + 1):
                px = -1.0 + (ix * 2.0 / RESOLUTION)
                py = (iy * (math.pi / 2.0) / RESOLUTION)
                
                # Calculate 3D point
                pos = calabi_yau(complex(px, py), k1, k2, alpha)
                verts.append(bm.verts.new([p * SCALE for p in pos]))
        
        # Connect vertices into faces for this patch
        stride = RESOLUTION + 1
        for ix in range(RESOLUTION):
            for iy in range(RESOLUTION):
                v1 = verts[ix * stride + iy]
                v2 = verts[(ix + 1) * stride + iy]
                v3 = verts[(ix + 1) * stride + (iy + 1)]
                v4 = verts[ix * stride + (iy + 1)]
                try:
                    bm.faces.new((v1, v2, v3, v4))
                except:
                    pass

# --- Finalize ---
# Clean up overlapping vertices at the seams
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
bm.to_mesh(mesh_data)
bm.free()

# Visual Polish
bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth()

# Material: Pearlescent Silk
mat = bpy.data.materials.new(name="CalabiMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs['Base Color'].default_value = (0.8, 0.9, 1.0, 1.0)
    bsdf.inputs['Subsurface Weight'].default_value = 0.3
    bsdf.inputs['Specular IOR Level'].default_value = 0.8
    bsdf.inputs['Roughness'].default_value = 0.2
    # Add a bit of 'Coat' for a shiny finish
    bsdf.inputs['Coat Weight'].default_value = 1.0

obj.data.materials.append(mat)

print("Quantum Manifold Generated.")