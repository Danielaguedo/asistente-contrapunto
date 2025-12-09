# primera_especie/analisis.py (Actualizado v2 - Con soporte para SVG y Flechas)

import streamlit as st 
from primera_especie.reglas import analizar_reglas_contrapunto
from music21 import note as m21note, interval
import traceback 

class ResultadoAnalisis:
    def __init__(self, errores, evaluacion, observaciones=None, 
                 datos_intervalos_svg=None, movimientos_cf=None, movimientos_cp=None): 
        """
        Objeto para transportar todos los resultados del análisis.
        """
        self.errores = errores
        self.evaluacion = evaluacion
        self.observaciones = observaciones if observaciones is not None else []
        
        # Datos para la visualización en el PDF (números y flechas)
        self.datos_intervalos_svg = datos_intervalos_svg if datos_intervalos_svg is not None else []
        self.movimientos_cf = movimientos_cf if movimientos_cf is not None else []
        self.movimientos_cp = movimientos_cp if movimientos_cp is not None else []

def _calcular_movimientos_melodicos(notes_list):
    """
    Función auxiliar para determinar si el movimiento es ascendente o descendente
    entre notas consecutivas. Devuelve una lista de tuplas (id_prev, id_curr, tipo).
    """
    movimientos = []
    if len(notes_list) < 2:
        return movimientos
        
    for i in range(len(notes_list) - 1):
        n1 = notes_list[i]
        n2 = notes_list[i+1]
        
        if not hasattr(n1, 'id') or not hasattr(n2, 'id'):
            continue
            
        # Comparar alturas (pitch)
        p1 = n1.pitch.ps
        p2 = n2.pitch.ps
        
        tipo_mov = "lateral" # Igual altura
        if p2 > p1:
            tipo_mov = "ascendente"
        elif p2 < p1:
            tipo_mov = "descendente"
            
        movimientos.append((n1.id, n2.id, tipo_mov))
        
    return movimientos

def seccion_analizar_ejercicio(score_m21_completo, cf_part_identificada, cp_part_identificada):
    """
    Analiza la partitura de 1ra Especie.
    Calcula reglas, intervalos y movimientos melódicos.
    """
    errores_analisis = []
    observaciones_analisis = []
    evaluacion_predeterminada = "Error durante el análisis."
    
    # Listas para datos visuales
    datos_intervalos_svg = []
    movimientos_cf = []
    movimientos_cp = []

    try:
        if not cf_part_identificada or not cp_part_identificada:
            errores_analisis.append("Partes CF/CP no proporcionadas para el análisis de reglas.")
            return ResultadoAnalisis(errores_analisis, "Error en Configuración de Análisis")

        # 1. Análisis de Reglas (Lógica teórica)
        errores_reglas, observaciones_de_reglas = analizar_reglas_contrapunto(cf_part_identificada, cp_part_identificada)
        errores_analisis.extend(errores_reglas)
        observaciones_analisis.extend(observaciones_de_reglas)

        # 2. Preparación de Datos para Visualización (PDF/SVG)
        
        # Extraer listas de notas limpias
        cf_notes = [n for n in cf_part_identificada.recurse().getElementsByClass(m21note.Note)]
        cp_notes = [n for n in cp_part_identificada.recurse().getElementsByClass(m21note.Note)]
        
        # A. Calcular Intervalos Armónicos (para los números debajo de la partitura)
        min_len = min(len(cf_notes), len(cp_notes))
        for i in range(min_len):
            n_cf = cf_notes[i]
            n_cp = cp_notes[i]
            try:
                # Creamos el objeto intervalo
                inter = interval.Interval(noteStart=n_cf, noteEnd=n_cp)
                # Guardamos la tupla (NotaCP, NotaCF, ObjetoIntervalo)
                datos_intervalos_svg.append((n_cp, n_cf, inter))
            except Exception:
                continue

        # B. Calcular Movimientos Melódicos (para las flechas)
        movimientos_cf = _calcular_movimientos_melodicos(cf_notes)
        movimientos_cp = _calcular_movimientos_melodicos(cp_notes)

        # 3. Evaluación Final
        evaluacion_final = "Análisis de reglas completado."
        if errores_analisis:
            evaluacion_final = f"Se encontraron {len(errores_analisis)} errores en las reglas de contrapunto."
        else:
            evaluacion_final = "¡Ejercicio correcto según las reglas de contrapunto!"
        
        # Retornar el objeto completo con TODO lo que app.py necesita
        return ResultadoAnalisis(
            errores=errores_analisis, 
            evaluacion=evaluacion_final, 
            observaciones=observaciones_analisis,
            datos_intervalos_svg=datos_intervalos_svg, # <--- ¡ESTO FALTABA!
            movimientos_cf=movimientos_cf,             # <--- ¡ESTO TAMBIÉN!
            movimientos_cp=movimientos_cp              # <--- ¡ESTO TAMBIÉN!
        )
            
    except Exception as e:
        print(f"ERROR en seccion_analizar_ejercicio (primera_especie/analisis.py): {e}")
        traceback.print_exc() 
        errores_analisis.append(f"Error técnico en análisis de reglas: {str(e)}")
        return ResultadoAnalisis(errores_analisis, evaluacion_predeterminada)