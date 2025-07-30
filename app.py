from flask import Flask, render_template, request, jsonify
from backend.cut_optimizer import optimize_cuts
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/optimize", methods=["POST"])
def optimize():
    data = request.json
    logger.info(f"Recebido: material_length={data['material_length']}, pieces={data['pieces']}, kerf={data.get('kerf', 0)}")
    material_length = data.get("material_length")
    pieces = data.get("pieces", [])
    kerf = data.get("kerf", 0)

    # Validação
    if not isinstance(material_length, (int, float)) or material_length <= 0:
        return jsonify({"error": "Comprimento do material deve ser maior que 0"}), 400
    if not pieces or not all(isinstance(p, (int, float)) and p > 0 for p in pieces):
        return jsonify({"error": "Peças devem ser uma lista de números positivos"}), 400
    if not isinstance(kerf, (int, float)) or kerf < 0:
        return jsonify({"error": "Espessura do corte não pode ser negativa"}), 400

    result = optimize_cuts(material_length, pieces, kerf)
    return jsonify(result)

if __name__ == "__main__":
    print("Templates path:", app.template_folder)
    app.run(debug=True)