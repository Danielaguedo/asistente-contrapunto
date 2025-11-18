# segunda_especie/reglas.py (v9 - BLINDADO contra SystemLayout)

from music21 import interval, note, stream, meter

def es_consonancia(nota_cf, nota_cp):
    """Verifica si el intervalo entre dos notas es una consonancia."""
    # BLINDAJE: Si no son notas, devolvemos False inmediatamente para evitar crash
    if not isinstance(nota_cf, note.Note) or not isinstance(nota_cp, note.Note):
        return False
    
    try:
        intervalo_obj = interval.Interval(nota_cf, nota_cp)
        # La 4ta justa contra el bajo es tratada como disonancia
        if intervalo_obj.name == 'P4':
            return False 
        return intervalo_obj.isConsonant()
    except:
        return False

def es_disonancia(nota_cf, nota_cp):
    """Verifica si el intervalo entre dos notas es una disonancia."""
    # BLINDAJE: Si no son notas, asumimos que NO es disonancia para no procesarla
    if not isinstance(nota_cf, note.Note) or not isinstance(nota_cp, note.Note):
        return False 
    return not es_consonancia(nota_cf, nota_cp)

def quintas_octavas_consecutivas(cf_ant, cp_ant, cf_actual, cp_actual):
    """Verifica si hay quintas u octavas paralelas entre dos momentos."""
    notes_list = [cf_ant, cp_ant, cf_actual, cp_actual]
    # BLINDAJE: Verificación estricta de tipos
    if not all(isinstance(n, note.Note) for n in notes_list): return False
    try:
        int_ant = interval.Interval(cf_ant, cp_ant)
        int_actual = interval.Interval(cf_actual, cp_actual)
    except Exception: return False
    
    if int_ant.name == 'P5' and int_actual.name == 'P5': return True
    if (int_ant.name == 'P8' or int_ant.name == 'P1') and \
       (int_actual.name == 'P8' or int_actual.name == 'P1'): return True
    return False

def verificar_inicio_final_segunda_especie_modificado(cf_part, cp_part):
    """Verifica las reglas específicas del inicio y final del ejercicio."""
    errores = []
    
    # BLINDAJE: Filtramos explícitamente solo Notas para el CF
    cf_flat_notes = [n for n in cf_part.flatten().notes if isinstance(n, note.Note)]
    # BLINDAJE: Filtramos Notas y Silencios para el CP (ignorando layouts)
    cp_flat_elements = [n for n in cp_part.flatten().notesAndRests if isinstance(n, (note.Note, note.Rest))]
    
    if not cf_flat_notes: errores.append("Regla Inicio/Final: Cantus Firmus no contiene notas.")
    if not cp_flat_elements: errores.append("Regla Inicio/Final: Contrapunto no contiene elementos válidos.")
    
    if not cf_flat_notes or not cp_flat_elements: return errores
    
    cf_primera_nota = cf_flat_notes[0]; cp_primera_nota_armonica_efectiva = None
    idx = 0
    
    # Lógica de inicio (silencios vs notas)
    if cp_flat_elements[idx].isRest:
        if cp_flat_elements[idx].duration.quarterLength == 2.0:
            if (idx + 1) < len(cp_flat_elements) and cp_flat_elements[idx+1].isNote and cp_flat_elements[idx+1].duration.quarterLength == 2.0:
                cp_primera_nota_armonica_efectiva = cp_flat_elements[idx+1]
            else: errores.append("Regla Inicio: Silencio de blanca inicial no seguido de una blanca en el CP.")
        elif cp_flat_elements[idx].duration.quarterLength == 4.0: pass 
        else: errores.append("Regla Inicio: Inicio del CP con silencio de duración no estándar.")
    elif cp_flat_elements[idx].isNote and cp_flat_elements[idx].duration.quarterLength == 2.0:
        cp_primera_nota_armonica_efectiva = cp_flat_elements[idx]
    else: errores.append("Regla Inicio: El contrapunto no comienza de forma estándar.")
    
    if cp_primera_nota_armonica_efectiva:
        try:
            intervalo_inicio_obj = interval.Interval(cf_primera_nota, cp_primera_nota_armonica_efectiva)
            if intervalo_inicio_obj.simpleName not in ['P1', 'P5', 'P8']:
                errores.append(f"Regla Inicio: El primer intervalo armónico ({intervalo_inicio_obj.niceName}) debe ser P1, P5, u P8. Encontrado: {cf_primera_nota.nameWithOctave} con {cp_primera_nota_armonica_efectiva.nameWithOctave}.")
        except Exception as e_int_ini: errores.append(f"Regla Inicio: Error calculando intervalo inicial: {e_int_ini}")
    elif not any("Regla Inicio:" in err for err in errores) and not (cp_flat_elements[0].isRest and cp_flat_elements[0].duration.quarterLength == 4.0):
        errores.append("Regla Inicio: No se pudo determinar la primera nota armónica del CP.")
        
    cf_ultima_nota = cf_flat_notes[-1]; cp_ultima_nota = None; cp_penultima_nota_cp = None
    
    # Búsqueda inversa para el final
    for el_idx in range(len(cp_flat_elements) - 1, -1, -1):
        el = cp_flat_elements[el_idx]
        if isinstance(el, note.Note):
            if cp_ultima_nota is None: cp_ultima_nota = el
            elif cp_penultima_nota_cp is None: 
                cp_penultima_nota_cp = el
                break # Ya encontramos las dos últimas notas
                
    if not cp_ultima_nota: errores.append("Regla Final: No se encontró la última nota del contrapunto.")
    else:
        if cp_ultima_nota.duration.quarterLength != 4.0:
            errores.append(f"Regla Final (CP): La última nota del CP ({cp_ultima_nota.nameWithOctave}) debería ser una redonda, es {cp_ultima_nota.duration.type}.")
        if cp_penultima_nota_cp:
            try:
                mov_al_final_cp = interval.Interval(cp_penultima_nota_cp, cp_ultima_nota)
                if not mov_al_final_cp.isStep:
                     errores.append(f"Regla Final (CP): CP no llega a su última nota ({cp_ultima_nota.nameWithOctave}) por grado conjunto desde ({cp_penultima_nota_cp.nameWithOctave}). Mov: {mov_al_final_cp.directedName}.")
            except: pass
        try:
            final_interval_obj = interval.Interval(cf_ultima_nota, cp_ultima_nota)
            if final_interval_obj.simpleName not in ["P1", "P8"]:
                errores.append(f"Regla Final: Intervalo final ({final_interval_obj.niceName}) debe ser P1 o P8. Encontrado: {cf_ultima_nota.nameWithOctave} con {cp_ultima_nota.nameWithOctave}.")
        except Exception as e_int_fin: errores.append(f"Regla Final: Error calculando intervalo final: {e_int_fin}")
    return errores

def _analizar_figura_de_suspension(cp_nota_prep, cp_nota_sus, cp_nota_res, cf_part_obj):
    """
    Función auxiliar que analiza una figura de 3 notas.
    """
    errores = []
    observaciones = []
    ids_rojos = []

    m_sus = cp_nota_sus.getContextByClass(stream.Measure)
    numero_compas = m_sus.number if m_sus else "?"
    
    try:
        cf_score_context = cf_part_obj.getContextByClass('Score')
        # BLINDAJE: Filtro estricto classList=[note.Note] ya estaba, pero nos aseguramos
        cf_notes_at_prep = cf_part_obj.flatten().getElementsByOffset(cp_nota_prep.getOffsetInHierarchy(cf_score_context), mustBeginInSpan=False, classList=[note.Note])
        cf_notes_at_sus_res = cf_part_obj.flatten().getElementsByOffset(cp_nota_sus.getOffsetInHierarchy(cf_score_context), mustBeginInSpan=False, classList=[note.Note])

        if not cf_notes_at_prep or not cf_notes_at_sus_res: return [], [], []
        
        cf_nota_prep = cf_notes_at_prep[0]
        cf_nota_sus_res = cf_notes_at_sus_res[0]

        intervalo_prep = interval.Interval(noteStart=cf_nota_prep, noteEnd=cp_nota_prep)
        intervalo_sus = interval.Interval(noteStart=cf_nota_sus_res, noteEnd=cp_nota_sus)
        intervalo_res = interval.Interval(noteStart=cf_nota_sus_res, noteEnd=cp_nota_res)
        movimiento_resolucion = interval.Interval(noteStart=cp_nota_sus, noteEnd=cp_nota_res)
        
        # 1. ANALIZAR PREPARACIÓN
        if es_disonancia(cf_nota_prep, cp_nota_prep):
            msg = f"Compás {int(numero_compas)-1}: Suspensión mal preparada. El intervalo de preparación '{intervalo_prep.niceName}' es disonante."
            errores.append(msg)
            ids_rojos.extend([cp_nota_prep.id, cp_nota_sus.id])
            return errores, observaciones, ids_rojos

        # 2. ANALIZAR DISONANCIA DE SUSPENSIÓN
        if intervalo_sus.simpleName not in ['m2', 'M2', 'P4', 'm7', 'M7', 'm9', 'M9']:
            msg = f"Compás {numero_compas}: La nota {cp_nota_sus.nameWithOctave} forma un intervalo de '{intervalo_sus.niceName}', que no es una disonancia de suspensión/retardo típica (2, 4, 7, 9)."
            observaciones.append(msg)
            return errores, observaciones, ids_rojos

        # 3. ANALIZAR RESOLUCIÓN
        es_resolucion_correcta = False
        if es_consonancia(cf_nota_sus_res, cp_nota_res) and movimiento_resolucion.isStep and movimiento_resolucion.direction < 0:
            es_resolucion_correcta = True
            msg = f"Compás {numero_compas}: Suspensión {intervalo_sus.simpleName}-{intervalo_res.simpleName} resuelta correctamente."
            observaciones.append(msg)
        
        if not es_resolucion_correcta:
            if es_consonancia(cf_nota_sus_res, cp_nota_res) and movimiento_resolucion.isStep and movimiento_resolucion.direction > 0:
                msg = f"Error en Compás {numero_compas}: La figura {intervalo_sus.simpleName}-{intervalo_res.simpleName} es un 'Retardo' (resolución ascendente). En el contrapunto estricto de especies, la resolución de una suspensión debe ser descendente."
                errores.append(msg)
            elif es_disonancia(cf_nota_sus_res, cp_nota_res):
                msg = f"Error en Compás {numero_compas}: La suspensión {intervalo_sus.simpleName} resuelve a una disonancia ({intervalo_res.niceName})."
                errores.append(msg)
            elif not movimiento_resolucion.isStep:
                msg = f"Error en Compás {numero_compas}: La suspensión {intervalo_sus.simpleName} no resuelve por grado conjunto (resolvió con un salto de {movimiento_resolucion.niceName})."
                errores.append(msg)
            else:
                msg = f"Error en Compás {numero_compas}: La suspensión {intervalo_sus.simpleName}-{intervalo_res.simpleName} tiene una resolución irregular no clasificada."
                errores.append(msg)
            
            ids_rojos.extend([cp_nota_sus.id, cp_nota_res.id])

    except Exception as e:
        errores.append(f"Error interno analizando figura en compás {numero_compas}: {e}")
        
    return errores, observaciones, ids_rojos


def analizar_figuras_disonantes_2da_especie(cp_part_obj, cf_part_obj):
    """
    Función principal para analizar todas las figuras disonantes de la 2da especie.
    """
    todos_errores = []
    todas_observaciones = []
    todos_ids_rojos = []
    
    # BLINDAJE: Aquí estaba el error crítico. 
    # Filtramos para asegurar que SOLO procesamos notas reales y no SystemLayouts.
    cp_notes_flat = [n for n in cp_part_obj.flatten().notes if isinstance(n, note.Note)]
    
    notas_ya_analizadas = set() 

    # Iteramos
    for i in range(1, len(cp_notes_flat)):
        
        cp_nota_actual = cp_notes_flat[i]
        
        if cp_nota_actual.id in notas_ya_analizadas:
            continue

        # --- LÓGICA PRINCIPAL: ¿ES UNA DISONANCIA EN TIEMPO FUERTE? ---
        # Como ya filtramos que es nota, acceder a .beat es seguro (o casi seguro)
        try:
            beat_actual = cp_nota_actual.beat
        except:
            continue # Si la nota no tiene beat asignado por alguna razón extraña, la saltamos

        if beat_actual == 1.0:
            # Filtramos también las notas del Cantus Firmus
            cf_notes_simultaneas = cf_part_obj.flatten().getElementsByOffset(cp_nota_actual.offset, mustBeginInSpan=False, classList=[note.Note])
            
            if not cf_notes_simultaneas: continue
            cf_nota_simultanea = cf_notes_simultaneas[0]

            if es_disonancia(cf_nota_simultanea, cp_nota_actual):
                
                if i > 0 and (i + 1) < len(cp_notes_flat):
                    cp_nota_prep = cp_notes_flat[i-1]
                    cp_nota_res = cp_notes_flat[i+1]
                    
                    # Verificar ligaduras de manera segura
                    tiene_ligadura = (cp_nota_prep.tie and cp_nota_prep.tie.type == 'start')
                    
                    if not tiene_ligadura:
                        m_num = cp_nota_actual.getContextByClass(stream.Measure).number if cp_nota_actual.getContextByClass(stream.Measure) else "?"
                        todas_observaciones.append(f"Compás {m_num}: Disonancia de tiempo fuerte ('{interval.Interval(cf_nota_simultanea, cp_nota_actual).niceName}') sin ligadura de preparación (suspensión por acento).")

                    errores_figura, obs_figura, ids_rojos_figura = _analizar_figura_de_suspension(
                        cp_nota_prep, cp_nota_actual, cp_nota_res, cf_part_obj
                    )
                    
                    todos_errores.extend(errores_figura)
                    todas_observaciones.extend(obs_figura)
                    todos_ids_rojos.extend(ids_rojos_figura)
                    
                    notas_ya_analizadas.add(cp_nota_prep.id)
                    notas_ya_analizadas.add(cp_nota_actual.id)
                    notas_ya_analizadas.add(cp_nota_res.id)

    if not todas_observaciones and not todos_errores:
        todas_observaciones.append("Análisis de Figuras Disonantes: No se detectaron figuras de suspensión o retardos.")

    return todos_errores, todas_observaciones, todos_ids_rojos