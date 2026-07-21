# ROADMAP — Asistente de Contrapunto

## Estado actual (funcional)
- **Motor de análisis (núcleo desacoplado, `cli_runner.py`)**: completo y usable
  desde CLI y API.
- **Primera especie**: reglas completas (consonancias, paralelas, movimiento
  directo, inicio/final, cruces, repeticiones) + análisis melódico y entre voces.
- **Segunda especie**: reglas completas (disonancias en tiempo débil, nota de paso,
  paralelas fuerte-a-fuerte, unísonos, cruces).
- **Generación de PDFs**: partitura anotada (Verovio→SVG→cairosvg) e informe
  textual (reportlab).
- **API FastAPI** (`main.py`): `POST /analyze/` con contrato documentado.
- **Frontend** (HTML/CSS/JS vanilla, estética Barroca): completo, accesible,
  con dropzone y manejo de estados.
- **ARCHITECTURE.md**: reglas de arquitectura y sistema de diseño definidos.

## En progreso
- Migración desde el stack antiguo (Streamlit + Firebase multiusuario) hacia
  núcleo + API + frontend estático. El desacople está hecho; falta la limpieza.

## Pendiente
- [x] Regenerar `requirements.txt` desde `requirements.in` con pip-compile
      (versiones del motor fijadas). Eliminadas streamlit/firebase/google-cloud/
      pandas/altair/pydeck; añadido el stack FastAPI que faltaba. API verificada ✅.
- [x] Fuentes de Verovio: resuelto — el paquete `verovio` de pip trae y carga
      las fuentes solo (verificado). No requiere `data/` local ni `.woff`.
- [ ] Añadir ruta `GET /download/{token}` para servir PDFs como archivos
      descargables (hoy se devuelven rutas absolutas → enlaces file:// bloqueados).
- [ ] README con instrucciones de arranque (backend + frontend).
- [ ] Ajustar `.gitignore` y añadir `samples/` con MusicXML de ejemplo por especie.
- [ ] Suite mínima de tests (pytest) sobre ambos pipelines.
- [ ] Endurecer `verovio_pdf.py`: temp con nombre único (concurrencia),
      resource path independiente del CWD, limpieza de temporales en `main.py`,
      y retirar el andamiaje obsoleto de `data/`/`.woff` + `descargar_fuentes_final.py`
      (URLs 404 y crash cp1252 por emojis).
- [ ] Decidir destino de `material_didactico/` (fantasma) y `midi.py` (huérfano).
- [ ] Tercera / cuarta / quinta especie (fuera del MVP actual).

## Riesgos conocidos
- **Arranque en limpio**: resuelto. `requirements.txt` regenerado e instalado,
  API verificada; fuentes servidas por el paquete de Verovio. Deuda menor: retirar
  el andamiaje obsoleto de `data/`/`.woff`.
- **Balance de dependencias**: resuelto (regenerado con pip-compile). Nota: el venv
  aún contiene `aider-chat` y `streamlit` viejos → warnings de conflicto de pip
  inofensivos; limpiar el venv es opcional.
- **Entrega de PDF rota en el navegador**: rutas file:// desde origen http se
  bloquean. El flujo end-to-end no cierra hasta añadir /download.
- **Concurrencia**: `verovio_pdf.py` escribe a un nombre de archivo fijo →
  peticiones simultáneas colisionan.
- **Fugas de recursos**: los directorios temporales de `main.py` nunca se limpian.
- **Sin tests**: cualquier cambio en las reglas puede romper el análisis sin aviso.
- **CORS `["*"]` + `allow_credentials=True`**: configuración inválida.
- **Solo local monomáquina**: la arquitectura asume frontend y backend en el
  mismo equipo (documentado en ARCHITECTURE.md).
