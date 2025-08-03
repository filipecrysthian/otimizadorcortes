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

@app.route('/export', methods=['POST'])
def export_pdf():
    data = request.json
    formatted_bars = data.get("formatted_bars", [])
    material_total = data.get("material_total", 0)
    material_used = data.get("material_used", 0)
    total_waste = data.get("total_waste", 0)
    total_cuts = data.get("total_cuts", 0)
    efficiency = data.get("efficiency", 0)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Relatório de Otimização de Corte")
    y -= 30

    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Material total: {material_total} mm")
    y -= 20
    p.drawString(50, y, f"Material utilizado: {material_used} mm")
    y -= 20
    p.drawString(50, y, f"Desperdício: {total_waste} mm")
    y -= 20
    p.drawString(50, y, f"Total de cortes: {total_cuts}")
    y -= 20
    p.drawString(50, y, f"Eficiência: {efficiency}%")
    y -= 30

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Detalhamento por barra:")
    y -= 20
    p.setFont("Helvetica", 10)
    for bar in formatted_bars:
        if y < 50:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 10)
        p.drawString(50, y, bar.replace("// ", ""))
        y -= 15

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="relatorio_otimizacao.pdf", mimetype="application/pdf")


if __name__ == "__main__":
    print("Iniciando servidor Flask", file=sys.stderr)
    print("Templates path:", app.template_folder, file=sys.stderr)
    app.run(debug=True)