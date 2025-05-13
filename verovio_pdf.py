# verovio_pdf.py

import os
import verovio
import cairosvg
# import streamlit as st # Quitar st de aquí para hacerlo más portable si es posible
import tempfile
import shutil
import traceback # Para imprimir detalles completos de excepciones

# --- Importación de la función de anotación ---
ANNOTATION_FUNCTION_LOADED = False # Por defecto
# Esta función se importa aquí para que generar_pdf_partitura pueda llamarla.
# Si causa un error de importación circular, habría que reestructurar.
try:
    from primera_especie.anotador_svg_intervalos import anotar_svg_con_intervalos_primera_especie
    ANNOTATION_FUNCTION_LOADED = True
    print("DEBUG (verovio_pdf): Función 'anotar_svg_con_intervalos_primera_especie' cargada exitosamente.")
except ImportError as e:
    print(f"ADVERTENCIA (verovio_pdf): No se pudo importar 'anotar_svg_con_intervalos_primera_especie' de 'primera_especie.anotador_svg_intervalos': {e}")
    # Función placeholder para evitar errores si la importación falla
    def anotar_svg_con_intervalos_primera_especie(svg_string, score_m21, cf_part_m21, cp_part_m21, species="primera"):
        print("DEBUG (verovio_pdf): Usando placeholder para 'anotar_svg_con_intervalos_primera_especie'. Devolviendo SVG original.")
        return svg_string
except Exception as e_general_import:
    print(f"ERROR INESPERADO (verovio_pdf): al intentar importar función de anotación: {e_general_import}")
    traceback.print_exc()
    def anotar_svg_con_intervalos_primera_especie(svg_string, score_m21, cf_part_m21, cp_part_m21, species="primera"):
        return svg_string # Fallback
    
def generar_svg_de_musicxml(musicxml_path, verovio_options_dict=None):
    print(f"--- DEBUG (SVG Gen): Iniciando generar_svg_de_musicxml ---")
    print(f"DEBUG (SVG Gen): musicxml_path: {musicxml_path}")
    
    if verovio_options_dict is None: 
        verovio_options_dict = {
            "pageHeight": 600, "adjustPageHeight": True, "scale": 60,
            "pageMarginTop": 40, "pageMarginBottom": 40, 
            "pageMarginLeft": 40, "pageMarginRight": 40,
            "landscape": 0, "breaks": "none" 
        }
    print(f"DEBUG (SVG Gen): Opciones de Verovio a usar: {verovio_options_dict}")

    svg_content_str = ""
    error_msg_verovio = None
    tk_instance = None
    try:
        tk_instance = verovio.toolkit()
        default_data_path = os.path.join(os.path.dirname(verovio.__file__), "data")
        if not os.path.exists(default_data_path):
             print(f"ADVERTENCIA CRÍTICA (SVG Gen): Ruta de recursos Verovio NO ENCONTRADA: {default_data_path}")
        tk_instance.setResourcePath(default_data_path)
        tk_instance.setOptions(verovio_options_dict)

        with open(musicxml_path, "r", encoding="utf-8") as f:
            musicxml_data_str = f.read()

        if not tk_instance.loadData(musicxml_data_str):
            error_msg_verovio = "Verovio no pudo cargar los datos del archivo MusicXML."
            svg_content_str = f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="100"><text x="10" y="40" fill="red">{error_msg_verovio}</text></svg>'
            print(f"DEBUG (SVG Gen): Error al cargar datos en Verovio: {error_msg_verovio}")
        else:
            svg_temp_str = tk_instance.renderToSVG(1) 
            svg_content_str = svg_temp_str.replace('overflow="inherit"', 'overflow="visible"')
            print(f"DEBUG (SVG Gen): SVG generado exitosamente.")

            # --- SECCIÓN PARA GUARDAR SVG DE DEPURACIÓN (CORREGIDA) ---
            debug_svg_path = "debug_verovio_output_for_ids.svg" 
            try:
                with open(debug_svg_path, "w", encoding="utf-8") as f_svg_debug:
                    f_svg_debug.write(svg_content_str)
                # Esta línea DEBE estar indentada para pertenecer al try
                print(f"DEBUG (SVG Gen): SVG de Verovio guardado en {os.path.abspath(debug_svg_path)}") 
            except Exception as e_save_svg:
                # Esta línea DEBE estar indentada para pertenecer al except
                print(f"DEBUG (SVG Gen): Error al guardar SVG de depuración: {e_save_svg}")
            # --- FIN SECCIÓN DE DEPURACIÓN ---

    except Exception as e_verovio_exc:
        error_msg_verovio = f"Excepción en Verovio al generar SVG: {str(e_verovio_exc)}"
        print(f"DEBUG (SVG Gen): EXCEPCIÓN en Verovio:")
        traceback.print_exc()
        svg_content_str = f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="100"><text x="10" y="40" fill="red">Error Verovio: {e_verovio_exc}</text></svg>'
    
    print(f"--- DEBUG (SVG Gen): Fin generar_svg_de_musicxml ---")
    return svg_content_str, error_msg_verovio


def convertir_svg_a_pdf_tempfile(svg_content_str, dpi=96):
    print(f"--- DEBUG (SVG->PDF): Iniciando convertir_svg_a_pdf_tempfile ---")
    temp_pdf_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="svg_to_pdf_") as tmp_pdf_file:
            temp_pdf_file_path = tmp_pdf_file.name
        cairosvg.svg2pdf(bytestring=svg_content_str.encode("utf-8"), write_to=temp_pdf_file_path, dpi=dpi)
        if not os.path.exists(temp_pdf_file_path) or os.path.getsize(temp_pdf_file_path) == 0:
            if os.path.exists(temp_pdf_file_path): os.remove(temp_pdf_file_path)
            raise IOError("CairoSVG falló en crear o llenar el PDF temporal.")
        print(f"DEBUG (SVG->PDF): PDF temporal creado en {temp_pdf_file_path}")
        return temp_pdf_file_path
    except Exception as e_cairosvg_exc:
        print(f"DEBUG (SVG->PDF): EXCEPCIÓN SVG->PDF:")
        traceback.print_exc()
        if temp_pdf_file_path and os.path.exists(temp_pdf_file_path):
            try: os.remove(temp_pdf_file_path)
            except Exception: pass
        return None

# Esta es la función que material_didactico.py está intentando importar
def generar_pdf_partitura(musicxml_path, 
                          output_pdf="partitura.pdf", 
                          verovio_options=None,
                          score_m21_obj=None, 
                          cf_part_m21_obj=None, 
                          cp_part_m21_obj=None, 
                          species_str="primera", 
                          anotar_intervalos=False):
    print(f"\n--- DEBUG (PDF Partitura Principal): Iniciando generar_pdf_partitura ---")
    print(f"DEBUG (PDF Partitura Principal): musicxml_path: {musicxml_path}, output_pdf: {output_pdf}")
    print(f"DEBUG (PDF Partitura Principal): anotar_intervalos: {anotar_intervalos}, species_str: {species_str}")

    if verovio_options is None: # Asegurar que verovio_options tenga un valor por defecto
        verovio_options = {
            "pageHeight": 600, "adjustPageHeight": True, "scale": 60,
            "pageMarginTop": 40, "pageMarginBottom": 40, 
            "pageMarginLeft": 40, "pageMarginRight": 40,
            "landscape": 0, "breaks": "none"
        }
        print(f"DEBUG (PDF Partitura Principal): Usando opciones de Verovio por defecto (generar_pdf_partitura).")
    
    svg_string_original, error_svg_gen = generar_svg_de_musicxml(musicxml_path, verovio_options)
    
    if error_svg_gen:
        print(f"DEBUG (PDF Partitura Principal): Error de Verovio al generar SVG: {error_svg_gen}")
    
    final_svg_para_conversion = svg_string_original

    if anotar_intervalos and ANNOTATION_FUNCTION_LOADED and score_m21_obj and cf_part_m21_obj and cp_part_m21_obj:
        print("DEBUG (PDF Partitura Principal): Intentando anotar SVG con intervalos...")
        try:
            if species_str == "primera":
                final_svg_para_conversion = anotar_svg_con_intervalos_primera_especie(
                    svg_string_original, score_m21_obj, cf_part_m21_obj, cp_part_m21_obj, species=species_str
                )
                print("DEBUG (PDF Partitura Principal): Anotación SVG para primera especie intentada.")
            else:
                print(f"DEBUG (PDF Partitura Principal): Anotación no implementada para '{species_str}'.")
        except Exception as e_anotacion:
            print(f"DEBUG (PDF Partitura Principal): Error durante la anotación del SVG: {e_anotacion}")
            traceback.print_exc()
    elif anotar_intervalos:
        print("DEBUG (PDF Partitura Principal): Anotación solicitada pero faltan datos/función.")

    ruta_pdf_temporal = convertir_svg_a_pdf_tempfile(final_svg_para_conversion)

    if not ruta_pdf_temporal:
        print(f"ERROR CRÍTICO (PDF Partitura Principal): No se pudo generar el PDF temporal.")
        return None

    ruta_pdf_final_disco = None
    try:
        if os.path.isabs(output_pdf): ruta_pdf_final_disco = output_pdf
        else: ruta_pdf_final_disco = os.path.abspath(os.path.join(os.getcwd(), output_pdf))
        
        directorio_destino = os.path.dirname(ruta_pdf_final_disco)
        if directorio_destino: os.makedirs(directorio_destino, exist_ok=True)

        shutil.copy2(ruta_pdf_temporal, ruta_pdf_final_disco)
        print(f"DEBUG (PDF Partitura Principal): PDF final copiado a: {ruta_pdf_final_disco}")
        return ruta_pdf_final_disco
    except Exception as e_copia_final_exc:
        print(f"DEBUG (PDF Partitura Principal): EXCEPCIÓN al copiar PDF:")
        traceback.print_exc()
        return None
    finally:
        if ruta_pdf_temporal and os.path.exists(ruta_pdf_temporal):
            try: os.remove(ruta_pdf_temporal)
            except Exception: print(f"ADVERTENCIA: No se pudo eliminar temp PDF {ruta_pdf_temporal}")
        print(f"--- DEBUG (PDF Partitura Principal): Fin generar_pdf_partitura ---")

