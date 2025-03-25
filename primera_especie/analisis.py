from primera_especie.reglas import analizar_reglas_contrapunto
import streamlit as st
import tempfile
from music21 import converter
from primera_especie.reglas import (
    analizar_reglas_contrapunto,
    verificar_consonancias,
    buscar_quintas_octavas_paralelas,
    movimiento_directo_prohibido,
    verificar_inicio_final,
    detectar_notas_repetidas,
)

def seccion_analizar_ejercicio():
    st.header(" Análisis de Contrapunto de Primera Especie")
    archivo_subido = st.file_uploader("Sube un archivo MusicXML", type=["xml", "musicxml"])

    if archivo_subido:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as temp_file:
                temp_file.write(archivo_subido.getvalue())
                temp_file_path = temp_file.name

            score = converter.parse(temp_file_path)
            errores = analizar_reglas_contrapunto(score)

            if errores:
                st.error("### Errores Detectados")
                for error in errores:
                    st.write(f"❌ {error}")
            else:
                st.success("🎉 ¡Ejercicio perfecto! Cumple todas las reglas de la primera especie")

        except Exception as e:
            st.error(f"Ocurrió un error al procesar la partitura: {str(e)}")