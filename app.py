from flask import Flask, render_template, request, jsonify, send_file
import os
from backend.cut_optimizer import optimize_cuts
from pylatex import Document, Section, Subsection, Command, Package
from pylatex.utils import NoEscape
import io

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

    # Criar documento LaTeX
    doc = Document()
    doc.packages.append(Package('geometry', options=['a4paper', 'margin=1in']))
    doc.packages.append(Package('fontenc', options=['T1']))
    doc.packages.append(Package('inputenc', options=['utf8']))
    doc.packages.append(Package('lmodern'))
    doc.preamble.append(Command('title', 'Relatório de Otimização de Cortes'))
    doc.preamble.append(Command('author', 'xAI Cut Optimizer'))
    doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.append(NoEscape(r'\maketitle'))

    with doc.create(Section('Resultados')):
        doc.append(f'Comprimento do Material: {material_length}mm\n')
        doc.append(f'Espessura do Corte (Kerf): {kerf}mm\n')
        with doc.create(Subsection('Cortes Otimizados')):
            for i, bar in enumerate(result["bars"], 1):
                pieces_str = " x ".join(f"{length}mm" for length in bar["pieces"])
                doc.append(f'Seguimento {i}: {pieces_str} | Desperdício: {bar["remaining"]:.2f}mm\n')
        with doc.create(Subsection('Resumo')):
            doc.append(f'Barras necessárias: {result["total_bars"]}\n')
            doc.append(f'Desperdício total: {result["total_waste"]:.2f}mm\n')
            doc.append(f'Eficiência: {result["efficiency"]}%')

    # Gerar PDF em memória
    pdf_buffer = io.BytesIO()
    doc.generate_pdf('output', clean_tex=True, compiler='pdflatex')
    with open('output.pdf', 'rb') as f:
        pdf_buffer.write(f.read())
    pdf_buffer.seek(0)
    os.remove('output.pdf')  # Limpar arquivo temporário

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name='relatorio_cortes.pdf',
        mimetype='application/pdf'
    )

if __name__ == "__main__":
    print("Templates path:", app.template_folder)
    app.run(debug=True)