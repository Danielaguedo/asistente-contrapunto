# primera_especie/anotador_svg_intervalos.py
import xml.etree.ElementTree as ET
from music21 import interval, note as m21note 
import re
import os
import traceback 
import math 

# --- Funciones para dibujar elementos SVG ---
def _add_arrowhead_marker_definition(svg_root, ns, arrowhead_id="arrowhead", color="#000000", size="10"):
    """
    Añade la definición de un marcador de punta de flecha a la sección <defs> del SVG.
    """
    defs_element = svg_root.find(".//svg:defs", ns)
    if defs_element is None:
        defs_element = ET.Element(f"{{{ns['svg']}}}defs")
        svg_root.insert(0, defs_element)

    if defs_element.find(f".//svg:marker[@id='{arrowhead_id}']", ns) is not None:
        return 

    # print(f"DEBUG (Anotador): Añadiendo definición de marcador '{arrowhead_id}'")
    
    s = float(size) 
    
    marker = ET.Element(f"{{{ns['svg']}}}marker", {
        "id": arrowhead_id,
        "viewBox": f"0 0 {s} {s}", 
        "refX": str(s * 0.8), 
        "refY": str(s / 2),
        "markerWidth": size, 
        "markerHeight": size,
        "orient": "auto-start-reverse"
    })
    
    ET.SubElement(marker, f"{{{ns['svg']}}}path", {
        "d": f"M0,{s*0.2} L{s*0.8},{s/2} L0,{s*0.8} Z", 
        "fill": color,
        "fill-opacity": "1.0"
    })
    defs_element.append(marker)

def _draw_connecting_line(target_group, coords1, coords2, ns, 
                          line_color="#000000", stroke_width="2.5", 
                          use_arrowhead=False, arrowhead_id="arrowhead"):
    """
    Dibuja una línea entre dos coordenadas. Opcionalmente añade una punta de flecha.
    """
    if not coords1 or not coords2:
        # print(f"DEBUG (Anotador Dibujo): Coordenadas faltantes para línea/flecha. C1: {coords1}, C2: {coords2}")
        return

    x1, y1 = coords1['x'], coords1['y']
    x2, y2 = coords2['x'], coords2['y']
    
    if x1 == x2 and y1 == y2:
        # print(f"DEBUG (Anotador Dibujo): Coordenadas idénticas ({x1},{y1}), no se dibuja línea.")
        return

    line_attributes = {
        "x1": str(x1), "y1": str(y1),
        "x2": str(x2), "y2": str(y2),
        "stroke": line_color,
        "stroke-width": stroke_width, # Usar el valor pasado como argumento
        "stroke-opacity": "1.0"
    }
    if use_arrowhead:
        line_attributes["marker-end"] = f"url(#{arrowhead_id})"
    
    ET.SubElement(target_group, f"{{{ns['svg']}}}line", line_attributes)
    # print(f"DEBUG (Anotador Dibujo): Línea dibujada de ({x1:.0f},{y1:.0f}) a ({x2:.0f},{y2:.0f}) color: {line_color}, stroke-width: {stroke_width}, arrowhead: {use_arrowhead}")


def _get_note_svg_coords(svg_root, note_id_m21_value, search_attr="data-id"):
    if not note_id_m21_value: 
        return None
    target_element_note_group = None
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    try:
        xpath_query_note_group = f".//svg:g[@{search_attr}='{note_id_m21_value}']"
        target_element_note_group = svg_root.find(xpath_query_note_group, ns)
        if target_element_note_group is None and search_attr == "data-id": 
            xpath_query_note_group_fallback = f".//svg:g[@id='{note_id_m21_value}']"
            target_element_note_group = svg_root.find(xpath_query_note_group_fallback, ns)

        if target_element_note_group is not None:
            notehead_group = target_element_note_group.find("./svg:g[@class='notehead']", ns)
            if notehead_group is None: 
                notehead_group = target_element_note_group.find("./svg:g[@data-class='notehead']", ns) 
            
            if notehead_group is not None:
                use_element = notehead_group.find("./svg:use", ns)
                if use_element is not None:
                    x_attr = use_element.get('x')
                    y_attr = use_element.get('y')
                    if x_attr is not None and y_attr is not None:
                        try:
                            return {'x': float(x_attr), 'y': float(y_attr)}
                        except ValueError: pass
                    # Verovio 4/5+: la posicion del notehead esta en el transform del <use>.
                    use_transform = use_element.get('transform')
                    if use_transform:
                        m = re.search(r"translate\(\s*([-\d.]+)[,\s]+([-\d.]+)", use_transform)
                        if m:
                            return {'x': float(m.group(1)), 'y': float(m.group(2))}

            transform_attr = target_element_note_group.get('transform')
            if transform_attr and "translate" in transform_attr:
                try:
                    match = re.search(r"translate\(\s*([-\d\.]+)\s*[, ]?\s*([-\d\.]+)\s*\)", transform_attr)
                    if match:
                        return {'x': float(match.group(1)), 'y': float(match.group(2))}
                except Exception: pass 
    except Exception as e: pass 
    return None 

def anotar_svg_con_intervalos_primera_especie(
    svg_string, 
    score_m21, cf_part_m21, cp_part_m21, 
    datos_movimiento_melodico_cf=None, 
    datos_movimiento_melodico_cp=None,
    species="primera"
):
    print("DEBUG (Anotador): Iniciando anotación de SVG...")
    namespaces_map = {'svg': 'http://www.w3.org/2000/svg'}
    try:
        ET.register_namespace('', namespaces_map['svg']) 
        if isinstance(svg_string, str) and svg_string.strip().startswith('<?xml'):
            svg_string_cleaned = svg_string.split('?>', 1)[-1].strip()
        else:
            svg_string_cleaned = svg_string
        svg_root = ET.fromstring(svg_string_cleaned)
    except ET.ParseError as e:
        print(f"ERROR CRÍTICO (Anotador): Error parseando SVG string: {e}")
        return svg_string 

    arrowhead_id_for_lines = "melodicMovementArrowhead"
    _add_arrowhead_marker_definition(svg_root, namespaces_map, arrowhead_id=arrowhead_id_for_lines, color="#333333", size="15") # Definición de marcador, opcional

    page_margin_group = svg_root.find(".//svg:g[@class='page-margin']", namespaces=namespaces_map)
    target_group_for_annotations = page_margin_group if page_margin_group is not None else svg_root
    
    all_note_coords = {}
    notes_cp_for_coords = []
    if cp_part_m21:
        notes_cp_for_coords = [n for n in cp_part_m21.recurse().getElementsByClass(m21note.Note) if n.isNote and getattr(n, 'id', None)]
    
    notes_cf_for_coords = []
    if cf_part_m21:
        notes_cf_for_coords = [n for n in cf_part_m21.recurse().getElementsByClass(m21note.Note) if n.isNote and getattr(n, 'id', None)]
    
    for note_obj in notes_cp_for_coords + notes_cf_for_coords:
        note_id = getattr(note_obj, 'id')
        if note_id and note_id not in all_note_coords: 
            coords = _get_note_svg_coords(svg_root, note_id)
            if coords:
                all_note_coords[note_id] = coords
            else:
                print(f"DEBUG (Anotador Coords): No se pudieron obtener coords para nota ID {note_id}")

    # --- Sección de Anotación de Intervalos ---
    if cp_part_m21 and cf_part_m21:
        cp_notes_interval_ordered = [n for n in cp_part_m21.recurse().getElementsByClass(m21note.Note) if n.isNote and getattr(n, 'id', None)]
        cf_notes_interval_ordered = [n for n in cf_part_m21.recurse().getElementsByClass(m21note.Note) if n.isNote and getattr(n, 'id', None)]
        min_len = min(len(cp_notes_interval_ordered), len(cf_notes_interval_ordered))
        for i in range(min_len):
            n_cp, n_cf = cp_notes_interval_ordered[i], cf_notes_interval_ordered[i]
            cp_id, cf_id = getattr(n_cp, 'id', None), getattr(n_cf, 'id', None)
            if not cp_id or not cf_id: continue
            inter = interval.Interval(noteStart=n_cf, noteEnd=n_cp)
            interval_text = str(inter.simpleName) if inter.simpleName else (str(inter.generic.value) if inter.generic else "?")
            if inter.specifier and inter.generic and str(inter.specifier) in ['P', 'M', 'm']:
                interval_text = str(inter.generic.value)
            
            coord_cp_svg, coord_cf_svg = all_note_coords.get(cp_id), all_note_coords.get(cf_id)
            if coord_cp_svg and coord_cf_svg:
                font_size_svg_units = 270 
                text_x = coord_cf_svg['x'] + (font_size_svg_units * 0.7) 
                text_y = (min(coord_cp_svg['y'], coord_cf_svg['y']) + max(coord_cp_svg['y'], coord_cf_svg['y'])) / 2
                text_element = ET.Element(f"{{{namespaces_map['svg']}}}text", {
                    "x": str(text_x), "y": str(text_y),
                    "font-family": "Arial, Helvetica, sans-serif", "font-size": str(font_size_svg_units) + "px",
                    "fill": "blue", "text-anchor": "middle", "dominant-baseline": "middle"
                })
                text_element.text = interval_text
                target_group_for_annotations.append(text_element)

    # --- Sección de Anotación de Líneas de Movimiento Coloreadas ---
    print(f"DEBUG (Anotador): Iniciando anotación de líneas de movimiento.")
    
    USAR_CABEZAS_DE_FLECHA = True # Mantenemos esto en False por ahora
    
    # CAMBIO: Aumentar el grosor de la línea
    line_stroke_width = "7.5" # 2.5 * 3 = 7.5

    if datos_movimiento_melodico_cf:
        print(f"DEBUG (Anotador): Procesando {len(datos_movimiento_melodico_cf)} movimientos para CF.")
        for nota_anterior_id, nota_actual_id, movimiento_tipo_str in datos_movimiento_melodico_cf:
            coord_nota1 = all_note_coords.get(nota_anterior_id)
            coord_nota2 = all_note_coords.get(nota_actual_id)
            if coord_nota1 and coord_nota2:
                color = "black" 
                if movimiento_tipo_str == "ascendente": color = "green"
                elif movimiento_tipo_str == "descendente": color = "red"
                _draw_connecting_line(target_group_for_annotations, coord_nota1, coord_nota2, namespaces_map,
                                      line_color=color, stroke_width=line_stroke_width,
                                      use_arrowhead=USAR_CABEZAS_DE_FLECHA, arrowhead_id=arrowhead_id_for_lines)
            else:
                print(f"DEBUG (Anotador CF): Coords faltantes para línea entre {nota_anterior_id} y {nota_actual_id}.")

    if datos_movimiento_melodico_cp:
        print(f"DEBUG (Anotador): Procesando {len(datos_movimiento_melodico_cp)} movimientos para CP.")
        for nota_anterior_id, nota_actual_id, movimiento_tipo_str in datos_movimiento_melodico_cp:
            coord_nota1 = all_note_coords.get(nota_anterior_id)
            coord_nota2 = all_note_coords.get(nota_actual_id)
            if coord_nota1 and coord_nota2:
                color = "black" 
                if movimiento_tipo_str == "ascendente": color = "green"
                elif movimiento_tipo_str == "descendente": color = "red"
                _draw_connecting_line(target_group_for_annotations, coord_nota1, coord_nota2, namespaces_map,
                                      line_color=color, stroke_width=line_stroke_width,
                                      use_arrowhead=USAR_CABEZAS_DE_FLECHA, arrowhead_id=arrowhead_id_for_lines)
            else:
                print(f"DEBUG (Anotador CP): Coords faltantes para línea entre {nota_anterior_id} y {nota_actual_id}.")
    
    final_svg_string = ET.tostring(svg_root, encoding="unicode", xml_declaration=False)
    
    debug_svg_path = "debug_annotated_output_final.svg" 
    try:
        with open(debug_svg_path, "w", encoding="utf-8") as f_svg_debug_annotated:
            f_svg_debug_annotated.write(final_svg_string)
        print(f"DEBUG (Anotador): SVG ANOTADO final guardado en {os.path.abspath(debug_svg_path)}")
    except Exception as e_save_annot_svg:
        print(f"DEBUG (Anotador): Error al guardar SVG ANOTADO de depuración: {e_save_annot_svg}")
        
    return final_svg_string
