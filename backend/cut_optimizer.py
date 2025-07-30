def optimize_cuts(material_length, pieces, kerf=0):
    pieces_sorted = sorted(pieces, reverse=True)
    bars = []

    for piece in pieces_sorted:
        best_bar = None
        min_remaining = float('inf')

        for bar in bars:
            required_space = piece + (kerf if bar["remaining"] != material_length else 0)
            if bar["remaining"] >= required_space and bar["remaining"] - required_space < min_remaining:
                best_bar = bar
                min_remaining = bar["remaining"] - required_space

        if best_bar:
            best_bar["pieces"].append(piece)
            best_bar["remaining"] -= (piece + (kerf if best_bar["remaining"] != material_length else 0))
        else:
            bars.append({
                "pieces": [piece],
                "remaining": material_length - piece
            })

    total_waste = sum(bar["remaining"] for bar in bars)
    efficiency = (1 - (total_waste / (len(bars) * material_length))) * 100

    return {
        "bars": bars,
        "total_bars": len(bars),
        "total_waste": total_waste,
        "efficiency": round(efficiency, 2)
    }