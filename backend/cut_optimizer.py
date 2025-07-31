from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, value
import sys

def optimize_cuts(material_length, pieces, kerf=0):
    print("Iniciando otimização com material_length={}, pieces={}, kerf={}".format(material_length, pieces, kerf), file=sys.stderr)
    # Criar o problema de otimização
    prob = LpProblem("Cutting_Stock_Problem", LpMinimize)

    # Preparar dados: contar peças por tamanho
    piece_counts = {}
    for p in pieces:
        piece_counts[p] = piece_counts.get(p, 0) + 1
    unique_pieces = list(piece_counts.keys())
    print("Peças únicas: {}".format(unique_pieces), file=sys.stderr)

    # Estimar um limite superior mais generoso para o número de barras
    max_bars = max(3, sum(piece_counts.values()) // 10 + 1)
    print("Máximo de barras estimado: {}".format(max_bars), file=sys.stderr)

    # Variáveis: y_j = 1 se a barra j for usada, x_ij = quantidade da peça i na barra j
    y = [LpVariable(f"y_{j}", cat="Binary") for j in range(max_bars)]
    x = [[LpVariable(f"x_{i}_{j}", lowBound=0, cat="Integer") for j in range(max_bars)] for i in range(len(unique_pieces))]
    print("Variáveis criadas para {} barras".format(max_bars), file=sys.stderr)

    # Função objetivo: minimizar o número de barras
    prob += lpSum(y[j] for j in range(max_bars))

    # Restrições
    # 1. Atender à demanda de cada peça
    for i, piece_length in enumerate(unique_pieces):
        prob += lpSum(x[i][j] for j in range(max_bars)) >= piece_counts[piece_length], f"Demand_{i}"
        print("Restrição de demanda adicionada para peça {}: {}".format(piece_length, piece_counts[piece_length]), file=sys.stderr)

    # 2. Respeitar o comprimento da barra, considerando kerf entre as peças
    for j in range(max_bars):
        total_length = lpSum(x[i][j] * unique_pieces[i] for i in range(len(unique_pieces)))
        total_pieces = lpSum(x[i][j] for i in range(len(unique_pieces)))
        kerf_constraint = (total_pieces - 1) * kerf  # Removida a condição if, kerf é aplicado linearmente
        prob += total_length + kerf_constraint <= material_length * y[j], f"Capacity_{j}"
        print("Restrição de capacidade adicionada para barra {} com kerf {}".format(j, kerf_constraint), file=sys.stderr)

    # Resolver o problema
    print("Resolvendo o problema...", file=sys.stderr)
    prob.solve()
    print("Status da solução: {}".format(LpStatus[prob.status]), file=sys.stderr)

    # Verificar se a solução é válida
    if LpStatus[prob.status] != "Optimal":
        print("Solução não ótima detectada", file=sys.stderr)
        raise ValueError("Não foi possível encontrar uma solução ótima")

    # Extrair resultados iniciais
    bars = []
    for j in range(max_bars):
        if value(y[j]) == 1:
            bar_pieces = []
            for i in range(len(unique_pieces)):
                count = int(value(x[i][j]))
                for _ in range(count):
                    bar_pieces.append(unique_pieces[i])
            if bar_pieces:
                total_used = sum(bar_pieces) + max(0, len(bar_pieces) - 1) * kerf
                bars.append({
                    "pieces": bar_pieces,
                    "remaining": material_length - total_used
                })
    print("Barras otimizadas: {}".format(bars), file=sys.stderr)

    # Pós-processamento com heurística First-Fit Decreasing para ajustar a distribuição
    def first_fit_decreasing(pieces_list, material_length, kerf):
        remaining_pieces = pieces_list.copy()
        optimized_bars = []
        while remaining_pieces:
            current_bar = []
            current_length = 0
            i = 0
            while i < len(remaining_pieces):
                if current_length + remaining_pieces[i] + (len(current_bar) * kerf) <= material_length:
                    current_bar.append(remaining_pieces[i])
                    current_length += remaining_pieces[i]
                i += 1
            for piece in current_bar:
                remaining_pieces.remove(piece)
            waste = material_length - current_length - ((len(current_bar) - 1) * kerf) if current_bar else 0
            optimized_bars.append({"pieces": current_bar, "remaining": waste})
        return optimized_bars

    # Reorganizar as peças alocadas com FFD
    all_pieces = [p for bar in bars for p in bar["pieces"]]
    optimized_bars = first_fit_decreasing(all_pieces, material_length, kerf)
    print("Barras após FFD: {}".format(optimized_bars), file=sys.stderr)

    # Calcular métricas
    total_waste = sum(bar["remaining"] for bar in optimized_bars)
    efficiency = (1 - (total_waste / (len(optimized_bars) * material_length))) * 100 if optimized_bars else 0
    print("Total de desperdício: {}, Eficiência: {}".format(total_waste, efficiency), file=sys.stderr)

    return {
        "bars": optimized_bars,
        "total_bars": len(optimized_bars),
        "total_waste": total_waste,
        "efficiency": round(efficiency, 2)
    }