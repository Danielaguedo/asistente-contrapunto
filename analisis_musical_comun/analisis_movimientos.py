# analisis_musical_comun/analisis_movimientos.py
from music21 import interval, note as m21note, stream
import traceback # Para imprimir tracebacks completos en caso de error inesperado

# --- IMPORTACIÓN DE MotionType ---
MOTIONTYPE_CLASS = None
MOTIONTYPE_AVAILABLE = False
print("DEBUG (analisis_movimiento.py): Intentando importar MotionType...")

try:
    # Intento principal: Asumiendo que MotionType está en el archivo voiceLeading.py
    from music21.voiceLeading import MotionType
    MOTIONTYPE_CLASS = MotionType
    MOTIONTYPE_AVAILABLE = True
    print("DEBUG (analisis_movimiento.py): ÉXITO importando MotionType desde music21.voiceLeading")
except ImportError as e1:
    print(f"DEBUG (analisis_movimiento.py): Falló importación 'from music21.voiceLeading import MotionType': {e1}.")
    print("                       Esto es esperado si 'voiceLeading' es un archivo y MotionType no está directamente en su __init__ o no es un módulo.")
    print("                       Intentando importar el módulo voiceLeading y acceder a MotionType como atributo...")
    try:
        from music21 import voiceLeading as voiceLeading_module
        if hasattr(voiceLeading_module, 'MotionType'):
            MOTIONTYPE_CLASS = voiceLeading_module.MotionType
            MOTIONTYPE_AVAILABLE = True
            print("DEBUG (analisis_movimiento.py): ÉXITO obteniendo MotionType como atributo de music21.voiceLeading")
        else:
            print(f"ADVERTENCIA (analisis_movimiento.py): Módulo 'music21.voiceLeading' importado, pero NO tiene atributo 'MotionType'. Contenido: {dir(voiceLeading_module)}")
    except ImportError as e2:
        print(f"ADVERTENCIA CRÍTICA (analisis_movimiento.py): No se pudo importar ni 'MotionType' desde 'music21.voiceLeading' ni el módulo 'music21.voiceLeading' en sí: {e2}")
    except Exception as e_attr:
        print(f"ERROR (analisis_movimiento.py): Buscando MotionType como atributo de voiceLeading: {e_attr}")
        
except Exception as e_general_imp:
    print(f"ERROR INESPERADO (analisis_movimiento.py) durante los intentos de importación de MotionType: {e_general_imp}")
    traceback.print_exc()

if not MOTIONTYPE_AVAILABLE:
    print("ADVERTENCIA CRÍTICA (analisis_movimiento.py): Todos los intentos de importar MotionType fallaron.")


def describir_movimiento_melodico_voz(lista_notas_voz, nombre_voz_para_mensaje="Voz"):
    # ... (esta función no cambia) ...
    descripciones = []
    if len(lista_notas_voz) < 2:
        return descripciones
    for i in range(len(lista_notas_voz) - 1):
        nota_anterior = lista_notas_voz[i]
        nota_actual = lista_notas_voz[i+1]
        if not (hasattr(nota_anterior, 'pitch') and hasattr(nota_actual, 'pitch')):
            continue
        mov_desc = ""
        if nota_anterior.pitch == nota_actual.pitch:
            mov_desc = f"Repetición de {nota_actual.nameWithOctave}"
        else:
            try:
                inter_melodico = interval.Interval(noteStart=nota_anterior, noteEnd=nota_actual)
                tipo_salto = "Grado Conjunto" if inter_melodico.isStep else "Salto"
                direccion_str = ""
                if inter_melodico.direction == interval.Direction.ASCENDING:
                    direccion_str = "Ascendente"
                elif inter_melodico.direction == interval.Direction.DESCENDING:
                    direccion_str = "Descendente"
                mov_desc = f"{tipo_salto} de {inter_melodico.niceName} {direccion_str} (de {nota_anterior.nameWithOctave} a {nota_actual.nameWithOctave})"
            except Exception as e_mel:
                mov_desc = f"No se pudo calcular movimiento melódico ({e_mel})"
        descripciones.append(f"  {nombre_voz_para_mensaje} - Del evento {i+1} al {i+2}: {mov_desc}")
    return descripciones

def identificar_movimiento_entre_voces(cp_notes_list, cf_notes_list):
    movimientos = []
    num_eventos_comunes = min(len(cp_notes_list), len(cf_notes_list))

    if num_eventos_comunes < 2:
        return movimientos
    
    if not MOTIONTYPE_AVAILABLE or MOTIONTYPE_CLASS is None:
        movimientos.append("  Entre voces: Herramienta MotionType no disponible para análisis (fallo en importación).")
        return movimientos

    for i in range(num_eventos_comunes - 1):
        cp_ant = cp_notes_list[i]
        cp_curr = cp_notes_list[i+1]
        cf_ant = cf_notes_list[i]
        cf_curr = cf_notes_list[i+1]

        if not all(hasattr(n, 'pitch') for n in [cp_ant, cp_curr, cf_ant, cf_curr]):
            movimientos.append(f"  Entre voces - Del tiempo {i+1} al {i+2}: No se pudo determinar (elemento no es nota).")
            continue
            
        try:
            motion_obj = MOTIONTYPE_CLASS(cp_ant, cp_curr, cf_ant, cf_curr)
            tipo_mov_str = motion_obj.type.capitalize() 
            
            detalle_paralelo = ""
            if tipo_mov_str == 'Parallel':
                if hasattr(cf_curr, 'pitch') and hasattr(cp_curr, 'pitch'):
                    try:
                        intervalo_par = interval.Interval(noteStart=cf_curr, noteEnd=cp_curr)
                        detalle_paralelo = f" (formando {intervalo_par.simpleName}s)"
                    except Exception as e_int_par:
                        detalle_paralelo = f" (error al calcular intervalo paralelo: {e_int_par})"
            movimientos.append(
                f"  Entre voces - Del tiempo {i+1} al {i+2}: Movimiento {tipo_mov_str}{detalle_paralelo}"
            )
        except Exception as e:
            movimientos.append(
                f"  Entre voces - Del tiempo {i+1} al {i+2}: No se pudo determinar el movimiento (error interno con MotionType: {e})."
            )
    return movimientos
