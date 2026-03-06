#!/usr/bin/env python3
"""
Generador de Oferta de Compra — Calace Propiedades
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
MARTILLERO   = "Mariangeles Calace"
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
    miles, cientos  = divmod(resto, 1_000)
    if millones:
        partes.append("UN MILLÓN" if millones == 1 else f"{_cientos(millones)} MILLONES")
    if miles:
        partes.append("MIL" if miles == 1 else f"{_cientos(miles)} MIL")
    if cientos:
        partes.append(_cientos(cientos))
    return " ".join(partes)


def usd_fmt(n):
    """Devuelve (LETRAS, U$S formato)"""
    return numero_a_letras(int(n)), f"U$S {int(n):,}".replace(",", ".")


# ── Estilos ────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "T", parent=base["Normal"],
        fontSize=13, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=16,
    )
    body = ParagraphStyle(
        "B", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_JUSTIFY, spaceAfter=9, leading=14,
    )
    label = ParagraphStyle(
        "L", parent=base["Normal"],
        fontSize=10, fontName="Helvetica-Bold",
        alignment=TA_LEFT, spaceAfter=4, spaceBefore=8,
    )
    bullet = ParagraphStyle(
        "BU", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_LEFT, spaceAfter=4, leading=13, leftIndent=16,
    )
    section = ParagraphStyle(
        "S", parent=base["Normal"],
        fontSize=11, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=12, spaceBefore=14,
    )
    firma = ParagraphStyle(
        "F", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_LEFT, spaceAfter=3, leading=14,
    )
    firma_c = ParagraphStyle(
        "FC", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_CENTER, spaceAfter=3, leading=14,
    )
    return title, body, label, bullet, section, firma, firma_c


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

    title_s, body_s, label_s, bullet_s, section_s, firma_s, firma_c_s = make_styles()

    hoy  = date.today()
    dia  = hoy.day
    mes  = MESES_ES[hoy.month]
    anio = hoy.year

    # ── Datos ───────────────────────────────────────────────────────────────
    of_nom    = data["oferente_nombre"]
    of_dni    = data["oferente_dni"]
    of_dom    = data["oferente_domicilio"]
    of_ciudad = data["oferente_ciudad"]

    loc_inm   = data["localidad_inmueble"]
    prov_inm  = data["provincia_inmueble"]
    calle_inm = data["calle_inmueble"]
    num_inm   = data["numero_inmueble"]
    uf        = data["uf"]
    poligonos = data.get("poligonos")
    circ      = data["circ"]
    secc      = data["secc"]
    manz      = data["manz"]
    parc      = data["parc"]
    subparc   = data.get("subparcela")
    matricula = data["matricula"]

    res_l, res_f    = usd_fmt(data["monto_reserva_usd"])
    prec_l, prec_f  = usd_fmt(data["precio_total_usd"])
    medio_pago      = data["medio_pago"]
    pct_boleto      = data["pct_boleto"]
    pct_escrit      = data["pct_escritura"]
    dias_boleto     = data["plazo_boleto_dias"]
    dias_escrit     = data["plazo_escritura_dias"]
    fecha_lim       = data["fecha_limite"]
    honorarios      = data["honorarios"]
    localidad       = data["localidad_firma"]

    v1_nom  = data["vendedor1_nombre"]
    v1_dni  = data["vendedor1_dni"]
    v2_nom  = data.get("vendedor2_nombre")
    v2_dni  = data.get("vendedor2_dni")
    dos_v   = bool(v2_nom and v2_dni)
    v_dom   = data["vendedores_domicilio"]

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
    
    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 1: OFERTA DE COMPRA
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("OFERTA DE COMPRA", title_s))

    # Descripción catastral del inmueble
    cat_parts = [
        f"Circ.: <b>{circ}</b>",
        f"Secc.: <b>{secc}</b>",
        f"Manz.: <b>{manz}</b>",
        f"Parc.: <b>{parc}</b>",
    ]
    if subparc and subparc.lower() not in ("no aplica", "no", ""):
        cat_parts.append(f"Subparcela: <b>{subparc}</b>")
    catastro_str = "; ".join(cat_parts)

    poligono_str = ""
    if poligonos and poligonos.lower() not in ("no aplica", "no", ""):
        poligono_str = f", integrada por los polígonos <b>{poligonos}</b>"

    p_intro = (
        f"RECIBIMOS de <b>{of_nom} (D.N.I {of_dni})</b> con domicilio en la calle "
        f"<b>{of_dom}, {of_ciudad}</b>, la suma de <b>DÓLARES ESTADOUNIDENSES BILLETE "
        f"{res_l} ({res_f}.-)</b>, en <b>{medio_pago}</b>, en concepto de reserva por la "
        f"compra de un Inmueble ubicado en la Localidad y Partido de <b>{loc_inm}</b>, "
        f"Provincia de <b>{prov_inm}</b>, sito con frente a la calle <b>{calle_inm} {num_inm}</b> "
        f"Identificado según Título como Unidad Funcional Nro. <b>{uf}</b>{poligono_str}. "
        f"Nomenclatura Catastral: {catastro_str}. "
        f"Inscripto el Dominio en el Registro de la Propiedad en la matrícula <b>{matricula}</b>."
    )
    story.append(Paragraph(p_intro, body_s))

    # Precio total
    story.append(Paragraph(
        f"<b>PRECIO TOTAL:</b> DÓLARES ESTADOUNIDENSES BILLETE <b>{prec_l} ({prec_f})</b>",
        body_s,
    ))

    # Forma de pago
    story.append(Paragraph("<b>FORMA DE PAGO:</b>", label_s))
    story.append(Paragraph(
        f"• {pct_boleto}% A la firma del Boleto de Compraventa.", bullet_s
    ))
    story.append(Paragraph(
        f"• {pct_escrit}% Contra Escritura traslativa de Dominio y entrega de Posesión.", bullet_s
    ))

    # Plazos y escribano
    story.append(Paragraph(
        f"<b>FECHA DE FIRMA DE BOLETO DE COMPRAVENTA:</b> Dentro de los {dias_boleto} días "
        f"de aceptada la presente Oferta.",
        body_s,
    ))
    story.append(Paragraph(
        f"<b>FECHA DE ESCRITURA Y ENTREGA DE POSESIÓN:</b> Dentro de los {dias_escrit} días "
        f"corridos de firmado el Boleto de Compraventa.",
        body_s,
    ))
    story.append(Paragraph(
        "<b>ESCRIBANO ACTUANTE:</b> A designar por la parte Compradora.",
        body_s,
    ))

    # Párrafo estándar estado del inmueble
    story.append(Paragraph(
        "Esta venta se realiza en base a títulos perfectos, debiéndose entregar el inmueble "
        "en el estado en que se encuentra y que el comprador declara conocer y aceptar por "
        "haberlo visitado antes de ahora. Asimismo la escrituración se realizará libre de "
        "gravámenes, impuestos, tasas y servicios, a la fecha de escritura traslativa de "
        "dominio y posesión, la que se entregará libre de ocupantes y/o intrusos. Los gastos "
        "que demande la Escritura serán soportados según usos y costumbres.",
        body_s,
    ))

    # Cláusula esencial (fija)
    story.append(Paragraph(
        "<b>CLÁUSULA ESENCIAL:</b> Es condición esencial de esta venta que el pago sea "
        "realizado en DÓLARES ESTADOUNIDENSES BILLETE, los mismos deberán ser de alta "
        "denominación, de cara grande, sin roturas ni manchas. La parte compradora no podrá "
        "invocar la causa de imprevisión, ni la eventual imposibilidad de adquirirlos por no "
        "estar autorizada la venta al público, por cuanto manifiesta en este acto que tiene "
        "en su poder los billetes necesarios para abonar el precio pactado, haciéndose custodia "
        "y responsable por la tenencia de los mismos. Por tal motivo, queda debidamente aclarado "
        "que el precio de esta compraventa no podrá ser transformado a ninguna otra moneda o "
        "papel que no sea el aquí pactado como cláusula esencial (Arts. 765 y 766 del Código Civil).",
        body_s,
    ))

    # Condiciones de la reserva (fija + fecha límite variable)
    story.append(Paragraph(
        f"<b>CONDICIONES DE LA RESERVA:</b> La presente se efectúa \"ad referéndum\" del "
        f"propietario y, una vez aceptada por el mismo a más tardar el <b>{fecha_lim}</b>, "
        f"tendrá vigencia hasta el día de la firma del Boleto de Compraventa, dejándose "
        f"expresamente aclarado que su falta de aceptación por parte del vendedor no dará "
        f"derecho a indemnización alguna contra el mismo y/o intermediario, salvo la restitución "
        f"simple de las sumas entregadas en el presente acto. Una vez conformada la presente por "
        f"el propietario, las sumas entregadas adquirirán carácter de seña. Ante cualquier "
        f"incumplimiento del comprador, éste perderá las sumas entregadas en concepto de única "
        f"indemnización a favor del vendedor, quien podrá disponer libremente de la propiedad. "
        f"Mientras que, si el vendedor incumpliere sus obligaciones una vez aceptada la presente, "
        f"deberá reintegrar al comprador las sumas abonadas, más otro tanto igual en concepto de "
        f"única y total indemnización. Una vez conformada la presente, si las partes no fueran "
        f"notificadas por otro medio fehaciente, se entenderá que la Escritura Traslativa de "
        f"Dominio se firmará en lugar y horario a convenir entre las partes y dentro del plazo previsto.",
        body_s,
    ))

    # Honorarios
    story.append(Paragraph(
        f"Se deja constancia que <b>{INMOBILIARIA}</b> (<b>{MARTILLERO}</b>, Mat. "
        f"<b>{MATRICULAS}</b>) percibirá en la firma del Boleto de Compraventa el "
        f"<b>{honorarios}</b>, en concepto de honorarios a cargo del oferente, "
        f"por la intervención cumplida.",
        body_s,
    ))

    # Cierre y firma oferente
    story.append(Paragraph(
        f"En la localidad de <b>{localidad}</b>, a los <b>{dia} días del mes de {mes} "
        f"de {anio}</b>.",
        body_s,
    ))

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("……………………………………………", firma_c_s))
    story.append(Paragraph("<b>OFERENTE</b>", firma_c_s))
    story.append(Paragraph(f"Aclaración: {of_nom}", firma_c_s))
    story.append(Paragraph(f"DNI: {of_dni}", firma_c_s))

    story.append(hr(spb=14))

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 2: ACEPTACIÓN DE LA OFERTA
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("ACEPTACIÓN DE LA OFERTA", section_s))

    if dos_v:
        p_acep = (
            f"Presente en este acto: el/la <b>{v1_nom}</b> (D.N.I <b>{v1_dni}</b>) "
            f"y el/la <b>{v2_nom}</b> (D.N.I <b>{v2_dni}</b>), ambos con domicilio en "
            f"<b>{v_dom}</b>, en su carácter de Parte Vendedora del inmueble objeto de la "
            f"presente Reserva de Compra y Condiciones de Pago, manifiestan expresamente no "
            f"tener impedimento alguno para efectivizar la transferencia de dominio convenida, "
            f"prestando su plena y expresa conformidad con la oferta efectuada y demás "
            f"condiciones pactadas que aceptan en todos sus términos."
        )
    else:
        p_acep = (
            f"Presente en este acto: el/la <b>{v1_nom}</b> (D.N.I <b>{v1_dni}</b>), "
            f"con domicilio en <b>{v_dom}</b>, en su carácter de Parte Vendedora del inmueble "
            f"objeto de la presente Reserva de Compra y Condiciones de Pago, manifiesta "
            f"expresamente no tener impedimento alguno para efectivizar la transferencia de "
            f"dominio convenida, prestando su plena y expresa conformidad con la oferta efectuada "
            f"y demás condiciones pactadas que acepta en todos sus términos."
        )
    story.append(Paragraph(p_acep, body_s))

    story.append(Spacer(1, 0.8 * cm))

    # Firmas vendedores
    if dos_v:
        col_v1 = Paragraph(
            f"……………………………………<br/><b>Parte Vendedora</b><br/>"
            f"Aclaración: {v1_nom}<br/>DNI: {v1_dni}",
            firma_c_s,
        )
        col_v2 = Paragraph(
            f"……………………………………<br/><b>Parte Vendedora</b><br/>"
            f"Aclaración: {v2_nom}<br/>DNI: {v2_dni}",
            firma_c_s,
        )
        tabla_v = Table([[col_v1, col_v2]], colWidths=[8 * cm, 8 * cm])
        tabla_v.setStyle(TableStyle([
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",(0, 0), (-1, -1), 0),
        ]))
        story.append(tabla_v)
    else:
        story.append(Paragraph("……………………………………………", firma_c_s))
        story.append(Paragraph("<b>Parte Vendedora</b>", firma_c_s))
        story.append(Paragraph(f"Aclaración: {v1_nom}", firma_c_s))
        story.append(Paragraph(f"DNI: {v1_dni}", firma_c_s))

    story.append(hr(spb=14))

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN 3: NOTIFICACIÓN
    # ════════════════════════════════════════════════════════════════════════
    story.append(Paragraph(
        "NOTIFICACIÓN: Por la presente y en mi carácter de PARTE RESERVANTE/COMPRADORA del "
        "INMUEBLE, me NOTIFICO de la aceptación por la PARTE PROPIETARIA de la RESERVA "
        "aquí instrumentada.",
        body_s,
    ))

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph("…………………………………………", firma_c_s))
    story.append(Paragraph("<b>OFERENTE</b>", firma_c_s))
    story.append(Paragraph(f"Aclaración: {of_nom}", firma_c_s))
    story.append(Paragraph(f"DNI: {of_dni}", firma_c_s))

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
