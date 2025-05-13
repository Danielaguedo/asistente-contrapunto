import streamlit as st
import os
# import sys # Ya no es necesario sys.path.append
# sys.path.append('..') # ELIMINAR ESTA LÍNEA

# Importación directa, asumiendo que verovio_pdf.py está en el mismo directorio
# o en una ruta accesible por Python (lo cual debería ser si app.py lo puede importar)
from verovio_pdf import generar_pdf_partitura 

def mostrar_seccion():
    st.subheader("📚 Material Didáctico")

    with st.expander("Contrapunto de Primera Especie"):
        st.subheader("Principios Fundamentales")
        st.markdown("""
            La primera especie de contrapunto consiste en una melodía (contrapunto) que se mueve nota contra nota con una melodía dada (cantus firmus).
            Las reglas principales incluyen:
            - Una nota contra una nota.
            - Solo consonancias permitidas (P1, m3, M3, P5, m6, M6, P8 y sus compuestos). P4 es disonante.
            - Inicio en P1, P5, P8.
            - Final en P1 o P8, llegando el contrapunto por grado conjunto.
            - Evitar quintas y octavas paralelas.
            - Evitar movimiento directo a quintas u octavas perfectas si la voz superior salta.
            - Movimiento melódico fluido.
        """)

        st.subheader("Ejemplo Ilustrativo")
        st.markdown("A continuación, se presenta un ejemplo de un ejercicio de primera especie correcto:")

        # Asegúrate de que este archivo exista en la ruta correcta relativa a donde ejecutas streamlit
        # Por ejemplo, en C:\proyectos\asistente-contrapunto\ejercicio_correcto.musicxml
        ruta_musicxml_ejemplo = "ejercicio_correcto.musicxml" 
        
        # Crear el directorio si no existe para el PDF generado
        directorio_pdf_ejemplos = "material_didactico_output/ejemplos_primera_especie"
        os.makedirs(directorio_pdf_ejemplos, exist_ok=True)
        ruta_pdf_generado = os.path.join(directorio_pdf_ejemplos, "ejemplo_1_primera_especie.pdf")

        # Generar el PDF si no existe aún o si el MusicXML es más reciente
        generar_este_pdf = True
        if os.path.exists(ruta_pdf_generado) and os.path.exists(ruta_musicxml_ejemplo):
            if os.path.getmtime(ruta_pdf_generado) > os.path.getmtime(ruta_musicxml_ejemplo):
                generar_este_pdf = False # El PDF es más reciente que el XML, no regenerar
        
        if generar_este_pdf:
            if os.path.exists(ruta_musicxml_ejemplo):
                st.info(f"Generando partitura del ejemplo en PDF: {ruta_pdf_generado}")
                # Usar las opciones por defecto de generar_pdf_partitura o pasar unas específicas
                opciones_verovio_ejemplo = {
                    "pageWidth": 1000, "scale": 50, "adjustPageHeight": True,
                    "pageMarginTop": 30, "pageMarginBottom": 30,
                    "pageMarginLeft": 30, "pageMarginRight": 30,
                    "breaks": "auto" # Para que se vea como una partitura normal
                }
                resultado_generacion = generar_pdf_partitura(
                    ruta_musicxml_ejemplo, 
                    ruta_pdf_generado,
                    verovio_options=opciones_verovio_ejemplo
                    # No pasamos objetos music21 ni anotaciones para este ejemplo simple
                )
                if not resultado_generacion:
                    st.error("No se pudo generar el PDF del ejemplo.")
            else:
                st.warning(f"Archivo MusicXML de ejemplo no encontrado en: {ruta_musicxml_ejemplo}")
                generar_este_pdf = False # No se pudo generar

        if os.path.exists(ruta_pdf_generado):
            try:
                with open(ruta_pdf_generado, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                st.download_button(
                    label="Descargar Partitura de Ejemplo (PDF)",
                    data=pdf_bytes,
                    file_name="ejemplo_primera_especie.pdf", # Nombre para la descarga del usuario
                    mime="application/pdf",
                    key="download_ejemplo_1ra_especie_md"
                )
                # st.warning("Actualmente, la visualización directa de PDF en Streamlit puede ser limitada. Se ofrece la descarga.")
                # Para mostrar el PDF (si es posible y Streamlit lo soporta bien con bytes):
                # st.pdf_viewer(pdf_bytes) # Esto no es un widget estándar de Streamlit
                # Podrías intentar mostrarlo como un iframe base64, pero es complejo y no siempre funciona.
                # La descarga es la opción más robusta.
            except FileNotFoundError:
                st.error(f"No se encontró el PDF generado en: {ruta_pdf_generado}, aunque se intentó crear.")
            except Exception as e_read_pdf:
                st.error(f"Error al leer el PDF del ejemplo: {e_read_pdf}")
        elif generar_este_pdf: # Si se intentó generar pero no existe
             st.error(f"El PDF del ejemplo no se generó correctamente y no se encontró en: {ruta_pdf_generado}")


        st.markdown("""
            En este ejemplo, podemos observar:
            - **Movimiento Contrario:** En el compás 1, mientras el cantus firmus asciende (Do a Re), el contrapunto desciende (Sol a Fa).
            - **Consonancias:** Todos los intervalos en los tiempos fuertes son consonancias perfectas (octava, quinta) o imperfectas (tercera mayor).
            - **Final:** El ejercicio termina en una octava (Do-Do).
        """)

    with st.expander("Contrapunto de Segunda Especie"):
        st.subheader("Principios Fundamentales")
        st.markdown("""
            La segunda especie de contrapunto presenta dos notas en el contrapunto por cada nota del cantus firmus...
        """)
        # ... (añade aquí el contenido para la segunda especie cuando estés listo)
