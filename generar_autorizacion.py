#!/usr/bin/env python3
"""
Genera un PDF de Autorización de Alquiler para Calace Propiedades.
"""

import argparse
import locale
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.colors import HexColor


# --- Datos fijos de la inmobiliaria ---
INMOBILIARIA = "Calace Propiedades"
MARTILLERO = "Mariangeles Calace"
MATRICULA_CMCPSI = "7240"
MATRICULA_CUCIBCA = "9796"


from reportlab.platypus import Image as RLImage
import os as _os

def get_fecha_actual():
    """Retorna la fecha actual formateada en español."""
    meses = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    now = datetime.now()
    return f"{now.day} días del mes de {meses[now.month - 1]} de {now.year}"


def build_pdf(args):
    """Genera el PDF de autorización de alquiler."""

    doc = SimpleDocTemplate(
        args.output,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Estilos personalizados
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=15,
        fontName="Helvetica-Bold",
        spaceAfter=14,
        alignment=TA_CENTER,
        textColor=HexColor("#1a1a1a"),
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10.5,
        fontName="Helvetica",
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "CustomBullet",
        parent=body_style,
        leftIndent=1.5 * cm,
        bulletIndent=0.5 * cm,
        spaceAfter=4,
    )

    firma_style = ParagraphStyle(
        "FirmaStyle",
        parent=styles["Normal"],
        fontSize=10.5,
        fontName="Helvetica",
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=2,
    )

    firma_bold = ParagraphStyle(
        "FirmaBold",
        parent=firma_style,
        fontName="Helvetica-Bold",
    )

    # Determinar moneda
    simbolo = "$" if args.moneda.lower() in ("pesos", "ars", "$") else "USD "
    valor_formateado = f"{simbolo}{args.valor}"

    fecha_texto = get_fecha_actual()

    # --- Construir el documento ---
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

    # Título
    story.append(Paragraph("AUTORIZACIÓN DE ALQUILER", title_style))
    story.append(Spacer(1, 6))

    # Cuerpo principal
    parrafo1 = (
        f'Por la presente, yo, <b>{args.nombre}</b>, DNI Nº <b>{args.dni}</b>, '
        f'en mi carácter de <b>propietario</b> del inmueble ubicado en '
        f'<b>{args.direccion}</b>, autorizo a la firma <b>{INMOBILIARIA}</b>, '
        f'a ofrecer en <b>alquiler</b> dicho inmueble, bajo las siguientes condiciones:'
    )
    story.append(Paragraph(parrafo1, body_style))
    story.append(Spacer(1, 6))

    # Condiciones
    condiciones = [
        f'<b>Valor locativo mensual</b>: {valor_formateado}',
        f'<b>Plazo del contrato</b>: {args.plazo}',
        f'<b>Honorarios inmobiliarios</b>: equivalentes a <b>un (1) mes de alquiler</b>, '
        f'a cargo del <b>{args.honorarios}</b>, conforme a lo acordado entre las partes.',
        f'<b>Condiciones generales</b>: {args.garantia}',
    ]

    for cond in condiciones:
        story.append(Paragraph(f"•&nbsp;&nbsp;{cond}", bullet_style))

    story.append(Spacer(1, 6))

    # Autorizaciones adicionales
    story.append(Paragraph("Asimismo, autorizo a la inmobiliaria a:", body_style))
    story.append(Spacer(1, 4))

    autorizaciones = [
        "Tomar fotografías y/o videos del inmueble",
        "Publicar el mismo en portales especializados y/o medios de difusión pertinentes",
        "Coordinar y realizar visitas con potenciales inquilinos, con previo aviso",
    ]

    for aut in autorizaciones:
        story.append(Paragraph(f"•&nbsp;&nbsp;{aut}", bullet_style))

    story.append(Spacer(1, 6))

    # Declaración jurada
    declaracion = (
        'Declaro bajo juramento que soy <b>titular registral</b> del inmueble '
        'antes mencionado y que tengo plena capacidad legal para celebrar '
        'contratos de locación sobre el mismo.'
    )
    story.append(Paragraph(declaracion, body_style))
    story.append(Spacer(1, 6))

    # Cierre
    cierre = (
        f'Sin otro particular, firmamos en conformidad en la localidad de '
        f'<b>{args.localidad}</b>, a los <b>{fecha_texto}</b>.'
    )
    story.append(Paragraph(cierre, body_style))
    story.append(Spacer(1, 20))

    # Línea separadora
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#333333")))
    story.append(Spacer(1, 10))

    # Firma del propietario
    story.append(Paragraph("<b>Firma del Propietario</b>: ......................................................", firma_bold))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Nombre completo</b>: {args.nombre}", firma_style))
    story.append(Paragraph(f"<b>DNI Nº</b>: {args.dni}", firma_style))
    story.append(Spacer(1, 16))

    # Línea separadora
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#333333")))
    story.append(Spacer(1, 10))

    # Firma del martillero
    story.append(Paragraph(
        "<b>Firma del Martillero / Corredor Público</b>: ......................................................",
        firma_bold
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Nombre completo</b>: {MARTILLERO}", firma_style))
    story.append(Paragraph(f"<b>Matrícula CMCPSI Nº</b>: {MATRICULA_CMCPSI}", firma_style))
    story.append(Paragraph(f"<b>Matrícula CUCIBCA Nº</b>: {MATRICULA_CUCIBCA}", firma_style))

    # Generar PDF
    doc.build(story)
    print(f"PDF generado exitosamente: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Generar Autorización de Alquiler en PDF")
    parser.add_argument("--nombre", required=True, help="Nombre completo del propietario")
    parser.add_argument("--dni", required=True, help="DNI del propietario")
    parser.add_argument("--direccion", required=True, help="Dirección completa del inmueble")
    parser.add_argument("--localidad", required=True, help="Localidad donde se firma")
    parser.add_argument("--valor", required=True, help="Valor locativo mensual (solo número)")
    parser.add_argument("--moneda", default="pesos", help="Moneda: pesos o dolares")
    parser.add_argument("--plazo", required=True, help="Plazo del contrato")
    parser.add_argument("--honorarios", required=True, help="A cargo de: propietario o inquilino")
    parser.add_argument("--garantia", required=True, help="Condiciones de garantía")
    parser.add_argument("--output", required=True, help="Ruta del archivo PDF de salida")

    args = parser.parse_args()
    build_pdf(args)


if __name__ == "__main__":
    main()
