# primera_especie/anotador_svg_intervalos.py
import xml.etree.ElementTree as ET
from music21 import interval, note as m21note 
import re
import os

def _get_note_svg_coords(svg_root, note_id_m21_value, search_attr="data-id"):
    # Esta función ya está funcionando bien.
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
                        except ValueError:
                            pass 
            # Fallback si no se encuentra en <use>
            transform_attr = target_element_note_group.get('transform')
            if transform_attr and "translate" in transform_attr:
                try:
                    transform_parts = transform_attr.split('(')[1].split(')')[0]
                    coords_re = re.findall(r"[-+]?\d*\.?\d+|[-+]?\d+", transform_parts)
                    coords = [float(c.strip()) for c in coords_re]
                    if len(coords) >= 2: return {'x': coords[0], 'y': coords[1]}
                except Exception: pass
    except Exception as e:
        print(f"DEBUG Anotador (_get_note_svg_coords): Excepción extrayendo coords SVG para {note_id_m21_value}: {e}")
        # traceback.print_exc() # Descomentar para traceback completo si es necesario
    return None


def anotar_svg_con_intervalos_primera_especie(svg_string, score_m21, cf_part_m21, cp_part_m21, species="primera"):
    print("DEBUG (Anotador): Iniciando anotación de SVG para primera especie...")
    namespaces_map = {'svg': 'http://www.w3.org/2000/svg'}
    try:
        ET.register_namespace('', namespaces_map['svg']) 
        if svg_string.startswith('<?xml'):
            svg_string_cleaned = svg_string.split('?>', 1)[1]
        else:
            svg_string_cleaned = svg_string
        svg_root = ET.fromstring(svg_string_cleaned)
    except ET.ParseError as e:
        print(f"DEBUG (Anotador): Error parseando SVG: {e}")
        return svg_string 

    if cp_part_m21 is None or cf_part_m21 is None:
        print("DEBUG (Anotador): Error - Partes CP o CF no proporcionadas.")
        return ET.tostring(svg_root, encoding="unicode", xml_declaration=False)

    page_margin_group = svg_root.find(".//svg:g[@class='page-margin']", namespaces=namespaces_map)
    if page_margin_group is None:
        print("ADVERTENCIA (Anotador): No se encontró el grupo <g class='page-margin'>. Anotaciones en root.")
        target_group_for_annotations = svg_root 
    else:
        print("DEBUG (Anotador): Grupo <g class='page-margin'> encontrado.")
        target_group_for_annotations = page_margin_group

    cp_notes = [n for n in cp_part_m21.recurse().getElementsByClass(m21note.Note) if n.isNote]
    cf_notes = [n for n in cf_part_m21.recurse().getElementsByClass(m21note.Note) if n.isNote]
    
    min_len = min(len(cp_notes), len(cf_notes))
    print(f"DEBUG (Anotador): Procesando {min_len} pares de notas para intervalos.")

    anotaciones_agregadas = 0
    for i in range(min_len):
        n_cp = cp_notes[i] 
        n_cf = cf_notes[i]   
        cp_id = getattr(n_cp, 'id', None)
        cf_id = getattr(n_cf, 'id', None)

        if not cp_id or not cf_id: continue

        inter = interval.Interval(noteStart=n_cf, noteEnd=n_cp)
        interval_text = "?"
        if inter.specifier is not None and inter.generic is not None:
            especificador_str = str(inter.specifier) 
            if especificador_str in ['P', 'M', 'm']: 
                interval_text = str(inter.generic.value) 
            else: 
                interval_text = str(inter.simpleName) 
        elif inter.simpleName: 
            interval_text = str(inter.simpleName)
        
        coord_cp_svg = _get_note_svg_coords(svg_root, cp_id)
        coord_cf_svg = _get_note_svg_coords(svg_root, cf_id)

        if coord_cp_svg and coord_cf_svg:
            # --- AJUSTES DE POSICIONAMIENTO Y TAMAÑO ---
            font_size_svg_units = 270  # Aumentado de 180 a 220 (o prueba 200, 250)
            
            # Posición X:
            # El 'x' de <use> es el inicio de la cabeza de nota.
            # El ancho de una cabeza de nota (símbolo E0A2) es de aprox. 400 unidades en su propio viewBox de 1000.
            # La escala de Verovio (ej. 60) y el viewBox general del SVG afectan cómo se traduce esto.
            # Vamos a intentar centrarlo usando el promedio de las X y un text-anchor="middle".
            # Para moverlo "un poco más a la derecha" del inicio de la nota del CF:
            text_x = coord_cf_svg['x'] + (font_size_svg_units * 0.7) # Offset relativo al tamaño de la fuente
                                                                    # Antes era +0 del promedio, o +35 fijo.
                                                                    # Prueba con este offset o ajusta.
                                                                    # Si quieres centrarlo entre las notas:
                                                                    # avg_x_noteheads = (coord_cp_svg['x'] + coord_cf_svg['x']) / 2
                                                                    # text_x = avg_x_noteheads

            # Posición Y:
            y_nota_superior_svg = min(coord_cp_svg['y'], coord_cf_svg['y'])
            y_nota_inferior_svg = max(coord_cp_svg['y'], coord_cf_svg['y'])
            punto_medio_y_cabezas = (y_nota_superior_svg + y_nota_inferior_svg) / 2
            
            # Con dominant-baseline="middle", la coordenada 'y' es el centro vertical del texto.
            text_y = punto_medio_y_cabezas 
                                    
            text_element = ET.Element(f"{{{namespaces_map['svg']}}}text")
            text_element.set("x", str(text_x))
            text_element.set("y", str(text_y))
            text_element.set("font-family", "Arial, Helvetica, sans-serif")
            text_element.set("font-size", str(font_size_svg_units) + "px")
            text_element.set("fill", "blue")    
            text_element.set("text-anchor", "middle") 
            text_element.set("dominant-baseline", "middle") # Ayuda a centrar verticalmente
            text_element.text = interval_text
            
            print(f"DEBUG (Anotador): Añadiendo texto '{interval_text}' en X={text_x:.2f}, Y={text_y:.2f} con font-size={font_size_svg_units}px")
            target_group_for_annotations.append(text_element)
            anotaciones_agregadas += 1
        else:
            if not coord_cp_svg: print(f"DEBUG (Anotador): Fallo final en encontrar coords para CP ID '{cp_id}'")
            if not coord_cf_svg: print(f"DEBUG (Anotador): Fallo final en encontrar coords para CF ID '{cf_id}'")

    print(f"DEBUG (Anotador): Fin de anotación SVG. Se intentaron agregar {anotaciones_agregadas} números de intervalo.")
    
    final_svg_string = ET.tostring(svg_root, encoding="unicode", xml_declaration=False)
    debug_annotated_svg_path = "debug_annotated_output.svg"
    try:
        with open(debug_annotated_svg_path, "w", encoding="utf-8") as f_svg_debug_annotated:
            f_svg_debug_annotated.write(final_svg_string)
        print(f"DEBUG (Anotador): SVG ANOTADO guardado en {os.path.abspath(debug_annotated_svg_path)}")
    except Exception as e_save_annot_svg:
        print(f"DEBUG (Anotador): Error al guardar SVG ANOTADO de depuración: {e_save_annot_svg}")
        
    return final_svg_string
