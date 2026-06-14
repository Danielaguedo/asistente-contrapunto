# main.py - FastAPI backend para el Asistente de Contrapunto (Fase 2).
#
# Envuelve el core engine desacoplado (cli_runner.py) en una API HTTP.
# Arranque:  uvicorn main:app --reload

import os
import shutil
import tempfile

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import cli_runner

app = FastAPI(
    title="Asistente de Contrapunto API",
    description="Analiza ejercicios de contrapunto (MusicXML) y devuelve PDFs anotados.",
    version="2.0.0",
)

# CORS abierto: permite que el futuro frontend local consuma la API sin fricciones.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Procesadores disponibles por especie.
PROCESADORES = {
    "primera": cli_runner.procesar_primera,
    "segunda": cli_runner.procesar_segunda,
}


@app.get("/")
def health():
    return {"status": "ok", "service": "asistente-contrapunto", "especies": list(PROCESADORES)}


@app.post("/analyze/")
async def analyze(file: UploadFile = File(...), especie: str = Form(...)):
    especie = (especie or "").strip().lower()
    if especie not in PROCESADORES:
        raise HTTPException(
            status_code=422,
            detail=f"Especie no soportada: '{especie}'. Use {list(PROCESADORES)}.",
        )

    # Directorio temporal aislado por peticion (no se borra: contiene los PDFs servibles).
    work_dir = tempfile.mkdtemp(prefix="contrapunto_")
    stem, ext = os.path.splitext(os.path.basename(file.filename or "ejercicio.musicxml"))
    if ext.lower() not in (".xml", ".musicxml"):
        ext = ".musicxml"

    input_path = os.path.join(work_dir, f"{stem}{ext}")
    output_pdf = os.path.join(work_dir, f"{stem}_anotada.pdf")
    report_pdf = f"{os.path.splitext(output_pdf)[0]}_informe.pdf"

    # Guardar el archivo subido de forma segura.
    try:
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        await file.close()

    # Ejecutar el pipeline del core engine.
    try:
        procesar = PROCESADORES[especie]
        ruta_pdf = procesar(input_path, output_pdf)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el pipeline: {e}")

    if not (ruta_pdf and os.path.exists(ruta_pdf)):
        raise HTTPException(status_code=500, detail="No se genero el PDF anotado.")

    return {
        "status": "ok",
        "especie": especie,
        "input_file": input_path,
        "annotated_pdf": ruta_pdf,
        "report_pdf": report_pdf if os.path.exists(report_pdf) else None,
    }
