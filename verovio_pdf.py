# verovio_pdf.py (v6 - Conexión final para pasar IDs rojos al anotador)

import os
import verovio
import cairosvg
import tempfile
import shutil
import traceback
import xml.etree.ElementTree as ET 
import re 
from music21 import note as m21note

SVG_NS_VEROVIO = "http://www.w3.org/2000/svg"
ET.register_namespace('', SVG_NS_VEROVIO)
NAMESPACES_SVG_MAP = {'svg': SVG_NS_VEROVIO}

def _get_note_svg_coords(svg_root_et, note_element_g):
    # Extrae las coordenadas X, Y de un elemento de nota <g> del SVG.
    if note_element_g is None: return None
    try:
        # Intenta encontrar las coordenadas en el elemento <use> dentro de <g class="notehead">
        notehead_group = note_element_g.find("./svg:g[@class='notehead']", NAMESPACES_SVG_MAP)
        if notehead_group is None: notehead_group = note_element_g.find("./svg:g[@data-class='notehead']", NAMESPACES_SVG_MAP)
        if notehead_group is not None:
            use_element = notehead_group.find("./svg:use", NAMESPACES_SVG_MAP)
            if use_element is not None:
                x_attr = use_element.get('x'); y_attr = use_element.get('y')
                if x_attr is not None and y_attr is not None:
                    try: return {'x': float(x_attr), 'y': float(y_attr)}
                    except ValueError: pass 
        
        # Como fallback, intenta encontrar las coordenadas en el atributo 'transform' del grupo principal
        transform_attr = note_element_g.get('transform')
        if transform_attr and "translate" in transform_attr:
            try:
                match = re.search(r"translate\(\s*([-\d\.]+)\s*[, ]?\s*([-\d\.]+)\s*\)", transform_attr)
                if match: return {'x': float(match.group(1)), 'y': float(match.group(2))}
            except Exception: pass 
    except Exception as e_find: 
        print(f"Error (Coords) extrayendo coords de elemento SVG: {e_find}")
    return None

# --- Carga dinámica de funciones de anotación ---
ANNOTATION_FUNC_1RA_LOADED = False
try:
    from primera_especie.anotador_svg_intervalos import anotar_svg_con_intervalos_primera_especie
    ANNOTATION_FUNC_1RA_LOADED = True
except ImportError : pass 

ANNOTATION_FUNC_2DA_LOADED = False
try:
    from segunda_especie.anotador_svg_segunda import anotar_svg_intervalos_2da_especie
    ANNOTATION_FUNC_2DA_LOADED = True
except ImportError : pass 

def generar_svg_de_musicxml(musicxml_path, verovio_options_dict=None):
    # Genera una cadena de texto SVG a partir de un archivo MusicXML usando Verovio.
    print(f"--- DEBUG (SVG Gen): Iniciando generar_svg_de_musicxml para '{musicxml_path}' ---")
    if verovio_options_dict is None: 
        verovio_options_dict = {"pageHeight": 600, "adjustPageHeight": True, "scale": 60, "pageMarginTop": 40, "pageMarginBottom": 40, "pageMarginLeft": 40, "pageMarginRight": 40, "landscape": 0, "breaks": "none", "svgHtml5": True}
    
    svg_content_str = ""
    error_msg_verovio = None
    
    try:
        tk_instance = verovio.toolkit()
        try:
            default_data_path = os.path.join(os.path.dirname(verovio.__file__), "data")
            if not os.path.exists(default_data_path):
                default_data_path = os.path.join(os.path.dirname(verovio.__file__), '..', 'share', 'verovio', "data")
                if not os.path.exists(default_data_path): default_data_path = "/usr/local/share/verovio/data" 
            if os.path.exists(default_data_path): 
                tk_instance.setResourcePath(default_data_path)
            else: 
                print(f"ADVERTENCIA CRÍTICA (SVG Gen): Ruta de recursos Verovio NO ENCONTRADA.")
        except Exception as e_path: 
            print(f"ERROR (SVG Gen): Configurando ruta de recursos Verovio: {e_path}")
        
        tk_instance.setOptions(verovio_options_dict)
        with open(musicxml_path, "r", encoding="utf-8") as f: 
            musicxml_data_str = f.read()
        
        if not tk_instance.loadData(musicxml_data_str):
            error_msg_verovio = "Verovio no pudo cargar los datos del MusicXML."
            svg_content_str = f'<svg xmlns="{SVG_NS_VEROVIO}" width="600" height="100"><text x="10" y="40" fill="red">{error_msg_verovio}</text></svg>'
        else:
            svg_temp_str = tk_instance.renderToSVG(1) 
            try:
                with open("debug_raw_verovio_output.svg", "w", encoding="utf-8") as f_debug_raw: 
                    f_debug_raw.write(svg_temp_str)
            except Exception as e_save_raw: 
                print(f"ERROR (SVG Gen): No se pudo guardar debug_raw_verovio_output.svg: {e_save_raw}")
            
            svg_content_str = svg_temp_str.replace('overflow="inherit"', 'overflow="visible"')
            
    except Exception as e_verovio_exc:
        error_msg_verovio = f"Excepción en Verovio: {str(e_verovio_exc)}"
        traceback.print_exc()
        svg_content_str = f'<svg xmlns="{SVG_NS_VEROVIO}" width="600" height="100"><text x="10" y="40" fill="red">Error Verovio: {e_verovio_exc}</text></svg>'
        
    return svg_content_str, error_msg_verovio

def convertir_svg_a_pdf_tempfile(svg_content_str, dpi=96):
    # Convierte una cadena de texto SVG a un archivo PDF temporal.
    temp_pdf_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="svg_to_pdf_") as tmp_pdf_file:
            temp_pdf_file_path = tmp_pdf_file.name
        cairosvg.svg2pdf(bytestring=svg_content_str.encode("utf-8"), write_to=temp_pdf_file_path, dpi=dpi)
        if not os.path.exists(temp_pdf_file_path) or os.path.getsize(temp_pdf_file_path) == 0:
            if os.path.exists(temp_pdf_file_path):
                try: os.remove(temp_pdf_file_path)
                except Exception as e_remove_empty: print(f"Advertencia: No se pudo eliminar PDF temporal problemático {temp_pdf_file_path}: {e_remove_empty}")
            raise IOError("CairoSVG falló en crear o llenar el PDF temporal correctamente.")
        return temp_pdf_file_path
    except Exception as e_cairosvg_exc:
        print(f"ERROR (SVG->PDF): EXCEPCIÓN SVG->PDF: {e_cairosvg_exc}") 
        traceback.print_exc()
        if temp_pdf_file_path and os.path.exists(temp_pdf_file_path):
            try: os.remove(temp_pdf_file_path)
            except Exception as e_remove_err: print(f"Advertencia: No se pudo eliminar PDF temporal {temp_pdf_file_path} tras error: {e_remove_err}")
        return None

def generar_pdf_partitura(musicxml_path, output_pdf="partitura.pdf", verovio_options=None,
                          score_m21_obj=None, cf_part_m21_obj=None, cp_part_m21_obj=None, 
                          species_str="primera", datos_anotacion_especie=None ):
    print(f"\n--- DEBUG (PDF Partitura): Iniciando generar_pdf_partitura para especie: {species_str} ---")
    
    svg_string_original, error_svg_gen = generar_svg_de_musicxml(musicxml_path, verovio_options)
    if error_svg_gen: print(f"ERROR (PDF Partitura): Error de Verovio al generar SVG base: {error_svg_gen}")
    
    final_svg_string_para_conversion = svg_string_original 

    if score_m21_obj and (ANNOTATION_FUNC_1RA_LOADED or ANNOTATION_FUNC_2DA_LOADED):
        svg_root_et = None
        try:
            if isinstance(svg_string_original, str) and svg_string_original.strip().startswith('<?xml'):
                svg_string_cleaned = svg_string_original.split('?>', 1)[-1].strip()
            else: svg_string_cleaned = svg_string_original
            svg_root_et = ET.fromstring(svg_string_cleaned)
        except ET.ParseError as e_parse: 
            print(f"ERROR (PDF Partitura): No se pudo parsear SVG: {e_parse}"); svg_root_et = None

        if svg_root_et is not None:
            print("DEBUG (PDF Partitura): --- INICIO EXTRACCIÓN DE COORDENADAS (Mapeo por Grupo de Pentagramas) ---")
            all_note_coords_dict = {}
            
            # Estrategia de mapeo robusta que agrupa pentagramas por parte
            svg_all_staves = svg_root_et.findall(".//svg:g[@data-class='staff']", namespaces=NAMESPACES_SVG_MAP)
            m21_parts_in_score_order = score_m21_obj.parts
            
            num_parts = len(m21_parts_in_score_order)
            if num_parts > 0 and len(svg_all_staves) % num_parts == 0:
                for i in range(num_parts):
                    part_obj = m21_parts_in_score_order[i]
                    part_id = getattr(part_obj, 'id', f'part_{i}')
                    
                    m21_notes_in_part = [n for n in part_obj.flatten().notes if hasattr(n, 'id') and n.id]
                    
                    svg_notes_in_grouped_staves = []
                    for j, staff_element in enumerate(svg_all_staves):
                        if j % num_parts == i:
                            svg_notes_in_grouped_staves.extend(staff_element.findall(".//svg:g[@data-class='note']", namespaces=NAMESPACES_SVG_MAP))
                    
                    if len(m21_notes_in_part) == len(svg_notes_in_grouped_staves):
                        for k, m21_note_obj in enumerate(m21_notes_in_part):
                            svg_note_element = svg_notes_in_grouped_staves[k]
                            coords = _get_note_svg_coords(svg_root_et, svg_note_element)
                            if coords:
                                all_note_coords_dict[m21_note_obj.id] = coords
                    else:
                        print(f"    ADVERTENCIA CRÍTICA: Desajuste de notas para la parte {part_id}. No se mapeará esta parte.")
            else:
                print(f"ADVERTENCIA CRÍTICA: El número de pentagramas en el SVG ({len(svg_all_staves)}) no es un múltiplo del número de partes en music21 ({num_parts}).")

            print(f"DEBUG (PDF Partitura): --- FIN EXTRACCIÓN --- Coordenadas extraídas para {len(all_note_coords_dict)} notas en TOTAL.")
            
            # --- LÓGICA DE LLAMADA AL ANOTADOR (CORREGIDA) ---
            annotated_svg_string = None
            if species_str == "segunda" and ANNOTATION_FUNC_2DA_LOADED and datos_anotacion_especie:
                datos_intervalos_para_anotador = datos_anotacion_especie.get('intervalos')
                # --- CAMBIO IMPORTANTE AQUÍ ---
                # Extraemos la lista de IDs rojos y se la pasamos al anotador
                ids_rojos_para_anotador = datos_anotacion_especie.get('ids_rojos', [])
                
                try: 
                    annotated_svg_string = anotar_svg_intervalos_2da_especie(
                        svg_string_original, 
                        datos_intervalos_para_anotador, 
                        all_note_coords_dict,
                        ids_notas_rojas=ids_rojos_para_anotador # Pasamos la lista como argumento
                    )
                except Exception as e: print(f"ERROR anotando 2da: {e}"); traceback.print_exc()
            
            # (Aquí iría la lógica para primera especie si también la adaptamos)

            if annotated_svg_string: 
                final_svg_string_para_conversion = annotated_svg_string
    
    # ... (Resto de la función sin cambios) ...
    ruta_pdf_temporal = convertir_svg_a_pdf_tempfile(final_svg_string_para_conversion)
    if not ruta_pdf_temporal: return None
    try:
        shutil.copy2(ruta_pdf_temporal, output_pdf)
        print(f"DEBUG (PDF Partitura): PDF final copiado a: {output_pdf}")
        return output_pdf
    except Exception as e_copia_final_exc: 
        print(f"ERROR (PDF Partitura): Excepción al copiar PDF final: {e_copia_final_exc}"); return None
    finally:
        if ruta_pdf_temporal and os.path.exists(ruta_pdf_temporal):
            try: os.remove(ruta_pdf_temporal)
            except Exception: pass
