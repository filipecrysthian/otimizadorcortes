from flask import Flask, render_template, request, jsonify, send_file
from backend.cut_optimizer import optimize_cuts
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
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

    page_num = 1

    def new_page():
        nonlocal y, page_num
        c.showPage()
        draw_footer(page_num, '___')
        page_num += 1
        y = height - 50

    # Título centralizado
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "Relatório de Otimização de Corte")
    y -= 40

    # Título do Resumo
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Resumo dos Materiais:")
    y -= 25

    # Cabeçalhos e dados do resumo em formato de tabela com bordas
    resumo_headers = ["Material total", "Material utilizado", "Desperdício", "Total de cortes", "Eficiência"]
    resumo_data = [f"{material_total} mm", f"{material_used} mm", f"{total_waste} mm", str(total_cuts), f"{efficiency:.1f}%"]

    col_widths = [90, 110, 90, 100, 80]
    x_pos = 50

    # Cabeçalhos
    c.setFont("Helvetica-Bold", 10)
    for i, header in enumerate(resumo_headers):
        c.setFillColor(colors.lightgrey)
        c.rect(x_pos, y, col_widths[i], 18, fill=1)
        c.setFillColor(colors.black)
        c.drawCentredString(x_pos + col_widths[i] / 2, y + 5, header)
        x_pos += col_widths[i]
    y -= 18

    # Dados
    x_pos = 50
    c.setFont("Helvetica", 10)
    for i, value in enumerate(resumo_data):
        c.rect(x_pos, y, col_widths[i], 18)
        c.drawCentredString(x_pos + col_widths[i] / 2, y + 5, value)
        x_pos += col_widths[i]
    y -= 40

    # Cabeçalho da "tabela" de cortes
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Detalhamento por barra:")
    y -= 25

    def draw_table_header():
        nonlocal y
        headers = ["Barra", "Segmentos", "Desperdício"]
        col_widths = [50, 320, 100]
        x_pos = 50
        c.setFont("Helvetica-Bold", 10)
        for i, header in enumerate(headers):
            c.setFillColor(colors.lightgrey)
            c.rect(x_pos, y, col_widths[i], 18, fill=1)
            c.setFillColor(colors.black)
            c.drawCentredString(x_pos + col_widths[i] / 2, y + 5, header)
            x_pos += col_widths[i]
        y -= 18
        return col_widths

    col_widths = draw_table_header()
    c.setFont("Helvetica", 10)

    for bar in formatted_bars:
        if y < 70:
            draw_footer(page_num, '___')
            new_page()
            col_widths = draw_table_header()
            c.setFont("Helvetica", 10)

        # Remover "//" e extrair informações
        bar = bar.lstrip("/ ").strip()

        partes = bar.split("|")
        barra = partes[0].strip().replace("6000mm /", "").replace("Barra ", "")
        segmentos = " | ".join(p.strip() for p in partes[1:-1])
        desperdicio = partes[-1].replace("Desperdício - ", "").strip()

        x_pos = 50
        values = [barra, segmentos, desperdicio]
        for i, val in enumerate(values):
            c.rect(x_pos, y, col_widths[i], 18)
            c.drawCentredString(x_pos + col_widths[i] / 2, y + 5, val)
            x_pos += col_widths[i]
        y -= 18

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