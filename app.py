from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import json
import uuid
import re
import base64
import logging
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

# ── Logging básico ─────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("calace")

# ── SignWell ────────────────────────────────────────────────────────────────
SIGNWELL_API_URL = "https://www.signwell.com/api/v1/documents/"

SCRIPTS = {
    "autorizacion-alquiler":  "generar_autorizacion.py",
    "autorizacion-venta":     "generar_autorizacion_venta.py",
    "reserva-alquiler":       "generar_reserva_alquiler.py",
    "contrato-alquiler":      "generar_contrato_alquiler.py",
    "oferta-compra":          "generar_oferta_compra.py",
    "boleto-compraventa":     "generar_boleto_compraventa.py",
    "contraoferta":           "generar_contraoferta.py",
    "recibo-refuerzo":        "generar_recibo_refuerzo.py",
    "notif-refuerzo":         "generar_notif_refuerzo.py",
    "notif-contraoferta":     "generar_notif_aceptacion.py",
    "nota-presentacion":      "generar_nota_presentacion.py",
    "reporte-rendimiento":    "generar_reporte_rendimiento.py",
}

def get_apellido(data):
    candidates = [
        data.get("nombre"), data.get("nombre_interesado"),
        data.get("locatario_nombre"), data.get("oferente_nombre"),
        data.get("comprador1_nombre"), data.get("cliente_nombre"),
        data.get("propietario1_nombre"), data.get("oferente"),
        data.get("propietario_nombre"),
    ]
    for c in candidates:
        if c:
            return c.split()[-1].upper()
    # Fallback para docs sin propietario/cliente (ej: reporte-rendimiento → usa dirección)
    direccion = data.get("direccion") or data.get("direccion_inmueble") or data.get("domicilio_inmueble")
    if direccion:
        primera = direccion.split()[0] if direccion.split() else ""
        limpio = "".join(c for c in primera if c.isalnum())
        if limpio:
            return limpio.upper()
    return "DOC"

@app.route("/generar", methods=["POST"])
def generar():
    body = request.get_json()
    doc_type = body.get("doc_type")
    data = body.get("data", {})

    if doc_type not in SCRIPTS:
        return jsonify({"error": "Tipo de documento no reconocido"}), 400

    script = os.path.join(os.path.dirname(__file__), SCRIPTS[doc_type])
    apellido = get_apellido(data)
    output_path = f"/tmp/calace_{uuid.uuid4().hex}_{apellido}.pdf"
    json_path = f"/tmp/calace_data_{uuid.uuid4().hex}.json"

    try:
        with open(json_path, "w") as f:
            json.dump(data, f, ensure_ascii=False)

        cmd = ["python3", script, "--data-file", json_path, "--output", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            return jsonify({"error": result.stderr or "Error al generar PDF"}), 500

        if not os.path.exists(output_path):
            return jsonify({"error": "No se generó el PDF"}), 500

        filename = f"{doc_type.replace('-','_')}_{apellido}.pdf"
        return send_file(
            output_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Tiempo de espera agotado"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for path in [output_path, json_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass


# ── Helpers de validación ───────────────────────────────────────────────────
def _email_valido(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


# ── Enviar a firmar (SignWell) ──────────────────────────────────────────────
@app.route("/enviar-a-firmar", methods=["POST"])
def enviar_a_firmar():
    """
    Recibe un PDF (multipart, campo 'archivo') + datos del firmante en form-data,
    lo sube a SignWell y dispara el envío inmediato para firma electrónica.
    """
    # 1. Verificar configuración del servidor
    api_key = os.environ.get("SIGNWELL_API_KEY")
    if not api_key:
        logger.error("SIGNWELL_API_KEY no configurada en el entorno")
        return jsonify({
            "error": "El servicio de firma no está configurado en el servidor. "
                     "Falta la variable SIGNWELL_API_KEY."
        }), 500

    # 2. Validar archivo
    archivo = request.files.get("archivo")
    if not archivo or archivo.filename == "":
        return jsonify({"error": "No se recibió el archivo PDF a firmar."}), 400

    # 3. Validar datos del firmante
    nombre = (request.form.get("nombre_firmante") or "").strip()
    email = (request.form.get("email_firmante") or "").strip()
    asunto = (request.form.get("asunto") or "").strip() \
        or "Documento para firmar - Calace Propiedades"
    mensaje = (request.form.get("mensaje") or "").strip() or (
        "Estimado/a, le enviamos el documento adjunto para su firma electrónica. "
        "Ante cualquier consulta quedamos a su disposición. "
        "Saludos cordiales, Calace Propiedades."
    )

    if not nombre:
        return jsonify({"error": "El nombre del firmante es obligatorio."}), 400
    if not _email_valido(email):
        return jsonify({"error": "El email del firmante no es válido."}), 400

    # 4. Leer PDF y convertir a base64
    try:
        pdf_bytes = archivo.read()
        if not pdf_bytes:
            return jsonify({"error": "El archivo PDF está vacío."}), 400
        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
    except Exception as e:
        return jsonify({"error": f"No se pudo leer el archivo PDF: {e}"}), 400

    filename = archivo.filename or "documento.pdf"
    test_mode = os.environ.get("SIGNWELL_TEST_MODE", "true").lower() in ("1", "true", "yes", "si")

    # 5. Armar payload para SignWell API v1
    payload = {
        "test_mode": test_mode,
        "draft": False,
        "name": asunto,
        "subject": asunto,
        "message": mensaje,
        "files": [{"name": filename, "file_base64": pdf_b64}],
        "recipients": [{"id": "1", "name": nombre, "email": email}],
        "reminders": True,
    }

    # 6. Llamar a SignWell
    try:
        resp = requests.post(
            SIGNWELL_API_URL,
            headers={
                "X-Api-Key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=45,
        )
    except requests.exceptions.Timeout:
        logger.error("Timeout al contactar SignWell")
        return jsonify({
            "error": "El servicio de firma tardó demasiado en responder. Intentá de nuevo en unos minutos."
        }), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red con SignWell: {e}")
        return jsonify({
            "error": "No se pudo contactar el servicio de firma. Revisá tu conexión e intentá de nuevo."
        }), 502

    # 7. Procesar respuesta de SignWell
    if resp.status_code not in (200, 201):
        detalle = ""
        try:
            j = resp.json()
            detalle = j.get("errors") or j.get("error") or j.get("message") or ""
        except Exception:
            detalle = (resp.text or "")[:300]
        logger.error(f"SignWell respondió {resp.status_code}: {detalle}")
        return jsonify({
            "error": f"El servicio de firma rechazó el envío (código {resp.status_code}). {detalle}".strip()
        }), 502

    try:
        data = resp.json()
    except Exception:
        logger.error("SignWell devolvió una respuesta no interpretable")
        return jsonify({"error": "El servicio de firma devolvió una respuesta inesperada."}), 502

    doc_id = data.get("id")
    estado = data.get("status", "sent")

    # 8. Logging del envío
    logger.info(
        "FIRMA-ENVIADA | %s | doc=%s | destinatario=%s | signwell_id=%s | test_mode=%s",
        datetime.now().isoformat(timespec="seconds"), filename, email, doc_id, test_mode
    )

    return jsonify({
        "signwell_document_id": doc_id,
        "estado": estado,
        "test_mode": test_mode,
        "mensaje": f"Documento enviado a {email}. Te avisamos cuando lo firme."
    }), 200


@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
