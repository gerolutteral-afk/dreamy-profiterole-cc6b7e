#!/usr/bin/env python3
"""
Generador de Notificación de Refuerzo de Reserva — Calace Propiedades
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

    p1_nom   = data["propietario1_nombre"]
    p1_dni   = data["propietario1_dni"]
    p1_dom   = data["propietario1_domicilio"]
    p1_email = data["propietario1_email"]
    p2_nom   = data.get("propietario2_nombre")
    p2_dni   = data.get("propietario2_dni")
    p2_dom   = data.get("propietario2_domicilio")
    p2_email = data.get("propietario2_email")
    dos_p    = bool(p2_nom and p2_dni)

    dom_inm       = data["domicilio_inmueble"]
    monto         = int(data["monto_usd"])
    monto_letras  = numero_a_letras(monto)
    monto_fmt     = f"{monto:,}".replace(",", ".")
    oferente_nom  = data["oferente_nombre"]
    oferente_dni  = data["oferente_dni"]
    fecha_ref     = data["fecha_refuerzo"]
    localidad     = data["localidad_firma"]

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
    story.append(Paragraph("NOTIFICACIÓN DE REFUERZO DE RESERVA", title_s))

    # ── Párrafo principal ──────────────────────────────────────────────────
    if dos_p:
        sujeto = (
            f"<b>{p1_nom}</b>, DNI <b>{p1_dni}</b>, con domicilio en <b>{p1_dom}</b>, "
            f"domicilio electrónico en el email <b>{p1_email}</b>, "
            f"y <b>{p2_nom}</b>, DNI <b>{p2_dni}</b>, con domicilio en <b>{p2_dom}</b>, "
            f"domicilio electrónico en el email <b>{p2_email}</b>, "
            f"en su carácter de <b>PROPIETARIOS</b>"
        )
    else:
        sujeto = (
            f"<b>{p1_nom}</b>, DNI <b>{p1_dni}</b>, con domicilio en <b>{p1_dom}</b>, "
            f"domicilio electrónico en el email <b>{p1_email}</b>, "
            f"en su carácter de <b>PROPIETARIO</b>"
        )

    p_main = (
        f"{sujeto} del inmueble ubicado en <b>{dom_inm}</b>, se notifica del "
        f"<b>Refuerzo de Reserva</b> por la suma de "
        f"<b>DÓLARES ESTADOUNIDENSES BILLETES {monto_letras} (US$ {monto_fmt})</b> "
        f"entregado por <b>{oferente_nom}</b>, DNI <b>{oferente_dni}</b>, "
        f"en su carácter de <b>OFERENTE</b>, con fecha <b>{fecha_ref}</b>, "
        f"<b>ratificando por la presente todas sus cláusulas</b>."
    )
    story.append(Paragraph(p_main, body_s))

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
