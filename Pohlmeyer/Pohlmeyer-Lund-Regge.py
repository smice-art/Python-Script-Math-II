import bpy
import bmesh
import math

def get_next_name(base_name):
    i = 1
    while base_name + f"_{i:03d}" in bpy.data.objects:
        i += 1
    return base_name + f"_{i:03d}"

def create_plr_surface(amplitude=1.0, frequency=1.5, phase=0.0, res=80, size=4.0):
    """
    This Script visualizes a soliton solution to the Pohlmeyer-Lund-Regge equation.
    The geometry uses sine-Gordon-like transitions.
    
    The Pohlmeyer-Lund-Regge equation (PLR equation) is a system of nonlinear partial differential equations. It is considered an integrable extension of the sine-Gordon equation and geometrically describes the evolution of curves as well as special flatness conditions in theoretical physics and mathematical geometry.
    
    Visualisiert eine Solitonen-Lösung der Pohlmeyer-Lund-Regge Gleichung.
    Die Geometrie nutzt Sinus-Gordon-ähnliche Übergänge.
    """
    obj_name = get_next_name("PLR_Soliton")
    mesh = bpy.data.meshes.new(obj_name)
    obj = bpy.data.objects.new(obj_name, mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    step = (size * 2) / (res - 1)
    verts = []

    for i in range(res):
        row = []
        u = -size + i * step
        for j in range(res):
            v = -size + j * step
            
            # X und Y bilden das Basis-Gitter
            x = u
            y = v
            
            # PLR-Solitonen-Approximation:
            # Nutzt die typische Form von 'Kink'-Lösungen (arc-tangens oder lokalisierte Wellen)
            # Hier: Eine interagierende Wellenfront, die für PLR-Systeme typisch ist
            dist = math.sqrt(u**2 + v**2)
            
            # Die 'Kink'-Funktion der Feldtheorie
            term1 = 4 * math.atan(math.exp(u * frequency + phase))
            term2 = 4 * math.atan(math.exp(v * frequency))
            
            # Kombinierte Oberflächentopologie
            z = amplitude * math.sin(term1 - term2)
            
            vert = bm.verts.new((x, y, z))
            row.append(vert)
        verts.append(row)
    
    bm.verts.ensure_lookup_table()
    for i in range(res - 1):
        for j in range(res - 1):
            bm.faces.new((verts[i][j], verts[i+1][j], 
                          verts[i+1][j+1], verts[i][j+1]))
    
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    # Fokus auf das neue Objekt
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()
    
    return obj

# --- KONFIGURATION ---
# Experimentiere mit 'frequency' für mehr Wellen-Interaktion
params = {
    "amplitude": 2.2,
    "frequency": 1.0, 
    "phase": 0.5,    # Verschiebt die Solitonen-Interaktion
    "res": 100,      # Höhere Auflösung für glattere Kanten
    "size": 5.0
}

new_plr = create_plr_surface(**params)
