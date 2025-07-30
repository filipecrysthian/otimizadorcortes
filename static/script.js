async function calculate() {
    const materialLength = parseFloat(document.getElementById("materialLength").value);
    const kerfWidth = parseFloat(document.getElementById("kerfWidth").value); // Novo!
    const pieces = [];

    document.querySelectorAll("#pieces .piece-row").forEach(row => {
        const length = parseFloat(row.querySelector(".piece-length").value);
        const qty = parseInt(row.querySelector(".piece-qty").value);
        
        if (length && qty) {
            for (let i = 0; i < qty; i++) {
                pieces.push(length + kerfWidth); // Adiciona kerf a cada peça!
            }
        }
    });

    const response = await fetch("/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            material_length: materialLength,
            pieces: pieces,
            kerf: kerfWidth // Envia kerf para o backend (opcional)
        })
    });
    
    const result = await response.json();
    displayResult(result);
}

function displayResult(result) {
    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = ""; // Limpa o resultado anterior

    // 1. Primeiro mostra as barras
    result.bars.forEach((bar, index) => {
        const barDiv = document.createElement("div");
        barDiv.className = "bar";
        barDiv.innerHTML = `
            <strong>Barra ${index + 1}:</strong> 
            ${bar.pieces.join("mm, ")}mm | 
            Sobra: ${bar.remaining.toFixed(2)}mm
        `;
        resultDiv.appendChild(barDiv);
    });

    // 2. Depois mostra os totais (em uma div separada)
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

function addPiece() {
    const piecesDiv = document.getElementById("pieces");
    const newRow = document.createElement("div");
    newRow.className = "piece-row";
    newRow.innerHTML = `
        <input type="number" class="piece-length" placeholder="Comprimento (mm)">
        <input type="number" class="piece-qty" placeholder="Quantidade" value="1">
        <button class="remove-btn" onclick="removePiece(this)">Remover</button>
    `;
    piecesDiv.appendChild(newRow);
}

function removePiece(button) {
    button.parentElement.remove();
}