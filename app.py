from flask import Flask, render_template, request, jsonify, send_file
from backend.cut_optimizer import optimize_cuts
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import sys

app = Flask(__name__)

@app.route("/")
def home():
    print("Rota / acessada", file=sys.stderr)
    return render_template("index.html")

@app.route("/optimize", methods=["POST"])
def optimize():
    print("Requisição POST recebida em /optimize", file=sys.stderr)
    data = request.json
    material_length = data.get("material_length", 6000)
    pieces = data.get("pieces", [])
    kerf = data.get("kerf", 0)

    print(f"Dados recebidos: material_length={material_length}, pieces={pieces}, kerf={kerf}", file=sys.stderr)

    # Validação
    if not isinstance(material_length, (int, float)) or material_length <= 0:
        print("Validação falhou: material_length inválido", file=sys.stderr)
        return jsonify({"error": "Comprimento do material deve ser maior que 0"}), 400
    if not pieces or not all(isinstance(p, (int, float)) and p > 0 for p in pieces):
        print("Validação falhou: peças inválidas", file=sys.stderr)
        return jsonify({"error": "Peças devem ser uma lista de números positivos"}), 400
    if not isinstance(kerf, (int, float)) or kerf < 0:
        print("Validação falhou: kerf inválido", file=sys.stderr)
        return jsonify({"error": "Espessura do corte não pode ser negativa"}), 400

    try:
        result = optimize_cuts(material_length, pieces, kerf)
        print("Resultado da otimização: {}".format(result), file=sys.stderr)
        return jsonify(result)
    except Exception as e:
        print("Erro na otimização: {}".format(str(e)), file=sys.stderr)
        return jsonify({"error": str(e)}), 500

@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    print("Requisição POST recebida em /download_pdf", file=sys.stderr)
    data = request.json
    material_length = data.get("material_length", 6000)
    pieces = data.get("pieces", [])
    kerf = data.get("kerf", 3)
    names = data.get("names", [])

    print(f"Dados recebidos para PDF: material_length={material_length}, pieces={pieces}, kerf={kerf}, names={names}", file=sys.stderr)

    # Validação
    if not isinstance(material_length, (int, float)) or material_length <= 0:
        return jsonify({"error": "Comprimento do material deve ser maior que 0"}), 400
    if not pieces or not all(isinstance(p, (int, float)) and p > 0 for p in pieces):
        return jsonify({"error": "Peças devem ser uma lista de números positivos"}), 400
    if not isinstance(kerf, (int, float)) or kerf < 0:
        return jsonify({"error": "Espessura do corte não pode ser negativa"}), 400

    result = optimize_cuts(material_length, pieces, kerf)

    # Adicionar nomes aos resultados
    for i, bar in enumerate(result["bars"]):
        bar["name"] = names[i] if i < len(names) else f"Segmento {i + 1}"

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
    for i in range(result["total_bars"]):
        bar = result["bars"][i] if i < len(result["bars"]) else {"pieces": [], "remaining": 0}
        pieceCounts = {}
        for piece in bar["pieces"]:
            pieceCounts[piece] = pieceCounts.get(piece, 0) + 1
        pieces_str = " | ".join(f"{length}mm x {count}" for length, count in pieceCounts.items())
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0, 0, 0)  # Preto
        c.drawString(100, y, f"{i + 1}. {pieces_str} | {bar['remaining']:.2f}mm")
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.42, 0.46, 0.49)  # #6c757d
        labels = [f"Segmento {idx + 1}" for idx in range(len(pieceCounts))] if pieceCounts else []
        labels.append("Desperdício")
        c.drawString(100, y - 15, " | ".join(labels))
        y -= 30
    c.setFillColorRGB(0, 0, 0)  # Preto
    c.drawString(100, y, "Resumo:")
    y -= 20
    c.drawString(100, y, f"Barras necessárias: {result['total_bars']}")
    y -= 20
    c.drawString(100, y, f"Desperdício total: {result['total_waste']:.2f}mm")
    y -= 20
    c.drawString(100, y, f"Eficiência: {result['efficiency']:.2f}%")
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
    print("Iniciando servidor Flask", file=sys.stderr)
    print("Templates path:", app.template_folder, file=sys.stderr)
    app.run(debug=True)