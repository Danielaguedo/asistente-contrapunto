# exportar_pdf.py (Versión Estable - Solo Texto, Fondo Marfil, Colores y Compases)
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, landscape # Mantenemos landscape por ahora
from reportlab.lib import colors
import datetime
import re
import os
import traceback 

# No necesitamos svglib ni nada de graphics.shapes para esta versión
# try:
#     from svglib.svglib import svg2rlg
#     SVGLIB_AVAILABLE = True
# except ImportError:
#     SVGLIB_AVAILABLE = False
#     def svg2rlg(path): return None 
# from reportlab.graphics.shapes import Drawing, Group 


def _header_footer_with_background(canvas, doc):
    canvas.saveState()
    ivory_color = colors.HexColor('#FFFAF0') 
    canvas.setFillColor(ivory_color)
    canvas.rect(0, 0, doc.width + doc.leftMargin + doc.rightMargin,
                doc.height + doc.topMargin + doc.bottomMargin,
                stroke=0, fill=1)
    footer_style_dict = dict(name='FooterStyleEstable', fontName='Helvetica', fontSize=8,
                              textColor=colors.darkgrey, alignment=TA_CENTER)
    footer_paragraph_style = ParagraphStyle(**footer_style_dict)
    footer_text = f"Fecha del Análisis: {doc.analysis_date_str} - Página {canvas.getPageNumber()}"
    p_footer = Paragraph(footer_text, footer_paragraph_style)
    p_footer.wrapOn(canvas, doc.width, doc.bottomMargin)
    p_footer.drawOn(canvas, doc.leftMargin, 0.5 * inch)
    canvas.restoreState()

def generar_pdf_analisis_estable(ejercicio_data, ruta_svg_partitura=None): # ruta_svg_partitura se ignora aquí
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), # Mantenemos landscape
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    doc.analysis_date_str = ejercicio_data.get('fecha', datetime.date.today().strftime("%Y-%m-%d"))
    styles = getSampleStyleSheet()

    # --- Definición de Estilos (Consistentes con los últimos que te gustaron) ---
    main_title_color = colors.HexColor('#002244'); section_heading_color = main_title_color
    section_heading2_color = colors.HexColor('#335577'); body_text_main_color = colors.HexColor('#333333')
    
    styles.add(ParagraphStyle(name='MyMainTitleEstable', fontName='Times-Bold', fontSize=20,textColor=main_title_color, alignment=TA_CENTER, spaceAfter=0.2*inch, spaceBefore=0.1*inch))
    styles.add(ParagraphStyle(name='MyExerciseInfoEstable', fontName='Helvetica', fontSize=9, leading=12,textColor=colors.dimgrey, alignment=TA_LEFT, spaceAfter=0.15*inch))
    
    # Usaremos el 'Heading1' base y lo modificaremos directamente si es necesario,
    # o crearemos uno nuevo para asegurar que no haya conflictos si se usa en otro lado.
    # Por simplicidad, vamos a crear uno nuevo para los títulos de sección.
    styles.add(ParagraphStyle(name='MySectionHeadingEstable', fontName='Times-Bold', fontSize=14, leading=18, textColor=section_heading_color, alignment=TA_LEFT, spaceBefore=0.2*inch, spaceAfter=0.1*inch, keepWithNext=1))
    
    styles.add(ParagraphStyle(name='MySectionHeading2Estable', fontName='Times-BoldItalic', fontSize=11, leading=14,textColor=section_heading2_color, alignment=TA_LEFT, spaceBefore=0.1*inch, spaceAfter=0.05*inch, leftIndent=0.2*inch, keepWithNext = 1))
    
    body_text_style_base = styles['Normal'] # Usamos 'Normal' como base
    body_text_style_base.fontName = 'Helvetica'; body_text_style_base.fontSize = 9; body_text_style_base.leading = 12; body_text_style_base.textColor = body_text_main_color; body_text_style_base.alignment = TA_JUSTIFY; body_text_style_base.spaceAfter = 0.05*inch
    styles.add(ParagraphStyle(name='MyBodyTextEstable', parent=body_text_style_base)) # Creamos un alias por si acaso

    styles.add(ParagraphStyle(name='MySuccessTextEstable', parent=styles['MyBodyTextEstable'], textColor=colors.HexColor('#C77700'),fontName='Helvetica-Bold')) # Naranja oscuro
    styles.add(ParagraphStyle(name='MyWarningTextEstable', parent=styles['MyBodyTextEstable'], textColor=colors.HexColor('#A02C2C'), fontName='Helvetica-Bold')) # Rojo oscuro

    styles.add(ParagraphStyle(name='MyErrorListItemEstable', fontName='Helvetica', fontSize=9, leading=12,textColor=colors.HexColor('#A02C2C'), leftIndent=0.2*inch, bulletIndent=0, bulletText='❌ ', spaceAfter=1))
    
    base_info_list_style_name = 'BaseInfoListItemEstable'
    styles.add(ParagraphStyle(name=base_info_list_style_name, fontName='Helvetica', fontSize=8, leading=11,textColor=body_text_main_color, leftIndent=0.2*inch, bulletIndent=0, bulletText='• ', spaceAfter=1))
    
    styles.add(ParagraphStyle(name='ContraryMovementStyleEstable', parent=styles[base_info_list_style_name], textColor=colors.HexColor('#B9770E'))) 
    styles.add(ParagraphStyle(name='ParallelMovementStyleEstable', parent=styles[base_info_list_style_name], textColor=colors.HexColor('#943126'))) 
    styles.add(ParagraphStyle(name='OtherMovementStyleEstable', parent=styles[base_info_list_style_name], textColor=colors.HexColor('#4A4A4A'))) 
    styles.add(ParagraphStyle(name='MeasureInfoSubtleEstable', fontName='Helvetica-Oblique', fontSize=7,textColor=colors.dimgrey, leading=8, leftIndent=0.4*inch, spaceBefore=-1, spaceAfter=1))

    story = []

    story.append(Paragraph("Análisis de Ejercicio de Contrapunto", styles['MyMainTitleEstable']))
    info_text_data = f"<b>Especie:</b> {ejercicio_data.get('especie', 'No especificada')}<br/>" \
                     f"<b>Fecha del Análisis:</b> {doc.analysis_date_str}"
    story.append(Paragraph(info_text_data, styles['MyExerciseInfoEstable']))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceBefore=0.1*inch, spaceAfter=0.2*inch))

    # --- SECCIÓN DE PARTITURA SVG ELIMINADA ---

    story.append(Paragraph("Diagnóstico General", styles['MySectionHeadingEstable']))
    errores = ejercicio_data.get("errores", [])
    evaluacion_general_texto = ejercicio_data.get("evaluacion", "Evaluación no disponible.")
    if not errores:
        story.append(Paragraph(f"🎉 ¡Excelente! {evaluacion_general_texto}", styles['MySuccessTextEstable']))
    else:
        story.append(Paragraph(f"⚠️ Atención: {evaluacion_general_texto}", styles['MyWarningTextEstable']))
    story.append(Spacer(1, 0.1*inch))

    if errores:
        story.append(Paragraph("Correcciones Necesarias: Errores de Reglas", styles['MySectionHeadingEstable']))
        for error_msg in errores:
            story.append(Paragraph(error_msg, styles['MyErrorListItemEstable']))
        story.append(Spacer(1, 0.1*inch))

    observaciones = ejercicio_data.get("observaciones", [])
    mov_melodico_violin_data, mov_melodico_viola_data, mov_entre_voces_data, patrones_especificos_data = [], [], [], []
    current_section = None
    measure_pattern = re.compile(r"^(Compás\s*\d+\s*(?:a\s*\d+)?|Del\s*tiempo\s*\d+\s*(?:al\s*\d+)?)\s*:\s*", re.IGNORECASE)
    for obs_line in observaciones:
        obs_line_stripped = obs_line.strip()
        measure_info_str, main_content_str = "", obs_line_stripped
        match = measure_pattern.match(obs_line_stripped)
        if match:
            measure_info_str = match.group(1).replace("Del tiempo", "T.").replace("Compás", "C.")
            main_content_str = measure_pattern.sub("", obs_line_stripped).strip()
        main_content_str = main_content_str.replace("Violin - ", "").replace("Viola - ", "").replace("Entre voces - ", "")
        if "Movimiento Melódico del Violin" in obs_line_stripped or "Movimiento Melódico del Contrapunto" in obs_line_stripped : current_section = "violin"; continue
        elif "Movimiento Melódico del Viola" in obs_line_stripped or "Movimiento Melódico del Cantus Firmus" in obs_line_stripped: current_section = "viola"; continue
        elif "Movimiento Entre Voces" in obs_line_stripped: current_section = "entre_voces"; continue
        elif "Patrones Específicos" in obs_line_stripped: current_section = "patrones"; continue
        if current_section == "violin": mov_melodico_violin_data.append((measure_info_str, main_content_str))
        elif current_section == "viola": mov_melodico_viola_data.append((measure_info_str, main_content_str))
        elif current_section == "entre_voces": mov_entre_voces_data.append((measure_info_str, main_content_str))
        elif current_section == "patrones": patrones_especificos_data.append((measure_info_str, main_content_str))
            
    story.append(Paragraph("Dinámica entre Voces: Movimiento Armónico/Contrapuntístico", styles['MySectionHeadingEstable']))
    if mov_entre_voces_data:
        for measure_info, mov_text_original in mov_entre_voces_data:
            mov_text_for_comparison = mov_text_original.replace("<b>","").replace("</b>","")
            style_to_use = styles['OtherMovementStyleEstable']
            if "Movimiento Contrary" in mov_text_for_comparison: style_to_use = styles['ContraryMovementStyleEstable']
            elif "Movimiento Parallel" in mov_text_for_comparison: style_to_use = styles['ParallelMovementStyleEstable']
            story.append(Paragraph(mov_text_original, style_to_use))
            if measure_info: story.append(Paragraph(measure_info, styles['MeasureInfoSubtleEstable']))
    else:
        story.append(Paragraph("No se generó análisis de movimiento entre voces.", styles['MyBodyTextEstable']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("Perfil de las Voces: Diseño Melódico Individual", styles['MySectionHeadingEstable']))
    if mov_melodico_violin_data:
        story.append(Paragraph("Contrapunto (Voz Superior):", styles['MySectionHeading2Estable']))
        for measure_info, mov_text in mov_melodico_violin_data:
             story.append(Paragraph(mov_text, styles[base_info_list_style_name])) # Usar el nombre de la variable
             if measure_info: story.append(Paragraph(measure_info, styles['MeasureInfoSubtleEstable']))
        story.append(Spacer(1, 0.05*inch))
    if mov_melodico_viola_data:
        story.append(Paragraph("Cantus Firmus (Voz Inferior):", styles['MySectionHeading2Estable']))
        for measure_info, mov_text in mov_melodico_viola_data:
            story.append(Paragraph(mov_text, styles[base_info_list_style_name])) # Usar el nombre de la variable
            if measure_info: story.append(Paragraph(measure_info, styles['MeasureInfoSubtleEstable']))
    if not mov_melodico_violin_data and not mov_melodico_viola_data:
         story.append(Paragraph("No se generó análisis de movimiento melódico.", styles['MyBodyTextEstable']))
    story.append(Spacer(1, 0.1*inch))

    if patrones_especificos_data:
        story.append(Paragraph("Observaciones Adicionales y Patrones", styles['MySectionHeadingEstable']))
        for measure_info, pat_text in patrones_especificos_data:
            if "No se identificaron patrones especiales" in pat_text:
                 story.append(Paragraph(pat_text, styles['MyBodyTextEstable']))
            else:
                 story.append(Paragraph(pat_text, styles[base_info_list_style_name])) # Usar el nombre de la variable
            if measure_info: story.append(Paragraph(measure_info, styles['MeasureInfoSubtleEstable']))
    
    try:
        doc.build(story, onFirstPage=_header_footer_with_background, onLaterPages=_header_footer_with_background)
    except Exception as e_doc_build: 
        print(f"ERROR CRÍTICO al construir el documento PDF final: {e_doc_build}") 
        traceback.print_exc() 
        
    buffer.seek(0)
    return buffer