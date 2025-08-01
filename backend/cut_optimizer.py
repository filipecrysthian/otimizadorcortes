import sys

def optimize_cuts(material_length, pieces, kerf=0, stock=500):
    print(f"Iniciando otimização com material_length={material_length}, pieces={pieces}, kerf={kerf}, stock={stock}", file=sys.stderr)

    # Normalizar e validar a entrada
    piece_counts = {}
    if not pieces or not isinstance(pieces, (list, tuple)):
        raise ValueError("A entrada 'pieces' deve ser uma lista ou tupla de segmentos")

    if all(isinstance(p, (list, tuple)) and len(p) == 2 for p in pieces):
        for length, qty in pieces:
            if not isinstance(length, (int, float)) or not isinstance(qty, int):
                raise ValueError("Cada segmento deve ser uma tupla (comprimento, quantidade) com valores numéricos")
            piece_counts[length] = piece_counts.get(length, 0) + qty
    elif all(isinstance(p, (int, float)) for p in pieces):
        for length in pieces:
            piece_counts[length] = piece_counts.get(length, 0) + 1
    else:
        raise ValueError("Formato de entrada 'pieces' inválido. Use [(comprimento, quantidade)] ou [comprimento]")

    unique_pieces = sorted(piece_counts.keys(), reverse=True)
    total_pieces = sum(piece_counts.values())
    print(f"Peças únicas: {unique_pieces}", file=sys.stderr)

    if total_pieces > stock:
        raise ValueError(f"Quantidade total de peças ({total_pieces}) excede o stock disponível ({stock})")

    all_pieces = []
    for length, qty in piece_counts.items():
        all_pieces.extend([length] * qty)

    remaining_pieces = sorted(all_pieces, reverse=True)
    optimized_bars = []

    while remaining_pieces:
        current_bar = []
        i = 0
        while i < len(remaining_pieces):
            piece = remaining_pieces[i]
            total_length = sum(current_bar) + (len(current_bar) * kerf if current_bar else 0)
            extra_kerf = kerf if current_bar else 0
            if total_length + piece + extra_kerf <= material_length:
                current_bar.append(piece)
                remaining_pieces.pop(i)
            else:
                i += 1
        waste = material_length - (sum(current_bar) + (len(current_bar) - 1) * kerf if current_bar else 0)
        optimized_bars.append({"pieces": current_bar, "remaining": waste})

    # Realocação entre últimas barras, se possível
    if len(optimized_bars) > 1:
        for i in range(len(optimized_bars) - 1, 0, -1):
            current = optimized_bars[i]
            prev = optimized_bars[i - 1]
            while current["pieces"]:
                piece_to_move = current["pieces"][-1]
                new_length = sum(prev["pieces"]) + piece_to_move + len(prev["pieces"]) * kerf
                if new_length <= material_length:
                    prev["pieces"].append(piece_to_move)
                    current["pieces"].pop()
                    prev["remaining"] = material_length - (sum(prev["pieces"]) + (len(prev["pieces"]) - 1) * kerf)
                    current["remaining"] = material_length - (sum(current["pieces"]) + (len(current["pieces"]) - 1) * kerf if current["pieces"] else 0)
                else:
                    break

    # Formatar a saída
    formatted_bars = []
    for idx, bar in enumerate(optimized_bars, 1):
        segments = bar["pieces"]
        if segments:
            segment_counts = {}
            for seg in segments:
                segment_counts[seg] = segment_counts.get(seg, 0) + 1
            segment_str = " | ".join(f"Segmento {i+1} - {length} x {qty}" for i, (length, qty) in enumerate(sorted(segment_counts.items())))
            formatted_bars.append(f"// {material_length}mm / Barra {idx} | {segment_str} | Desperdício - {bar['remaining']}mm")

    # Estatísticas
    material_total = material_length * len(optimized_bars)
    total_waste = sum(bar["remaining"] for bar in optimized_bars)
    material_used = material_total - total_waste
    total_cuts = total_cuts = sum(len(bar["pieces"]) for bar in optimized_bars if bar["pieces"])
    efficiency = (1 - (total_waste / material_total)) * 100 if material_total else 0

    print(f"Barras otimizadas: {optimized_bars}", file=sys.stderr)
    print(f"Resumo - Material total: {material_total}mm, Barras necessárias: {len(optimized_bars)}, Material usado: {material_used}mm, Desperdício total: {total_waste}mm, Total de cortes: {total_cuts}, Eficiência: {efficiency:.1f}%", file=sys.stderr)

    return {
        "bars": optimized_bars,
        "formatted_bars": formatted_bars,
        "material_total": material_total,
        "bars_needed": len(optimized_bars),
        "material_used": material_used,
        "total_waste": total_waste,
        "total_cuts": total_cuts,
        "efficiency": round(efficiency, 1)
    }
