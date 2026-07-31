import bpy, bmesh, math
from math import sin, cos, pi

# -------- Parameters --------
N = 60
segments_v = 1001
segments_u = 21
a0 = 1.9
b = 4.5 #weave parameter
r = 0.3 #diagonale
scale_z = 0.1
phase = 0.0
extra_spin = 0.0   # >0 adds a woven twist

# -------- Vector helpers --------
def add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def mul(a,s): return (a[0]*s,a[1]*s,a[2]*s)
def dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])
def norm(v):
    l = math.sqrt(dot(v,v))
    return (v[0]/l,v[1]/l,v[2]/l)

# -------- Curve + derivatives --------
def curve_core(v, t):
    a = a0 + sin(5*v - 4*t + 3*t/4) / 14
    f = cos(v) + a * cos(3*v)
    g = sin(v) - a * sin(3*v)
    h = b * sin(2*(4*v - 0.8*sin(4*v)))
    return (f, g, h * scale_z)

def curve_point(v,t):
    return curve_core(v,t)

def curve_d1(v,t,eps=1e-4):
    return sub(curve_core(v+eps,t), curve_core(v-eps,t))

def curve_d2(v,t,eps=1e-4):
    # second finite difference: p(v+eps) - 2p(v) + p(v-eps)
    p_plus  = curve_core(v+eps,t)
    p_minus = curve_core(v-eps,t)
    p_mid   = curve_core(v,t)
    return add( sub(p_plus, mul(p_mid,2.0)),
                sub(p_minus, mul((0,0,0),0.0)) )  # simplifies to p_plus - 2p_mid + p_minus

# -------- Build tube using Frenet frame --------
def make_tube():
    bm = bmesh.new()
    verts_grid = []

    tval = 2*pi * (phase % N) / N

    for i in range(segments_v):
        v = 2*pi * i / (segments_v-1)

        p  = curve_point(v,tval)
        d1 = curve_d1(v,tval)
        d2 = curve_d2(v,tval)

        T = norm(d1)

        # Frenet normal from change of tangent
        proj = mul(T, dot(d2,T))
        Nf = norm(sub(d2, proj))
        B  = cross(T, Nf)

        # Optional extra spin for woven look
        spin = extra_spin * v
        cs, sn = math.cos(spin), math.sin(spin)
        Nvec = add(mul(Nf,cs), mul(B,sn))
        Bvec = add(mul(Nf,-sn), mul(B,cs))

        ring = []
        for j in range(segments_u):
            u = 2*pi*j/segments_u
            offset = add(mul(Nvec, r*math.cos(u)),
                         mul(Bvec, r*math.sin(u)))
            ring.append(bm.verts.new(add(p, offset)))
        verts_grid.append(ring)

    # connect quads
    for i in range(segments_v-1):
        for j in range(segments_u):
            v0 = verts_grid[i][j]
            v1 = verts_grid[i][(j+1)%segments_u]
            v2 = verts_grid[i+1][(j+1)%segments_u]
            v3 = verts_grid[i+1][j]
            bm.faces.new((v0,v1,v2,v3))

    mesh = bpy.data.meshes.new("TwistedKnot_Frenet")
    bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new("TwistedKnot_Frenet", mesh)
    bpy.context.collection.objects.link(obj)

    for p in mesh.polygons:
        p.use_smooth = True

make_tube()
