# Paste this into Blender's Text Editor and Run
import bpy
import bmesh
import math
from mathutils import Vector

# --- Parameters you can tweak ---
radii = [0.4, 0.9, 1.7]  # 0.2, 0.8, 0.2
nu = 80   # samples in u (wraps)
nv = 80   # samples in v (no wrap)
# Domain: u in [0,1), v in [0, 1/2)
v_min, v_max = 0.0, 0.65

# --- Math helpers matching Asymptote code ---
def circlecenter(r):
    # Asy: return r + 1/(1+r)
    return r + 1.0/(1.0 + r)

def circleparam(r):
    # returns a function F(t) -> (radial, z)
    c = circlecenter(r)
    def F(t):
        # Asy: center + r * expi(2*pi*t)  => (center + r*cos, r*sin)
        return (c + r * math.cos(2.0*math.pi*t),
                r * math.sin(2.0*math.pi*t))
    return F

def revolve(F):
    # returns function G(u,theta) -> (x,y,z) given F(t) returns (radial, z)
    def G(u, theta):
        radial, z = F(u)
        x = radial * math.cos(theta)
        y = radial * math.sin(theta)
        return (x, y, z)
    return G

def torusparam(r):
    return revolve(circleparam(r))

def hopfparam(r):
    mytorus = torusparam(r)
    # in Asy: mytorus((uv.x, 2*pi*(uv.y - uv.x)))
    def H(u, v):
        theta = 2.0 * math.pi * (v - u)    # note the (v-u) shift from Asy
        return mytorus(u, theta)
    return H

def rescale(t):
    # Asy: atan((pi/2)*t) / (pi/2)
    return math.atan((math.pi/2.0) * t) / (math.pi/2.0)

# Color function matching Asymptote's pen color(pair uv) logic.
# uv is (u, v) with u in [0,1], v in [0,1/2]
def make_color_func(r):
    z0 = 2.0 * rescale(r) - 1.0
    # clamp
    if z0 > 1.0:
        z0 = 1.0
    elif z0 < -1.0:
        z0 = -1.0
    cylradius = math.sqrt(max(0.0, 1.0 - z0*z0))
    def color_at_uv(uv):
        u, v = uv
        theta = 2.0 * math.pi * v   # Asy: theta = 2*pi*uv.y
        x = cylradius * math.cos(theta)
        y = cylradius * math.sin(theta)
        # map from [-1,1] to [0,1]
        xr = (x + 1.0) / 2.0
        yr = (y + 1.0) / 2.0
        zr = (z0 + 1.0) / 2.0
        # return RGB (no explicit color mixing objects in Blender),
        # keep alpha = 1.0
        return (xr, yr, zr, 1.0)
    return color_at_uv

# Utility to create mesh object from grid of vertices and quad faces
def build_hopf_mesh(r, nu, nv):
    H = hopfparam(r)
    colorfunc = make_color_func(r)

    # Create list of vertices sampled on a nu x nv grid
    verts = []
    # We'll generate nu * nv vertices. u wraps (periodic), v does not.
    for i in range(nu):
        u = i / float(nu)                # i in [0, nu-1] -> u in [0,1)
        for j in range(nv):
            v = v_min + (j + 0.0) / float(nv) * (v_max - v_min)
            x, y, z = H(u, v)
            verts.append((x, y, z))

    # Create quad faces (wrap in u)
    faces = []
    for i in range(nu):
        inext = (i + 1) % nu
        for j in range(nv - 1):   # v not wrapping -> create faces only for j and j+1
            a = i * nv + j
            b = inext * nv + j
            c = inext * nv + (j + 1)
            d = i * nv + (j + 1)
            faces.append((a, b, c, d))

    # Create the mesh and object
    name = f"hopf_r{r}"
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)

    # Add to scene collection
    bpy.context.collection.objects.link(obj)

    # Make smooth shading
    for p in obj.data.polygons:
        p.use_smooth = True

    # Add vertex color layer and assign per-face color (use face center uv)
    if mesh.vertex_colors:
        col_layer = mesh.vertex_colors.active
    else:
        col_layer = mesh.vertex_colors.new(name="Col")

    # loop over polygons and set colors per loop
    # We compute face uv center at the parameter-space center corresponding to the cell:
    # For face defined by (i,j) cell, uv center = ((i+0.5)/nu, (j+0.5)/nv)
    # We must recover (i,j) from face index ordering used above: faces were appended in i-major order
    face_idx = 0
    for i in range(nu):
        inext = (i + 1) % nu
        for j in range(nv - 1):
            # uv center mapping matching Asymptote patch z = (interp(a.x,b.x,i/nu), interp(a.y,b.y,j/nv))
            uc = (i + 0.5) / float(nu)
            vc = v_min + (j + 0.5) / float(nv) * (v_max - v_min)
            rgba = colorfunc((uc, vc))
            poly = mesh.polygons[face_idx]
            # assign same color to all loops of this polygon
            for loop_index in poly.loop_indices:
                col_layer.data[loop_index].color = rgba
            face_idx += 1

    return obj

# Remove previous objects created by earlier runs with name prefix 'hopf_r' to avoid duplicates
for ob in list(bpy.data.objects):
    if ob.name.startswith("hopf_r"):
        # unlink from collections first
        for coll in ob.users_collection:
            coll.objects.unlink(ob)
        bpy.data.objects.remove(ob, do_unlink=True)

# Build objects for each radius
for r in radii:
    build_hopf_mesh(r, nu, nv)

print("Hopf-like meshes created for radii:", radii)
