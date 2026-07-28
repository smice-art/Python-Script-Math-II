import bpy
import bmesh
import math

def create_perfect_wente_torus():
    # 1. Altes Mesh-Material und Objekte löschen
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    if 'bpy.ops.object.delete' in dir(bpy.ops):
        bpy.ops.object.delete()

    # --- GEOMETRIE-EINSTELLUNGEN ---
    u_segments = 160  # Höhere Auflösung für perfekte Rundung
    v_segments = 160
    lobes = 3         # Die 3 charakteristischen Haupt-Bälle
    
    # Material für den Torus anlegen (Glas/Glossy für optische Tiefe)
    mat_torus = bpy.data.materials.new(name="Wente_Glass")
    mat_torus.use_nodes = True
    nodes = mat_torus.node_tree.nodes
    nodes.clear()
    
    # Einfaches, performantes Glas-Shading über Nodes
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_glass = nodes.new(type='ShaderNodeBsdfGlass')
    node_glass.inputs['IOR'].default_value = 1.333 # Wasser/Seifenblase
    node_glass.inputs['Color'].default_value = (0.2, 0.6, 1.0, 1.0) # Hellblau
    mat_torus.node_tree.links.new(node_glass.outputs['BSDF'], node_output.inputs['Surface'])

    # 2. WENTE-TORUS GENERIEREN
    mesh = bpy.data.meshes.new(name="WenteTorusMesh")
    obj = bpy.data.objects.new("Wente_Torus", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_torus)
    
    bm = bmesh.new()
    verts = []

    # Optimierte Formel für pralle, sphärische Blasen-Symmetrie
    for i in range(u_segments):
        u = (i / u_segments) * 2 * math.pi
        for j in range(v_segments):
            v = (j / v_segments) * 2 * math.pi
            
            # Verstärkte Amplituden für die Kugelform (Blasen-Effekt)
            # Schafft den extremen Übergang von dünnem Hals zu fetter Kugel
            bubble_envelope = 1.4 + 1.1 * math.cos(lobes * u)
            
            # Lokaler Radius schwillt synchron an, um Kugelform zu erzwingen
            r_local = 1.1 * (1.1 + 0.8 * math.cos(lobes * u))
            
            # Die Verformung in Z-Richtung sorgt für die vertikale Rundung der Bälle
            z_wave = 1.6 * math.sin(lobes * u) * math.sin(v)
            
            # Dreidimensionale Einbettung mit ausgeprägter Kugel-Symmetrie
            x = (bubble_envelope + r_local * math.cos(v)) * math.cos(u)
            y = (bubble_envelope + r_local * math.cos(v)) * math.sin(u)
            z = r_local * math.sin(v) * 0.5 + z_wave
            
            verts.append(bm.verts.new((x, y, z)))
            
    bm.verts.ensure_lookup_table()
    
    # Quad-Flächen erzeugen
    for i in range(u_segments):
        i_next = (i + 1) % u_segments
        for j in range(v_segments):
            j_next = (j + 1) % v_segments
            
            v1 = verts[i * v_segments + j]
            v2 = verts[i_next * v_segments + j]
            v3 = verts[i_next * v_segments + j_next]
            v4 = verts[i * v_segments + j_next]
            
            try:
                bm.faces.new((v1, v2, v3, v4))
            except ValueError:
                pass

    bm.to_mesh(mesh)
    bm.free()
    
    # Schattierung glätten
    for poly in mesh.polygons:
        poly.use_smooth = True

    # 3. DIE 3 INNEN-KUGELN ERZEUGEN
    # Material für die inneren Kugeln (Leuchtend/Kontrastfarbe)
    mat_sphere = bpy.data.materials.new(name="Inner_Sphere_Mat")
    mat_sphere.use_nodes = True
    s_nodes = mat_sphere.node_tree.nodes
    s_nodes.clear()
    
    s_output = s_nodes.new(type='ShaderNodeOutputMaterial')
    s_emission = s_nodes.new(type='ShaderNodeEmission')
    s_emission.inputs['Color'].default_value = (1.0, 0.2, 0.2, 1.0) # Signalrot
    s_emission.inputs['Strength'].default_value = 2.0
    mat_sphere.node_tree.links.new(s_emission.outputs['Emission'], s_output.inputs['Surface'])

    # Exakte mathematische Mittelpunkte der drei großen Blasen berechnen
    for k in range(lobes):
        # Winkelpositionen der drei maximalen Ausbuchtungen (0°, 120°, 240°)
        u_angle = (k / lobes) * 2 * math.pi
        
        # Radius-Vektor zum geometrischen Schwerpunkt der Blase
        dist = 2.3 
        sp_x = dist * math.cos(u_angle)
        sp_y = dist * math.sin(u_angle)
        sp_z = 0.5
        
        # Kugel hinzufügen
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=1.6, 
            location=(sp_x, sp_y, sp_z),
            segments=64,
            ring_count=32
        )
        sphere_obj = bpy.context.active_object
        sphere_obj.name = f"Wente_Center_Ball_{k+1}"
        sphere_obj.data.materials.append(mat_sphere)
        bpy.ops.object.shade_smooth()

    # Fokus zurück auf den Torus
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

create_perfect_wente_torus()
