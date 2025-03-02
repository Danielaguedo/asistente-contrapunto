import streamlit as st
from music21 import *
from reglas_contrapunto import *

def analizar_contrapunto(archivo):
    try:
        # Cargar y procesar la partitura
        print (archivo)
        score = converter.parse(archivo)
        soprano = score.parts[0].flatten().notes
        bajo = score.parts[1].flatten().notes
        
        errores = []
        sugerencias = []
        intervalo_anterior = None
        nota_s_ant, nota_b_ant = None, None

        # Aplicar reglas a cada nota
        for i in range(len(soprano)):
            s, b = soprano[i], bajo[i]
            intervalo = interval.Interval(b, s)
            
            # Regla 1: Consonancias
            if not verificar_consonancias(s, b):
                errores.append(f"Compás {s.measureNumber}: Intervalo no consonante ({intervalo.name})")
                
            # Regla 2: Quintas/Octavas paralelas
            if buscar_quintas_octavas_paralelas(intervalo_anterior, intervalo):
                errores.append(f"Compás {s.measureNumber}: Quintas/octavas paralelas")
            
            # Regla 3: Movimiento directo prohibido
            if movimiento_directo_prohibido(nota_s_ant, s, nota_b_ant, b):
                errores.append(f"Compás {s.measureNumber}: Movimiento directo prohibido")
            
            intervalo_anterior = intervalo
            nota_s_ant, nota_b_ant = s, b

        # Otras reglas
        errores += verificar_inicio_final(soprano, bajo)
        
        if notas_rep := detectar_notas_repetidas(soprano):
            errores.extend([f"Compás {soprano[i].measureNumber}: Nota repetida en soprano" for i in notas_rep])
            
        if notas_rep := detectar_notas_repetidas(bajo):
            errores.extend([f"Compás {bajo[i].measureNumber}: Nota repetida en bajo" for i in notas_rep])

        # Sugerencias estilísticas
        sugerencias = [
            "¿Buscas un efecto dramático? Las quintas paralelas se usan en el Romanticismo.",
            "Las cuartas justas pueden funcionar si se resuelven en terceras."
        ]
        
        return errores, sugerencias
    
    except Exception as e:
        return [f"Error de análisis: {str(e)}"], []

# Interfaz web
st.set_page_config(page_title="Analizador de Contrapunto")
st.title("🎼 Asistente de Primera Especie")

archivo = st.file_uploader("Sube tu partitura MusicXML", type=["xml", "musicxml"])
if archivo:
    errores, sugerencias = analizar_contrapunto(archivo)
    
    with st.expander("🔍 Resultados del Análisis", expanded=True):
        if errores:
            st.error("## Errores Técnicos")
            for error in errores:
                print (error)
                st.write(f"- {error}")
        else:
            st.success("✅ ¡Perfecto! No se encontraron errores técnicos.")
        
        if sugerencias:
            st.info("## Sugerencias Creativas")
            for sug in sugerencias:
                st.write(f"- {sug}")