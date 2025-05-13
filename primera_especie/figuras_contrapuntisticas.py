# primera_especie/figuras_contrapuntisticas.py
from music21 import note as m21note, interval

def identificar_patrones_primera_especie(cp_part, cf_part):
    """
    Identifica patrones melódicos o armónicos relevantes para la primera especie.
    Por ahora, esta función es un placeholder o puede realizar análisis simples.
    Retorna una lista de strings con observaciones.
    """
    observaciones_figuras = []
    
    cp_notes_list = [n for n in cp_part.recurse().getElementsByClass(m21note.Note) if n.isNote]
    cf_notes_list = [n for n in cf_part.recurse().getElementsByClass(m21note.Note) if n.isNote]

    min_len = min(len(cp_notes_list), len(cf_notes_list))

    if min_len == 0:
        return ["No hay suficientes notas para identificar patrones específicos de primera especie."]

    # Ejemplo: Verificar si se llega a una consonancia perfecta por salto en el CP
    # (Esto ya se cubre en parte por la regla de movimiento directo, pero es un ejemplo de patrón)
    if min_len > 1:
        for i in range(1, min_len):
            cp_ant = cp_notes_list[i-1]
            cp_curr = cp_notes_list[i]
            cf_curr = cf_notes_list[i]

            inter_armonico_actual = interval.Interval(noteStart=cf_curr, noteEnd=cp_curr)
            mov_cp = interval.Interval(noteStart=cp_ant, noteEnd=cp_curr)

            if inter_armonico_actual.simpleName in ["P5", "P8"] and not mov_cp.isStep:
                observaciones_figuras.append(
                    f"  Patrón: En el tiempo {i+1}, se llega a una consonancia perfecta ({inter_armonico_actual.simpleName}) "
                    f"con un salto en el Contrapunto ({mov_cp.simpleName}). (Revisar regla de movimiento directo)."
                )
    
    if not observaciones_figuras:
        observaciones_figuras.append("  No se identificaron patrones especiales adicionales para destacar en esta primera especie.")
        
    return observaciones_figuras

# Podrías añadir aquí funciones para identificar tipos de cadencia si fuera relevante
# def identificar_cadencia_final(cp_notes_list, cf_notes_list):
#     # ... lógica para identificar patrones cadenciales ...
#     pass
