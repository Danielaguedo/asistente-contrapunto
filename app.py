# app.py (Manejo final de IDs rojos para pasar al anotador)

import streamlit as st
import datetime
import tempfile
import firebase_admin
try:
    from firebase_admin import credentials
except ImportError:
    credentials = None

import os
import re
import traceback

# --- Importaciones de tus módulos locales ---
try:
    import autenticacion
    import material_didactico
    import gestion_alumnos
    from material_didactico import material_didactico as md
    
    # Primera Especie
    from primera_especie.analisis import seccion_analizar_ejercicio, ResultadoAnalisis
    
    # Segunda Especie
    from segunda_especie.analisis import analizar_segunda_especie, ResultadoAnalisisSegundaEspecie 
    from segunda_especie.analisis import identificar_cantus_firmus_y_contrapunto as identificar_cf_cp_segunda_auto

    import verovio_pdf 
    import exportar_pdf
except ImportError as ie:
    st.error(f"Error CRÍTICO importando módulos base: {ie}. La aplicación no puede continuar.")
    st.stop()

from music21 import converter, note as m21note, stream as m21stream, interval as m21interval, pitch

# ===============================================
# CONFIGURACIÓN DE LA PÁGINA
# ===============================================
st.set_page_config(page_title="Analizador de Contrapunto", layout="wide", initial_sidebar_state="expanded")

# ===============================================
# CONFIGURACIÓN FIREBASE
# ===============================================
FIREBASE_INITIALIZED = False
if credentials:
    try:
        if not firebase_admin._apps:
            creds_path = "firebase-creds.json"
            if os.path.exists(creds_path):
                cred = credentials.Certificate(creds_path)
                firebase_admin.initialize_app(cred)
                FIREBASE_INITIALIZED = True
            elif st.secrets.get("firebase_private_key"):
                firebase_creds_dict = {
                    "type": st.secrets.get("firebase_type"), "project_id": st.secrets.get("firebase_project_id"),
                    "private_key_id": st.secrets.get("firebase_private_key_id"), "private_key": st.secrets.get("firebase_private_key", "").replace('\\n', '\n'),
                    "client_email": st.secrets.get("firebase_client_email"), "client_id": st.secrets.get("firebase_client_id"),
                    "auth_uri": st.secrets.get("firebase_auth_uri"), "token_uri": st.secrets.get("firebase_token_uri"),
                    "auth_provider_x509_cert_url": st.secrets.get("firebase_auth_provider_x509_cert_url"),
                    "client_x509_cert_url": st.secrets.get("firebase_client_x509_cert_url")
                }
                if firebase_creds_dict.get("private_key"):
                    cred = credentials.Certificate(firebase_creds_dict); firebase_admin.initialize_app(cred); FIREBASE_INITIALIZED = True
        else: FIREBASE_INITIALIZED = True
    except Exception as e: print(f"ERROR: Inicializando Firebase: {e}")

# ===============================================
# FUNCIÓN PARA SANITIZAR NOMBRES DE ARCHIVO
# ===============================================
def sanitizar_nombre_archivo(nombre_original):
    nombre = str(nombre_original); nombre_sin_ext, _ = os.path.splitext(nombre)
    nombre = os.path.basename(nombre_sin_ext); nombre = nombre.replace(" ", "_")
    nombre = re.sub(r'(?u)[^-\w.]', '', nombre); nombre = nombre.strip('._- ')
    return nombre if nombre else "documento_procesado"

# ===============================================
# TEXTOS GLOBALES
# ===============================================
ANALISIS_PRIMERA_ESPECIE_SUBTITULO = "Análisis de Contrapunto de Primera Especie"
ANALISIS_SEGUNDA_ESPECIE_SUBTITULO = "Análisis de Contrapunto de Segunda Especie"

# ===============================================
# SECCIONES DE LA APLICACIÓN: PRIMERA ESPECIE 
# ===============================================
def cargar_archivo_primera_especie():
    # ... (Sin cambios) ...
    st.subheader(ANALISIS_PRIMERA_ESPECIE_SUBTITULO)
    with st.expander("📜 Recordatorio de las Reglas de la Primera Especie", expanded=False): st.markdown("""...""")
    with st.expander("⚠️ ¡Importante! Cómo preparar correctamente tu archivo MusicXML", expanded=False): st.markdown("""...""")
    if 'uploader_primera_key_v9' not in st.session_state: st.session_state.uploader_primera_key_v9 = 0
    archivo = st.file_uploader("Selecciona un archivo MusicXML para Primera Especie", type=["xml", "musicxml"], key=f"uploader_primera_especie_widget_{st.session_state.uploader_primera_key_v9}")
    if not archivo: st.info("Por favor, sube un archivo MusicXML para comenzar el análisis."); return
    original_musicxml_path = None; musicxml_to_verovio_path = None; cf_part_m21_para_anotacion = None; cp_part_m21_para_anotacion = None
    score_m21_obj = None; errores_lista = []; evaluacion_str = "Evaluación no disponible."; observaciones_lista = []; movimientos_cf_data = []; movimientos_cp_data = []; datos_intervalos_1ra = [] 
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml", prefix="original_1ra_") as tmp: tmp.write(archivo.read()); original_musicxml_path = tmp.name
        with st.spinner("Procesando archivo MusicXML (1ra Especie)..."): score_m21_obj = converter.parse(original_musicxml_path)
        if len(score_m21_obj.parts) != 2:
            st.error("❌ La partitura debe contener exactamente dos partes (voces).")
            if original_musicxml_path and os.path.exists(original_musicxml_path):
                try: os.remove(original_musicxml_path)
                except Exception as e_remove: print(f"Advertencia: No se pudo eliminar archivo temporal {original_musicxml_path}: {e_remove}")
            return
        st.markdown("---"); st.subheader("Identificación de Voces (1ra Especie)")
        part_display_map = {}; part_object_map = {}
        for i, p in enumerate(score_m21_obj.parts):
            part_id_key = p.id if (p.id and isinstance(p.id, str) and p.id.strip() != "") else f"part_{i}"; p.id = part_id_key 
            display_name = p.partName if p.partName else f"Voz {i+1} (ID: {part_id_key})"; part_display_map[part_id_key] = display_name; part_object_map[part_id_key] = p
        part_keys_for_selectbox = list(part_object_map.keys()); default_cf_idx = 1 if len(part_keys_for_selectbox) > 1 else 0 
        session_key_cf_select = f"selected_cf_key_1ra_{archivo.name}_{archivo.size}"
        if session_key_cf_select not in st.session_state: st.session_state[session_key_cf_select] = part_keys_for_selectbox[default_cf_idx]
        selected_cf_key = st.selectbox("Voz del Cantus Firmus (CF):", options=part_keys_for_selectbox, index=part_keys_for_selectbox.index(st.session_state[session_key_cf_select]), format_func=lambda x: part_display_map[x], key=f"cf_selector_1ra_widget_{archivo.name}_{archivo.size}")
        st.session_state[session_key_cf_select] = selected_cf_key; cf_part_m21_para_anotacion = part_object_map[selected_cf_key]; cp_part_m21_para_anotacion = None
        for key, part_obj_iter in part_object_map.items():
            if key != selected_cf_key: cp_part_m21_para_anotacion = part_obj_iter; break
        if cf_part_m21_para_anotacion and cp_part_m21_para_anotacion: st.success(f"CF asignado a: **{part_display_map[cf_part_m21_para_anotacion.id]}**. \nCP asignado a: **{part_display_map[cp_part_m21_para_anotacion.id]}**.")
        else: st.error("Error crítico al asignar CF y CP."); return
        st.markdown("---")
        for part_idx, part_iter in enumerate([cf_part_m21_para_anotacion, cp_part_m21_para_anotacion]):
            part_prefix = part_iter.id; current_note_index_in_part = 0
            for element in part_iter.recurse().getElementsByClass(m21note.GeneralNote):
                if element.isNote: element.id = f"{part_prefix}_n{current_note_index_in_part}"; current_note_index_in_part += 1
        musicxml_to_verovio_path = original_musicxml_path 
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml", prefix="m21_with_ids_1ra_") as tmp_m21_out: score_m21_obj.write('musicxml', fp=tmp_m21_out.name); musicxml_to_verovio_path = tmp_m21_out.name
        except Exception as e_write_m21: st.error(f"Error al re-escribir MusicXML con IDs (1ra Especie): {e_write_m21}")
        # ... (resto de la lógica de 1ra especie sin cambios) ...
    except Exception as e_general: st.error(f"Ocurrió un error general (1ra Especie): {e_general}"); traceback.print_exc()
    finally:
        # ... (sin cambios) ...
        pass

# ===============================================
# SECCIONES DE LA APLICACIÓN: SEGUNDA ESPECIE
# ===============================================
def cargar_archivo_segunda_especie():
    st.subheader(ANALISIS_SEGUNDA_ESPECIE_SUBTITULO)
    with st.expander("📜 Recordatorio de las Reglas de la Segunda Especie", expanded=False): st.markdown("""...""") 
    with st.expander("⚠️ ¡Importante! Cómo preparar tu archivo MusicXML", expanded=False): st.markdown("""...""") 

    if 'uploader_segunda_key_v1' not in st.session_state: st.session_state.uploader_segunda_key_v1 = 0
    archivo_segunda = st.file_uploader("Selecciona un archivo MusicXML para Segunda Especie", type=["xml", "musicxml"], key=f"uploader_segunda_especie_widget_{st.session_state.uploader_segunda_key_v1}")
    if not archivo_segunda: st.info("Por favor, sube un archivo MusicXML para comenzar el análisis de segunda especie."); return

    original_musicxml_path_2da = None; musicxml_to_verovio_path_2da = None
    cf_part_2da = None; cp_part_2da = None 
    score_m21_obj_2da_original_parsed = None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml", prefix="original_2da_") as tmp: tmp.write(archivo_segunda.read()); original_musicxml_path_2da = tmp.name
        with st.spinner("Procesando archivo MusicXML (2da Especie)..."): score_m21_obj_2da_original_parsed = converter.parse(original_musicxml_path_2da)
        if len(score_m21_obj_2da_original_parsed.parts) != 2:
            st.error("❌ La partitura debe contener exactamente dos partes (voces) para el análisis de segunda especie.")
            if original_musicxml_path_2da and os.path.exists(original_musicxml_path_2da):
                try: os.remove(original_musicxml_path_2da)
                except Exception as e_remove: print(f"Advertencia: No se pudo eliminar {original_musicxml_path_2da}: {e_remove}")
            return
        
        st.markdown("---"); st.subheader("Identificación de Voces (2da Especie)")
        auto_cf_part_sugg, auto_cp_part_sugg, auto_id_mensaje = identificar_cf_cp_segunda_auto(score_m21_obj_2da_original_parsed)
        if auto_id_mensaje: st.info(f"Sugerencia: {auto_id_mensaje}")
        
        part_display_map_2da = {}; part_object_map_2da = {}
        default_cf_key_2da = None; default_cp_key_2da = None
        for i, p_part_original in enumerate(score_m21_obj_2da_original_parsed.parts):
            part_id_key = p_part_original.id if (p_part_original.id and isinstance(p_part_original.id, str) and p_part_original.id.strip()!="") else f"part2da_{i}"; p_part_original.id = part_id_key 
            display_name = p_part_original.partName if p_part_original.partName else f"Voz {i+1} (ID: {part_id_key})"; part_display_map_2da[part_id_key] = display_name; part_object_map_2da[part_id_key] = p_part_original 
            if auto_cf_part_sugg and p_part_original is auto_cf_part_sugg: default_cf_key_2da = part_id_key
            if auto_cp_part_sugg and p_part_original is auto_cp_part_sugg: default_cp_key_2da = part_id_key
        part_keys_for_selectbox_2da = list(part_object_map_2da.keys()) 
        if default_cf_key_2da is None and len(part_keys_for_selectbox_2da)>1: default_cf_key_2da = part_keys_for_selectbox_2da[1]
        elif default_cf_key_2da is None and part_keys_for_selectbox_2da: default_cf_key_2da = part_keys_for_selectbox_2da[0]
        if default_cf_key_2da:
            temp_cp_options = [k for k in part_keys_for_selectbox_2da if k != default_cf_key_2da]
            if temp_cp_options: default_cp_key_2da = temp_cp_options[0]
        elif default_cp_key_2da is None and len(part_keys_for_selectbox_2da)>1: default_cp_key_2da = part_keys_for_selectbox_2da[0]
        elif default_cp_key_2da is None and part_keys_for_selectbox_2da: default_cp_key_2da = part_keys_for_selectbox_2da[0]
        session_key_cf_select_2da = f"selected_cf_key_2da_{archivo_segunda.name}_{archivo_segunda.size}"; current_cf_idx = part_keys_for_selectbox_2da.index(default_cf_key_2da) if default_cf_key_2da in part_keys_for_selectbox_2da else 0
        if session_key_cf_select_2da not in st.session_state: st.session_state[session_key_cf_select_2da] = part_keys_for_selectbox_2da[current_cf_idx]
        selected_cf_key_2da = st.selectbox("Voz del Cantus Firmus (CF) (2da Especie):", options=part_keys_for_selectbox_2da, index=part_keys_for_selectbox_2da.index(st.session_state[session_key_cf_select_2da]), format_func=lambda x: part_display_map_2da[x], key=f"cf_selector_2da_{archivo_segunda.name}")
        st.session_state[session_key_cf_select_2da] = selected_cf_key_2da; cf_part_2da = part_object_map_2da[selected_cf_key_2da]
        available_cp_options = [k for k in part_keys_for_selectbox_2da if k != selected_cf_key_2da]; 
        if not available_cp_options: st.error("Error: No hay opciones para Contrapunto."); return
        session_key_cp_select_2da = f"selected_cp_key_2da_{archivo_segunda.name}_{archivo_segunda.size}"
        current_cp_default_key = default_cp_key_2da if default_cp_key_2da in available_cp_options else available_cp_options[0]
        if selected_cf_key_2da == current_cp_default_key and available_cp_options: current_cp_default_key = available_cp_options[0]
        elif current_cp_default_key not in available_cp_options and available_cp_options: current_cp_default_key = available_cp_options[0]
        current_cp_idx = available_cp_options.index(current_cp_default_key) if current_cp_default_key in available_cp_options else 0
        if session_key_cp_select_2da not in st.session_state or st.session_state[session_key_cp_select_2da] not in available_cp_options : st.session_state[session_key_cp_select_2da] = current_cp_default_key
        selected_cp_key_2da = st.selectbox("Voz del Contrapunto (CP) (2da Especie):", options=available_cp_options, index=available_cp_options.index(st.session_state[session_key_cp_select_2da]), format_func=lambda x: part_display_map_2da[x], key=f"cp_selector_2da_{archivo_segunda.name}")
        st.session_state[session_key_cp_select_2da] = selected_cp_key_2da; cp_part_2da = part_object_map_2da[selected_cp_key_2da]
        if cf_part_2da and cp_part_2da: st.success(f"CF (2da Esp): **{part_display_map_2da[cf_part_2da.id]}**. \nCP (2da Esp): **{part_display_map_2da[cp_part_2da.id]}**.")
        else: st.error("Error crítico al asignar CF y CP (2da Esp)."); return
        st.markdown("---")
        
        for part_iter in [cf_part_2da, cp_part_2da]: 
            part_prefix = part_iter.id 
            current_note_index_in_part = 0
            for element in part_iter.recurse().getElementsByClass(m21note.GeneralNote):
                if element.isNote: 
                    element.id = f"{part_prefix}_n{current_note_index_in_part}"
                    current_note_index_in_part += 1
        
        musicxml_to_verovio_path_2da = original_musicxml_path_2da
        score_for_verovio_2da = m21stream.Score()
        try:
            score_for_verovio_2da.append(cp_part_2da) 
            score_for_verovio_2da.append(cf_part_2da) 
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml", prefix="m21_with_ids_2da_") as tmp_m21_out:
                score_for_verovio_2da.write('musicxml', fp=tmp_m21_out.name)
                musicxml_to_verovio_path_2da = tmp_m21_out.name
        except Exception as e_write_m21: st.error(f"Error al re-escribir MusicXML con IDs (2da Especie): {e_write_m21}")
        
        with st.spinner("Realizando análisis y generando PDF (2da Especie)..."):
            resultados_2da_obj = analizar_segunda_especie(score_for_verovio_2da, cf_part_2da, cp_part_2da)
            
            # --- SECCIÓN MODIFICADA PARA MANEJAR IDS ROJOS ---
            errores_lista_2da = []
            datos_intervalos_2da = []
            observaciones_lista_2da = []
            evaluacion_str_2da = "Análisis no completado."
            ids_rojos_2da = [] # Inicializar lista

            if resultados_2da_obj:
                errores_lista_2da = resultados_2da_obj.errores
                datos_intervalos_2da = resultados_2da_obj.datos_intervalos_svg
                observaciones_lista_2da = resultados_2da_obj.observaciones 
                evaluacion_str_2da = resultados_2da_obj.evaluacion
                ids_rojos_2da = resultados_2da_obj.ids_notas_rojas # Extraer la lista de IDs rojos
            else:
                st.error("El análisis de segunda especie no devolvió un objeto de resultado válido.")
            
            st.subheader("Resultados del Análisis de Reglas (2da Especie)")
            if errores_lista_2da:
                st.markdown(f"**Se encontraron {len(errores_lista_2da)} problemas/errores:**") 
                for e_msg in errores_lista_2da: 
                    st.markdown(f"⚠️ {e_msg}")
            else:
                st.success(evaluacion_str_2da if evaluacion_str_2da else "🎉 ¡Ejercicio parece cumplir reglas de segunda especie!") 
            
            st.subheader("Análisis Descriptivo Adicional (2da Especie)")
            if observaciones_lista_2da:
                 st.info("El análisis descriptivo detallado estará disponible en el PDF de 'Análisis Completo del Ejercicio'.")
            else:
                 st.info("No hay observaciones analíticas adicionales disponibles para el informe PDF.")

            st.subheader("Interpretación de la Partitura Anotada (2da Especie)")
            st.info("La partitura anotada con intervalos está disponible para descarga. Los intervalos problemáticos o de interés especial se marcarán en rojo.")
            
            st.markdown("---"); st.subheader("Descargas (2da Especie)")
            col_descarga_partitura_2da, col_descarga_analisis_2da = st.columns(2)
            nombre_base_saneado_2da = sanitizar_nombre_archivo(archivo_segunda.name); verovio_opts_2da = {"pageHeight": 600, "adjustPageHeight": True, "scale": 60, "pageMarginTop": 40, "pageMarginBottom": 40, "pageMarginLeft": 40, "pageMarginRight": 40, "breaks": "none", "landscape": 0, "svgHtml5": True }
            with col_descarga_partitura_2da:
                pdf_nombre_partitura_2da = f"Partitura_2daEsp_{nombre_base_saneado_2da}_Anotada.pdf"; ruta_pdf_partitura_anotada_2da = None
                
                # --- DICCIONARIO MODIFICADO PARA INCLUIR IDS ROJOS ---
                datos_anot_2da = {
                    'tipo': 'segunda', 
                    'intervalos': datos_intervalos_2da,
                    'ids_rojos': ids_rojos_2da # Añadir la lista al diccionario
                }
                
                boton_partitura_2da_deshabilitado = not bool(datos_intervalos_2da)
                if not boton_partitura_2da_deshabilitado:
                    try:
                        if os.path.exists(musicxml_to_verovio_path_2da): 
                            ruta_pdf_partitura_anotada_2da = verovio_pdf.generar_pdf_partitura(
                                musicxml_path=musicxml_to_verovio_path_2da, 
                                output_pdf=pdf_nombre_partitura_2da, 
                                verovio_options=verovio_opts_2da, 
                                score_m21_obj=score_for_verovio_2da, 
                                cf_part_m21_obj=cf_part_2da, 
                                cp_part_m21_obj=cp_part_2da, 
                                species_str="segunda", 
                                datos_anotacion_especie=datos_anot_2da # Pasar el diccionario actualizado
                            )
                    except Exception as e_pdf_gen_2da: st.warning(f"⚠️ No se pudo generar PDF partitura (2da): {e_pdf_gen_2da}"); traceback.print_exc()
                    if ruta_pdf_partitura_anotada_2da and os.path.exists(ruta_pdf_partitura_anotada_2da):
                        with open(ruta_pdf_partitura_anotada_2da, "rb") as f: st.download_button(label="⬇️ Descargar Partitura Anotada (2da)", data=f, file_name=os.path.basename(ruta_pdf_partitura_anotada_2da), mime="application/pdf", key=f"dl_part_2da_{archivo_segunda.name}")
                    else: st.warning("⚠️ PDF partitura (2da) no generado.")
                else: st.info("No hay datos para anotar partitura (2da)."); st.button("⬇️ Partitura Anotada (2da)", disabled=True, key=f"dl_part_2da_dis_{archivo_segunda.name}")
            with col_descarga_analisis_2da:
                pdf_nombre_analisis_2da = f"Analisis_Completo_2daEsp_{nombre_base_saneado_2da}.pdf"; datos_para_pdf_analisis_2da = {"especie": "Segunda", "errores": errores_lista_2da, "evaluacion": evaluacion_str_2da, "fecha": datetime.date.today().strftime("%Y-%m-%d"), "observaciones": observaciones_lista_2da, "cp_part_name": cp_part_2da.partName if cp_part_2da.partName else cp_part_2da.id, "cf_part_name": cf_part_2da.partName if cf_part_2da.partName else cf_part_2da.id }; buffer_analisis_2da = None
                if errores_lista_2da or observaciones_lista_2da: 
                    try: buffer_analisis_2da = exportar_pdf.generar_pdf_analisis_estable(datos_para_pdf_analisis_2da)
                    except Exception as e_pdf_an_comp_2da: st.error(f"Error generando PDF análisis (2da): {e_pdf_an_comp_2da}"); traceback.print_exc()
                if buffer_analisis_2da: st.download_button(label="⬇️ Descargar Análisis Textual (2da)", data=buffer_analisis_2da, file_name=pdf_nombre_analisis_2da, mime="application/pdf", key=f"dl_an_txt_2da_{archivo_segunda.name}")
                else: st.info("No hay datos para informe textual (2da)."); st.button("⬇️ Análisis Textual (2da)", disabled=True, key=f"dl_an_txt_2da_dis_{archivo_segunda.name}")
    except Exception as e_general_2da: 
        st.error(f"Ocurrió un error general (2da Especie): {e_general_2da}")
        traceback.print_exc()
    finally:
        if original_musicxml_path_2da and os.path.exists(original_musicxml_path_2da):
            try: os.remove(original_musicxml_path_2da)
            except Exception as e_remove: print(f"Advertencia: No se pudo eliminar {original_musicxml_path_2da}: {e_remove}")
        if musicxml_to_verovio_path_2da and os.path.exists(musicxml_to_verovio_path_2da) and musicxml_to_verovio_path_2da != original_musicxml_path_2da and "m21_with_ids_2da_" in os.path.basename(musicxml_to_verovio_path_2da):
            try: os.remove(musicxml_to_verovio_path_2da)
            except Exception as e_remove_ids: print(f"Advertencia: No se pudo eliminar {musicxml_to_verovio_path_2da}: {e_remove_ids}")

# ===============================================
# INTERFAZ PRINCIPAL (Definición)
# ===============================================
def interfaz_principal():
    if st.session_state.get('autenticado', False) and FIREBASE_INITIALIZED and 'autenticacion' in globals() and hasattr(autenticacion, 'mostrar_login'):
        user_email = st.session_state.get('user_email', 'Usuario'); st.sidebar.caption(f"Conectado como:"); st.sidebar.markdown(f"**{user_email}**")
        if st.sidebar.button("Cerrar Sesión", key="logout_button_sidebar_no_css", help="Finalizar la sesión actual", use_container_width=True):
            st.session_state['autenticado'] = False; st.session_state.pop('user_email', None)
            if 'uploader_primera_key_v9' in st.session_state: st.session_state.uploader_primera_key_v9 += 1
            if 'uploader_segunda_key_v1' in st.session_state: st.session_state.uploader_segunda_key_v1 += 1
            st.rerun()
        st.sidebar.markdown("---")
    st.sidebar.title("Menú Principal")
    opcion_menu = st.sidebar.radio( "Selecciona una opción:", ["🔎 Analizar Ejercicio (Primera Especie)", "🔎 Analizar Ejercicio (Segunda Especie)", "📚 Material Didáctico", "🧑‍🎓 Gestión de Alumnos"], key="menu_principal_selector_no_css")
    if opcion_menu == "🔎 Analizar Ejercicio (Primera Especie)": cargar_archivo_primera_especie()
    elif opcion_menu == "🔎 Analizar Ejercicio (Segunda Especie)": cargar_archivo_segunda_especie() 
    elif opcion_menu == "📚 Material Didáctico":
        if 'md' in globals() and hasattr(md, 'mostrar_seccion'): md.mostrar_seccion()
        else: st.info("Módulo de material didáctico no disponible.")
    elif opcion_menu == "🧑‍🎓 Gestión de Alumnos":
        if 'gestion_alumnos' in globals() and hasattr(gestion_alumnos, 'mostrar_seccion'): gestion_alumnos.mostrar_seccion()
        else: st.info("Módulo de gestión de alumnos no disponible.")

# ===============================================
# FUNCIÓN PRINCIPAL (main)
# ===============================================
def main():
    st.title("🎼 Asistente Interactivo de Contrapunto")
    if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
    if 'uploader_primera_key_v9' not in st.session_state: st.session_state.uploader_primera_key_v9 = 0
    if 'uploader_segunda_key_v1' not in st.session_state: st.session_state.uploader_segunda_key_v1 = 0 
    if st.session_state['autenticado']: interfaz_principal()
    else:
        if FIREBASE_INITIALIZED and 'autenticacion' in globals() and hasattr(autenticacion, 'mostrar_login'):
            autenticacion.mostrar_login()
        else:
            st.error("El sistema de autenticación no está disponible en este momento.")
            if st.button("Acceder como Invitado (Funcionalidad Limitada)", key="guest_login_v1"):
                st.session_state['autenticado'] = True; st.session_state['user_email'] = "Invitado"; st.rerun()

if __name__ == "__main__":
    main()
