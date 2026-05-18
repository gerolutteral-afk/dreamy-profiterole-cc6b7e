from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import json
import uuid

app = Flask(__name__)
CORS(app)

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

@app.route("/ping")
def ping():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
