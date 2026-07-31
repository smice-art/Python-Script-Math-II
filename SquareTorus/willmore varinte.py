import bpy
import bmesh
import math

# ==============================
# Parameters
# ==============================
R0 = 2.0
a = 0.35          # 4-lobed modulation
r1 = 1.4          # ellipse major radius
r2 = 0.35         # ellipse minor radius
w = 4             # visible equivariant twist
u_res = 256
v_res = 64

name = "Equivariant_Willmore_Torus_REAL_TWIST"

mesh = bpy.data.meshes.new(name)
obj = bpy.data.objects.new(name, mesh)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()
rings = []

for i in range(u_res):
    phi = 2 * math.pi * i / u_res

    # 4-lobed major radius
    R = R0 + a * math.cos(4 * phi)

    # Frenet-like frame
    N = (math.cos(phi), math.sin(phi), 0.0)
    B = (0.0, 0.0, 1.0)

    # equivariant twist
    psi = w * phi
    cp = math.cos(psi)
    sp = math.sin(psi)

    # rotate ellipse axes
    Nr = (
        cp * N[0] + sp * B[0],
        cp * N[1] + sp * B[1],
        cp * N[2] + sp * B[2],
    )
    Br = (
        -sp * N[0] + cp * B[0],
        -sp * N[1] + cp * B[1],
        -sp * N[2] + cp * B[2],
    )

    ring = []
    for j in range(v_res):
        theta = 2 * math.pi * j / v_res

        # elliptical cross-section
        offset = (
            r1 * math.cos(theta) * Nr[0] +
            r2 * math.sin(theta) * Br[0],
            r1 * math.cos(theta) * Nr[1] +
            r2 * math.sin(theta) * Br[1],
            r1 * math.cos(theta) * Nr[2] +
            r2 * math.sin(theta) * Br[2],
        )

        x = R * math.cos(phi) + offset[0]
        y = R * math.sin(phi) + offset[1]
        z = offset[2]

        ring.append(bm.verts.new((x, y, z)))

    rings.append(ring)

bm.verts.ensure_lookup_table()

# Faces
for i in range(u_res):
    for j in range(v_res):
        bm.faces.new((
            rings[i][j],
            rings[(i + 1) % u_res][j],
            rings[(i + 1) % u_res][(j + 1) % v_res],
            rings[i][(j + 1) % v_res]
        ))

bm.normal_update()
bm.to_mesh(mesh)
bm.free()

bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth()

sub = obj.modifiers.new("Subdivision", type='SUBSURF')
sub.levels = 2
sub.render_levels = 3
