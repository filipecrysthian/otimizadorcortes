from flask import Flask, render_template, request, jsonify
import os
from backend.cut_optimizer import optimize_cuts

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/optimize", methods=["POST"])
def optimize():
    data = request.json
    material_length = data["material_length"]
    pieces = data["pieces"]
    result = optimize_cuts(material_length, pieces)
    return jsonify(result)

if __name__ == "__main__":
    print("Templates path:", app.template_folder)
    app.run(debug=True)