#!/usr/bin/env python3
"""
Generador de Contraoferta — Calace Propiedades
"""

import argparse
import json
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
)
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
        "MyTitle", parent=base["Normal"],
        fontSize=14, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=20,
    )
    body = ParagraphStyle(
        "MyBody", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_JUSTIFY, spaceAfter=10, leading=15,
    )
    section = ParagraphStyle(
        "MySection", parent=base["Normal"],
        fontSize=10, fontName="Helvetica-Bold",
        alignment=TA_LEFT, spaceBefore=10, spaceAfter=8,
    )
    bullet = ParagraphStyle(
        "MyBullet", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_JUSTIFY, spaceAfter=6, leading=14, leftIndent=20,
    )
    firma = ParagraphStyle(
        "MyFirma", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_LEFT, spaceAfter=3, leading=14,
    )
    return title, body, section, bullet, firma


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

    title_s, body_s, section_s, bullet_s, firma_s = make_styles()

    # Fecha
    hoy  = date.today()
    dia  = hoy.day
    mes  = MESES_ES[hoy.month]
    anio = hoy.year

    # Datos
    p1_nom  = data["propietario1_nombre"]
    p1_dni  = data["propietario1_dni"]
    p1_dom  = data["propietario1_domicilio"]
    p2_nom  = data.get("propietario2_nombre")
    p2_dni  = data.get("propietario2_dni")
    p2_dom  = data.get("propietario2_domicilio")
    dos_p   = bool(p2_nom and p2_dni)

    dom_inm          = data["domicilio_inmueble"]
    fecha_oferta     = data["fecha_oferta"]
    oferente_nom     = data["oferente_nombre"]
    oferente_dni     = data["oferente_dni"]
    precio_usd       = int(data["precio_usd"])
    fecha_escritura  = data["fecha_limite_escritura"]
    cond_extra       = data.get("condiciones_adicionales", [])
    validez_dias     = data["validez_dias"]
    localidad        = data["localidad_firma"]

    precio_letras = numero_a_letras(precio_usd)
    precio_fmt    = f"{precio_usd:,}".replace(",", ".")

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
    story.append(Paragraph("CONTRAOFERTA", title_s))

    # ── Párrafo principal ──────────────────────────────────────────────────
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

    p_intro = (
        f"{sujeto} del inmueble ubicado en <b>{dom_inm}</b>, manifiesta no tener "
        f"impedimento alguno para efectivizar la transferencia del dominio, prestando su expresa "
        f"conformidad con la <b>oferta de fecha {fecha_oferta}</b> presentada por "
        f"<b>{oferente_nom}</b>, DNI <b>{oferente_dni}</b>, en su carácter de <b>OFERENTE</b>, "
        f"aceptando los términos y condiciones allí pactados, a excepción del "
        f"<b>PRECIO TOTAL Y DEFINITIVO</b>, siendo el <b>precio contraofertado</b> la suma de "
        f"<b>DÓLARES ESTADOUNIDENSES BILLETES {precio_letras} (US$ {precio_fmt})</b>, "
        f"y sujeto a la aceptación de las siguientes condiciones establecidas por el PROPIETARIO:"
    )
    story.append(Paragraph(p_intro, body_s))

    story.append(hr(spb=2))

    # ── Sección condiciones ────────────────────────────────────────────────
    story.append(Paragraph("CONDICIONES DE LA CONTRAOFERTA:", section_s))

    # Condición fija: billetes cara grande
    story.append(Paragraph(
        "• El OFERENTE abonará la totalidad del precio en <b>dólares estadounidenses billetes "
        "de alta denominación (US$ 100), de los denominados CARA GRANDE</b>, es decir, "
        "los correspondientes a las series emitidas a partir del año 1996, en buen estado "
        "de conservación, sin manchas ni escrituras.",
        bullet_s,
    ))

    # Condición fija: fecha límite escritura
    story.append(Paragraph(
        f"• El plazo límite para la firma de la Escritura Traslativa de Dominio será hasta "
        f"el día <b>{fecha_escritura}</b>.",
        bullet_s,
    ))

    # Condiciones adicionales (si las hay)
    for cond in cond_extra:
        story.append(Paragraph(f"• {cond}", bullet_s))

    story.append(hr(spb=6))

    # ── Validez y cierre ───────────────────────────────────────────────────
    story.append(Paragraph(
        f"La validez de la presente contraoferta es de <b>{validez_dias} días</b>.",
        body_s,
    ))
    story.append(Paragraph(
        f"Se firma un ejemplar electrónicamente en <b>{localidad}</b>, a los "
        f"<b>{dia} días del mes de {mes} de {anio}</b>.",
        body_s,
    ))

    story.append(hr())

    # ── Firmas ─────────────────────────────────────────────────────────────
    def bloque_firma(nombre, dni, etiqueta="PROPIETARIO"):
        story.append(Paragraph(
            f"......................................................",
            firma_s,
        ))
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
    parser = argparse.ArgumentParser(description="Genera Contraoferta en PDF")
    parser.add_argument("--data-file", required=True)
    parser.add_argument("--output",    required=True)
    args = parser.parse_args()

    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    build_pdf(data, args.output)


if __name__ == "__main__":
    main()
