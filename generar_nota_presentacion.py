#!/usr/bin/env python3
"""
Generador de Nota de Presentación de Cliente Comprador — Calace Propiedades
"""

import argparse
import json
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle,
)
from reportlab.lib import colors

# ── Constantes ─────────────────────────────────────────────────────────────
CORREDOR_PRESENTANTE  = "Mariangeles Calace"
INM_PRESENTANTE       = "Calace Propiedades"
MAT_PRESENTANTE       = "7240"

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


# ── Estilos ────────────────────────────────────────────────────────────────
from reportlab.platypus import Image as RLImage
import os as _os

def make_styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "T", parent=base["Normal"],
        fontSize=12, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=14,
    )
    fecha = ParagraphStyle(
        "FE", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_LEFT, spaceAfter=12,
    )
    body = ParagraphStyle(
        "B", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_JUSTIFY, spaceAfter=10, leading=15,
    )
    item = ParagraphStyle(
        "I", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_JUSTIFY, spaceAfter=6, leading=14, leftIndent=16,
    )
    firma = ParagraphStyle(
        "F", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_LEFT, spaceAfter=3, leading=14,
    )
    return title, fecha, body, item, firma


def hr(spb=6, spa=10):
    return HRFlowable(
        width="100%", thickness=0.5, color=colors.grey,
        spaceBefore=spb, spaceAfter=spa,
    )


# ── PDF ────────────────────────────────────────────────────────────────────
def build_pdf(data, output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=2.5 * cm, leftMargin=2.5 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
    )

    title_s, fecha_s, body_s, item_s, firma_s = make_styles()

    hoy  = date.today()
    dia  = hoy.day
    mes  = MESES_ES[hoy.month]
    anio = hoy.year

    cliente_nom      = data["cliente_nombre"]
    cliente_dni      = data["cliente_dni"]
    dir_inmueble     = data["inmueble_direccion"]
    inm_rec_nom      = data["inm_receptora_nombre"]
    cor_rec_nom      = data["corredor_receptor_nombre"]
    cor_rec_mat      = data["corredor_receptor_matricula"]
    cor_rec_cont     = data["corredor_receptor_contacto"]
    div_hon          = data["division_honorarios"]
    vigencia         = data["vigencia_dias"]
    calace_cont      = data["calace_contacto"]
    localidad        = data["localidad_firma"]

    story = []
    # --- Logo ---
    _logo_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'logo_calace.jpg')
    if _os.path.exists(_logo_path):
        from reportlab.lib.units import cm as _cm
        _logo = RLImage(_logo_path, width=5*_cm, height=2.3*_cm)
        _logo.hAlign = 'LEFT'
        story.append(_logo)
        story.append(Spacer(1, 8))
    # --- Fin logo ---

    # ── Título ─────────────────────────────────────────────────────────────
    story.append(Paragraph("NOTA DE PRESENTACIÓN DE CLIENTE COMPRADOR", title_s))

    # ── Encabezado de fecha ────────────────────────────────────────────────
    story.append(Paragraph(
        f"En <b>{localidad}</b>, a los <b>{dia}</b> días del mes de "
        f"<b>{mes}</b> de <b>{anio}</b>.",
        fecha_s,
    ))

    # ── Párrafo de presentación ────────────────────────────────────────────
    p_intro = (
        f"Por la presente, yo, <b>{CORREDOR_PRESENTANTE}</b>, matrícula N° "
        f"<b>{MAT_PRESENTANTE}</b>, en representación de la inmobiliaria "
        f"<b>{INM_PRESENTANTE}</b>, presento a <b>{cliente_nom}</b>, DNI N° "
        f"<b>{cliente_dni}</b>, como cliente interesado en el inmueble ubicado en "
        f"<b>{dir_inmueble}</b>, el cual se encuentra a la venta por medio de la firma "
        f"<b>{inm_rec_nom}</b>, representada por <b>{cor_rec_nom}</b>, matrícula N° "
        f"<b>{cor_rec_mat}</b>."
    )
    story.append(Paragraph(p_intro, body_s))

    # ── Condiciones ────────────────────────────────────────────────────────
    story.append(Paragraph(
        "Ambas partes acuerdan trabajar en conjunto en esta operación bajo las "
        "siguientes condiciones:",
        body_s,
    ))

    condiciones = [
        (
            "División de honorarios",
            f"en caso de concretarse la operación, los honorarios serán compartidos entre "
            f"ambas partes en un <b>{div_hon}</b> sobre el arancel correspondiente por ley "
            f"a la parte compradora."
        ),
        (
            "Exclusividad de presentación",
            f"se reconoce que el cliente antes mencionado fue presentado en forma directa y "
            f"exclusiva por <b>{CORREDOR_PRESENTANTE}</b>, quedando asentado que cualquier "
            f"gestión posterior deberá ser canalizada en conjunto."
        ),
        (
            "Confidencialidad",
            "ambas partes se comprometen a mantener la confidencialidad de la información "
            "intercambiada, tanto del cliente como del inmueble."
        ),
        (
            "Vigencia",
            f"esta presentación tendrá una vigencia de <b>{vigencia} días corridos</b>, "
            f"salvo renovación expresa."
        ),
    ]

    for i, (titulo, texto) in enumerate(condiciones, 1):
        story.append(Paragraph(
            f"{i}. <b>{titulo}:</b> {texto}",
            item_s,
        ))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Sin otro particular, se firma en conformidad por duplicado, quedando un ejemplar "
        "en poder de cada parte.",
        body_s,
    ))

    story.append(hr())

    # ── Bloque de firmas ───────────────────────────────────────────────────
    col_presentante = Paragraph(
        f"<b>Firma y sello</b><br/>"
        f"<b>{CORREDOR_PRESENTANTE}</b><br/>"
        f"Matrícula N° {MAT_PRESENTANTE}<br/>"
        f"Inmobiliaria: {INM_PRESENTANTE}<br/>"
        f"Teléfono / Mail: {calace_cont}",
        firma_s,
    )
    col_receptor = Paragraph(
        f"<b>Firma y sello</b><br/>"
        f"<b>{cor_rec_nom}</b><br/>"
        f"Matrícula N° {cor_rec_mat}<br/>"
        f"Inmobiliaria: {inm_rec_nom}<br/>"
        f"Teléfono / Mail: {cor_rec_cont}",
        firma_s,
    )

    tabla_firmas = Table(
        [[col_presentante, col_receptor]],
        colWidths=[8 * cm, 8 * cm],
    )
    tabla_firmas.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(tabla_firmas)

    doc.build(story)
    print(f"PDF generado: {output_path}")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-file", required=True)
    parser.add_argument("--output",    required=True)
    args = parser.parse_args()

    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    build_pdf(data, args.output)


if __name__ == "__main__":
    main()
