# segunda_especie/anotador_svg_segunda.py (v15 - Coloreado Final)

import xml.etree.ElementTree as ET
from music21 import interval as m21interval 
import os 
import re 

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace('', SVG_NS) 
NAMESPACES_MAP = {'svg': SVG_NS}

def _get_simplified_interval_text_v6(interval_obj, mostrar_compuesto_entre_parentesis=True):
    # Esta función de ayuda convierte un objeto de intervalo en texto simple (ej. '6', '5(12)').
    if not interval_obj: return "?"
    nombre_simple_a_parsear = interval_obj.simpleName 
    numero_simple_str = "?"
    match_simple = re.search(r'\d+', nombre_simple_a_parsear)
    if match_simple:
        numero_simple_str = match_simple.group(0)
    texto_final = numero_simple_str
    is_actually_compound = False
    if interval_obj.generic and interval_obj.generic.value is not None:
        if interval_obj.generic.value > 8: is_actually_compound = True
    if mostrar_compuesto_entre_parentesis and is_actually_compound:
        numero_compuesto_str = "?"
        if interval_obj.generic and interval_obj.generic.value:
            numero_compuesto_str = str(interval_obj.generic.value)
        if numero_compuesto_str != "?" and numero_compuesto_str != numero_simple_str:
            texto_final += f"({numero_compuesto_str})"
    return texto_final

# --- FIRMA DE FUNCIÓN MODIFICADA para aceptar la lista de IDs rojos ---
def anotar_svg_intervalos_2da_especie(svg_string_original, datos_intervalos_2da, all_note_coords_dict, ids_notas_rojas=None):
    print("\n--- DEBUG (Anotador 2da Especie): Iniciando anotación (v15 - Coloreado Final) ---")

    # Inicializar ids_notas_rojas como un conjunto para búsquedas rápidas
    if ids_notas_rojas is None:
        ids_notas_rojas = set()
    else:
        ids_notas_rojas = set(ids_notas_rojas)

    if not datos_intervalos_2da or not all_note_coords_dict:
        print("DEBUG (Anotador 2da Especie): Faltan datos de intervalos o coordenadas. Saliendo sin anotar.")
        return svg_string_original
        
    try:
        svg_root = ET.fromstring(svg_string_original.split('?>', 1)[-1].strip() if '<?xml' in svg_string_original else svg_string_original)
    except ET.ParseError as e:
        print(f"ERROR CRÍTICO (Anotador 2da Especie): Error parseando SVG: {e}")
        return svg_string_original

    target_group_for_annotations = svg_root.find(".//svg:g[@class='page-margin']", namespaces=NAMESPACES_MAP) or svg_root
    
    # --- Parámetros de Estilo ---
    font_size_svg_units = 220 
    color_normal = "forestgreen"
    color_problema = "red" # Color para los problemas
    font_family = "Arial, Helvetica, sans-serif"

    # --- Ajustes de Posición ---
    y_pivote_ajuste_desde_medio = -(font_size_svg_units * 0.4) 
    offset_x_desde_cp = font_size_svg_units * 0.6 

    print(f"DEBUG (Anotador 2da Especie): Anotando {len(datos_intervalos_2da)} intervalos. {len(ids_notas_rojas)} notas marcadas para colorear.")
    
    fixed_y_coordinate_for_intervals = None

    for i, (cp_note, cf_note, intervalo_obj) in enumerate(datos_intervalos_2da):
        cp_id = getattr(cp_note, 'id', None)
        cf_id = getattr(cf_note, 'id', None)

        if not cp_id or not cf_id: continue
        
        coord_cp_svg = all_note_coords_dict.get(cp_id)
        coord_cf_svg = all_note_coords_dict.get(cf_id)
        
        if not coord_cp_svg or not coord_cf_svg:
            continue
            
        interval_text = _get_simplified_interval_text_v6(intervalo_obj) 
        
        text_x = coord_cp_svg['x'] + offset_x_desde_cp
        
        if fixed_y_coordinate_for_intervals is None:
            mid_y_inicial = (coord_cp_svg['y'] + coord_cf_svg['y']) / 2
            fixed_y_coordinate_for_intervals = mid_y_inicial + y_pivote_ajuste_desde_medio
            print(f"  PUNTO PIVOTE Y (v15) establecido en: {fixed_y_coordinate_for_intervals:.1f}")

        text_y = fixed_y_coordinate_for_intervals
        
        # --- LÓGICA DE COLOREADO FINAL ---
        # Comprobar si el ID de la nota del contrapunto está en el conjunto de notas rojas
        fill_color = color_problema if cp_id in ids_notas_rojas else color_normal
        
        text_element = ET.Element(f"{{{SVG_NS}}}text", {
            "x": str(text_x), "y": str(text_y),
            "font-family": font_family, "font-size": str(font_size_svg_units) + "px",
            "fill": fill_color, # Usar el color determinado
            "text-anchor": "middle",
            "dominant-baseline": "middle" 
        })
        text_element.text = interval_text
        target_group_for_annotations.append(text_element)
        
    final_svg_string = ET.tostring(svg_root, encoding="unicode")
    
    debug_svg_path = "debug_2da_especie_anotado_pos_v15.svg" # Nuevo nombre de versión
    try:
        with open(debug_svg_path, "w", encoding="utf-8") as f:
            f.write(final_svg_string)
        print(f"DEBUG (Anotador 2da Especie): SVG anotado (v15) guardado en {os.path.abspath(debug_svg_path)}")
    except Exception as e:
        print(f"DEBUG (Anotador 2da Especie): Error al guardar SVG de depuración: {e}")
    
    print("--- DEBUG (Anotador 2da Especie): Anotación (v15) completada. ---")
    return final_svg_string
