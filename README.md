# Asistente de Contrapunto

Herramienta de análisis de ejercicios de **contrapunto de especies**. Recibe un
ejercicio en **MusicXML**, aplica las reglas contrapuntísticas de la especie
indicada y produce dos PDF: la **partitura anotada** y un **informe académico**
con el diagnóstico.

- **Primera especie** (nota contra nota) y **segunda especie** (dos contra una).
- Motor musical con [music21](https://web.mit.edu/music21/); grabado con
  [Verovio](https://www.verovio.org/); PDF con [svglib](https://pypi.org/project/svglib/)
  y [reportlab](https://www.reportlab.com/).

> Estado del proyecto y trabajo pendiente: ver [`ROADMAP.md`](ROADMAP.md).
> Reglas de arquitectura y sistema de diseño: ver [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## Requisitos

- **Python 3.12**
- Windows, macOS o Linux (desarrollado y verificado en Windows 11).

No hace falta descargar fuentes de Verovio por separado: el paquete `verovio` de
pip ya las trae y las carga automáticamente.

## Instalación

```powershell
python -m venv venv
venv\Scripts\Activate.ps1      # PowerShell   (cmd: venv\Scripts\activate.bat)
pip install -r requirements.txt
```

---

## Uso por línea de comandos (CLI)

El núcleo (`cli_runner.py`) es autónomo y no necesita el servidor:

```powershell
python cli_runner.py <archivo.musicxml> -e primera -o salida.pdf
```

- `-e, --species` → `primera` | `segunda` (por defecto: `segunda`).
- `-o, --output` → PDF anotado de salida (por defecto: `<archivo>_anotada.pdf`).
- `--cf-index {0,1}` → (solo primera) índice de la voz que es Cantus Firmus (por defecto: 1).
- `--no-report` → no generar el PDF de informe textual.

Junto al PDF anotado se genera también `<salida>_informe.pdf` con el diagnóstico.

> La partitura de entrada debe tener **exactamente 2 voces**.

## Uso por API + Frontend (flujo de demo)

El frontend espera el backend en `http://localhost:8000`.

**1. Backend** (FastAPI) — desde la raíz del proyecto:

```powershell
uvicorn main:app --reload
```

- `POST /analyze/` — recibe `file` (MusicXML) y `especie` (`primera`/`segunda`);
  devuelve `annotated_url` y `report_url` (rutas `GET /download/{token}`).
- `GET /download/{token}` — sirve el PDF generado.
- `GET /` — health check. `GET /docs` — documentación interactiva.

**2. Frontend** (HTML/CSS/JS vanilla, sin build) — desde la carpeta `frontend/`:

```powershell
cd frontend
python -m http.server 5500
```

Abrir `http://localhost:5500`, subir el MusicXML, elegir la especie y someterlo a
análisis. Los PDF (partitura anotada e informe) quedan disponibles como descargas.

---

## Estructura del proyecto

| Ruta | Contenido |
| --- | --- |
| `cli_runner.py` | Núcleo desacoplado: pipeline MusicXML → reglas → SVG → PDF. |
| `main.py` | API FastAPI (capa HTTP delgada sobre `cli_runner`). |
| `verovio_pdf.py` | Grabado con Verovio (SVG) y conversión a PDF (svglib + reportlab). |
| `exportar_pdf.py` | PDF de informe textual (reportlab). |
| `primera_especie/` | Reglas y anotación de primera especie. |
| `segunda_especie/` | Reglas y anotación de segunda especie. |
| `analisis_musical_comun/` | Análisis de movimiento melódico y entre voces. |
| `frontend/` | Interfaz estática (`index.html`, `style.css`, `app.js`). |

---

## Limitaciones conocidas

- **Anotaciones sobre la partitura**: la partitura anotada se genera
  correctamente, pero los **números de intervalo y las flechas de movimiento
  todavía no se dibujan** sobre las notas (bug de mapeo de coordenadas del
  anotador). El pentagrama, claves y notas sí se renderizan. Ver `ROADMAP.md`.
- **Solo local / monomáquina**: la arquitectura asume el frontend y el backend en
  el mismo equipo.
- La entrada debe tener exactamente 2 voces.

Consulta [`ROADMAP.md`](ROADMAP.md) para el estado completo, riesgos y próximos pasos.
