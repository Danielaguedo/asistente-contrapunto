import streamlit as st
import tempfile
from music21 import converter, interval
import json

# ===============================================
# CONFIGURACIÓN DE LA PÁGINA
# ===============================================
st.set_page_config(page_title="Analizador de Contrapunto", layout="wide")

# ===============================================
# TÍTULO Y REGLAS
# ===============================================
st.title("🎵 Asistente de Contrapunto - Primera Especie")
st.markdown("---")

with st.expander("📚 **Reglas de la Primera Especie**", expanded=True):
    st.markdown("""
    **Normas básicas:**
    1. ✅ Solo intervalos consonantes: Unísono, 3ra, 5ta, 6ta, 8va  
    2. ❌ Prohibido: Quintas/octavas paralelas  
    3. 🚫 Movimiento directo a unísono, 5ta u 8va  
    4. 🎼 Inicio y final deben ser consonancias perfectas (P1, P5, P8)
    """)

# ===============================================
# IMPORTAR FUNCIONES DE REGLAS DE CONTRAPUNTO
# ===============================================
from reglas_contrapunto import (
    verificar_consonancias,
    buscar_quintas_octavas_paralelas,
    movimiento_directo_prohibido,
    verificar_inicio_final,
    detectar_notas_repetidas
)

# ===============================================
# FUNCIÓN DE ANÁLISIS DE REGLAS
# ===============================================
def analizar_reglas_contrapunto(score):
    """
    Aplica las reglas de la primera especie a la partitura dada.
    Retorna una lista de errores encontrados.
    """
    try:
        # Se asume que hay 2 partes: la primera es soprano y la segunda, bajo
        soprano = score.parts[0].flatten().notes
        bajo = score.parts[1].flatten().notes

        errores = []
        intervalo_anterior = None
        nota_s_ant, nota_b_ant = None, None

        for i in range(len(soprano)):
            s, b = soprano[i], bajo[i]
            inter = interval.Interval(b, s)  # Intervalo actual

            # 1. Consonancias
            if not verificar_consonancias(s, b):
                errores.append(f"Compás {s.measureNumber}: Intervalo no consonante ({inter.name})")

            # 2. Quintas/Octavas paralelas
            if buscar_quintas_octavas_paralelas(intervalo_anterior, inter):
                errores.append(f"Compás {s.measureNumber}: Quintas/octavas paralelas")

            # 3. Movimiento directo prohibido
            if movimiento_directo_prohibido(nota_s_ant, s, nota_b_ant, b):
                errores.append(f"Compás {s.measureNumber}: Movimiento directo prohibido")

            intervalo_anterior = inter
            nota_s_ant, nota_b_ant = s, b

        # 4. Verificar inicio y final
        errores += verificar_inicio_final(soprano, bajo)

        # 5. Notas repetidas
        if notas_rep := detectar_notas_repetidas(soprano):
            errores.extend([f"Compás {soprano[i].measureNumber}: Nota repetida en soprano"
                            for i in notas_rep])
        if notas_rep := detectar_notas_repetidas(bajo):
            errores.extend([f"Compás {bajo[i].measureNumber}: Nota repetida en bajo"
                            for i in notas_rep])

        return errores

    except Exception as e:
        return [f"Error de análisis: {str(e)}"]

# ===============================================
# EJEMPLOS VISUALES
# ===============================================
st.markdown("---")
st.header("🎼 Ejemplos Visuales")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Ejemplo Correcto")
    # Ajusta 'width' si deseas cambiar el tamaño de la imagen
    st.image("ejemplo_correcto_señales.png", 
             caption="Movimientos contrarios y sin errores", 
             width=600)
    st.markdown("""
    **Características:**
    - Inicio en P5
    - Final en P8
    - Movimientos oblicuos y contrarios
    """)

with col2:
    st.subheader("Ejemplo Incorrecto")
    st.image("ejemplo_incorrecto_señales.png", 
             caption="Quintas paralelas en compás 2", 
             width=600)
    st.markdown("""
    **Errores:**
    - Inicio en P6 (compás 1)
    - Octavas paralelas (compás 7 y 8)
    - Movimientos directos
    """)

# ===============================================
# ANÁLISIS DE CONTRAPUNTO (MUSICXML)
# ===============================================
st.markdown("---")
st.header("🔍 Análisis de Contrapunto con MusicXML")

archivo_subido = st.file_uploader("Sube un archivo MusicXML", type=["xml", "musicxml"])

if archivo_subido:
    try:
        # Guardamos el archivo subido en un temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as temp_file:
            temp_file.write(archivo_subido.getvalue())
            temp_file_path = temp_file.name

        # Parseamos con music21
        score = converter.parse(temp_file_path)

        # Analizamos las reglas de contrapunto
        errores = analizar_reglas_contrapunto(score)

        if errores:
            st.error("### Errores Detectados")
            for error in errores:
                st.write(f"❌ {error}")
        else:
            st.success("🎉 ¡Ejercicio perfecto! Cumple todas las reglas de la primera especie")

    except Exception as e:
        st.error(f"Ocurrió un error al procesar la partitura: {str(e)}")
