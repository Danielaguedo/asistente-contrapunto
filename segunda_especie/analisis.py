from music21 import note, chord, stream, interval

# Importación relativa correcta
from . import reglas

def es_parte_de_redondas(part_stream):
    """Verifica si una parte consiste principalmente en notas redondas."""
    part_notes = list(part_stream.flat.notes)
    if not part_notes:
        return False
    
    num_redondas = 0
    num_otras_duraciones = 0

    for el in part_stream.flat.notesAndRests:
        if isinstance(el, note.Note):
            if el.duration.quarterLength == 4.0:
                num_redondas += 1
            else:
                num_otras_duraciones +=1
        elif isinstance(el, chord.Chord):
            return False # CF no debería tener acordes
    
    # Para ser considerado CF, debe tener redondas y muy pocas o ninguna otra duración.
    if num_redondas > 0 and num_otras_duraciones <= 1: # Permite una posible nota final diferente en algunos estilos de CF
        return True
    return False

def es_ritmo_segunda_especie_flexible(part_stream):
    """
    Verifica de forma más flexible si una parte tiene características generales
    de un contrapunto de segunda especie (no es CF de redondas, tiene blancas).
    Útil para una identificación inicial.
    """
    if es_parte_de_redondas(part_stream): # Si es de redondas, no es CP de 2da
        return False

    part_notes_and_rests = list(part_stream.flat.notesAndRests)
    if not part_notes_and_rests:
        return False

    num_blancas = 0
    num_silencios_blanca = 0
    num_redondas = 0 # CP de 2da puede tener redondas al final

    for el in part_notes_and_rests:
        if isinstance(el, note.Note):
            if el.duration.quarterLength == 2.0:
                num_blancas += 1
            elif el.duration.quarterLength == 4.0:
                num_redondas +=1
        elif isinstance(el, note.Rest):
            if el.duration.quarterLength == 2.0: # Silencio de blanca inicial
                num_silencios_blanca +=1
            elif el.duration.quarterLength == 4.0 and len(part_notes_and_rests) == 1 : # Silencio de redonda inicial
                return True 

    # Si hay al menos una blanca o un silencio de blanca (y no es CF)
    return (num_blancas > 0 or num_silencios_blanca > 0)


def identificar_cantus_firmus_y_contrapunto(score):
    """Identifica CF y CP para segunda especie."""
    if len(score.parts) != 2:
        return None, None, "La partitura debe contener exactamente dos partes."

    part0, part1 = score.parts[0], score.parts[1]
    cf_part, cp_part = None, None
    
    p0_es_cf = es_parte_de_redondas(part0)
    p1_es_cf = es_parte_de_redondas(part1)
    p0_es_cp_flex = es_ritmo_segunda_especie_flexible(part0)
    p1_es_cp_flex = es_ritmo_segunda_especie_flexible(part1)

    mensaje = ""

    if p0_es_cf and p1_es_cp_flex: # P0 es CF, P1 parece CP
        cf_part, cp_part = part0, part1
        mensaje = "Identificado: Parte 1 como Cantus Firmus (redondas), Parte 2 como Contrapunto (patrón 2da especie)."
    elif p1_es_cf and p0_es_cp_flex: # P1 es CF, P0 parece CP
        cf_part, cp_part = part1, part0
        mensaje = "Identificado: Parte 2 como Cantus Firmus (redondas), Parte 1 como Contrapunto (patrón 2da especie)."
    elif p0_es_cf and not p1_es_cf: # P0 es CF, P1 no es CF (se asume CP)
        cf_part, cp_part = part0, part1
        mensaje = "Identificado: Parte 1 como Cantus Firmus (redondas). Parte 2 se asume Contrapunto."
    elif p1_es_cf and not p0_es_cf: # P1 es CF, P0 no es CF (se asume CP)
        cf_part, cp_part = part1, part0
        mensaje = "Identificado: Parte 2 como Cantus Firmus (redondas). Parte 1 se asume Contrapunto."
    elif p0_es_cp_flex and not p1_es_cp_flex and not p1_es_cf : # P0 parece CP, P1 no parece ni CP ni CF claro
        cp_part, cf_part = part0, part1 # Orden invertido aquí, cf_part es el segundo
        mensaje = "Identificado: Parte 1 como Contrapunto (patrón 2da especie). Parte 2 se asume Cantus Firmus."
    elif p1_es_cp_flex and not p0_es_cp_flex and not p0_es_cf: # P1 parece CP, P0 no parece ni CP ni CF claro
        cp_part, cf_part = part1, part0 # Orden invertido
        mensaje = "Identificado: Parte 2 como Contrapunto (patrón 2da especie). Parte 1 se asume Cantus Firmus."
    else: # Casos ambiguos
        if p0_es_cf and p1_es_cf:
            mensaje = "Ambigüedad: Ambas partes parecen ser Cantus Firmus (redondas)."
        elif p0_es_cp_flex and p1_es_cp_flex:
            mensaje = "Ambigüedad: Ambas partes tienen características de Contrapunto de 2da especie."
        else:
            mensaje = "No se pudo identificar claramente el CF y CP. Asignando Parte 1 como CP y Parte 2 como CF por defecto. El análisis puede ser impreciso."
            # Fallback: Asignar P2 como CF (típicamente inferior o voz más lenta) y P1 como CP
            cf_part, cp_part = part1, part0 # part1 es P2 del XML
            
    if cf_part and cp_part:
        cf_part.id = 'CantusFirmus_id' # Evitar conflicto con el nombre de la variable
        cp_part.id = 'Contrapunto_id'
        # print(f"Debug ID: {mensaje}, CF: {cf_part.id}, CP: {cp_part.id}")
        return cf_part, cp_part, mensaje
    
    return None, None, mensaje


def analizar_segunda_especie(score_original):
    errores = []
    cf_part_obj, cp_part_obj, mensaje_id = identificar_cantus_firmus_y_contrapunto(score_original)

    if mensaje_id and (not cf_part_obj or not cp_part_obj):
        errores.append(f"Error de Identificación de Partes: {mensaje_id}")
        return errores
    elif mensaje_id:
         # Podrías añadir mensajes informativos a una lista separada si lo deseas
         # print(f"Nota de identificación: {mensaje_id}")
         pass

    if not cf_part_obj or not cp_part_obj: # Fallback si la identificación falló completamente
        errores.append("Error Crítico: No se pudieron asignar las partes de Cantus Firmus y Contrapunto.")
        return errores

    cf_measures_list = list(cf_part_obj.getElementsByClass(stream.Measure))
    cp_measures_list = list(cp_part_obj.getElementsByClass(stream.Measure))

    num_cf_measures = len(cf_measures_list)
    num_cp_measures = len(cp_measures_list)

    if num_cf_measures == 0:
        errores.append("Error Crítico: El Cantus Firmus identificado no contiene compases.")
        return errores
    if num_cp_measures == 0:
        errores.append("Error Crítico: El Contrapunto identificado no contiene compases.")
        return errores

    min_compases_analizables = min(num_cf_measures, num_cp_measures)
    if num_cf_measures != num_cp_measures:
        errores.append(f"ADVERTENCIA de Longitud: CF tiene {num_cf_measures} compases, CP tiene {num_cp_measures}. Se analizarán los primeros {min_compases_analizables} compases.")

    cf_nota_anterior_tf = None
    cp_nota_anterior_tf = None

    for i in range(min_compases_analizables):
        cf_compas_actual = cf_measures_list[i]
        cp_compas_actual = cp_measures_list[i]

        cf_notas_en_compas = list(cf_compas_actual.flat.notes)
        if not cf_notas_en_compas:
            errores.append(f"Compás {i+1} (CF): No contiene notas.")
            cf_nota_anterior_tf = None 
            cp_nota_anterior_tf = None
            continue
        cf_nota_actual_tf = cf_notas_en_compas[0] 

        cp_elementos_en_compas = [el for el in cp_compas_actual.flat.notesAndRests if not isinstance(el, chord.Chord)]
        
        nota_cp_tf_actual = None 
        nota_cp_td_actual = None 

        # --- Validación Rítmica del CP para el compás actual ---
        num_elements_cp = len(cp_elementos_en_compas)
        is_first_measure_cp = (i == 0)
        is_last_measure_cp = (i == num_cp_measures - 1)
        is_penultimate_measure_cp = (i == num_cp_measures - 2)

        if is_first_measure_cp:
            if num_elements_cp == 1 and cp_elementos_en_compas[0].isRest and cp_elementos_en_compas[0].duration.quarterLength == 4.0:
                # Silencio de redonda inicial
                pass
            elif num_elements_cp == 2:
                el1, el2 = cp_elementos_en_compas[0], cp_elementos_en_compas[1]
                if el1.isRest and el1.duration.quarterLength == 2.0 and isinstance(el2, note.Note) and el2.duration.quarterLength == 2.0:
                    nota_cp_tf_actual = el2
                elif isinstance(el1, note.Note) and el1.duration.quarterLength == 2.0 and isinstance(el2, note.Note) and el2.duration.quarterLength == 2.0:
                    nota_cp_tf_actual = el1
                    nota_cp_td_actual = el2
                else:
                    errores.append(f"Compás {i+1} (CP): Ritmo inicial no esperado. Debe ser silencio de redonda, silencio de blanca + blanca, o blanca + blanca.")
            else:
                errores.append(f"Compás {i+1} (CP): Ritmo inicial no esperado (número incorrecto de elementos).")
        elif is_last_measure_cp:
            if num_elements_cp == 1 and isinstance(cp_elementos_en_compas[0], note.Note) and cp_elementos_en_compas[0].duration.quarterLength == 4.0:
                nota_cp_tf_actual = cp_elementos_en_compas[0] # La redonda final es el "tiempo fuerte" armónico
            else:
                errores.append(f"Compás {i+1} (CP): Ritmo final no esperado. El último compás del CP debe ser una redonda.")
        elif is_penultimate_measure_cp:
            if num_elements_cp == 1 and isinstance(cp_elementos_en_compas[0], note.Note) and cp_elementos_en_compas[0].duration.quarterLength == 4.0:
                nota_cp_tf_actual = cp_elementos_en_compas[0] # Redonda en penúltimo compás
            elif num_elements_cp == 2 and \
                 isinstance(cp_elementos_en_compas[0], note.Note) and cp_elementos_en_compas[0].duration.quarterLength == 2.0 and \
                 isinstance(cp_elementos_en_compas[1], note.Note) and cp_elementos_en_compas[1].duration.quarterLength == 2.0:
                nota_cp_tf_actual = cp_elementos_en_compas[0]
                nota_cp_td_actual = cp_elementos_en_compas[1]
            else:
                 errores.append(f"Compás {i+1} (CP): Ritmo penúltimo no esperado. Debe ser redonda o dos blancas.")
        else: # Compases intermedios
            if num_elements_cp == 2 and \
                 isinstance(cp_elementos_en_compas[0], note.Note) and cp_elementos_en_compas[0].duration.quarterLength == 2.0 and \
                 isinstance(cp_elementos_en_compas[1], note.Note) and cp_elementos_en_compas[1].duration.quarterLength == 2.0:
                nota_cp_tf_actual = cp_elementos_en_compas[0]
                nota_cp_td_actual = cp_elementos_en_compas[1]
            else:
                errores.append(f"Compás {i+1} (CP): Ritmo intermedio no esperado. Deben ser dos blancas.")

        # --- ANÁLISIS ARMÓNICO ---
        if not nota_cp_tf_actual and not nota_cp_td_actual and not (is_first_measure_cp and num_elements_cp == 1 and cp_elementos_en_compas[0].isRest):
            # Si no se pudieron determinar las notas del CP y no es un silencio de redonda inicial,
            # probablemente por un error de ritmo ya reportado. Continuar al siguiente compás para el análisis armónico.
            cf_nota_anterior_tf = cf_nota_actual_tf # CF avanza
            cp_nota_anterior_tf = None # CP no tuvo nota efectiva
            continue

        if nota_cp_tf_actual:
            if reglas.es_disonancia(cf_nota_actual_tf, nota_cp_tf_actual):
                intervalo_obj = interval.Interval(cf_nota_actual_tf, nota_cp_tf_actual)
                errores.append(f"Compás {i+1} (CP): Tiempo Fuerte. Intervalo disonante '{intervalo_obj.niceName}' ({cf_nota_actual_tf.nameWithOctave} vs {nota_cp_tf_actual.nameWithOctave}). Debe ser consonante.")
            
            if cf_nota_anterior_tf and cp_nota_anterior_tf: 
                if reglas.quintas_octavas_consecutivas(cf_nota_anterior_tf, cp_nota_anterior_tf, cf_nota_actual_tf, nota_cp_tf_actual):
                    int_ant = interval.Interval(cf_nota_anterior_tf, cp_nota_anterior_tf)
                    int_act = interval.Interval(cf_nota_actual_tf, nota_cp_tf_actual)
                    tipo_paralela = "Quintas" if '5' in int_ant.name else "Octavas/Unísonos"
                    errores.append(f"Paralelismo de {tipo_paralela} (TFs): Compás {i} ({cp_nota_anterior_tf.nameWithOctave}) a Compás {i+1} ({nota_cp_tf_actual.nameWithOctave}) contra CF. Intervalos: {int_ant.niceName} -> {int_act.niceName}.")
            
            cf_nota_anterior_tf = cf_nota_actual_tf
            cp_nota_anterior_tf = nota_cp_tf_actual
        else: 
            cf_nota_anterior_tf = cf_nota_actual_tf
            cp_nota_anterior_tf = None

        if nota_cp_td_actual and nota_cp_tf_actual: 
            if reglas.es_disonancia(cf_nota_actual_tf, nota_cp_td_actual):
                es_paso_valido = False
                if reglas.es_consonancia(cf_nota_actual_tf, nota_cp_tf_actual):
                    mov_tf_a_td = interval.Interval(nota_cp_tf_actual, nota_cp_td_actual)
                    if mov_tf_a_td.isStep:
                        siguiente_nota_cp_tf_para_paso = None
                        if (i + 1) < min_compases_analizables : # Si hay un siguiente compás
                            siguiente_cp_compas_obj = cp_measures_list[i+1]
                            siguiente_cp_elementos_compas = [el for el in siguiente_cp_compas_obj.flat.notesAndRests if not isinstance(el, chord.Chord)]
                            # Lógica para obtener la primera nota efectiva del siguiente compás del CP
                            if len(siguiente_cp_elementos_compas) > 0:
                                if isinstance(siguiente_cp_elementos_compas[0], note.Note) and siguiente_cp_elementos_compas[0].duration.quarterLength >= 2.0 : # Blanca o Redonda
                                     siguiente_nota_cp_tf_para_paso = siguiente_cp_elementos_compas[0]
                                elif len(siguiente_cp_elementos_compas) > 1 and siguiente_cp_elementos_compas[0].isRest and isinstance(siguiente_cp_elementos_compas[1], note.Note): # Silencio + nota
                                     siguiente_nota_cp_tf_para_paso = siguiente_cp_elementos_compas[1]
                        
                        if siguiente_nota_cp_tf_para_paso:
                            mov_td_a_sigtf = interval.Interval(nota_cp_td_actual, siguiente_nota_cp_tf_para_paso)
                            if mov_td_a_sigtf.isStep and mov_tf_a_td.direction == mov_td_a_sigtf.direction:
                                es_paso_valido = True
                
                if not es_paso_valido:
                    intervalo_td_obj = interval.Interval(cf_nota_actual_tf, nota_cp_td_actual)
                    errores.append(f"Compás {i+1} (CP): Tiempo Débil. Disonancia '{intervalo_td_obj.niceName}' ({cf_nota_actual_tf.nameWithOctave} vs {nota_cp_td_actual.nameWithOctave}). No es una nota de paso válida (verificar consonancia del TF, grados conjuntos y dirección del movimiento).")
    
    errores_inicio_final = reglas.verificar_inicio_final_segunda_especie_modificado(cf_part_obj, cp_part_obj)
    errores.extend(errores_inicio_final)

    return errores