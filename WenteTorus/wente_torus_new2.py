import bpy
import math

# ==============================================================================
# PARAMETER & STEUERUNG (Hier bequem anpassen!)
# ==============================================================================
OBJECT_NAME = "WenteTorus_3Ueberlappend"

# --- 1. GEOMETRIE & ANORDNUNG ---
NUMBER_OF_LOBES = 3       # Anzahl der Kugeln/Lappen (k)
MAIN_RADIUS = 1.45        # Hauptradius (R0) -> kleiner = mehr Überlappung im Zentrum
RADIUS_OFFSET = 0.15      # Radialer Versatz der Kugelzentren (A)

# --- 2. KUGELFORM & VOLUMEN ---
TUBE_RADIUS_BASE = 1.55   # Basis-Radius der Röhre (r0)
SPHERE_EXPANSION = 1.10   # Kugel-Anschwellung (B) -> bestimmt die Gesamtdicke

# --- 3. HÖHENKONTROLLE & ABFLACHUNG (Gegen spitze Oberseiten) ---
HEIGHT_SCALE = 0.70       # Z-Skalierung (< 1.0 flacht ab & nimmt die Spitze)
TOP_ROUNDING = 0.75       # Formkorrektur für sanfter gewölbte Kugelkuppeln

# --- 4. AUFLÖSUNG & GLÄTTUNG ---
SEGMENTS_U = 240          # Auflösung entlang des Hauptrings
SEGMENTS_V = 120          # Auflösung des Kugelprofils
SUBDIV_LEVELS = 2         # Subdivision Surface Modifier Stufe (0 = Aus)

# --- 5. MATERIAL EINSTELLUNGEN ---
MAT_NAME = "Wente_Gold_Material"
MAT_COLOR = (0.95, 0.65, 0.15, 1.0)  # RGBA Gold
MAT_METALLIC = 0.95
MAT_ROUGHNESS = 0.12
# ==============================================================================


def create_wente_torus():
    # Altes Objekt mit gleichem Namen löschen
    if OBJECT_NAME in bpy.data.objects:
        existing_obj = bpy.data.objects[OBJECT_NAME]
        mesh_to_delete = existing_obj.data
        bpy.data.objects.remove(existing_obj, do_unlink=True)
        if mesh_to_delete:
            bpy.data.meshes.remove(mesh_to_delete)

    verts = []
    faces = []

    # Vertices berechnen
    for i in range(SEGMENTS_U):
        u = 2.0 * math.pi * i / SEGMENTS_U
        cos_ku = math.cos(NUMBER_OF_LOBES * u)

        # Radien für Hauptschleife und Kugelvolumen
        R = MAIN_RADIUS + RADIUS_OFFSET * cos_ku
        r = TUBE_RADIUS_BASE + SPHERE_EXPANSION * cos_ku

        for j in range(SEGMENTS_V):
            v = 2.0 * math.pi * j / SEGMENTS_V
            cos_v = math.cos(v)
            sin_v = math.sin(v)

            # Radiale Ausdehnung (XY)
            rad = R + r * cos_v

            # 3D Koordinaten
            x = rad * math.cos(u)
            y = rad * math.sin(u)
            
            # Z-Koordinate mit steuerbarer Höhe & Kuppel-Abflachung
            z = r * sin_v * HEIGHT_SCALE * TOP_ROUNDING

            verts.append((x, y, z))

    # Quad-Faces mit geschlossener Torus-Topologie aufbauen
    for i in range(SEGMENTS_U):
        i_next = (i + 1) % SEGMENTS_U
        for j in range(SEGMENTS_V):
            j_next = (j + 1) % SEGMENTS_V

            p1 = i * SEGMENTS_V + j
            p2 = i_next * SEGMENTS_V + j
            p3 = i_next * SEGMENTS_V + j_next
            p4 = i * SEGMENTS_V + j_next

            faces.append((p1, p2, p3, p4))

    # Mesh & Objekt in Blender erstellen
    mesh = bpy.data.meshes.new(OBJECT_NAME + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(OBJECT_NAME, mesh)
    bpy.context.collection.objects.link(obj)

    # Aktivieren & Smooth Shading
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()

    # Subdivision Surface Modifier anwenden
    if SUBDIV_LEVELS > 0:
        subsurf = obj.modifiers.new(name="Subdivision", type='SUBSURF')
        subsurf.levels = SUBDIV_LEVELS
        subsurf.render_levels = SUBDIV_LEVELS + 1

    # Material erstellen & zuweisen
    mat = bpy.data.materials.get(MAT_NAME)
    if not mat:
        mat = bpy.data.materials.new(name=MAT_NAME)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)

        if "Base Color" in bsdf.inputs:
            bsdf.inputs["Base Color"].default_value = MAT_COLOR
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = MAT_METALLIC
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = MAT_ROUGHNESS

        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    obj.data.materials.append(mat)
    print(f"Modell '{OBJECT_NAME}' erfolgreich erzeugt!")

# Script ausführen
create_wente_torus()