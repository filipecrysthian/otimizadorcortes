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
  const resultDiv = document.getElementById('result');
  resultDiv.innerHTML = '';

  if (!result || !result.formatted_bars) {
    resultDiv.innerHTML = '<div class="alert alert-danger">Erro ao calcular os cortes.</div>';
    return;
  }

  const info = `
    <div class="card mb-3 w-100">
      <div class="card-body">
        <h5 class="card-title">Resumo</h5>
        <p><strong>Total de material:</strong> ${result.material_total}mm</p>
        <p><strong>Barras utilizadas:</strong> ${result.bars_needed}</p>
        <p><strong>Material utilizado:</strong> ${result.material_used}mm</p>
        <p><strong>Total de desperdício:</strong> ${result.total_waste}mm</p>
        <p><strong>Total de cortes:</strong> ${result.total_cuts}</p>
        <p><strong>Eficiência:</strong> ${result.efficiency.toFixed(2)}%</p>
      </div>
    </div>`;

  const barsList = result.formatted_bars.map((bar, index) => {
    const barraLabel = `Barra ${index + 1}`;
    
    // Remove "// 6000mm / Barra X | " ou qualquer prefixo até o primeiro "| "
    const segmentos = bar.split('| ').slice(1).join('| ').trim();

    return `
      <div class="card mb-3 w-100">
        <div class="card-body">
          <h5 class="card-title">${barraLabel}</h5>
          <p class="card-text">${segmentos}</p>
        </div>
      </div>
    `;
  }).join('');

  resultDiv.innerHTML = info + barsList;
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
    document.getElementById("kerfWidth").value = "0";
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