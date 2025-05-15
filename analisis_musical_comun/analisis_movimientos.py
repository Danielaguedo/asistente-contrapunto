# analisis_musical_comun/analisis_movimientos.py (Con números de compás)
from music21 import interval, note as m21note, stream
from music21.voiceLeading import VoiceLeadingQuartet, MotionType 
import traceback

# --- ESTADO DE LAS HERRAMIENTAS DE ANÁLISIS DE MOVIMIENTO ---
VOICELEADING_QUARTET_CLASS = None
MOTION_ANALYSIS_AVAILABLE = False 

print("DEBUG (analisis_movimiento.py): Intentando configurar herramientas de análisis de movimiento...")

try:
    VOICELEADING_QUARTET_CLASS = VoiceLeadingQuartet 
    MOTION_ANALYSIS_AVAILABLE = True
    print("DEBUG (analisis_movimiento.py): ÉXITO, VoiceLeadingQuartet está disponible.")
except NameError: 
    print("ADVERTENCIA CRÍTICA (analisis_movimiento.py): VoiceLeadingQuartet no se pudo encontrar. El análisis de movimiento entre voces no funcionará.")
except Exception as e_init_vl_tools:
    print(f"ERROR INESPERADO (analisis_movimiento.py) configurando herramientas de VoiceLeading: {e_init_vl_tools}")
    traceback.print_exc()

def get_measure_info_str(nota_anterior, nota_actual):
    """
    Genera una cadena con la información del compás para dos notas.
    Ej: "Compás X a Y:", "Compás X:", o "" si no se puede determinar.
    """
    try:
        m_ant = nota_anterior.measureNumber
        m_curr = nota_actual.measureNumber
        if m_ant is not None and m_curr is not None:
            if m_ant == m_curr:
                return f"Compás {m_ant}:"
            else:
                return f"Compás {m_ant} a {m_curr}:"
        elif m_ant is not None: # Si solo la primera nota tiene info de compás
             return f"Desde Compás {m_ant}:"
        elif m_curr is not None: # Si solo la segunda nota tiene info de compás
             return f"Hacia Compás {m_curr}:"

    except AttributeError: # Si las notas no tienen .measureNumber o algo falla
        pass # Simplemente no se añade info de compás
    return "" # Devuelve cadena vacía si no se pudo determinar

def describir_movimiento_melodico_voz(lista_notas_voz, nombre_voz_para_mensaje="Voz"):
    descripciones = []
    if len(lista_notas_voz) < 2:
        return descripciones
        
    for i in range(len(lista_notas_voz) - 1):
        nota_anterior = lista_notas_voz[i]
        nota_actual = lista_notas_voz[i+1]

        # Asegurarse de que sean objetos Note con pitch
        if not all(isinstance(n, m21note.Note) and hasattr(n, 'pitch') for n in [nota_anterior, nota_actual]):
            # Podríamos añadir un mensaje de error o simplemente saltar este par
            # descripciones.append(f"   {nombre_voz_para_mensaje} - Evento {i+1} a {i+2}: Elementos no son notas válidas para análisis melódico.")
            continue

        mov_desc_text = ""
        if nota_anterior.pitch == nota_actual.pitch:
            mov_desc_text = f"Repetición de {nota_actual.nameWithOctave}"
        else:
            try:
                inter_melodico = interval.Interval(noteStart=nota_anterior, noteEnd=nota_actual)
                tipo_salto = "Grado Conjunto" if inter_melodico.isStep else "Salto"
                direccion_str = ""
                if inter_melodico.direction == interval.Direction.ASCENDING:
                    direccion_str = "Ascendente"
                elif inter_melodico.direction == interval.Direction.DESCENDING:
                    direccion_str = "Descendente"
                mov_desc_text = f"{tipo_salto} de {inter_melodico.niceName} {direccion_str} (de {nota_anterior.nameWithOctave} a {nota_actual.nameWithOctave})"
            except Exception as e_mel:
                mov_desc_text = f"No se pudo calcular movimiento melódico ({e_mel})"
        
        measure_info = get_measure_info_str(nota_anterior, nota_actual)
        descripciones.append(f"{measure_info} {nombre_voz_para_mensaje} - {mov_desc_text}") # Quitamos "Del evento..."
        
    return descripciones

def identificar_movimiento_entre_voces(cp_notes_list, cf_notes_list):
    movimientos = []
    num_eventos_comunes = min(len(cp_notes_list), len(cf_notes_list))

    if num_eventos_comunes < 2:
        return movimientos
    
    if not MOTION_ANALYSIS_AVAILABLE or VOICELEADING_QUARTET_CLASS is None:
        movimientos.append("   Entre voces: Herramienta de análisis de movimiento no disponible.") # Mantener un prefijo general
        return movimientos

    for i in range(num_eventos_comunes - 1):
        cp_ant = cp_notes_list[i]
        cp_curr = cp_notes_list[i+1]
        cf_ant = cf_notes_list[i]
        cf_curr = cf_notes_list[i+1]

        if not all(isinstance(n, m21note.Note) and hasattr(n, 'pitch') for n in [cp_ant, cp_curr, cf_ant, cf_curr]):
            measure_info = get_measure_info_str(cf_ant, cf_curr) # Usar CF para la referencia de compás aquí, o CP.
            movimientos.append(f"{measure_info} Entre voces: No se pudo determinar (elemento no es una nota válida con pitch).")
            continue
            
        try:
            vlq = VOICELEADING_QUARTET_CLASS(cf_ant, cf_curr, cp_ant, cp_curr)
            motion_type_enum_member = vlq.motionType()
            
            if motion_type_enum_member is not None:
                tipo_mov_str = motion_type_enum_member.name.capitalize()
            else:
                tipo_mov_str = "Indeterminado"

            detalle_paralelo = ""
            if tipo_mov_str == 'Parallel':
                if hasattr(cf_curr, 'pitch') and hasattr(cp_curr, 'pitch'):
                    try:
                        intervalo_par = interval.Interval(noteStart=cf_curr, noteEnd=cp_curr)
                        detalle_paralelo = f" (formando {intervalo_par.simpleName}s)"
                    except Exception: # No hacer nada si falla el cálculo del intervalo paralelo
                        pass
            
            measure_info = get_measure_info_str(cf_ant, cf_curr) # Usar el par de notas del CF (o CP) para la referencia de compás
            movimientos.append(
                f"{measure_info} Entre voces: Movimiento {tipo_mov_str}{detalle_paralelo}"
            )
        except Exception as e:
            measure_info = get_measure_info_str(cf_ant, cf_curr)
            movimientos.append(
                f"{measure_info} Entre voces: No se pudo determinar el movimiento (error interno: {e})."
            )
    return movimientos