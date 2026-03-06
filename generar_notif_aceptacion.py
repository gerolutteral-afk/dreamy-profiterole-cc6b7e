#!/usr/bin/env python3
"""
Generador de Notificación de Aceptación de Contraoferta — Calace Propiedades
"""

import argparse
import json
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors

# ── Constantes inmobiliaria ────────────────────────────────────────────────
INMOBILIARIA = "Calace Propiedades"
MATRICULAS   = "CMCPSI N° 7240 / CUCIBCA N° 9796"

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

# Números a palabras (para porcentajes pequeños)
_NUM_LETRAS = {
    1: "UN", 2: "DOS", 3: "TRES", 4: "CUATRO", 5: "CINCO",
    6: "SEIS", 7: "SIETE", 8: "OCHO", 9: "NUEVE", 10: "DIEZ",
}

from reportlab.platypus import Image as RLImage
import os as _os

def pct_a_letras(n):
    n = int(n)
    return _NUM_LETRAS.get(n, str(n).upper())


# ── Estilos ────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "T", parent=base["Normal"],
        fontSize=12, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=20,
    )
    body = ParagraphStyle(
        "B", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_JUSTIFY, spaceAfter=12, leading=15,
    )
    firma = ParagraphStyle(
        "F", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_LEFT, spaceAfter=3, leading=14,
    )
    return title, body, firma


def hr(spb=4, spa=8):
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

    title_s, body_s, firma_s = make_styles()

    hoy  = date.today()
    dia  = hoy.day
    mes  = MESES_ES[hoy.month]
    anio = hoy.year

    p1_nom  = data["propietario1_nombre"]
    p1_dni  = data["propietario1_dni"]
    p1_dom  = data["propietario1_domicilio"]
    p2_nom  = data.get("propietario2_nombre")
    p2_dni  = data.get("propietario2_dni")
    p2_dom  = data.get("propietario2_domicilio")
    dos_p   = bool(p2_nom and p2_dni)

    dom_inm         = data["domicilio_inmueble"]
    fecha_co        = data["fecha_contraoferta"]
    oferente_nom    = data["oferente_nombre"]
    oferente_dni    = data["oferente_dni"]
    cuit            = data["cuit_inmobiliaria"]
    hon_pct         = int(data["honorarios_pct"])
    hon_letras      = pct_a_letras(hon_pct)
    localidad       = data["localidad_firma"]

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

    # --- Logo Calace Propiedades ---
    _logo_path = _os.path.join(_os.path.dirname(__file__), "logo_calace.jpg")
    if _os.path.exists(_logo_path):
        _logo = RLImage(_logo_path, width=5*cm, height=2.3*cm)
        _logo.hAlign = "LEFT"
        story.append(_logo)
        story.append(Spacer(1, 8))
    # --- Fin logo ---

    # ── Título ─────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "NOTIFICACIÓN DE ACEPTACIÓN DE CONTRAOFERTA", title_s
    ))

    # ── Párrafo 1: identificación y notificación ───────────────────────────
    if dos_p:
        sujeto = (
            f"<b>{p1_nom}</b>, DNI <b>{p1_dni}</b>, con domicilio en <b>{p1_dom}</b>, "
            f"y <b>{p2_nom}</b>, DNI <b>{p2_dni}</b>, con domicilio en <b>{p2_dom}</b>, "
            f"en su carácter de <b>PROPIETARIOS</b>"
        )
    else:
        sujeto = (
            f"<b>{p1_nom}</b>, DNI <b>{p1_dni}</b>, con domicilio en <b>{p1_dom}</b>, "
            f"en su carácter de <b>PROPIETARIO</b>"
        )

    p1_text = (
        f"{sujeto} del inmueble ubicado en <b>{dom_inm}</b>, se notifica de la "
        f"<b>Aceptación de la Contraoferta</b> de fecha <b>{fecha_co}</b> efectuada por "
        f"<b>{oferente_nom}</b>, DNI <b>{oferente_dni}</b>, en su carácter de <b>OFERENTE</b>."
    )
    story.append(Paragraph(p1_text, body_s))

    # ── Párrafo 2: honorarios ──────────────────────────────────────────────
    p2_text = (
        f"El PROPIETARIO abonará a <b>{INMOBILIARIA}</b>, CUIT <b>{cuit}</b>, "
        f"con matrículas <b>{MATRICULAS}</b>, en concepto de <b>honorarios profesionales</b> "
        f"el <b>{hon_pct}% + IVA ({hon_letras} por ciento + IVA)</b>, correspondiente al precio "
        f"de venta, monto que será abonado el día de la firma del Boleto de Compraventa, en "
        f"<b>dólares estadounidenses billetes de alta denominación (US$ 100), de los denominados "
        f"CARA GRANDE</b>, es decir, los correspondientes a las series emitidas a partir del año "
        f"1996, en buen estado de conservación, sin manchas ni escrituras."
    )
    story.append(Paragraph(p2_text, body_s))

    # ── Párrafo 3: retención de honorarios ────────────────────────────────
    p3_text = (
        f"El PROPIETARIO <b>faculta a {INMOBILIARIA} a retener sus honorarios de la seña</b> "
        f"en el acto de firma de dicha Escritura."
    )
    story.append(Paragraph(p3_text, body_s))

    # ── Cierre ─────────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"Se firma un (1) ejemplar electrónicamente en <b>{localidad}</b>, a los "
        f"<b>{dia} días del mes de {mes} de {anio}</b>.",
        body_s,
    ))

    story.append(hr())

    # ── Firma(s) ───────────────────────────────────────────────────────────
    def bloque_firma(nombre, dni, etiqueta="PROPIETARIO"):
        story.append(Paragraph("......................................................", firma_s))
        story.append(Paragraph(f"<b>{etiqueta}</b>", firma_s))
        story.append(Paragraph(f"Aclaración: {nombre}", firma_s))
        story.append(Paragraph(f"DNI: {dni}", firma_s))

    if dos_p:
        bloque_firma(p1_nom, p1_dni, "PROPIETARIO 1")
        story.append(Spacer(1, 0.6 * cm))
        bloque_firma(p2_nom, p2_dni, "PROPIETARIO 2")
    else:
        bloque_firma(p1_nom, p1_dni, "PROPIETARIO")

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
