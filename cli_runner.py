#!/usr/bin/env python3
# cli_runner.py - Nucleo desacoplado del Asistente de Contrapunto.
#
# Pipeline puro y ejecutable desde linea de comandos:
#   parseo MusicXML -> aplicacion de reglas -> generacion SVG (Verovio) -> exportacion PDF
#
# Sin Streamlit ni Firebase. Pensado para ser reutilizado por un backend FastAPI local.

import argparse
import os
import sys
import tempfile
import datetime
import traceback

from music21 import converter, note as m21note, stream as m21stream

import verovio_pdf
import exportar_pdf
from primera_especie.analisis import seccion_analizar_ejercicio
from segunda_especie.analisis import (
    analizar_segunda_especie,
    identificar_cantus_firmus_y_contrapunto,
)

VEROVIO_OPTS_1RA = {
    "pageHeight": 600, "adjustPageHeight": True, "scale": 60, "svgHtml5": True,
}
VEROVIO_OPTS_2DA = {
    "pageHeight": 600, "adjustPageHeight": True, "scale": 60,
    "pageMarginTop": 40, "pageMarginBottom": 40,
    "pageMarginLeft": 40, "pageMarginRight": 40,
    "breaks": "none", "landscape": 0, "svgHtml5": True,
}


def log(msg):
    print(f"[cli_runner] {msg}")


# ----------------------------------------------------------------------
# Utilidades del pipeline
# ----------------------------------------------------------------------
def _normalizar_part_ids(score):
    """Garantiza que cada parte tenga un id string estable."""
    for i, p in enumerate(score.parts):
        if not (p.id and isinstance(p.id, str) and p.id.strip()):
            p.id = f"part_{i}"
    return list(score.parts)


def _asignar_ids_notas(part):
    """Asigna IDs estables a cada nota (necesario para anotar el SVG por id)."""
    prefix = part.id
    idx = 0
    for element in part.recurse().getElementsByClass(m21note.GeneralNote):
        if element.isNote:
            element.id = f"{prefix}_n{idx}"
            idx += 1


def _escribir_musicxml_temporal(score, prefijo):
    """Reescribe el score (ya con IDs) a un MusicXML temporal para Verovio."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml", prefix=prefijo)
    tmp.close()
    score.write('musicxml', fp=tmp.name)
    return tmp.name


def _safe_remove(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _reportar_consola(errores, evaluacion):
    if errores:
        log(f"Se encontraron {len(errores)} errores/observaciones:")
        for e in errores:
            print(f"   - {e}")
    else:
        log(f"OK: {evaluacion}")


def _generar_reporte_pdf(output_pdf, especie, errores, evaluacion, observaciones,
                         cp_name=None, cf_name=None):
    """Genera el PDF de informe textual junto al PDF de partitura anotada."""
    datos = {
        "especie": especie,
        "errores": errores,
        "evaluacion": evaluacion,
        "fecha": datetime.date.today().strftime("%Y-%m-%d"),
        "observaciones": observaciones,
    }
    if cp_name:
        datos["cp_part_name"] = cp_name
    if cf_name:
        datos["cf_part_name"] = cf_name

    buffer = exportar_pdf.generar_pdf_analisis_estable(datos)
    base, _ = os.path.splitext(output_pdf)
    reporte_path = f"{base}_informe.pdf"
    with open(reporte_path, "wb") as f:
        f.write(buffer.read())
    log(f"Informe textual generado: {reporte_path}")
    return reporte_path


# ----------------------------------------------------------------------
# Pipelines por especie
# ----------------------------------------------------------------------
def procesar_primera(input_path, output_pdf, cf_index=1, generar_reporte=True):
    log(f"Parseando MusicXML: {input_path}")
    score = converter.parse(input_path)
    parts = _normalizar_part_ids(score)
    if len(parts) != 2:
        raise ValueError(f"La partitura debe tener exactamente 2 voces (encontradas: {len(parts)}).")

    cp_index = 0 if cf_index == 1 else 1
    cf_part, cp_part = parts[cf_index], parts[cp_index]
    log(f"CF = parte[{cf_index}] (id={cf_part.id}) | CP = parte[{cp_index}] (id={cp_part.id})")

    for p in (cf_part, cp_part):
        _asignar_ids_notas(p)

    musicxml_ids = _escribir_musicxml_temporal(score, "m21_ids_1ra_")
    try:
        log("Aplicando reglas de primera especie...")
        resultado = seccion_analizar_ejercicio(score, cf_part, cp_part)
        _reportar_consola(resultado.errores, resultado.evaluacion)

        datos_anot = {
            'tipo': 'primera',
            'movimientos_cf': resultado.movimientos_cf,
            'movimientos_cp': resultado.movimientos_cp,
            'intervalos': resultado.datos_intervalos_svg,
        }
        log("Generando partitura anotada (Verovio -> SVG -> PDF)...")
        ruta = verovio_pdf.generar_pdf_partitura(
            musicxml_ids, output_pdf, VEROVIO_OPTS_1RA,
            score, cf_part, cp_part, "primera", datos_anot)

        if generar_reporte:
            _generar_reporte_pdf(output_pdf, "Primera",
                                 resultado.errores, resultado.evaluacion,
                                 getattr(resultado, "observaciones", []))
        return ruta
    finally:
        _safe_remove(musicxml_ids)


def procesar_segunda(input_path, output_pdf, generar_reporte=True):
    log(f"Parseando MusicXML: {input_path}")
    score = converter.parse(input_path)
    parts = _normalizar_part_ids(score)
    if len(parts) != 2:
        raise ValueError(f"La partitura debe tener exactamente 2 voces (encontradas: {len(parts)}).")

    cf_part, cp_part, mensaje = identificar_cantus_firmus_y_contrapunto(score)
    log(f"Identificacion automatica CF/CP: {mensaje}")

    for p in (cf_part, cp_part):
        _asignar_ids_notas(p)

    # Verovio espera CP arriba y CF abajo (mismo orden que usaba la app original).
    score_verovio = m21stream.Score()
    score_verovio.append(cp_part)
    score_verovio.append(cf_part)

    musicxml_ids = _escribir_musicxml_temporal(score_verovio, "m21_ids_2da_")
    try:
        log("Aplicando reglas de segunda especie...")
        resultado = analizar_segunda_especie(score_verovio, cf_part, cp_part)
        _reportar_consola(resultado.errores, resultado.evaluacion)

        datos_anot = {
            'tipo': 'segunda',
            'intervalos': resultado.datos_intervalos_svg,
            'ids_rojos': resultado.ids_notas_rojas,
            'movimientos_cp': resultado.movimientos_cp,
        }
        log("Generando partitura anotada (Verovio -> SVG -> PDF)...")
        ruta = verovio_pdf.generar_pdf_partitura(
            musicxml_path=musicxml_ids, output_pdf=output_pdf,
            verovio_options=VEROVIO_OPTS_2DA, score_m21_obj=score_verovio,
            cf_part_m21_obj=cf_part, cp_part_m21_obj=cp_part,
            species_str="segunda", datos_anotacion_especie=datos_anot)

        if generar_reporte:
            _generar_reporte_pdf(output_pdf, "Segunda",
                                 resultado.errores, resultado.evaluacion,
                                 resultado.observaciones,
                                 cp_name=(cp_part.partName or cp_part.id),
                                 cf_name=(cf_part.partName or cf_part.id))
        return ruta
    finally:
        _safe_remove(musicxml_ids)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Nucleo CLI del Asistente de Contrapunto: MusicXML -> PDF anotado.")
    parser.add_argument("input", help="Archivo MusicXML de entrada (.xml / .musicxml).")
    parser.add_argument("-o", "--output", default=None,
                        help="PDF anotado de salida (por defecto: <input>_anotada.pdf).")
    parser.add_argument("-e", "--species", choices=["primera", "segunda"], default="segunda",
                        help="Especie de contrapunto (por defecto: segunda).")
    parser.add_argument("--cf-index", type=int, choices=[0, 1], default=1,
                        help="(Solo primera) indice de la parte que es Cantus Firmus (por defecto: 1).")
    parser.add_argument("--no-report", action="store_true",
                        help="No generar el PDF de informe textual adicional.")
    args = parser.parse_args(argv)

    if not os.path.exists(args.input):
        log(f"ERROR: no existe el archivo de entrada: {args.input}")
        return 2

    output_pdf = args.output
    if output_pdf is None:
        base, _ = os.path.splitext(os.path.basename(args.input))
        output_pdf = f"{base}_anotada.pdf"

    generar_reporte = not args.no_report
    try:
        if args.species == "primera":
            ruta = procesar_primera(args.input, output_pdf, args.cf_index, generar_reporte)
        else:
            ruta = procesar_segunda(args.input, output_pdf, generar_reporte)
    except Exception as e:
        log(f"ERROR en el pipeline: {e}")
        traceback.print_exc()
        return 1

    if ruta and os.path.exists(ruta):
        log(f"PDF anotado generado correctamente: {ruta}")
        return 0
    log("ERROR: no se genero el PDF anotado.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
