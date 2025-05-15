# verovio_pdf.py (con nueva función para obtener ruta SVG)

import os
import verovio
import cairosvg
import tempfile
import shutil
import traceback

# --- Importación de la función de anotación ---
ANNOTATION_FUNCTION_LOADED = False
try:
    from primera_especie.anotador_svg_intervalos import anotar_svg_con_intervalos_primera_especie
    ANNOTATION_FUNCTION_LOADED = True
    # print("DEBUG (verovio_pdf): Función 'anotar_svg_con_intervalos_primera_especie' cargada exitosamente.") # Ya lo tienes en tu código original
except ImportError as e:
    print(f"ADVERTENCIA (verovio_pdf): No se pudo importar 'anotar_svg_con_intervalos_primera_especie': {e}")
    def anotar_svg_con_intervalos_primera_especie(svg_string, score_m21, cf_part_m21, cp_part_m21, species="primera"):
        return svg_string # Fallback
except Exception as e_general_import:
    print(f"ERROR INESPERADO (verovio_pdf): al intentar importar función de anotación: {e_general_import}")
    traceback.print_exc()
    def anotar_svg_con_intervalos_primera_especie(svg_string, score_m21, cf_part_m21, cp_part_m21, species="primera"):
        return svg_string

def generar_svg_de_musicxml(musicxml_path, verovio_options_dict=None):
    # ... (esta función permanece igual que en tu código) ...
    # Solo asegúrate de que esta función devuelve: svg_content_str, error_msg_verovio
    print(f"--- DEBUG (SVG Gen): Iniciando generar_svg_de_musicxml ---")
    print(f"DEBUG (SVG Gen): musicxml_path: {musicxml_path}")
    
    if verovio_options_dict is None: 
        verovio_options_dict = {
            "pageHeight": 600, "adjustPageHeight": True, "scale": 60,
            "pageMarginTop": 40, "pageMarginBottom": 40, 
            "pageMarginLeft": 40, "pageMarginRight": 40,
            "landscape": 0, "breaks": "none", "svgHtml5": True # Añadido svgHtml5 por si acaso
        }
    print(f"DEBUG (SVG Gen): Opciones de Verovio a usar: {verovio_options_dict}")

    svg_content_str = ""
    error_msg_verovio = None
    tk_instance = None # Definir fuera del try para que esté en el scope del finally si es necesario
    try:
        tk_instance = verovio.toolkit()
        default_data_path = os.path.join(os.path.dirname(verovio.__file__), "data")
        if not os.path.exists(default_data_path):
            print(f"ADVERTENCIA CRÍTICA (SVG Gen): Ruta de recursos Verovio NO ENCONTRADA: {default_data_path}")
        tk_instance.setResourcePath(default_data_path) # Asegúrate que esto se llama
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
            
            # Guardar SVG de depuración (opcional pero útil)
            # debug_svg_path = "debug_verovio_output_raw.svg" 
            # try:
            #     with open(debug_svg_path, "w", encoding="utf-8") as f_svg_debug:
            #         f_svg_debug.write(svg_content_str)
            #     print(f"DEBUG (SVG Gen): SVG crudo de Verovio guardado en {os.path.abspath(debug_svg_path)}") 
            # except Exception as e_save_svg:
            #     print(f"DEBUG (SVG Gen): Error al guardar SVG crudo de depuración: {e_save_svg}")

    except Exception as e_verovio_exc:
        error_msg_verovio = f"Excepción en Verovio al generar SVG: {str(e_verovio_exc)}"
        print(f"DEBUG (SVG Gen): EXCEPCIÓN en Verovio:")
        traceback.print_exc()
        svg_content_str = f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="100"><text x="10" y="40" fill="red">Error Verovio: {e_verovio_exc}</text></svg>'
    
    print(f"--- DEBUG (SVG Gen): Fin generar_svg_de_musicxml ---")
    return svg_content_str, error_msg_verovio


def convertir_svg_a_pdf_tempfile(svg_content_str, dpi=96):
    # ... (esta función permanece igual que en tu código) ...
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

# Función original para generar el PDF de la partitura (la conservamos)
def generar_pdf_partitura(musicxml_path, 
                          output_pdf="partitura.pdf", 
                          verovio_options=None,
                          score_m21_obj=None, 
                          cf_part_m21_obj=None, 
                          cp_part_m21_obj=None, 
                          species_str="primera", 
                          anotar_intervalos=False):
    # ... (esta función permanece igual que en tu código) ...
    print(f"\n--- DEBUG (PDF Partitura Principal): Iniciando generar_pdf_partitura ---")
    print(f"DEBUG (PDF Partitura Principal): musicxml_path: {musicxml_path}, output_pdf: {output_pdf}")
    print(f"DEBUG (PDF Partitura Principal): anotar_intervalos: {anotar_intervalos}, species_str: {species_str}")

    if verovio_options is None:
        verovio_options = {
            "pageHeight": 600, "adjustPageHeight": True, "scale": 60,
            "pageMarginTop": 40, "pageMarginBottom": 40, 
            "pageMarginLeft": 40, "pageMarginRight": 40,
            "landscape": 0, "breaks": "none", "svgHtml5": True
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


# --- NUEVA FUNCIÓN ---
def generar_y_guardar_svg_anotado_temporal(musicxml_path, 
                                        verovio_options=None,
                                        score_m21_obj=None, 
                                        cf_part_m21_obj=None, 
                                        cp_part_m21_obj=None, 
                                        species_str="primera", 
                                        anotar_intervalos=False,
                                        temp_svg_prefix="partitura_anotada_"):
    """
    Genera el SVG (potencialmente anotado) y lo guarda en un archivo temporal,
    devolviendo la ruta a este archivo SVG.
    """
    print(f"\n--- DEBUG (SVG Temporal): Iniciando generar_y_guardar_svg_anotado_temporal ---")
    
    if verovio_options is None:
        verovio_options = {
            "pageHeight": 600, "adjustPageHeight": True, "scale": 60,
            "pageMarginTop": 40, "pageMarginBottom": 40, 
            "pageMarginLeft": 40, "pageMarginRight": 40,
            "landscape": 0, "breaks": "none", "svgHtml5": True
        }
        print(f"DEBUG (SVG Temporal): Usando opciones de Verovio por defecto.")
    
    svg_string_original, error_svg_gen = generar_svg_de_musicxml(musicxml_path, verovio_options)
    
    if error_svg_gen:
        print(f"ERROR (SVG Temporal): Error de Verovio al generar SVG base: {error_svg_gen}")
        # Podríamos devolver None o lanzar una excepción si el SVG base falla
        return None 
    
    final_svg_string = svg_string_original

    if anotar_intervalos and ANNOTATION_FUNCTION_LOADED and score_m21_obj and cf_part_m21_obj and cp_part_m21_obj:
        print("DEBUG (SVG Temporal): Intentando anotar SVG con intervalos...")
        try:
            if species_str == "primera":
                final_svg_string = anotar_svg_con_intervalos_primera_especie(
                    svg_string_original, score_m21_obj, cf_part_m21_obj, cp_part_m21_obj, species=species_str
                )
                print("DEBUG (SVG Temporal): Anotación SVG para primera especie completada.")
            else:
                print(f"DEBUG (SVG Temporal): Anotación no implementada para '{species_str}'.")
        except Exception as e_anotacion:
            print(f"ERROR (SVG Temporal): durante la anotación del SVG: {e_anotacion}")
            traceback.print_exc()
            # Decidir si continuar con el SVG no anotado o devolver None
            # Por ahora, continuaremos con el SVG que tengamos (podría ser el original si la anotación falló)
    elif anotar_intervalos:
        print("ADVERTENCIA (SVG Temporal): Anotación solicitada pero faltan datos/función para anotar.")

    # Guardar el SVG final en un archivo temporal
    temp_svg_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".svg", prefix=temp_svg_prefix, mode="w", encoding="utf-8") as tmp_svg_file:
            tmp_svg_file.write(final_svg_string)
            temp_svg_file_path = tmp_svg_file.name
        print(f"DEBUG (SVG Temporal): SVG final guardado en archivo temporal: {temp_svg_file_path}")
        return temp_svg_file_path
    except Exception as e_save_temp_svg:
        print(f"ERROR (SVG Temporal): No se pudo guardar el SVG en un archivo temporal: {e_save_temp_svg}")
        traceback.print_exc()
        if temp_svg_file_path and os.path.exists(temp_svg_file_path): # Limpiar si se creó pero falló después
            try: os.remove(temp_svg_file_path)
            except Exception: pass
        return None
    finally:
        print(f"--- DEBUG (SVG Temporal): Fin generar_y_guardar_svg_anotado_temporal ---")