#!/usr/bin/env python3
"""
Generador de Autorización de Venta — Calace Propiedades
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

# ── Constantes inmobiliaria ────────────────────────────────────────────────
INMOBILIARIA = "Calace Propiedades"
MARTILLERO   = "Mariangeles Calace"
MAT_CMCPSI   = "7240"
MAT_CUCIBCA  = "9796"
MATRICULAS   = f"CMCPSI N° {MAT_CMCPSI} / CUCIBCA N° {MAT_CUCIBCA}"
COLEGIO      = "Colegio de Martilleros y Corredores Públicos del Partido de San Isidro"

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
        "MyTitle",
        parent=base["Normal"],
        fontSize=13,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=18,
    )
    body = ParagraphStyle(
        "MyBody",
        parent=base["Normal"],
        fontSize=10,
        fontName="Helvetica",
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=15,
    )
    bullet = ParagraphStyle(
        "MyBullet",
        parent=base["Normal"],
        fontSize=10,
        fontName="Helvetica",
        alignment=TA_LEFT,
        spaceAfter=5,
        leading=14,
        leftIndent=20,
    )
    label = ParagraphStyle(
        "MyLabel",
        parent=base["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceBefore=14,
        spaceAfter=4,
    )
    firma = ParagraphStyle(
        "MyFirma",
        parent=base["Normal"],
        fontSize=10,
        fontName="Helvetica",
        alignment=TA_LEFT,
        spaceAfter=3,
        leading=14,
    )
    return title, body, bullet, label, firma


def hr(spb=4, spa=8):
    return HRFlowable(
        width="100%", thickness=0.5, color=colors.grey,
        spaceBefore=spb, spaceAfter=spa,
    )


# ── PDF ────────────────────────────────────────────────────────────────────
def build_pdf(data, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    title_s, body_s, bullet_s, label_s, firma_s = make_styles()

    # Fecha
    hoy = date.today()
    dia  = hoy.day
    mes  = MESES_ES[hoy.month]
    anio = hoy.year

    # Extraer datos
    propietarios = []
    for i in range(1, 7):
        n = data.get(f"propietario{i}_nombre", "").strip()
        d = data.get(f"propietario{i}_dni", "").strip()
        if n and d:
            propietarios.append({"nombre": n, "dni": d})

    dir_inmueble     = data["direccion_inmueble"]
    precio_usd       = int(data["precio_usd"])
    honorarios_pct   = data["honorarios_pct"]
    honorarios_cargo = data["honorarios_cargo"]
    localidad        = data["localidad_firma"]

    multiples = len(propietarios) > 1
    p1_nombre = propietarios[0]["nombre"]
    p1_dni    = propietarios[0]["dni"]
    # compat
    dos_propietarios = multiples

    # Formatear precio
    precio_fmt = f"{precio_usd:,}".replace(",", ".")

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
    story.append(Paragraph("AUTORIZACIÓN DE VENTA", title_s))

    # ── Párrafo principal ──────────────────────────────────────────────────
    if multiples:
        partes = ", ".join(
            f"<b>{p['nombre']}</b>, DNI Nº <b>{p['dni']}</b>"
            for p in propietarios[:-1]
        )
        ultimo = propietarios[-1]
        sujeto = (
            f"nosotros, {partes} "
            f"y <b>{ultimo['nombre']}</b>, DNI Nº <b>{ultimo['dni']}</b>, "
            f"en nuestro carácter de <b>propietarios</b>"
        )
    else:
        sujeto = (
            f"yo, <b>{p1_nombre}</b>, DNI Nº <b>{p1_dni}</b>, "
            f"en mi carácter de <b>propietario</b>"
        )

    verbo = "autorizamos" if dos_propietarios else "autorizo"
    p_intro = (
        f"Por la presente, {sujeto} del inmueble ubicado en "
        f"<b>{dir_inmueble}</b>, {verbo} a la firma <b>{INMOBILIARIA}</b> "
        f"a ofrecer en venta dicho inmueble, bajo las siguientes condiciones:"
    )
    story.append(Paragraph(p_intro, body_s))

    # ── Condiciones ────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"• <b>Precio de venta:</b> USD <b>{precio_fmt}</b> (dólares estadounidenses)",
        bullet_s,
    ))
    story.append(Paragraph(
        f"• <b>Honorarios inmobiliarios:</b> <b>{honorarios_pct}%</b> del valor de venta, "
        f"a cargo <b>{honorarios_cargo}</b>",
        bullet_s,
    ))

    # ── Autorizaciones ─────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "Asimismo, autorizamos expresamente a la inmobiliaria a:" if dos_propietarios else "Asimismo, autorizo expresamente a la inmobiliaria a:", body_s
    ))
    for item in [
        "Tomar fotografías y/o videos del inmueble",
        "Publicar el mismo en portales inmobiliarios y/o medios de difusión pertinentes",
        "Coordinar y realizar visitas con potenciales compradores, con previo aviso",
    ]:
        story.append(Paragraph(f"• {item}", bullet_s))

    # ── Declaración ────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    if dos_propietarios:
        story.append(Paragraph(
            "Declaramos bajo juramento que somos <b>titulares registrales</b> del inmueble "
            "mencionado y que tenemos plena capacidad legal para disponer del mismo.",
            body_s,
        ))
    else:
        story.append(Paragraph(
            "Declaro bajo juramento que soy <b>titular registral</b> del inmueble "
            "mencionado y que tengo plena capacidad legal para disponer del mismo.",
            body_s,
        ))
    story.append(Paragraph(
        "El precio de comercialización podrá ser modificado posteriormente por indicación "
        "de la parte propietaria, incluso por medios electrónicos.",
        body_s,
    ))

    # ── Cierre ─────────────────────────────────────────────────────────────
    story.append(Paragraph(
        f"Sin otro particular, firmamos en conformidad en la localidad de "
        f"<b>{localidad}</b>, a los <b>{dia} días del mes de {mes} de {anio}</b>.",
        body_s,
    ))

    story.append(hr())

    # ── Bloques de firma por cada propietario ──────────────────────────────
    for idx, p in enumerate(propietarios):
        if idx > 0:
            story.append(Spacer(1, 0.5 * cm))
        label = "Co-Propietario" if idx > 0 else "Propietario"
        story.append(Paragraph(f"<b>Firma del {label}:</b> ......................................................", firma_s))
        story.append(Paragraph(f"<b>Nombre completo:</b> {p['nombre']}", firma_s))
        story.append(Paragraph(f"<b>DNI Nº:</b> {p['dni']}", firma_s))

    story.append(hr())

    # ── Bloque firma martillero ────────────────────────────────────────────
    story.append(Paragraph(
        "<b>Firma del Martillero / Corredor Público:</b> ......................................................",
        firma_s,
    ))
    story.append(Paragraph(f"<b>Nombre completo:</b> {MARTILLERO}", firma_s))
    story.append(Paragraph(f"<b>Matrículas:</b> {MATRICULAS}", firma_s))
    story.append(Paragraph(f"<b>Colegio Profesional:</b> {COLEGIO}", firma_s))

    doc.build(story)
    print(f"PDF generado: {output_path}")


# ── Main ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Genera Autorización de Venta en PDF"
    )
    parser.add_argument("--data-file", required=True, help="JSON con los datos")
    parser.add_argument("--output",    required=True, help="Ruta del PDF de salida")
    args = parser.parse_args()

    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    build_pdf(data, args.output)


if __name__ == "__main__":
    main()
