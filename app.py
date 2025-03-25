import streamlit as st
import firebase_admin
from firebase_admin import credentials
import autenticacion
import json
import tempfile
from music21 import converter, interval
from PIL import Image
import os
from primera_especie.analisis import seccion_analizar_ejercicio
import material_didactico
import gestion_alumnos
import cookies

# ===============================================
# CONFIGURACIÓN DE LA PÁGINA
# ===============================================
st.set_page_config(page_title="Analizador de Contrapunto", layout="wide")

# ===============================================
# CONFIGURACIÓN FIREBASE (Reemplaza con tu JSON)
# ===============================================
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-creds.json")
    firebase_admin.initialize_app(cred)

# ===============================================
# DISEÑO PERSONALIZADO (CSS)
# ===============================================
def cargar_estilos():
    st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .stButton>button {
            background: #4A90E2;
            color: white;
            border-radius: 8px;
            padding: 10px 24px;
        }
        .card {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

# ===============================================
# FUNCIÓN PARA CARGAR EL ARCHIVO MUSICXML
# ===============================================
def cargar_archivo():
    archivo_subido = st.file_uploader("Sube un archivo MusicXML", type=["xml", "musicxml"], key="file_uploader_musicxml")
    if archivo_subido:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as temp_file:
                temp_file.write(archivo_subido.getvalue())
                temp_file_path = temp_file.name
            score = converter.parse(temp_file_path)
            seccion_analizar_ejercicio(score)
        except Exception as e:
            st.error(f"Ocurrió un error al procesar la partitura: {str(e)}")
def main():
    cookie_manager = cookies.inicializar_cookies()

    if cookies.obtener_cookie(cookie_manager, "autenticado") == "true":
        st.session_state["autenticado"] = True
    else:
        st.session_state["autenticado"] = False

    # ... (resto del código)
# ===============================================
# INTERFAZ PRINCIPAL (Solo para autenticados)
# ===============================================
def interfaz_principal():
    st.title(" Asistente de Contrapunto")
    st.container()
    st.header("Bienvenido, Profesor!")
    st.write("Explora nuestras herramientas avanzadas:")

    opcion = st.sidebar.selectbox("Menú", ["Analizar Ejercicio", "Material Didáctico", "Gestión de Alumnos"])

    if opcion == "Analizar Ejercicio":
        st.header(" Análisis de Contrapunto con MusicXML")
        cargar_archivo()

# ===============================================
# FLUJO PRINCIPAL DE LA APLICACIÓN
# ===============================================
def main():
    cargar_estilos()
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False
    if not st.session_state['autenticado']:
        col1, col2 = st.columns([1, 1])
        with col1:
            autenticacion.mostrar_login()
        with col2:
            autenticacion.mostrar_registro()
    else:
        interfaz_principal()
        if st.sidebar.button(" Cerrar Sesión"):
            st.session_state['autenticado'] = False
            st.experimental_rerun()

if __name__ == "__main__":
    main()

