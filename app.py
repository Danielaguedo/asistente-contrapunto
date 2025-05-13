# app.py (Estructura Completa con UI Refactorizada y Datos para PDF Completo)

import streamlit as st
import datetime
import tempfile
import firebase_admin 
try:
    from firebase_admin import credentials
except ImportError: 
    credentials = None 
    print("ADVERTENCIA: firebase_admin.credentials no se pudo importar.")

import os
import re
import traceback

# --- Importaciones de tus módulos locales ---
try:
    import autenticacion
    import material_didactico
    import gestion_alumnos
    from material_didactico import material_didactico as md
    from primera_especie.analisis import seccion_analizar_ejercicio, ResultadoAnalisis
    from segunda_especie.analisis import analizar_segunda_especie # Asume que existe
    import verovio_pdf
    import exportar_pdf
except ImportError as ie:
    st.error(f"Error CRÍTICO importando módulos base: {ie}. La aplicación no puede continuar.")
    st.stop()

from music21 import converter, note as m21note, stream as m21stream

# ===============================================
# CONFIGURACIÓN DE LA PÁGINA
# ===============================================
st.set_page_config(page_title="Analizador de Contrapunto", layout="wide")

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
                print("DEBUG: Firebase inicializado con archivo local.")
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
                    print("DEBUG: Firebase inicializado con secretos.")
        else: FIREBASE_INITIALIZED = True
    except Exception as e: print(f"ERROR: Inicializando Firebase: {e}")

# ===============================================
# DISEÑO PERSONALIZADO (CSS)
# ===============================================
def cargar_estilos():
    st.markdown("""
    <style>
        .main { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
        .stButton>button { background: #4A90E2; color: white; border-radius: 8px; padding: 10px 24px; }
        .card { background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin: 1rem 0; }
        .upload-header h2 { color: black !important; background-color: #e6f7ff; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .prep-info-expander > div[data-testid="stExpander"] > div { background-color: #f0f8ff !important; border-radius: 5px; padding: 10px !important; border: 1px solid #e0e0e0; }
        .prep-info-expander details > summary { color: black !important; }
        .prep-info-expander details > div { color: black !important; }
        .stDownloadButton>button { background-color: #007bff; color: white; border-radius: 5px; padding: 8px 16px; border: none; transition: background-color 0.3s ease; margin-top: 5px; }
        .stDownloadButton>button:hover { background-color: #0056b3; }
    </style>
    """, unsafe_allow_html=True)

# ===============================================
# FUNCIÓN PARA SANITIZAR NOMBRES DE ARCHIVO
# ===============================================
def sanitizar_nombre_archivo(nombre_original):
    nombre = str(nombre_original)
    nombre_sin_ext, _ = os.path.splitext(nombre)
    nombre = os.path.basename(nombre_sin_ext); nombre = nombre.replace(" ", "_") 
    nombre = re.sub(r'(?u)[^-\w.]', '', nombre); nombre = nombre.strip('._- ') 
    return nombre if nombre else "documento_procesado"

# ===============================================
# TEXTOS GLOBALES
# ===============================================
ANALISIS_PRIMERA_ESPECIE_SUBTITULO = "Análisis de Contrapunto de Primera Especie"
ANALISIS_SEGUNDA_ESPECIE_SUBTITULO = "Análisis de Contrapunto de Segunda Especie"

# ===============================================
# SECCIONES DE LA APLICACIÓN
# ===============================================
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

    if 'uploader_primera_key_v9' not in st.session_state: 
        st.session_state.uploader_primera_key_v9 = 0 

    archivo = st.file_uploader(
        "Selecciona un archivo MusicXML para Primera Especie", 
        type=["xml", "musicxml"], 
        key=f"uploader_primera_especie_widget_{st.session_state.uploader_primera_key_v9}"
    )

    if not archivo:
        st.info("Por favor, sube un archivo MusicXML para comenzar el análisis.")
        return

    original_musicxml_path = None
    musicxml_to_verovio_path = None 
    cf_part_m21_para_anotacion = None
    cp_part_m21_para_anotacion = None
    score_m21_obj = None 
    
    errores_lista = []
    evaluacion_str = "Evaluación no disponible."
    observaciones_lista = []

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml", prefix="original_") as tmp:
            tmp.write(archivo.read())
            original_musicxml_path = tmp.name

        with st.spinner("Procesando archivo MusicXML..."):
            score_m21_obj = converter.parse(original_musicxml_path)

        if len(score_m21_obj.parts) != 2:
            st.error("❌ La partitura debe contener exactamente dos voces.")
            if original_musicxml_path and os.path.exists(original_musicxml_path): 
                try: os.remove(original_musicxml_path)
                except Exception as e_clean: print(f"Error limpiando temp original: {e_clean}")
            return
        
        st.write("---"); st.subheader("Identificación de Voces")
        part_display_map = {}; part_object_map = {} 
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
                "Voz del Cantus Firmus (CF):", options=part_keys_for_selectbox,
                index=part_keys_for_selectbox.index(st.session_state[session_key_cf_select]),
                format_func=lambda x: part_display_map[x],
                key=f"cf_selector_1ra_widget_{archivo.name}_{archivo.size}"
            )
        st.session_state[session_key_cf_select] = selected_cf_key
        temp_cf_part = part_object_map[selected_cf_key]; temp_cp_part = None
        for key, part_obj_iter in part_object_map.items():
            if key != selected_cf_key: temp_cp_part = part_obj_iter; break
        if temp_cf_part and temp_cp_part:
            cf_part_m21_para_anotacion = temp_cf_part
            cp_part_m21_para_anotacion = temp_cp_part
            st.success(f"CF asignado a: **{part_display_map[selected_cf_key]}**. \nCP asignado a: **{part_display_map[next(k for k,v in part_object_map.items() if v == cp_part_m21_para_anotacion)]}**.")
        else: st.error("Error crítico al asignar CF y CP."); return
        st.write("---")

        print("DEBUG APP (1ra Esp): Asignando IDs de notas en music21...")
        for part_iter in [cp_part_m21_para_anotacion, cf_part_m21_para_anotacion]:
            part_prefix = part_iter.id if (part_iter.id and isinstance(part_iter.id, str)) else ("CP" if part_iter == cp_part_m21_para_anotacion else "CF")
            part_iter.id = part_prefix 
            current_note_index_in_part = 0
            for element in part_iter.recurse().getElementsByClass(m21note.GeneralNote):
                if element.isNote: 
                    element.id = f"{part_prefix}_n{current_note_index_in_part}"
                    current_note_index_in_part += 1
        
        musicxml_to_verovio_path = original_musicxml_path 
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml", prefix="m21_with_ids_") as tmp_m21_out:
                score_m21_obj.write('musicxml', fp=tmp_m21_out.name)
                musicxml_to_verovio_path = tmp_m21_out.name
        except Exception as e_write_m21: st.error(f"Error al re-escribir MusicXML con IDs: {e_write_m21}")

        with st.spinner("Realizando análisis de reglas y generando PDFs..."):
            resultados_obj = seccion_analizar_ejercicio(score_m21_obj, cf_part_m21_para_anotacion, cp_part_m21_para_anotacion) 
            
            if resultados_obj:
                errores_lista = resultados_obj.errores
                evaluacion_str = resultados_obj.evaluacion
                observaciones_lista = getattr(resultados_obj, 'observaciones', []) 
            else: 
                st.error("El análisis no devolvió resultados válidos.")
                # Las variables errores_lista, evaluacion_str, observaciones_lista mantendrán sus valores iniciales

            st.subheader("Resultados del Análisis de Reglas de Contrapunto")
            if errores_lista:
                st.error(f"### ⚠️ Se encontraron {len(errores_lista)} errores en las reglas:")
                for e in errores_lista: 
                    st.markdown(f"❌ {e}") 
            else:
                st.success("🎉 ¡Ejercicio correcto según las reglas de contrapunto!")
            
            # --- MODIFICACIÓN: Mostrar un mensaje más conciso en la UI ---
            st.subheader("Análisis Descriptivo Adicional")
            if observaciones_lista:
                # Comprobar si hay advertencias específicas sobre herramientas no disponibles
                motion_type_warning_present = any("MotionType no disponible" in obs for obs in observaciones_lista)
                if motion_type_warning_present:
                    st.warning("⚠️ El análisis de movimiento entre voces no está completamente disponible (MotionType). Detalles en PDF.")
                
                st.info("El análisis descriptivo detallado (movimientos melódicos, etc.) está disponible en el PDF de 'Análisis Completo del Ejercicio'.")
            else:
                st.info("No hay observaciones analíticas adicionales disponibles o el análisis descriptivo falló.")
            # --- FIN MODIFICACIÓN ---
            
            st.divider(); st.subheader("Descargas")
            col_descarga_partitura, col_descarga_analisis = st.columns(2)
            nombre_base_saneado = sanitizar_nombre_archivo(archivo.name)
            
            with col_descarga_partitura:
                st.subheader("Partitura con Intervalos")
                pdf_nombre_partitura = f"Partitura_1raEsp_{nombre_base_saneado}_Intervalos_Horizontal.pdf"
                verovio_opts = {
                    "pageHeight": 600, "adjustPageHeight": True, "scale": 60,
                    "pageMarginTop": 40, "pageMarginBottom": 40, "pageMarginLeft": 40, "pageMarginRight": 40,
                    "breaks": "none", "landscape": 0, "svgHtml5": True 
                }
                ruta_pdf_partitura = None
                try:
                    if os.path.exists(musicxml_to_verovio_path): 
                        ruta_pdf_partitura = verovio_pdf.generar_pdf_partitura(
                            musicxml_to_verovio_path, output_pdf=pdf_nombre_partitura, 
                            verovio_options=verovio_opts, score_m21_obj=score_m21_obj, 
                            cf_part_m21_obj=cf_part_m21_para_anotacion, cp_part_m21_obj=cp_part_m21_para_anotacion,
                            species_str="primera", anotar_intervalos=True 
                        )
                except Exception as e_pdf_gen: 
                    st.warning(f"⚠️ No se pudo generar PDF de partitura: {e_pdf_gen}")
                    traceback.print_exc() # Mostrar traceback en consola para depuración
                if ruta_pdf_partitura and os.path.exists(ruta_pdf_partitura):
                    with open(ruta_pdf_partitura, "rb") as f:
                        st.download_button(label="⬇️ Descargar Partitura con Intervalos (PDF)", data=f,
                                           file_name=os.path.basename(ruta_pdf_partitura), mime="application/pdf",
                                           key=f"dl_part_int_1ra_final_{archivo.name}_{archivo.size}")
                else: 
                    st.warning("⚠️ El PDF de la partitura con intervalos no pudo ser generado o no se encontró.")
            
            with col_descarga_analisis:
                st.subheader("Análisis Completo del Ejercicio") # Nombre actualizado
                pdf_nombre_analisis_completo = f"Analisis_Completo_1raEsp_{nombre_base_saneado}.pdf"
                
                datos_para_pdf_analisis = {
                    "especie": "Primera", "errores": errores_lista, 
                    "evaluacion": evaluacion_str, "fecha": datetime.date.today().strftime("%Y-%m-%d"),
                    "observaciones": observaciones_lista # Pasar la lista completa
                }
                buffer_analisis = exportar_pdf.generar_pdf_analisis(datos_para_pdf_analisis, imagen_partitura_png=None)
                st.download_button(label="⬇️ Descargar Análisis Completo (PDF)", data=buffer_analisis,
                                   file_name=pdf_nombre_analisis_completo, mime="application/pdf",
                                   key=f"dl_analisis_completo_1ra_{archivo.name}_{archivo.size}")

    except Exception as e_general:
        st.error(f"Ocurrió un error general procesando el archivo de Primera Especie: {e_general}")
        traceback.print_exc() 
    finally:
        if original_musicxml_path and os.path.exists(original_musicxml_path):
            try: os.remove(original_musicxml_path)
            except Exception: pass
        if musicxml_to_verovio_path and os.path.exists(musicxml_to_verovio_path) and musicxml_to_verovio_path != original_musicxml_path:
            try: os.remove(musicxml_to_verovio_path)
            except Exception: pass

def cargar_archivo_segunda_especie():
    st.warning("La funcionalidad de análisis y anotación de Segunda Especie está en desarrollo.")
    # Aquí iría la lógica para la segunda especie

# ===============================================
# INTERFAZ PRINCIPAL (Definición)
# ===============================================
def interfaz_principal():
    # st.title("🎼 Asistente de Contrapunto") # El título ya está en main()
    
    opcion_menu = st.sidebar.selectbox(
        "Menú",
        [
            "🔎 Analizar Ejercicio (Primera Especie)",
            "🔎 Analizar Ejercicio (Segunda Especie)",
            "📚 Material Didáctico",
            "🧑‍🎓 Gestión de Alumnos",
        ], key="menu_principal_selector_v3" 
    )
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
    cargar_estilos()
    st.title("🎼 Asistente de Contrapunto") 

    if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False
    if 'uploader_primera_key_v9' not in st.session_state: st.session_state.uploader_primera_key_v9 = 0
    
    # Descomenta para desarrollo local sin Firebase
    # st.session_state['autenticado'] = True 

    if st.session_state['autenticado']:
        interfaz_principal()
        if FIREBASE_INITIALIZED and 'autenticacion' in globals() and hasattr(autenticacion, 'mostrar_login'): 
            if st.sidebar.button("Cerrar Sesión", key="logout_button_main_v4"):
                st.session_state['autenticado'] = False; st.session_state.pop('user_email', None) 
                st.session_state.uploader_primera_key_v9 += 1 
                st.experimental_rerun()
    else:
        if FIREBASE_INITIALIZED and 'autenticacion' in globals() and hasattr(autenticacion, 'mostrar_login'):
            autenticacion.mostrar_login() 
        else:
            st.sidebar.warning("Firebase no configurado o módulo de autenticación no disponible. Autenticación deshabilitada.")
            # st.info("La autenticación no está disponible.") # Comentado para reducir ruido si se accede directamente
            if st.sidebar.button("Continuar sin autenticación (Desarrollo)", key="bypass_login_dev_v4"):
                 st.session_state['autenticado'] = True; st.experimental_rerun()
            # Si no hay Firebase y no se presiona bypass, la interfaz principal no se llama,
            # lo que significa que la app se queda esperando en el título.

if __name__ == "__main__":
    main()
