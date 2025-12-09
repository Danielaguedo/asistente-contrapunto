# segunda_especie/analisis.py (v11 - Detección de Paralelas ACTIVADA)

from music21 import stream, interval, note as m21note, tempo, meter, clef, key
from segunda_especie.reglas import (
    analizar_figuras_disonantes_2da_especie,
    verificar_inicio_final_segunda_especie_modificado,
    quintas_octavas_consecutivas, # ¡Importante!
    es_consonancia
)
import traceback

class ResultadoAnalisisSegundaEspecie:
    def __init__(self, errores, evaluacion, datos_intervalos_svg, observaciones, ids_notas_rojas=None, movimientos_cp=None):
        self.errores = errores
        self.evaluacion = evaluacion
        self.datos_intervalos_svg = datos_intervalos_svg
        self.observaciones = observaciones
        self.ids_notas_rojas = ids_notas_rojas if ids_notas_rojas is not None else []
        self.movimientos_cp = movimientos_cp if movimientos_cp is not None else []

def _calcular_movimientos_melodicos(notes_list):
    """Calcula si el movimiento es ascendente o descendente."""
    movimientos = []
    if len(notes_list) < 2: return movimientos
    for i in range(len(notes_list) - 1):
        n1 = notes_list[i]; n2 = notes_list[i+1]
        if not hasattr(n1, 'id') or not hasattr(n2, 'id'): continue
        p1 = n1.pitch.ps; p2 = n2.pitch.ps
        tipo = "lateral"
        if p2 > p1: tipo = "ascendente"
        elif p2 < p1: tipo = "descendente"
        movimientos.append((n1.id, n2.id, tipo))
    return movimientos

def identificar_cantus_firmus_y_contrapunto(score):
    parts = list(score.parts)
    if len(parts) != 2: return None, None, "Error: No hay 2 partes."
    p0_notes = list(parts[0].flatten().notes)
    p1_notes = list(parts[1].flatten().notes)
    if not p0_notes or not p1_notes: return parts[0], parts[1], "Advertencia: Partes vacías."
    avg0 = sum([n.duration.quarterLength for n in p0_notes]) / len(p0_notes)
    avg1 = sum([n.duration.quarterLength for n in p1_notes]) / len(p1_notes)
    if avg0 > avg1: return parts[0], parts[1], "Auto: Voz 1 es CF, Voz 2 es CP."
    else: return parts[1], parts[0], "Auto: Voz 2 es CF, Voz 1 es CP."

def analizar_segunda_especie(score_original, cf_part, cp_part):
    errores = []
    observaciones = []
    datos_intervalos_svg = [] 
    ids_notas_rojas = []      
    
    try:
        # 1. Reglas Inicio/Final y Figuras (Lo que ya tenías)
        errores.extend(verificar_inicio_final_segunda_especie_modificado(cf_part, cp_part))
        err_fig, obs_fig, ids_fig = analizar_figuras_disonantes_2da_especie(cp_part, cf_part)
        errores.extend(err_fig)
        observaciones.extend(obs_fig)
        ids_notas_rojas.extend(ids_fig)
        
        # 2. Preparar datos
        cp_flat = list(cp_part.flatten().notes)
        cf_flat_stream = cf_part.flatten()
        
        # Variables para rastrear el "Tiempo Fuerte Anterior" (Para detectar paralelas de compás a compás)
        last_downbeat_cp = None
        last_downbeat_cf = None
        
        # Variables para rastrear la nota INMEDIATAMENTE anterior (Para paralelas consecutivas directas)
        prev_note_cp = None
        prev_note_cf = None

        for n_cp in cp_flat:
            # Buscar nota CF simultánea
            notes_cf_sim = cf_flat_stream.getElementsByOffset(n_cp.offset, mustBeginInSpan=False, classList=[m21note.Note])
            if not notes_cf_sim: continue
            n_cf = notes_cf_sim[0]

            # Calcular intervalo para SVG
            try:
                inter = interval.Interval(noteStart=n_cf, noteEnd=n_cp)
                datos_intervalos_svg.append((n_cp, n_cf, inter))
                
                # --- ANÁLISIS DE PARALELAS (LA PARTE NUEVA) ---
                
                # A. Paralelas Inmediatas (Nota a Nota)
                if prev_note_cp and prev_note_cf:
                    if quintas_octavas_consecutivas(prev_note_cf, prev_note_cp, n_cf, n_cp):
                        errores.append(f"Error: {inter.simpleName} paralelas consecutivas en compás {n_cp.measureNumber}.")
                        ids_notas_rojas.extend([n_cp.id, prev_note_cp.id])

                # B. Paralelas de Tiempo Fuerte a Tiempo Fuerte (Regla Clave de 2da Especie)
                # Si estamos en tiempo fuerte (beat 1)
                if n_cp.beat == 1.0:
                    if last_downbeat_cp and last_downbeat_cf:
                        if quintas_octavas_consecutivas(last_downbeat_cf, last_downbeat_cp, n_cf, n_cp):
                             errores.append(f"Error Crítico: {inter.simpleName} paralelas entre tiempos fuertes (Compases {last_downbeat_cp.measureNumber}-{n_cp.measureNumber}).")
                             ids_notas_rojas.extend([n_cp.id, last_downbeat_cp.id])
                    
                    # Actualizar "último tiempo fuerte visto"
                    last_downbeat_cp = n_cp
                    last_downbeat_cf = n_cf

            except Exception as e: 
                print(f"Error calculando intervalo/reglas en nota {n_cp.id}: {e}")

            # Actualizar nota inmediata anterior
            prev_note_cp = n_cp
            prev_note_cf = n_cf

        # 3. Movimientos Melódicos
        movimientos_cp = _calcular_movimientos_melodicos(cp_flat)

        # 4. Evaluación
        if not errores:
            evaluacion = "¡Excelente! Ejercicio correcto."
        else:
            evaluacion = f"Se encontraron {len(errores)} errores."
            
        return ResultadoAnalisisSegundaEspecie(errores, evaluacion, datos_intervalos_svg, observaciones, ids_notas_rojas, movimientos_cp)

    except Exception as e:
        traceback.print_exc()
        return ResultadoAnalisisSegundaEspecie([f"Error interno: {str(e)}"], "Error crítico", [], [], [], [])