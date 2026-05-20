#!/usr/bin/env python3
"""
Generador de Reporte de Rendimiento Mensual — Calace Propiedades
"""
import argparse
import json
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    Table, TableStyle, Image as RLImage,
)
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Circle, Polygon

# ── Constantes ─────────────────────────────────────────────────────────────
INMOBILIARIA = "Calace Propiedades"

MESES_ES = {
    "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
    "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
    "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre",
}

# ── Colores ────────────────────────────────────────────────────────────────
BG_COLOR     = colors.HexColor("#fafbf3")
INK          = colors.HexColor("#1a1208")
MUTED        = colors.HexColor("#7a7060")
DOT_COLOR    = colors.HexColor("#bdb6a4")
BAND_BG      = colors.HexColor("#e8e3d3")
BAND_LINE    = colors.HexColor("#a89e87")
ROW_ALT      = colors.HexColor("#f2eee0")
TABLE_BORDER = colors.HexColor("#d4cfc4")
DECO_COLOR   = colors.HexColor("#c9b88a")
PIN_COLOR    = colors.HexColor("#7a6040")

# ── Layout ─────────────────────────────────────────────────────────────────
MARGIN_LR = 2.0 * cm
MARGIN_TOP = 1.8 * cm
MARGIN_BOT = 2.0 * cm
DOC_WIDTH = A4[0] - 2 * MARGIN_LR


# ── Pin (chinche) dibujado vectorialmente ──────────────────────────────────
def make_pin_drawing(size=14):
    """Mini chinche vectorial: círculo (cabeza) + triángulo (cuerpo)."""
    d = Drawing(size, size)
    # Cuerpo: triángulo apuntando hacia abajo
    d.add(Polygon(
        points=[
            size * 0.30, size * 0.55,
            size * 0.70, size * 0.55,
            size * 0.50, size * 0.08,
        ],
        fillColor=PIN_COLOR, strokeColor=None,
    ))
    # Cabeza: círculo arriba
    d.add(Circle(
        size * 0.50, size * 0.70, size * 0.22,
        fillColor=PIN_COLOR, strokeColor=None,
    ))
    return d


# ── Estilos ────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "RTitle", parent=base["Normal"],
        fontSize=30, fontName="Helvetica-Bold", textColor=INK,
        alignment=TA_LEFT, spaceAfter=4, leading=34,
    )
    subtitle = ParagraphStyle(
        "RSubtitle", parent=base["Normal"],
        fontSize=11, fontName="Helvetica", textColor=INK,
        alignment=TA_LEFT, spaceAfter=22, leading=16,
    )
    kpi_label = ParagraphStyle(
        "RKpiLabel", parent=base["Normal"],
        fontSize=13, fontName="Helvetica-Bold", textColor=INK,
        alignment=TA_LEFT, leading=18,
    )
    kpi_value = ParagraphStyle(
        "RKpiValue", parent=base["Normal"],
        fontSize=22, fontName="Helvetica", textColor=INK,
        alignment=TA_RIGHT, leading=24,
    )
    kpi_dots = ParagraphStyle(
        "RKpiDots", parent=base["Normal"],
        fontSize=8, fontName="Helvetica", textColor=DOT_COLOR,
        alignment=TA_LEFT, leading=12,
    )
    section = ParagraphStyle(
        "RSection", parent=base["Normal"],
        fontSize=12, fontName="Helvetica-Bold", textColor=INK,
        alignment=TA_LEFT, leading=14,
    )
    body = ParagraphStyle(
        "RBody", parent=base["Normal"],
        fontSize=10, fontName="Helvetica", textColor=INK,
        alignment=TA_JUSTIFY, leading=15, spaceAfter=4,
    )
    bullet = ParagraphStyle(
        "RBullet", parent=base["Normal"],
        fontSize=10, fontName="Helvetica", textColor=INK,
        alignment=TA_LEFT, leading=15, spaceAfter=4,
        leftIndent=16, bulletIndent=0,
    )
    return title, subtitle, kpi_label, kpi_value, kpi_dots, section, body, bullet


# ── Callback de página (fondo + decoración) ────────────────────────────────
def _draw_page_background(canvas, doc):
    canvas.saveState()
    # Fondo crema
    canvas.setFillColor(BG_COLOR)
    canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

    # Decoración: 3 curvas Bezier finas en esquina superior derecha
    w, h = A4
    canvas.setStrokeColor(DECO_COLOR)
    canvas.setLineWidth(0.7)
    canvas.bezier(
        w - 4.0 * cm, h - 0.3 * cm,
        w - 2.2 * cm, h - 1.6 * cm,
        w - 1.4 * cm, h - 0.6 * cm,
        w - 0.3 * cm, h - 2.3 * cm,
    )
    canvas.setLineWidth(0.5)
    canvas.bezier(
        w - 3.2 * cm, h - 0.4 * cm,
        w - 1.8 * cm, h - 1.4 * cm,
        w - 1.0 * cm, h - 0.4 * cm,
        w - 0.2 * cm, h - 1.7 * cm,
    )
    canvas.setLineWidth(0.4)
    canvas.bezier(
        w - 2.0 * cm, h - 0.35 * cm,
        w - 1.3 * cm, h - 1.1 * cm,
        w - 0.7 * cm, h - 0.7 * cm,
        w - 0.25 * cm, h - 1.4 * cm,
    )
    canvas.restoreState()


# ── Helpers ────────────────────────────────────────────────────────────────
def _escape(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def _band(text, section_s):
    """Banda con fondo gris claro y título de sección."""
    t = Table(
        [[Paragraph(text, section_s)]],
        colWidths=[DOC_WIDTH],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BAND_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def _kpi_row(label, value, styles):
    title_s, subtitle_s, kpi_label_s, kpi_value_s, kpi_dots_s, _, _, _ = styles
    dots = "·" * 100
    cell_dots = Paragraph(
        f'<font color="#bdb6a4">{dots}</font>',
        kpi_dots_s,
    )
    row = [[
        Paragraph(label, kpi_label_s),
        cell_dots,
        Paragraph(str(value), kpi_value_s),
    ]]
    t = Table(row, colWidths=[5.5 * cm, 8.3 * cm, 3.2 * cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def _parse_comentarios(text, body_s, bullet_s):
    """Respeta saltos de línea. Líneas que empiezan con '-' se renderizan como bullets."""
    paragraphs = []
    lines = text.split("\n")
    buf = []

    def flush_buf():
        if buf:
            paragraphs.append(Paragraph(" ".join(buf).strip(), body_s))
            buf.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush_buf()
            paragraphs.append(Spacer(1, 4))
            continue
        if stripped.startswith("-"):
            flush_buf()
            content = stripped.lstrip("-").strip()
            paragraphs.append(
                Paragraph(f"•&nbsp;&nbsp;{_escape(content)}", bullet_s)
            )
        else:
            buf.append(_escape(stripped))
    flush_buf()
    return paragraphs


def _format_mes(mes_raw):
    """Convierte '2026-05' o '05/2026' a 'Mayo 2026'. Devuelve '' si no se puede parsear."""
    if not mes_raw:
        return ""
    mes_raw = mes_raw.strip()
    # Formato HTML <input type=month>: YYYY-MM
    if "-" in mes_raw and len(mes_raw) >= 7:
        try:
            anio, mm = mes_raw.split("-")[:2]
            nombre = MESES_ES.get(mm.zfill(2), "")
            if nombre:
                return f"{nombre} {anio}"
        except Exception:
            pass
    # Formato MM/YYYY
    if "/" in mes_raw:
        try:
            mm, anio = mes_raw.split("/")
            nombre = MESES_ES.get(mm.zfill(2), "")
            if nombre:
                return f"{nombre} {anio}"
        except Exception:
            pass
    return mes_raw


# ── Builder ────────────────────────────────────────────────────────────────
def build_pdf(data, output_path):
    doc = BaseDocTemplate(
        output_path, pagesize=A4,
        rightMargin=MARGIN_LR, leftMargin=MARGIN_LR,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOT,
        title="Reporte de Rendimiento — Calace Propiedades",
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height, id="main",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([
        PageTemplate(id="bg", frames=[frame], onPage=_draw_page_background),
    ])

    styles = make_styles()
    (title_s, subtitle_s, kpi_label_s, kpi_value_s, kpi_dots_s,
     section_s, body_s, bullet_s) = styles

    # Datos
    direccion        = str(data.get("direccion", "")).strip()
    barrio           = str(data.get("barrio", "")).strip()
    mes_raw          = str(data.get("mes", "")).strip()
    exposicion_total = str(data.get("exposicion_total", "")).strip() or "0"
    consultas_total  = str(data.get("consultas_totales", "")).strip() or "0"
    visitas_total    = str(data.get("visitas_totales", "")).strip() or "0"
    portales         = data.get("portales", []) or []
    comentarios      = str(data.get("comentarios", "")).strip()

    mes_formateado = _format_mes(mes_raw)

    story = []

    # ── Logo centrado (PNG transparente, sin fondo blanco) ─────────────────
    here = os.path.dirname(os.path.abspath(__file__))
    logo_png = os.path.join(here, "logo_calace.png")
    logo_jpg = os.path.join(here, "logo_calace.jpg")
    logo_path = logo_png if os.path.exists(logo_png) else logo_jpg
    if os.path.exists(logo_path):
        # PNG: relación 1200x553 ≈ 2.17:1
        logo = RLImage(logo_path, width=7.0 * cm, height=3.22 * cm)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 16))

    # ── Título ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Rendimiento", title_s))

    # ── Subtítulo: dirección - barrio (+ mes opcional) ─────────────────────
    sub_parts = []
    if direccion:
        sub_parts.append(_escape(direccion))
    if barrio:
        sub_parts.append(_escape(barrio))
    sub_main = "  -  ".join(sub_parts)
    if mes_formateado:
        sub_main = (sub_main + "   ·   " if sub_main else "") + f"<i>{_escape(mes_formateado)}</i>"
    if sub_main:
        story.append(Paragraph(sub_main, subtitle_s))

    # ── KPIs ───────────────────────────────────────────────────────────────
    story.append(_kpi_row("Exposición Total", exposicion_total, styles))
    story.append(Spacer(1, 4))
    story.append(_kpi_row("Consultas Totales", consultas_total, styles))
    story.append(Spacer(1, 4))
    story.append(_kpi_row("Visitas Totales", visitas_total, styles))
    story.append(Spacer(1, 28))

    # ── Tabla por portal ───────────────────────────────────────────────────
    story.append(_band("Rendimiento por portal", section_s))
    story.append(Spacer(1, 4))

    table_data = [
        ["", "Sitio", "Exposición", "Consultas", "Visitas"],
    ]
    for idx, p in enumerate(portales, start=1):
        table_data.append([
            f"{idx}.",
            _escape(str(p.get("sitio", "") or "")),
            str(p.get("exposicion", "") or "0"),
            str(p.get("consultas", "") or "0"),
            str(p.get("visitas", "") or "0"),
        ])

    portal_table = Table(
        table_data,
        colWidths=[1.0 * cm, 5.5 * cm, 3.4 * cm, 3.3 * cm, 3.3 * cm],
        repeatRows=1,
    )
    style_cmds = [
        # Header
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), MUTED),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 9),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        # Body
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("TEXTCOLOR", (0, 1), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Align
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        # Padding
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 9),
        # Separadores entre filas — TODOS del mismo color
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, TABLE_BORDER),
    ]
    portal_table.setStyle(TableStyle(style_cmds))
    story.append(portal_table)
    story.append(Spacer(1, 26))

    # ── Comentarios ────────────────────────────────────────────────────────
    story.append(_band("Comentarios", section_s))
    story.append(Spacer(1, 10))

    if comentarios:
        story.extend(_parse_comentarios(comentarios, body_s, bullet_s))
    else:
        story.append(Paragraph("<i>Sin comentarios.</i>", body_s))

    doc.build(story)
    print(f"PDF generado: {output_path}")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Genera Reporte de Rendimiento Mensual en PDF",
    )
    parser.add_argument("--data-file", required=True, help="JSON con los datos")
    parser.add_argument("--output",    required=True, help="Ruta del PDF de salida")
    args = parser.parse_args()

    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    build_pdf(data, args.output)


if __name__ == "__main__":
    main()
