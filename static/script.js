async function calculate() {
    const materialLengthInput = document.getElementById("materialLength");
    const kerfWidthInput = document.getElementById("kerfWidth");
    const materialLength = parseFloat(materialLengthInput.value);
    const kerfWidth = parseFloat(kerfWidthInput.value);
    const pieces = [];
    const pieceNames = [];
    const errorMessage = document.getElementById("errorMessage");

    // Limpar mensagens de erro
    errorMessage.style.display = "none";
    errorMessage.textContent = "";
    materialLengthInput.classList.remove("is-invalid");
    kerfWidthInput.classList.remove("is-invalid");
    document.querySelectorAll(".piece-name, .piece-length, .piece-qty").forEach(input => input.classList.remove("is-invalid"));

    // Validação
    if (isNaN(materialLength) || materialLength <= 0) {
        materialLengthInput.classList.add("is-invalid");
        errorMessage.textContent = "Comprimento do material deve ser maior que 0.";
        errorMessage.style.display = "block";
        return;
    }
    if (isNaN(kerfWidth) || kerfWidth < 0) {
        kerfWidthInput.classList.add("is-invalid");
        errorMessage.textContent = "Espessura do corte não pode ser negativa.";
        errorMessage.style.display = "block";
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
        errorMessage.textContent = "Por favor, insira pelo menos uma peça válida.";
        errorMessage.style.display = "block";
        return;
    }

    try {
        const response = await fetch("/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                material_length: materialLength,
                pieces: pieces,
                kerf: kerfWidth,
                stock: 500  // Adicionado para compatibilidade com o backend
            })
        });

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const result = await response.json();
        if (result.error) {
            throw new Error(result.error);
        }
        
        // Adicionar nomes aos resultados
        result.bars.forEach((bar, index) => {
            bar.name = pieceNames[index] || `Segmento ${index + 1}`;
        });

        displayResult(result);
        document.getElementById("downloadBtn").style.display = "inline-block";
    } catch (error) {
        console.error("Erro ao calcular:", error);
        errorMessage.textContent = `Erro: ${error.message}. Verifique o console para mais detalhes.`;
        errorMessage.style.display = "block";
    }
}

function displayResult(result) {
    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = ""; // Limpa o resultado anterior

    // Container com layout vertical
    const container = document.createElement("div");
    container.className = "border rounded shadow-sm info-box";

    // Lista de barras
    const list = document.createElement("div");

    // Adicionar itens para cada barra
    for (let i = 0; i < result.bars_needed; i++) {
        const bar = result.bars[i] || { pieces: [], remaining: 0 };
        const pieceCounts = {};
        bar.pieces.forEach(piece => {
            pieceCounts[piece] = (pieceCounts[piece] || 0) + 1;
        });
        const piecesStr = Object.entries(pieceCounts)
            .map(([length, count]) => `${length}mm x ${count}`)
            .join(" | ");
        
        const item = document.createElement("div");
        item.className = `d-flex flex-column py-2 ${i < result.bars_needed - 1 ? 'border-bottom border-end-light' : ''}`;
        item.innerHTML = `
            <div class="info-title d-flex justify-content-center">${i + 1}. ${piecesStr} | ${bar.remaining.toFixed(2)}mm</div>
            <div class="info-label d-flex justify-content-center">
                ${pieceCounts.length > 0 ? Object.keys(pieceCounts).map((_, idx) => bar.name || `Segmento ${idx + 1}`).join(" | ") : ''} | Desperdício
            </div>
        `;
        list.appendChild(item);
    }

    container.appendChild(list);
    resultDiv.appendChild(container);

    // Resumo
    const totalsDiv = document.createElement("div");
    totalsDiv.className = "totals mt-3";
    totalsDiv.innerHTML = `
        <h3>Resumo:</h3>
        <p>Material total: ${result.material_total.toFixed(2)}mm</p>
        <p>Barras necessárias: ${result.bars_needed}</p>
        <p>Material usado: ${result.material_used.toFixed(2)}mm</p>
        <p>Desperdício total: ${result.total_waste.toFixed(2)}mm</p>
        <p>Total de cortes: ${result.total_cuts}</p>
        <p>Eficiência: ${result.efficiency}%</p>
    `;
    resultDiv.appendChild(totalsDiv);
}

async function downloadPDF() {
    const materialLength = parseFloat(document.getElementById("materialLength").value);
    const kerfWidth = parseFloat(document.getElementById("kerfWidth").value);
    const pieces = [];
    const pieceNames = [];
    const errorMessage = document.getElementById("errorMessage");

    errorMessage.style.display = "none";
    errorMessage.textContent = "";

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

    try {
        const response = await fetch("/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                material_length: materialLength,
                pieces: pieces,
                kerf: kerfWidth,
                stock: 500  // Adicionado para compatibilidade
            })
        });

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const result = await response.json();
        if (result.error) {
            throw new Error(result.error);
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

        if (!pdfResponse.ok) {
            throw new Error(`Erro ao gerar PDF: ${pdfResponse.status}`);
        }

        const blob = await pdfResponse.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "relatorio_cortes.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Erro ao baixar PDF:", error);
        errorMessage.textContent = `Erro: ${error.message}. Verifique o console para mais detalhes.`;
        errorMessage.style.display = "block";
    }
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
    document.getElementById("errorMessage").style.display = "none";
    document.querySelectorAll(".piece-name, .piece-length, .piece-qty, #materialLength, #kerfWidth").forEach(input => input.classList.remove("is-invalid"));
}