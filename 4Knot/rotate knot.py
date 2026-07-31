import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# --- Parameters ---
res_t = 420        # Resolution along the knot length
res_theta = 32     # Resolution around the tube
r_tube = 1.0/8.0   # Thickness of the tube original 6
rotation_phi = math.pi / 2  # The Ryw rotation angle

# --- Mathematical Functions ---

def f_knot(t):
    """The base knot path in 3D."""
    x = (2 + math.cos(2 * t)) * math.cos(3 * t)
    y = (2 + math.cos(2 * t)) * math.sin(3 * t)
    z = math.sin(4 * t)
    return Vector((x, y, z)) / 4.0

def f_prime(t):
    """First derivative for the tangent (Numerical approximation)."""
    dt = 0.001
    return (f_knot(t + dt) - f_knot(t - dt)) / (2 * dt)

def f_double_prime(t):
    """Second derivative for the normal (Numerical approximation)."""
    dt = 0.001
    return (f_prime(t + dt) - f_prime(t - dt)) / (2 * dt)

def inverse_stereographic(v):
    """Lifts a 3D vector to a 4D unit sphere."""
    sq_mag = v.length_squared
    denom = 1 + sq_mag
    return [2*v.x/denom, 2*v.y/denom, 2*v.z/denom, (sq_mag - 1)/denom]

def rotate_yw(v4, angle):
    """Rotates a 4D vector in the YW plane."""
    # Ryw = {{1, 0, 0, 0}, {0, cos, 0, -sin}, {0, 0, 1, 0}, {0, sin, 0, cos}}
    x, y, z, w = v4
    new_y = y * math.cos(angle) - w * math.sin(angle)
    new_w = y * math.sin(angle) + w * math.cos(angle)
    return (x, new_y, z, new_w)

def stereographic_projection(v4):
    """Projects 4D back to 3D."""
    x, y, z, w = v4
    denom = 1.0 - w
    if abs(denom) < 1e-6: denom = 1e-6
    return Vector((x/denom, y/denom, z/denom))

# --- Mesh Generation ---

mesh = bpy.data.meshes.new("Knot4D")
obj = bpy.data.objects.new("Knot4D", mesh)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()

verts_grid = []

for i in range(res_t):
    t = (i / res_t) * 2 * math.pi
    
    # Calculate Frenet-Serret-like Frame for the tube
    pos = f_knot(t)
    df = f_prime(t)
    ddf = f_double_prime(t)
    
    tangent = df.normalized()
    # x = Normalize[ddf(df.df) - df(df.ddf)]
    normal = (ddf * df.length_squared - df * df.dot(ddf)).normalized()
    binormal = normal.cross(tangent)
    
    row = []
    for j in range(res_theta):
        theta = (j / res_theta) * 2 * math.pi
        
        # 1. Create the tube point in 3D
        tube_point = pos + r_tube * (normal * math.cos(theta) + binormal * math.sin(theta))
        
        # 2. Lift to 4D
        v4 = inverse_stereographic(tube_point)
        
        # 3. Rotate in YW
        v4_rot = rotate_yw(v4, rotation_phi)
        
        # 4. Project back to 3D
        final_pos = stereographic_projection(v4_rot)
        row.append(bm.verts.new(final_pos))
    verts_grid.append(row)

# Stitch the grid (with wrap-around for t and theta)
for i in range(res_t):
    next_i = (i + 1) % res_t
    for j in range(res_theta):
        next_j = (j + 1) % res_theta
        bm.faces.new((
            verts_grid[i][j], 
            verts_grid[next_i][j], 
            verts_grid[next_i][next_j], 
            verts_grid[i][next_j]
        ))

bm.to_mesh(mesh)
bm.free()

bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth()