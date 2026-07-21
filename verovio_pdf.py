# verovio_pdf.py (v17 - Modo Local Seguro: Adiós WinError 32 y Fuentes Locales)

import os
import io
import verovio
import shutil
import traceback
import xml.etree.ElementTree as ET
import re
from music21 import note as m21note
import time
import resvg_py
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.utils import ImageReader

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
                # Verovio 4/5+: posicion en transform="translate(x,y) ..." del <use>.
                use_tr = use_element.get('transform')
                if use_tr:
                    m = re.search(r"translate\(\s*([-\d.]+)[,\s]+([-\d.]+)", use_tr)
                    if m: return {'x': float(m.group(1)), 'y': float(m.group(2))}

        transform = note_element_g.get('transform')
        if transform and "translate" in transform:
            match = re.search(r"translate\(\s*([-\d\.]+)\s*[, ]?\s*([-\d\.]+)\s*\)", transform)
            if match: return {'x': float(match.group(1)), 'y': float(match.group(2))}
    except: pass 
    return None

# Importaciones dinámicas
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
    
    if verovio_options_dict is None: 
        verovio_options_dict = {
            "pageWidth": 2970, "pageHeight": 2100, "scale": 50,
            "adjustPageHeight": True, 
            "pageMarginTop": 100, "pageMarginBottom": 100, 
            "pageMarginLeft": 100, "pageMarginRight": 100, 
            "header": "none", "footer": "none", "breaks": "auto", "svgHtml5": True
        }
    
    svg_content_str = ""
    error_msg = None
    
    try:
        tk = verovio.toolkit()
        
        # --- CARGA DE FUENTES LOCALES (PRIORIDAD ABSOLUTA) ---
        # Buscamos la carpeta 'data' exactamente donde estamos ejecutando el script
        ruta_data_local = os.path.join(os.getcwd(), "data")
        
        if os.path.exists(ruta_data_local) and os.path.isdir(ruta_data_local):
            # Verificar que los archivos existan
            if os.path.exists(os.path.join(ruta_data_local, "Bravura.woff")):
                tk.setResourcePath(ruta_data_local)
                print(f"✅ DEBUG: Fuentes cargadas desde: {ruta_data_local}")
            else:
                print(f"⚠️ DEBUG: La carpeta data existe pero no tiene Bravura.woff")
        else:
            print(f"❌ ADVERTENCIA: No se encontró la carpeta '{ruta_data_local}'")

        tk.setOptions(verovio_options_dict)
        with open(musicxml_path, "r", encoding="utf-8") as f: tk.loadData(f.read())
        svg_content_str = tk.renderToSVG(1).replace('overflow="inherit"', 'overflow="visible"')
        
    except Exception as e:
        error_msg = f"Error Verovio: {e}"
        traceback.print_exc()
        svg_content_str = f'<svg xmlns="{SVG_NS_VEROVIO}" width="500" height="100"><text x="10" y="50" fill="red">{error_msg}</text></svg>'
        
    return svg_content_str, error_msg

def convertir_svg_a_pdf_local(svg_content, zoom=3.0):
    """
    Convierte el SVG a PDF: resvg (SVG -> PNG) + reportlab (PNG -> PDF).

    resvg (motor Rust) renderiza correctamente los glifos SMuFL de Verovio (via
    <use>), el escalado del <svg viewBox> anidado y las anotaciones (texto/lineas).
    Historial: cairosvg fallaba con GDI en Windows; svglib no aplicaba el escalado
    del viewBox anidado (partitura rota). El PDF resultante es raster de alta
    resolucion (zoom por defecto 3x); el informe textual sigue siendo vectorial.
    """
    nombre_seguro = "temp_partitura_generada.pdf"

    # Asegurarnos de que no exista o que se pueda borrar
    if os.path.exists(nombre_seguro):
        try: os.remove(nombre_seguro)
        except: pass

    try:
        png_bytes = bytes(resvg_py.svg_to_bytes(
            svg_string=svg_content, zoom=zoom, background="#ffffff"))
        img = ImageReader(io.BytesIO(png_bytes))
        iw, ih = img.getSize()            # pixeles renderizados (a 'zoom')
        pw, ph = iw / zoom, ih / zoom     # tamano logico en puntos
        c = rl_canvas.Canvas(nombre_seguro, pagesize=(pw, ph))
        c.drawImage(img, 0, 0, width=pw, height=ph)
        c.showPage()
        c.save()
        return nombre_seguro
    except Exception as e:
        print(f"Error resvg->PDF: {e}")
        traceback.print_exc()
        return None

def generar_pdf_partitura(musicxml_path, output_pdf="partitura.pdf", verovio_options=None,
                          score_m21_obj=None, cf_part_m21_obj=None, cp_part_m21_obj=None, 
                          species_str="primera", datos_anotacion_especie=None ):
    
    svg_str, err = generar_svg_de_musicxml(musicxml_path, verovio_options)
    if err: print(err)
    final_svg = svg_str 

    # Lógica de anotación
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
    
    # Generación Local Segura
    pdf_local = convertir_svg_a_pdf_local(final_svg)
    
    if pdf_local and os.path.exists(pdf_local):
        try:
            time.sleep(0.1) 
            shutil.copy2(pdf_local, output_pdf)
            return output_pdf
        except Exception as e:
            print(f"Error copiando PDF final: {e}")
            return pdf_local
    
    return None