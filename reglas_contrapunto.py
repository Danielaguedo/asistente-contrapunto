from music21 import interval


def verificar_consonancias(nota_soprano, nota_bajo):
    intervalo = interval.Interval(nota_bajo, nota_soprano)
    semitonos = intervalo.semitones % 12
    return semitonos in [0, 3, 4, 7, 8, 9]  # Consonancias


def buscar_quintas_octavas_paralelas(intervalo_anterior, intervalo_actual):
    if not intervalo_anterior:
        return False
    return (intervalo_anterior.name == "P5" and intervalo_actual.name == "P5") or (
        intervalo_anterior.name == "P8" and intervalo_actual.name == "P8"
    )


def movimiento_directo_prohibido(
    nota_soprano_ant, nota_soprano, nota_bajo_ant, nota_bajo
):
    if not nota_soprano_ant or not nota_bajo_ant:
        return False

    intervalo_actual = interval.Interval(nota_bajo, nota_soprano)
    direccion_soprano = interval.Interval(nota_soprano_ant, nota_soprano).direction
    direccion_bajo = interval.Interval(nota_bajo_ant, nota_bajo).direction

    return (intervalo_actual.name in ["P1", "P5", "P8"]) and (
        direccion_soprano == direccion_bajo
    )


def verificar_inicio_final(soprano, bajo):
    inicio = interval.Interval(bajo[0], soprano[0]).name
    final = interval.Interval(bajo[-1], soprano[-1]).name
    errores = []

    if inicio not in ["P1", "P5", "P8", "P15"]:
        errores.append(f"Inicio no válido: {inicio}")
    if final not in ["P1", "P5", "P8", "P15"]:
        errores.append(f"Final no válido: {final}")

    return errores


def detectar_notas_repetidas(voz):
    return [i for i in range(1, len(voz)) if voz[i].pitch == voz[i - 1].pitch]
