#!/usr/bin/env python3
"""
Generador de Recibo de Refuerzo de Reserva — Calace Propiedades
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
INMOBILIARIA = "Calace Propiedades"
MATRICULAS   = "CMCPSI N° 7240 / CUCIBCA N° 9796"

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

# ── Número a letras ────────────────────────────────────────────────────────
UNIDADES = [
    "", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS",
    "SIETE", "OCHO", "NUEVE", "DIEZ", "ONCE", "DOCE",
    "TRECE", "CATORCE", "QUINCE", "DIECISÉIS", "DIECISIETE",
    "DIECIOCHO", "DIECINUEVE",
]
DECENAS = [
    "", "", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA",
    "SESENTA", "SETENTA", "OCHENTA", "NOVENTA",
]
VEINTI = {
    1: "VEINTIÚN", 2: "VEINTIDÓS", 3: "VEINTITRÉS", 4: "VEINTICUATRO",
    5: "VEINTICINCO", 6: "VEINTISÉIS", 7: "VEINTISIETE",
    8: "VEINTIOCHO", 9: "VEINTINUEVE",
}
CENTENAS = [
    "", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS",
    "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS",
]


from reportlab.platypus import Image as RLImage
import os as _os

def _cientos(n):
    if n == 100:
        return "CIEN"
    c, resto = divmod(n, 100)
    parts = []
    if c:
        parts.append(CENTENAS[c])
    if 1 <= resto <= 19:
        parts.append(UNIDADES[resto])
    elif resto >= 20:
        dec, uni = divmod(resto, 10)
        if dec == 2 and uni > 0:
            parts.append(VEINTI[uni])
        elif uni:
            parts.append(f"{DECENAS[dec]} Y {UNIDADES[uni]}")
        else:
            parts.append(DECENAS[dec])
    return " ".join(parts)


def numero_a_letras(n):
    n = int(n)
    if n == 0:
        return "CERO"
    partes = []
    millones, resto = divmod(n, 1_000_000)
    miles, cientos = divmod(resto, 1_000)
    if millones:
        partes.append("UN MILLÓN" if millones == 1 else f"{_cientos(millones)} MILLONES")
    if miles:
        partes.append("MIL" if miles == 1 else f"{_cientos(miles)} MIL")
    if cientos:
        partes.append(_cientos(cientos))
    return " ".join(partes)


def usd(n):
    """Devuelve (LETRAS DÓLARES ESTADOUNIDENSES, US$ formato)"""
    letras = f"DÓLARES ESTADOUNIDENSES BILLETES {numero_a_letras(int(n))}"
    fmt    = f"US$ {int(n):,}".replace(",", ".")
    return letras, fmt


# ── Estilos ────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "T", parent=base["Normal"],
        fontSize=13, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=20,
    )
    body = ParagraphStyle(
        "B", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_JUSTIFY, spaceAfter=11, leading=15,
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

    cuit_inm    = data["cuit_inmobiliaria"]
    dom_inm     = data["domicilio_inmobiliaria"]
    email_inm   = data["email_inmobiliaria"]

    of_nom      = data["oferente_nombre"]
    of_dni      = data["oferente_dni"]
    of_dom      = data["oferente_domicilio"]
    of_email    = data["oferente_email"]

    dir_inm     = data["direccion_inmueble"]
    loc_inm     = data["localidad_inmueble"]

    precio_l, precio_f       = usd(data["precio_inmueble_usd"])
    refuerzo_l, refuerzo_f   = usd(data["monto_refuerzo_usd"])
    original_l, original_f   = usd(data["monto_original_usd"])
    total_l, total_f         = usd(data["monto_total_usd"])

    fecha_orig  = data["fecha_oferta_original"]
    fecha_co    = data["fecha_contraoferta"]
    fecha_acep  = data["fecha_aceptacion"]
    localidad   = data["localidad_firma"]

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
    story.append(Paragraph("RECIBO DE REFUERZO DE RESERVA", title_s))

    # ── Párrafo 1: recibo principal ────────────────────────────────────────
    p1 = (
        f"<b>{INMOBILIARIA}</b>, CUIT <b>{cuit_inm}</b>, con matrículas <b>{MATRICULAS}</b>, "
        f"con domicilio en <b>{dom_inm}</b>, domicilio electrónico en el email <b>{email_inm}</b>, "
        f"recibió de <b>{of_nom}</b>, DNI <b>{of_dni}</b>, con domicilio en <b>{of_dom}</b>, "
        f"domicilio electrónico en el email <b>{of_email}</b>, en adelante el <b>OFERENTE</b>, "
        f"la cantidad de <b>{refuerzo_l} ({refuerzo_f})</b>, en concepto de "
        f"<b>Refuerzo de Oferta – Reserva</b> por la compra del inmueble ubicado en "
        f"<b>{dir_inm}</b>, <b>{loc_inm}</b>, por el precio de <b>{precio_l} ({precio_f})</b>."
    )
    story.append(Paragraph(p1, body_s))

    # ── Párrafo 2: historial de pagos ──────────────────────────────────────
    p2 = (
        f"El importe recibido en este acto, sumado al de <b>{original_l} ({original_f})</b> "
        f"entregados en oportunidad de la <b>Oferta – Reserva Original</b> de fecha "
        f"<b>{fecha_orig}</b>, con contraoferta del <b>PROPIETARIO</b> de fecha "
        f"<b>{fecha_co}</b>, aceptada por el OFERENTE el día <b>{fecha_acep}</b>, completa "
        f"la suma total de <b>{total_l} ({total_f})</b>."
    )
    story.append(Paragraph(p2, body_s))

    # ── Párrafo 3: ratificación ────────────────────────────────────────────
    p3 = (
        "El OFERENTE ratifica por la presente todas las cláusulas de la Oferta – Reserva "
        "original y modificaciones introducidas por la Contraoferta. La suma entregada en "
        "este acto se integra a la seña constituida oportunamente al haberse confirmado la "
        "mencionada Oferta‑Reserva original."
    )
    story.append(Paragraph(p3, body_s))

    # ── Cierre ─────────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"En <b>{localidad}</b>, a los <b>{dia} días del mes de {mes} de {anio}</b>, "
        f"se firman tres (3) ejemplares de un mismo tenor y a un solo efecto.",
        body_s,
    ))

    story.append(hr())

    # ── Firmas ─────────────────────────────────────────────────────────────
    col_oferente = Paragraph(
        f"<b>Firma:</b> ......................................................<br/>"
        f"<b>Aclaración:</b> {of_nom}<br/>"
        f"<b>DNI:</b> {of_dni}<br/>"
        f"<b>OFERENTE</b>",
        firma_s,
    )
    col_inmobiliaria = Paragraph(
        f"<b>Firma:</b> ......................................................<br/>"
        f"<b>Aclaración:</b> {INMOBILIARIA}<br/>"
        f"<b>Matrículas:</b> {MATRICULAS}<br/>"
        f"<b>INMOBILIARIA</b>",
        firma_s,
    )

    tabla_firmas = Table(
        [[col_oferente, col_inmobiliaria]],
        colWidths=[8 * cm, 8 * cm],
    )
    tabla_firmas.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
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
