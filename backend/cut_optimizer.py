def optimize_cuts(material_length, pieces, kerf=0):
    # Adiciona kerf a cada peça (se já não foi feito no frontend)
    pieces_with_kerf = [p + kerf for p in pieces]
    pieces_sorted = sorted(pieces_with_kerf, reverse=True)
    
    bars = []
    for piece in pieces_sorted:
        placed = False
        for bar in bars:
            if bar["remaining"] >= piece:
                bar["pieces"].append(piece - kerf)  # Remove kerf para exibir o valor real
                bar["remaining"] -= piece
                placed = True
                break
        
        if not placed:
            bars.append({
                "pieces": [piece - kerf],  # Remove kerf para exibir o valor real
                "remaining": material_length - piece
            })
    
    total_waste = sum(bar["remaining"] for bar in bars)
    efficiency = (1 - (total_waste / (len(bars) * material_length))) * 100
    
    return {
        "bars": bars,
        "total_bars": len(bars),
        "total_waste": total_waste,
        "efficiency": round(efficiency, 2),
        "kerf": kerf  # Opcional: retornar para referência
    }