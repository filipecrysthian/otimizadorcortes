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
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    y = height - 50
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

    def draw_footer(page_num, total_pages):
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(margin, 10 * mm, f"Gerado em: {timestamp}")
        c.drawRightString(width - margin, 10 * mm, f"Página {page_num} de {total_pages}")

    pages = []
    page_num = 1

    def new_page():
        nonlocal y, page_num
        c.showPage()
        pages.append(c.getpdfdata())
        page_num += 1
        y = height - 50

    # Título centralizado
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "Relatório de Otimização de Corte")
    y -= 40

    # Informações gerais
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Material total: {material_total} mm")
    y -= 20
    c.drawString(50, y, f"Material utilizado: {material_used} mm")
    y -= 20
    c.drawString(50, y, f"Desperdício: {total_waste} mm")
    y -= 20
    c.drawString(50, y, f"Total de cortes: {total_cuts}")
    y -= 20
    c.drawString(50, y, f"Eficiência: {efficiency:.1f}%")
    y -= 30

    # Cabeçalho da "tabela"
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Detalhamento por barra:")
    y -= 20

    def draw_table_header():
        nonlocal y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Barra")
        c.drawString(100, y, "Segmentos")
        c.drawString(400, y, "Desperdício")
        y -= 15
        c.line(50, y, 550, y)
        y -= 10

    draw_table_header()
    c.setFont("Helvetica", 10)

    for bar in formatted_bars:
        if y < 70:
            draw_footer(page_num, '___')
            new_page()
            draw_table_header()
            c.setFont("Helvetica", 10)

        # Exemplo: "Barra 1 | Segmento 1 - 800 x 7 | Desperdício - 400mm"
        partes = bar.split("|")
        barra = partes[0].strip().replace("6000mm /", "").replace("Barra ", "")
        segmentos = " | ".join(p.strip() for p in partes[1:-1])
        desperdicio = partes[-1].replace("Desperdício - ", "").strip()

        c.drawString(50, y, barra)
        c.drawString(100, y, segmentos)
        c.drawString(400, y, desperdicio)
        y -= 15

    # Última página
    draw_footer(page_num, page_num)
    c.showPage()
    c.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="relatorio_otimizacao.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    print("Iniciando servidor Flask", file=sys.stderr)
    print("Templates path:", app.template_folder, file=sys.stderr)
    app.run(debug=True)