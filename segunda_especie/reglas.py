from music21 import interval, note

def es_consonancia(nota_cf, nota_cp):
    """
    Verifica si el intervalo entre dos notas es una consonancia.
    Consonancias perfectas: P1, P8, P5.
    Consonancias imperfectas: M3, m3, M6, m6.
    P4 es tratada como disonante armónicamente en contrapunto estricto a dos voces.
    """
    if not isinstance(nota_cf, note.Note) or not isinstance(nota_cp, note.Note):
        return False # No se puede calcular intervalo si no son notas
    
    intervalo_obj = interval.Interval(nota_cf, nota_cp)
    semitones = intervalo_obj.semitones % 12

    # Consonancias (P1, m3, M3, P5, m6, M6). P8 también es 0 semitonos módulo 12.
    if semitones in [0, 3, 4, 7, 8, 9]:
        # Asegurar que el P4 (5 semitonos) no se cuele si alguna vez se considera.
        if intervalo_obj.name == 'P4': # Tratar P4 como disonancia armónica aquí
             return False
        return True
    return False

def es_disonancia(nota_cf, nota_cp):
    """Verifica si el intervalo entre dos notas es una disonancia."""
    return not es_consonancia(nota_cf, nota_cp)

def quintas_octavas_consecutivas(cf_ant, cp_ant, cf_actual, cp_actual):
    """
    Verifica si hay quintas u octavas perfectas consecutivas entre dos pares de notas.
    """
    notes_list = [cf_ant, cp_ant, cf_actual, cp_actual]
    if not all(isinstance(n, note.Note) for n in notes_list):
        return False

    try:
        int_ant = interval.Interval(cf_ant, cp_ant)
        int_actual = interval.Interval(cf_actual, cp_actual)
    except Exception:
        return False # Error al crear el intervalo

    # Chequear Quintas Perfectas consecutivas
    if int_ant.name == 'P5' and int_actual.name == 'P5':
        return True
    # Chequear Octavas Perfectas (o Unísonos) consecutivas
    if (int_ant.name == 'P8' or int_ant.name == 'P1') and \
       (int_actual.name == 'P8' or int_actual.name == 'P1'):
        return True
        
    return False

def verificar_inicio_final_segunda_especie_modificado(cf_part, cp_part):
    """
    Verifica las reglas de inicio y final para contrapunto de segunda especie.
    Retorna una lista de errores string. Lista vacía si no hay errores.
    """
    errores = []
    
    cf_flat_notes = list(cf_part.flat.notes)
    cp_flat_elements = list(cp_part.flat.notesAndRests) 

    if not cf_flat_notes:
        errores.append("Regla Inicio/Final: Cantus Firmus no contiene notas.")
    if not cp_flat_elements:
        errores.append("Regla Inicio/Final: Contrapunto no contiene elementos (notas/silencios).")
    
    if not cf_flat_notes or not cp_flat_elements:
        return errores

    # --- ANÁLISIS DEL INICIO ---
    cf_primera_nota = cf_flat_notes[0]
    cp_primera_nota_armonica_efectiva = None

    if cp_flat_elements[0].isRest and cp_flat_elements[0].duration.quarterLength == 2.0: # Silencio de blanca
        if len(cp_flat_elements) > 1 and isinstance(cp_flat_elements[1], note.Note) and \
           cp_flat_elements[1].duration.quarterLength == 2.0:
            cp_primera_nota_armonica_efectiva = cp_flat_elements[1]
    elif isinstance(cp_flat_elements[0], note.Note) and cp_flat_elements[0].duration.quarterLength == 2.0: # Blanca
        cp_primera_nota_armonica_efectiva = cp_flat_elements[0]
    elif cp_flat_elements[0].isRest and cp_flat_elements[0].duration.quarterLength == 4.0: # Silencio de Redonda
        errores.append("Regla Inicio: CP inicia con silencio de redonda. El análisis del intervalo de inicio canónico se aplicaría a la primera interacción armónica real (siguiente compás).")
    else:
        errores.append("Regla Inicio: El contrapunto no comienza con una blanca, o un silencio de blanca seguido de blanca, para el análisis de intervalo inicial.")

    if cp_primera_nota_armonica_efectiva:
        intervalo_inicio_obj = interval.Interval(cf_primera_nota, cp_primera_nota_armonica_efectiva)
        if intervalo_inicio_obj.name not in ['P1', 'P5', 'P8']:
            errores.append(f"Regla Inicio: El primer intervalo armónico ({intervalo_inicio_obj.directedName}) debe ser P1, P5, u P8. Encontrado: {cf_primera_nota.nameWithOctave} con {cp_primera_nota_armonica_efectiva.nameWithOctave}.")
    elif not any("Regla Inicio:" in err for err in errores):
        errores.append("Regla Inicio: No se pudo determinar la primera nota armónica del CP para verificar el intervalo inicial.")

    # --- ANÁLISIS DEL FINAL ---
    cf_ultima_nota = cf_flat_notes[-1]
    cp_ultima_nota = None
    for el in reversed(cp_flat_elements):
        if isinstance(el, note.Note):
            cp_ultima_nota = el
            break
            
    if not cp_ultima_nota:
        errores.append("Regla Final: No se encontró la última nota del contrapunto.")
    else:
        idx_ultima_cp_nota = -1
        try:
            idx_ultima_cp_nota = cp_flat_elements.index(cp_ultima_nota)
        except ValueError:
             pass # No debería ocurrir si se encontró arriba
             
        if idx_ultima_cp_nota > 0:
            cp_penultima_nota_real = None
            for i_idx in range(idx_ultima_cp_nota - 1, -1, -1):
                if isinstance(cp_flat_elements[i_idx], note.Note):
                    cp_penultima_nota_real = cp_flat_elements[i_idx]
                    break
            if cp_penultima_nota_real:
                mov_al_final = interval.Interval(cp_penultima_nota_real, cp_ultima_nota)
                if not mov_al_final.isStep:
                     errores.append(f"Regla Final (CP): El contrapunto no llega a su última nota ({cp_ultima_nota.nameWithOctave}) por grado conjunto desde ({cp_penultima_nota_real.nameWithOctave}). Movimiento: {mov_al_final.directedName}.")

        final_interval_obj = interval.Interval(cf_ultima_nota, cp_ultima_nota)
        if final_interval_obj.name not in ["P1", "P8"]:
            errores.append(f"Regla Final: El intervalo armónico final ({final_interval_obj.directedName}) debe ser P1 u P8. Encontrado: {cf_ultima_nota.nameWithOctave} con {cp_ultima_nota.nameWithOctave}.")
            
    return errores