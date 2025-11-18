# segunda_especie/analisis.py (v10 - Llamada a analizar_figuras_disonantes)

from music21 import note, chord, stream, interval

# Importación relativa correcta para reglas.py
from . import reglas

# Importación de funciones de análisis de movimiento
try:
    from analisis_musical_comun.analisis_movimientos import describir_movimiento_melodico_voz, identificar_movimiento_entre_voces
    print("DEBUG (2daEspecie analisis.py): Funciones de analisis_movimientos importadas.")
except ImportError as e_mov:
    print(f"ADVERTENCIA (2daEspecie analisis.py): No se pudo importar desde analisis_musical_comun: {e_mov}. Usando placeholders.")
    def describir_movimiento_melodico_voz(lista_notas, nombre_voz="Voz"): return [f"Placeholder: Análisis melódico para {nombre_voz} no disponible."]
    def identificar_movimiento_entre_voces(cp_notas, cf_notas): return ["Placeholder: Análisis de movimiento entre voces no disponible."]

# --- Clase de Resultado (ya incluye ids_rojos) ---
class ResultadoAnalisisSegundaEspecie:
    def __init__(self, errores, datos_intervalos_svg, observaciones_textuales, evaluacion_general, ids_notas_rojas=None):
        self.errores = errores if errores is not None else []
        self.datos_intervalos_svg = datos_intervalos_svg if datos_intervalos_svg is not None else []
        self.observaciones = observaciones_textuales if observaciones_textuales is not None else [] 
        self.evaluacion = evaluacion_general if evaluacion_general is not None else "Evaluación no generada."
        self.ids_notas_rojas = ids_notas_rojas if ids_notas_rojas is not None else []

# --- Funciones de identificación de partes (sin cambios) ---
def es_parte_de_redondas(part_stream):
    part_notes = list(part_stream.flatten().notes);
    if not part_notes: return False
    num_redondas = 0; num_otras_duraciones = 0
    for el in part_stream.flatten().notesAndRests:
        if isinstance(el, note.Note):
            if el.duration.quarterLength == 4.0: num_redondas += 1
            else: num_otras_duraciones +=1
        elif isinstance(el, chord.Chord): return False
    if num_redondas > 0 and num_otras_duraciones <= 1: return True
    return False

def es_ritmo_segunda_especie_flexible(part_stream):
    if es_parte_de_redondas(part_stream): return False
    part_notes_and_rests = list(part_stream.flatten().notesAndRests);
    if not part_notes_and_rests: return False
    num_blancas = 0; num_silencios_blanca = 0; num_redondas = 0
    for el in part_notes_and_rests:
        if isinstance(el, note.Note):
            if el.duration.quarterLength == 2.0: num_blancas += 1
            elif el.duration.quarterLength == 4.0: num_redondas +=1
        elif isinstance(el, note.Rest):
            if el.duration.quarterLength == 2.0: num_silencios_blanca +=1
            elif el.duration.quarterLength == 4.0 and len(part_notes_and_rests) == 1 : return True 
    return (num_blancas > 0 or num_silencios_blanca > 0)

def identificar_cantus_firmus_y_contrapunto(score):
    if len(score.parts) != 2: return None, None, "La partitura debe contener exactamente dos partes."
    part0, part1 = score.parts[0], score.parts[1]; cf_part, cp_part = None, None
    p0_es_cf = es_parte_de_redondas(part0); p1_es_cf = es_parte_de_redondas(part1)
    p0_es_cp_flex = es_ritmo_segunda_especie_flexible(part0); p1_es_cp_flex = es_ritmo_segunda_especie_flexible(part1)
    mensaje = ""
    if p0_es_cf and p1_es_cp_flex: cf_part, cp_part = part0, part1; mensaje = "Identificado: Parte 1->CF, Parte 2->CP."
    elif p1_es_cf and p0_es_cp_flex: cf_part, cp_part = part1, part0; mensaje = "Identificado: Parte 2->CF, Parte 1->CP."
    elif p0_es_cf and not p1_es_cf: cf_part, cp_part = part0, part1; mensaje = "Identificado: Parte 1->CF. Parte 2 asume CP."
    elif p1_es_cf and not p0_es_cf: cf_part, cp_part = part1, part0; mensaje = "Identificado: Parte 2->CF. Parte 1 asume CP."
    elif p0_es_cp_flex and not p1_es_cp_flex and not p1_es_cf : cp_part, cf_part = part0, part1; mensaje = "Identificado: Parte 1->CP. Parte 2 asume CF."
    elif p1_es_cp_flex and not p0_es_cp_flex and not p0_es_cf: cp_part, cf_part = part1, part0; mensaje = "Identificado: Parte 2->CP. Parte 1 asume CF."
    else: 
        if p0_es_cf and p1_es_cf: mensaje = "Ambigüedad: Ambas partes parecen CF."
        elif p0_es_cp_flex and p1_es_cp_flex: mensaje = "Ambigüedad: Ambas partes parecen CP 2da esp."
        else: mensaje = "No se pudo identificar CF/CP. Asignando P2->CF, P1->CP por defecto."
        cf_part, cp_part = part1, part0
    if cf_part and cp_part:
        cf_part.id = cf_part.id if cf_part.id else 'CantusFirmus_auto_id' 
        cp_part.id = cp_part.id if cp_part.id else 'Contrapunto_auto_id'
        return cf_part, cp_part, mensaje
    return None, None, mensaje


def analizar_segunda_especie(score_con_ids_en_notas, cf_part_seleccionada, cp_part_seleccionada):
    """
    Analiza un ejercicio de segunda especie.
    Devuelve un objeto ResultadoAnalisisSegundaEspecie.
    """
    errores = []
    datos_intervalos_svg = []
    observaciones_textuales = []
    ids_notas_rojas = [] 
    
    cf_part_obj = cf_part_seleccionada
    cp_part_obj = cp_part_seleccionada

    if not cf_part_obj or not cp_part_obj:
        errores.append("Error Crítico: Partes de Cantus Firmus y/o Contrapunto no proporcionadas correctamente.")
        return ResultadoAnalisisSegundaEspecie(errores, [], [], "Análisis fallido", [])

    # --- 1. Recopilación de todos los intervalos para la anotación gráfica ---
    cp_notes_all = list(cp_part_obj.flatten().notes)
    for cp_nota in cp_notes_all:
        cf_notes_simultaneas = cf_part_obj.flatten().getElementsByOffset(cp_nota.offset, mustBeginInSpan=False, classList=[note.Note])
        if cf_notes_simultaneas:
            cf_nota = cf_notes_simultaneas[0]
            intervalo_obj = interval.Interval(noteStart=cf_nota, noteEnd=cp_nota)
            datos_intervalos_svg.append((cp_nota, cf_nota, intervalo_obj))

    # --- 2. Análisis de Reglas Básicas (Paralelas, Inicio, Final) ---
    errores.extend(reglas.verificar_inicio_final_segunda_especie_modificado(cf_part_obj, cp_part_obj))
    
    cp_strong_beat_notes = [n for n in cp_notes_all if n.beat == 1.0]
    cf_strong_beat_notes_paired = []
    for cp_tf_note in cp_strong_beat_notes:
        cf_notes = cf_part_obj.flatten().getElementsByOffset(cp_tf_note.offset, mustBeginInSpan=False, classList=[note.Note])
        if cf_notes:
            cf_strong_beat_notes_paired.append(cf_notes[0])

    for i in range(len(cp_strong_beat_notes) - 1):
        if i < len(cf_strong_beat_notes_paired) -1:
            if reglas.quintas_octavas_consecutivas(cf_strong_beat_notes_paired[i], cp_strong_beat_notes[i], cf_strong_beat_notes_paired[i+1], cp_strong_beat_notes[i+1]):
                errores.append(f"Paralelismo de 5as/8as entre tiempos fuertes de compases {cp_strong_beat_notes[i].measureNumber} y {cp_strong_beat_notes[i+1].measureNumber}.")

    # --- 3. ANÁLISIS DE FIGURAS DISONANTES (NUEVA LLAMADA) ---
    try:
        errores_figuras, obs_figuras, ids_rojos_figuras = reglas.analizar_figuras_disonantes_2da_especie(cp_part_obj, cf_part_obj)
        errores.extend(errores_figuras)
        if obs_figuras:
            if any(obs.strip() and "no se detectaron" not in obs.lower() for obs in obs_figuras):
                observaciones_textuales.append("--- Análisis de Figuras Disonantes ---")
            observaciones_textuales.extend(obs_figuras)
        ids_notas_rojas.extend(ids_rojos_figuras)
    except Exception as e_figuras_call:
        print(f"ERROR al llamar a reglas.analizar_figuras_disonantes_2da_especie: {e_figuras_call}")
        errores.append(f"Error interno durante el análisis de figuras: {e_figuras_call}")

    # --- 4. Análisis Descriptivo (Movimiento) ---
    try:
        cp_part_name_display = cp_part_obj.partName or getattr(cp_part_obj, 'id', "Contrapunto")
        cf_part_name_display = cf_part_obj.partName or getattr(cf_part_obj, 'id', "Cantus Firmus")
        observaciones_textuales.append(f"--- Movimiento Melódico del {cp_part_name_display} ---")
        observaciones_textuales.extend(describir_movimiento_melodico_voz(cp_notes_all, cp_part_name_display))
        observaciones_textuales.append(f"--- Movimiento Melódico del {cf_part_name_display} ---")
        observaciones_textuales.extend(describir_movimiento_melodico_voz(list(cf_part_obj.flatten().notes), cf_part_name_display))
        if cp_strong_beat_notes and cf_strong_beat_notes_paired:
            observaciones_textuales.append(f"--- Movimiento Entre Voces ({cp_part_name_display} vs {cf_part_name_display} - Tiempos Fuertes) ---")
            observaciones_textuales.extend(identificar_movimiento_entre_voces(cp_strong_beat_notes, cf_strong_beat_notes_paired))
    except Exception as e_mov:
        observaciones_textuales.append("Error generando descripciones de movimiento.")
        
    if not errores:
        evaluacion_general = "¡Ejercicio parece cumplir las reglas de segunda especie!"
    else:
        evaluacion_general = f"Se encontraron {len(errores)} problemas/errores en el ejercicio de segunda especie."

    return ResultadoAnalisisSegundaEspecie(errores, datos_intervalos_svg, observaciones_textuales, evaluacion_general, ids_notas_rojas)
