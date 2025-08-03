from flask import Flask, render_template, request, jsonify, send_file
from backend.cut_optimizer import optimize_cuts
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO
from datetime import datetime
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

@app.route("/export", methods=["POST"])
def export_pdf():
    data = request.get_json()
    buffer = BytesIO()

    width, height = A4
    margin = 20 * mm
    y = height - margin
    line_height = 15

    c = canvas.Canvas(buffer, pagesize=A4)

    def draw_footer(page_num, total_pages):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(margin, 10 * mm, f"Gerado em: {timestamp}")
        c.drawRightString(width - margin, 10 * mm, f"Página {page_num} de {total_pages}")

    def add_header():
        nonlocal y
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, y, "Relatório de Otimização de Corte")
        y -= 30

        c.setFont("Helvetica", 12)
        resumo = [
            f"Material total: {data['material_total']} mm",
            f"Material utilizado: {data['material_used']} mm",
            f"Desperdício: {data['total_waste']} mm",
            f"Total de cortes: {data['total_cuts']}",
            f"Eficiência: {round(data['efficiency'], 1)}%"
        ]
        for linha in resumo:
            c.drawString(margin, y, linha)
            y -= line_height

        y -= 10
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Detalhamento por barra:")
        y -= line_height

    add_header()

    c.setFont("Helvetica", 10)

    barra_num = 1
    for bar in data["formatted_bars"]:
        parts = bar.split("|")
        segmentos = " | ".join(p.strip() for p in parts[1:])
        texto = f"Barra {barra_num} | {segmentos}"

        if y < margin + 30:
            draw_footer(c.getPageNumber(), 999)  # temporário
            c.showPage()
            y = height - margin
            add_header()
            c.setFont("Helvetica", 10)

        c.drawString(margin, y, texto)
        y -= line_height
        barra_num += 1

    # Total de páginas
    total_pages = c.getPageNumber()
    draw_footer(total_pages, total_pages)
    c.save()

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="relatorio_otimizacao.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    print("Iniciando servidor Flask", file=sys.stderr)
    print("Templates path:", app.template_folder, file=sys.stderr)
    app.run(debug=True)