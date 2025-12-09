# segunda_especie/anotador_svg_segunda.py (v29 - Alineación Perfecta / Pivote Fijo)

import xml.etree.ElementTree as ET
from music21 import interval as m21interval 
import os 
import re 

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace('', SVG_NS) 
NAMESPACES_MAP = {'svg': SVG_NS}

def _add_arrow(svg_root, ns, id="arrowhead", color="black"):
    defs = svg_root.find(".//svg:defs", ns)
    if defs is None:
        defs = ET.Element(f"{{{ns['svg']}}}defs")
        svg_root.insert(0, defs)
    if defs.find(f".//svg:marker[@id='{id}']", ns) is not None: return
    
    m = ET.Element(f"{{{ns['svg']}}}marker", {
        "id": id, "viewBox": "0 0 10 10", "refX": "8", "refY": "5",
        "markerWidth": "8", "markerHeight": "8", "orient": "auto-start-reverse"
    })
    ET.SubElement(m, f"{{{ns['svg']}}}path", {"d": "M0,2 L8,5 L0,8 Z", "fill": color})
    defs.append(m)

def _draw_line(group, c1, c2, ns, color="black", width="2.5", arrow_id=None):
    if not c1 or not c2 or (c1['x'] == c2['x'] and c1['y'] == c2['y']): return
    attr = {"x1": str(c1['x']), "y1": str(c1['y']), "x2": str(c2['x']), "y2": str(c2['y']),
            "stroke": color, "stroke-width": width, "stroke-opacity": "0.7"}
    if arrow_id: attr["marker-end"] = f"url(#{arrow_id})"
    ET.SubElement(group, f"{{{ns['svg']}}}line", attr)

def _get_interval_text(interval_obj):
    if not interval_obj: return "?"
    simple = str(interval_obj.simpleName)
    num = "".join(filter(str.isdigit, simple)) or "?"
    if interval_obj.generic.value > 8:
        return f"{num}({interval_obj.generic.value})"
    return num

def _calc_motion(n_cp_curr, n_cf_curr, n_cp_prev, n_cf_prev):
    try:
        cp1, cp2 = n_cp_prev.pitch.ps, n_cp_curr.pitch.ps
        cf1, cf2 = n_cf_prev.pitch.ps, n_cf_curr.pitch.ps
    except: return None, None
    
    d_cp = 1 if cp2 > cp1 else (-1 if cp2 < cp1 else 0)
    d_cf = 1 if cf2 > cf1 else (-1 if cf2 < cf1 else 0)

    if d_cp == 0 or d_cf == 0: return "O", "#6C757D" 
    if d_cp == d_cf:
        try:
            i1 = m21interval.Interval(n_cf_prev, n_cp_prev).simpleName
            i2 = m21interval.Interval(n_cf_curr, n_cp_curr).simpleName
            if i1 == i2: return "P", "#D93025" 
        except: pass
        return "D", "#E69138" 
    return "C", "#28A745" 

def anotar_svg_intervalos_2da_especie(svg_str, datos_int, coords, ids_notas_rojas=None, datos_movimiento_melodico_cp=None):
    print("\n--- DEBUG (Anotador 2da): Iniciando v29 (Alineación Fija) ---")
    if not datos_int or not coords: return svg_str
    ids_red = set(ids_notas_rojas or [])

    try:
        root = ET.fromstring(svg_str.split('?>', 1)[-1].strip() if '<?xml' in svg_str else svg_str)
    except: return svg_str

    _add_arrow(root, NAMESPACES_MAP, "arrow", "black")
    group = root.find(".//svg:g[@class='page-margin']", NAMESPACES_MAP) or root

    # --- CONFIGURACIÓN VISUAL ---
    FONT_SIZE = 180  
    Y_OFFSET_NUM = -(FONT_SIZE * 0.4)
    Y_OFFSET_LETRA = -(FONT_SIZE * 0.85)
    X_OFFSET = FONT_SIZE * 0.4

    prev_cp, prev_cf = None, None
    
    # VARIABLE DE CONTROL PARA ALINEACIÓN
    fixed_y_base = None 

    # 1. DIBUJAR NÚMEROS Y LETRAS
    for cp, cf, inter in datos_int:
        c_cp, c_cf = coords.get(getattr(cp,'id',None)), coords.get(getattr(cf,'id',None))
        if not c_cp or not c_cf: continue
        
        # LÓGICA DE PIVOTE:
        # Si es la primera vez (fixed_y_base es None), calculamos la altura.
        # Si no, usamos la que ya calculamos.
        if fixed_y_base is None:
            fixed_y_base = (c_cp['y'] + c_cf['y']) / 2 + Y_OFFSET_NUM
        
        # Usamos siempre la altura fija
        y_final = fixed_y_base
        x = c_cp['x'] + X_OFFSET
        
        col = "#D93025" if getattr(cp,'id',None) in ids_red else "#0055AA"
        
        # Número Intervalo
        txt = ET.SubElement(group, f"{{{SVG_NS}}}text", {
            "x": str(x), "y": str(y_final), "font-family": "Arial", 
            "font-size": str(FONT_SIZE), "fill": col, "text-anchor": "middle"
        })
        txt.text = _get_interval_text(inter)
        
        # Letra Movimiento (C, P, D, O)
        if prev_cp and prev_cf:
            letra, col_mov = _calc_motion(cp, cf, prev_cp, prev_cf)
            if letra:
                l_txt = ET.SubElement(group, f"{{{SVG_NS}}}text", {
                    "x": str(x), "y": str(y_final + Y_OFFSET_LETRA), # Usamos también y_final
                    "font-family": "Arial",
                    "font-size": str(FONT_SIZE * 0.8), "fill": col_mov, "font-weight": "bold", "text-anchor": "middle"
                })
                l_txt.text = letra
        prev_cp, prev_cf = cp, cf

    # 2. FLECHAS
    if datos_movimiento_melodico_cp:
        for id1, id2, dir_str in datos_movimiento_melodico_cp:
            c1, c2 = coords.get(id1), coords.get(id2)
            if c1 and c2:
                col = "green" if dir_str == "ascendente" else "red"
                _draw_line(group, c1, c2, NAMESPACES_MAP, col, "4.0", "arrow")

    return ET.tostring(root, encoding="unicode")