# exportar_pdf.py (Ajuste de título para Segunda Especie)

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
import datetime
import re
import os
import traceback

# _header_footer_info_with_background (sin cambios)
def _header_footer_info_with_background(canvas, doc):
    canvas.saveState()
    ivory_color = colors.HexColor('#FFFAF0') 
    canvas.setFillColor(ivory_color)
    canvas.rect(0, 0, doc.width + doc.leftMargin + doc.rightMargin,
                doc.height + doc.topMargin + doc.bottomMargin,
                stroke=0, fill=1)
    header_info_style_dict = dict(name='HeaderInfoStyle', fontName='Helvetica', fontSize=8,
                                  textColor=colors.dimgrey, alignment=TA_RIGHT)
    header_info_paragraph_style = ParagraphStyle(**header_info_style_dict)
    especie_texto = f"Especie: {getattr(doc, 'ejercicio_especie', 'No especificada')}"
    fecha_texto = f"Fecha: {getattr(doc, 'analysis_date_str', 'N/A')}"
    p_especie = Paragraph(especie_texto, header_info_paragraph_style)
    p_fecha = Paragraph(fecha_texto, header_info_paragraph_style)
    available_width_for_header_info = doc.width / 2 
    p_especie_width, p_especie_height = p_especie.wrapOn(canvas, available_width_for_header_info, doc.topMargin)
    p_fecha_width, p_fecha_height = p_fecha.wrapOn(canvas, available_width_for_header_info, doc.topMargin)
    y_position_especie = doc.height + doc.topMargin - 0.4 * inch 
    y_position_fecha = y_position_especie - p_especie_height - (0.05 * inch) 
    max_text_width = max(p_especie_width, p_fecha_width)
    x_position = doc.leftMargin + doc.width - max_text_width
    if x_position < doc.leftMargin:
        x_position = doc.leftMargin + doc.width - available_width_for_header_info
    p_especie.drawOn(canvas, x_position, y_position_especie)
    p_fecha.drawOn(canvas, x_position, y_position_fecha)
    footer_style_dict = dict(name='FooterStyleEstable', fontName='Helvetica', fontSize=7.5,
                             textColor=colors.Color(0.6, 0.6, 0.6), alignment=TA_CENTER)
    footer_paragraph_style = ParagraphStyle(**footer_style_dict)
    footer_text = f"Fecha del Análisis: {getattr(doc, 'analysis_date_str', 'N/A')}   •   Página {canvas.getPageNumber()}   •   Asistente de Contrapunto"
    p_footer = Paragraph(footer_text, footer_paragraph_style)
    footer_y_position = doc.bottomMargin * 0.4 
    p_footer.wrapOn(canvas, doc.width, doc.bottomMargin)
    p_footer.drawOn(canvas, doc.leftMargin, footer_y_position)
    canvas.restoreState()

def generar_pdf_analisis_estable(ejercicio_data):
    buffer = BytesIO()
    current_top_margin = 0.5 * inch 
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=current_top_margin, 
                            bottomMargin=0.75*inch) 
    
    doc.analysis_date_str = ejercicio_data.get('fecha', datetime.date.today().strftime("%Y-%m-%d"))
    doc.ejercicio_especie = ejercicio_data.get('especie', 'No especificada')

    styles = getSampleStyleSheet()
    # ... (Tu definición de estilos existente - MyMainTitleEstable, MySectionHeadingEstable, etc. sin cambios) ...
    main_title_color = colors.HexColor('#002244'); section_heading_color = main_title_color; section_heading2_color = colors.HexColor('#2E4053'); body_text_main_color = colors.HexColor('#1C1C1C')
    styles.add(ParagraphStyle(name='MyMainTitleEstable', fontName='Helvetica-Bold', fontSize=20, textColor=main_title_color, alignment=TA_CENTER, spaceAfter=0.2*inch, spaceBefore=0.1*inch))
    styles.add(ParagraphStyle(name='MySectionHeadingEstable', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=section_heading_color, alignment=TA_LEFT, spaceBefore=0.25*inch, spaceAfter=0.1*inch, keepWithNext=1))
    styles.add(ParagraphStyle(name='MySectionHeading2Estable', fontName='Helvetica-Oblique', fontSize=11, leading=14, textColor=section_heading2_color, alignment=TA_LEFT, spaceBefore=0.15*inch, spaceAfter=0.05*inch, leftIndent=0.2*inch, keepWithNext=1))
    body_text_style_base = ParagraphStyle(name='BodyTextBase', fontName='Helvetica', fontSize=9, leading=13, textColor=body_text_main_color, alignment=TA_JUSTIFY, spaceAfter=0.05*inch)
    styles.add(ParagraphStyle(name='MyBodyTextEstable', parent=body_text_style_base))
    styles.add(ParagraphStyle(name='MySuccessTextEstable', parent=styles['MyBodyTextEstable'], textColor=colors.HexColor('#1E8449'), fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='MyWarningTextEstable', parent=styles['MyBodyTextEstable'], textColor=colors.HexColor('#B71C1C'), fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='MyErrorListItemEstable', fontName='Helvetica', fontSize=9, leading=13, textColor=colors.HexColor('#C0392B'), leftIndent=0.25*inch, bulletIndent=0.1*inch, bulletText='• ', spaceAfter=2))
    base_info_list_style_name = 'BaseInfoListItemEstable'
    styles.add(ParagraphStyle(name=base_info_list_style_name, fontName='Helvetica', fontSize=8.5, leading=12, textColor=body_text_main_color, leftIndent=0.25*inch, bulletIndent=0.1*inch, bulletText='- ', spaceAfter=2))
    styles.add(ParagraphStyle(name='ContraryMovementStyleEstable', parent=styles[base_info_list_style_name], textColor=colors.HexColor('#AF601A'))) 
    styles.add(ParagraphStyle(name='ParallelMovementStyleEstable', parent=styles[base_info_list_style_name], textColor=colors.HexColor('#78281F'))) 
    styles.add(ParagraphStyle(name='SimilarMovementStyleEstable', parent=styles[base_info_list_style_name], textColor=colors.HexColor('#154360')))
    styles.add(ParagraphStyle(name='ObliqueMovementStyleEstable', parent=styles[base_info_list_style_name], textColor=colors.HexColor('#4E342E')))
    styles.add(ParagraphStyle(name='OtherMovementStyleEstable', parent=styles[base_info_list_style_name], textColor=colors.HexColor('#424949'))) 
    styles.add(ParagraphStyle(name='MeasureInfoSubtleEstable', fontName='Helvetica-Oblique', fontSize=7.5, textColor=colors.darkgrey, leading=9, leftIndent=0, spaceBefore=0, spaceAfter=3, firstLineIndent=0))


    story = []
    story.append(Paragraph("Análisis de Ejercicio de Contrapunto", styles['MyMainTitleEstable']))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceBefore=0.05*inch, spaceAfter=0.2*inch))

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
    mov_melodico_cp_data, mov_melodico_cf_data, mov_entre_voces_data, patrones_especificos_data = [], [], [], [] # Renombrado violin/viola a cp/cf
    
    current_section = None
    measure_pattern = re.compile(r"^(Compás\s*\d+\s*(?:(?:a|-)\s*\d+)?|Del\s*tiempo\s*\d+\s*(?:(?:al|-)\s*\d+)?)\s*:\s*", re.IGNORECASE)
    
    for obs_line in observaciones:
        obs_line_stripped = obs_line.strip()
        if not obs_line_stripped: continue

        # Lógica de asignación de sección (ajustada para ser más genérica con CP/CF)
        # El nombre de la parte vendrá de `cp_part_name_display` o `cf_part_name_display` en las observaciones
        if "Movimiento Melódico del" in obs_line_stripped:
            if "Contrapunto" in obs_line_stripped or ejercicio_data.get("cp_part_name", "Contrapunto") in obs_line_stripped : # Asumimos que cp_part_name podría pasarse en ejercicio_data
                current_section = "cp_melodico"; continue
            elif "Cantus Firmus" in obs_line_stripped or ejercicio_data.get("cf_part_name", "Cantus Firmus") in obs_line_stripped:
                current_section = "cf_melodico"; continue
        elif "Movimiento Entre Voces" in obs_line_stripped: # Esto capturará "Movimiento Entre Voces (entre Tiempos Fuertes)"
            current_section = "entre_voces"; continue
        elif "Patrones Específicos" in obs_line_stripped:
            current_section = "patrones"; continue
        
        measure_info_str, main_content_str = "", obs_line_stripped
        match = measure_pattern.match(obs_line_stripped)
        if match:
            measure_info_str = match.group(1).replace("Del tiempo", "T.").replace("Compás", "C.")
            main_content_str = measure_pattern.sub("", obs_line_stripped).strip()
        
        # Eliminar prefijos genéricos si aún están en main_content_str
        main_content_str = re.sub(r"^(?:.*?Contrapunto\s*-\s*|.*?Cantus Firmus\s*-\s*|Entre voces\s*-\s*)", "", main_content_str, flags=re.IGNORECASE)


        if current_section == "cp_melodico": mov_melodico_cp_data.append((measure_info_str, main_content_str))
        elif current_section == "cf_melodico": mov_melodico_cf_data.append((measure_info_str, main_content_str))
        elif current_section == "entre_voces": mov_entre_voces_data.append((measure_info_str, main_content_str))
        elif current_section == "patrones": patrones_especificos_data.append((measure_info_str, main_content_str))

    # --- TÍTULO CONDICIONAL PARA MOVIMIENTO ENTRE VOCES ---
    especie_actual = ejercicio_data.get("especie", "Primera") 
    if especie_actual == "Segunda":
        titulo_seccion_mov_entre_voces = "Movimiento entre Tiempos Fuertes"
    else: # Para Primera Especie o si no se especifica
        titulo_seccion_mov_entre_voces = "Dinámica entre Voces: Movimiento Armónico/Contrapuntístico"
    # --- FIN DE TÍTULO CONDICIONAL ---

    story.append(Paragraph(titulo_seccion_mov_entre_voces, styles['MySectionHeadingEstable']))
    if mov_entre_voces_data:
        for measure_info, mov_text_original in mov_entre_voces_data:
            item_content = []
            mov_text_for_comparison = mov_text_original.replace("<b>","").replace("</b>","") # Para comparación sin formato
            style_key = 'OtherMovementStyleEstable' # Estilo por defecto
            if "Movimiento Contrary" in mov_text_for_comparison: style_key = 'ContraryMovementStyleEstable'
            elif "Movimiento Parallel" in mov_text_for_comparison: style_key = 'ParallelMovementStyleEstable'
            elif "Movimiento Similar" in mov_text_for_comparison: style_key = 'SimilarMovementStyleEstable'
            elif "Movimiento Oblique" in mov_text_for_comparison: style_key = 'ObliqueMovementStyleEstable'
            item_content.append(Paragraph(mov_text_original, styles[style_key]))
            if measure_info:
                item_content.append(Paragraph(f"<i>({measure_info})</i>", styles['MeasureInfoSubtleEstable']))
            story.append(KeepTogether(item_content))
    else:
        story.append(Paragraph(f"No se generó análisis de {titulo_seccion_mov_entre_voces.lower()}.", styles['MyBodyTextEstable']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("Perfil de las Voces: Diseño Melódico Individual", styles['MySectionHeadingEstable']))
    
    def add_melodic_movement_section(title, data, story_list, styles_dict, base_style_name):
        if data:
            story_list.append(Paragraph(title, styles_dict['MySectionHeading2Estable']))
            for measure_info, mov_text in data:
                item_content = [Paragraph(mov_text, styles_dict[base_style_name])]
                if measure_info:
                    item_content.append(Paragraph(f"<i>({measure_info})</i>", styles_dict['MeasureInfoSubtleEstable']))
                story_list.append(KeepTogether(item_content))
            story_list.append(Spacer(1, 0.05*inch))

    # Usar nombres de parte más genéricos o pasarlos desde ejercicio_data si es necesario
    cp_display_name_pdf = ejercicio_data.get("cp_part_name", "Contrapunto (Voz Superior)") 
    cf_display_name_pdf = ejercicio_data.get("cf_part_name", "Cantus Firmus (Voz Inferior)")

    add_melodic_movement_section(f"{cp_display_name_pdf}:", mov_melodico_cp_data, story, styles, base_info_list_style_name)
    add_melodic_movement_section(f"{cf_display_name_pdf}:", mov_melodico_cf_data, story, styles, base_info_list_style_name)

    if not mov_melodico_cp_data and not mov_melodico_cf_data:
        story.append(Paragraph("No se generó análisis de movimiento melódico.", styles['MyBodyTextEstable']))
    story.append(Spacer(1, 0.1*inch))

    if patrones_especificos_data: # Esta sección se omitirá si no hay datos, lo cual es bueno para 2da especie por ahora
        story.append(Paragraph("Observaciones Adicionales y Patrones", styles['MySectionHeadingEstable']))
        for measure_info, pat_text in patrones_especificos_data:
            item_content = []
            if "No se identificaron patrones especiales" in pat_text: item_content.append(Paragraph(pat_text, styles['MyBodyTextEstable']))
            else: item_content.append(Paragraph(pat_text, styles[base_info_list_style_name]))
            if measure_info: item_content.append(Paragraph(f"<i>({measure_info})</i>", styles['MeasureInfoSubtleEstable']))
            if item_content: story.append(KeepTogether(item_content))
    
    try:
        doc.build(story, onFirstPage=_header_footer_info_with_background, 
                  onLaterPages=_header_footer_info_with_background)
    except Exception as e_doc_build:
        print(f"ERROR CRÍTICO al construir el documento PDF final: {e_doc_build}")
        traceback.print_exc()
    
    buffer.seek(0)
    return buffer