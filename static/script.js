async function calculate() {
    const materialLength = parseFloat(document.getElementById("materialLength").value);
    const kerfWidth = parseFloat(document.getElementById("kerfWidth").value);
    const pieces = [];

    // Validação
    if (isNaN(materialLength) || materialLength <= 0) {
        alert("Por favor, insira um comprimento de material válido.");
        return;
    }
    if (isNaN(kerfWidth) || kerfWidth < 0) {
        alert("Por favor, insira uma espessura de corte válida.");
        return;
    }

    let valid = true;
    document.querySelectorAll("#pieces .piece-row").forEach(row => {
        const length = parseFloat(row.querySelector(".piece-length").value);
        const qty = parseInt(row.querySelector(".piece-qty").value);
        
        if (isNaN(length) || length <= 0 || isNaN(qty) || qty <= 0) {
            valid = false;
        } else {
            for (let i = 0; i < qty; i++) {
                pieces.push(length);
            }
        }
    });

    if (!valid || pieces.length === 0) {
        alert("Por favor, insira pelo menos uma peça com comprimento e quantidade válidos.");
        return;
    }

    const response = await fetch("/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            material_length: materialLength,
            pieces: pieces,
            kerf: kerfWidth
        })
    });
    
    const result = await response.json();
    if (result.error) {
        alert(result.error);
        return;
    }
    
    displayResult(result);
    document.getElementById("downloadBtn").style.display = "inline-block";
}

function displayResult(result) {
    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = ""; // Limpa o resultado anterior

    // Contar peças por tamanho em cada barra
    result.bars.forEach((bar, index) => {
        const pieceCounts = {};
        bar.pieces.forEach(piece => {
            pieceCounts[piece] = (pieceCounts[piece] || 0) + 1;
        });
        const piecesStr = Object.entries(pieceCounts)
            .map(([length, count]) => `${length}mm x ${count}`)
            .join(", ");
        const barDiv = document.createElement("div");
        barDiv.className = "bar";
        barDiv.innerHTML = `Seguimento ${index + 1}: ${piecesStr} | Desperdício: ${bar.remaining.toFixed(2)}mm`;
        resultDiv.appendChild(barDiv);
    });

    // Resumo
    const totalsDiv = document.createElement("div");
    totalsDiv.className = "totals";
    totalsDiv.innerHTML = `
        <h3>Resumo:</h3>
        <p>Barras necessárias: ${result.total_bars}</p>
        <p>Desperdício total: ${result.total_waste.toFixed(2)}mm</p>
        <p>Eficiência: ${result.efficiency}%</p>
    `;
    resultDiv.appendChild(totalsDiv);
}

async function downloadPDF() {
    const materialLength = parseFloat(document.getElementById("materialLength").value);
    const kerfWidth = parseFloat(document.getElementById("kerfWidth").value);
    const pieces = [];

    document.querySelectorAll("#pieces .piece-row").forEach(row => {
        const length = parseFloat(row.querySelector(".piece-length").value);
        const qty = parseInt(row.querySelector(".piece-qty").value);
        if (length && qty) {
            for (let i = 0; i < qty; i++) {
                pieces.push(length);
            }
        }
    });

    const response = await fetch("/download_pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            material_length: materialLength,
            pieces: pieces,
            kerf: kerfWidth
        })
    });

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "relatorio_cortes.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
}

function addPiece() {
    const piecesDiv = document.getElementById("pieces");
    const newRow = document.createElement("div");
    newRow.className = "piece-row";
    newRow.innerHTML = `
        <input type="number" class="piece-length" placeholder="Comprimento (mm)" min="1">
        <input type="number" class="piece-qty" placeholder="Quantidade" value="1" min="1">
        <button class="remove-btn" onclick="removePiece(this)">Remover</button>
    `;
    piecesDiv.appendChild(newRow);
}

function removePiece(button) {
    button.parentElement.remove();
}