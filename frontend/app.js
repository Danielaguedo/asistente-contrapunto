/* =========================================================================
   Asistente de Contrapunto — frontend logic (vanilla JS, no framework)
   Intercepts the form, POSTs multipart/form-data to the FastAPI backend,
   and renders the returned PDF paths as download links.
   ========================================================================= */

const API_URL = "http://localhost:8000/analyze/";

const form        = document.getElementById("analyze-form");
const fileInput   = document.getElementById("file");
const dropzone    = document.getElementById("dropzone");
const dropzoneTxt = document.getElementById("dropzone-text");
const fileError   = document.getElementById("file-error");
const submitBtn   = document.getElementById("submit");
const submitLabel = submitBtn.querySelector(".submit__label");
const results     = document.getElementById("results");

/* -------------------------------------------------------------------------
   File picker affordances: reflect the chosen file + drag-and-drop.
   ------------------------------------------------------------------------- */
const VALID_EXT = /\.(musicxml|xml)$/i;

function reflectFile(file) {
  if (file) {
    dropzoneTxt.textContent = file.name;
    dropzone.classList.add("has-file");
    clearFileError();
  } else {
    dropzoneTxt.innerHTML = "Pulse para seleccionar &mdash; o arrastre el archivo aquí";
    dropzone.classList.remove("has-file");
  }
}

fileInput.addEventListener("change", () => reflectFile(fileInput.files[0]));

["dragenter", "dragover"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("is-dragover");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("is-dragover");
  })
);
dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer?.files?.[0];
  if (file) {
    fileInput.files = e.dataTransfer.files;
    reflectFile(file);
  }
});

/* -------------------------------------------------------------------------
   Validation helpers
   ------------------------------------------------------------------------- */
function showFileError(msg) {
  fileError.textContent = msg;
  fileError.hidden = false;
  dropzone.classList.remove("has-file");
}
function clearFileError() {
  fileError.hidden = true;
  fileError.textContent = "";
}

/* -------------------------------------------------------------------------
   Submit
   ------------------------------------------------------------------------- */
form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    showFileError("Seleccione un manuscrito antes de continuar.");
    fileInput.focus();
    return;
  }
  if (!VALID_EXT.test(file.name)) {
    showFileError("El archivo debe ser .musicxml o .xml.");
    return;
  }
  clearFileError();

  setLoading(true);
  renderLoading();

  const data = new FormData();
  data.append("file", file);
  data.append("especie", document.getElementById("especie").value);

  try {
    const response = await fetch(API_URL, { method: "POST", body: data });

    let payload = null;
    try { payload = await response.json(); } catch { /* non-JSON error body */ }

    if (!response.ok) {
      const detail = payload?.detail || `El servidor respondió ${response.status}.`;
      throw new Error(detail);
    }

    renderResults(payload);
  } catch (err) {
    const isNetwork = err instanceof TypeError;
    renderError(
      isNetwork
        ? "No se pudo contactar al servidor. Verifique que el backend esté activo en localhost:8000."
        : err.message
    );
  } finally {
    setLoading(false);
  }
});

/* -------------------------------------------------------------------------
   UI state rendering
   ------------------------------------------------------------------------- */
function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  submitBtn.classList.toggle("is-loading", isLoading);
  submitLabel.textContent = isLoading ? "Analizando…" : "Someter a Análisis";
}

function renderLoading() {
  results.innerHTML = `
    <div class="panel" role="status">
      <p class="loading">
        <span class="loading__quill" aria-hidden="true"></span>
        Examinando el contrapunto&hellip;
      </p>
    </div>`;
}

function renderError(message) {
  results.innerHTML = `
    <div class="panel panel--error" role="alert">
      <h2 class="panel__title">Objeción del Tribunal</h2>
      <p class="panel__msg">${escapeHtml(message)}</p>
    </div>`;
}

function renderResults(payload) {
  // Backend returns real download URLs (GET /download/{token}), served by the
  // API as application/pdf. No more file:// paths.
  const plates = [
    { name: "Partitura Anotada", url: payload.annotated_url, seal: "I" },
    { name: "Informe Académico", url: payload.report_url, seal: "II" },
  ].filter((p) => p.url);

  if (plates.length === 0) {
    renderError("El análisis finalizó pero no se generó ningún PDF.");
    return;
  }

  const items = plates.map((p) => `
    <li>
      <a class="plate" href="${escapeHtml(p.url)}" target="_blank" rel="noopener">
        <span class="plate__seal" aria-hidden="true">${p.seal}</span>
        <span class="plate__body">
          <span class="plate__name">${escapeHtml(p.name)}</span>
          <span class="plate__path">Descargar PDF</span>
        </span>
      </a>
    </li>`).join("");

  results.innerHTML = `
    <div class="panel" role="status">
      <h2 class="panel__title">Dictamen &middot; Especie ${escapeHtml(payload.especie || "")}</h2>
      <ul class="plates">${items}</ul>
      <p class="note">Los documentos se abren en una pestaña nueva desde el servidor local.</p>
    </div>`;
}

/* -------------------------------------------------------------------------
   Utilities
   ------------------------------------------------------------------------- */
function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}
