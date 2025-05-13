# exportar_pdf.py
from reportlab.lib.pagesizes import letter # Cambiado a portrait para mejor lectura de texto
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.colors import red, black, navy, grey
from io import BytesIO
import os
# from PIL import Image # No se usa si imagen_partitura_png es None
# import cairosvg # No se usa en generar_pdf_analisis

def generar_pdf_analisis(ejercicio_data, imagen_partitura_png=None):
    """
    Genera un PDF con el análisis del ejercicio de contrapunto usando ReportLab.
    Incluye errores de reglas y observaciones analíticas detalladas.
    """
    buffer = BytesIO()
    # Usar orientación vertical (portrait) para el informe de análisis
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Estilos
    styles = getSampleStyleSheet()
    style_h1 = styles['h1']
    style_h2 = styles['h2']
    style_h2.textColor = navy
    style_normal = styles['Normal']
    style_normal.leading = 14 # Espacio entre líneas
    style_error_marker = styles['Normal'] # Para el marcador X
    style_error_marker.textColor = red
    style_error_text = styles['Normal'] # Para el texto del error
    style_error_text.leading = 14
    style_info_marker = styles['Normal'] # Para el marcador i
    style_info_marker.textColor = black # O un gris oscuro
    style_info_text = styles['Normal'] # Para el texto de observación
    style_info_text.leading = 14
    style_warning_marker = styles['Normal']
    style_warning_marker.textColor = red # O un naranja/amarillo oscuro
    style_warning_text = styles['Normal']
    style_warning_text.leading = 14


    # Coordenadas y márgenes
    margin = 0.75 * inch
    y_position = height - margin
    max_width_content = width - 2 * margin # Ancho disponible para Paragraphs

    def check_new_page(current_y, element_height):
        """ Revisa si se necesita una nueva página y la crea si es así. """
        nonlocal y_position # Necesario para modificar y_position de la función externa
        nonlocal c # Necesario para modificar c de la función externa
        if current_y - element_height < margin:
            c.showPage()
            y_position = height - margin
            # Podrías añadir un pequeño header/footer en cada página si lo deseas
            # c.setFont("Helvetica", 8)
            # c.drawCentredString(width / 2, margin / 2, f"Página {c.getPageNumber()}")
            return True # Indica que se creó una nueva página
        return False

    # Título Principal
    p_titulo = Paragraph("Análisis Completo del Ejercicio", style_h1)
    p_w, p_h = p_titulo.wrapOn(c, max_width_content, height)
    if check_new_page(y_position, p_h): pass # Solo para asegurar y_position
    p_titulo.drawOn(c, margin, y_position - p_h)
    y_position -= (p_h + 0.2 * inch)

    # Información del ejercicio
    c.setFont("Helvetica", 10)
    info_text = f"<b>Especie:</b> {ejercicio_data.get('especie', 'No especificada')}<br/>" \
                f"<b>Fecha del Análisis:</b> {ejercicio_data.get('fecha', 'No especificada')}"
    p_info = Paragraph(info_text, style_normal)
    p_w, p_h = p_info.wrapOn(c, max_width_content, height)
    if check_new_page(y_position, p_h): pass
    p_info.drawOn(c, margin, y_position - p_h)
    y_position -= (p_h + 0.2 * inch)
    
    c.line(margin, y_position, width - margin, y_position)
    y_position -= 0.2 * inch

    # Sección de Errores de Reglas
    p_errores_titulo = Paragraph("<u>Errores de Reglas de Contrapunto:</u>", style_h2)
    p_w, p_h = p_errores_titulo.wrapOn(c, max_width_content, height)
    if check_new_page(y_position, p_h): pass
    p_errores_titulo.drawOn(c, margin, y_position - p_h)
    y_position -= (p_h + 0.1 * inch)

    errores = ejercicio_data.get("errores", [])
    if errores:
        for error_msg in errores:
            # Usar una tabla de un solo renglón para alinear el marcador y el texto
            error_paragraph = Paragraph(f"❌ {error_msg}", style_error_text)
            p_w, p_h = error_paragraph.wrapOn(c, max_width_content - 0.2*inch, height)
            if check_new_page(y_position, p_h): 
                 # Repetir título de sección si se desea en nueva página
                p_temp_title = Paragraph("<u>Errores de Reglas (continuación):</u>", style_h2)
                p_w_t, p_h_t = p_temp_title.wrapOn(c,max_width_content, height)
                p_temp_title.drawOn(c, margin, y_position - p_h_t); y_position -= (p_h_t + 0.1 * inch)
            error_paragraph.drawOn(c, margin + 0.2*inch, y_position - p_h)
            y_position -= (p_h + 0.05 * inch)
    else:
        p_no_errores = Paragraph("🎉 ¡No se encontraron errores en las reglas de contrapunto!", style_normal)
        p_w, p_h = p_no_errores.wrapOn(c, max_width_content, height)
        if check_new_page(y_position, p_h): pass
        p_no_errores.drawOn(c, margin + 0.2*inch, y_position - p_h)
        y_position -= (p_h + 0.1 * inch)
    
    y_position -= 0.3 * inch 

    # Sección de Observaciones Analíticas Detalladas
    observaciones = ejercicio_data.get("observaciones", [])
    if observaciones:
        p_obs_titulo = Paragraph("<u>Análisis Descriptivo Detallado:</u>", style_h2)
        p_w, p_h = p_obs_titulo.wrapOn(c, max_width_content, height)
        if check_new_page(y_position, p_h): pass
        p_obs_titulo.drawOn(c, margin, y_position - p_h)
        y_position -= (p_h + 0.1 * inch)

        for obs_line in observaciones:
            texto_obs_formateado = obs_line
            current_text_style = style_info_text
            
            if "---" in obs_line: 
                texto_obs_formateado = f"<b>{obs_line.replace('---', '').strip()}</b>" 
                # Podrías usar un estilo de heading más pequeño aquí si lo defines
            elif "Placeholder:" in obs_line or "no disponible" in obs_line or "Error" in obs_line.split(":")[0]:
                texto_obs_formateado = f"⚠️ {obs_line}"
                # Podrías usar un estilo específico para advertencias si lo defines
            else:
                texto_obs_formateado = f"ℹ️ {obs_line}"

            p_obs = Paragraph(texto_obs_formateado, current_text_style)
            p_w, p_h = p_obs.wrapOn(c, max_width_content - 0.2*inch, height)
            if check_new_page(y_position, p_h): 
                p_temp_title = Paragraph("<u>Análisis Descriptivo (continuación):</u>", style_h2)
                p_w_t, p_h_t = p_temp_title.wrapOn(c,max_width_content, height)
                p_temp_title.drawOn(c, margin, y_position - p_h_t); y_position -= (p_h_t + 0.1 * inch)
            p_obs.drawOn(c, margin + 0.2*inch, y_position - p_h)
            y_position -= (p_h + 0.05 * inch)
    else:
        p_no_obs = Paragraph("No hay observaciones analíticas adicionales disponibles.", style_normal)
        p_w, p_h = p_no_obs.wrapOn(c, max_width_content, height)
        if check_new_page(y_position, p_h): pass
        p_no_obs.drawOn(c, margin + 0.2*inch, y_position - p_h)
        y_position -= (p_h + 0.1 * inch)

    # Evaluación General
    y_position -= 0.2 * inch
    evaluacion_texto = ejercicio_data.get("evaluacion", "Evaluación no proporcionada.")
    p_eval = Paragraph(f"<b>Evaluación General:</b> {evaluacion_texto}", style_normal)
    p_w, p_h = p_eval.wrapOn(c, max_width_content, height)
    if check_new_page(y_position, p_h): pass
    p_eval.drawOn(c, margin, y_position - p_h)

    c.save()
    buffer.seek(0)
    return buffer

# Las funciones generar_pdf_partitura y crear_botones_descarga_pdf
# no son necesarias en este archivo si la generación de PDF de partitura
# se maneja exclusivamente en verovio_pdf.py.
# Si las necesitas por alguna otra razón, puedes mantenerlas.
