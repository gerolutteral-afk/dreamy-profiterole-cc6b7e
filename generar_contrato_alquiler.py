#!/usr/bin/env python3
"""
Genera un PDF del Contrato de Locación de Vivienda para Calace Propiedades.
26 cláusulas legales completas con datos variables de las partes.
"""

import argparse
import json
import calendar
import sys
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.colors import HexColor


# ─── Helpers de lenguaje ──────────────────────────────────────────────────────

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

VEINTI = {
    1: "VEINTIÚN", 2: "VEINTIDÓS", 3: "VEINTITRÉS", 4: "VEINTICUATRO",
    5: "VEINTICINCO", 6: "VEINTISÉIS", 7: "VEINTISIETE", 8: "VEINTIOCHO",
    9: "VEINTINUEVE"
}


from reportlab.platypus import Image as RLImage
import os as _os

def numero_a_letras(n):
    """Convierte un entero positivo a palabras en español (mayúsculas)."""
    if n == 0:
        return "CERO"

    unidades = [
        "", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS",
        "SIETE", "OCHO", "NUEVE", "DIEZ", "ONCE", "DOCE", "TRECE",
        "CATORCE", "QUINCE", "DIECISÉIS", "DIECISIETE", "DIECIOCHO", "DIECINUEVE"
    ]
    decenas = [
        "", "DIEZ", "VEINTE", "TREINTA", "CUARENTA", "CINCUENTA",
        "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"
    ]
    centenas = [
        "", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS",
        "QUINIENTOS", "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"
    ]

    def menor_mil(num):
        if num == 0:
            return ""
        elif num == 100:
            return "CIEN"
        elif num < 20:
            return unidades[num]
        elif num < 30:
            u = num % 10
            if u == 0:
                return "VEINTE"
            return VEINTI[u]
        elif num < 100:
            d, u = divmod(num, 10)
            if u == 0:
                return decenas[d]
            return f"{decenas[d]} Y {unidades[u]}"
        else:
            c, resto = divmod(num, 100)
            if resto == 0:
                return centenas[c]
            return f"{centenas[c]} {menor_mil(resto)}"

    if n < 1000:
        return menor_mil(n)
    elif n < 2000:
        resto = n % 1000
        return "MIL" if resto == 0 else f"MIL {menor_mil(resto)}"
    elif n < 1_000_000:
        miles, resto = divmod(n, 1000)
        parte = menor_mil(miles)
        return f"{parte} MIL" if resto == 0 else f"{parte} MIL {menor_mil(resto)}"
    elif n < 2_000_000:
        resto = n % 1_000_000
        return "UN MILLÓN" if resto == 0 else f"UN MILLÓN {numero_a_letras(resto)}"
    else:
        millones, resto = divmod(n, 1_000_000)
        parte = numero_a_letras(millones)
        return f"{parte} MILLONES" if resto == 0 else f"{parte} MILLONES {numero_a_letras(resto)}"


def fmt_pesos(n):
    """Formatea un número como pesos argentinos: 850.000"""
    return f"{n:,.0f}".replace(",", ".")


def fmt_dolares(n):
    """Formatea un número como dólares: 3.000"""
    return f"{n:,.0f}".replace(",", ".")


def fecha_desde_string(s):
    """Parsea DD/MM/AAAA → date."""
    return datetime.strptime(s.strip(), "%d/%m/%Y").date()


def sumar_meses(d, meses):
    """Suma N meses a una fecha, respetando fin de mes."""
    total = d.month - 1 + meses
    year = d.year + total // 12
    month = total % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def fmt_fecha_larga(d):
    """Devuelve '1 de junio de 2025'."""
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def fmt_fecha_hoy():
    """Devuelve fecha actual como 'X días del mes de MES de AÑO'."""
    h = datetime.now()
    return f"{h.day} días del mes de {MESES[h.month - 1]} de {h.year}"


# ─── Generación del PDF ───────────────────────────────────────────────────────

def build_pdf(data, output_path):
    loc1 = data["locador1"]
    loc2 = data.get("locador2")
    lct = data["locatario"]
    inm = data["inmueble"]
    contrato = data["contrato"]
    fid1 = data["fiador1"]
    fid2 = data.get("fiador2")
    garantia = data["garantia"]
    rpi = data["rpi"]
    localidad = data["localidad_firma"]

    # ─ Fechas ─
    fecha_inicio = fecha_desde_string(contrato["fecha_inicio"])
    plazo = int(contrato["plazo_meses"])
    fecha_venc = sumar_meses(fecha_inicio, plazo)
    primer_ajuste = sumar_meses(fecha_inicio, 4)
    primer_ajuste_txt = f"{MESES[primer_ajuste.month - 1]} del año {primer_ajuste.year}"

    # ─ Importes ─
    precio = int(contrato["precio_mensual"])
    deposito = int(contrato["deposito_dolares"])
    precio_letras = numero_a_letras(precio)
    deposito_letras = numero_a_letras(deposito)
    plazo_letras = numero_a_letras(plazo)
    mes_prop = MESES[fecha_inicio.month - 1].upper()
    anio_prop = fecha_inicio.year

    # ─ Descripción del inmueble ─
    cochera = inm.get("cochera")
    emprendimiento = inm.get("emprendimiento")

    if cochera:
        inmueble_base = (
            f'calle <b>{inm["calle"]}</b>, piso <b>{inm["piso"]}</b>, '
            f'UF Nro. <b>{inm["uf"]}</b>, junto con la cochera Nro. <b>{cochera}</b>, '
            f'ubicada en Planta baja'
        )
        if emprendimiento:
            inmueble_base += f', ambas sitas en el emprendimiento denominado "<b>{emprendimiento}</b>"'
    else:
        inmueble_base = (
            f'calle <b>{inm["calle"]}</b>, piso <b>{inm["piso"]}</b>, '
            f'UF Nro. <b>{inm["uf"]}</b>'
        )
        if emprendimiento:
            inmueble_base += f', sito en el emprendimiento denominado "<b>{emprendimiento}</b>"'

    inmueble_base += f', de <b>{localidad}</b>'

    # ─ Intro locador ─
    es_sra1 = "Sra" in loc1["genero"]
    if loc2:
        locador_intro = (
            f'Los cónyuges {loc1["genero"]} <b>{loc1["nombre"]}</b>, '
            f'DNI Nro. <b>{loc1["dni"]}</b>, y {loc2["genero"]} <b>{loc2["nombre"]}</b>, '
            f'DNI Nro. <b>{loc2["dni"]}</b>, '
            f'domiciliados en la calle <b>{loc1["domicilio"]}</b>, '
            f'Provincia de <b>{loc1["provincia"]}</b>, '
            f'con domicilio electrónico <b>{loc1["email"]}</b>, '
            f'Celular: <b>{loc1["celular"]}</b>, '
            f'en adelante llamados <b>"LA LOCADORA"</b>'
        )
    else:
        dom_lbl = "domiciliada" if es_sra1 else "domiciliado"
        llam_lbl = "llamada" if es_sra1 else "llamado"
        locador_intro = (
            f'{loc1["genero"]} <b>{loc1["nombre"]}</b>, '
            f'DNI Nro. <b>{loc1["dni"]}</b>, '
            f'{dom_lbl} en la calle <b>{loc1["domicilio"]}</b>, '
            f'Provincia de <b>{loc1["provincia"]}</b>, '
            f'con domicilio electrónico <b>{loc1["email"]}</b>, '
            f'Celular: <b>{loc1["celular"]}</b>, '
            f'en adelante {llam_lbl} <b>"LA LOCADORA"</b>'
        )

    # ─ Intro locatario ─
    es_sra_lct = "Sra" in lct["genero"]
    dom_lct = "domiciliada" if es_sra_lct else "domiciliado"
    locatario_intro = (
        f'{lct["genero"]} <b>{lct["nombre"]}</b>, '
        f'DNI Nro. <b>{lct["dni"]}</b>, '
        f'{dom_lct} en <b>{lct["domicilio"]}</b>, '
        f'con domicilio electrónico <b>{lct["email"]}</b>, '
        f'Celular: <b>{lct["celular"]}</b>, '
        f'en adelante llamado <b>"EL LOCATARIO"</b>'
    )

    # ─ Fiadores ─
    if fid2:
        fiadores_intro = (
            f'{fid1["genero"]} <b>{fid1["nombre"]}</b>, DNI Nro. <b>{fid1["dni"]}</b>, '
            f'con domicilio en <b>{fid1["domicilio"]}</b>, <b>{fid1["barrio"]}</b>, '
            f'Provincia de <b>{fid1["provincia"]}</b>, mail <b>{fid1["mail"]}</b>, '
            f'y {fid2["genero"]} <b>{fid2["nombre"]}</b>, DNI Nro. <b>{fid2["dni"]}</b>, '
            f'con domicilio en <b>{fid2["domicilio"]}</b>, <b>{fid2["barrio"]}</b>, '
            f'Provincia de <b>{fid2["provincia"]}</b>, mail <b>{fid2["mail"]}</b>'
        )
        fiadores_rpi = f'<b>{fid1["nombre"]}</b> y <b>{fid2["nombre"]}</b>'
    else:
        fiadores_intro = (
            f'{fid1["genero"]} <b>{fid1["nombre"]}</b>, DNI Nro. <b>{fid1["dni"]}</b>, '
            f'con domicilio en <b>{fid1["domicilio"]}</b>, <b>{fid1["barrio"]}</b>, '
            f'Provincia de <b>{fid1["provincia"]}</b>, mail <b>{fid1["mail"]}</b>'
        )
        fiadores_rpi = f'<b>{fid1["nombre"]}</b>'

    # ─ Inmueble de garantía ─
    garantia_desc = (
        f'el inmueble sito en la calle <b>{garantia["calle"]}</b>, '
        f'Unidad Funcional Nro. <b>{garantia["uf"]}</b>, '
        f'ubicada en el piso <b>{garantia["piso"]}</b>, '
        f'<b>{garantia["ciudad"]}</b>. '
        f'Nomenclatura Catastral: Circ.: <b>{garantia["circ"]}</b>; '
        f'Secc.: <b>{garantia["sec"]}</b>; '
        f'Manz.: <b>{garantia["manz"]}</b>; '
        f'Parc.: <b>{garantia["parc"]}</b>. '
        f'Matrícula: <b>{garantia["matricula"]}</b>'
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Setup PDF
    # ─────────────────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
    )

    styles = getSampleStyleSheet()

    title_s = ParagraphStyle(
        "T", parent=styles["Title"],
        fontSize=13, fontName="Helvetica-Bold",
        spaceAfter=10, alignment=TA_CENTER,
        textColor=HexColor("#1a1a1a"),
    )
    body_s = ParagraphStyle(
        "B", parent=styles["Normal"],
        fontSize=9.5, fontName="Helvetica",
        leading=13, alignment=TA_JUSTIFY, spaceAfter=5,
    )
    clause_s = ParagraphStyle(
        "C", parent=body_s,
        fontName="Helvetica-Bold", spaceAfter=2, spaceBefore=8,
    )
    firma_s = ParagraphStyle(
        "F", parent=styles["Normal"],
        fontSize=9.5, fontName="Helvetica",
        leading=13, alignment=TA_LEFT, spaceAfter=2,
    )
    firma_bold_s = ParagraphStyle(
        "FB", parent=firma_s, fontName="Helvetica-Bold",
    )

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

    def p(text, style=body_s):
        story.append(Paragraph(text, style))

    def sp(n=6):
        story.append(Spacer(1, n))

    def hr():
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#444444")))

    # ─────────────────────────────────────────────────────────────────────────
    # TÍTULO
    # ─────────────────────────────────────────────────────────────────────────
    p("CONTRATO DE LOCACIÓN DE VIVIENDA", title_s)
    sp(4)

    # Introducción
    intro = (
        f'Entre {locador_intro}, por una parte, y {locatario_intro}, '
        f'por la otra parte, ambas partes hábiles para la realización de este acto '
        f'(en adelante para abreviar LAS PARTES), convienen en celebrar el presente '
        f'<b>CONTRATO DE LOCACIÓN</b>, sujeto a las siguientes cláusulas y condiciones '
        f'particulares:'
    )
    p(intro)
    hr()
    sp(4)

    # ─────────────────────────────────────────────────────────────────────────
    # CLÁUSULAS
    # ─────────────────────────────────────────────────────────────────────────

    # PRIMERA – OBJETO
    p("<b>PRIMERA – OBJETO:</b>", clause_s)
    p(
        f'La "LOCADORA" da en locación al "LOCATARIO" y éste acepta, el inmueble de la '
        f'{inmueble_base}, quien lo acepta de conformidad, libre de intrusos y/u ocupantes, '
        f'con todos sus vidrios, herrajes, instalaciones sanitarias y eléctricas, en el estado '
        f'de conservación e higiene en el que actualmente se encuentran por haberlos visitado y '
        f'observado detalladamente, comprometiéndose EL LOCATARIO a reintegrarlo en el mismo '
        f'estado de uso y conservación y con las mejoras que pudiera incorporar, las que quedarán '
        f'en favor de LA LOCADORA sin que deba mediar contraprestación de ninguna naturaleza.'
    )

    # SEGUNDA – PLAZO
    p("<b>SEGUNDA – PLAZO:</b>", clause_s)
    p(
        f'El plazo del presente contrato se establece en <b>{plazo_letras} ({plazo})</b> meses '
        f'que comenzarán a regir desde el día <b>{fmt_fecha_larga(fecha_inicio)}</b>, '
        f'venciendo en consecuencia, el día <b>{fmt_fecha_larga(fecha_venc)}</b>, de pleno '
        f'derecho y sin necesidad de interpelación alguna. En caso de que EL LOCATARIO continuara '
        f'en ocupación del Inmueble vencido el plazo pactado, no será interpretado como una '
        f'prórroga y/o reconducción tácita del presente contrato. El término de la locación es '
        f'total y absolutamente perentorio, debiendo a su finalización restituirse el bien locado '
        f'sin demora o excusa alguna. Se deja constancia que el presente contrato se realiza bajo '
        f'el régimen de libre contratación, rigiéndose por las disposiciones del CCCN y en el '
        f'marco del decreto ley Nro. 70/2023, publicado en el Boletín Oficial el día 21/12/2023, '
        f'con exclusión de cualquier régimen de emergencia futuro que se sancionare en materia '
        f'de locaciones.'
    )

    # TERCERA – DESTINO
    p("<b>TERCERA – DESTINO:</b>", clause_s)
    p(
        'El "LOCATARIO" destinará el inmueble locado exclusivamente para vivienda propia y de sus '
        'familiares directos. EL LOCATARIO no podrá cambiar dicha afectación siendo su '
        'incumplimiento pasible de resolución del presente contrato.'
    )

    # CUARTA – PRECIO
    p("<b>CUARTA – PRECIO:</b>", clause_s)
    p(
        f'El precio del alquiler mensual es de Pesos <b>{precio_letras} ($ {fmt_pesos(precio)}.-)</b>, '
        f'mensuales. Los alquileres serán abonados por mes adelantado del día 1 al 5 de cada mes '
        f'en el domicilio de LA LOCADORA o bien transferidos a su cuenta bancaria o en el domicilio '
        f'en donde ésta indique, produciéndose la mora de pleno derecho, por el sólo vencimiento '
        f'del plazo fijado, sin necesidad de intimación previa alguna. El alquiler se pacta por '
        f'período de mes entero y aunque EL LOCATARIO reintegrará el inmueble antes de finalizado '
        f'el mes, deberá abonar íntegramente el alquiler correspondiente a ese mes. Asimismo las '
        f'partes acuerdan un ajuste cuatrimestral sobre el alquiler mensual acordando utilizar el '
        f'índice de precios al consumidor (IPC), que elabora y publica el INDEC, acumulando los '
        f'últimos cuatro (4) porcentuales publicados al momento de realizar la facturación del mes '
        f'en que se practica el aumento, respectivamente. El primer ajuste se realizará en el mes '
        f'de <b>{primer_ajuste_txt}</b>. Al término de cada período de cuatro meses, este '
        f'procedimiento será repetido, siendo las actualizaciones acumulativas. Si el índice de '
        f'actualización se demora en su publicación, la diferencia que pudiera llegar a surgir '
        f'deberá ser abonada por EL LOCATARIO en el plazo de 5 días de conocido el índice '
        f'publicado con posterioridad. Si durante el transcurso del presente contrato, en algún '
        f'cuatrimestre se produjera deflación reflejado en el índice IPC, no se aplicará ningún '
        f'aumento, y el monto del alquiler seguirá igual al cuatrimestre anterior. En caso de que '
        f'el índice pactado dejara de publicarse, las partes acuerdan utilizar un índice equivalente '
        f'que refleje la variación del valor de mercado de los alquileres. La actualización será '
        f'automática y obligatoria para ambas partes, sin necesidad de notificación expresa. En '
        f'caso de incumplimiento en el pago del canon locativo mensual, las partes acuerdan la '
        f'mora automática, acordando adicionalmente una tasa de interés punitorio del diez por '
        f'ciento (10%) mensual sobre el monto adeudado. De verse obligada la "LOCADORA" a intimar '
        f'al "LOCATARIO" para obtener el cobro de las obligaciones contraídas, este último deberá '
        f'abonar además del alquiler pactado los gastos y honorarios que se devengaren por dicha '
        f'intimación. Para el caso en que la presente locación tributara I.V.A., el mismo deberá '
        f'ser abonado por EL LOCATARIO conjuntamente con el pago de cada cuota mensual. EL '
        f'LOCATARIO abona en este acto el proporcional del alquiler del mes de <b>{mes_prop} DE '
        f'{anio_prop}</b>, sirviendo el presente como suficiente recibo de pago.'
    )

    # QUINTA – CLÁUSULA PENAL
    p("<b>QUINTA – CLÁUSULA PENAL:</b>", clause_s)
    p(
        'Al vencimiento del plazo de la locación, será obligación de EL LOCATARIO restituir el '
        'inmueble en buenas condiciones y libre de ocupantes sin interpelación alguna, caso '
        'contrario deberá abonar a la LOCADORA como cláusula penal la suma de dólares billetes '
        'estadounidenses DOSCIENTOS (U$S 200.-) por día y hasta la restitución del inmueble, '
        'pactándose para su cobro la vía procesal ejecutiva. La cláusula penal por la no '
        'restitución de la locación es independiente del pago del alquiler y del derecho de '
        'accionar que tendrá la LOCADORA por incumplimiento de EL LOCATARIO, sea por mora en el '
        'pago de alquileres, tributos, tasas, contribuciones, etc. En todos los casos de '
        'incumplimiento la mora será automática sin interpelación previa alguna.'
    )

    # SEXTA – INTRANSFERIBILIDAD
    p("<b>SEXTA – INTRANSFERIBILIDAD:</b>", clause_s)
    p(
        'Queda absolutamente prohibido para EL LOCATARIO subarrendar y/o subalquilar el inmueble '
        'como así también, la transferencia del presente contrato o la celebración de contratos '
        'de comodato, ya sea en forma parcial o total, sin la expresa conformidad por escrito de '
        'LA LOCADORA. También está absolutamente prohibido guardar materiales explosivos e '
        'inflamables, usar EL INMUEBLE con destino comercial o como depósito de mercadería de '
        'terceros, aun en forma parcial o bien realizar cualquier acto o hecho que pudiera causar '
        'perjuicios o molestias, a LA LOCADORA, al inmueble o a los vecinos. Tampoco podrá tener '
        'EL LOCATARIO en EL INMUEBLE cosas materiales que pudieren afectar la seguridad de las '
        'personas, objetos e instalaciones, ni realizar actos que contraríen las normas municipales '
        'vigentes, el reglamento de copropiedad e interno del edificio, la moral y las buenas '
        'costumbres.'
    )

    # SÉPTIMA – MEJORAS
    p("<b>SÉPTIMA – MEJORAS:</b>", clause_s)
    p(
        'EL LOCATARIO recibe de conformidad EL INMUEBLE en el estado de conservación e higiene '
        'en el que actualmente se encuentra, por haberlo visitado y observado detalladamente, '
        'libre de ocupantes e intrusos. Asimismo, las partes convienen en que las mejoras que '
        'EL LOCATARIO realice en el inmueble, durante la relación contractual, quedarán en '
        'beneficio de LA LOCADORA, sin derecho a reclamo indemnizatorio alguno por parte del '
        'inquilino. En el hipotético caso de que EL LOCATARIO decidiera la realización de obras '
        'que sustancialmente modifiquen la estructura de EL INMUEBLE, este deberá solicitar por '
        'escrito la autorización expresa de LA LOCADORA. EL LOCATARIO manifiesta que, al momento '
        'de la celebración del presente contrato, ha inspeccionado el inmueble locado y declara '
        'conocer y aceptar su estado de conservación y mantenimiento, renunciando expresamente a '
        'formular reclamo alguno por tal situación.'
    )

    # OCTAVA – CONSERVACIÓN
    p("<b>OCTAVA – CONSERVACIÓN:</b>", clause_s)
    p(
        'Serán por cuenta del "LOCATARIO" la conservación de los artefactos y accesorios de la '
        'propiedad, y las reparaciones de los desperfectos provocados por su mal uso. EL LOCATARIO '
        'se compromete a dar aviso inmediato a LA LOCADORA de todo deterioro que se produzca en '
        'EL INMUEBLE, permitiendo la ejecución de todo trabajo que sea necesario para su '
        'conservación o mejora, sin derecho a cobrar indemnización alguna. En caso de emergencia, '
        'EL LOCATARIO deberá aislar la parte afectada y hacer los arreglos que eviten males '
        'mayores. Serán a su cargo además los daños que pudieran ocasionar a EL INMUEBLE, a '
        'vecinos o a terceros, por demora, negligencia, impericia o imprevisión de su parte. '
        'LA LOCADORA no se responsabiliza de los daños y perjuicios que pudieran producirle a '
        'EL LOCATARIO o a terceros los accidentes que pudieran ocurrir en EL INMUEBLE. EL '
        'LOCATARIO contratará un seguro durante todo el período locativo, en una compañía de '
        'seguros reconocida, dentro de las autorizadas por la Superintendencia de Seguros de la '
        'Nación Argentina. Dicha póliza deberá contratarse dentro de los diez (10) días de '
        'celebrado el presente, debiendo EL LOCATARIO endosar la misma en favor de LA LOCADORA.'
    )

    # NOVENA – REPARACIONES
    p("<b>NOVENA – REPARACIONES:</b>", clause_s)
    p(
        'En caso que el "LOCATARIO" notificara fehacientemente a la "LOCADORA" para que efectúe '
        'alguna reparación urgente dentro de las 24 hs contadas desde la recepción de la '
        'notificación y transcurrido dicho plazo la "LOCADORA" hiciere silencio o se negara, '
        'el "LOCATARIO" podrá realizarla por sí, con cargo a LA LOCADORA. Si las reparaciones '
        'no fueran urgentes, el "LOCATARIO" deberá intimar fehacientemente a LA "LOCADORA" para '
        'que las realice dentro de un plazo no inferior a diez (10) días corridos, contados a '
        'partir de la recepción de la intimación, cumplido el cual podrá proceder en la forma '
        'indicada anteriormente (art. 1201 del CCyCN).'
    )

    # DÉCIMA – IMPUESTOS, TASAS Y SERVICIOS
    p("<b>DÉCIMA – IMPUESTOS, TASAS Y SERVICIOS:</b>", clause_s)
    p(
        'Son a cargo del <b>LOCATARIO</b> los siguientes gastos correspondientes al inmueble '
        'objeto del presente: EXPENSAS COMUNES, LUZ y todo servicio que contrate como internet, '
        'televisión por cable, teléfono o cualquiera que agregue en un futuro. Se deja '
        'especialmente aclarado que todo impuesto, tasa, contribución o servicio que deba '
        'abonarse con motivo de la propiedad o del alquiler deberá ser abonado por <b>EL '
        'LOCATARIO</b>, ya sea existente a la fecha del presente o nuevo en el futuro, de manera '
        'que el alquiler que percibe <b>LA LOCADORA</b> lo recibirá libre de descuento por gasto '
        'o pago alguno. En oportunidad de pagar cada alquiler mensual <b>EL LOCATARIO</b> deberá '
        'entregar a la <b>LOCADORA</b> los correspondientes recibos pagados por los rubros antes '
        'mencionados. El incumplimiento de lo expuesto es causal de desalojo.'
    )

    # DÉCIMO PRIMERA – CAMBIO DE TITULARIDAD
    p("<b>DÉCIMO PRIMERA – CAMBIO DE TITULARIDAD:</b>", clause_s)
    p(
        'El servicio de luz quedará bajo la titularidad de LA <b>"LOCADORA"</b>. En caso de que '
        'el <b>"LOCATARIO"</b> adeude más de 1 mes de servicio, LA <b>"LOCADORA"</b> podrá '
        'solicitar ante quien corresponda la suspensión del servicio.'
    )

    # DÉCIMO SEGUNDA – DEPÓSITO EN GARANTÍA
    p("<b>DÉCIMO SEGUNDA – DEPÓSITO EN GARANTÍA:</b>", clause_s)
    p(
        f'A fin de garantizar el fiel cumplimiento de este contrato y de todas las obligaciones '
        f'contraídas por el "LOCATARIO", este entrega en calidad de depósito de garantía la suma '
        f'de <b>DÓLARES ESTADOUNIDENSES BILLETE {deposito_letras} (U$S {fmt_dolares(deposito)},-)</b>, '
        f'sirviendo el presente contrato como carta de pago y suficiente recibo. Dicha suma será '
        f'devuelta en idéntica moneda y forma a la que se recibe, sin intereses ni reajuste, '
        f'dentro de los treinta (30) días posteriores a la finalización del presente contrato, '
        f'previa deducción de las sumas que conforme al mismo pudiera descontar LA LOCADORA en '
        f'caso de corresponder. Asimismo las partes convienen en que en ningún caso EL LOCATARIO '
        f'podrá aplicar dicha suma al pago de los cánones locativos, preaviso y/o cualquier otro '
        f'concepto.'
    )

    # DÉCIMO TERCERA – RESTITUCIÓN
    p("<b>DÉCIMO TERCERA – RESTITUCIÓN:</b>", clause_s)
    p(
        'Al vencimiento del término pactado en el presente, el "LOCATARIO" se obliga a entregar '
        'el inmueble alquilado a LA "LOCADORA" en perfecto estado de conservación, no '
        'admitiéndose la tácita reconducción del contrato aun cuando el "LOCATARIO" continuara '
        'ocupando lo arrendado.'
    )

    # DÉCIMO CUARTA
    p("<b>DÉCIMO CUARTA:</b>", clause_s)
    p(
        'La falta de cumplimiento a cualquiera de las obligaciones precedentes y/o el no pago '
        'de dos (2) alquileres en la forma acordada dará derecho al desalojo del inmueble. Para '
        'el caso de restitución tardía de la propiedad y/o existencia de daños según cláusulas '
        'de este contrato LA LOCADORA podrá además de exigir el desalojo, reclamar a EL '
        'LOCATARIO los daños y perjuicios que pudieran corresponder, quedando a cargo de EL '
        'LOCATARIO el pago de la Tasa de Justicia y de los honorarios de profesionales actuantes '
        'regulados en sede judicial, como así también de todas las costas derivadas del proceso.'
    )

    # DÉCIMO QUINTA – LLAVES
    p("<b>DÉCIMO QUINTA – LLAVES:</b>", clause_s)
    p(
        'EL LOCATARIO se compromete con LA LOCADORA a hacer entrega de las llaves de EL INMUEBLE '
        'en funcionamiento, libre de ocupantes y deudas, ya sea por vencimiento de la vigencia '
        'del presente contrato o lanzamiento judicial. EL INMUEBLE debe estar con las paredes en '
        'perfecto estado de limpieza y funcionamiento tal como se entrega, salvo el deterioro '
        'producido por transcurso del tiempo y el buen uso, de lo contrario LA LOCADORA podrá '
        'deducir a su criterio del depósito de garantía el importe que corresponda para la '
        'realización de trabajos de limpieza y/o acondicionamiento de EL INMUEBLE. El recibo de '
        'llaves por escrito será el único medio de prueba de su entrega a LA LOCADORA.'
    )

    # DÉCIMO SEXTA – CONSIGNACIÓN DE LLAVES
    p("<b>DÉCIMO SEXTA – CONSIGNACIÓN DE LLAVES:</b>", clause_s)
    p(
        'En caso de consignación de llaves o en caso de desalojo, el alquiler regirá hasta el '
        'día en que LA LOCADORA tome la tenencia real y efectiva de la propiedad, así como la '
        'indemnización, multas y demás cargas que surjan por incumplimiento del presente contrato.'
    )

    # DÉCIMO SÉPTIMA – ABANDONO
    p("<b>DÉCIMO SÉPTIMA – ABANDONO:</b>", clause_s)
    p(
        'Si EL LOCATARIO abandonara manifiestamente la propiedad, LA LOCADORA podrá '
        'opcionalmente, bajo acta notarial, acceder y tomar razón de su estado, realizar '
        'inventario y enviar los bienes de EL LOCATARIO a depósito por cuenta y cargo de este. '
        'Asimismo LA LOCADORA hará las reparaciones que correspondiere por cuenta y cargo de '
        'EL LOCATARIO, y dispondrá libremente de EL INMUEBLE, sin perjuicio de las '
        'reclamaciones a que LA LOCADORA se considere con derecho.'
    )

    # DÉCIMO OCTAVA – DERECHOS DE VISITA E INSPECCIÓN
    p("<b>DÉCIMO OCTAVA – DERECHOS DE VISITA E INSPECCIÓN:</b>", clause_s)
    p(
        'A fines de controlar el estado del inmueble, las partes acuerdan que LA LOCADORA '
        'tendrá derecho a inspeccionarlo por sí o por un tercero autorizado, en cualquier '
        'momento con la única salvedad de preavisar con setenta y dos (72) horas en cada '
        'oportunidad en que realice la visita.'
    )

    # DÉCIMO NOVENA – INCUMPLIMIENTO
    p("<b>DÉCIMO NOVENA – INCUMPLIMIENTO:</b>", clause_s)
    p(
        'El incumplimiento de EL LOCATARIO a cualquiera de las cláusulas de este contrato y/o '
        'de la ley producirá culpablemente su resolución. En este caso, LA LOCADORA podrá '
        'declarar rescindida la locación debiendo EL LOCATARIO devolver EL INMUEBLE en el plazo '
        'de diez (10) días corridos de comunicada fehacientemente la decisión, bajo '
        'apercibimiento de considerar toda ocupación indebida y dará lugar a LA LOCADORA al '
        'reclamo por los daños y perjuicios sufridos, sin perjuicio de promoverse también la '
        'pertinente acción por desalojo.'
    )

    # VIGÉSIMA – DESALOJO ABREVIADO
    p("<b>VIGÉSIMA – DESALOJO ABREVIADO:</b>", clause_s)
    p(
        'De verse obligada la "LOCADORA" a intimar al "LOCATARIO" para obtener el cobro de las '
        'obligaciones contraídas, este último deberá abonar además del alquiler pactado los '
        'gastos y honorarios que se devengaren por dicha intimación. Si la "LOCADORA" debiera '
        'recurrir a la vía judicial para recuperar la tenencia del inmueble por cualquier causal, '
        'queda pactado que podrá recurrir a las normas propias del proceso de desalojo '
        'especialmente la vinculada con la desocupación inmediata del inmueble alquilado '
        'contemplada en el artículo 684 bis del Código Procesal Civil y Comercial de la Nación, '
        'con caución juratoria. EL LOCATARIO renuncia al derecho de recusar el juez sin causa.'
    )

    # VIGÉSIMO PRIMERA – REGLAMENTO
    p("<b>VIGÉSIMO PRIMERA – REGLAMENTO:</b>", clause_s)
    p(
        'EL "LOCATARIO" se compromete a respetar el Reglamento de Copropiedad y Administración '
        'del Edificio donde se encuentra EL INMUEBLE, que ha tenido a su vista, ha leído previo '
        'a la firma del presente y que manifiesta que lo conoce con exactitud y se obliga a dar '
        'estricto cumplimiento con las disposiciones del mismo.'
    )

    # VIGÉSIMO SEGUNDA – FIANZA
    p("<b>VIGÉSIMO SEGUNDA – FIANZA:</b>", clause_s)
    p(
        f'{fiadores_intro}, se constituyen en FIADORES solidarios, codeudores, lisos y llanos '
        f'pagadores principales de todas las sumas que pudiera adeudar EL LOCATARIO, incluso '
        f'de los honorarios y gastos de los juicios que promuevan contra ella por desalojo, '
        f'posesión judicial, daños y perjuicios, cobro de alquileres, sellados, '
        f'indemnizaciones, etcétera, comprometiéndose a pagar los alquileres adeudados a la '
        f'simple presentación de los recibos, si EL LOCATARIO no lo hiciera en las fechas '
        f'pactadas y garantizando solidariamente el fiel cumplimiento de todas las obligaciones '
        f'principales y accesorias mencionadas en el presente contrato. La fianza subsistirá '
        f'aun vencido el término del mismo y hasta tanto EL LOCATARIO permanezca en la '
        f'propiedad, o hasta que se resuelvan los eventuales juicios de desalojo y/o cobro de '
        f'alquileres entablados por LA LOCADORA. LOS FIADORES renuncian expresamente a los '
        f'beneficios de división y/o excusión, quedando asimismo convenido que las obligaciones '
        f'que contraen se transmitirán a sus sucesores. Además de responder con todos sus '
        f'bienes, LOS FIADORES afectan su participación en {garantia_desc}. LOS FIADORES '
        f'manifiestan que la propiedad mencionada no está afectada como bien de familia y se '
        f'comprometen a no enajenar, ni afectar el bien declarado con gravámenes, o regímenes '
        f'especiales, de familia u otros sin previamente sustituir las garantías a satisfacción '
        f'de LA LOCADORA. LOS FIADORES expresan que el inmueble aquí identificado no ha sido '
        f'consignado como garantía en otros contratos. LOS FIADORES manifiestan que no se '
        f'encuentran inhibidos, ni concursados, asumiendo las responsabilidades fijadas en la '
        f'ley penal vigente para el caso de desapoderamiento. LOS FIADORES quedan obligados a '
        f'comunicar en forma fehaciente cualquier modificación que realicen respecto de las '
        f'garantías ofrecidas en el presente contrato y en dicho supuesto a constituir nuevas '
        f'garantías para mantener la solvencia acreditada, en un plazo de treinta días. En el '
        f'caso de que EL LOCATARIO no devolviera la propiedad al vencimiento del contrato, LOS '
        f'FIADORES mantendrán su fianza hasta la efectiva restitución del inmueble y serán '
        f'solidariamente responsables por los daños y perjuicios que pudieran corresponder.'
    )

    # VIGÉSIMO TERCERA – INFORMES
    p("<b>VIGÉSIMO TERCERA – INFORMES:</b>", clause_s)
    p(
        f'Conforme los informes expedidos por el Registro de la Propiedad Inmueble de la Ciudad '
        f'Autónoma de Buenos Aires <b>DOMINIO: {rpi["dominio"]}</b> de fecha '
        f'<b>{rpi["fecha"]}</b>, surge que el inmueble de los FIADORES, '
        f'{fiadores_rpi}, no posee gravámenes, restricciones e interdicciones, al día de la '
        f'firma del presente, ni <b>INHIBICIONES {rpi["inhibicion_num"]}</b> de fecha '
        f'<b>{rpi["inhibicion_fecha"]}</b>.'
    )

    # VIGÉSIMO CUARTA – RESOLUCIÓN ANTICIPADA
    p("<b>VIGÉSIMO CUARTA – RESOLUCIÓN ANTICIPADA:</b>", clause_s)
    p(
        'El contrato de locación puede ser resuelto anticipadamente por el "LOCATARIO", en los '
        'términos del art. 1221 del CCyCN, si han transcurrido 6 meses de contrato, debiendo el '
        '"LOCATARIO" notificar en forma fehaciente su decisión a LA "LOCADORA" con 1 mes de '
        'antelación. Si hace uso de esta opción resolutoria en el primer año de vigencia de la '
        'relación locativa, debe abonar a LA "LOCADORA", en concepto de indemnización, la suma '
        'equivalente a un (1) mes y medio de alquiler al momento de desocupar el inmueble y la '
        'de un (1) mes si la opción se ejercita transcurrido dicho lapso. Si el "LOCATARIO" '
        'notifica fehacientemente su decisión con una anticipación de tres (3) meses o más, no '
        'le corresponde el pago de indemnización alguna por rescisión anticipada.'
    )

    # VIGÉSIMO QUINTA – RENOVACIÓN
    p("<b>VIGÉSIMO QUINTA – RENOVACIÓN:</b>", clause_s)
    p(
        'Dentro de los últimos tres (3) meses del contrato cualquiera de las partes puede '
        'convocar, mediante notificación fehaciente al domicilio electrónico constituido, a la '
        'otra a conversar sobre la renovación del contrato. En caso de silencio de LA "LOCADORA", '
        'o su negativa a renovar el contrato, el "LOCATARIO" podrá rescindir el contrato '
        'anticipadamente, sin necesidad de preaviso, ni obligación de pago de indemnización '
        'alguna (art. 1221 bis del CCyCN).'
    )

    # VIGÉSIMO SEXTA
    p("<b>VIGÉSIMO SEXTA:</b>", clause_s)
    p(
        'En caso que correspondiera pagar el impuesto de sellos será abonado por LAS PARTES en '
        'idénticas proporciones y partes iguales.'
    )

    # VIGÉSIMO SÉPTIMA – JURISDICCIÓN Y DOMICILIOS
    p("<b>VIGÉSIMO SÉPTIMA – JURISDICCIÓN Y DOMICILIOS:</b>", clause_s)
    p(
        f'Todas las PARTES se someten a la jurisdicción de la justicia ordinaria de '
        f'<b>{localidad}</b>, constituyendo domicilios especiales en los citados en el '
        f'encabezado, donde cada una de las partes tendrá por válidas las notificaciones y '
        f'emplazamientos que se cursen, y hasta tanto no comuniquen fehacientemente nuevos '
        f'domicilios. Las comunicaciones realizadas por vía electrónica serán válidas y eficaces '
        f'cuando así se estipule expresamente en el contrato (art. 75 del CCyCN).'
    )

    # ─────────────────────────────────────────────────────────────────────────
    # CIERRE
    # ─────────────────────────────────────────────────────────────────────────
    sp(10)
    p(
        f'En prueba de conformidad se firman tres (3) ejemplares de un mismo tenor y a un solo '
        f'efecto en <b>{localidad}</b>, a los <b>{fmt_fecha_hoy()}</b>.'
    )
    sp(24)

    # ─────────────────────────────────────────────────────────────────────────
    # FIRMAS
    # ─────────────────────────────────────────────────────────────────────────
    hr()
    sp(10)

    # Locador(es)
    p("<b>LA LOCADORA</b>", firma_bold_s)
    sp(4)
    story.append(Paragraph("Firma: ......................................................", firma_s))
    story.append(Paragraph(f"<b>Nombre:</b> {loc1['nombre']}", firma_s))
    story.append(Paragraph(f"<b>DNI:</b> {loc1['dni']}", firma_s))

    if loc2:
        sp(14)
        story.append(Paragraph("Firma: ......................................................", firma_s))
        story.append(Paragraph(f"<b>Nombre:</b> {loc2['nombre']}", firma_s))
        story.append(Paragraph(f"<b>DNI:</b> {loc2['dni']}", firma_s))

    sp(18)
    hr()
    sp(10)

    # Locatario
    p("<b>EL LOCATARIO</b>", firma_bold_s)
    sp(4)
    story.append(Paragraph("Firma: ......................................................", firma_s))
    story.append(Paragraph(f"<b>Nombre:</b> {lct['nombre']}", firma_s))
    story.append(Paragraph(f"<b>DNI:</b> {lct['dni']}", firma_s))

    sp(18)
    hr()
    sp(10)

    # Fiadores
    p("<b>LOS FIADORES</b>", firma_bold_s)
    sp(4)
    story.append(Paragraph("Firma: ......................................................", firma_s))
    story.append(Paragraph(f"<b>Nombre:</b> {fid1['nombre']}", firma_s))
    story.append(Paragraph(f"<b>DNI:</b> {fid1['dni']}", firma_s))

    if fid2:
        sp(14)
        story.append(Paragraph("Firma: ......................................................", firma_s))
        story.append(Paragraph(f"<b>Nombre:</b> {fid2['nombre']}", firma_s))
        story.append(Paragraph(f"<b>DNI:</b> {fid2['dni']}", firma_s))

    # ─────────────────────────────────────────────────────────────────────────
    doc.build(story)
    print(f"PDF generado exitosamente: {output_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generar Contrato de Locación de Vivienda en PDF")
    parser.add_argument("--data-file", required=True, help="Ruta al archivo JSON con los datos")
    parser.add_argument("--output", required=True, help="Ruta del archivo PDF de salida")
    args = parser.parse_args()

    with open(args.data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    build_pdf(data, args.output)


if __name__ == "__main__":
    main()
