from music21 import *

def verificar_consonancias(nota_soprano, nota_bajo):
    intervalo = interval.Interval(nota_bajo, nota_soprano)
    semitonos = intervalo.semitones % 12  # Reduce intervalos compuestos a simples
    consonancias = [0, 3, 4, 7, 8, 9]    # Unísono, 3ras, 5tas, 6tas
    return semitonos in consonancias

def buscar_quintas_octavas_paralelas(intervalo_anterior, intervalo_actual):
    if not intervalo_anterior:
        return False
    return (intervalo_anterior.name == "P5" and intervalo_actual.name == "P5") or \
           (intervalo_anterior.name == "P8" and intervalo_actual.name == "P8")

def movimiento_directo_prohibido(nota_soprano_ant, nota_soprano, nota_bajo_ant, nota_bajo):
    if not nota_soprano_ant or not nota_bajo_ant:
        return False
    
    direccion_soprano = interval.Interval(nota_soprano_ant, nota_soprano).direction
    direccion_bajo = interval.Interval(nota_bajo_ant, nota_bajo).direction
    
    intervalo_actual = interval.Interval(nota_bajo, nota_soprano)
    return (intervalo_actual.name in ["P1", "P5", "P8"]) and (direccion_soprano == direccion_bajo)

def verificar_inicio_final(soprano, bajo):
    errores = []
    inicio = interval.Interval(bajo[0], soprano[0]).name
    final = interval.Interval(bajo[-1], soprano[-1]).name
    
    # Permite quintas, octavas y dobles octavas
    if inicio not in ["P1", "P5", "P8", "P15"]:
        errores.append(f"Inicio no válido: {inicio}")
    if final not in ["P1", "P5", "P8", "P15"]:
        errores.append(f"Final no válido: {final}")
    return errores

def detectar_notas_repetidas(voz):
    return [i for i in range(1, len(voz)) if voz[i].pitch == voz[i-1].pitch]

def analizar_rango_vocal(voz, rango_min, rango_max):
    return [nota for nota in voz if not (rango_min <= nota.pitch.midi <= rango_max)]