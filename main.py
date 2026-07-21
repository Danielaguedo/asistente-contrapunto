# main.py - FastAPI backend para el Asistente de Contrapunto (Fase 2).
#
# Envuelve el core engine desacoplado (cli_runner.py) en una API HTTP.
# Arranque:  uvicorn main:app --reload

import os
import secrets
import shutil
import tempfile

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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

# Registro efimero token -> ruta de PDF (en memoria; se pierde al reiniciar el
# proceso). Suficiente para el uso local monomaquina: convierte rutas de servidor
# en URLs descargables sin exponer el filesystem.
_PDF_REGISTRY: dict[str, str] = {}


def _registrar_descarga(path: str) -> str:
    token = secrets.token_urlsafe(16)
    _PDF_REGISTRY[token] = path
    return token


@app.get("/")
def health():
    return {"status": "ok", "service": "asistente-contrapunto", "especies": list(PROCESADORES)}


@app.get("/download/{token}")
def download(token: str):
    path = _PDF_REGISTRY.get(token)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Documento no encontrado o expirado.")
    return FileResponse(path, media_type="application/pdf", filename=os.path.basename(path))


@app.post("/analyze/")
async def analyze(request: Request, file: UploadFile = File(...), especie: str = Form(...)):
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

    annotated_token = _registrar_descarga(ruta_pdf)
    report_exists = os.path.exists(report_pdf)
    report_token = _registrar_descarga(report_pdf) if report_exists else None

    base = str(request.base_url).rstrip("/")
    return {
        "status": "ok",
        "especie": especie,
        "annotated_url": f"{base}/download/{annotated_token}",
        "report_url": f"{base}/download/{report_token}" if report_token else None,
        # Rutas de servidor conservadas solo para depuracion local.
        "input_file": input_path,
        "annotated_pdf": ruta_pdf,
        "report_pdf": report_pdf if report_exists else None,
    }
