# verovio_pdf.py (v12 - Configuración A4 Horizontal Limpia)

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
    if note_element_g is None: return None
    try:
        notehead_group = note_element_g.find("./svg:g[@class='notehead']", NAMESPACES_SVG_MAP) or \
                         note_element_g.find("./svg:g[@data-class='notehead']", NAMESPACES_SVG_MAP)
        if notehead_group is not None:
            use_element = notehead_group.find("./svg:use", NAMESPACES_SVG_MAP)
            if use_element is not None:
                x = use_element.get('x'); y = use_element.get('y')
                if x and y: return {'x': float(x), 'y': float(y)}
        
        transform = note_element_g.get('transform')
        if transform and "translate" in transform:
            match = re.search(r"translate\(\s*([-\d\.]+)\s*[, ]?\s*([-\d\.]+)\s*\)", transform)
            if match: return {'x': float(match.group(1)), 'y': float(match.group(2))}
    except: pass 
    return None

ANNOTATION_FUNC_1RA_LOADED = False
try:
    from primera_especie.anotador_svg_intervalos import anotar_svg_con_intervalos_primera_especie
    ANNOTATION_FUNC_1RA_LOADED = True
except ImportError: pass 

ANNOTATION_FUNC_2DA_LOADED = False
try:
    from segunda_especie.anotador_svg_segunda import anotar_svg_intervalos_2da_especie
    ANNOTATION_FUNC_2DA_LOADED = True
except ImportError: pass 

def generar_svg_de_musicxml(musicxml_path, verovio_options_dict=None):
    print(f"--- DEBUG (SVG Gen): Iniciando generar_svg_de_musicxml ---")
    
    # --- CONFIGURACIÓN A4 LANDSCAPE ESTÁNDAR ---
    if verovio_options_dict is None: 
        verovio_options_dict = {
            "pageWidth": 2970,        # A4 Landscape ancho
            "pageHeight": 2100,       # A4 Landscape alto
            "scale": 50,              # Escala 50 (Estándar y legible para landscape)
            "adjustPageHeight": True, 
            "pageMarginTop": 100, 
            "pageMarginBottom": 100, 
            "pageMarginLeft": 100, 
            "pageMarginRight": 100, 
            "header": "none", "footer": "none", "breaks": "auto", "svgHtml5": True
        }
    
    svg_content_str = ""
    error_msg = None
    
    try:
        tk = verovio.toolkit()
        try:
            data_path = os.path.join(os.path.dirname(verovio.__file__), "data")
            if not os.path.exists(data_path): data_path = "/usr/local/share/verovio/data"
            if os.path.exists(data_path): tk.setResourcePath(data_path)
        except: pass
        
        tk.setOptions(verovio_options_dict)
        with open(musicxml_path, "r", encoding="utf-8") as f: tk.loadData(f.read())
        svg_content_str = tk.renderToSVG(1).replace('overflow="inherit"', 'overflow="visible"')
        
    except Exception as e:
        error_msg = f"Error Verovio: {e}"
        traceback.print_exc()
        svg_content_str = f'<svg xmlns="{SVG_NS_VEROVIO}" width="500" height="100"><text x="10" y="50" fill="red">{error_msg}</text></svg>'
        
    return svg_content_str, error_msg

def convertir_svg_a_pdf_tempfile(svg_content, dpi=96):
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp: tmp_path = tmp.name
        cairosvg.svg2pdf(bytestring=svg_content.encode("utf-8"), write_to=tmp_path, dpi=dpi)
        return tmp_path
    except:
        if tmp_path: os.remove(tmp_path)
        return None

def generar_pdf_partitura(musicxml_path, output_pdf="partitura.pdf", verovio_options=None,
                          score_m21_obj=None, cf_part_m21_obj=None, cp_part_m21_obj=None, 
                          species_str="primera", datos_anotacion_especie=None ):
    
    svg_str, err = generar_svg_de_musicxml(musicxml_path, verovio_options)
    if err: print(err)
    final_svg = svg_str 

    if score_m21_obj and (ANNOTATION_FUNC_1RA_LOADED or ANNOTATION_FUNC_2DA_LOADED):
        svg_et = None
        try:
            clean_svg = svg_str.split('?>', 1)[-1].strip() if '<?xml' in svg_str else svg_str
            svg_et = ET.fromstring(clean_svg)
        except: pass

        if svg_et is not None:
            coords_dict = {}
            staves = svg_et.findall(".//svg:g[@data-class='staff']", NAMESPACES_SVG_MAP)
            parts = score_m21_obj.parts
            if len(parts) > 0 and len(staves) % len(parts) == 0:
                for i, part in enumerate(parts):
                    m21_notes = [n for n in part.flatten().notes if hasattr(n,'id') and n.id]
                    svg_notes = []
                    for j, staff in enumerate(staves):
                        if j % len(parts) == i:
                            svg_notes.extend(staff.findall(".//svg:g[@data-class='note']", NAMESPACES_SVG_MAP))
                    if len(m21_notes) == len(svg_notes):
                        for k, n in enumerate(m21_notes):
                            c = _get_note_svg_coords(svg_et, svg_notes[k])
                            if c: coords_dict[n.id] = c

            annotated = None
            if species_str == "segunda" and ANNOTATION_FUNC_2DA_LOADED and datos_anotacion_especie:
                try:
                    annotated = anotar_svg_intervalos_2da_especie(
                        svg_str, datos_anotacion_especie.get('intervalos'), coords_dict,
                        ids_notas_rojas=datos_anotacion_especie.get('ids_rojos', []),
                        datos_movimiento_melodico_cp=datos_anotacion_especie.get('movimientos_cp', [])
                    )
                except: traceback.print_exc()
            elif species_str == "primera" and ANNOTATION_FUNC_1RA_LOADED:
                try:
                    annotated = anotar_svg_con_intervalos_primera_especie(
                        svg_str, score_m21_obj, cf_part_m21_obj, cp_part_m21_obj,
                        datos_movimiento_melodico_cf=datos_anotacion_especie.get('movimientos_cf'),
                        datos_movimiento_melodico_cp=datos_anotacion_especie.get('movimientos_cp'),
                        species="primera"
                    )
                except: traceback.print_exc()
            if annotated: final_svg = annotated
    
    pdf_path = convertir_svg_a_pdf_tempfile(final_svg)
    if pdf_path:
        try: shutil.copy2(pdf_path, output_pdf); return output_pdf
        except: pass
    return None