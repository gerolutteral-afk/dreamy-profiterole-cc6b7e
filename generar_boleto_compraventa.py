#!/usr/bin/env python3
"""
Generador de Boleto de Compraventa — Calace Propiedades
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

# ── Constantes ──────────────────────────────────────────────────────────────
INMOBILIARIA = "Calace Propiedades"
MARTILLERO   = "Mariangeles Calace"
MAT_CMCPSI   = "7240"
MAT_CUCIBCA  = "9796"

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

# ── Número a letras ─────────────────────────────────────────────────────────
from reportlab.platypus import Image as RLImage
import os as _os

def numero_a_letras(n):
    UNIDADES = [
        "", "UNO", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE",
        "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISÉIS",
        "DIECISIETE", "DIECIOCHO", "DIECINUEVE",
    ]
    DECENAS = [
        "", "DIEZ", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA",
        "SESENTA", "SETENTA", "OCHENTA", "NOVENTA",
    ]
    CENTENAS = [
        "", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS",
        "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS",
    ]
    VEINTI = {
        1: "VEINTIUNO", 2: "VEINTIDÓS", 3: "VEINTITRÉS", 4: "VEINTICUATRO",
        5: "VEINTICINCO", 6: "VEINTISÉIS", 7: "VEINTISIETE", 8: "VEINTIOCHO",
        9: "VEINTINUEVE",
    }

    n = int(n)
    if n == 0:
        return "CERO"
    if n == 100:
        return "CIEN"
    if n == 1000:
        return "MIL"

    parts = []

    if n >= 1_000_000:
        m = n // 1_000_000
        r = n % 1_000_000
        parts.append("UN MILLÓN" if m == 1 else numero_a_letras(m) + " MILLONES")
        if r:
            parts.append(numero_a_letras(r))
        return " ".join(parts)

    if n >= 1_000:
        th = n // 1_000
        r  = n % 1_000
        parts.append("MIL" if th == 1 else numero_a_letras(th) + " MIL")
        if r:
            parts.append(numero_a_letras(r))
        return " ".join(parts)

    if n >= 100:
        c = n // 100
        r = n % 100
        parts.append(CENTENAS[c])
        if r:
            parts.append(numero_a_letras(r))
        return " ".join(parts)

    if n >= 20:
        d, u = divmod(n, 10)
        if d == 2 and u:
            return VEINTI[u]
        txt = DECENAS[d]
        if u:
            txt += " Y " + UNIDADES[u]
        return txt

    return UNIDADES[n]


def usd(n):
    """Devuelve (letras_completo, símbolo+número) para un monto en dólares."""
    return (
        f"DÓLARES ESTADOUNIDENSES BILLETES {numero_a_letras(int(n))}",
        f"U$S {int(n):,}",
    )


# ── Estilos ──────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "Titulo", parent=base["Normal"],
        fontSize=13, fontName="Helvetica-Bold",
        alignment=TA_CENTER, spaceAfter=16,
    )
    body = ParagraphStyle(
        "Cuerpo", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_JUSTIFY, spaceAfter=10, leading=15,
    )
    clause_title = ParagraphStyle(
        "ClausulaT", parent=base["Normal"],
        fontSize=10, fontName="Helvetica-Bold",
        alignment=TA_LEFT, spaceAfter=4, leading=14,
    )
    item = ParagraphStyle(
        "Item", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_JUSTIFY, spaceAfter=8, leading=14, leftIndent=18,
    )
    firma = ParagraphStyle(
        "Firma", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_LEFT, spaceAfter=3, leading=14,
    )
    firma_c = ParagraphStyle(
        "FirmaCentro", parent=base["Normal"],
        fontSize=10, fontName="Helvetica",
        alignment=TA_CENTER, spaceAfter=3, leading=14,
    )
    return title, body, clause_title, item, firma, firma_c


def hr(spb=4, spa=8):
    return HRFlowable(
        width="100%", thickness=0.5, color=colors.grey,
        spaceBefore=spb, spaceAfter=spa,
    )


# ── Helpers de texto ─────────────────────────────────────────────────────────
def g(genero, masc, fem):
    """Selecciona forma masculina o femenina según el género dado."""
    return masc if str(genero).lower() == "masculino" else fem


def persona_inline(nombre, genero, fecha_nac, dni, cuil):
    """Descripción inline de una persona para el encabezado del boleto."""
    nac = g(genero, "nacido", "nacida")
    arg = g(genero, "argentino", "argentina")
    return (
        f"<b>{nombre}</b>, {arg}, {nac} el <b>{fecha_nac}</b>, "
        f"titular del Documento Nacional de Identidad Nro. <b>{dni}</b>, "
        f"CUIT/CUIL <b>{cuil}</b>"
    )


# ── Secciones del documento ──────────────────────────────────────────────────
def partes_text(data):
    """Genera el párrafo introductorio con los datos de las partes."""
    dos_v = bool(data.get("vendedor2_nombre"))
    dos_c = bool(data.get("comprador2_nombre"))

    # — Vendedores —
    t1v = data["vendedor1_tratamiento"]
    v1  = persona_inline(
        data["vendedor1_nombre"], data["vendedor1_genero"],
        data["vendedor1_fecha_nac"], data["vendedor1_dni"], data["vendedor1_cuil"],
    )
    dom_v = (
        f"con domicilio en <b>{data['vendedores_domicilio']}</b>, "
        f"Localidad y Partido de <b>{data['vendedores_partido']}</b>, "
        f"<b>{data['vendedores_provincia']}</b>"
    )

    if dos_v:
        t2v = data["vendedor2_tratamiento"]
        v2  = persona_inline(
            data["vendedor2_nombre"], data["vendedor2_genero"],
            data["vendedor2_fecha_nac"], data["vendedor2_dni"], data["vendedor2_cuil"],
        )
        conyuges_v = data.get("vendedores_conyuges", False)
        intro_v    = "los cónyuges" if conyuges_v else "los señores"
        v_part = (
            f"Entre {intro_v} {t1v} {v1}, y {t2v} {v2}, ambos {dom_v}, "
            f"por una parte y en adelante denominada la parte \"<b>LA VENDEDORA</b>\""
        )
    else:
        art_v = "la" if t1v == "Sra." else "el"
        v_part = (
            f"Entre {art_v} {t1v} {v1}, {dom_v}, "
            f"por una parte y en adelante denominada la parte \"<b>LA VENDEDORA</b>\""
        )

    # — Compradores —
    t1c = data["comprador1_tratamiento"]
    c1  = persona_inline(
        data["comprador1_nombre"], data["comprador1_genero"],
        data["comprador1_fecha_nac"], data["comprador1_dni"], data["comprador1_cuil"],
    )

    if dos_c:
        t2c = data["comprador2_tratamiento"]
        c2  = persona_inline(
            data["comprador2_nombre"], data["comprador2_genero"],
            data["comprador2_fecha_nac"], data["comprador2_dni"], data["comprador2_cuil"],
        )
        conyuges_c = data.get("compradores_conyuges", False)
        intro_c    = "los cónyuges" if conyuges_c else "los señores"
        c_part = (
            f"y por la otra {intro_c} {t1c} {c1}, y {t2c} {c2}, ambos con domicilio en la calle "
            f"<b>{data['compradores_domicilio']}</b>, de <b>{data['compradores_ciudad']}</b>, "
            f"por la otra parte y en adelante denominada la parte \"<b>LA COMPRADORA</b>\""
        )
    else:
        art_c = "la" if t1c == "Sra." else "el"
        c_part = (
            f"y por la otra {art_c} {t1c} {c1}, con domicilio en la calle "
            f"<b>{data['compradores_domicilio']}</b>, de <b>{data['compradores_ciudad']}</b>, "
            f"por la otra parte y en adelante denominada la parte \"<b>LA COMPRADORA</b>\""
        )

    return (
        f"{v_part}; {c_part}; convienen en celebrar el presente Boleto de Compraventa, "
        f"sujeto a las siguientes cláusulas y condiciones:"
    )


def primera_text(data):
    """Genera el texto de la PRIMERA cláusula (descripción del inmueble)."""
    partido  = data["partido_inmueble"]
    provincia = data["provincia_inmueble"]
    calle    = data["calle_inmueble"]
    circ     = data["circ"]
    secc     = data["secc"]
    fracc    = data["fracc"]
    parc     = data["parc"]
    partida  = data["partida_inmobiliaria"]
    matricula = data["matricula"]

    catastro = (
        f"Nomenclatura Catastral: Circunscripción: <b>{circ}</b>, Sección: <b>{secc}</b>, "
        f"Fracción: <b>{fracc}</b>, Parcela: <b>{parc}</b>"
    )
    registro = (
        f"Partida Inmobiliaria <b>{partida}</b>; inscripto el Dominio en el Registro de la "
        f"Propiedad Inmueble en la matrícula <b>{matricula}</b>.-"
    )

    if data.get("es_ph"):
        uf          = data["uf"]
        poligonos   = data["poligonos"]
        condominio  = data["condominio_nombre"]
        entre       = data["entre_calles"]
        return (
            f"La vendedora vende a la compradora, y esta adquiere bajo el régimen de Propiedad "
            f"Horizontal, la Unidad Funcional Nro. <b>{uf}</b>, integrada por los POLÍGONOS "
            f"<b>{poligonos}</b> que forma parte del Condominio denominado <b>{condominio}</b>, "
            f"sito en la Localidad y Partido de <b>{partido}</b>, Provincia de <b>{provincia}</b>, "
            f"con frente a la calle <b>{calle}</b>, entre las de <b>{entre}</b>; "
            f"{catastro}; {registro}"
        )
    else:
        numero = data.get("numero_inmueble") or ""
        calle_str = (
            f"<b>{calle}</b> Nro. <b>{numero}</b>" if numero else f"<b>{calle}</b>"
        )
        return (
            f"La vendedora vende a la compradora, y esta adquiere el inmueble sito en la "
            f"Localidad y Partido de <b>{partido}</b>, Provincia de <b>{provincia}</b>, "
            f"con frente a la calle {calle_str}; "
            f"{catastro}; {registro}"
        )


def cuarta_text(data):
    """Genera el texto de la CUARTA cláusula (escribano y escritura)."""
    fecha_esc    = data["fecha_escritura"]
    esc_gen      = data.get("escribano_genero", "escribano")
    esc_nom      = data["escribano_nombre"]
    esc_reg      = data["escribano_registro"]
    esc_prov     = data["escribano_provincia"]
    esc_tel      = data["escribano_telefono"]
    esc_dir      = data["escribano_direccion"]
    prov_inmueble = data["provincia_inmueble"]

    art_esc = "la" if esc_gen == "escribana" else "el"
    return (
        f"La Escritura Traslativa de Dominio y entrega de la Posesión se otorgará a más "
        f"tardar el <b>{fecha_esc}</b>, por ante {art_esc} <b>{esc_gen} {esc_nom}</b> "
        f"(Registro N° <b>{esc_reg}</b> de <b>{esc_prov}</b>) – teléfono <b>{esc_tel}</b>, "
        f"con oficinas en la calle <b>{esc_dir}</b>. "
        f"Los gastos, honorarios e impuestos propios de la escrituración serán afrontados por "
        f"las partes conforme usos y costumbres. Se deja constancia que la vendedora se obliga "
        f"a entregar en tiempo y forma al escribano designado la documentación original "
        f"perteneciente al Inmueble objeto del presente. El escribano designado citará a las "
        f"partes en forma fehaciente con una antelación de por lo menos cinco días hábiles "
        f"respecto a la fecha máxima convenida para el acto escriturario. \"LA VENDEDORA\" se "
        f"compromete y obliga a cumplir con todo lo establecido por la ley 10707, sobre la "
        f"actualización del estado parcelario, designando agrimensor y asumiendo los gastos que "
        f"ello implica. La cédula catastral correspondiente le será entregada al escribano "
        f"interviniente con una antelación mínima de quince (15) días a la fecha de "
        f"escrituración. El plazo de escrituración podrá prorrogarse sin penalidad alguna para "
        f"las partes, en caso de demoras administrativas correspondientes al Registro de la "
        f"Propiedad Inmueble o el Catastro de <b>{prov_inmueble}</b>.-"
    )


def septima_text(data):
    """Genera el texto de la SÉPTIMA cláusula (informes registrales)."""
    fecha_inf = data["fecha_informes"]
    inf1      = data["informe_1"]
    inf2      = data["informe_2"]
    inf3      = data["informe_3"]
    return (
        f"Se deja expresa constancia que el presente boleto de compraventa se firma con los "
        f"correspondientes informes del estado de dominio y anotaciones personales a la vista, "
        f"solicitados al Registro de la Propiedad Inmueble de la Prov. de Bs. As., el "
        f"<b>{fecha_inf}</b>, con los números <b>{inf1}</b>, <b>{inf2}</b> y <b>{inf3}</b>, "
        f"respectivamente; de los cuales resulta que el dominio no presenta gravamen alguno, "
        f"y que la vendedora no se encuentra inhibida.-"
    )


def decima_text(data):
    """Genera el texto de la DÉCIMA cláusula (jurisdicción)."""
    jurisdiccion = data["jurisdiccion"]
    return (
        f"Para todos los efectos legales derivados de este Boleto de Compraventa, las partes "
        f"se someten a la jurisdicción de los Tribunales Ordinarios de "
        f"<b>{jurisdiccion}</b>, renunciando a cualquier otro fuero o jurisdicción que pudiere "
        f"corresponder. Fijando domicilios legales y especiales, a los efectos de cualquier "
        f"notificación o citación judicial o extrajudicial, en los arriba mencionados.-"
    )


def cierre_text(data):
    """Genera el párrafo de cierre y firma."""
    hoy       = date.today()
    dia       = hoy.day
    mes       = MESES_ES[hoy.month]
    anio      = hoy.year
    localidad = data["localidad_firma"]
    provincia = data["provincia_firma"]
    return (
        f"Leída y de conformidad, se firman dos (2) ejemplares de un mismo contenido y a un "
        f"solo efecto, en la localidad de <b>{localidad}</b>, Provincia de <b>{provincia}</b>, "
        f"a los <b>{dia}</b> días del mes de <b>{mes}</b> de <b>{anio}</b>."
    )


# ── Bloques de firma ─────────────────────────────────────────────────────────
def firma_vendedor_lines(data):
    lines = ["<b>Firma y aclaración</b>", "<b>LA VENDEDORA</b>"]
    lines.append(data["vendedor1_nombre"])
    lines.append(f"DNI {data['vendedor1_dni']}")
    if data.get("vendedor2_nombre"):
        lines.append("")
        lines.append(data["vendedor2_nombre"])
        lines.append(f"DNI {data['vendedor2_dni']}")
    return "<br/>".join(lines)


def firma_comprador_lines(data):
    lines = ["<b>Firma y aclaración</b>", "<b>LA COMPRADORA</b>"]
    lines.append(data["comprador1_nombre"])
    lines.append(f"DNI {data['comprador1_dni']}")
    if data.get("comprador2_nombre"):
        lines.append("")
        lines.append(data["comprador2_nombre"])
        lines.append(f"DNI {data['comprador2_dni']}")
    return "<br/>".join(lines)


# ── Build PDF ─────────────────────────────────────────────────────────────────
def build_pdf(data, output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=2.5 * cm, leftMargin=2.5 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
    )

    title_s, body_s, ct_s, item_s, firma_s, firma_c_s = make_styles()
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

    # ── Título ──
    story.append(Paragraph("BOLETO DE COMPRAVENTA", title_s))

    # ── PARTES ──
    story.append(Paragraph(partes_text(data), body_s))
    story.append(hr())

    # ── PRIMERA ──
    story.append(Paragraph("<b>PRIMERA:</b>", ct_s))
    story.append(Paragraph(primera_text(data), body_s))
    story.append(hr())

    # ── SEGUNDA (fija) ──
    story.append(Paragraph("<b>SEGUNDA:</b>", ct_s))
    story.append(Paragraph(
        "La presente venta se realiza en base a títulos perfectos, libre de todo gravamen y/o "
        "inhibiciones, libre de ocupantes y/o intrusos y sin oposición de terceros. Los "
        "impuestos, tasas, servicios y contribuciones correspondientes al inmueble objeto de "
        "este boleto se encontrarán pagos al día de la fecha de la Escritura Traslativa de "
        "Dominio y entrega de la Posesión. Sin perjuicio de lo mencionado, se deja constancia "
        "que el Inmueble objeto del presente Boleto se encuentra afectado al Régimen de "
        "Vivienda Familiar, obligándose la PARTE VENDEDORA a desafectarlo en simultáneo con "
        "la Escritura Traslativa de Dominio.-",
        body_s,
    ))
    story.append(hr())

    # ── TERCERA ──
    story.append(Paragraph("<b>TERCERA:</b>", ct_s))
    total_let, total_num     = usd(data["precio_total_usd"])
    acuenta_let, acuenta_num = usd(data["monto_acuenta_usd"])
    saldo_let, saldo_num     = usd(data["saldo_usd"])

    story.append(Paragraph(
        f"El precio total y convenido para esta venta se fija en la suma de "
        f"<b>{total_let} ({total_num})</b>, pagaderos de la siguiente forma:",
        body_s,
    ))
    story.append(Paragraph(
        f"a) la suma de <b>{acuenta_let} ({acuenta_num})</b> a cuenta de precio y principio "
        f"de ejecución, que son abonados en este acto por la compradora en efectivo y que la "
        f"vendedora declara recibir, sirviendo el presente de suficiente recibo y carta de "
        f"pago en forma;",
        item_s,
    ))
    story.append(Paragraph(
        f"b) la suma de <b>{saldo_let} ({saldo_num})</b> como saldo de precio, los abonará "
        f"la compradora a la vendedora al momento de la firma de la Escritura Traslativa de "
        f"Dominio y entrega de la Posesión.-",
        item_s,
    ))
    story.append(hr())

    # ── CUARTA ──
    story.append(Paragraph("<b>CUARTA:</b>", ct_s))
    story.append(Paragraph(cuarta_text(data), body_s))
    story.append(hr())

    # ── QUINTA (fija) ──
    story.append(Paragraph("<b>QUINTA:</b>", ct_s))
    story.append(Paragraph(
        "Las partes pactan la mora automática para todas las obligaciones emergentes de este "
        "boleto, por lo que ella se producirá en todos los casos por el mero vencimiento de "
        "los plazos. Si a la fecha indicada para la escrituración, y sin necesidad de "
        "intimación judicial o extrajudicial alguna, la compradora no se presentara a firmar "
        "la escritura de compraventa, la vendedora quedará habilitada para utilizar la acción "
        "de cumplimiento demandado judicialmente la escrituración pendiente; estipulándose "
        "para ese caso en concepto de penalidad, una multa de Dólares Estadounidenses Billete "
        "CIENTO CINCUENTA (U$S 150.-) por cada día de retardo en el cumplimiento de su "
        "obligación. Si quien no concurriere a escriturar fuera la vendedora, la compradora "
        "quedará habilitada para ejercer la acción de cumplimiento; estipulándose para ese "
        "caso una multa de Dólares Estadounidenses Billete CIENTO CINCUENTA (U$S 150.-), por "
        "cada día de retardo en el cumplimiento de su obligación, en concepto de penalidad, "
        "que podrá descontar del saldo de precio de compra cuando se opere el cumplimiento.- "
        "Se deja constancia, y así las partes lo acuerdan, que si se cumple el plazo acordado, "
        "y esto es por causas y/o motivos ajenos a las partes, como ser demora en la "
        "expedición de certificados, paros en las entidades intervinientes, demoras por temas "
        "Catastrales, Municipales, Registro de la Propiedad, impedimento o cese de actividades "
        "por causa de la pandemia, se viera prorrogado de hecho el plazo de la escritura, esta "
        "situación no producirá mora y sólo extenderá los plazos, no pudiendo reclamar las "
        "partes por estos motivos, ni exigir el pago de las multas.-",
        body_s,
    ))
    story.append(hr())

    # ── SEXTA (fija) ──
    story.append(Paragraph("<b>SEXTA:</b>", ct_s))
    story.append(Paragraph(
        "El presente boleto es intransferible, quedando prohibido a la compradora transferir "
        "o de algún modo ceder los derechos y acciones emergentes de él, sin la conformidad "
        "expresada por escrito ante escribano público por la vendedora.-",
        body_s,
    ))
    story.append(hr())

    # ── SÉPTIMA ──
    story.append(Paragraph("<b>SÉPTIMA:</b>", ct_s))
    story.append(Paragraph(septima_text(data), body_s))
    story.append(hr())

    # ── OCTAVA (fija) ──
    story.append(Paragraph("<b>OCTAVA:</b>", ct_s))
    story.append(Paragraph(
        "Es condición esencial de esta operación que el saldo de precio sea abonado "
        "íntegramente en billetes dólares estadounidenses. La compradora deja constancia que "
        "se encuentra debidamente asesorada en cuanto a la situación y riesgos de tipo "
        "cambiario y económico del país, renunciando por consiguiente a hacer valer ante la "
        "vendedora, tanto la teoría de la imprevisión con fundamento en eventuales "
        "alteraciones de esa naturaleza, así como la imposibilidad de adquirir dicha moneda "
        "por no estar autorizada la venta al público o por otros motivos; manifestando además "
        "la compradora que a la fecha posee el saldo de precio en la moneda indicada, y que "
        "lo mantiene reservado en su poder a efectos de afrontar el pago comprometido en la "
        "presente operación. Asimismo, y de acuerdo con ello, la compradora asume el caso "
        "fortuito que pudiera ocurrir al respecto. Por tal motivo queda debidamente aclarado "
        "que la moneda convenida para el pago del saldo de precio de esta compraventa no "
        "podrá ser sustituida por otra moneda que no sea la aquí pactada como cláusula "
        "esencial.-",
        body_s,
    ))
    story.append(hr())

    # ── NOVENA (fija) ──
    story.append(Paragraph("<b>NOVENA:</b>", ct_s))
    story.append(Paragraph(
        "FALLECIMIENTO, INCAPACIDAD O INHABILITACIÓN DE LA COMPRADORA Y/O VENDEDORES. En "
        "caso de fallecimiento, incapacidad o inhabilitación legalmente declarada del "
        "comprador y/o del vendedor, o sus herederos, deberán unificar representación en el "
        "primer caso, y su representante legal en los restantes, deberán tomar a su cargo y "
        "asumir las obligaciones contraídas por la compradora y/o vendedores según corresponda "
        "el caso conforme este boleto, dentro de los treinta (30) días corridos de ocurrido el "
        "fallecimiento o declarada la incapacidad o inhabilitación legal, so pena de incurrir "
        "en mora.-",
        body_s,
    ))
    story.append(hr())

    # ── DÉCIMA ──
    story.append(Paragraph("<b>DÉCIMA:</b>", ct_s))
    story.append(Paragraph(decima_text(data), body_s))
    story.append(hr())

    # ── Cierre ──
    story.append(Paragraph(cierre_text(data), body_s))

    # ── Firmas: Vendedor / Comprador ──
    story.append(Spacer(1, 0.6 * cm))
    col_v = Paragraph(firma_vendedor_lines(data), firma_s)
    col_c = Paragraph(firma_comprador_lines(data), firma_s)

    tabla_firmas = Table(
        [[col_v, col_c]],
        colWidths=[8 * cm, 8 * cm],
    )
    tabla_firmas.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
    ]))
    story.append(tabla_firmas)

    # ── Corredor interviniente ──
    story.append(Spacer(1, 0.6 * cm))
    story.append(hr(spb=2, spa=6))
    story.append(Paragraph(
        f"<b>Corredor interviniente</b><br/>"
        f"{MARTILLERO}<br/>"
        f"CMCPSI N° {MAT_CMCPSI} / CUCIBCA N° {MAT_CUCIBCA}<br/>"
        f"{INMOBILIARIA}",
        firma_c_s,
    ))

    doc.build(story)
    print(f"PDF generado: {output_path}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Genera Boleto de Compraventa en PDF")
    parser.add_argument("--data-file", required=True, help="Ruta al JSON de datos")
    parser.add_argument("--output",    required=True, help="Ruta del PDF de salida")
    args = parser.parse_args()

    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    build_pdf(data, args.output)


if __name__ == "__main__":
    main()
