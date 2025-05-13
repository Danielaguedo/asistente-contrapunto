# primera_especie/reglas.py
from music21 import interval, note as m21note, pitch
# NO DEBE HABER importación directa de music21.motion o music21.analysis.discrete o music21.analysis.motion aquí

# --- IMPORTACIONES DE MÓDULOS DE ANÁLISIS ---
# Esto asume que 'analisis_musical_comun' está en el directorio raíz del proyecto
# y que 'primera_especie' es un subdirectorio.
try:
    from analisis_musical_comun.analisis_movimientos import describir_movimiento_melodico_voz, identificar_movimiento_entre_voces
    print("DEBUG (reglas.py): Funciones de analisis_movimientos importadas correctamente.")
except ImportError as e_mov:
    print(f"ADVERTENCIA (reglas.py): No se pudo importar desde analisis_musical_comun.analisis_movimientos: {e_mov}. Usando placeholders.")
    # Definir placeholders para que el resto del archivo no falle si la importación falla
    def describir_movimiento_melodico_voz(lista_notas, nombre_voz="Voz"): return [f"Placeholder: Análisis melódico para {nombre_voz} no disponible (error import analisis_movimientos)."]
    def identificar_movimiento_entre_voces(cp_notas, cf_notas): return ["Placeholder: Análisis de movimiento entre voces no disponible (error import analisis_movimientos)."]

try:
    from .figuras_contrapuntisticas import identificar_patrones_primera_especie 
    print("DEBUG (reglas.py): Función de figuras_contrapuntisticas importada correctamente.")
except ImportError as e_fig:
    print(f"ADVERTENCIA (reglas.py): No se pudo importar desde .figuras_contrapuntisticas: {e_fig}. Usando placeholder.")
    def identificar_patrones_primera_especie(cp_part, cf_part): return ["Placeholder: Análisis de patrones no disponible (error import figuras_contrapuntisticas)."]


# --- FUNCIONES DE VALIDACIÓN DE REGLAS ---

def verificar_cruce_de_voces(cp_notes_list, cf_notes_list, cp_nombre="Contrapunto", cf_nombre="Cantus Firmus"):
    errores_cruce = []
    min_len_cruce = min(len(cp_notes_list), len(cf_notes_list))
    for i in range(min_len_cruce):
        nota_cp = cp_notes_list[i]
        nota_cf = cf_notes_list[i]
        if hasattr(nota_cp, 'pitch') and hasattr(nota_cf, 'pitch'): 
            if nota_cp.pitch.ps < nota_cf.pitch.ps:
                errores_cruce.append(
                    f"Cruce de voces en tiempo {i + 1}: "
                    f"{cp_nombre} ({nota_cp.nameWithOctave}) está por debajo del "
                    f"{cf_nombre} ({nota_cf.nameWithOctave})."
                )
    return errores_cruce

def verificar_consonancia_entre_notas(nota_cp, nota_cf):
    try:
        current_interval = interval.Interval(noteStart=nota_cf, noteEnd=nota_cp)
        if current_interval.name == 'P4': 
            return False
        return current_interval.isConsonant()
    except Exception as e:
        # print(f"Error en verificar_consonancia_entre_notas: {e}") 
        return False

def buscar_quintas_octavas_paralelas(intervalo_anterior, intervalo_actual):
    if not intervalo_anterior or not intervalo_actual: return False
    if intervalo_anterior.name == "P5" and intervalo_actual.name == "P5": return True
    if intervalo_anterior.name in ["P1", "P8"] and intervalo_actual.name in ["P1", "P8"]: return True
    return False

def movimiento_directo_prohibido(cp_ant, cp_curr, cf_ant, cf_curr):
    if not all(hasattr(n, 'pitch') for n in [cp_ant, cp_curr, cf_ant, cf_curr]): 
        return False
    intervalo_destino = interval.Interval(noteStart=cf_curr, noteEnd=cp_curr)
    if intervalo_destino.simpleName not in ["P1", "P5", "P8"]: return False
    try:
        mov_cp = interval.Interval(noteStart=cp_ant, noteEnd=cp_curr)
        mov_cf = interval.Interval(noteStart=cf_ant, noteEnd=cf_curr)
    except Exception: return False
    if mov_cp.direction.value != 0 and mov_cf.direction.value != 0 and (mov_cp.direction == mov_cf.direction):
        if not mov_cp.isStep: 
            return True
    return False

def verificar_inicio_final_primera_especie(cp_notes_list, cf_notes_list):
    errores = []
    if not cp_notes_list or not cf_notes_list:
        errores.append("Voces vacías, no se puede verificar inicio/final.")
        return errores
    try:
        intervalo_inicio = interval.Interval(noteStart=cf_notes_list[0], noteEnd=cp_notes_list[0])
        if intervalo_inicio.simpleName not in ["P1", "P5", "P8", "m3", "M3"]:
            errores.append(f"Intervalo de inicio no convencional: {intervalo_inicio.niceName}. Se espera P1, P5, P8 (o M/m3 si CP arriba).")
    except Exception as e: 
        errores.append(f"Error calculando intervalo de inicio: {e}")
    try:
        intervalo_final = interval.Interval(noteStart=cf_notes_list[-1], noteEnd=cp_notes_list[-1])
        if intervalo_final.simpleName not in ["P1", "P8"]:
            errores.append(f"Intervalo final no válido: {intervalo_final.niceName}. Se espera P1 o P8.")
        if len(cp_notes_list) > 1 and len(cf_notes_list) > 1: 
            mov_cp_a_final = interval.Interval(noteStart=cp_notes_list[-2], noteEnd=cp_notes_list[-1])
            if not mov_cp_a_final.isStep:
                errores.append(f"El Contrapunto no llega a la última nota por grado conjunto (movimiento de {mov_cp_a_final.simpleName}).")
    except Exception as e: 
        errores.append(f"Error calculando intervalo final o movimiento a la final: {e}")
    return errores

def detectar_notas_repetidas_en_voz(lista_notas_voz, nombre_voz="Voz"):
    errores_repeticion = []
    if len(lista_notas_voz) < 2: 
        return errores_repeticion
    for i in range(len(lista_notas_voz) - 1):
        if hasattr(lista_notas_voz[i], 'pitch') and hasattr(lista_notas_voz[i+1], 'pitch'):
            if lista_notas_voz[i].pitch == lista_notas_voz[i+1].pitch:
                errores_repeticion.append(f"Nota repetida en {nombre_voz} (eventos {i+1} y {i+2}: {lista_notas_voz[i].nameWithOctave}).")
    return errores_repeticion

# --- FUNCIÓN PRINCIPAL DE ANÁLISIS DE REGLAS ---
def analizar_reglas_contrapunto(cf_part, cp_part):
    errores = [] 
    observaciones_analiticas = [] 
    
    cp_notes_list = [n for n in cp_part.recurse().getElementsByClass(m21note.Note) if n.isNote]
    cf_notes_list = [n for n in cf_part.recurse().getElementsByClass(m21note.Note) if n.isNote]

    if not cp_notes_list or not cf_notes_list:
        errores.append("Una o ambas voces designadas no contienen notas musicales para analizar.")
        return errores, observaciones_analiticas

    min_len = min(len(cp_notes_list), len(cf_notes_list))
    if min_len == 0:
        errores.append("No hay suficientes notas coincidentes para el análisis de primera especie.")
        return errores, observaciones_analiticas

    # (Aquí va el resto de tu lógica de análisis de reglas, llamando a las funciones de arriba)
    # ... (Consonancias, Paralelas, Movimiento Directo, Inicio/Final, Repetidas, Cruce) ...
    for i in range(min_len):
        if not verificar_consonancia_entre_notas(cp_notes_list[i], cf_notes_list[i]):
            intervalo_error = interval.Interval(noteStart=cf_notes_list[i], noteEnd=cp_notes_list[i])
            errores.append(f"Error de consonancia en tiempo {i + 1}. Intervalo: {intervalo_error.niceName} ({cp_notes_list[i].nameWithOctave} vs {cf_notes_list[i].nameWithOctave}).")
    if min_len > 1:
        for i in range(1, min_len):
            if not (hasattr(cf_notes_list[i-1], 'pitch') and hasattr(cp_notes_list[i-1], 'pitch') and \
                    hasattr(cf_notes_list[i], 'pitch') and hasattr(cp_notes_list[i], 'pitch')):
                continue
            try:
                intervalo_anterior = interval.Interval(noteStart=cf_notes_list[i-1], noteEnd=cp_notes_list[i-1])
                intervalo_actual = interval.Interval(noteStart=cf_notes_list[i], noteEnd=cp_notes_list[i])
                if buscar_quintas_octavas_paralelas(intervalo_anterior, intervalo_actual):
                    errores.append(f"Quintas u octavas paralelas entre tiempo {i} y {i+1}.")
            except Exception as e_paralelas:
                print(f"Error al verificar paralelas en tiempo {i}-{i+1}: {e_paralelas}")
    if min_len > 1:
        for i in range(1, min_len):
            if movimiento_directo_prohibido(cp_notes_list[i-1], cp_notes_list[i], cf_notes_list[i-1], cf_notes_list[i]):
                try:
                    intervalo_destino = interval.Interval(noteStart=cf_notes_list[i], noteEnd=cp_notes_list[i])
                    errores.append(f"Movimiento directo a consonancia perfecta ({intervalo_destino.simpleName}) hacia tiempo {i+1}.")
                except Exception as e_directo:
                     print(f"Error al obtener intervalo destino en mov. directo tiempo {i+1}: {e_directo}")
    
    errores.extend(verificar_inicio_final_primera_especie(cp_notes_list, cf_notes_list))
    
    cp_part_name = cp_part.partName if cp_part.partName else "Contrapunto"
    cf_part_name = cf_part.partName if cf_part.partName else "Cantus Firmus"

    errores_cp_rep = detectar_notas_repetidas_en_voz(cp_notes_list, cp_part_name)
    if errores_cp_rep: errores.extend(errores_cp_rep)
    
    errores_cruce = verificar_cruce_de_voces(cp_notes_list, cf_notes_list, cp_part_name, cf_part_name)
    if errores_cruce: errores.extend(errores_cruce)

    # --- ANÁLISIS DESCRIPTIVO ---
    try:
        observaciones_analiticas.append(f"--- Movimiento Melódico del {cp_part_name} ---")
        observaciones_analiticas.extend(describir_movimiento_melodico_voz(cp_notes_list, cp_part_name))
        
        observaciones_analiticas.append(f"--- Movimiento Melódico del {cf_part_name} ---")
        observaciones_analiticas.extend(describir_movimiento_melodico_voz(cf_notes_list, cf_part_name))
        
        observaciones_analiticas.append("--- Movimiento Entre Voces (Armónico/Contrapuntístico) ---")
        observaciones_analiticas.extend(identificar_movimiento_entre_voces(cp_notes_list, cf_notes_list))

        observaciones_analiticas.append("--- Patrones Específicos (Primera Especie) ---")
        observaciones_analiticas.extend(identificar_patrones_primera_especie(cp_part, cf_part))
    except Exception as e_desc:
        print(f"Error durante el análisis descriptivo: {e_desc}")
        observaciones_analiticas.append("Error generando análisis descriptivo.")

    return errores, observaciones_analiticas
