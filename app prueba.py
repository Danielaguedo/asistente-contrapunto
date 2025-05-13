# app.py (Solo la función cargar_archivo_primera_especie y sus dependencias directas)

import streamlit as st
import tempfile
from music21 import converter, note as m21note, stream as m21stream
import os
import re
import datetime
import traceback

# --- Importaciones de tus módulos locales ---
try:
    from primera_especie.analisis import seccion_analizar_ejercicio, ResultadoAnalisis
    import verovio_pdf
    import exportar_pdf
except ImportError as ie:
    st.error(f"Error importando módulos necesarios para 'cargar_archivo_primera_especie': {ie}.")
    st.stop()

def sanitizar_nombre_archivo(nombre_original):
    nombre = str(nombre_original)
    nombre_sin_ext, _ = os.path.splitext(nombre)
    nombre = os.path.basename(nombre_sin_ext) 
    nombre = nombre.replace(" ", "_") 
    nombre = re.sub(r'(?u)[^-\w.]', '', nombre) 
    nombre = nombre.strip('._- ') 
    if not nombre: 
        nombre = "documento_procesado"
    return nombre

def cargar_archivo_primera_especie():
    st.markdown("<h2 class='upload-header'>Sube tu Archivo MusicXML para el Análisis (Primera Especie)</h2>", unsafe_allow_html=True)
    with st.expander("📜 Recordatorio de las Reglas de la Primera Especie", expanded=False):
        st.markdown("""
            - Una nota contra una nota.
            - Movimiento preferentemente contrario u oblicuo.
            - Evitar 5as y 8as paralelas.
            - Evitar movimiento directo a 5as y 8as (especialmente con saltos en la voz superior).
            - El contrapunto debe tener un perfil melódico fluido.
            - Inicio: P1, P5, P8 (o M/m3 si CP arriba).
            - Final: P1, P8. CP llega por grado conjunto.
            - Todas las armonías deben ser consonantes (P1, m3, M3, P5, m6, M6, P8). La P4 contra el bajo es disonante.
        """)
    with st.expander("⚠️ ¡Importante! Cómo preparar correctamente tu archivo MusicXML", expanded=False):
        st.markdown("""
            - Dos voces separadas en dos pentagramas.
            - Formato .musicxml o .xml.
            - Cada voz en una parte.
            - Exporta desde MuseScore, Sibelius, Finale, etc.
        """)

    if 'uploader_primera_key_v5' not in st.session_state:
        st.session_state.uploader_primera_key_v5 = 0

    archivo = st.file_uploader(
        "Selecciona un archivo MusicXML para Primera Especie", 
        type=["xml", "musicxml"], 
        key=f"uploader_primera_especie_widget_{st.session_state.uploader_primera_key_v5}"
    )

    if not archivo:
        st.info("Por favor, sube un archivo MusicXML para comenzar el análisis.")
        return

    musicxml_path = None
    cf_part_m21_para_anotacion = None # Renombrado para claridad
    cp_part_m21_para_anotacion = None # Renombrado para claridad
    score_m21_obj = None 

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
            tmp.write(archivo.read())
            musicxml_path = tmp.name

        with st.spinner("Procesando archivo MusicXML..."):
            score_m21_obj = converter.parse(musicxml_path)

        if len(score_m21_obj.parts) != 2:
            st.error("❌ La partitura debe contener exactamente dos voces.")
            if musicxml_path and os.path.exists(musicxml_path): os.remove(musicxml_path)
            return
        
        st.write("---") 
        st.subheader("Identificación de Voces")
        st.caption("Por favor, indica cuál voz es el Cantus Firmus (CF) y cuál el Contrapunto (CP).")

        part_display_map = {} 
        part_object_map = {} 
        for i, p in enumerate(score_m21_obj.parts):
            part_id_key = p.id if (p.id and isinstance(p.id, str)) else str(i)
            display_name = p.partName if p.partName else f"Voz {i+1}"
            part_display_map[part_id_key] = f"{display_name} (Originalmente: {p.partName if p.partName else 'Parte ' + str(i+1)})"
            part_object_map[part_id_key] = p
        
        part_keys_for_selectbox = list(part_object_map.keys())
        default_cf_idx = 1 if len(part_keys_for_selectbox) > 1 else 0
        
        session_key_cf_select = f"selected_cf_key_1ra_{archivo.name}_{archivo.size}"
        if session_key_cf_select not in st.session_state:
            st.session_state[session_key_cf_select] = part_keys_for_selectbox[default_cf_idx]

        with st.container():
            selected_cf_key = st.selectbox(
                "Voz del Cantus Firmus (CF):", 
                options=part_keys_for_selectbox,
                index=part_keys_for_selectbox.index(st.session_state[session_key_cf_select]),
                format_func=lambda x: part_display_map[x],
                key=f"cf_selector_1ra_widget_{archivo.name}_{archivo.size}"
            )
        st.session_state[session_key_cf_select] = selected_cf_key
        
        temp_cf_part = part_object_map[selected_cf_key]
        temp_cp_part = None
        for key, part_obj_iter in part_object_map.items():
            if key != selected_cf_key:
                temp_cp_part = part_obj_iter
                break
        
        if temp_cf_part and temp_cp_part:
            cf_part_m21_para_anotacion = temp_cf_part
            cp_part_m21_para_anotacion = temp_cp_part
            st.success(f"CF asignado a: **{part_display_map[selected_cf_key]}**. \nCP asignado a: **{part_display_map[next(k for k,v in part_object_map.items() if v == cp_part_m21_para_anotacion)]}**.")
        else:
            st.error("Error crítico al asignar CF y CP. Intenta recargar el archivo."); return
        
        st.write("---")

        print("DEBUG APP (1ra Esp): Asignando IDs de notas en music21...")
        note_id_counter_total = 0
        # Asignar IDs basados en el ID de la parte y un contador
        for part_iter, prefix_part_id in [(cp_part_m21_para_anotacion, cp_part_m21_para_anotacion.id if cp_part_m21_para_anotacion.id else "cp_part"), 
                                           (cf_part_m21_para_anotacion, cf_part_m21_para_anotacion.id if cf_part_m21_para_anotacion.id else "cf_part")]:
            
            if not part_iter.id or not isinstance(part_iter.id, str): # Asegurar que la parte tenga un ID
                part_iter.id = prefix_part_id # Usar el prefijo como ID de parte si no tiene
                
            notes_in_this_part = list(part_iter.recurse().getElementsByClass(m21note.Note))
            for n_obj_idx, n_obj in enumerate(notes_in_this_part):
                # Crear un ID más estructurado y potencialmente más único si Verovio lo usa
                # Usar el ID de la parte (que podría ser P1, P2, o el nombre como Violin)
                # y un índice secuencial dentro de esa parte.
                n_obj.id = f"{part_iter.id}_n{n_obj_idx}" # Ej: P1_n0, P1_n1, P2_n0, P2_n1
                note_id_counter_total+=1 # Solo para contar el total global si es necesario

        print(f"DEBUG APP (1ra Esp): IDs de notas asignados/verificados. Total: {note_id_counter_total}")
        
        # Imprimir los IDs de las primeras notas para comparar con el SVG
        print("DEBUG APP: IDs de music21 que se usarán para anotación:")
        if cp_part_m21_para_anotacion.flat.notes: 
            print(f"  Primeros CP Note IDs (music21): {[n.id for n in list(cp_part_m21_para_anotacion.flat.notes)[:5]]}")
        if cf_part_m21_para_anotacion.flat.notes: 
            print(f"  Primeros CF Note IDs (music21): {[n.id for n in list(cf_part_m21_para_anotacion.flat.notes)[:5]]}")


        with st.spinner("Realizando análisis de reglas y generando PDFs..."):
            resultados_obj = seccion_analizar_ejercicio(score_m21_obj, cf_part_m21_para_anotacion, cp_part_m21_para_anotacion) 
            errores_lista = resultados_obj.errores
            evaluacion_str = resultados_obj.evaluacion

            st.subheader("Resultados del Análisis de Reglas")
            if errores_lista:
                st.error(f"### ⚠️ Se encontraron {len(errores_lista)} errores en las reglas:")
                for e in errores_lista: st.write(f"❌ {e}")
            else:
                st.success("🎉 ¡Ejercicio correcto según las reglas de primera especie!"); st.balloons()
            
            st.divider(); st.subheader("Descargas")
            col_descarga_partitura, col_descarga_analisis = st.columns(2)
            nombre_base_saneado = sanitizar_nombre_archivo(archivo.name)
            
            with col_descarga_partitura:
                st.subheader("Partitura con Intervalos")
                pdf_nombre_partitura = f"Partitura_1raEsp_{nombre_base_saneado}_Intervalos_Horizontal.pdf"
                verovio_opts = {
                    "pageHeight": 600, "adjustPageHeight": True, "scale": 60,
                    "pageMarginTop": 40, "pageMarginBottom": 40, 
                    "pageMarginLeft": 40, "pageMarginRight": 40,
                    "breaks": "none", 
                    "landscape": 0,
                    # "svgHtml5": True # Probar esta opción para ver si ayuda con los IDs
                }
                ruta_pdf_partitura = None
                try:
                    if os.path.exists(musicxml_path):
                        ruta_pdf_partitura = verovio_pdf.generar_pdf_partitura(
                            musicxml_path, output_pdf=pdf_nombre_partitura, verovio_options=verovio_opts,
                            score_m21_obj=score_m21_obj, 
                            cf_part_m21_obj=cf_part_m21_para_anotacion, 
                            cp_part_m21_obj=cp_part_m21_para_anotacion,
                            species_str="primera", anotar_intervalos=True 
                        )
                except Exception as e_pdf_gen:
                    st.warning(f"⚠️ No se pudo generar PDF de partitura: {e_pdf_gen}"); traceback.print_exc()

                if ruta_pdf_partitura and os.path.exists(ruta_pdf_partitura):
                    with open(ruta_pdf_partitura, "rb") as f:
                        st.download_button(label="⬇️ Descargar Partitura con Intervalos (PDF)", data=f,
                                           file_name=os.path.basename(ruta_pdf_partitura), mime="application/pdf",
                                           key=f"dl_part_int_1ra_final_{archivo.name}_{archivo.size}")
                else: 
                    st.warning("⚠️ El PDF de la partitura con intervalos no pudo ser generado o no se encontró.")
            
            with col_descarga_analisis:
                st.subheader("Análisis de Reglas (Texto)")
                buffer_analisis = exportar_pdf.generar_pdf_analisis(
                    {"especie": "Primera", "errores": errores_lista, "evaluacion": evaluacion_str, "fecha": datetime.date.today().strftime("%Y-%m-%d")},
                    imagen_partitura_png=None)
                st.download_button(label="⬇️ Descargar Análisis de Reglas (PDF)", data=buffer_analisis,
                                   file_name=f"Analisis_Reglas_1raEsp_{nombre_base_saneado}.pdf", mime="application/pdf",
                                   key=f"dl_analisis_txt_1ra_final_{archivo.name}_{archivo.size}")
    except Exception as e_general:
        st.error(f"Ocurrió un error general procesando el archivo de Primera Especie: {e_general}"); traceback.print_exc()
    finally:
        if musicxml_path and os.path.exists(musicxml_path):
            try: os.remove(musicxml_path)
            except Exception as e_clean_tmp: st.warning(f"No se pudo eliminar archivo temporal: {e_clean_tmp}")

