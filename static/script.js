async function calculate() {
    const materialLengthInput = document.getElementById("materialLength");
    const kerfWidthInput = document.getElementById("kerfWidth");
    const materialLength = parseFloat(materialLengthInput.value);
    const kerfWidth = parseFloat(kerfWidthInput.value);
    const pieces = [];
    const pieceNames = [];

    // Limpar validações anteriores
    materialLengthInput.classList.remove("is-invalid");
    kerfWidthInput.classList.remove("is-invalid");
    document.querySelectorAll(".piece-name, .piece-length, .piece-qty").forEach(input => input.classList.remove("is-invalid"));

    // Validação
    if (isNaN(materialLength) || materialLength <= 0) {
        materialLengthInput.classList.add("is-invalid");
        return;
    }
    if (isNaN(kerfWidth) || kerfWidth < 0) {
        kerfWidthInput.classList.add("is-invalid");
        return;
    }

    let valid = true;
    document.querySelectorAll("#pieces .piece-row").forEach((row, index) => {
        const nameInput = row.querySelector(".piece-name");
        const lengthInput = row.querySelector(".piece-length");
        const qtyInput = row.querySelector(".piece-qty");
        const name = nameInput.value.trim() || `Segmento ${index + 1}`;
        const length = parseFloat(lengthInput.value);
        const qty = parseInt(qtyInput.value);
        
        if (isNaN(length) || length <= 0) {
            lengthInput.classList.add("is-invalid");
            valid = false;
        }
        if (isNaN(qty) || qty <= 0) {
            qtyInput.classList.add("is-invalid");
            valid = false;
        }
        if (valid) {
            for (let i = 0; i < qty; i++) {
                pieces.push(length);
                pieceNames.push(name);
            }
        }
    });

    if (!valid || pieces.length === 0) {
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
    
    // Adicionar nomes aos resultados
    result.bars.forEach((bar, index) => {
        bar.name = pieceNames[index] || `Segmento ${index + 1}`;
    });

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
        barDiv.innerHTML = `Segmento ${bar.name}: ${piecesStr} | Desperdício: ${bar.remaining.toFixed(2)}mm`;
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
    const pieceNames = [];

    document.querySelectorAll("#pieces .piece-row").forEach((row, index) => {
        const name = row.querySelector(".piece-name").value.trim() || `Segmento ${index + 1}`;
        const length = parseFloat(row.querySelector(".piece-length").value);
        const qty = parseInt(row.querySelector(".piece-qty").value);
        if (length && qty) {
            for (let i = 0; i < qty; i++) {
                pieces.push(length);
                pieceNames.push(name);
            }
        }
    });

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

    // Adicionar nomes aos resultados para o PDF
    result.bars.forEach((bar, index) => {
        bar.name = pieceNames[index] || `Segmento ${index + 1}`;
    });

    const pdfResponse = await fetch("/download_pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            material_length: materialLength,
            pieces: pieces,
            kerf: kerfWidth,
            names: pieceNames
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
    const pieceCount = document.querySelectorAll("#pieces .piece-row").length + 1;
    const newRow = document.createElement("div");
    newRow.className = "piece-row d-flex gap-2 mb-2";
    newRow.innerHTML = `
        <input type="text" class="form-control piece-name" placeholder="Nome do Segmento (ex.: Segmento ${pieceCount})">
        <input type="number" class="form-control piece-length" placeholder="Comprimento (mm)" min="1">
        <input type="number" class="form-control piece-qty" placeholder="Quantidade" value="1" min="1">
        <button class="btn btn-danger remove-btn" onclick="removePiece(this)"><i class="bi bi-trash"></i> Remover</button>
    `;
    piecesDiv.appendChild(newRow);
}

function removePiece(button) {
    button.parentElement.remove();
}

function clearForm() {
    document.getElementById("materialLength").value = "6000";
    document.getElementById("kerfWidth").value = "3";
    const piecesDiv = document.getElementById("pieces");
    piecesDiv.innerHTML = `
        <div class="piece-row d-flex gap-2 mb-2">
            <input type="text" class="form-control piece-name" placeholder="Nome do Segmento (ex.: Segmento 1)">
            <input type="number" class="form-control piece-length" placeholder="Comprimento (mm)" min="1">
            <input type="number" class="form-control piece-qty" placeholder="Quantidade" value="1" min="1">
            <button class="btn btn-danger remove-btn" onclick="removePiece(this)"><i class="bi bi-trash"></i> Remover</button>
        </div>
    `;
    document.getElementById("result").innerHTML = "";
    document.getElementById("downloadBtn").style.display = "none";
    document.querySelectorAll(".piece-name, .piece-length, .piece-qty, #materialLength, #kerfWidth").forEach(input => input.classList.remove("is-invalid"));
}