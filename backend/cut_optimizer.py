from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, value

def optimize_cuts(material_length, pieces, kerf=0):
    # Criar o problema de otimização
    prob = LpProblem("Cutting_Stock_Problem", LpMinimize)

    # Preparar dados: contar peças por tamanho
    piece_counts = {}
    for p in pieces:
        piece_counts[p] = piece_counts.get(p, 0) + 1
    unique_pieces = list(piece_counts.keys())

    # Variáveis: y_j = 1 se a barra j for usada, x_ij = quantidade da peça i na barra j
    max_bars = len(pieces)  # Limite superior para o número de barras
    y = [LpVariable(f"y_{j}", cat="Binary") for j in range(max_bars)]
    x = [[LpVariable(f"x_{i}_{j}", lowBound=0, cat="Integer") for j in range(max_bars)] for i in range(len(unique_pieces))]

    # Função objetivo: minimizar o número de barras
    prob += lpSum(y[j] for j in range(max_bars))

    # Restrições
    # 1. Atender à demanda de cada peça
    for i, piece_length in enumerate(unique_pieces):
        prob += lpSum(x[i][j] for j in range(max_bars)) >= piece_counts[piece_length], f"Demand_{i}"

    # 2. Respeitar o comprimento da barra, considerando kerf após cada peça
    for j in range(max_bars):
        total_pieces = lpSum(x[i][j] for i in range(len(unique_pieces)))
        total_length = lpSum(x[i][j] * unique_pieces[i] for i in range(len(unique_pieces)))
        kerf_constraint = total_pieces * kerf  # Kerf após cada peça, incluindo a última
        prob += total_length + kerf_constraint <= material_length * y[j], f"Capacity_{j}"

    # Resolver o problema
    prob.solve()

    # Verificar se a solução é válida
    if LpStatus[prob.status] != "Optimal":
        raise ValueError("Não foi possível encontrar uma solução ótima")

    # Extrair resultados
    bars = []
    for j in range(max_bars):
        if value(y[j]) == 1:
            bar_pieces = []
            for i in range(len(unique_pieces)):
                count = int(value(x[i][j]))
                for _ in range(count):
                    bar_pieces.append(unique_pieces[i])
            if bar_pieces:
                total_used = sum(bar_pieces) + len(bar_pieces) * kerf  # Incluir kerf para cada peça
                bars.append({
                    "pieces": bar_pieces,
                    "remaining": material_length - total_used
                })

    # Calcular métricas
    total_waste = sum(bar["remaining"] for bar in bars)
    efficiency = (1 - (total_waste / (len(bars) * material_length))) * 100 if bars else 0

    return {
        "bars": bars,
        "total_bars": len(bars),
        "total_waste": total_waste,
        "efficiency": round(efficiency, 2)
    }