# segunda_especie/reglas.py (v12 - Set de Reglas COMPLETO: Unísonos, Repeticiones y Cruces)

from music21 import interval, note, stream, meter

# --- FUNCIONES AUXILIARES ---

def es_consonancia(nota_cf, nota_cp):
    if not isinstance(nota_cf, note.Note) or not isinstance(nota_cp, note.Note): return False
    try:
        intervalo_obj = interval.Interval(nota_cf, nota_cp)
        if intervalo_obj.simpleName == 'P4': return False 
        return intervalo_obj.isConsonant()
    except: return False

def es_disonancia(nota_cf, nota_cp):
    if not isinstance(nota_cf, note.Note) or not isinstance(nota_cp, note.Note): return False 
    return not es_consonancia(nota_cf, nota_cp)

def quintas_octavas_consecutivas(cf_ant, cp_ant, cf_actual, cp_actual):
    notes_list = [cf_ant, cp_ant, cf_actual, cp_actual]
    if not all(isinstance(n, note.Note) for n in notes_list): return False
    try:
        int_ant = interval.Interval(cf_ant, cp_ant)
        int_actual = interval.Interval(cf_actual, cp_actual)
        if int_actual.simpleName not in ['P1', 'P5', 'P8']: return False
        if int_ant.simpleName == int_actual.simpleName: return True
    except Exception: return False
    return False

# --- REGLAS DE INICIO Y FINAL ---

def verificar_inicio_final_segunda_especie_modificado(cf_part, cp_part):
    errores = []
    cf_flat_notes = [n for n in cf_part.flatten().notes if isinstance(n, note.Note)]
    cp_flat_elements = [n for n in cp_part.flatten().notesAndRests if isinstance(n, (note.Note, note.Rest))]
    
    if not cf_flat_notes or not cp_flat_elements: return ["Error: Partes vacías o inválidas."]
    
    cf_primera = cf_flat_notes[0]
    cp_primera_armonica = None
    
    # 1. Inicio
    elem0 = cp_flat_elements[0]
    if elem0.isRest:
        if elem0.duration.quarterLength == 2.0:
            if len(cp_flat_elements) > 1 and isinstance(cp_flat_elements[1], note.Note):
                cp_primera_armonica = cp_flat_elements[1]
            else: errores.append("Regla Inicio: Silencio inicial no seguido de nota.")
        elif elem0.duration.quarterLength == 4.0: pass 
        else: errores.append("Regla Inicio: El silencio inicial debe ser de blanca.")
    elif isinstance(elem0, note.Note):
        cp_primera_armonica = elem0
    else: errores.append("Regla Inicio: Elemento inicial desconocido.")
        
    if cp_primera_armonica:
        try:
            int_ini = interval.Interval(cf_primera, cp_primera_armonica)
            if int_ini.simpleName not in ['P1', 'P5', 'P8']:
                errores.append(f"Regla Inicio: Debe comenzar con consonancia perfecta (1, 5, 8). Encontrado: {int_ini.simpleName}.")
        except: pass

    # 2. Final
    cf_ultima = cf_flat_notes[-1]
    cp_notas_reales = [n for n in cp_flat_elements if isinstance(n, note.Note)]
    if not cp_notas_reales: return errores
    cp_ultima = cp_notas_reales[-1]
    
    if cp_ultima.duration.quarterLength < 4.0:
         errores.append(f"Regla Final: La última nota del CP debe ser una redonda. Es {cp_ultima.duration.type}.")
    
    try:
        int_fin = interval.Interval(cf_ultima, cp_ultima)
        if int_fin.simpleName not in ['P1', 'P8']:
             errores.append(f"Regla Final: Debe terminar en Octava o Unísono. Encontrado: {int_fin.simpleName}.")
    except: pass
    
    if len(cp_notas_reales) > 1:
        cp_penultima = cp_notas_reales[-2]
        try:
            mov_final = interval.Interval(cp_penultima, cp_ultima)
            if not mov_final.isStep:
                errores.append(f"Regla Final: Se debe llegar a la nota final por grado conjunto. Salto: {mov_final.simpleName}.")
        except: pass

    return errores

# --- ANÁLISIS CUERPO (DISONANCIAS, UNÍSONOS, REPETICIONES) ---

def analizar_figuras_disonantes_2da_especie(cp_part_obj, cf_part_obj):
    errores = []
    observaciones = []
    ids_rojos = []
    
    cp_notes = [n for n in cp_part_obj.flatten().notes if isinstance(n, note.Note)]
    cf_flat = cf_part_obj.flatten()
    # Solo notas reales del CF: descarta SystemLayout, Clef, TimeSignature, etc.
    cf_notes = [n for n in cf_flat.notes if isinstance(n, note.Note)]

    # Dirección de referencia (inicio) calculada UNA sola vez y de forma segura.
    # Antes se usaba cf_flat[0], que podía ser un SystemLayout -> AttributeError 'pitch'.
    direccion_referencia = None
    if cf_notes and cp_notes:
        try:
            direccion_referencia = interval.Interval(cf_notes[0], cp_notes[0]).direction
        except Exception:
            direccion_referencia = None

    for i in range(len(cp_notes)):
        cp_curr = cp_notes[i]
        cf_simultaneas = cf_flat.getElementsByOffset(cp_curr.offset, mustBeginInSpan=False, classList=[note.Note])
        if not cf_simultaneas: continue
        cf_curr = cf_simultaneas[0]
        
        # --- NUEVA REGLA: NOTAS REPETIDAS ---
        if i > 0:
            cp_prev = cp_notes[i-1]
            if cp_curr.pitch == cp_prev.pitch:
                errores.append(f"Compás {cp_curr.measureNumber}: Nota repetida. En 2da especie debe haber movimiento constante.")
                ids_rojos.append(cp_curr.id)

        # --- NUEVA REGLA: CRUCE DE VOCES ---
        try:
            # Si es intervalo negativo (ej. -P5), hubo cruce
            int_cruce = interval.Interval(cf_curr, cp_curr)
            if direccion_referencia is not None and int_cruce.direction != direccion_referencia:
                # Comparación simple: si la dirección del intervalo cambia respecto al inicio, hubo cruce
                # (Asumiendo que no cruzan en la primera nota)
                errores.append(f"Compás {cp_curr.measureNumber}: Cruce de voces detectado ({int_cruce.niceName}). Evitar cruces.")
                ids_rojos.append(cp_curr.id)
        except: pass

        # --- REGLAS DE TIEMPOS ---
        
        # 1. TIEMPO FUERTE (Beat 1)
        if cp_curr.beat == 1.0:
            # Disonancia en tiempo fuerte
            if es_disonancia(cf_curr, cp_curr):
                int_obj = interval.Interval(cf_curr, cp_curr)
                errores.append(f"Error en Compás {cp_curr.measureNumber}: Disonancia ({int_obj.simpleName}) en tiempo fuerte. Debe ser consonancia.")
                ids_rojos.append(cp_curr.id)
            
            # --- NUEVA REGLA: UNÍSONO EN TIEMPO FUERTE ---
            # Permitido solo en primer y último compás
            try:
                int_uni = interval.Interval(cf_curr, cp_curr)
                if int_uni.simpleName == 'P1':
                    es_inicio = (i == 0)
                    es_final = (i == len(cp_notes) - 1)
                    if not es_inicio and not es_final:
                        errores.append(f"Error en Compás {cp_curr.measureNumber}: Unísono en tiempo fuerte. Solo permitido al inicio o final.")
                        ids_rojos.append(cp_curr.id)
            except: pass
        
        # 2. TIEMPO DÉBIL
        else:
            if es_disonancia(cf_curr, cp_curr):
                es_nota_paso = False
                problema = "Disonancia no justificada"
                
                if i > 0 and i < len(cp_notes) - 1:
                    cp_prev = cp_notes[i-1]; cp_next = cp_notes[i+1]
                    try:
                        int_in = interval.Interval(cp_prev, cp_curr)
                        int_out = interval.Interval(cp_curr, cp_next)
                        
                        step_in = int_in.isStep
                        step_out = int_out.isStep
                        mismo_sentido = (int_in.direction == int_out.direction)
                        
                        if step_in and step_out and mismo_sentido:
                            es_nota_paso = True
                            observaciones.append(f"Compás {cp_curr.measureNumber}: Nota de paso correcta.")
                        else:
                            detalles = []
                            if not step_in: detalles.append("entrada por salto")
                            if not step_out: detalles.append("salida por salto")
                            if not mismo_sentido and step_in and step_out: detalles.append("bordadura (evitar en estricto)")
                            problema = f"Disonancia mal tratada ({', '.join(detalles)})"
                    except: pass
                
                if not es_nota_paso:
                    int_obj = interval.Interval(cf_curr, cp_curr)
                    errores.append(f"Error en Compás {cp_curr.measureNumber}: {problema}. Disonancia ({int_obj.simpleName}) debe ser nota de paso.")
                    ids_rojos.append(cp_curr.id)

    return errores, observaciones, ids_rojos