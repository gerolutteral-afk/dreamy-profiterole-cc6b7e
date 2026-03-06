#!/usr/bin/env python3
"""
Generador de Constancia de Reserva de Alquiler — Calace Propiedades
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
INMOBILIARIA    = "Calace Propiedades"
MARTILLERO      = "Mariangeles Calace"
MAT_CMCPSI      = "7240"
MAT_CUCIBCA     = "9796"
MATRICULAS      = f"CMCPSI N° {MAT_CMCPSI} / CUCIBCA N° {MAT_CUCIBCA}"

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

# ── Conversión número a letras ─────────────────────────────────────────────
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


def formatear_monto(numero, moneda):
    """Devuelve (letras_con_moneda, símbolo+número)."""
    letras = numero_a_letras(int(numero))
    if moneda == "USD":
        letras += " DÓLARES ESTADOUNIDENSES"
        simbolo = f"U$S {int(numero):,}".replace(",", ".")
    else:
        letras += " PESOS"
        simbolo = f"$ {int(numero):,}".replace(",", ".")
    return letras, simbolo


# ── Estilos ────────────────────────────────────────────────────────────────
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
    section = ParagraphStyle(
        "MySection",
        parent=base["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=8,
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
    firma = ParagraphStyle(
        "MyFirma",
        parent=base["Normal"],
        fontSize=10,
        fontName="Helvetica",
        alignment=TA_LEFT,
        spaceAfter=4,
        leading=14,
    )
    return title, body, section, bullet, firma


def hr(spb=4, spa=6):
    return HRFlowable(
        width="100%", thickness=0.5, color=colors.grey,
        spaceBefore=spb, spaceAfter=spa,
    )


# ── Construcción del PDF ───────────────────────────────────────────────────
def build_pdf(data, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    title_s, body_s, section_s, bullet_s, firma_s = make_styles()

    # Fecha de hoy
    hoy = date.today()
    dia  = hoy.day
    mes  = MESES_ES[hoy.month]
    anio = hoy.year

    # Extraer datos
    genero              = data["genero"]
    nombre_interesado   = data["nombre_interesado"]
    dni                 = data["dni_interesado"]
    domicilio_int       = data["domicilio_interesado"]
    moneda              = data["moneda"]           # "Pesos" | "USD"
    monto_reserva       = int(data["monto_reserva"])
    medio_pago          = data["medio_pago"]
    dir_inmueble        = data["direccion_inmueble"]
    uf_inmueble         = data["uf_inmueble"]
    destino             = data["destino"]
    nombre_propietario  = data["nombre_propietario"]
    fecha_limite        = data["fecha_limite"]
    plazo_contrato      = data["plazo_contrato"]
    monto_mensual       = int(data["monto_mensual"])
    ajustes             = data["ajustes"]
    deposito            = data["deposito"]
    garantia            = data["garantia"]
    fecha_firma_est     = data["fecha_firma_estimada"]
    plazo_dias          = data["plazo_dias"]
    honorarios          = data["honorarios"]
    a_cargo_de          = data["a_cargo_de"]
    localidad_firma     = data["localidad_firma"]

    # Formatear montos
    reserva_letras, reserva_num = formatear_monto(monto_reserva, moneda)
    mensual_letras, mensual_num = formatear_monto(monto_mensual, moneda)

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
    story.append(Paragraph("CONSTANCIA DE RESERVA DE ALQUILER", title_s))

    # ── Párrafo de apertura ────────────────────────────────────────────────
    p_apertura = (
        f"En la localidad de <b>{localidad_firma}</b>, a los <b>{dia}</b> días del mes de "
        f"<b>{mes}</b> de <b>{anio}</b>, se deja constancia de que <b>{genero} {nombre_interesado}</b>, "
        f"titular del DNI N° <b>{dni}</b>, con domicilio en <b>{domicilio_int}</b>, entrega en este "
        f"acto la suma de <b>{reserva_letras} ({reserva_num})</b>, mediante <b>{medio_pago}</b>, "
        f"en concepto de <b>reserva</b> para el alquiler del inmueble ubicado en "
        f"<b>{dir_inmueble}</b>, correspondiente a la unidad <b>{uf_inmueble}</b>, destinado a "
        f"<b>{destino}</b>, propiedad de <b>{nombre_propietario}</b>."
    )
    story.append(Paragraph(p_apertura, body_s))

    p_ref = (
        f'La presente reserva se realiza "ad referéndum" del propietario, quien deberá manifestar '
        f"su aceptación o rechazo de la misma hasta el día <b>{fecha_limite}</b>, inclusive."
    )
    story.append(Paragraph(p_ref, body_s))

    story.append(hr())

    # ── Condiciones básicas ────────────────────────────────────────────────
    story.append(Paragraph("CONDICIONES BÁSICAS DEL ALQUILER PROPUESTO:", section_s))

    items = [
        ("Plazo del contrato",                    plazo_contrato),
        ("Monto mensual del alquiler",            f"{mensual_letras} ({mensual_num})"),
        ("Ajustes",                               ajustes),
        ("Depósito",                              deposito),
        ("Garantía ofrecida",                     garantia),
        ("Fecha estimada de firma del contrato",  fecha_firma_est),
    ]
    for label, valor in items:
        story.append(Paragraph(f"• <b>{label}:</b> {valor}", bullet_s))

    story.append(hr(spb=10))

    # ── Párrafos generales ─────────────────────────────────────────────────
    p_imput = (
        "En caso de aceptación por parte del propietario, la presente suma será imputada al pago "
        "del primer mes de alquiler o al concepto que se acuerde en el contrato definitivo. "
        "En caso de rechazo de la oferta, la suma entregada será reintegrada al interesado "
        "sin derecho a reclamo alguno."
    )
    story.append(Paragraph(p_imput, body_s))

    p_plazo = (
        f"La firma del contrato deberá realizarse dentro del plazo de <b>{plazo_dias} días "
        f"corridos</b> desde la aceptación de esta reserva, salvo pacto en contrario."
    )
    story.append(Paragraph(p_plazo, body_s))

    p_desist = (
        "En caso de aceptación y posterior desistimiento por parte del interesado, la reserva "
        "quedará a favor del propietario o la inmobiliaria en carácter de seña no reintegrable."
    )
    story.append(Paragraph(p_desist, body_s))

    story.append(hr())

    # ── Interviene ─────────────────────────────────────────────────────────
    p_interviene = (
        f"<b>INTERVIENE:</b> <b>{INMOBILIARIA}</b>, actuando a través de <b>{MARTILLERO}</b>, "
        f"Matrículas {MATRICULAS}, quien percibirá en el acto de firma del contrato la suma "
        f"equivalente a <b>{honorarios}</b>, en concepto de honorarios profesionales, "
        f"a cargo <b>{a_cargo_de}</b>."
    )
    story.append(Paragraph(p_interviene, body_s))

    story.append(hr())

    # ── Firmas ─────────────────────────────────────────────────────────────
    story.append(Paragraph("<b>FIRMAS:</b>", section_s))
    story.append(Spacer(1, 1 * cm))

    col_interesado = Paragraph(
        f"......................................................<br/>"
        f"<b>{nombre_interesado}</b><br/>"
        f"DNI: {dni}",
        firma_s,
    )
    col_inmobiliaria = Paragraph(
        f"......................................................<br/>"
        f"<b>{MARTILLERO}</b><br/>"
        f"{MATRICULAS}",
        firma_s,
    )

    tabla_firmas = Table(
        [[col_interesado, col_inmobiliaria]],
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
    parser = argparse.ArgumentParser(
        description="Genera Constancia de Reserva de Alquiler en PDF"
    )
    parser.add_argument("--data-file", required=True, help="JSON con los datos del formulario")
    parser.add_argument("--output",    required=True, help="Ruta del archivo PDF de salida")
    args = parser.parse_args()

    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    build_pdf(data, args.output)


if __name__ == "__main__":
    main()
