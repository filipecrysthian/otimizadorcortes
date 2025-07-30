from flask import Flask, render_template, request, jsonify, send_file
from backend.cut_optimizer import optimize_cuts
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/optimize", methods=["POST"])
def optimize():
    data = request.json
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

@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    data = request.json
    material_length = data.get("material_length")
    pieces = data.get("pieces", [])
    kerf = data.get("kerf", 0)
    result = optimize_cuts(material_length, pieces, kerf)

    # Criar PDF com reportlab
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica", 14)
    c.drawString(100, 800, "Relatório de Otimização de Cortes")
    c.setFont("Helvetica", 12)
    c.drawString(100, 780, f"Comprimento do Material: {material_length}mm")
    c.drawString(100, 760, f"Espessura do Corte (Kerf): {kerf}mm")
    y = 740
    c.drawString(100, y, "Cortes Otimizados:")
    y -= 20
    for i, bar in enumerate(result["bars"], 1):
        pieces_str = " x ".join(f"{length}mm" for length in bar["pieces"])
        c.drawString(100, y, f"Segmento {i}: {pieces_str} | Desperdício: {bar['remaining']:.2f}mm")
        y -= 20
    y -= 20
    c.drawString(100, y, "Resumo:")
    y -= 20
    c.drawString(100, y, f"Barras necessárias: {result['total_bars']}")
    y -= 20
    c.drawString(100, y, f"Desperdício total: {result['total_waste']:.2f}mm")
    y -= 20
    c.drawString(100, y, f"Eficiência: {result['efficiency']}%")
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='relatorio_cortes.pdf',
        mimetype='application/pdf'
    )

if __name__ == "__main__":
    print("Templates path:", app.template_folder)
    app.run(debug=True)